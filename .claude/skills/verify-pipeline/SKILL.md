---
name: verify-pipeline
description: Run the end-to-end acceptance test for the local voice pipeline — live Claude Code dictation, type-out injection with no corruption, terminal profile auto-activation, custom-vocab correction, Ollama-down fallback, and the airplane-mode offline test. Use to verify the whole flow works, after wiring a phase, or before considering the MVP done (PRD §10).
when_to_use: verify, acceptance test, end-to-end, does it work, airplane mode test, MVP done, offline test, regression check
allowed-tools: Read, Grep, Glob, Bash
---

# End-to-end acceptance verification (PRD §10)

Drive the real flow and observe behavior — don't just build. Work top-down; stop at the first failure
and report it with the observed symptom.

## Pre-flight
- [ ] `ollama run llama3.2:3b "hi"` responds (Ollama up).
- [ ] App builds in Xcode and launches; Microphone + Accessibility granted (`/macos-permissions`).

## Core flow — in a LIVE Claude Code session
- [ ] Focus the terminal running Claude Code. Hold the hotkey and say:
      *"um can you refactor the auth module and add tests"*.
- [ ] Release → the **cleaned** instruction is **typed** into the Claude Code input: no `00~`, no
      corruption, filler removed, ready to send (you press Enter). This is the headline criterion.
- [ ] The **Terminal profile auto-activated** (type-out mode) without manual switching.

## Robustness
- [ ] **Custom vocab:** speak a dev term Whisper usually mishears → the dictionary corrects it.
- [ ] **Ollama independence:** stop Ollama → the **raw** transcript still injects (ASR ⟂ LLM).
- [ ] **Airplane mode:** turn networking OFF → the whole flow still works. This proves 100% local and
      is the project's entire reason to exist (unlike native `/voice`).

## Report
For each item: PASS/FAIL + what you observed. On failure, point to the likely area:
- No text typed / hotkey dead → `/macos-permissions` (Accessibility).
- Garbled or `00~` text → `/terminal-injection` (must be type-out mode, not paste).
- Cleanup wrong/over-formatted → `/ollama-cleanup` (light-touch prompt).
- Slow / wrong transcript → `/asr-config`.
Only report the MVP "done" when the headline criterion **and** the airplane-mode test both pass.
