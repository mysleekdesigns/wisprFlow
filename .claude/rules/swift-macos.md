---
paths:
  - "**/*.swift"
---

# Swift & macOS conventions (VoiceInk fork)

This is a **fork** of VoiceInk. Match the surrounding code's style, naming, and structure over any
personal preference, and keep diffs small and localized so upstream rebases stay easy.

## Language
- No force-unwrap (`!`), `try!`, or `as!` on values that can be nil/throw/mismatch. Use `guard let`,
  `if let`, `try?`/`do-catch`, and conditional casts.
- Prefer `let` over `var`; prefer value types; keep functions focused.
- Handle errors explicitly — don't swallow them with empty `catch {}`.

## Concurrency (this app is concurrency-heavy: audio + ASR + HTTP + UI)
- Touch UI/AppKit/`@Published` state on the main actor (`@MainActor` or `DispatchQueue.main`).
- Do audio capture, ASR, and Ollama HTTP off the main thread; hop back to main for UI/state.
- Prefer `async/await` and actors for shared mutable state; avoid unguarded shared state.
- Capture `[weak self]` in escaping closures, `Task`s, timers, and notification observers.

## macOS specifics
- Global hotkeys go through the `KeyboardShortcuts` package (reuse the existing pattern).
- Text injection for the terminal profile is **type-out mode (CGEvent per-character)** — never route
  terminal output through `NSPasteboard`/clipboard paste.
- Gate injection on `AXIsProcessTrusted()`; gate recording on microphone authorization. Degrade
  gracefully when a permission is missing.
- Guard newer APIs with availability checks; the deployment target is macOS 14.4+.

## Local-only invariant
No network calls to non-localhost hosts. The Ollama client stays on `http://localhost:11434`. Never
add a cloud ASR/LLM dependency — the whole pipeline must work in airplane mode.

## Fork hygiene
- Preserve existing **GPL v3** license headers; add them to new files if the fork uses them.
- Don't reformat or refactor upstream code you aren't functionally changing.
