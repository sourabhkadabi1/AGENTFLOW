"""Explainable, deterministic bid scoring.  S_i = w_r*R_i - w_c*C_i - w_t*T_i   (C = price/stage budget, T = eta/deadline).
R_i is VERIFIED reliability from the registry, never the provider's claim. Hard constraints filter BEFORE scoring."""
WEIGHTS = {  # (w_r, w_c, w_t)
    "balanced": (0.40, 0.40, 0.20),
    "reliability": (0.70, 0.20, 0.10),
    "cost": (0.15, 0.75, 0.10),
    "auto": (0.40, 0.40, 0.20),
    "cheapest": (0.0, 1.0, 0.0),
}

def rank(bids: list, priority: str, cap_budget: int, deadline_ms: int, custom_weights: tuple | None = None):
    """bids: [{provider_id, price(gross paise), eta_ms, reliability}] already filtered by hard constraints.
    C = price / stage budget, T = eta / deadline  (both in [0,1]). NOT min-max across bids: min-max blows a 5-paise gap up to a full
    point and would let a provably unreliable cheap agent keep winning."""
    wr, wc, wt = custom_weights if custom_weights else WEIGHTS.get(priority, WEIGHTS["balanced"])
    out = []
    for b in bids:
        C, T, R = min(1.0, b["price"] / max(1, cap_budget)), min(1.0, b["eta_ms"] / max(1, deadline_ms)), b["reliability"]
        s = wr * R - wc * C - wt * T
        out.append({**b, "score": round(s, 4), "breakdown": {"R": round(R, 3), "C": round(C, 3), "T": round(T, 3), "w": [wr, wc, wt],
                    "terms": [round(wr * R, 4), round(-wc * C, 4), round(-wt * T, 4)]}})
    out.sort(key=lambda b: (-b["score"], b["price"], b["eta_ms"], b["provider_id"]))   # deterministic tie-break
    return out
