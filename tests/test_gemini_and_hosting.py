"""Gemini integration (against a local MOCK of the REST API), narrative grounding, hosting guards."""
import asyncio, json, os, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest
os.environ.setdefault("AGENTFLOW_DB", os.path.join(tempfile.mkdtemp(), "g.db"))
from common import gemini
from common.domain import generate_reviews

ROOT = os.path.dirname(os.path.dirname(__file__))

class Mock(BaseHTTPRequestHandler):
    reply = {"text": "ok", "status": 200}; seen = []
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        Mock.seen.append(("GET", self.path, dict(self.headers)))
        if self.headers.get("x-goog-api-key") != "k": return self._send(403, {})
        self._send(200, {"models": [{"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent"]}, {"name": "models/gemini-3.5-flash", "supportedGenerationMethods": ["generateContent"]}]})
    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); body = json.loads(self.rfile.read(n)); Mock.seen.append(("POST", self.path, dict(self.headers), body))
        if "gemini-2.5-flash" in self.path: return self._send(404, {"error": "NOT_FOUND"})      # mimic the reported 404 for the old model
        self._send(Mock.reply["status"], {"candidates": [{"content": {"parts": [{"text": Mock.reply["text"]}]}}]})

@pytest.fixture()
def mock(monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), Mock); threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("GEMINI_BASE_URL", f"http://127.0.0.1:{srv.server_port}/v1beta"); monkeypatch.setenv("GEMINI_API_KEY", "k"); monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")
    Mock.seen.clear(); Mock.reply = {"text": "ok", "status": 200}; yield srv; srv.shutdown()

def test_no_key_means_none_and_no_network(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); assert asyncio.run(gemini.generate("hi")) is None

def test_key_goes_in_header_never_in_url(mock):
    Mock.reply["text"] = "hello"; assert asyncio.run(gemini.generate("hi")) == "hello"
    m, path, headers, body = Mock.seen[-1]; assert "key=" not in path and headers["x-goog-api-key"] == "k" and path.endswith("gemini-3.5-flash:generateContent")

def test_api_errors_degrade_to_none_not_exceptions(mock):
    Mock.reply["status"] = 500; assert asyncio.run(gemini.generate("hi")) is None
    assert asyncio.run(gemini.generate("hi", model_name="gemini-2.5-flash")) is None        # the 404 case

def test_goal_interpretation_falls_back_on_garbage(mock):
    from gateway import llm
    Mock.reply["text"] = "not json at all"; assert asyncio.run(llm.interpret_goal("analyze reviews"))["source"] == "deterministic_fallback"
    Mock.reply["text"] = json.dumps({"pipeline": "rm -rf"}); assert asyncio.run(llm.interpret_goal("x"))["source"] == "deterministic_fallback"
    Mock.reply["text"] = json.dumps({"pipeline": "reviews"}); assert asyncio.run(llm.interpret_goal("x"))["source"] == "gemini"

def _report_case():
    from providers.provider_app import do_clean, do_sentiment, do_report
    c = do_clean({"reviews": generate_reviews(300, 5)}, "honest"); s = do_sentiment({"reviews": c["reviews"]}, "honest")
    return {"labels": s["labels"], "themes": s["complaint_themes"]}, do_report({"labels": s["labels"], "themes": s["complaint_themes"]}, "honest")

def test_grounded_gemini_narrative_passes_verifier(mock):
    from providers.provider_app import narrative
    from gateway import verifier
    rin, rep = _report_case(); br = rep["sentiment_breakdown"]
    Mock.reply["text"] = f"There were {br['positive']} positive and {br['negative']} negative reviews. The top issue is {rep['top_complaints'][0]['theme']}."
    rep["narrative"], rep["narrative_source"] = asyncio.run(narrative(rep, "honest")); assert rep["narrative_source"] == "gemini"
    assert verifier.verify("report", rin, rep)["passed"]

def test_hallucinated_number_is_caught_by_verifier(mock):
    from providers.provider_app import narrative
    from gateway import verifier
    rin, rep = _report_case(); Mock.reply["text"] = "Customers love it and sales grew 73% after launch."
    rep["narrative"], _ = asyncio.run(narrative(rep, "honest")); v = verifier.verify("report", rin, rep)
    assert not v["passed"] and "narrative_numbers_grounded" in v["reason"]

def test_hallucinate_mode_without_any_key_is_caught(monkeypatch):
    from providers.provider_app import narrative
    from gateway import verifier
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); rin, rep = _report_case()
    rep["narrative"], rep["narrative_source"] = asyncio.run(narrative(rep, "hallucinate")); assert rep["narrative_source"] == "template"
    assert not verifier.verify("report", rin, rep)["passed"]
    rep["narrative"], _ = asyncio.run(narrative(rep, "honest")); assert verifier.verify("report", rin, rep)["passed"]       # template fallback is itself grounded

def test_check_gemini_script_skips_404_model_and_finds_working_one(mock):
    env = {**os.environ, "GEMINI_MODEL": "gemini-2.5-flash"}
    r = subprocess.run([sys.executable, "scripts/check_gemini.py"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and "gemini-2.5-flash: HTTP 404" in r.stdout and "export GEMINI_MODEL=gemini-3.5-flash" in r.stdout, r.stdout + r.stderr
    r = subprocess.run([sys.executable, "scripts/check_gemini.py"], cwd=ROOT, env={**env, "GEMINI_API_KEY": "wrong"}, capture_output=True, text=True, timeout=30)
    assert r.returncode != 0 and "models.list failed" in (r.stdout + r.stderr)

def test_config_endpoint_and_concurrency_cap(monkeypatch):
    from fastapi.testclient import TestClient
    from gateway import db, main
    db.reset(); c = TestClient(main.app)
    cfg = c.get("/config").json(); assert cfg["dev_tokens"] is True and cfg["demo_mode"] is True
    monkeypatch.setattr(main, "ADMIN_TOKEN", "real-secret"); assert c.get("/config").json()["dev_tokens"] is False
    for i in range(main.MAX_CONCURRENT): db.x("INSERT INTO tasks(id,idem_key,user_id,goal,budget,priority,mode,status,result,created_at) VALUES(?,?,?,?,?,?,?,?,?,0)", (f"x{i}", f"k{i}", "u", "g", 1, "balanced", "agentflow", "RUNNING", "{}"))
    r = c.post("/tasks", json={"goal": "Analyze reviews", "budget_inr": 5}, headers={"x-api-key": "dev-user-key"}); assert r.status_code == 429
    assert db.q1("SELECT COUNT(*) c FROM tasks")["c"] == main.MAX_CONCURRENT          # rejected request created nothing
