"""LLM is used ONLY to interpret the goal. Money, permissions, deadlines, settlement are deterministic code.
No GEMINI_API_KEY (or any failure/invalid output) => deterministic fallback. The pipeline never depends on the LLM being up."""
import json
from common import gemini

PIPELINES = {"reviews": ["clean_data", "sentiment", "report"],
             "code_audit": ["parse_code", "find_bugs", "audit_report"]}

# keywords that route to code_audit without needing an LLM
_CODE_KEYWORDS = ("code audit", "code review", "security audit", "bug scan", "vulnerability",
                  "find bugs", "code quality", "static analysis", "security scan", "code scan")

def _fallback(goal: str) -> dict:
    g = (goal or "").lower()
    if any(k in g for k in _CODE_KEYWORDS):
        return {"pipeline": "code_audit", "source": "deterministic_fallback"}
    return {"pipeline": "reviews", "source": "deterministic_fallback"}

async def interpret_goal(goal: str) -> dict:
    if not gemini.enabled(): return _fallback(goal)
    txt = await gemini.generate('Classify this goal. Reply ONLY JSON {"pipeline":"reviews"|"code_audit"|"unsupported"}. '
                                'reviews = customer review analysis. code_audit = code security/quality audit. '
                                'Goal: ' + goal[:500], json_mode=True, timeout=6)
    try:
        d = json.loads(txt)
        if d.get("pipeline") in PIPELINES: return {"pipeline": d["pipeline"], "source": "gemini"}
    except Exception: pass
    return _fallback(goal)
