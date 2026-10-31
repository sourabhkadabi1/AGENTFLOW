"""Pre-flight environment check. Run this FIRST:  python scripts/doctor.py   Exit code 0 = ready."""
import importlib, os, socket, sys
ok = True
def line(good, msg, hint=""):
    global ok; ok &= good or hint == "optional"; print(("PASS " if good else ("note " if hint == "optional" else "FAIL ")) + msg + (f"   -> {hint}" if hint and hint != "optional" and not good else ""))
line(sys.version_info >= (3, 11), f"python {sys.version.split()[0]} (need >= 3.11)", "install Python 3.11+")
for m in ("fastapi", "uvicorn", "httpx", "pydantic", "cryptography", "pytest"):
    try: importlib.import_module(m); line(True, f"module {m}")
    except Exception: line(False, f"module {m}", "pip install -r requirements.txt")
for port in [8000] + list(range(9101, 9109)) + list(range(9201, 9206)):
    s = socket.socket(); s.settimeout(0.3); busy = s.connect_ex(("127.0.0.1", port)) == 0; s.close()
    if port == 9108: line(not busy, f"port {port} free (optional LLM provider)", "optional")
    else: line(not busy, f"port {port} free", "something is already running there: stop it (an old AgentFlow stack?)")
line(os.access(".", os.W_OK), "working directory writable (SQLite db + .keys/)", "run from the project folder")
line(os.path.exists("dashboard/index.html"), "dashboard/index.html present", "run from the project root")
line(bool(os.getenv("GEMINI_API_KEY")), "GEMINI_API_KEY set" if os.getenv("GEMINI_API_KEY") else "GEMINI_API_KEY not set: platform works anyway, Gemini features use fallbacks", "optional")
if os.getenv("ADMIN_TOKEN", "dev-admin-token") == "dev-admin-token": line(False, "default dev tokens in use: fine locally, NOT fine on a public URL", "optional")
print("\nREADY" if ok else "\nFIX THE FAIL LINES ABOVE FIRST"); sys.exit(0 if ok else 1)
