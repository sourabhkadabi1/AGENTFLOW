---
name: demo-rehearsal
description: Use before any presentation or recording. Runs the preflight checks, the scripted failure-recovery demo, and the tamper-evidence demo, and reports anything that deviates from docs/DEMO_SCRIPT.md.
---
# Demo rehearsal
1. `./scripts/run_all.sh` fresh (no KEEP_DB). Wait for 7 healthy providers on the dashboard.
2. Follow docs/DEMO_SCRIPT.md step by step using the browser, then repeat once with `python scripts/demo_cli.py` as the fallback path.
3. Verify the expected beats happened in order: cheap provider bids and wins, verifier FAIL, refund, re-bid, PASS, SETTLED, second run avoids the cheat, tamper -> chain BROKEN.
4. Report every deviation with the audit seq numbers. Do not present until all beats are reproducible 3 times in a row.
