"""Terminal fallback demo if the browser dies on stage. Prints the story of one task in plain language."""
import httpx, sys, time, json
B = "http://127.0.0.1:8000"; mode = sys.argv[1] if len(sys.argv) > 1 else "agentflow"; inr = lambda p: f"Rs {p/100:.2f}"
tid = httpx.post(B + "/tasks", headers={"x-api-key": "dev-user-key"}, json={"goal": "Analyze reviews and produce a report", "budget_inr": 20, "mode": mode, "n_reviews": 150}).json()["task_id"]
seen = 0
while True:
    ev = httpx.get(f"{B}/audit?task_id={tid}").json()
    for e in ev[seen:]:
        p, t = e["payload"], e["type"]
        if t == "LEDGER_TXN": continue
        msg = {"BID": lambda: f"{p['name']} bids {inr(p['price'])} (claims {p['claimed_R']:.0%}, verified {p['verified_R']:.0%})",
               "VERDICT": lambda: ("VERIFIER PASS" if p["passed"] else "VERIFIER FAIL: " + p["reason"]),
               "CONTRACT": lambda: f"contract {p['contract_id']}: {inr(p['escrow_held'])} held in escrow for {p['provider']}",
               "SETTLED": lambda: f"released {inr(p['paid'])} to {p['provider']}", "REFUNDED": lambda: f"refunded {inr(p['amount'])}, {p['provider']} unpaid",
               "NEGOTIATED": lambda: f"negotiated {inr(p['list_price'])} -> {inr(p['agreed'])}", "BID_SCORED": lambda: f"winner: {p['winner']} ({p['rule']})",
               "TASK_COMPLETED": lambda: f"DONE. spent {inr(p['spent'])}, paid for bad work {inr(p['wasted_on_bad_work'])}",
               "TASK_FAILED": lambda: f"FAILED: {p['reason']}"}.get(t)
        if msg: print(f"#{e['seq']:<4} {t:<16} {msg()}")
    seen = len(ev)
    if ev and ev[-1]["type"] in ("TASK_COMPLETED", "TASK_FAILED"): break
    time.sleep(0.4)
print("audit chain:", httpx.get(B + "/audit/verify").json()); print("ledger:", httpx.get(B + "/ledger/verify").json()["invariants"]["ok"])
