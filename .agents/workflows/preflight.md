---
description: Run all checks before committing or presenting
---
1. Stop any running stack with `./scripts/stop_all.sh` (never `pkill -f` with text from your own command), then `python scripts/doctor.py` must say READY.
2. Run `python -m pytest tests -q` and require 100% green.
3. Start `./scripts/run_all.sh`, run `python scripts/demo_cli.py`, then GET /ledger/verify and /audit/verify and require ok.
4. Run `python scripts/benchmark.py 8`, regenerate docs/BENCHMARK.md numbers, and flag any claim in the deck that the numbers no longer support.
