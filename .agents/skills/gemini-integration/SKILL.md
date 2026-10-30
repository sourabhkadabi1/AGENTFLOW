---
name: gemini-integration
description: Use when connecting, testing, changing or debugging the Gemini API (goal interpretation, the GemReport LLM provider, model names, 404 or key errors, hallucinated numbers). Keeps the LLM away from money and verdicts.
---
# Gemini integration (already built: do NOT rebuild it)
Existing pieces: `common/gemini.py` (REST client, header auth, returns None on ANY failure), `gateway/llm.py` (goal interpretation + fallback), `providers/provider_app.py` `narrative()` + profile `gemreport` (WITH_LLM=1), `gateway/verifier.py` narrative grounding check, `scripts/check_gemini.py`, tests in `tests/test_gemini_and_hosting.py` (local mock server).
## Rules
1. LLM output is untrusted. Any number an LLM states must be checked against verified data (`narrative_numbers_grounded`). If you add a new LLM-written field, add a deterministic check for it FIRST.
2. LLM never touches money, bids, deadlines, balances, verdicts or reputation.
3. Every call must have a fallback: no key, timeout, 404 or garbage JSON => deterministic path. Never let a Gemini outage fail a task.
4. API key only via env `GEMINI_API_KEY`, sent in the `x-goog-api-key` header. Never in a URL, log, dashboard, audit event or commit.
## Procedure
- Key/model problems: run `python scripts/check_gemini.py`. It lists models for the key, skips ones that 404, and prints the `GEMINI_MODEL` to export. Model names change; do not hard-code a new one without running it.
- After any change: `python -m pytest tests/test_gemini_and_hosting.py -q` then the full suite.
- Demo the safety property: dashboard -> set GemReport to `hallucinate` -> run with the other report providers set to `garbage` -> verifier rejects "73%" and the user is refunded.
