---
name: terminal-injection
description: The crux of the project — how to inject dictated text into terminal TUIs safely for Claude Code. Covers type-out (CGEvent per-character) mode vs clipboard paste, the bracketed-paste 00~ corruption bug, configuring a Power Mode profile that auto-activates for terminal apps, Auto-Send, and a custom dictionary for dev jargon. Use when working on text injection/output, Power Mode, the Claude Code terminal profile, or debugging garbled/corrupted injected text (Phase 3).
when_to_use: text injection, type-out vs paste, garbled/00~ text in terminal, Power Mode profile, Auto-Send, Claude Code terminal profile, custom dictionary
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Terminal injection for Claude Code (PRD Phase 3)

This is the core reason to fork VoiceInk. Getting clean text into the Claude Code TUI has two failure
modes; both are avoided by **type-out mode**.

## Why type-out, never clipboard paste (in the terminal)
- **Paste corruption:** auto-paste into terminal TUIs mangles text (e.g. Superwhisper corrupted text
  in a Codex terminal).
- **Bracketed paste:** terminals wrap pasted text in `\e[200~ ... \e[201~`; when a TUI doesn't consume
  it you get stray `00~` / `201~` in the input.
- **Fix:** VoiceInk's **type-out (keystroke) mode** injects characters one-by-one via `CGEvent`, which
  sidesteps both. Reserve clipboard paste for normal apps only.

## Build the Claude Code / Terminal Power Mode profile
1. Create a **Power Mode profile** that auto-activates for your terminal app(s): Terminal.app, iTerm2,
   Ghostty, VS Code (match by bundle identifier / frontmost app).
2. Set that profile's injection to **type-out (keystroke) mode**.
3. Give it the **light-touch coding-agent cleanup prompt** (see `/ollama-cleanup`): preserve technical
   terms, file paths, command names, identifiers; no markdown/code fences; no rephrasing.
4. Add a **custom dictionary / word-replacements** for dev jargon Whisper mishears: "Claude Code",
   "npm", "refactor", "SwiftUI", "CGEvent", plus your repo/lib/file names.
5. **Auto-Send:** start **OFF**. Multi-line prompts + a premature Return can send half a prompt. Test
   Return-to-submit separately before enabling per-profile.

## Fallback: if you ever must use paste in the terminal
Programmatic stdin submission to the Claude Code TUI is unreliable (claude-code issue #15553), so
prefer type-out + user-pressed Enter. If paste mode is unavoidable, disable bracketed paste in the
shell:
```
# in ~/.zshrc — clears bracketed-paste mode around claude
claude() { command claude "$@"; printf '\e[?2004l'; }
```

## Where to implement (in the fork)
Use the `voiceink-explorer` subagent to locate the injection/output path and Power Mode matching, then
confirm the terminal profile selects the CGEvent per-character path. Verify end-to-end with
`/verify-pipeline`.
