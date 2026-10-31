import httpx, time, json

BASE = "http://127.0.0.1:8000"
H = {"x-api-key": "dev-user-key"}

print("--- 1. Testing Scenario 1: Customer Review Analysis ---")
t1_resp = httpx.post(f"{BASE}/tasks", json={
    "goal": "Analyze customer reviews and produce a report",
    "budget_inr": 20,
    "priority": "balanced",
    "mode": "agentflow",
    "n_reviews": 100,
    "constraints": ["must mention battery issues", "minimum 5 recommendations"]
}, headers=H, timeout=10)
print("Task 1 created:", t1_resp.status_code, t1_resp.json())
tid1 = t1_resp.json()["task_id"]

for _ in range(60):
    t = httpx.get(f"{BASE}/tasks/{tid1}").json()
    if t["status"] in ("COMPLETED", "FAILED"):
        print("Task 1 finished with status:", t["status"], "Spent:", t.get("spent"), "Wasted:", t.get("wasted"))
        break
    time.sleep(1)

print("\n--- 2. Testing Scenario 2: Code Security Audit ---")
t2_resp = httpx.post(f"{BASE}/tasks", json={
    "goal": "Run a security code audit to find vulnerabilities and bugs",
    "budget_inr": 25,
    "priority": "balanced",
    "mode": "agentflow",
    "n_reviews": 50,
    "constraints": ["must mention sql_injection", "minimum 3 recommendations"]
}, headers=H, timeout=10)
print("Task 2 created:", t2_resp.status_code, t2_resp.json())
tid2 = t2_resp.json()["task_id"]

for _ in range(60):
    t = httpx.get(f"{BASE}/tasks/{tid2}").json()
    if t["status"] in ("COMPLETED", "FAILED"):
        print("Task 2 finished with status:", t["status"], "Spent:", t.get("spent"), "Wasted:", t.get("wasted"))
        if "final" in t.get("result", {}):
            print("Audit Report Summary:", t["result"]["final"].get("audit_report", {}).get("summary"))
        break
    time.sleep(1)

print("\n--- 3. Verifying Invariants ---")
av = httpx.get(f"{BASE}/audit/verify").json()
lv = httpx.get(f"{BASE}/ledger/verify").json()
print("Audit verification:", av)
print("Ledger verification:", lv)

print("\n--- 4. Checking Bayesian Reputations ---")
agents = httpx.get(f"{BASE}/registry/agents").json()
for a in agents:
    if a.get("role") == "provider":
        caps = a.get("capabilities", {})
        for cap, cdata in caps.items():
            if cdata.get("evidence", 0) > 0:
                print(f"Agent: {a['name']:<15} Capability: {cap:<15} Verified R: {cdata['verified_reliability']} (Evidence: {cdata['evidence']})")
