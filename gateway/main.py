"""AgentFlow gateway: registry, tasks, ledger/audit read APIs, SSE stream, demo controls, dashboard.   uvicorn gateway.main:app --port 8000"""
import asyncio, json, os, time, uuid
from pathlib import Path
import httpx
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from common import signing
from common.domain import generate_reviews
from . import db, audit, ledger, registry, orchestrator
from .scoring import WEIGHTS

API_KEY = os.getenv("USER_API_KEY", "dev-user-key"); ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token")
REG_TOKEN = os.getenv("REGISTRATION_TOKEN", "dev-registration-token"); DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
DEMO_USER = "user:demo"; DEMO_CREDITS = 100_000   # ₹1000 simulated credits
nonces = signing.NonceCache(); BG = set()
app = FastAPI(title="AgentFlow Gateway")

def bootstrap():
    db.conn(); orchestrator.register_system_agents(); orchestrator.recover_orphans()
    if ledger.balance(DEMO_USER) == 0 and not db.q1("SELECT 1 FROM txns WHERE idem_key='seed:demo'"):
        ledger.fund(DEMO_USER, DEMO_CREDITS, "seed:demo")

@app.on_event("startup")
async def _start():
    bootstrap(); asyncio.create_task(_health_loop())

async def _health_loop():
    misses = {}   # hysteresis: only flag an agent unhealthy after 2 consecutive failed pings (one slow ping is not an outage)
    while True:
        async with httpx.AsyncClient(timeout=3.0) as c:
            for a in db.q("SELECT id, endpoint FROM agents WHERE role='provider'"):
                try: ok = (await c.get(a["endpoint"] + "/health")).status_code == 200
                except Exception: ok = False
                misses[a["id"]] = 0 if ok else misses.get(a["id"], 0) + 1
                db.x("UPDATE agents SET healthy=? WHERE id=?", (0 if misses[a["id"]] >= 2 else 1, a["id"]))
        await asyncio.sleep(3)

def _user(x_api_key): 
    if x_api_key != API_KEY: raise HTTPException(401, "bad_api_key")

class Manifest(BaseModel):
    capabilities: list
class RegisterReq(BaseModel):
    agent_id: str; name: str; role: str; pubkey: str; endpoint: str; manifest: Manifest; registration_token: str

@app.post("/registry/register")
async def register(request: Request):
    body = await request.body(); d = RegisterReq.model_validate_json(body)
    if d.registration_token != REG_TOKEN: raise HTTPException(403, "bad_registration_token")   # sybil gate
    if d.role != "provider": raise HTTPException(422, "only_providers_self_register")
    ok, why = signing.verify_headers(d.pubkey, request.headers, "POST", "/registry/register", body, nonces)  # proof of key possession
    if not ok: raise HTTPException(401, why)
    if request.headers["x-agent-id"] != d.agent_id: raise HTTPException(401, "agent_id_mismatch")
    try: is_new = registry.register(d.agent_id, d.name, d.role, d.pubkey, d.endpoint, d.manifest.model_dump())
    except ValueError as e: raise HTTPException(409, str(e))
    ledger.stake_bond(d.agent_id)
    if is_new:
        audit.append(None, "AGENT_REGISTERED", {"agent_id": d.agent_id, "name": d.name, "pubkey_prefix": d.pubkey[:12], "capabilities": [c["capability"] for c in d.manifest.capabilities], "bond_paise": ledger.balance(f"bond:{d.agent_id}")})
    return {"ok": True}

@app.get("/registry/agents")
def agents():
    out = []
    for a in db.q("SELECT id,name,role,endpoint,healthy,status FROM agents"):
        a["bond_paise"] = ledger.balance(f"bond:{a['id']}")
        a["capabilities"] = {c["capability"]: {"verified_reliability": round(registry.reliability(a["id"], c["capability"]), 3), "evidence": round(registry.evidence(a["id"], c["capability"]), 1), "price_hint": c["price_hint"], "claimed": c.get("claimed_reliability")} for c in registry.get(a["id"])["manifest"].get("capabilities", [])}
        out.append(a)
    return out

@app.get("/registry/agents/{agent_id}")
def agent(agent_id: str):
    a = registry.get(agent_id)
    if not a: raise HTTPException(404, "unknown_agent")
    return {k: a[k] for k in ("id", "name", "role", "pubkey", "endpoint", "manifest")}

@app.get("/registry/discover")
def discover(capability: str): return registry.discover(capability)

class TaskReq(BaseModel):
    goal: str = Field(min_length=3, max_length=500)
    budget_inr: float = Field(gt=0, le=10_000)
    priority: str = "balanced"
    mode: str = "agentflow"
    n_reviews: int = Field(default=200, ge=10, le=2000)
    seed: int = 7
    reviews: list | None = None
    constraints: list[str] = []   # customer-specified acceptance criteria checked by verifier

@app.post("/tasks")
async def create_task(req: TaskReq, x_api_key: str = Header(None), idempotency_key: str = Header(None)):
    _user(x_api_key)
    if req.priority not in WEIGHTS or req.priority == "cheapest": raise HTTPException(422, "priority must be balanced|reliability|cost")
    if req.mode not in ("agentflow", "cheapest_verified", "naive"): raise HTTPException(422, "bad mode")
    key = idempotency_key or uuid.uuid4().hex
    ex = db.q1("SELECT id FROM tasks WHERE idem_key=?", (key,))
    if ex: return {"task_id": ex["id"], "duplicate": True}      # a retried POST never creates a second task / second spend
    if db.q1("SELECT COUNT(*) c FROM tasks WHERE status IN ('PENDING','RUNNING')")["c"] >= MAX_CONCURRENT: raise HTTPException(429, "too_many_running_tasks")
    if req.reviews is not None:
        ok = 10 <= len(req.reviews) <= 3000 and all(isinstance(r, dict) and {"id", "text", "rating"} <= set(r) and isinstance(r["text"], str) and isinstance(r["rating"], int) and 1 <= r["rating"] <= 5 and len(r["text"]) <= 2000 for r in req.reviews)
        if not ok or len({r["id"] for r in req.reviews}) != len(req.reviews): raise HTTPException(422, "reviews must be 10-3000 unique {id,text,rating 1-5} objects")
    data = req.reviews or generate_reviews(req.n_reviews, req.seed)
    constraints = [c.strip() for c in req.constraints if c.strip()]
    tid = "t-" + uuid.uuid4().hex[:8]
    db.x("INSERT INTO tasks(id,idem_key,user_id,goal,budget,priority,mode,status,result,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
         (tid, key, DEMO_USER, req.goal, int(round(req.budget_inr * 100)), req.priority, req.mode, "PENDING", json.dumps({"_input": data, "_constraints": constraints}), time.time()))
    audit.append(tid, "TASK_CREATED", {"goal": req.goal, "budget": int(round(req.budget_inr * 100)), "priority": req.priority, "mode": req.mode, "n_reviews": len(data), "constraints": constraints})
    t = asyncio.create_task(orchestrator.run_task(tid)); BG.add(t); t.add_done_callback(BG.discard)
    return {"task_id": tid, "duplicate": False}

def _task_view(t):
    r = json.loads(t["result"] or "{}"); r.pop("_input", None); r.pop("_constraints", None); t["result"] = r; return t

@app.get("/tasks")
def tasks(): return [_task_view(t) for t in db.q("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50")]

@app.get("/tasks/{tid}")
def task(tid: str):
    t = db.q1("SELECT * FROM tasks WHERE id=?", (tid,))
    if not t: raise HTTPException(404, "unknown_task")
    t = _task_view(t); t["contracts"] = db.q("SELECT id,capability,provider_id,price,fee,state FROM contracts WHERE task_id=?", (tid,)); return t

@app.get("/ledger/balances")
def balances(): return ledger.balances()
@app.get("/ledger/verify")
def lverify(): return {"invariants": ledger.invariants(), "reconcile_with_audit": audit.reconcile_ledger()}
@app.get("/audit")
def audit_list(task_id: str | None = None, limit: int = 500):
    rows = db.q("SELECT * FROM events WHERE (? IS NULL OR task_id=?) ORDER BY seq DESC LIMIT ?", (task_id, task_id, limit))
    for r in rows: r["payload"] = json.loads(r["payload"])
    return rows[::-1]
@app.get("/audit/verify")
def averify(): return audit.verify_chain()

@app.get("/stream")
async def stream(request: Request, since: int = 0):
    async def gen():
        last = since
        while True:
            if await request.is_disconnected(): return
            for r in db.q("SELECT * FROM events WHERE seq>? ORDER BY seq LIMIT 200", (last,)):
                last = r["seq"]; r["payload"] = json.loads(r["payload"]); yield f"id: {last}\ndata: {json.dumps(r)}\n\n"
            yield ": ping\n\n"; await asyncio.sleep(0.4)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/metrics")
def metrics():
    rows = db.q("SELECT mode, COUNT(*) n, SUM(status='COMPLETED') ok, SUM(spent) spent, SUM(wasted) wasted FROM tasks WHERE status IN ('COMPLETED','FAILED') GROUP BY mode")
    return {"by_mode": rows, "ledger": ledger.invariants(), "audit": audit.verify_chain()}

# ---- demo controls (DEMO_MODE only) ----
class Inject(BaseModel): provider: str; mode: str
@app.post("/demo/inject")
async def inject(r: Inject, x_admin_token: str = Header(None)):
    if not DEMO_MODE or x_admin_token != ADMIN_TOKEN: raise HTTPException(403, "demo_controls_disabled_or_bad_token")
    a = registry.get(r.provider)
    if not a: raise HTTPException(404, "unknown_provider")
    async with httpx.AsyncClient(timeout=3) as c:
        resp = await c.post(a["endpoint"] + "/admin/mode", json={"mode": r.mode}, headers={"x-admin-token": ADMIN_TOKEN})
    if resp.status_code != 200: raise HTTPException(resp.status_code, resp.text)
    audit.append(None, "FAILURE_INJECTED", {"provider": r.provider, "mode": r.mode}); return resp.json()

@app.post("/demo/tamper")
def tamper(x_admin_token: str = Header(None)):
    """Demo only: edits an old audit row directly in SQLite to show the chain detects it."""
    if not DEMO_MODE or x_admin_token != ADMIN_TOKEN: raise HTTPException(403, "disabled")
    row = db.q1("SELECT seq FROM events WHERE type='SETTLED' ORDER BY seq LIMIT 1") or db.q1("SELECT seq FROM events ORDER BY seq LIMIT 1")
    if not row: raise HTTPException(409, "nothing to tamper with")
    db.x("UPDATE events SET payload=REPLACE(payload,'\"paid\":','\"paid\":9') WHERE seq=?", (row["seq"],)); return {"tampered_seq": row["seq"], "verify_now": audit.verify_chain()}

@app.post("/demo/reset")
async def reset(x_admin_token: str = Header(None)):
    if not DEMO_MODE or x_admin_token != ADMIN_TOKEN: raise HTTPException(403, "disabled")
    db.reset(); bootstrap(); return {"ok": True, "note": "providers re-register automatically within ~8s"}

@app.get("/", response_class=HTMLResponse)
def index(): return (Path(__file__).parent.parent / "dashboard" / "index.html").read_text(encoding="utf-8")

@app.get("/benchmark")
def benchmark():
    p = Path(__file__).parent.parent / "docs" / "benchmark_results.json"
    return json.loads(p.read_text()) if p.exists() else {}


@app.get("/config")
def config():
    """Lets the dashboard know whether it may use the built-in dev tokens (local) or must ask for real ones (hosted)."""
    from common import gemini
    return {"demo_mode": DEMO_MODE, "dev_tokens": API_KEY == "dev-user-key" and ADMIN_TOKEN == "dev-admin-token", "llm": gemini.enabled(), "max_concurrent": MAX_CONCURRENT}
