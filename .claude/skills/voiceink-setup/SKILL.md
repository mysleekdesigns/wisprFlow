---
name: voiceink-setup
description: Set up and build the VoiceInk fork — clone it, resolve SwiftPM deps, build in Xcode, grant Microphone/Accessibility permissions, download an ASR model, set the global hotkey, and validate the raw hotkey→speech→text loop with no AI layer. Use when starting the project, doing Phase 0/1 environment setup, or when the build/environment needs (re)verifying.
when_to_use: starting the project, cloning VoiceInk, setting up Xcode/Ollama, "get the base building", validating the raw dictation loop
allowed-tools: Read, Grep, Glob, Bash
---

# VoiceInk fork setup (PRD Phase 0–1)

Goal: get the base VoiceInk app building and prove the **raw** loop (hotkey → speak → text appears in
TextEdit) before any AI layer. Local-only from the start.

## Phase 0 — prerequisites
- Install **Xcode** (latest) and **Homebrew**. Confirm: `xcodebuild -version`.
- Install and start **Ollama**, then pull the cleanup model:
  ```
  brew install ollama            # or the official installer
  ollama serve                   # leave running (or use the menu-bar app)
  ollama pull llama3.2:3b
  ollama run llama3.2:3b "say hi"   # must respond
  ```
- Have a working **Claude Code** session in a terminal (Terminal.app / iTerm2 / Ghostty / VS Code).
- (Optional) `brew install --cask voiceink` to trial the shipped app and confirm target UX.

## Phase 1 — fork, build, validate the RAW loop
1. Fork **Beingpax/VoiceInk** on GitHub, then clone your fork into this repo directory.
2. Read the fork's `BUILDING.md`. Open the `.xcodeproj`/`.xcworkspace` in Xcode.
3. Let **SwiftPM** resolve dependencies: KeyboardShortcuts, whisper.cpp, FluidAudio,
   MediaRemoteAdapter. If resolution stalls, hand off to the `build-doctor` subagent.
4. Build & run (⌘R).
5. Grant **Microphone** and **Accessibility** permissions when prompted (see `/macos-permissions`).
6. Download an ASR model in-app and set the global hotkey (see `/asr-config`).
7. **Raw-loop test in TextEdit:** hold the hotkey, speak a sentence, release → text appears. No AI
   cleanup yet. If nothing types, check Accessibility; if nothing records, check Microphone.

## After the raw loop works
- Wire the cleanup layer → `/ollama-cleanup` (Phase 2).
- Build the Claude Code terminal profile → `/terminal-injection` (Phase 3).
- Map the code you'll customize → delegate to the `voiceink-explorer` subagent, then record exact
  file paths in `CLAUDE.md` / PRD §8.

## Notes
- This is a **GPL v3 fork** — keep it minimal and rebase-friendly.
- Everything must run offline; never swap in a cloud ASR/LLM.
