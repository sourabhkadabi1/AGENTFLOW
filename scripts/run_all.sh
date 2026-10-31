#!/usr/bin/env bash
# Starts gateway + 12 provider agents (+ GemReport if WITH_LLM=1) as separate processes. Ctrl-C stops all. Fresh DB unless KEEP_DB=1.
cd "$(dirname "$0")/.."
export AGENTFLOW_DB=${AGENTFLOW_DB:-agentflow.db}; export GATEWAY_URL=${GATEWAY_URL:-http://127.0.0.1:8000}
PY=${PYTHON:-python3}
PORTS="8000 9101 9102 9103 9104 9105 9106 9107 9201 9202 9203 9204 9205"; [ "$WITH_LLM" = "1" ] && PORTS="$PORTS 9108"
for p in $PORTS; do
  if (exec 3<>/dev/tcp/127.0.0.1/$p) 2>/dev/null; then echo "ERROR: port $p is already in use (stale AgentFlow stack?). Run ./scripts/stop_all.sh first." >&2; exit 1; fi
done
[ "$KEEP_DB" = "1" ] || rm -f "$AGENTFLOW_DB" "$AGENTFLOW_DB-wal" "$AGENTFLOW_DB-shm"
PIDS=()
cleanup() { trap - EXIT INT TERM; for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; sleep 1.5; for p in "${PIDS[@]}"; do kill -9 "$p" 2>/dev/null; done; }
trap cleanup EXIT INT TERM
start() { "$@" & PIDS+=($!); }
start $PY -m uvicorn gateway.main:app --host 127.0.0.1 --port 8000 --log-level warning --timeout-graceful-shutdown 2
sleep 1.5
for p in cleanco quickclean sentipro bargainsent slowsent reportwriter cheapreport codeparser fastparse bugfinder cheapscanner auditwriter; do start env PROFILE=$p $PY -m providers.provider_app; done
[ "$WITH_LLM" = "1" ] && start env PROFILE=gemreport $PY -m providers.provider_app
echo "AgentFlow up -> http://127.0.0.1:8000   (Ctrl-C to stop)"; wait
