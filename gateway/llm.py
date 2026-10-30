"""LLM is used ONLY to interpret the goal. Money, permissions, deadlines, settlement are deterministic code.
No GEMINI_API_KEY (or any failure/invalid output) => deterministic fallback. The pipeline never depends on the LLM being up."""
import json
from common import gemini

PIPELINES = {"reviews": ["clean_data", "sentiment", "report"]}

def _fallback(goal: str) -> dict: return {"pipeline": "reviews", "source": "deterministic_fallback"}

async def interpret_goal(goal: str) -> dict:
    if not gemini.enabled(): return _fallback(goal)
    txt = await gemini.generate('Classify this goal. Reply ONLY JSON {"pipeline":"reviews"|"unsupported"}. Goal: ' + goal[:500], json_mode=True, timeout=6)
    try:
        d = json.loads(txt)
        if d.get("pipeline") in PIPELINES: return {"pipeline": d["pipeline"], "source": "gemini"}
    except Exception: pass
    return _fallback(goal)
