# 24-hour plan (4 people). The code runs from hour 0, so the work is understanding, hardening, and rehearsing, not building from scratch.

**Freeze rule: no new features after H18. H18-H24 = rehearse, record backup video, fix deck.**

| Hours | A: Backend/settlement | B: Agents/AI | C: Frontend/demo | D: Testing/deck/pitch |
|---|---|---|---|---|
| 0-2 | Run stack, read ledger.py + orchestrator.py until you can explain every line | Read providers/ + verifier.py; read scoring.py | Run dashboard, list UX gaps | Run full tests + benchmark; read THREAT_MODEL + JUDGE_QA |
| 2-8 | **Sybil defence**: provider bond (stake credits at registration, slashed on fraud verdicts) + probation (new agents get capped job size) | Gemini is already integrated (GemReport): run it with a real key (FINAL_RUNBOOK Part 4), then add a Gemini-backed SENTIMENT provider with its own verifier check | Polish dashboard: per-task timeline view, contract detail drawer, mobile layout; screenshot-test | Fix every item in DECK_FIXES; fill team slide; calibrate with real CSV (`load_reviews.py`) |
| 8-14 | Publish audit head hash (shown on dashboard + printed on slide) so tampering is detectable by outsiders | `harden-verifier` skill: add 2 new cheat modes + checks | Failure-injection UX; "cheapest-only vs AgentFlow" side-by-side run button | Write 10 more tests from JUDGE_QA attacks; 3 full rehearsals |
| 14-18 | Load test (20 concurrent tasks), fix whatever breaks | Tune thresholds on real data | Dark/light, empty states, errors | Record backup video of the full demo |
| 18-24 | Freeze. Only bug fixes with a test | Freeze | Freeze | Rehearse x5 with a timer, Q&A drills, sleep in shifts |

Start with docs/FINAL_RUNBOOK.md Parts 1-3 in the first 2 hours.

Cut list if you fall behind (cut in this order): Gemini sentiment provider, side-by-side run, load test, sybil bond. Never cut: tests, rehearsal, backup video, DECK_FIXES.
