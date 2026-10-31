"""Live multi-process tests: gateway + 7 provider processes. Order matters (reputation accumulates; tamper test is last)."""
import json, time, httpx, pytest
from tests.conftest import *
P = "http://127.0.0.1"

def test_01_all_agents_registered_with_distinct_keys(stack):
    a = {x["id"]: x for x in httpx.get(BASE + "/registry/agents").json()}
    keys = {httpx.get(f"{BASE}/registry/agents/{i}").json()["pubkey"] for i in a}
    assert len(keys) == len(a) == 15

def test_02_unsigned_forged_replayed_and_unknown_callers_rejected(stack):
    from common import signing
    body = b'{"rfq_id":"x","capability":"clean_data","task_size":10}'
    assert httpx.post(P + ":9101/rfq", content=body).status_code == 401                                        # unsigned
    rogue = signing.Ed25519PrivateKey.generate()
    h = signing.sign_headers(rogue, "buyer-agent-1", "POST", "/rfq", body)                                       # claims to be the buyer, wrong key
    assert httpx.post(P + ":9101/rfq", content=body, headers=h).status_code == 401
    h = signing.sign_headers(rogue, "evil-agent", "POST", "/rfq", body)                                          # unregistered identity
    assert httpx.post(P + ":9101/rfq", content=body, headers=h).status_code == 403
    signing.KEY_DIR = pytest.keys_dir; k = signing.load_or_create_key("buyer-agent-1"); h = signing.sign_headers(k, "buyer-agent-1", "POST", "/rfq", body)
    r1 = httpx.post(P + ":9101/rfq", content=body, headers=h); r2 = httpx.post(P + ":9101/rfq", content=body, headers=h)   # exact replay
    assert r1.status_code == 200 and r2.status_code == 401 and "replayed" in r2.text

def test_03_provider_cannot_register_with_wrong_token_or_steal_identity(stack):
    from common import signing
    k = signing.Ed25519PrivateKey.generate(); body = json.dumps({"agent_id": "provider-cleanco", "name": "x", "role": "provider", "pubkey": signing.pub_b64(k), "endpoint": "http://x", "manifest": {"capabilities": []}, "registration_token": "dev-registration-token"}).encode()
    h = signing.sign_headers(k, "provider-cleanco", "POST", "/registry/register", body); h["content-type"] = "application/json"
    assert httpx.post(BASE + "/registry/register", content=body, headers=h).status_code == 409                    # id already bound to another key
    body2 = body.replace(b"dev-registration-token", b"wrong"); h = signing.sign_headers(k, "provider-cleanco", "POST", "/registry/register", body2); h["content-type"] = "application/json"
    assert httpx.post(BASE + "/registry/register", content=body2, headers=h).status_code == 403

def test_04_cold_start_failure_recovery_and_money_conservation(stack):
    before = bal("user:demo"); t = run_task(20)
    assert t["status"] == "COMPLETED", t["result"]
    ev = [e["type"] for e in events(t["id"])]
    assert ev.count("REFUNDED") >= 1 and ev.count("SETTLED") == 3 and "NEGOTIATED" in ev        # failure -> refund -> re-bid; 3 stages paid; negotiation happened
    assert t["wasted"] == 0
    paid = sum(c["price"] + c["fee"] for c in t["contracts"] if c["state"] == "RELEASED")
    assert before - bal("user:demo") == paid == t["spent"]                                       # user paid exactly for verified work, nothing else
    assert all(c["state"] in ("RELEASED", "REFUNDED") for c in t["contracts"])
    l, a = verify(); assert l["invariants"]["ok"] and l["reconcile_with_audit"]["ok"] and a["ok"]

def test_04b_code_audit_scenario_picks_different_agents(stack):
    t = run_code_audit(25)
    assert t["status"] == "COMPLETED", t["result"]
    ev = events(t["id"])
    caps = [e["payload"]["capability"] for e in ev if e["type"] == "STAGE_START"]
    assert "parse_code" in caps and "find_bugs" in caps and "audit_report" in caps
    settled = [e["payload"]["provider"] for e in ev if e["type"] == "SETTLED"]
    assert "provider-codeparser" in settled
    assert "provider-bugfinder" in settled
    assert "provider-auditwriter" in settled

def test_05_reputation_learned_from_verdicts_not_claims(stack):
    ag = {x["id"]: x for x in httpx.get(BASE + "/registry/agents").json()}
    bad, good = ag["provider-quickclean"]["capabilities"]["clean_data"], ag["provider-cleanco"]["capabilities"]["clean_data"]
    assert bad["claimed"] > good["claimed"] and bad["verified_reliability"] < good["verified_reliability"]   # claims 99% but verified lower

def test_06_buyer_now_avoids_known_cheat(stack):
    t = run_task(20); ev = events(t["id"])
    scored = [e for e in ev if e["type"] == "BID_SCORED" and e["payload"]["capability"] == "clean_data"][0]["payload"]
    assert scored["winner"] == "provider-cleanco", scored
    assert not any(e["type"] == "REFUNDED" and e["payload"]["provider"] == "provider-quickclean" for e in ev)

def test_07_duplicate_task_post_is_idempotent(stack):
    before = bal("user:demo"); k = "idem-123"
    a = httpx.post(BASE + "/tasks", json={"goal": "Analyze reviews", "budget_inr": 20, "n_reviews": 60}, headers={**H, "idempotency-key": k}).json()
    b = httpx.post(BASE + "/tasks", json={"goal": "Analyze reviews", "budget_inr": 20, "n_reviews": 60}, headers={**H, "idempotency-key": k}).json()
    assert a["task_id"] == b["task_id"] and b["duplicate"]
    while httpx.get(f"{BASE}/tasks/{a['task_id']}").json()["status"] not in ("COMPLETED", "FAILED"): time.sleep(.5)
    assert len([t for t in httpx.get(BASE + "/tasks").json() if t["id"] == a["task_id"]]) == 1

def test_08_budget_too_small_rejected_before_any_money_moves(stack):
    before = bal("user:demo"); t = run_task(1)
    assert t["status"] == "FAILED" and t["result"]["error"] == "BUDGET_INSUFFICIENT" and bal("user:demo") == before and t["contracts"] == []

def test_09_bad_inputs_rejected(stack):
    for body in ({"goal": "x", "budget_inr": 5}, {"goal": "Analyze reviews", "budget_inr": -1}, {"goal": "Analyze reviews", "budget_inr": 5, "priority": "cheapest"}, {"goal": "Analyze reviews", "budget_inr": 5, "mode": "evil"}):
        assert httpx.post(BASE + "/tasks", json=body, headers=H).status_code == 422, body
    assert httpx.post(BASE + "/tasks", json={"goal": "Analyze reviews", "budget_inr": 5}, headers={"x-api-key": "bad"}).status_code == 401
    assert httpx.post(BASE + "/demo/inject", json={"provider": "provider-cleanco", "mode": "honest"}).status_code == 403

def test_10_provider_hangs_after_contract_funds_returned_and_next_provider_hired(stack):
    set_mode("provider-cleanco", "timeout")
    try:
        before = bal("user:demo"); t = run_task(20)
        ev = events(t["id"]); assert any(e["type"] == "DELIVERY" and e["payload"]["error"] for e in ev)
        assert any(e["type"] == "REFUNDED" and "delivery_error" in e["payload"]["reason"] for e in ev)
    finally: set_mode("provider-cleanco", "honest")
    l, a = verify(); assert l["invariants"]["ok"] and a["ok"]
    assert all(v == 0 for k, v in httpx.get(BASE + "/ledger/balances").json().items() if k.startswith("escrow:"))

def test_11_all_providers_for_a_stage_bad_task_fails_with_zero_loss(stack):
    set_mode("provider-cleanco", "garbage")
    try:
        before = bal("user:demo"); t = run_task(20)
        assert t["status"] == "FAILED" and "STAGE_FAILED:clean_data" in t["result"]["error"]
        assert bal("user:demo") == before and t["spent"] == 0 and t["wasted"] == 0                 # nothing paid for bad work
    finally: set_mode("provider-cleanco", "honest")

def test_12_naive_baseline_pays_for_bad_work_agentflow_does_not(stack):
    set_mode("provider-cleanco", "honest")
    naive = run_task(20, mode="naive"); af = run_task(20, mode="agentflow")
    assert naive["wasted"] > 0 and af["wasted"] == 0
    assert any(e["type"] == "PAID_WITHOUT_VERIFICATION" and not e["payload"]["ground_truth_passed"] for e in events(naive["id"]))

def test_14_llm_provider_hallucination_is_refused_and_honest_llm_provider_is_paid(stack):
    set_mode("provider-cleanco", "honest")
    set_mode("provider-reportwriter", "garbage"); set_mode("provider-cheapreport", "garbage")     # GemReport is now the only valid report provider
    try:
        set_mode("provider-gemreport", "hallucinate"); before = bal("user:demo"); t = run_task(20)
        trail = [e["type"] for e in events(t["id"])][-25:]
        assert t["status"] == "FAILED" and "STAGE_FAILED:report" in t["result"]["error"] and before - bal("user:demo") == t["spent"] and t["wasted"] == 0, trail
        assert any(e["type"] == "VERDICT" and not e["payload"]["passed"] and "narrative_numbers_grounded" in json.dumps(e["payload"]) for e in events(t["id"]))
        set_mode("provider-gemreport", "honest"); t = run_task(20)
        assert t["status"] == "COMPLETED", t["result"]
        rep = t["result"]["final"]["report"]; assert rep["narrative_source"] in ("gemini", "template") and len(rep["narrative"]) > 20
        assert any(c["provider_id"] == "provider-gemreport" and c["state"] == "RELEASED" for c in t["contracts"])
    finally:
        for p in ("provider-reportwriter", "provider-cheapreport", "provider-gemreport"): set_mode(p, "honest")
    l, a = verify(); assert l["invariants"]["ok"] and a["ok"]


def test_99_reset_free_audit_covers_everything_then_tamper_is_detected(stack):
    assert httpx.get(BASE + "/audit/verify").json()["ok"]
    r = httpx.post(BASE + "/demo/tamper", headers=ADMIN).json()
    assert r["verify_now"]["ok"] is False and r["verify_now"]["broken_at_seq"] == r["tampered_seq"]


