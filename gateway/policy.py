"""Neuro-Symbolic Risk & Policy Engine.
Derives dynamic scoring weights (w_r, w_c, w_t), minimum reliability floor, probation caps,
and negotiation aggressiveness from the user's goal and priority mode.
Falls back deterministically if GEMINI_API_KEY is unset or returns invalid output."""
import json
from common import gemini
from .scoring import WEIGHTS

PROFILES = {
    "HIGH_COMPLIANCE": {
        "weights": (0.72, 0.18, 0.10),
        "min_reliability": 0.42,
        "discount_target": 0.10,
        "probation_max_paise": 350,
        "reason": "High-stakes/compliance intent detected; prioritizing verified reliability and strict floor."
    },
    "COST_SAVER": {
        "weights": (0.20, 0.70, 0.10),
        "min_reliability": 0.20,
        "discount_target": 0.20,
        "probation_max_paise": 800,
        "reason": "Cost-constrained or bulk intent detected; maximizing price leverage and counter-offer depth."
    },
    "LOW_LATENCY": {
        "weights": (0.35, 0.25, 0.40),
        "min_reliability": 0.30,
        "discount_target": 0.12,
        "probation_max_paise": 600,
        "reason": "Time-critical intent detected; weighting execution ETA heavily."
    },
    "BALANCED": {
        "weights": (0.40, 0.40, 0.20),
        "min_reliability": 0.20,
        "discount_target": 0.15,
        "probation_max_paise": 600,
        "reason": "Balanced utility across verified reliability, stage cost, and latency."
    },
}

def _heuristic_profile(goal: str, priority: str, budget_paise: int) -> str:
    if priority == "reliability":
        return "HIGH_COMPLIANCE"
    if priority == "cost":
        return "COST_SAVER"
    g = (goal or "").lower()
    if any(k in g for k in ("audit", "board", "compliance", "critical", "strict", "accurate", "verified", "executive")):
        return "HIGH_COMPLIANCE"
    if any(k in g for k in ("cheap", "budget", "bulk", "draft", "low cost", "save")) or budget_paise <= 1200:
        return "COST_SAVER"
    if any(k in g for k in ("urgent", "fast", "quick", "immediate", "realtime", "real-time")):
        return "LOW_LATENCY"
    return "BALANCED"

async def derive_policy(goal: str, priority: str, budget_paise: int) -> dict:
    """Returns a validated policy dict guaranteed to obey hard safety bounds."""
    if priority in ("balanced", "reliability", "cost", "cheapest"):
        prof_name = _heuristic_profile(goal, priority, budget_paise)
        base = dict(PROFILES[prof_name])
        base["weights"] = WEIGHTS.get(priority, WEIGHTS["balanced"])
        return {**base, "profile": prof_name, "source": "explicit_priority"}

    # priority == "auto": let Gemini inspect semantic intent, bounded by deterministic clamps
    prof_name = _heuristic_profile(goal, "auto", budget_paise)
    if gemini.enabled():
        prompt = (
            "Analyze this buyer goal and return ONLY JSON: "
            '{"profile":"HIGH_COMPLIANCE"|"COST_SAVER"|"LOW_LATENCY"|"BALANCED",'
            '"w_r":float,"w_c":float,"w_t":float,"min_reliability":float,"reason":str}. '
            f"Budget paise: {budget_paise}. Goal: {goal[:400]}"
        )
        raw = await gemini.generate(prompt, json_mode=True, timeout=5.0)
        try:
            d = json.loads(raw or "{}")
            p = d.get("profile", prof_name)
            if p in PROFILES:
                wr = max(0.10, min(0.85, float(d.get("w_r", PROFILES[p]["weights"][0]))))
                wc = max(0.05, min(0.85, float(d.get("w_c", PROFILES[p]["weights"][1]))))
                wt = max(0.05, min(0.60, float(d.get("w_t", PROFILES[p]["weights"][2]))))
                s = wr + wc + wt
                weights = (round(wr / s, 3), round(wc / s, 3), round(wt / s, 3))
                min_r = max(0.20, min(0.50, float(d.get("min_reliability", PROFILES[p]["min_reliability"]))))
                return {
                    "profile": p,
                    "weights": weights,
                    "min_reliability": round(min_r, 2),
                    "discount_target": PROFILES[p]["discount_target"],
                    "probation_max_paise": PROFILES[p]["probation_max_paise"],
                    "reason": str(d.get("reason") or PROFILES[p]["reason"])[:160],
                    "source": "gemini_policy_brain",
                }
        except Exception:
            pass
    base = dict(PROFILES[prof_name])
    return {**base, "profile": prof_name, "source": "deterministic_policy_brain"}
