---
name: add-provider-agent
description: Use to add a new provider agent (honest, cheating, slow or LLM-backed) to the marketplace, or to add a new capability.
---
# Add a provider agent
1. Add an entry to `providers/profiles.py` (unique port, `base_price` and `min_price` in paise, `eta_ms`, `claimed`, `default_mode`).
2. Add the profile name to the loop in `scripts/run_all.sh` and the expected healthy count (7 -> N) in `tests/conftest.py` and `scripts/benchmark.py`.
3. New CAPABILITY? Add its work function in `providers/provider_app.py`, a `_check` function in `gateway/verifier.py` (fail closed, ground truth from input), the pipeline entry in `gateway/llm.py`, and `common/domain.py` constants. A capability without a verifier is not allowed.
4. LLM-backed provider: call the model INSIDE the provider process only. The verifier must still validate structure and facts deterministically; never let the model grade itself.
5. Add a unit test that the honest output passes the verifier and each cheat fails it. Run the full suite and the benchmark; update docs/BENCHMARK.md.
