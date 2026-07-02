#!/usr/bin/env bash
# PreToolUse (Edit|Write|MultiEdit) hook — block edits to secret / credential files.
# Exit 2 blocks the tool call and returns the stderr message to Claude.
input=$(cat)

# Extract the target file path from the tool input (jq preferred, python3 fallback).
if command -v jq >/dev/null 2>&1; then
  fp=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
elif command -v python3 >/dev/null 2>&1; then
  fp=$(printf '%s' "$input" | python3 -c 'import sys,json
try:
    ti=json.load(sys.stdin).get("tool_input",{})
    print(ti.get("file_path") or ti.get("path") or "")
except Exception:
    print("")' 2>/dev/null)
else
  exit 0   # cannot parse input; fail open (these files are also git-ignored)
fi

[ -z "$fp" ] && exit 0
base=$(basename "$fp")

# Explicitly allow the checked-in example env template.
[ "$base" = ".env.example" ] && exit 0

# Block edits inside a .git directory.
case "$fp" in
  */.git/*|.git/*)
    echo "Blocked: refusing to edit inside .git/." >&2
    exit 2 ;;
esac

# Block secret / credential files.
case "$base" in
  .env|.env.*|.mcp.json|*.pem|*.key|id_rsa|id_rsa.*|id_ed25519|id_ed25519.*|*.p12|*.keychain)
    echo "Blocked: '$base' holds secrets/credentials and is git-ignored (crawlforge/Google keys, etc.). Do not edit, print, or commit it. If a change is truly required, ask the user to edit it manually." >&2
    exit 2 ;;
esac

exit 0
