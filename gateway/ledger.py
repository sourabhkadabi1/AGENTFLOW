"""Double-entry credits ledger in integer paise. Simulated credits: NO real money moves."""
import time, uuid
from . import db, audit
from common.domain import gross, fee

MINT = "system:mint"          # the only account allowed to go negative (credit issuance for the demo)
PLATFORM = "platform:fees"

class LedgerError(Exception): pass

def balance(account: str) -> int:
    r = db.q1("SELECT COALESCE(SUM(credit),0)-COALESCE(SUM(debit),0) AS b FROM ledger WHERE account=?", (account,))
    return r["b"]

def transfer(src: str, dst: str, amount: int, idem_key: str, memo: str = "", task_id=None) -> dict:
    """Idempotent: the same idem_key can never move money twice (UNIQUE constraint + early return)."""
    if amount <= 0: raise LedgerError("amount must be positive")
    with db.tx():
        ex = db.q1("SELECT txn_id FROM txns WHERE idem_key=?", (idem_key,))
        if ex: return {"txn_id": ex["txn_id"], "duplicate": True}
        if src != MINT and balance(src) < amount: raise LedgerError(f"insufficient_funds:{src}")
        tid = uuid.uuid4().hex[:12]; ts = time.time()
        db.x("INSERT INTO txns(txn_id,idem_key,kind,ts) VALUES(?,?,?,?)", (tid, idem_key, memo, ts))
        db.x("INSERT INTO ledger(txn_id,account,debit,credit,memo,ts) VALUES(?,?,?,0,?,?)", (tid, src, amount, memo, ts))
        db.x("INSERT INTO ledger(txn_id,account,debit,credit,memo,ts) VALUES(?,?,0,?,?,?)", (tid, dst, amount, memo, ts))
        audit.append(task_id, "LEDGER_TXN", {"txn_id": tid, "src": src, "dst": dst, "amount": amount, "memo": memo})
        return {"txn_id": tid, "duplicate": False}

def fund(account: str, amount: int, key: str):
    return transfer(MINT, account, amount, key, "demo_credit_issue")

def hold(contract_id, user, price, task_id):
    return transfer(user, f"escrow:{contract_id}", gross(price), f"hold:{contract_id}", "escrow_hold", task_id)

def release(contract_id, provider, price, task_id):
    """Atomic: state guard HELD->RELEASED and both payouts in one DB transaction. A second call is a no-op/error."""
    with db.tx():
        n = db.x("UPDATE contracts SET state='RELEASED' WHERE id=? AND state='HELD'", (contract_id,)).rowcount
        if n != 1: raise LedgerError("contract_not_in_HELD_state")
        transfer(f"escrow:{contract_id}", f"agent:{provider}", price, f"release:{contract_id}:provider", "escrow_release", task_id)
        transfer(f"escrow:{contract_id}", PLATFORM, fee(price), f"release:{contract_id}:fee", "platform_fee", task_id)

def refund(contract_id, user, price, task_id):
    with db.tx():
        n = db.x("UPDATE contracts SET state='REFUNDED' WHERE id=? AND state='HELD'", (contract_id,)).rowcount
        if n != 1: raise LedgerError("contract_not_in_HELD_state")
        transfer(f"escrow:{contract_id}", user, gross(price), f"refund:{contract_id}", "escrow_refund", task_id)

def invariants() -> dict:
    t = db.q1("SELECT COALESCE(SUM(debit),0) d, COALESCE(SUM(credit),0) c FROM ledger")
    neg = [r for r in db.q("SELECT account, SUM(credit)-SUM(debit) b FROM ledger GROUP BY account HAVING b<0") if r["account"] != MINT]
    orphan = db.q("""SELECT c.id FROM contracts c WHERE c.state!='HELD' AND
        (SELECT COALESCE(SUM(credit)-SUM(debit),0) FROM ledger WHERE account='escrow:'||c.id)!=0""")
    return {"balanced": t["d"] == t["c"], "total_debit": t["d"], "total_credit": t["c"],
            "negative_accounts": neg, "unsettled_escrow_after_close": [o["id"] for o in orphan],
            "ok": t["d"] == t["c"] and not neg and not orphan}

def balances() -> dict:
    return {r["account"]: r["b"] for r in db.q("SELECT account, SUM(credit)-SUM(debit) b FROM ledger GROUP BY account ORDER BY account")}

SLASHED_POOL = "platform:slashed"
DEFAULT_BOND_PAISE = 500     # Rs 5.00 provider registration bond
DEFAULT_SLASH_PAISE = 100    # Rs 1.00 slashed per failed verification verdict

def stake_bond(agent_id: str, amount: int = DEFAULT_BOND_PAISE) -> dict:
    """Idempotent registration stake: re-registration heartbeats never double-fund."""
    return transfer(MINT, f"bond:{agent_id}", amount, f"bond_stake:{agent_id}", "provider_bond_stake")

def slash_bond(contract_id: str, agent_id: str, amount: int = DEFAULT_SLASH_PAISE, task_id=None) -> int:
    """Deterministically slashes up to `amount` paise from bond:<agent_id> on a failed verification verdict."""
    with db.tx():
        avail = balance(f"bond:{agent_id}")
        slash_amt = min(avail, amount)
        if slash_amt <= 0:
            return 0
        transfer(f"bond:{agent_id}", SLASHED_POOL, slash_amt, f"slash:{contract_id}", "verifier_fraud_slash", task_id)
        return slash_amt
