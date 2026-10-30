"""Find a Gemini model that actually works with YOUR key. Model names change and some 404 for new keys.
  export GEMINI_API_KEY=...   then   python scripts/check_gemini.py
Prints the model to put in GEMINI_MODEL. Safe to run any time; makes at most ~6 tiny requests."""
import os, sys, httpx
key = os.getenv("GEMINI_API_KEY"); base = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
if not key: sys.exit("GEMINI_API_KEY is not set. Get one free at https://aistudio.google.com (API keys). The platform works without it.")
H = {"x-goog-api-key": key}
r = httpx.get(f"{base}/models", headers=H, timeout=15)
if r.status_code != 200: sys.exit(f"models.list failed: HTTP {r.status_code} {r.text[:200]}  (bad key? API not enabled?)")
avail = [m["name"].split("/")[-1] for m in r.json().get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
print(f"{len(avail)} models support generateContent")
order = [os.getenv("GEMINI_MODEL"), "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
for m in [x for x in dict.fromkeys(order) if x]:
    if m not in avail: print(f"  skip {m}: not listed for your key"); continue
    t = httpx.post(f"{base}/models/{m}:generateContent", headers=H, timeout=20, json={"contents": [{"parts": [{"text": "Reply with the single word: ok"}]}]})
    print(f"  {m}: HTTP {t.status_code}")
    if t.status_code == 200:
        print(f"\nWORKS. Set:  export GEMINI_MODEL={m}"); sys.exit(0)
sys.exit("No candidate worked. Pick any name from the list above (see https://ai.google.dev/gemini-api/docs/models) and test it with curl.")
