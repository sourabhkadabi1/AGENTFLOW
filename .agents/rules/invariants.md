---
trigger: always_on
---
Read AGENTS.md first. Hard rules: (1) never let an LLM move money or decide verdicts; (2) all money goes through gateway/ledger.py; (3) verifier fails closed; (4) reputation only from verifier verdicts; (5) full test suite must pass before declaring done; (6) never claim real payments; (7) stop stacks only with ./scripts/stop_all.sh, never `pkill -f` with text from your own command, and never start a second stack on busy ports; (8) do not add heavy frameworks or new infrastructure.
