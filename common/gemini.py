"""Thin Gemini REST client (generateContent). Optional: with no key or on ANY error it returns None and callers fall back.
Auth uses the documented x-goog-api-key header. GEMINI_BASE_URL lets tests point at a local mock."""
import os, httpx

def base() -> str: return os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
def model() -> str: return os.getenv("GEMINI_MODEL", "gemini-3.5-flash")   # run scripts/check_gemini.py: names change, old ones 404
def enabled() -> bool: return bool(os.getenv("GEMINI_API_KEY"))

async def generate(prompt: str, json_mode: bool = False, timeout: float = 8.0, model_name: str | None = None):
    key = os.getenv("GEMINI_API_KEY")
    if not key: return None
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    if json_mode: body["generationConfig"] = {"responseMimeType": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(f"{base()}/models/{model_name or model()}:generateContent", headers={"x-goog-api-key": key}, json=body)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None
