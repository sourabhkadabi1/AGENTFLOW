# AGENTFLOW: project rules for any coding agent

AgentFlow is a trust-aware autonomous service marketplace for the "M2M coordination / agent identity / discovery / micro-settlement" hackathon track.
Loop: Discover -> Bid -> Negotiate -> Contract+Escrow -> Execute -> Verify -> Settle -> Learn. Money is SIMULATED credits (integer paise). Never claim otherwise.

## Commands
- Run everything: `./scripts/run_all.sh` (gateway :8000 + 7 provider processes :9101-9107). Dashboard at http://127.0.0.1:8000
- Unit tests (no network): `python -m pytest tests/test_unit.py -q`
- Full suite (starts its own stack, ~30s): `python -m pytest tests -q`   -> must be 100% green (38 tests) before any commit
- Benchmark: `python scripts/benchmark.py 8`  | Terminal demo: `python scripts/demo_cli.py [agentflow|cheapest_verified|naive]`
- Stop everything: `./scripts/stop_all.sh`   | Pre-flight: `python scripts/doctor.py`   | Gemini key/model check: `python scripts/check_gemini.py`
- Optional LLM provider: `WITH_LLM=1 ./scripts/run_all.sh`
- NEVER run `pkill -f` with a pattern that appears in your own command line (it kills your own shell). Use stop_all.sh.
- NEVER start a second stack while one is running (port clash makes an orphan answer with stale keys).

## Hard invariants (violating any of these is a bug, not a trade-off)
1. LLMs never touch money, permissions, deadlines, balances or verdicts. Deterministic code only. LLM = goal interpretation / provider-side generation.
2. Every ledger movement goes through `gateway/ledger.transfer` (idempotency key, no overdraft, double-entry, audit event). No raw INSERT/UPDATE on `ledger`.
3. Contract state moves HELD -> RELEASED|REFUNDED exactly once, atomically with the money (`ledger.release/refund`).
4. Provider output is untrusted. The verifier must FAIL CLOSED: any exception or unexpected shape = fail. Ground truth comes from the task INPUT, never from provider claims.
5. Reputation updates come only from verifier verdicts. `claimed_reliability` is display-only.
6. Every state change worth showing emits `audit.append`. The hash chain must verify (`/audit/verify`) and the ledger must reconcile (`/ledger/verify`).
7. All agent-to-agent calls are Ed25519-signed with timestamp + nonce; responses are signed too.
8. No Kubernetes, blockchain, vector DB or agent framework. They add risk and prove nothing here.

## Style
Python 3.12, type-light, small functions, comments only for WHY. Frontend stays a single dependency-free file `dashboard/index.html`.

## Definition of done for any change
Full test suite green + `/ledger/verify` ok + `/audit/verify` ok after a manual run + docs updated if behaviour changed. Add a test for every bug fixed.
