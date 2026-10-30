# FINAL RUNBOOK: do these in order. Do not skip a checkpoint.

Everything marked **BUILT** already works and is tested. Do not rebuild it. Your job is to run it, connect it, understand it, and extend it without breaking the flow.

| BUILT (don't redo) | Where |
|---|---|
| Gateway, registry, signed identities, escrow ledger, audit chain, verifier | `gateway/`, `common/` |
| 7 provider agents (3 cheat on purpose) + optional 8th Gemini-backed provider | `providers/` |
| Buyer agent: discover, bid, score, negotiate, contract, verify, settle, learn | `gateway/orchestrator.py` |
| Gemini client with fallbacks, model checker | `common/gemini.py`, `scripts/check_gemini.py` |
| Dashboard, terminal demo, CSV loader, benchmark, doctor | `dashboard/`, `scripts/` |
| 38 tests | `tests/` |
| Antigravity rules, 6 skills, 3 workflows | `AGENTS.md`, `GEMINI.md`, `.agents/` |

---
## PART 1. First run (10 minutes, local)
```bash
cd agentflow
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/doctor.py          # CHECKPOINT: last line must say READY
./scripts/run_all.sh              # leave this terminal open
```
Open **http://127.0.0.1:8000**. CHECKPOINT: header pills are green ("audit chain intact", "ledger balanced and reconciled"); the Providers table lists 7 agents.
Press **Run task** (budget 20, Balanced, AgentFlow). CHECKPOINT within ~15s: the tape shows BID → CONTRACT → VERDICT FAIL → REFUNDED → VERDICT PASS → SETTLED, ends with `task complete ... paid for bad work ₹0.00`. Press Run again: it should finish in ~3s with no failures (it learned).
Stop with Ctrl-C. If anything is left running: `./scripts/stop_all.sh`.

If `doctor.py` or `run_all.sh` says a port is busy, you have a stale stack. Run `./scripts/stop_all.sh` (this was the cause of every intermittent failure I chased; see Part 10).

## PART 2. Run the tests (2 minutes)
```bash
python -m pytest tests/test_unit.py -q        # no network, ~1s, 15 tests
python -m pytest tests -q                     # full suite, starts its own stack, ~47s, 38 tests
```
CHECKPOINT: `38 passed`. If a test fails, do NOT continue to later parts. Read Part 10. Never "fix" a test by loosening it without writing down why.

## PART 3. Connect it to Antigravity
1. Antigravity: **File → Add Folder to Workspace…** → select the `agentflow` folder.
2. Antigravity currently reads rules/skills/workflows from **`.agents/`** (plural) and still accepts the older **`.agent/`**; it also reads `AGENTS.md` and `GEMINI.md`. Docs and tutorials disagree between releases, so verify with step 3.
3. **Verify it loaded**: in the agent chat ask: *"List the skills you have available in this workspace and quote the first line of AGENTS.md."* You should see: money-safety-review, add-provider-agent, harden-verifier, demo-rehearsal, gemini-integration, host-and-demo-day. Workflows appear when you type `/` (`/preflight`, `/rehearse`, `/new-provider`).
4. Nothing loaded? Check which layout your version uses: `./scripts/link_antigravity.sh status`. If your Antigravity is older: `./scripts/link_antigravity.sh old`, then `rm -rf .agents`. Keep ONE copy only, or skills load twice.
5. Rules and workflow files have a **12,000-character limit** each. Ours are well under. Keep them under if you edit.
6. Optional global setup (all projects): skills go in `~/.gemini/antigravity/skills/`, global rules in `~/.gemini/GEMINI.md`. Not needed here; workspace scope is safer.
7. **Plugins / MCP servers: none required.** The platform has no external dependency beyond Python. If you want extras, the only ones worth it: a browser-automation skill/MCP (Playwright or Chrome DevTools type) so the agent can screenshot the dashboard. Read its SKILL.md before installing, and never install anything that runs shell commands you haven't read. Do not add agent frameworks, vector DBs or blockchains (rule 8 in AGENTS.md).
8. How to use the agent safely here: always start a task with *"Read AGENTS.md. Run `python -m pytest tests -q` first and tell me the result."* End every task with the same command. A change is done only when it is green.

## PART 4. Gemini API (optional, everything works without it)
What it adds: (a) goal interpretation, (b) **GemReport**, an LLM-backed provider whose prose the verifier fact-checks (every number must exist in the data).
1. Get a free key: Google AI Studio → *Get API key*. Treat it like a password.
2. `export GEMINI_API_KEY=your-key` (never put it in a file you commit; `.env` is git-ignored).
3. `python scripts/check_gemini.py`. CHECKPOINT: it prints `WORKS. Set: export GEMINI_MODEL=<name>`. Google renames and retires models, and `gemini-2.5-flash` returned 404 for new keys in reports from August 2026, so **do not assume a model name; run this**. Then `export GEMINI_MODEL=<that name>`.
4. Start with the extra provider: `WITH_LLM=1 ./scripts/run_all.sh`. CHECKPOINT: Providers table shows **GemReport** (8 providers).
5. Prove it works: `curl -s localhost:8000/config` → `"llm": true`. In the dashboard set *ReportWriter* and *CheapReport* to `garbage`, run a task: it should be hired and paid, and the final report contains a `narrative` with `narrative_source: "gemini"`.
6. Prove the safety property (this is your demo moment): set GemReport to `hallucinate`, run again. The tape shows `verifier: FAIL narrative_numbers_grounded (ungrounded numbers: ['73'])` and a refund. Set everything back to `honest`.
7. Failure behaviour (tested against a mock): wrong key, 404, timeout, rate limit or garbage JSON all fall back to the template narrative / deterministic goal parsing. A Gemini outage cannot fail a task.
8. Not covered: I could not call the real Gemini API from here, only a faithful local mock. Your first real call is the real test. If step 3 fails with 403/400 the key or API access is the problem, not the code.

## PART 5. Add or change agents without breaking the flow
Use the `/new-provider` workflow or the `add-provider-agent` skill. The checklist it enforces:
1. New provider = new entry in `providers/profiles.py` (unique port, prices in **paise**, `min_price` < `base_price`).
2. Add its name to the loop in `scripts/run_all.sh`; update the expected healthy count in `tests/conftest.py`, `scripts/benchmark.py`, `scripts/doctor.py` ports.
3. New **capability** = work function + **verifier check** (fail closed) + pipeline entry. No verifier, no capability.
4. Every provider speaks this contract (all calls Ed25519-signed both ways): `GET /health`, `POST /rfq`, `/counter`, `/accept`, `/execute`. A real external company's API has none of that, so wrap it: write a provider process that implements the five endpoints and calls their API inside `/execute`. The verifier still judges the output. Keep the wrapper's key in `.keys/`.
5. Provider ids are bound to the first public key seen (409 on a different key). To re-key a provider in dev, delete its `.keys/provider-<name>.key` AND reset the DB (`./scripts/run_all.sh` without `KEEP_DB=1`).
6. Run the full suite and `python scripts/benchmark.py 8`, then update `docs/BENCHMARK.md`.
**Never**: write to the `ledger` table directly; change the signing canonical string on one side only; change ports in one file only; let an LLM decide a verdict or a price; skip `audit.append` for a state change.

## PART 6. Use real data instead of synthetic
```bash
python scripts/load_reviews.py reviews.csv --text review_body --rating star_rating --limit 500 --budget 20
```
Needs a text column and a 1-5 star column. **Calibrate before demoing**: the built-in sentiment provider is a simple lexicon tuned on synthetic data. On real reviews it will score lower against star ratings and may be rejected by the verifier (default threshold 0.75). Run once, read the VERDICT detail in the tape, then either lower the threshold (`export SENT_AGREEMENT_MIN=0.65` before `run_all.sh`) or improve the provider. State the dataset and threshold in your pitch. Use ≤500 reviews for a live demo.

## PART 7. Hosting (only if judges ask for a live link)
Tested here: everything locally. **Not tested here**: any deployment below (I could not deploy from this environment). Do a dry run yourself before the event.
**Rules that apply to every option**: only expose port 8000; providers stay on localhost; set real secrets first:
```bash
export USER_API_KEY=$(openssl rand -hex 16) ADMIN_TOKEN=$(openssl rand -hex 16) REGISTRATION_TOKEN=$(openssl rand -hex 16)
export DEMO_MODE=1            # 0 = judges can only watch (inject/tamper/reset disabled)
export MAX_CONCURRENT_TASKS=5 # caps what a crowd can start
```
With non-default tokens the dashboard asks for the user key and admin token on first load (stored per tab). Share the user key with judges if they should run tasks; keep the admin token private.
**Option A, fastest (laptop must stay on and awake):**
`./scripts/run_all.sh` then in another terminal `cloudflared tunnel --url http://127.0.0.1:8000` (or `ngrok http 8000`). Share the printed https URL.
**Option B, a VM (more stable):** copy the folder, `pip install -r requirements.txt`, run `KEEP_DB=1 ./scripts/run_all.sh` under `tmux` or systemd, put Caddy in front:
```
agentflow.yourdomain.com {
    reverse_proxy 127.0.0.1:8000 {
        flush_interval -1      # required: keeps the live /stream tape from being buffered
    }
}
```
**Clock check if agents ever run on different machines**: signatures are rejected if clocks differ by more than 30s (`timestamp_outside_window`). Single-machine setups don't have this problem.
**After deploying**: `curl https://your-url/config`, open the dashboard, run one task, confirm the green pills. Then change nothing.
Hosted ≠ safer: it is a demo with simulated credits and a single-writer SQLite. Don't present it as production.

## PART 8. Demo day
- T-24h: Parts 1-2 on the demo machine. T-12h: Part 4 if using Gemini. T-6h: rehearse with `/rehearse` and `docs/DEMO_SCRIPT.md` until 3 clean runs in a row. T-3h: record the backup video. **T-2h: freeze, no more code changes.**
- T-1h: `./scripts/stop_all.sh`, `./scripts/run_all.sh`, `python -m pytest tests -q`, one full dry run, close everything else on the laptop.
- On stage: fresh stack, fresh DB. If the browser dies: `python scripts/demo_cli.py`. If the machine dies: the video.
- Fix `docs/DECK_FIXES.md` items before submitting the deck.

## PART 9. Order of work if you only have 6 hours
Parts 1, 2, 3, 8 (mandatory) → DECK_FIXES → Part 4 (Gemini) → Part 6 (real data) → Part 7 (hosting). Cut from the end.

## PART 10. Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `ERROR: port N is already in use` | Stale stack from an earlier run | `./scripts/stop_all.sh`, then retry |
| One provider keeps failing with 401 or never bids; tasks fail at a stage | **Orphan provider from an old stack holds the port with old keys.** This was the cause of the intermittent failures I hit (fixed: shutdown no longer hangs, ports are checked, orphans exit after ~1 min) | `./scripts/stop_all.sh`, restart |
| Providers table shows fewer than 7 | Still registering (≤8s) or crashed | wait 10s; check the terminal for tracebacks |
| `BUDGET_INSUFFICIENT` instantly | Budget below the sum of cheapest quotes (≈₹3 incl. fee) | raise the budget |
| HTTP 429 `too_many_running_tasks` | `MAX_CONCURRENT_TASKS` reached | wait, or raise it |
| 401 `timestamp_outside_window` | Clocks differ >30s across machines | sync clocks (NTP) |
| 401 `replayed_nonce` | Same signed request sent twice | expected for replays; never reuse headers |
| Dashboard asks for tokens | You set non-default tokens (intended on a hosted URL) | enter the user key; admin token optional |
| `audit BROKEN` after you clicked Tamper | Intended: that is the demo | click **Reset demo state** |
| `check_gemini.py`: models.list failed | Bad key or API not enabled | create a new key in AI Studio |
| `check_gemini.py`: all candidates fail | Names changed again | pick a name from its printed list, test with curl |
| Sentiment provider rejected on real data | Lexicon vs real language | Part 6 |
| Test fails with "ports in use" | Stale stack | `./scripts/stop_all.sh` |
| Agent changed something and tests fail | It broke an invariant | revert that change; re-ask citing the AGENTS.md rule it broke |
| Your own shell dies when you run `pkill -f` | The pattern appears in your own command | use `./scripts/stop_all.sh`; never write `pkill -f <text from your command>` |
