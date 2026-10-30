#!/usr/bin/env bash
# Stops every AgentFlow process, including strays from earlier runs. Safe to run any time.
PATS=("[u]vicorn gateway.main" "[p]roviders.provider_app")
for pat in "${PATS[@]}"; do pkill -f "$pat" 2>/dev/null; done
sleep 1.5
for pat in "${PATS[@]}"; do pkill -9 -f "$pat" 2>/dev/null; done
sleep 0.5; echo "stopped. AgentFlow processes remaining: $(pgrep -fc '[p]roviders.provider_app|[u]vicorn gateway.main')"
