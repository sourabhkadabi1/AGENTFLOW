"""Benchmark: AgentFlow vs two cheapest-price baselines against the SAME providers (3 of 7 are cheap fabricators).
Each arm starts from a freshly reset DB so no arm inherits reputation from another. Usage: python scripts/benchmark.py [runs_per_arm]
  naive             cheapest, pays on delivery, no verification
  cheapest_verified cheapest, escrow + verification + refund + re-bid
  agentflow         trust-weighted + escrow + verification + refund + re-bid (+ negotiation)"""
import httpx, json, sys, time, statistics as st
B = "http://127.0.0.1:8000"; H = {"x-api-key": "dev-user-key"}; A = {"x-admin-token": "dev-admin-token"}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8

def wait_providers():
    for _ in range(60):
        try:
            if sum(1 for a in httpx.get(B + "/registry/agents").json() if a["role"] == "provider" and a["healthy"]) >= 12: return
        except Exception: pass
        time.sleep(1)
    raise SystemExit("providers did not re-register")

def one(mode):
    tid = httpx.post(B + "/tasks", json={"goal": "Analyze reviews and produce a report", "budget_inr": 20, "priority": "balanced", "mode": mode, "n_reviews": 150}, headers=H).json()["task_id"]
    t0 = time.time()
    while True:
        t = httpx.get(f"{B}/tasks/{tid}").json()
        if t["status"] in ("COMPLETED", "FAILED"): break
        time.sleep(0.4)
    ev = httpx.get(f"{B}/audit?task_id={tid}").json()
    bad = sum(1 for e in ev if (e["type"] == "VERDICT" and not e["payload"]["passed"]) or (e["type"] == "PAID_WITHOUT_VERIFICATION" and not e["payload"]["ground_truth_passed"]))
    saved = sum(e["payload"]["saved"] for e in ev if e["type"] == "NEGOTIATED")
    # ground truth of the FINAL deliverable for naive: did every stage actually pass?
    good_final = t["status"] == "COMPLETED" and not any(e["type"] == "PAID_WITHOUT_VERIFICATION" and not e["payload"]["ground_truth_passed"] for e in ev)
    err = None if t['status']=='COMPLETED' else t['result'].get('error')
    return dict(err=err, ok=good_final, spent=t["spent"], wasted=t["wasted"], bad=bad, secs=time.time() - t0, saved=saved)

rows = {}
for mode in ("naive", "cheapest_verified", "agentflow"):
    httpx.post(B + "/demo/reset", headers=A); time.sleep(10); wait_providers()
    rows[mode] = [one(mode) for _ in range(N)]
    print(mode, "done", [x["err"] for x in rows[mode]], flush=True)
out = {}
for m, r in rows.items():
    out[m] = dict(runs=len(r), correct_deliverable_pct=round(100 * sum(x["ok"] for x in r) / len(r), 1),
                  avg_spent_inr=round(st.mean(x["spent"] for x in r) / 100, 2), avg_paid_for_bad_work_inr=round(st.mean(x["wasted"] for x in r) / 100, 2),
                  avg_bad_deliveries=round(st.mean(x["bad"] for x in r), 2), avg_seconds=round(st.mean(x["secs"] for x in r), 1),
                  avg_negotiated_saving_inr=round(st.mean(x["saved"] for x in r) / 100, 2),
                  bad_deliveries_first_run=r[0]["bad"], bad_deliveries_last_3_runs=round(st.mean(x["bad"] for x in r[-3:]), 2))
json.dump(out, open("docs/benchmark_results.json", "w"), indent=2); print(json.dumps(out, indent=2))
