"""Hash-chained audit log: hash_n = SHA256(hash_{n-1} | canonical(event)). Not a blockchain: tamper-EVIDENT, single operator."""
import hashlib, json, time
from . import db

GENESIS = "0" * 64

def _canon(ts, task_id, typ, payload) -> str:
    return json.dumps({"ts": ts, "task_id": task_id, "type": typ, "payload": payload}, sort_keys=True, separators=(",", ":"))

def append(task_id, typ, payload) -> dict:
    with db.tx():
        last = db.q1("SELECT hash FROM events ORDER BY seq DESC LIMIT 1")
        prev = last["hash"] if last else GENESIS
        ts = round(time.time(), 3)
        c = _canon(ts, task_id, typ, payload)
        h = hashlib.sha256((prev + "|" + c).encode()).hexdigest()
        cur = db.x("INSERT INTO events(ts,task_id,type,payload,prev_hash,hash) VALUES(?,?,?,?,?,?)",
                   (ts, task_id, typ, json.dumps(payload, sort_keys=True, separators=(",", ":")), prev, h))
        return {"seq": cur.lastrowid, "ts": ts, "task_id": task_id, "type": typ, "payload": payload, "hash": h}

def verify_chain() -> dict:
    prev, n = GENESIS, 0
    for e in db.q("SELECT * FROM events ORDER BY seq"):
        c = _canon(e["ts"], e["task_id"], e["type"], json.loads(e["payload"]))
        if e["prev_hash"] != prev or hashlib.sha256((prev + "|" + c).encode()).hexdigest() != e["hash"]:
            return {"ok": False, "broken_at_seq": e["seq"], "checked": n}
        prev, n = e["hash"], n + 1
    return {"ok": True, "checked": n, "head": prev}

def reconcile_ledger() -> dict:
    """Ledger rows must match LEDGER events in the (verified) chain. Catches direct DB edits of balances."""
    from_events = {}
    for e in db.q("SELECT payload FROM events WHERE type='LEDGER_TXN'"):
        p = json.loads(e["payload"]); from_events[p["txn_id"]] = (p["src"], p["dst"], p["amount"])
    rows = {}
    for r in db.q("SELECT txn_id, account, debit, credit FROM ledger"):
        d = rows.setdefault(r["txn_id"], {"debit": None, "credit": None, "amt_d": 0, "amt_c": 0})
        if r["debit"]: d["debit"], d["amt_d"] = r["account"], r["debit"]
        if r["credit"]: d["credit"], d["amt_c"] = r["account"], r["credit"]
    bad = []
    for t, (s, d, a) in from_events.items():
        r = rows.get(t)
        if not r or r["debit"] != s or r["credit"] != d or r["amt_d"] != a or r["amt_c"] != a: bad.append(t)
    for t in rows:
        if t not in from_events: bad.append(t)
    return {"ok": not bad, "mismatched_txns": bad[:10], "checked": len(rows)}
