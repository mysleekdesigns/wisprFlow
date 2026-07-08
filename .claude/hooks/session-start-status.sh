#!/usr/bin/env bash
# SessionStart hook — print local voice-pipeline environment status as context for Claude.
# Always exits 0; stdout is added to the session context.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

echo "## wisprFlow environment status"

# Ollama (local LLM cleanup layer)
if curl -s -m 1 http://localhost:11434/api/tags >/dev/null 2>&1; then
  if command -v jq >/dev/null 2>&1; then
    models=$(curl -s -m 1 http://localhost:11434/api/tags 2>/dev/null \
      | jq -r '[.models[].name] | join(", ")' 2>/dev/null)
  fi
  echo "- Ollama: running${models:+ (models: $models)}"
else
  echo "- Ollama: NOT running — start with 'ollama serve'. Raw ASR still works; cleanup layer won't."
fi

# VoiceInk fork presence
if ls -d "$PROJECT_DIR"/*.xcodeproj >/dev/null 2>&1 \
   || ls -d "$PROJECT_DIR"/*/*.xcodeproj >/dev/null 2>&1 \
   || ls -d "$PROJECT_DIR"/*.xcworkspace >/dev/null 2>&1 \
   || [ -f "$PROJECT_DIR/Package.swift" ]; then
  echo "- VoiceInk fork: present"
else
  echo "- VoiceInk fork: NOT cloned yet — run /voiceink-setup to start Phase 0/1."
fi

# Xcode toolchain
if command -v xcodebuild >/dev/null 2>&1; then
  echo "- Xcode: $(xcodebuild -version 2>/dev/null | head -1)"
else
  echo "- Xcode: not found on PATH — install Xcode (PRD Phase 0)."
fi

exit 0
