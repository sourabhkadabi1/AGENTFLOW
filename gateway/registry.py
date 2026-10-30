import json, time
from . import db

PRIOR_A, PRIOR_B, DECAY = 2.0, 2.0, 0.92   # Beta(2,2) prior => cold start 0.5; decay => one failure never permanently destroys trust

def register(agent_id, name, role, pubkey, endpoint, manifest):
    with db.tx():
        ex = db.q1("SELECT pubkey FROM agents WHERE id=?", (agent_id,))
        if ex and ex["pubkey"] != pubkey: raise ValueError("agent_id_bound_to_different_key")
        if ex: db.x("UPDATE agents SET name=?,role=?,endpoint=?,manifest=?,healthy=1 WHERE id=?", (name, role, endpoint, json.dumps(manifest), agent_id))
        else: db.x("INSERT INTO agents(id,name,role,pubkey,endpoint,manifest,created_at) VALUES(?,?,?,?,?,?,?)", (agent_id, name, role, pubkey, endpoint, json.dumps(manifest), time.time()))
        for cap in manifest.get("capabilities", []):
            db.x("INSERT OR IGNORE INTO reputation(agent_id,capability) VALUES(?,?)", (agent_id, cap["capability"]))

def get(agent_id):
    a = db.q1("SELECT * FROM agents WHERE id=?", (agent_id,))
    if a: a["manifest"] = json.loads(a["manifest"])
    return a

def reliability(agent_id, capability) -> float:
    r = db.q1("SELECT succ,fail FROM reputation WHERE agent_id=? AND capability=?", (agent_id, capability))
    s, f = (r["succ"], r["fail"]) if r else (0, 0)
    return (s + PRIOR_A) / (s + f + PRIOR_A + PRIOR_B)

def evidence(agent_id, capability) -> float:
    r = db.q1("SELECT succ,fail FROM reputation WHERE agent_id=? AND capability=?", (agent_id, capability))
    return (r["succ"] + r["fail"]) if r else 0

def record(agent_id, capability, passed: bool):
    """Only called with an INDEPENDENT verifier verdict. Self-reported scores are never an input."""
    with db.tx():
        db.x("INSERT OR IGNORE INTO reputation(agent_id,capability) VALUES(?,?)", (agent_id, capability))
        db.x("UPDATE reputation SET succ=succ*?, fail=fail*? WHERE agent_id=? AND capability=?", (DECAY, DECAY, agent_id, capability))
        db.x(f"UPDATE reputation SET {'succ' if passed else 'fail'}={'succ' if passed else 'fail'}+1 WHERE agent_id=? AND capability=?", (agent_id, capability))

def discover(capability, include_unhealthy=False):
    from . import ledger
    out = []
    for a in db.q("SELECT * FROM agents WHERE role='provider' AND status='active'"):
        if not include_unhealthy and not a["healthy"]: continue
        m = json.loads(a["manifest"])
        bond_b = ledger.balance(f"bond:{a['id']}")
        for c in m.get("capabilities", []):
            if c["capability"] == capability:
                ev_cnt = round(evidence(a["id"], capability), 1)
                out.append({"agent_id": a["id"], "name": a["name"], "endpoint": a["endpoint"], "version": c.get("version", "1"),
                            "price_hint": c["price_hint"], "claimed_reliability": c.get("claimed_reliability"),
                            "verified_reliability": round(reliability(a["id"], capability), 3), "evidence": ev_cnt,
                            "bond_paise": bond_b, "on_probation": ev_cnt < 1.0})
    return out
