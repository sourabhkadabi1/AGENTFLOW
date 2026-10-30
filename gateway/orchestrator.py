"""The BUYER AGENT. Plans, discovers, solicits bids, scores, negotiates, contracts, escrows, executes, verifies, settles, learns.
Modes (same machinery, different policy) -- used by the benchmark:
  agentflow         trust-weighted scoring + escrow + verification + refund + re-bid
  cheapest_verified cheapest bid, verification + refund + re-bid (ignores reputation)
  naive             cheapest bid, NO verification, pays on delivery, no retry (the 'pay on trust' baseline)"""
import asyncio, json, time, uuid, os
import httpx
from common import signing
from common.domain import gross, fee, CAPABILITIES, FEE_BPS
from . import db, audit, ledger, registry, scoring, verifier, llm, policy

BUYER_ID = "buyer-agent-1"; VERIFIER_ID = "verifier-1"
BUYER_KEY = signing.load_or_create_key(BUYER_ID); VERIFIER_KEY = signing.load_or_create_key(VERIFIER_ID)
MAX_RETRIES = 2; MAX_NEG_ROUNDS = 2; RFQ_TIMEOUT = 3.0; EXEC_TIMEOUT = float(os.getenv("EXEC_TIMEOUT", "8"))
MIN_ELIGIBLE_RELIABILITY = 0.20   # hard floor: an agent with verified R below this is not eligible at all

def fee_of_gross(g):
    n = g * 10000 // (10000 + FEE_BPS)
    while gross(n) < g: n += 1
    while gross(n) > g: n -= 1
    return g - n

def ev(task_id, typ, **payload): return audit.append(task_id, typ, payload)

async def _call(c, provider, path, obj, timeout):
    body = json.dumps(obj).encode(); h = signing.sign_headers(BUYER_KEY, BUYER_ID, "POST", path, body); h["content-type"] = "application/json"
    r = await c.post(provider["endpoint"] + path, content=body, headers=h, timeout=timeout)
    if r.status_code != 200: raise RuntimeError(f"http_{r.status_code}:{r.text[:80]}")
    pub = registry.get(provider["agent_id"])["pubkey"]
    ok, why = signing.verify_headers(pub, {k.lower(): v for k, v in r.headers.items()}, "RESPONSE", path, r.content, _resp_nonces)
    if not ok: raise RuntimeError(f"bad_provider_signature:{why}")      # unsigned/forged provider responses are rejected
    return r.json()
_resp_nonces = signing.NonceCache()

def register_system_agents():
    registry.register(BUYER_ID, "AgentFlow Buyer", "buyer", signing.pub_b64(BUYER_KEY), "internal", {"capabilities": []})
    registry.register(VERIFIER_ID, "AgentFlow Verifier", "verifier", signing.pub_b64(VERIFIER_KEY), "internal", {"capabilities": []})

async def run_task(task_id: str):
    t = db.q1("SELECT * FROM tasks WHERE id=?", (task_id,)); mode, user = t["mode"], t["user_id"]
    prio = "cheapest" if mode in ("naive", "cheapest_verified") else t["priority"]
    data = json.loads(t["result"])["_input"]; budget = t["budget"]; spent = wasted = 0; results = {}
    db.x("UPDATE tasks SET status='RUNNING' WHERE id=?", (task_id,))
    try:
        plan = await llm.interpret_goal(t["goal"]); pipeline = llm.PIPELINES[plan["pipeline"]]
        pol = await policy.derive_policy(t["goal"], prio, budget)
        ev(task_id, "PLAN", pipeline=pipeline, budget=budget, priority=t["priority"], mode=mode, interpreted_by=plan["source"])
        ev(task_id, "POLICY_DECISION", profile=pol["profile"], weights=list(pol["weights"]), min_reliability=pol["min_reliability"], discount_target=pol["discount_target"], reason=pol["reason"], source=pol["source"])
        hints = {cap: min([a["price_hint"] for a in registry.discover(cap)] or [None] or [0]) for cap in pipeline}
        if any(h is None for h in hints.values()):
            return _fail(task_id, "NO_PROVIDER_FOR_CAPABILITY", spent, wasted)
        floor = sum(gross(h) for h in hints.values())
        if floor > budget:
            ev(task_id, "BUDGET_REJECTED", needed_minimum=floor, budget=budget)
            return _fail(task_id, "BUDGET_INSUFFICIENT", spent, wasted)
        stage_input = {"reviews": data}
        async with httpx.AsyncClient() as c:
            for i, cap in enumerate(pipeline):
                remaining = budget - spent
                reserve = sum(gross(hints[x]) for x in pipeline[i + 1:])
                cap_budget = remaining - reserve
                excluded, done = set(), False
                for attempt in range(MAX_RETRIES + 1):
                    ev(task_id, "STAGE_START", capability=cap, attempt=attempt, stage_budget=cap_budget)
                    won = await _procure(c, task_id, cap, stage_input, prio, cap_budget, excluded, user, mode, pol)
                    if won is None:     # one grace retry: transient timeouts / health blips must not fail a stage
                        ev(task_id, "NO_ELIGIBLE_BID_RETRYING", capability=cap, attempt=attempt); await asyncio.sleep(1.0)
                        won = await _procure(c, task_id, cap, stage_input, prio, cap_budget, excluded, user, mode, pol)
                    if won is None: ev(task_id, "NO_ELIGIBLE_BID", capability=cap, attempt=attempt); break
                    cid, prov, price, out, verdict, paid = won
                    if paid: spent += gross(price); cap_budget = budget - spent - reserve
                    if paid and not verdict["passed"]: wasted += gross(price)
                    if verdict["passed"] or (mode == "naive" and out is not None):   # naive buyer cannot tell: it accepts anything delivered
                        results[cap] = out; done = True; break
                    excluded.add(prov["agent_id"])
                    if mode == "naive": break
                    cap_budget = budget - spent - reserve
                if not done: return _fail(task_id, f"STAGE_FAILED:{cap}", spent, wasted)
                stage_input = _next_input(cap, results[cap], stage_input)
        final = {"report": results.get("report"), "stats": {"cleaned": len(results["clean_data"]["reviews"])}}
        _finish(task_id, "COMPLETED", final, spent, wasted)
    except Exception as e:  # never leave a task half-open with money in escrow
        ev(task_id, "BUYER_CRASH", error=f"{type(e).__name__}: {e}")
        _fail(task_id, f"BUYER_ERROR:{type(e).__name__}", spent, wasted)

def _next_input(cap, out, prev):
    if cap == "clean_data": return {"reviews": out["reviews"]}
    if cap == "sentiment": return {"labels": out["labels"], "themes": out["complaint_themes"]}
    return prev

def candidates(cap, excluded):
    """Healthy providers first. If none are left, fall back to ones merely FLAGGED unhealthy: a single missed ping must not kill a task.
    The RFQ itself (3s timeout) is the real liveness test; dead providers simply fail to bid."""
    c = [p for p in registry.discover(cap) if p["agent_id"] not in excluded]
    return c or [p for p in registry.discover(cap, include_unhealthy=True) if p["agent_id"] not in excluded]

async def _procure(c, task_id, cap, stage_input, prio, cap_budget, excluded, user, mode, pol=None):
    """Returns (contract_id, provider, price, output, verdict, paid) or None if no eligible bid."""
    cands = candidates(cap, excluded)
    rfq_id = uuid.uuid4().hex[:10]
    ev(task_id, "DISCOVERED", capability=cap, providers=[{"id": p["agent_id"], "name": p["name"], "verified_R": p["verified_reliability"], "claimed_R": p["claimed_reliability"], "evidence": p["evidence"]} for p in cands])
    size = len(stage_input.get("reviews", stage_input.get("labels", [])))
    async def ask(p):
        try: return p, await _call(c, p, "/rfq", {"rfq_id": rfq_id, "capability": cap, "task_size": size, "buyer_id": BUYER_ID}, RFQ_TIMEOUT)
        except Exception as e: return p, {"error": f"{type(e).__name__}:{e}"}
    raw = await asyncio.gather(*[ask(p) for p in cands])
    eligible = []
    for p, b in raw:
        if "error" in b: ev(task_id, "BID_DROPPED", provider=p["agent_id"], reason=b["error"][:100]); continue
        g = gross(b["price"]); R = registry.reliability(p["agent_id"], cap)
        why = None
        if b.get("agent_id") != p["agent_id"]: why = "identity_mismatch"
        elif g > cap_budget: why = f"over_budget({g}>{cap_budget})"
        elif b["eta_ms"] > EXEC_TIMEOUT * 1000: why = "cannot_meet_deadline"
        elif R < MIN_ELIGIBLE_RELIABILITY and prio != "cheapest": why = f"reliability_below_floor({R:.2f})"
        if why: ev(task_id, "BID_REJECTED", provider=p["agent_id"], price=g, reason=why); continue
        ev(task_id, "BID", provider=p["agent_id"], name=p["name"], price=g, eta_ms=b["eta_ms"], claimed_R=b["claimed_reliability"], verified_R=round(R, 3))
        eligible.append({"provider_id": p["agent_id"], "price": b["price"], "eta_ms": b["eta_ms"], "reliability": R, "_p": p, "gross": g})
    if not eligible: return None
    for e in eligible: e["price_for_score"] = e["price"]
    c_weights = pol["weights"] if (pol and prio == "auto") else None
    ranked = scoring.rank([{**e, "price": e["gross"]} for e in eligible], prio, cap_budget, int(EXEC_TIMEOUT * 1000), custom_weights=c_weights)
    by_id = {e["provider_id"]: e for e in eligible}
    win = ranked[0]; wp = by_id[win["provider_id"]]["_p"]
    why = ("cheapest price" if prio == "cheapest" else "best weighted score")
    ev(task_id, "BID_SCORED", capability=cap, priority=prio, ranking=[{"provider": r["provider_id"], "score": r["score"], **r["breakdown"]} for r in ranked], winner=win["provider_id"], rule=why)
    price = by_id[win["provider_id"]]["price"]
    # bounded negotiation: counter at the best competing price (or 10% below if alone), max 2 rounds
    if mode == "agentflow":
        rivals = [r["price"] - fee_of_gross(r["price"]) for r in ranked[1:]]   # competitors' NET prices (leverage)
        disc = pol["discount_target"] if pol else 0.15
        target = min(rivals) if rivals and min(rivals) < price else int(price * (1.0 - disc))  # match a cheaper rival, else ask policy discount
        target = max(1, min(target, price))
        for rnd in range(1, MAX_NEG_ROUNDS + 1):
            try: resp = await _call(c, wp, "/counter", {"rfq_id": rfq_id, "price": target}, RFQ_TIMEOUT)
            except Exception as e: ev(task_id, "NEGOTIATION_ERROR", error=str(e)[:100]); break
            ev(task_id, "COUNTER", provider=wp["agent_id"], round=rnd, buyer_offer=target, accepted=resp["accepted"], provider_price=resp["price"])
            if resp["accepted"]: ev(task_id, "NEGOTIATED", provider=wp["agent_id"], list_price=by_id[win["provider_id"]]["price"], agreed=resp["price"], saved=by_id[win["provider_id"]]["price"] - resp["price"]); price = resp["price"]; break
            if resp["price"] < price: price = resp["price"]
            target = min(resp["price"], target + max(1, (resp["price"] - target) // 2))
        if gross(price) > cap_budget: price = by_id[win["provider_id"]]["price"]
    # contract: buyer signs canonical terms, provider counter-signs; escrow holds price+fee
    cid = "c-" + uuid.uuid4().hex[:10]
    terms = {"contract_id": cid, "task_id": task_id, "capability": cap, "provider_id": wp["agent_id"], "buyer_id": BUYER_ID, "price": price, "fee": fee(price), "deadline_ms": int(EXEC_TIMEOUT * 1000), "version": wp["version"], "acceptance": "verifier_pass"}
    tb = json.dumps(terms, sort_keys=True, separators=(",", ":")).encode()
    try: acc = await _call(c, wp, "/accept", {"terms": terms}, RFQ_TIMEOUT)
    except Exception as e: ev(task_id, "CONTRACT_REFUSED", provider=wp["agent_id"], error=str(e)[:100]); excluded.add(wp["agent_id"]); return None
    assert signing.verify_blob(registry.get(wp["agent_id"])["pubkey"], acc["provider_sig"], tb), "provider countersignature invalid"
    with db.tx():
        db.x("INSERT INTO contracts(id,task_id,capability,provider_id,price,fee,state,terms,buyer_sig,provider_sig,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
             (cid, task_id, cap, wp["agent_id"], price, fee(price), "HELD", tb.decode(), signing.sign_blob(BUYER_KEY, tb), acc["provider_sig"], time.time()))
        ledger.hold(cid, user, price, task_id)
        ev(task_id, "CONTRACT", contract_id=cid, provider=wp["agent_id"], price=price, fee=fee(price), escrow_held=gross(price), terms_sha=signing.body_hash(tb)[:16])
    # execute
    t0 = time.time(); out = None; err = None
    try: out = (await _call(c, wp, "/execute", {"contract_id": cid, "capability": cap, "input": stage_input, "deadline_ms": terms["deadline_ms"]}, EXEC_TIMEOUT))["output"]
    except Exception as e: err = f"{type(e).__name__}:{str(e)[:80] or 'timeout'}"
    ms = int((time.time() - t0) * 1000)
    ev(task_id, "DELIVERY", contract_id=cid, provider=wp["agent_id"], latency_ms=ms, error=err, output_bytes=len(json.dumps(out)) if out else 0)
    v = verifier.verify(cap, stage_input, out) if err is None else {"passed": False, "score": 0, "checks": [], "reason": f"delivery_error:{err}"}
    vsig = signing.sign_blob(VERIFIER_KEY, json.dumps({"c": cid, "passed": v["passed"], "reason": v["reason"]}, sort_keys=True).encode())
    if mode == "naive":   # baseline pays on delivery, no verdict used; verdict recorded only as hidden ground truth for the benchmark
        ledger.release(cid, wp["agent_id"], price, task_id)
        ev(task_id, "PAID_WITHOUT_VERIFICATION", contract_id=cid, provider=wp["agent_id"], amount=gross(price), ground_truth_passed=v["passed"])
        return cid, wp, price, out, v, True
    ev(task_id, "VERDICT", contract_id=cid, passed=v["passed"], reason=v["reason"], checks=[c_ for c_ in v["checks"] if not c_["ok"]] or "all_ok", verifier=VERIFIER_ID, verifier_sig=vsig[:24])
    if v["passed"]:
        ledger.release(cid, wp["agent_id"], price, task_id); registry.record(wp["agent_id"], cap, True)
        ev(task_id, "SETTLED", contract_id=cid, provider=wp["agent_id"], paid=price, fee=fee(price))
        return cid, wp, price, out, v, True
    ledger.refund(cid, user, price, task_id); registry.record(wp["agent_id"], cap, False)
    slashed = ledger.slash_bond(cid, wp["agent_id"], task_id=task_id) if err is None else 0
    ev(task_id, "REFUNDED", contract_id=cid, provider=wp["agent_id"], amount=gross(price), reason=v["reason"], bond_slashed=slashed)
    if slashed > 0:
        ev(task_id, "BOND_SLASHED", contract_id=cid, provider=wp["agent_id"], slashed_paise=slashed, remaining_bond=ledger.balance(f"bond:{wp['agent_id']}"))
    return cid, wp, price, out, v, False

def _finish(task_id, status, final, spent, wasted):
    r = json.loads(db.q1("SELECT result FROM tasks WHERE id=?", (task_id,))["result"]); r.pop("_input", None); r["final"] = final
    db.x("UPDATE tasks SET status=?, result=?, spent=?, wasted=?, finished_at=? WHERE id=?", (status, json.dumps(r), spent, wasted, time.time(), task_id))
    ev(task_id, f"TASK_{status}", spent=spent, wasted_on_bad_work=wasted)

def _fail(task_id, reason, spent, wasted):
    db.x("UPDATE tasks SET status='FAILED', result=?, spent=?, wasted=?, finished_at=? WHERE id=?", (json.dumps({"error": reason}), spent, wasted, time.time(), task_id))
    ev(task_id, "TASK_FAILED", reason=reason, spent=spent, wasted_on_bad_work=wasted)

def recover_orphans() -> int:
    """Crash safety. The buyer runs in-process, so at startup any HELD contract / RUNNING task belongs to a dead buyer.
    Refund every orphaned hold to its user and fail the task. Never leaves money stuck in escrow."""
    n = 0
    for c in db.q("SELECT c.id, c.price, c.task_id, t.user_id FROM contracts c JOIN tasks t ON t.id=c.task_id WHERE c.state='HELD'"):
        ledger.refund(c["id"], c["user_id"], c["price"], c["task_id"]); ev(c["task_id"], "ORPHAN_REFUNDED", contract_id=c["id"], amount=gross(c["price"])); n += 1
    for t in db.q("SELECT id FROM tasks WHERE status IN ('RUNNING','PENDING')"):
        db.x("UPDATE tasks SET status='FAILED', result=?, finished_at=? WHERE id=?", (json.dumps({"error": "BUYER_RESTARTED"}), time.time(), t["id"])); ev(t["id"], "TASK_FAILED", reason="BUYER_RESTARTED", spent=0, wasted_on_bad_work=0)
    return n
