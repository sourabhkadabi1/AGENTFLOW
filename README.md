# AGENTFLOW

Autonomous agents discover, bid, negotiate, verify and pay each other. **Payment is released only after an independent verifier approves the work.** A failed provider triggers refund, re-bid and retry inside a hard budget. Simulated credits only; no real money moves.

**Start here: `docs/FINAL_RUNBOOK.md`** (step-by-step: run, test, Antigravity, Gemini, hosting, demo day, troubleshooting).

## Run (2 minutes)
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python scripts/doctor.py            # must say READY
./scripts/run_all.sh                # gateway :8000 + 7 separate provider processes (WITH_LLM=1 adds a Gemini-backed 8th)
./scripts/stop_all.sh               # stops everything, including strays
open http://127.0.0.1:8000          # dashboard; press "Run task"
python -m pytest tests -q           # 38 tests, starts its own stack
python scripts/benchmark.py 8       # AgentFlow vs two cheapest-price baselines
python scripts/demo_cli.py          # terminal fallback demo
```
Optional Gemini: `export GEMINI_API_KEY=...; python scripts/check_gemini.py` (finds a working model name). Everything works without it.

## What is real
| Piece | Implementation | Verified by |
|---|---|---|
| Agent identity | Ed25519 keypair per agent; every request AND response signed with timestamp + nonce; replay/forgery/impersonation rejected | tests 02, 03, unit signing |
| Discovery | Registry of signed-in manifests, health checks, verified reliability per capability | integration 01, 05 |
| Bidding | RFQ to all providers in parallel; hard constraints (budget, deadline, identity, reliability floor) THEN score `S = wR·R − wC·C − wT·T`; full breakdown logged | unit scoring, integration 06 |
| Negotiation | Bounded (2 rounds), provider has private price floor | integration 04 |
| Escrow + ledger | Double-entry integer paise, idempotency keys, no overdraft, atomic HELD→RELEASED/REFUNDED, crash recovery | 7 unit tests |
| Verification | Deterministic, fail-closed, ground truth from task input (ids, ratings, recounts, exact report numbers) | 3 unit tests incl. subtle cheats |
| Learning | Beta(2,2) prior with decay, updated ONLY from verdicts; claims ignored | integration 05, 06 |
| Audit | SHA-256 hash chain + ledger reconciliation against it; tamper demo | unit audit, integration 13 |

## What is NOT real (say this before a judge asks)
Settlement is an internal credits ledger. Providers are our own processes (3 of 7 are deliberately cheating). Dataset is synthetic unless you load a CSV (`scripts/load_reviews.py`). The buyer and verifier run inside the gateway process (own keys, but one process). The hash chain is tamper-EVIDENT, not tamper-proof (the operator can rewrite everything unless the head hash is published). See docs/LIMITATIONS.md.

## Docs
`docs/PLAN_24H.md` timeline and ownership · `docs/DEMO_SCRIPT.md` · `docs/JUDGE_QA.md` · `docs/DECK_FIXES.md` (your deck currently over-claims in places) · `docs/THREAT_MODEL.md` · `docs/API_CONTRACT.md` · `docs/BENCHMARK.md` · `docs/LIMITATIONS.md`

## Antigravity setup
See `docs/FINAL_RUNBOOK.md` Part 3. Open this folder as the workspace; `AGENTS.md`/`GEMINI.md` and `.agents/` (rules, 6 skills, 3 workflows) load automatically. Older Antigravity versions use `.agent/`: `./scripts/link_antigravity.sh old`. No plugins or MCP servers are required. Integrity note: check your hackathon's rules on AI-assisted code and disclose it if required; every teammate must be able to explain every module.
