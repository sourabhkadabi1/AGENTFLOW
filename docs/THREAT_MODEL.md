# Threat model (what is defended, what is not)

| Threat | Defence | Status |
|---|---|---|
| Impersonating a buyer/provider | Ed25519 per agent, id bound to first-seen key (409 on rebind) | Done, tested |
| Replay of a signed request | Timestamp window 30s + per-agent nonce cache | Done, tested |
| Body/path tampering in transit | Signature covers method, path, timestamp, nonce, SHA-256(body) | Done, tested |
| Forged provider response | Responses signed and verified by buyer | Done |
| Provider fabricates output | Verifier recomputes from input; fails closed | Done for 3 capabilities, tested |
| Provider takes money and hangs | Escrow; execution timeout; refund; re-bid | Done, tested |
| Double payment / double refund | Idempotency keys + atomic state guard | Done, tested |
| Overspend | Hard stage budgets with reserve for later stages; budget pre-check | Done, tested |
| Buyer crash leaves funds locked | Startup orphan refund | Done, tested |
| Tampering with history | Hash chain + ledger reconciliation | Detects only if head hash is held externally |
| Registration spam / Sybil reputation reset | Registration token only | **NOT solved** (bond + probation planned) |
| Provider adapts to known verifier checks | None | **NOT solved**; verifier checks should be partly randomized/secret |
| Colluding provider + verifier | Single verifier owned by operator | **NOT solved** |
| LLM provider invents facts in prose | Every number in `narrative` must exist in verified data (`narrative_numbers_grounded`); text never reaches another LLM | Done, tested (numbers only; qualitative claims are NOT checked) |
| Public hosting abuse | `MAX_CONCURRENT_TASKS` cap, non-default tokens, `DEMO_MODE=0` | Done; no per-IP rate limiting |
| Prompt injection via provider output | Output never reaches an LLM; schema validation | Holds today; re-check if you add LLM consumers |
| Admin/demo endpoints in production | `DEMO_MODE=0` disables them; tokens from env | Change default tokens before any public deployment |
