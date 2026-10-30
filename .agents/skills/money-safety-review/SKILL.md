---
name: money-safety-review
description: Use when a change touches gateway/ledger.py, gateway/orchestrator.py settlement paths, contracts, escrow, refunds, or idempotency. Performs a strict adversarial review for double-pay, stuck escrow, overdraft and race conditions.
---
# Money safety review
For every changed line that moves or reserves credits, answer in writing:
1. What is the idempotency key, and what happens if this exact call runs twice? (must be a no-op)
2. Can the contract state change without the matching ledger rows, or vice versa? (must be one DB transaction)
3. If the process dies on every line between hold and settle, is the escrow recovered? (`orchestrator.recover_orphans`)
4. Can any account except `system:mint` go negative?
5. Is the amount an integer, positive, and checked against the contract price (+fee), not a value supplied by a provider?
6. Does the audit log record it, and does `audit.reconcile_ledger()` still pass?
Then add or extend a test in tests/test_unit.py proving each answer. Run `python -m pytest tests -q`. Report PASS/FAIL per question; do not summarize away a FAIL.
