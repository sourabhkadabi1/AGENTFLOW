import os, shutil, socket, subprocess, sys, time, signal, tempfile, httpx, pytest
ROOT = os.path.dirname(os.path.dirname(__file__)); BASE = "http://127.0.0.1:8000"
H = {"x-api-key": "dev-user-key"}; ADMIN = {"x-admin-token": "dev-admin-token"}
_WIN = os.name == "nt"
PROFILES = ["cleanco", "quickclean", "sentipro", "bargainsent", "slowsent", "reportwriter", "cheapreport",
            "codeparser", "fastparse", "bugfinder", "cheapscanner", "auditwriter"]

def _find_bash():
    """Locate bash: PATH first, then common Git-for-Windows locations."""
    found = shutil.which("bash")
    if found: return found
    for candidate in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files (x86)\Git\bin\bash.exe"):
        if os.path.isfile(candidate): return candidate
    return "bash"

def _busy(port):
    s = socket.socket(); s.settimeout(0.3); r = s.connect_ex(("127.0.0.1", port)) == 0; s.close(); return r

def _start_stack_native(env):
    """Start the gateway + providers as individual Python subprocesses (Windows-safe, no bash needed)."""
    procs = []
    kw = dict(cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if _WIN:
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    # remove stale db
    for s in ("", "-wal", "-shm"):
        try: os.remove(env["AGENTFLOW_DB"] + s)
        except FileNotFoundError: pass
    # gateway
    procs.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "gateway.main:app",
                  "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning",
                  "--timeout-graceful-shutdown", "2"], **kw))
    time.sleep(2)
    # providers
    profiles = PROFILES + (["gemreport"] if env.get("WITH_LLM") == "1" else [])
    for profile in profiles:
        p_env = {**env, "PROFILE": profile}
        procs.append(subprocess.Popen([sys.executable, "-m", "providers.provider_app"],
                      cwd=ROOT, env=p_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      **({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if _WIN else {})))
    return procs

def _kill_procs(procs):
    """Terminate all processes, forcefully if needed."""
    for p in procs:
        try: p.terminate()
        except OSError: pass
    deadline = time.time() + 3
    for p in procs:
        remaining = max(0.1, deadline - time.time())
        try: p.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            try: p.kill()
            except OSError: pass

@pytest.fixture(scope="session")
def stack(tmp_path_factory):
    stale = [p for p in [8000] + list(range(9101, 9109)) + list(range(9201, 9206)) if _busy(p)]
    if stale: pytest.fail(f"ports in use {stale}: stale AgentFlow processes. Run ./scripts/stop_all.sh and retry.", pytrace=False)
    d = tmp_path_factory.mktemp("af")
    env = {**os.environ, "AGENTFLOW_DB": str(d / "t.db"), "AGENTFLOW_KEYS": str(d / "keys"),
           "EXEC_TIMEOUT": "3", "WITH_LLM": "1", "GATEWAY_URL": "http://127.0.0.1:8000"}
    pytest.keys_dir = d / "keys"
    if _WIN:
        procs = _start_stack_native(env)
    else:
        env["PYTHON"] = sys.executable
        popen_kw = dict(cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
        procs = [subprocess.Popen([_find_bash(), "scripts/run_all.sh"], **popen_kw)]
    try:
        for _ in range(60):
            try:
                a = httpx.get(BASE + "/registry/agents", timeout=1).json()
                if sum(1 for x in a if x["role"] == "provider" and x["healthy"]) >= 12: break
            except Exception: pass
            time.sleep(0.5)
        else: pytest.fail("stack did not come up with 12+ healthy providers")
        yield BASE
    finally:
        if _WIN:
            _kill_procs(procs)
        else:
            try: os.killpg(os.getpgid(procs[0].pid), signal.SIGTERM)
            except (ProcessLookupError, OSError): pass
        for _ in range(20):
            if not any(_busy(x) for x in [8000] + list(range(9101, 9109)) + list(range(9201, 9206))): break
            time.sleep(0.25)
        else:
            if _WIN:
                _kill_procs(procs)
            else:
                try: os.killpg(os.getpgid(procs[0].pid), signal.SIGKILL)
                except (ProcessLookupError, OSError): pass

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

def run_code_audit(budget=25, mode="agentflow", priority="balanced", key=None, timeout=60):
    hdr = dict(H)
    if key: hdr["idempotency-key"] = key
    tid = httpx.post(BASE + "/tasks", json={"goal": "Security code audit and vulnerability scan", "budget_inr": budget, "priority": priority, "mode": mode, "n_reviews": 50}, headers=hdr).json()["task_id"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        t = httpx.get(f"{BASE}/tasks/{tid}").json()
        if t["status"] in ("COMPLETED", "FAILED"): return t
        time.sleep(0.5)
    pytest.fail("task timeout")
