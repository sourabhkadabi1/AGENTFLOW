---
name: harden-verifier
description: Use when improving gateway/verifier.py or when a provider output slipped through. Writes the cheating provider first, then the check that catches it.
---
# Harden the verifier (adversarial loop)
1. Write the cheat as a new provider mode (e.g. copies the input back, echoes ratings, pads with plausible text, returns correct structure with empty content).
2. Add a failing test in tests/test_unit.py showing the verifier currently ACCEPTS it.
3. Add the minimal deterministic check. Prefer ground truth derived from the task input (counts, ids, ratings, recomputation) over thresholds.
4. Confirm honest providers still pass (false rejections hurt honest agents' reputation and are as bad as false accepts).
5. Document the new check in docs/THREAT_MODEL.md. Never loosen a check to make a test pass without writing down why.
