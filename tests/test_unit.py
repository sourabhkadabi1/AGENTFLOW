"""Pure unit tests (no network): ledger, audit chain, verifier, signing, scoring."""
import json, os, tempfile, pytest
os.environ["AGENTFLOW_DB"] = os.path.join(tempfile.mkdtemp(), "u.db")
from gateway import db, ledger, audit, verifier, scoring
from common import signing
from common.domain import generate_reviews, gross, fee

@pytest.fixture(autouse=True)
def fresh(): db.reset(); yield

def mk_contract(cid="c1", price=100):
    db.x("INSERT INTO contracts(id,task_id,capability,provider_id,price,fee,state,terms,buyer_sig,provider_sig,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,0)", (cid, "t", "clean_data", "p1", price, fee(price), "HELD", "{}", "", ""))

def test_idempotent_transfer_never_double_pays():
    ledger.fund("user:a", 1000, "f1"); r1 = ledger.transfer("user:a", "agent:p", 300, "same-key"); r2 = ledger.transfer("user:a", "agent:p", 300, "same-key")
    assert r2["duplicate"] and r1["txn_id"] == r2["txn_id"] and ledger.balance("agent:p") == 300 and ledger.balance("user:a") == 700

def test_no_overdraft_and_no_negative_amount():
    ledger.fund("user:a", 100, "f1")
    with pytest.raises(ledger.LedgerError): ledger.transfer("user:a", "agent:p", 101, "k1")
    with pytest.raises(ledger.LedgerError): ledger.transfer("user:a", "agent:p", -5, "k2")
    with pytest.raises(ledger.LedgerError): ledger.transfer("user:a", "agent:p", 0, "k3")
    assert ledger.balance("user:a") == 100

def test_release_twice_and_release_after_refund_blocked():
    ledger.fund("user:a", 1000, "f1"); mk_contract(); ledger.hold("c1", "user:a", 100, "t")
    ledger.release("c1", "p1", 100, "t")
    with pytest.raises(ledger.LedgerError): ledger.release("c1", "p1", 100, "t")
    with pytest.raises(ledger.LedgerError): ledger.refund("c1", "user:a", 100, "t")
    assert ledger.balance("agent:p1") == 100 and ledger.balance(ledger.PLATFORM) == fee(100) and ledger.balance("escrow:c1") == 0

def test_refund_returns_full_gross_and_blocks_release():
    ledger.fund("user:a", 1000, "f1"); mk_contract(); ledger.hold("c1", "user:a", 100, "t")
    assert ledger.balance("user:a") == 1000 - gross(100)
    ledger.refund("c1", "user:a", 100, "t"); assert ledger.balance("user:a") == 1000
    with pytest.raises(ledger.LedgerError): ledger.release("c1", "p1", 100, "t")
    assert ledger.invariants()["ok"]

def test_failed_release_rolls_back_atomically():
    ledger.fund("user:a", 1000, "f1"); mk_contract(); ledger.hold("c1", "user:a", 100, "t")
    db.x("DELETE FROM ledger WHERE account='escrow:c1' AND credit>0")   # sabotage: escrow now empty -> payout must fail
    with pytest.raises(ledger.LedgerError): ledger.release("c1", "p1", 100, "t")
    assert db.q1("SELECT state FROM contracts WHERE id='c1'")["state"] == "HELD"   # state change rolled back with the money

def test_invariants_hold_over_random_flow():
    import random; r = random.Random(1); ledger.fund("user:a", 10**6, "f")
    for i in range(40):
        cid = f"c{i}"; mk_contract(cid, r.randint(50, 500)); p = db.q1("SELECT price FROM contracts WHERE id=?", (cid,))["price"]
        ledger.hold(cid, "user:a", p, "t"); (ledger.release if r.random() < .5 else lambda c, pr, p_, t: ledger.refund(c, "user:a", p_, t))(cid, "p1", p, "t")
    inv = ledger.invariants(); assert inv["ok"], inv

def test_audit_chain_detects_edit_delete_and_reorder():
    for i in range(5): audit.append("t", "E", {"i": i})
    assert audit.verify_chain()["ok"]
    db.x("UPDATE events SET payload='{\"i\":99}' WHERE seq=3"); assert audit.verify_chain() == {"ok": False, "broken_at_seq": 3, "checked": 2}
    db.reset(); [audit.append("t", "E", {"i": i}) for i in range(5)]
    db.x("DELETE FROM events WHERE seq=2"); assert not audit.verify_chain()["ok"]

def test_ledger_edit_detected_by_reconcile():
    ledger.fund("user:a", 1000, "f1"); ledger.transfer("user:a", "agent:p", 100, "k")
    assert audit.reconcile_ledger()["ok"]
    db.x("UPDATE ledger SET credit=999999 WHERE account='agent:p'")
    assert not audit.reconcile_ledger()["ok"] and not ledger.invariants()["ok"]

def test_signature_tamper_replay_skew_wrongkey(tmp_path, monkeypatch):
    k = signing.Ed25519PrivateKey.generate(); pub = signing.pub_b64(k); nc = signing.NonceCache(); body = b'{"a":1}'
    h = {x.lower(): v for x, v in signing.sign_headers(k, "a1", "POST", "/x", body).items()}
    assert signing.verify_headers(pub, h, "POST", "/x", body, nc) == (True, "ok")
    assert signing.verify_headers(pub, h, "POST", "/x", body, nc)[1] == "replayed_nonce"
    h2 = {x.lower(): v for x, v in signing.sign_headers(k, "a1", "POST", "/x", body).items()}
    assert signing.verify_headers(pub, h2, "POST", "/x", b'{"a":2}', signing.NonceCache())[1] == "bad_signature"      # body tamper
    assert signing.verify_headers(pub, h2, "POST", "/y", body, signing.NonceCache())[1] == "bad_signature"            # path swap
    other = signing.pub_b64(signing.Ed25519PrivateKey.generate()); h3 = {x.lower(): v for x, v in signing.sign_headers(k, "a1", "POST", "/x", body).items()}
    assert signing.verify_headers(other, h3, "POST", "/x", body, signing.NonceCache())[1] == "bad_signature"          # impersonation
    h4 = {x.lower(): v for x, v in signing.sign_headers(k, "a1", "POST", "/x", body).items()}; h4["x-timestamp"] = "1"
    assert signing.verify_headers(pub, h4, "POST", "/x", body, signing.NonceCache())[1] == "timestamp_outside_window"

# ---- verifier: honest passes, every cheat fails ----
from providers.provider_app import do_clean, do_sentiment, do_report
from collections import Counter
D = generate_reviews(300, 3)
def chain():
    c = do_clean({"reviews": D}, "honest"); s = do_sentiment({"reviews": c["reviews"]}, "honest")
    return c, s, {"labels": s["labels"], "themes": s["complaint_themes"]}

def test_honest_pipeline_passes_verifier():
    c, s, rin = chain()
    assert verifier.verify("clean_data", {"reviews": D}, c)["passed"]
    assert verifier.verify("sentiment", {"reviews": c["reviews"]}, s)["passed"], verifier.verify("sentiment", {"reviews": c["reviews"]}, s)
    assert verifier.verify("report", rin, do_report(rin, "honest"))["passed"]

def test_verifier_rejects_every_cheat():
    c, s, rin = chain(); fc = do_clean({"reviews": D}, "fabricate"); fs = do_sentiment({"reviews": c["reviews"]}, "random"); fr = do_report(rin, "fabricate")
    assert not verifier.verify("clean_data", {"reviews": D}, fc)["passed"]
    assert not verifier.verify("sentiment", {"reviews": c["reviews"]}, fs)["passed"]
    assert not verifier.verify("report", rin, fr)["passed"]
    for cap, inp in (("clean_data", {"reviews": D}), ("sentiment", {"reviews": c["reviews"]}), ("report", rin)):
        for junk in ({"result": "lorem", "note": "trust me"}, None, [], "ok", {"reviews": None}, {"labels": 5, "complaint_themes": []}, {}):
            assert not verifier.verify(cap, inp, junk)["passed"], (cap, junk)

def test_verifier_subtle_cheats():
    c, s, rin = chain()
    d = json.loads(json.dumps(c)); d["reviews"].pop(); assert not verifier.verify("clean_data", {"reviews": D}, d)["passed"]          # drops one row
    d = json.loads(json.dumps(c)); d["reviews"][0]["rating"] = 1 if d["reviews"][0]["rating"] != 1 else 5; assert not verifier.verify("clean_data", {"reviews": D}, d)["passed"]
    d = json.loads(json.dumps(s)); d["labels"].pop(); assert not verifier.verify("sentiment", {"reviews": c["reviews"]}, d)["passed"]
    r = do_report(rin, "honest"); r["sentiment_breakdown"]["positive"] += 1; assert not verifier.verify("report", rin, r)["passed"]
    r = do_report(rin, "honest"); r["top_complaints"][0]["count"] += 1; assert not verifier.verify("report", rin, r)["passed"]
    r = do_report(rin, "honest"); r["recommendations"] = r["recommendations"][:3]; assert not verifier.verify("report", rin, r)["passed"]

def test_scoring_hard_properties():
    mk = lambda i, p, e, r: {"provider_id": i, "price": p, "eta_ms": e, "reliability": r}
    assert scoring.rank([mk("cheap", 105, 500, .5), mk("good", 210, 900, .5)], "balanced", 1685, 8000)[0]["provider_id"] == "cheap"   # cold start: price decides
    assert scoring.rank([mk("cheap", 105, 500, .3), mk("good", 210, 900, .7)], "balanced", 1685, 8000)[0]["provider_id"] == "good"   # evidence beats price
    assert scoring.rank([mk("a", 100, 500, .5), mk("b", 100, 500, .5)], "balanced", 1000, 8000)[0]["provider_id"] == "a"            # deterministic tie-break
    assert scoring.rank([mk("cheap", 105, 500, .1), mk("good", 210, 900, .9)], "cheapest", 1685, 8000)[0]["provider_id"] == "cheap"

def test_crash_recovery_refunds_orphaned_escrow():
    from gateway import orchestrator
    ledger.fund("user:demo", 1000, "f"); db.x("INSERT INTO tasks(id,idem_key,user_id,goal,budget,priority,mode,status,result,created_at) VALUES('t1','k','user:demo','g',900,'balanced','agentflow','RUNNING','{}',0)")
    db.x("INSERT INTO contracts(id,task_id,capability,provider_id,price,fee,state,terms,buyer_sig,provider_sig,created_at) VALUES('c9','t1','clean_data','p1',100,5,'HELD','{}','','',0)")
    ledger.hold("c9", "user:demo", 100, "t1"); assert ledger.balance("user:demo") == 895   # buyer "crashes" here
    assert orchestrator.recover_orphans() == 1
    assert ledger.balance("user:demo") == 1000 and ledger.balance("escrow:c9") == 0 and ledger.invariants()["ok"]
    assert db.q1("SELECT status FROM tasks WHERE id='t1'")["status"] == "FAILED" and orchestrator.recover_orphans() == 0


def test_single_health_blip_cannot_exclude_the_only_provider():
    from gateway import orchestrator, registry
    m = {"capabilities": [{"capability": "clean_data", "version": "1", "price_hint": 100}]}
    registry.register("p-a", "A", "provider", "pk-a", "http://x", m); registry.register("p-b", "B", "provider", "pk-b", "http://y", m)
    assert {c["agent_id"] for c in orchestrator.candidates("clean_data", set())} == {"p-a", "p-b"}
    db.x("UPDATE agents SET healthy=0 WHERE id='p-a'"); assert {c["agent_id"] for c in orchestrator.candidates("clean_data", set())} == {"p-b"}      # healthy preferred
    db.x("UPDATE agents SET healthy=0 WHERE id='p-b'"); assert {c["agent_id"] for c in orchestrator.candidates("clean_data", set())} == {"p-a", "p-b"}  # none healthy -> still try
    assert {c["agent_id"] for c in orchestrator.candidates("clean_data", {"p-a"})} == {"p-b"}                                                          # exclusions still respected


def test_v2_sybil_bond_stake_and_slash_invariants():
    st1 = ledger.stake_bond("provider-quickclean", 500)
    st2 = ledger.stake_bond("provider-quickclean", 500)
    assert not st1["duplicate"] and st2["duplicate"]
    assert ledger.balance("bond:provider-quickclean") == 500
    slashed = ledger.slash_bond("c-fraud-1", "provider-quickclean", 100, "t-1")
    assert slashed == 100 and ledger.balance("bond:provider-quickclean") == 400
    assert ledger.balance(ledger.SLASHED_POOL) == 100
    assert ledger.invariants()["ok"] and audit.reconcile_ledger()["ok"]

def test_v2_policy_brain_derives_valid_weights():
    import asyncio
    from gateway import policy
    p_comp = asyncio.run(policy.derive_policy("Boardroom compliance audit of customer reviews", "auto", 2000))
    assert p_comp["profile"] == "HIGH_COMPLIANCE" and p_comp["weights"][0] >= 0.65
    p_cost = asyncio.run(policy.derive_policy("Quick cheap bulk draft", "auto", 1000))
    assert p_cost["profile"] == "COST_SAVER" and p_cost["weights"][1] >= 0.60

def test_v2_hardened_verifier_catches_lazy_echo_and_subtle_drift():
    c, s, rin = chain()
    # 1. ID-text swap in clean_data
    swapped = json.loads(json.dumps(c))
    swapped["reviews"][0]["text"], swapped["reviews"][1]["text"] = swapped["reviews"][1]["text"], swapped["reviews"][0]["text"]
    v_clean = verifier.verify("clean_data", {"reviews": D}, swapped)
    assert not v_clean["passed"] and "id_text_binding" in v_clean["reason"]
    # 2. Score-label mismatch in sentiment
    drifted = json.loads(json.dumps(s))
    drifted["labels"][0]["label"] = "positive"
    drifted["labels"][0]["score"] = 0
    v_sent = verifier.verify("sentiment", {"reviews": c["reviews"]}, drifted)
    assert not v_sent["passed"] and "score_matches_label" in v_sent["reason"]
    # 3. Duplicate recommendations in report
    rep = do_report(rin, "lazy_echo")
    v_rep = verifier.verify("report", rin, rep)
    assert not v_rep["passed"] and "distinct_recommendations" in v_rep["reason"]
