# Known limitations (read before presenting)
1. Simulated credits; no payment rail, KYC or compliance.
2. Providers are ours. Cheating modes are the ones the verifier was written against; the benchmark shows the mechanism works, not that it is unbeatable.
3. Sybil/cold start unsolved (new identity = neutral reputation).
4. Hash chain is single-operator tamper-evidence; publish head hashes externally for real value.
5. Verifier ground truth (star ratings) exists only because this task has labels. Tasks without ground truth need redundancy (multiple providers, cross-checks) or human sampling.
6. Synthetic dataset and co-designed lexicon make honest providers near-perfect; real data needs threshold calibration and probably an LLM-backed provider.
7. SQLite + global lock; no concurrency or scale claims. Buyer/verifier share the gateway process.
8. Intermittent task failures seen during development were traced to **orphaned provider processes from earlier runs** (a provider hung in `timeout` mode outlived its stack, kept its port with stale keys, and answered with 401s). Fixed: bounded shutdown, port checks in `run_all.sh`/tests/doctor, `stop_all.sh`, orphan self-exit. Verified: 3 back-to-back full-suite runs and 10 concurrent cold-start tasks. I also added health-check hysteresis and a one-retry grace on empty bids as defence in depth; those were not individually shown to be necessary.
9. Dashboard verified by JS syntax check and live endpoints, not visually in a browser. Open it and look before you rely on it.
10. The Gemini integration is tested only against a local mock of the REST API, never the real service (no key here). Model names change; run `scripts/check_gemini.py`.
11. Hosting instructions (tunnel, Caddy) are untested: no deployment was possible from this environment.
