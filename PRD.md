# PRD — Local Voice Input for Claude Code (macOS)

**Working title:** wisprFlow (local)
**Owner:** Simon
**Status:** Draft / pre-build
**Last updated:** 2026-07-02

---

## 1. Overview

Build a **local, private, offline** voice-dictation tool whose primary purpose is **talking to
Claude Code in the terminal** — hold a hotkey, speak a prompt/instruction, and clean text is typed
straight into the Claude Code TUI. Secondary benefit: it also works system-wide in any app (like
[Wispr Flow](https://wisprflow.ai/)).

**Approach (decided):** fork **[VoiceInk](https://github.com/Beingpax/VoiceInk)** (native macOS
Swift), run the **full local pipeline** (hotkey → local Whisper/Parakeet ASR → local Ollama cleanup
→ inject text at cursor), and add a dedicated **"Claude Code / Terminal" profile**.

---

## 2. Why local, when Claude Code already has voice? (the core justification)

Claude Code shipped a **native `/voice`** command (rolled out March 2026, v2.1.69+). It works — but
**it streams your audio to Anthropic's servers; transcription is NOT done locally.** So if you want
voice input that is **private, offline, free, and never leaves your Mac**, native `/voice` doesn't
qualify. **That gap is exactly this project's reason to exist.**

Two more facts shape the build:
- **Wispr Flow is also 100% cloud** (no offline mode) — so there's no local product to just install; we rebuild it.
- **Ollama is text-only — it cannot do speech-to-text.** A local clone needs **two** local models:
  1. a **Whisper-family ASR engine** (whisper.cpp / Parakeet / MLX) for transcription, and
  2. a **small text LLM via Ollama** for optional cleanup/formatting.

---

## 3. Solution validation — is forking VoiceInk the best fit for *this* goal?

**Yes.** For "local + private voice → Claude Code terminal," VoiceInk uniquely combines everything
out of the box, and — importantly — has features purpose-built for terminal injection:

| Option | Local ASR | Local LLM (Ollama) | Terminal-safe injection | Verdict |
|---|---|---|---|---|
| **Fork VoiceInk** ✅ | whisper.cpp + Parakeet | Yes | **Type-out (keystroke) mode** + per-app **Power Mode** + Auto-Send | **Chosen** |
| Claude Code native `/voice` | ❌ cloud (Anthropic) | ❌ | n/a (built-in) | Fails "local/private" |
| mcp-voice-hooks | ❌ browser Web Speech API | ❌ | via MCP (needs browser open) | Fails "local/Ollama" |
| Talon Voice | (own engine) | ❌ | command-based | Wrong paradigm; steep setup |
| Build from scratch | possible | possible | you'd re-implement all of the above | Slower; user chose "fork" |

**Key terminal-specific reason VoiceInk wins:** clipboard-paste into terminal TUIs is buggy
(Superwhisper's auto-paste corrupted text in a Codex terminal; Claude Code also trips
**bracketed-paste** `00~` issues). VoiceInk's **type-out mode** injects characters one-by-one via
CGEvent, which **avoids both problems**. Its **Power Mode** lets that mode auto-activate only for the
terminal, and **Auto-Send** can press Return to submit the prompt.

---

## 4. Goals / Non-goals

**Goals (MVP)**
- Global push-to-talk hotkey, focused on driving Claude Code in the terminal.
- Fully local ASR (no network) + optional local Ollama cleanup.
- Reliable text injection into terminal TUIs (**type-out mode**, not clipboard paste).
- A dedicated **Claude Code / Terminal profile** (auto-activates when terminal is focused).
- Works with airplane mode on.

**Non-goals (MVP)**
- Windows/Linux (macOS only for now).
- Mac App Store distribution (Accessibility-API policy blocks it — direct/notarized build instead).
- Voice *commands*/navigation (Talon-style). This is dictation of natural-language prompts.
- Fancy per-app formatting for non-terminal apps (nice-to-have, later).

---

## 5. Target architecture

```
[Hotkey down]                         KeyboardShortcuts (global shortcut)
   → record mic                       AVAudioEngine        (Microphone permission)
[Hotkey up]
   → local ASR → raw transcript       whisper.cpp (Metal) OR Parakeet-TDT (Neural Engine / FluidAudio)
   → (optional) LLM cleanup           Ollama HTTP @ localhost:11434, small model, MINIMAL prompt
   → inject at cursor                 **Type-out mode** (CGEvent per-character)  ← not clipboard paste
   [Power Mode: Terminal profile]     auto-activates for Terminal/iTerm2/Ghostty/VS Code
   [Auto-Send: optional Return]       submit the prompt to Claude Code
```

**Recommended defaults**
- **Injection:** **type-out (keystroke) mode** for the terminal profile. Reserve clipboard paste for
  normal apps only.
- **ASR:** Parakeet-TDT v3 on Apple Silicon (fastest, English) via FluidAudio; whisper-large-v3-turbo
  for multilingual.
- **Cleanup LLM:** `llama3.2:3b` / `qwen2.5:3b`, with a **light-touch** prompt (see §7) — for prompts
  *to a coding agent* we want filler removal + punctuation only, NOT reformatting into prose/markdown.
- **Auto-Send:** default **off** initially (multi-line prompts + premature Enter are risky); make it a
  per-profile toggle.
- Min OS: macOS 14.4+.

---

## 6. Phases & checklists

### Phase 0 — Prerequisites & environment
- [x] Install **Xcode** (latest) and **Homebrew**. *(Xcode 26.6, Homebrew 5.1.15)*
- [x] Install **Ollama**; run `ollama serve`; `ollama pull llama3.2:3b`. *(running; `llama3.2:latest` = the 3B default, plus `qwen2.5:3b` available)*
- [x] Verify `ollama run llama3.2:3b "say hi"` responds. *(verified via API 2026-07-02, ~1.8 s incl. model load)*
- [x] Have a working **Claude Code** install in a terminal (Terminal.app / iTerm2 / Ghostty / VS Code).
- [ ] (Optional) `brew install --cask voiceink` to trial the shipped app + confirm target UX.

### Phase 1 — Fork & build the base; validate the RAW loop
- [x] Fork **Beingpax/VoiceInk**; `git clone` your fork into this repo. *(cloned to `VoiceInk/`, `upstream` remote added, 2026-07-02)*
- [x] Follow `BUILDING.md`; open in Xcode; resolve SPM deps (KeyboardShortcuts, whisper.cpp,
      FluidAudio, MediaRemoteAdapter); build & run. *(built via `make local` → `~/Downloads/VoiceInk.app`,
      ad-hoc signed, 2026-07-02; whisper.xcframework patched macOS-only, see CLAUDE.md build notes)*
- [x] Grant **Microphone** + **Accessibility** permissions. *(granted via onboarding 2026-07-08; mic =
      Studio Display. ⚠️ ad-hoc rebuilds invalidate the Accessibility grant — remove with “−” and re-add
      in System Settings, toggling alone isn’t enough)*
- [x] Download an ASR model; set the global hotkey. *(parakeet-tdt-0.6b-v3 on disk at
      `~/Library/Application Support/FluidAudio/Models/`; hotkey = left ⌥, modifier-only, 2026-07-08)*
- [x] **Test raw loop** in TextEdit: hotkey → speak → text appears. (No AI layer yet.) *(passed
      2026-07-08 — left ⌥ hold → speak → release, text pasted at cursor)*

### Phase 2 — Wire the local Ollama cleanup layer
- [x] In AI-enhancement settings: provider = **Ollama**, endpoint `http://localhost:11434`, model = pulled model.
      *(2026-07-08: model = `wispr-cleanup:latest` — see §7 Phase 2 findings; set via AI Models → Local → Ollama row)*
- [x] Add the **light-touch** cleanup prompt (§7). *(2026-07-08: "Light cleanup" prompt on the Dictation
      mode + "Claude Code terminal" prompt created for Phase 3 — both with "Use System Template" OFF;
      cleanup verified live in TextEdit)*
- [x] Test filler-heavy sentence → cleaned output, **fully offline**; confirm cleanup < ~1s. *(2026-07-08:
      live TextEdit test passed; Ollama-down test passed — raw transcript still pastes with warning
      notification; warm cleanup ≈ 0.32 s in harness)*

### Phase 3 — Claude Code / Terminal profile (the core of this project)
- [x] Create a **Power Mode profile** that auto-activates for your terminal app(s). *(2026-07-08:
      "Claude Code" mode — Terminal, iTerm2, Hyper, Ghostty, VS Code; Cursor deliberately excluded.
      Written via `scripts/restore_phase3.py` — see §7 Phase 3 findings. **Reversed 2026-07-08 pm:
      Cursor added** (`com.todesktop.230313mzl4w4u92`) — Phase 4 verify caught Claude Code actually
      running in Cursor's terminal, where dictation silently fell through to the Dictation profile's
      paste path. Trade-off accepted: Cursor's editor panes now get type-out too. Restore script
      updated to match.)*
- [x] Set that profile's injection to **type-out (keystroke) mode** (avoids paste corruption + bracketed-paste bug).
      *(2026-07-08: `.typeOut` output mode added to the fork — commit `853a01d`, branch `wisprflow`;
      5 ms/char, newlines typed as spaces, modifier flags cleared)*
- [x] Give it a **coding-agent enhancement prompt** (§7) — preserve technical terms, file paths, identifiers; no markdown/code fences.
      *(2026-07-08: "Claude Code terminal" prompt, "Use System Template" OFF)*
- [x] Add a **custom dictionary / word-replacements** for dev jargon ("Claude Code", "npm", "refactor", lib/file names Whisper mishears).
      *(2026-07-08: 17 word-replacement rows — Claude Code, JSON, SwiftUI, CGEvent, … via
      `scripts/restore_dictionary.py`)*
- [x] Decide **Auto-Send** per profile (start **off**; test Return-to-submit separately).
      *(2026-07-08: OFF on both modes; Return-to-submit untested — revisit in Phase 4 if wanted)*
- [x] Fallback note: if ever using paste mode in the terminal, add the bracketed-paste guard
      (`claude() { command claude "$@"; printf '\e[?2004l'; }` in shell rc).
      *(documented only — type-out is mandated, guard not installed in `~/.zshrc`)*

### Phase 4 — Polish & optional extensions
- [x] Push-to-talk vs. toggle; start/stop sound; menu-bar status. *(2026-07-08 pm: hotkey stays
      **hybrid** (hold = PTT, tap <0.5 s = hands-free) and start/stop sounds already ON — both
      config-only, nothing to change. **Menu-bar recording-state badge added to the fork**:
      new `Views/MenuBarStatusLabel.swift` + one-line label swap in `VoiceInk.swift` — icon becomes
      ⏺ while recording, a waveform while transcribing/enhancing. Built 17:00 →
      `~/Downloads/VoiceInk.app`, confirmed live. Post-rebuild the hotkey was dead until the
      Accessibility remove/re-add + relaunch — log signature: `[ShortcutMonitor] Failed to install
      global shortcut event tap` at launch.)*
- [x] Tune ASR choice for lowest latency on your machine. *(2026-07-08 pm: kept Parakeet-TDT v3 on
      ANE. Prewarm was already ON (registered default — the earlier "enable it" finding was wrong,
      see §7 correction); log-verified ~0.25 s prewarm at every launch. Measured from history: warm
      ASR **median ≈ 0.13 s**/utterance, cleanup +0.26–0.82 s. Nothing further to tune.)*
- [x] (Optional) Command words ("new line", "send it"), streaming/partial transcripts. *(2026-07-08 pm:
      scoped; "new line" and streaming injection **deferred by decision** per §7 findings. 2026-07-08 eve:
      **"send it" implemented** — trailing-phrase strip in `TranscriptionPipeline` (pre-enhancement, so the
      cleanup LLM never sees it and history stays clean) + one-shot Return in `TranscriptionDelivery`;
      per-mode toggle `isSendItCommandEnabled` (default off, ON for the Claude Code profile; restore script
      updated). Bare "send it" types nothing and submits the already-typed prompt. Whitespace boundary
      rejects "re-send it"/"resend it". 12 unit tests green; live-verified end-to-end via history DB.)*

---

## 7. Reference prompts (Ollama cleanup)

**General (non-terminal apps):**
> You clean up dictated speech. Remove filler words (um, uh, like), fix grammar, punctuation, and
> capitalization. Preserve the speaker's meaning and wording. Output ONLY the cleaned text.

**Claude Code / Terminal profile (light-touch, agent instructions):**
> You clean up a spoken instruction to a coding assistant. Remove filler words and fix punctuation
> and capitalization only. **Do NOT** rephrase, summarize, translate to prose, or add markdown/code
> fences. **Preserve** technical terms, file paths, command names, and identifiers exactly as heard.
> Output ONLY the cleaned instruction.

**Phase 2 findings (2026-07-08, 11-fixture harness × {qwen2.5:3b, llama3.2} × {wrapped, raw} prompts):**
- **Model = `wispr-cleanup`** — derived local model (`FROM qwen2.5:3b` + `PARAMETER temperature 0.2`),
  created with `ollama create wispr-cleanup`; scores **10/11** vs 8–9/11 stock qwen2.5:3b and 5–8/11
  llama3.2. Needed because LLMkit's `OllamaClient.generate()` puts `temperature` at the **top level**
  of the `/api/generate` body where Ollama ignores it (only `options.temperature` counts) — the app's
  intended 0.3 never reaches the model, so we bake 0.2 into the model instead. Zero Swift changes.
- **Prompts: turn OFF "use system instructions"** (toggle in the prompt editor) — VoiceInk's wrapper
  template (`Models/AIPrompts.swift`) degrades small models: llama3.2 obeyed an embedded prompt
  injection (wrote a poem) and once returned the wrapper's own example text; qwen added stray
  newlines. The raw §7 prompts above perform best; do not "improve" them (a verbatim-phrase addition
  made the model reject input outright).
- Residual known-miss (accepted): a dictation *quoting* an instruction-like phrase may get
  re-punctuated so the phrase reads as a separate sentence — safe failure, never hijacked.
- Warm latency ≈ **0.32 s**/cleanup (target < 1 s); Ollama-down ⇒ raw transcript still pastes
  (`TranscriptionPipeline.swift:151,196-208`), worst-case block = 7 s (`EnhancementTimeoutSeconds`).

**Phase 3 findings (2026-07-08, live end-to-end test in Claude Code):**
- **All acceptance checks passed**: core flow (hotkey → cleaned instruction typed char-by-char into
  the Claude Code TUI, no `00~`/corruption, no auto-submit), dictionary correction ("clawed code" →
  "Claude Code"), Ollama-down fallback (raw transcript still types + warning), and the
  **airplane-mode test** — the 100%-local invariant is proven.
- **Type-out mode** = fork commit `853a01d` (branch `wisprflow`): `.typeOut` ModeOutputMode + a
  per-char CGEvent path in `CursorPaster.swift`. Safety details: newlines typed as **spaces** (a real
  Return submits the TUI prompt), modifier flags cleared (a still-held hotkey can't produce Ctrl/Cmd
  control sequences), cancellation-aware, delay clamped (`typeOutCharacterDelay`, default 5 ms/char).
- ⚠️ **In-app config is fragile across rebuilds**: after an ad-hoc rebuild + Accessibility re-grant,
  ALL in-app state (custom prompts, modes, dictionary — Phase 2's prompts included) was found wiped.
  Recreated programmatically: `scripts/restore_phase3.py` (prompts + modes via `defaults`; quit the
  app first) and `scripts/restore_dictionary.py` (word replacements via sqlite). Re-run these if it
  happens again.
- "Claude Code" mode config: outputMode `typeOut`, Auto-Send none, `isTextFormattingEnabled`
  **false** (upstream `ParagraphFormatter` inserts `\n\n` paragraph breaks — unwanted in a terminal),
  prompt "Claude Code terminal", model `wispr-cleanup:latest`, six terminal bundle IDs (Cursor
  added 2026-07-08 pm — see the Phase 3 checklist note).

**Phase 4 prep findings (2026-07-08, read-only fan-out: latency / interaction polish / command words):**
- **Phase 4 is almost entirely config-only.** Hotkey mode (toggle / push-to-talk / hybrid — currently
  **hybrid**: hold = PTT, tap <0.5 s = hands-free; picker in Settings → Shortcuts, logic
  `Shortcuts/RecordingShortcutManager.swift:384-462`, threshold hardcoded at `:359`) and start/stop
  sounds (ON by default, sound5/sound6, `SoundManager.swift:36-49`, Settings → Custom Sounds) both
  exist upstream. Only real gap: the menu-bar icon is static (`VoiceInk.swift:355-362`) — a
  recording-state badge would be a small optional Swift edit reacting to `VoiceInkEngine.recordingState`.
  **Done 2026-07-08 pm:** badge added — new `Views/MenuBarStatusLabel.swift` + one-line label swap in
  `VoiceInk.swift`; swift-reviewer verdict APPROVE-WITH-NITS, both actionable nits applied (fixed
  16 pt symbol size to avoid state-change width jump; idle icon resizes a copy, not the shared
  NSImage cache). Symbols render monochrome/template in the menu bar — intended.
- **Latency: keep Parakeet-TDT v3 on ANE** (already active on both modes; only model on disk; VAD off /
  16 kHz native / greedy decode already optimal). ~~Best win: enable `PrewarmModelOnWake`~~ **Correction
  (2026-07-08 pm):** prewarm is **already ON** — `AppDefaults.swift:64` registers the default `true`
  (registered defaults don't appear in `defaults read`, which is what misled the fan-out agent);
  unified log confirms "Prewarm completed in ~0.25s" on every app launch. **Measured baseline
  (2026-07-08, from the SwiftData history at `~/Library/Application Support/com.prakashjoshipax.VoiceInk/default.store`):**
  14 utterances, warm Parakeet V3 ASR = **median ≈ 0.13 s** (0.10–0.18 s for ≤10 s audio; 0.24 s for a
  40 s utterance); Ollama cleanup adds 0.26–0.82 s when it runs. Nothing further to tune.
- **Command words (all optional):** "send it" **implemented 2026-07-08** (see §6) — detector at
  `Transcription/Processing/SendItCommandDetector.swift`, strip wired into `TranscriptionPipeline`
  after word-replacement / before enhancement, one-shot Return via the existing keystroke path
  (`CursorPaster.performAutoSend` at `CursorPaster.swift:279-300`); empty-remainder delivery skips
  injection entirely (no clipboard clobber in paste modes). "new line" **deferred**: the only terminal-agnostic soft newline
  is backslash+Return (Shift/Option+Return are terminal-keymap-dependent), and every variant posts a
  real Return — a misfire submits the TUI prompt. Streaming injection **deferred** (large): local
  partials already exist (`Transcription/Streaming/FluidAudioStreamingProvider.swift`, Parakeet only)
  but feed a preview overlay; typing partials would require backspacing already-typed TUI text.

---

## 8. Where the work lands (a fork — mostly config + a few Swift files)
Paths relative to the fork root (`VoiceInk/` in this repo). Mapped 2026-07-02 by `voiceink-explorer`.

- [x] **Injection/output** — ✅ **type-out (CGEvent per-char) mode ADDED 2026-07-08** (fork commit
      `853a01d`, branch `wisprflow`): `.typeOut` case in `VoiceInk/Modes/ModeConfig.swift`, typing
      path `CursorPaster.typeOut()` in `VoiceInk/Paste/CursorPaster.swift`, routing in
      `VoiceInk/Transcription/Engine/TranscriptionDelivery.swift:paste()`. Upstream paste paths
      unchanged: clipboard Cmd+V via CGEvent (`CursorPaster.swift`), AppleScript variant, method enum
      `VoiceInk/Paste/PasteMethod.swift`.
- [ ] **LLM/enhancement service** — Ollama already integrated: `VoiceInk/Services/OllamaService.swift`
      (endpoint `http://localhost:11434` at `:6`; `enhance()` `:78-103`); provider dispatch
      `VoiceInk/Services/AIEnhancement/AIEnhancementService.swift:203-224`; prompts =
      `VoiceInk/Models/CustomPrompt.swift`, stored in UserDefaults `customPrompts`, selected
      **per profile** via `VoiceInk/Modes/ModeRuntimeConfiguration.swift:97-127` (endpoint/model are
      global; prompt selection is per-profile). Custom vocabulary auto-injected at
      `AIEnhancementService.swift:137-149`.
- [ ] **Power Mode** — upstream calls it **Modes**: `VoiceInk/Modes/ModeConfig.swift:66-253`
      (per-profile overrides incl. ASR model, prompt UUID, `outputMode` `:23-51`, `autoSendKey` `:3-21`;
      app matching via bundle-ID `appConfigs` `:227-241`); auto-activation on frontmost-app change in
      `VoiceInk/Modes/ActiveWindowService.swift:30-60`; runtime resolution
      `VoiceInk/Modes/ModeRuntimeConfiguration.swift:61-201`.
- [ ] **ASR/model config** — dual engine, **Parakeet TDT v3 already supported**:
      `VoiceInk/Transcription/FluidAudio/FluidAudioModelManager.swift:30-39` (`parakeet-tdt-0.6b-v3`);
      whisper.cpp side `VoiceInk/Transcription/Whisper/WhisperModelManager.swift`; per-profile model at
      `VoiceInk/Modes/ModeConfig.swift:76`.
- [x] **Hotkey** (KeyboardShortcuts) — reuse as-is: `VoiceInk/Shortcuts/RecordingShortcutManager.swift`
      (toggle / push-to-talk / hybrid modes) + global CGEvent tap `VoiceInk/Shortcuts/ShortcutMonitor.swift`.
- [x] Identify exact file paths on first read of the cloned repo (done — see above). Extras: Auto-Send
      Return via `VoiceInk/Paste/CursorPaster.swift:218-239` (500 ms after paste,
      `TranscriptionDelivery.swift:159-167`); custom dictionary =
      `VoiceInk/Services/CustomVocabularyService.swift`; entitlements have **no App Sandbox** (good);
      `MACOSX_DEPLOYMENT_TARGET = 14.4`.

---

## 9. macOS gotchas / risks
- [ ] **Permissions:** Microphone (`NSMicrophoneUsageDescription`) + **Accessibility** (for global hotkey CGEvents + keystroke injection).
- [ ] **Terminal injection:** prefer **type-out**, not clipboard paste (paste corruption + bracketed-paste `00~`).
- [ ] **Auto-submit is the rough edge:** reliably getting Claude Code's TUI to *submit* is fiddly
      (Auto-Send Return works via keystroke; programmatic stdin submission is unreliable — see Claude Code issue #15553). Default to letting the user press Enter.
- [ ] **Distribution:** Apple rejects App Store apps using Accessibility API for text injection → distribute via direct/notarized build, not MAS.
- [ ] **GPL v3:** fork/modify for personal use freely; if ever distributed, keep GPL and publish source.

---

## 10. Acceptance criteria / end-to-end verification
All PASSED 2026-07-08 pm (`/verify-pipeline` full run, live in Claude Code inside Cursor's terminal;
per-item evidence from the app's SwiftData history + unified log):
- [x] `ollama run llama3.2:3b "hi"` responds (Ollama up). *(generation verified via API)*
- [x] App builds in Xcode, launches, permissions granted. *(running from `/Applications/VoiceInk.app`
      after Simon moved it — grants survived the move)*
- [x] **In a live Claude Code session:** focus the terminal, hold hotkey, say
      *"um can you refactor the auth module and add tests"* → the cleaned instruction is **typed** into
      the Claude Code input (no `00~`, no corruption), ready to send. *(received byte-exact; ASR 0.13 s
      + cleanup 0.28 s)*
- [x] Terminal profile auto-activated (type-out mode) without manual switching. *(history rows show
      mode "Claude Code" + prompt "Claude Code terminal" — after adding Cursor's bundle ID; the first
      attempt silently fell through to the Dictation profile's paste path, see the Phase 3 note)*
- [x] Custom-vocab test: a mis-heard dev term is corrected via the dictionary. *("Claude Code",
      "SwiftUI", "JSON" all correct; new mishearing "UmClon/clon code" found live and added to the
      dictionary + restore script)*
- [x] Stop Ollama → raw transcript still injects (ASR independent of LLM). *(raw typed; history row
      records "Enhancement failed: Could not connect to the server." + warning notification)*
- [x] **Airplane mode** on → whole flow still works (proves 100% local, unlike native `/voice`).
      *(airportd log: Wi-Fi off 17:51:44 → dictation WITH 0.27 s Ollama cleanup at 17:52:05 → Wi-Fi
      on 17:52:20 — full pipeline incl. LLM ran offline over loopback)*

---

## 11. Lighter-weight fork alternatives (if VoiceInk feels too heavy)
- **`rcourtman/parakey`** — minimal native Swift, Parakeet-TDT v3 on ANE, ~100ms key-release→text (great low-latency reference; **no LLM layer**).
- **`jatinkrmalik/vocamac`** — WhisperKit-based hotkey→text.
- **`skulkworks/foxsay`** (Parakeet + local AI), **`Open-Less/openless`** (hotkey→speak→AI-polished, Mac+Windows).
- Trade-off: simpler, but you'd re-implement type-out + per-app profiles + Ollama that VoiceInk already ships. VoiceInk stays the recommended base.

---

## 12. Sources
- Claude Code native `/voice` streams audio to Anthropic (not local) — code.claude.com/docs/en/voice-dictation.
- VoiceInk type-out (keystroke) mode, Power Mode profiles, Auto-Send — tryvoiceink.com/docs/power-mode; github.com/Beingpax/VoiceInk.
- Clipboard-paste corruption in terminal TUIs; use keystroke mode — openai/codex issue #11103; iTerm2 bracketed-paste notes.
- Claude Code bracketed-paste fix (`printf '\e[?2004l'`) — shivankaul.com/blog/paste-bracketing-iterm2.
- Programmatic stdin submission to Claude Code TUI is unreliable — anthropics/claude-code issue #15553.
- mcp-voice-hooks uses browser Web Speech API (not local Whisper/Ollama) — github.com/johnmatthewtennant/mcp-voice-hooks.
- Ollama is text-only (no native ASR) — ollama/ollama discussions.
- Parakeet-TDT vs whisper-large-v3-turbo benchmarks (Apple Silicon) — spokenly / dicta.to.
