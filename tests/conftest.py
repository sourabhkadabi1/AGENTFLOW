import os, socket, subprocess, time, signal, tempfile, httpx, pytest
ROOT = os.path.dirname(os.path.dirname(__file__)); BASE = "http://127.0.0.1:8000"
H = {"x-api-key": "dev-user-key"}; ADMIN = {"x-admin-token": "dev-admin-token"}

def _busy(port):
    s = socket.socket(); s.settimeout(0.3); r = s.connect_ex(("127.0.0.1", port)) == 0; s.close(); return r

@pytest.fixture(scope="session")
def stack(tmp_path_factory):
    stale = [p for p in [8000] + list(range(9101, 9109)) if _busy(p)]
    if stale: pytest.fail(f"ports in use {stale}: stale AgentFlow processes. Run ./scripts/stop_all.sh and retry.", pytrace=False)
    d = tmp_path_factory.mktemp("af")
    env = {**os.environ, "AGENTFLOW_DB": str(d / "t.db"), "AGENTFLOW_KEYS": str(d / "keys"), "EXEC_TIMEOUT": "3", "WITH_LLM": "1"}
    p = subprocess.Popen(["bash", "scripts/run_all.sh"], cwd=ROOT, env=env, preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pytest.keys_dir = d / "keys"
    try:
        for _ in range(60):
            try:
                a = httpx.get(BASE + "/registry/agents", timeout=1).json()
                if sum(1 for x in a if x["role"] == "provider" and x["healthy"]) == 8: break
            except Exception: pass
            time.sleep(0.5)
        else: pytest.fail("stack did not come up with 8 healthy providers (7 + optional LLM provider)")
        yield BASE
    finally:
        try: os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except ProcessLookupError: pass
        for _ in range(20):
            if not any(_busy(x) for x in [8000] + list(range(9101, 9109))): break
            time.sleep(0.25)
        else:
            try: os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except ProcessLookupError: pass

def run_task(budget=20, mode="agentflow", priority="balanced", key=None, n=120, timeout=60):
    hdr = dict(H); 
    if key: hdr["idempotency-key"] = key
    tid = httpx.post(BASE + "/tasks", json={"goal": "Analyze reviews and produce a report", "budget_inr": budget, "priority": priority, "mode": mode, "n_reviews": n}, headers=hdr).json()["task_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        t = httpx.get(f"{BASE}/tasks/{tid}").json()
        if t["status"] in ("COMPLETED", "FAILED"): return t
        time.sleep(0.5)
    pytest.fail("task timeout")

def set_mode(provider, mode): assert httpx.post(BASE + "/demo/inject", json={"provider": provider, "mode": mode}, headers=ADMIN).status_code == 200
def bal(a): return httpx.get(BASE + "/ledger/balances").json().get(a, 0)
def events(tid): return httpx.get(f"{BASE}/audit?task_id={tid}").json()
def verify(): return httpx.get(BASE + "/ledger/verify").json(), httpx.get(BASE + "/audit/verify").json()
