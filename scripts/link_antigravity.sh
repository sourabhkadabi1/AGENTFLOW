#!/usr/bin/env bash
# Puts the Antigravity rules/skills/workflows where YOUR Antigravity version reads them. Run from the project root.
#   ./scripts/link_antigravity.sh status   show what exists
#   ./scripts/link_antigravity.sh old      older Antigravity (.agent/): creates a copy; REMOVE the .agents/ folder afterwards to avoid double loading
#   ./scripts/link_antigravity.sh new      current default (.agents/): removes a stale .agent/ copy if present
cd "$(dirname "$0")/.."
case "$1" in
  status) for d in .agents .agent; do [ -d $d ] && echo "$d: $(find $d -name SKILL.md | wc -l) skills, $(ls $d/workflows 2>/dev/null | wc -l) workflows, $(ls $d/rules 2>/dev/null | wc -l) rules" || echo "$d: absent"; done ;;
  old) [ -d .agents ] || { echo "no .agents/ to copy from"; exit 1; }; rm -rf .agent; cp -r .agents .agent; echo "created .agent/ (copy). Now delete .agents/ so skills are not loaded twice:  rm -rf .agents" ;;
  new) [ -d .agents ] || { [ -d .agent ] && mv .agent .agents || { echo "nothing to link"; exit 1; }; }; rm -rf .agent; echo ".agents/ is the only copy" ;;
  *) echo "usage: $0 status|old|new"; exit 1 ;;
esac
