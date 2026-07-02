#!/usr/bin/env bash
# PostToolUse (Edit|Write|MultiEdit) hook — format an edited Swift file if a formatter is installed.
# Always exits 0; formatting is best-effort and never blocks.
input=$(cat)

if command -v jq >/dev/null 2>&1; then
  fp=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
elif command -v python3 >/dev/null 2>&1; then
  fp=$(printf '%s' "$input" | python3 -c 'import sys,json
try:
    print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))
except Exception:
    print("")' 2>/dev/null)
else
  exit 0
fi

[ -z "$fp" ] && exit 0
case "$fp" in *.swift) ;; *) exit 0 ;; esac
[ -f "$fp" ] || exit 0

if command -v swiftformat >/dev/null 2>&1; then
  swiftformat "$fp" >/dev/null 2>&1 || true
elif command -v swift-format >/dev/null 2>&1; then
  swift-format --in-place "$fp" >/dev/null 2>&1 || true
fi

exit 0
