# API contract (gateway :8000)
Auth: user endpoints `x-api-key`; admin/demo `x-admin-token`; provider registration signed (Ed25519) + `registration_token`.
| Method | Path | Notes |
|---|---|---|
| POST | /registry/register | provider self-registration, signed; 409 if id bound to another key |
| GET | /registry/agents, /registry/agents/{id}, /registry/discover?capability= | verified vs claimed reliability |
| POST | /tasks | `{goal,budget_inr,priority:balanced|reliability|cost,mode:agentflow|cheapest_verified|naive,n_reviews,seed,reviews?}`; `Idempotency-Key` header; 429 when `MAX_CONCURRENT_TASKS` is reached; 10-3000 `reviews` of `{id,text,rating1-5}` |
| GET | /tasks, /tasks/{id} | status, spent, wasted, contracts |
| GET | /ledger/balances, /ledger/verify | invariants + reconciliation with audit |
| GET | /audit?task_id=, /audit/verify, /stream (SSE, `?since=`) | hash-chained events |
| GET | /metrics, /benchmark, /config | `/config` tells the dashboard whether dev tokens are active and whether Gemini is on |
| POST | /demo/inject, /demo/tamper, /demo/reset | DEMO_MODE only, admin token |
Provider (each :910x, all signed both directions): `GET /health`, `POST /rfq`, `/counter`, `/accept`, `/execute`, `/admin/mode`.
Event types: TASK_CREATED PLAN STAGE_START DISCOVERED BID BID_REJECTED BID_DROPPED BID_SCORED COUNTER NEGOTIATED CONTRACT DELIVERY VERDICT SETTLED REFUNDED PAID_WITHOUT_VERIFICATION TASK_COMPLETED TASK_FAILED LEDGER_TXN AGENT_REGISTERED FAILURE_INJECTED ORPHAN_REFUNDED NO_ELIGIBLE_BID_RETRYING. Provider modes: honest fabricate random garbage timeout hallucinate.
Money: integer paise. 1 ₹ = 100. Fee 5% added on top of quote (`common/domain.gross`).
