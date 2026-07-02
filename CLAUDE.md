# wisprFlow — local voice input for Claude Code (macOS)

<!-- Maintainer note: this file is loaded into every session. Keep it under ~200 lines and factual. Put procedures in .claude/skills/ and path-specific detail in .claude/rules/. -->

## What this is
A **local, private, offline** voice-dictation tool whose primary purpose is **talking to Claude Code
in the terminal**: hold a hotkey → speak → clean text is *typed* into the Claude Code TUI. It also
works system-wide like Wispr Flow. See `PRD.md` for the full spec.

**Approach (decided, do not re-litigate):** fork **[VoiceInk](https://github.com/Beingpax/VoiceInk)**
(native macOS Swift), run the full local pipeline, and add a dedicated **Claude Code / Terminal
profile**. Native Claude Code `/voice` is rejected because it streams audio to Anthropic's servers.

## The one invariant: 100% local, no network
The entire pipeline must work with **airplane mode on**. Never introduce a cloud ASR or cloud LLM
dependency. Two local models are required: (1) a Whisper-family **ASR** engine for transcription and
(2) a small **Ollama** text model for optional cleanup. Ollama is text-only — it cannot transcribe.

## Pipeline
```
[hotkey down] record mic            KeyboardShortcuts + AVAudioEngine (Microphone permission)
[hotkey up]   local ASR             whisper.cpp (Metal) OR Parakeet-TDT (ANE / FluidAudio)
              optional cleanup       Ollama HTTP @ localhost:11434, small model, light-touch prompt
              inject at cursor       type-out mode (CGEvent per-char)  ← NOT clipboard paste
              [Power Mode profile]   auto-activates for Terminal/iTerm2/Ghostty/VS Code
              [Auto-Send: optional]  press Return to submit (default OFF)
```

## Decided defaults
- **Injection:** type-out (keystroke) mode for the terminal profile. Clipboard paste is reserved for
  normal apps only — it corrupts terminal TUIs and trips the bracketed-paste `00~` bug.
- **ASR:** Parakeet-TDT v3 on Apple Silicon (fastest, English) via FluidAudio; whisper-large-v3-turbo
  for multilingual.
- **Cleanup LLM:** `llama3.2:3b` / `qwen2.5:3b` with a **light-touch** prompt (filler removal +
  punctuation only; never reformat a coding-agent prompt into prose/markdown).
- **Auto-Send:** default **OFF** (multi-line prompts + premature Enter are risky); per-profile toggle.
- **Min OS:** macOS 14.4+.

## Current state
Fork **cloned** at `VoiceInk/` (nested git repo, git-ignored here; remotes: `origin` =
mysleekdesigns/VoiceInk, `upstream` = Beingpax/VoiceInk). Exact `file:line` map recorded in PRD §8.

## Where the work lands (exact paths in PRD §8; fork-root-relative)
- **Injection/output** — ⚠️ upstream has **no type-out mode**; only clipboard Cmd+V
  (`VoiceInk/Paste/CursorPaster.swift`). Adding CGEvent per-char typing is the main Swift work.
- **LLM/enhancement service** — Ollama already integrated (`VoiceInk/Services/OllamaService.swift`,
  endpoint localhost:11434); prompt selection is per-profile (`Modes/ModeRuntimeConfiguration.swift`).
- **Power Mode** — upstream "Modes" system (`VoiceInk/Modes/ModeConfig.swift`): bundle-ID matching,
  auto-activation, per-profile `outputMode` + `autoSendKey` overrides already exist.
- **ASR/model config** — Parakeet TDT v3 already supported (`Transcription/FluidAudio/FluidAudioModelManager.swift`).
- **Hotkey** (KeyboardShortcuts) — reuse as-is (`VoiceInk/Shortcuts/`); toggle/push-to-talk/hybrid built in.

## Build & run
- Preferred: `make local` in `VoiceInk/` — ad-hoc signing, no Apple Developer cert; app lands in
  `~/Downloads/VoiceInk.app`. Or open `VoiceInk.xcodeproj` in Xcode (⌘R). See the fork's `BUILDING.md`.
- whisper.xcframework builds into `~/VoiceInk-Dependencies/whisper.cpp`; its `build-xcframework.sh` is
  **locally patched to macOS-only** (iOS/tvOS/visionOS slices fail without those SDKs and aren't
  needed). `make clean` wipes the deps dir and loses that patch — re-apply if rebuilding from scratch.
- If every compile fails with "No CMAKE_C_COMPILER" / plug-in load errors after an Xcode update, run
  `sudo xcodebuild -runFirstLaunch`.
- `xcodebuild -list` to inspect schemes; delegate noisy builds to the `build-doctor` subagent.
- Grant **Microphone** + **Accessibility** permissions on first run.

## Critical gotchas (see PRD §9)
- **Never** switch the terminal profile to clipboard paste. Type-out mode only.
- **Permissions:** Microphone (`NSMicrophoneUsageDescription` in Info.plist) + **Accessibility**
  (runtime TCC grant, not a plist key) for global hotkey CGEvents + keystroke injection.
- **Auto-submit is the rough edge:** Auto-Send Return works via keystroke; programmatic stdin
  submission to the Claude Code TUI is unreliable (claude-code issue #15553). Default to user pressing
  Enter.
- **Distribution:** App Store rejects Accessibility-API text injection → notarized/direct build only,
  no Mac App Store. Do not add the App Sandbox entitlement (it breaks CGEvent injection).
- **License:** VoiceInk is **GPL v3**. This is a fork — keep license headers; if ever distributed,
  keep GPL and publish source. Keep changes minimal and localized to ease upstream rebases.

## Secrets — do not touch
`.env` and `.mcp.json` are git-ignored and hold credentials (crawlforge/Google keys). Never edit,
print, or commit them. A `PreToolUse` hook blocks edits to them.

## Extensions in this repo
- **Skills** (`.claude/skills/`, run with `/name`): `/voiceink-setup`, `/terminal-injection`,
  `/ollama-cleanup`, `/asr-config`, `/macos-permissions`, `/verify-pipeline`.
- **Subagents** (`.claude/agents/`): `voiceink-explorer` (map the codebase), `swift-reviewer`
  (review Swift/macOS changes), `build-doctor` (build + triage errors).
- **Rules** (`.claude/rules/`): load automatically when you touch matching files.
- **Hooks** (`.claude/settings.json`): env status on start, secret-file protection, Swift auto-format.
