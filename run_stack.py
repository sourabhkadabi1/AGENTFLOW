"""Windows-native stack runner for AgentFlow demo.
Starts Gateway (8000) and all 12 provider agents (9101-9107, 9201-9205).
Keeps running until stopped."""
import os, sys, time, signal, subprocess
import httpx

# Ensure stdout uses utf-8 or ascii safely
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

ROOT = os.path.dirname(os.path.abspath(__file__))
PROFILES = [
    "cleanco", "quickclean", "sentipro", "bargainsent", "slowsent", "reportwriter", "cheapreport",
    "codeparser", "fastparse", "bugfinder", "cheapscanner", "auditwriter"
]

# Clean up stale DB for fresh demo
for f in ("agentflow.db", "agentflow.db-wal", "agentflow.db-shm"):
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        try: os.remove(p)
        except Exception: pass

env = {
    **os.environ,
    "AGENTFLOW_DB": os.path.join(ROOT, "agentflow.db"),
    "GATEWAY_URL": "http://127.0.0.1:8000",
    "DEMO_MODE": "1",
}

print("[*] Starting AgentFlow Gateway on http://127.0.0.1:8000 ...", flush=True)
procs = []

# Start Gateway
gw_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "gateway.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
    cwd=ROOT, env=env
)
procs.append(gw_proc)
time.sleep(2)

# Start all 12 providers
print(f"[*] Launching {len(PROFILES)} provider agents...", flush=True)
for prof in PROFILES:
    p_env = {**env, "PROFILE": prof}
    p = subprocess.Popen(
        [sys.executable, "-m", "providers.provider_app"],
        cwd=ROOT, env=p_env
    )
    procs.append(p)

print("[*] Waiting for all agents to register with Gateway...", flush=True)
ready = False
for attempt in range(45):
    try:
        r = httpx.get("http://127.0.0.1:8000/registry/agents", timeout=2.0)
        if r.status_code == 200:
            providers = [a for a in r.json() if a.get("role") == "provider" and a.get("healthy")]
            if len(providers) >= len(PROFILES):
                ready = True
                print(f"[+] All {len(providers)} providers registered and healthy!", flush=True)
                break
    except Exception:
        pass
    time.sleep(0.5)

if not ready:
    print("[!] Warning: Some providers may still be registering. Continuing...", flush=True)

print("=" * 60, flush=True)
print("[+] AGENTFLOW MARKETPLACE IS LIVE!", flush=True)
print("[+] Dashboard URL: http://127.0.0.1:8000", flush=True)
print("[+] Both Scenarios Available: Customer Reviews & Code Security Audit", flush=True)
print("=" * 60, flush=True)

def cleanup(sig=None, frame=None):
    print("\n[*] Stopping all AgentFlow processes...", flush=True)
    for p in procs:
        try: p.terminate()
        except Exception: pass
    time.sleep(1)
    for p in procs:
        try: p.kill()
        except Exception: pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()
