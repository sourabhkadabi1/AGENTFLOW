---
name: host-and-demo-day
description: Use when preparing a public/hosted demo, a judge-facing link, deployment, tokens, tunnels, reverse proxy, or last-hour checks before presenting.
---
# Hosting and demo-day checklist (read docs/FINAL_RUNBOOK.md part 7 and 8 first)
1. Only the gateway (port 8000) is ever exposed. Providers stay on 127.0.0.1.
2. Before ANY public URL: set non-default `USER_API_KEY`, `ADMIN_TOKEN`, `REGISTRATION_TOKEN` (the dashboard then asks for them instead of embedding them). `python scripts/doctor.py` warns if defaults are in use.
3. Decide the mode: judges only watching => `DEMO_MODE=0` (inject/tamper/reset disabled). You presenting live => `DEMO_MODE=1` plus the admin token kept private.
4. `MAX_CONCURRENT_TASKS` (default 5) stops a crowd from flooding the box.
5. Reverse proxy must not buffer `/stream` (SSE).
6. Always keep: terminal fallback (`python scripts/demo_cli.py`) and a recorded backup video.
7. Never start a second stack on a used port: `./scripts/stop_all.sh` first. `run_all.sh` refuses to start if ports are busy.
8. Last hour: `python -m pytest tests -q` x1, `python scripts/benchmark.py 8` if anything changed, full rehearsal x1, then FREEZE.
