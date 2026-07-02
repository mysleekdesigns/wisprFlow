# Per-phase fan-out plans

The concrete decomposition `next-phase` uses. Each block = one PRD §6 phase → the independent
workstreams, the sub-agent that runs each, its task, plus the human + verify steps. Launch all the
read-only/build agents of a block **in one message** (parallel). Sequence anything that edits the same
file. Everything stays offline (PRD §2).

Sub-agents available: `voiceink-explorer` (read-only code mapper), `build-doctor` (build + triage),
`swift-reviewer` (read-only Swift review), `general-purpose` (research/drafting). Per-phase skills do
the wiring: `/voiceink-setup`, `/asr-config`, `/macos-permissions`, `/ollama-cleanup`,
`/terminal-injection`, `/verify-pipeline`.

---

## Phase 0 — Prerequisites & environment
Not code — no fan-out. Route to `/voiceink-setup` Phase 0. Confirm: Xcode (`xcodebuild -version`),
Homebrew, Ollama up (`ollama run llama3.2:3b "say hi"`), a working Claude Code terminal. All human.

---

## Phase 1 — Fork & build; validate the RAW loop
**Precondition:** fork cloned. If not → STOP, route to `/voiceink-setup` (Simon forks on GitHub + clones
his fork URL into the repo). Only fan out once a `.xcodeproj`/`BUILDING.md` exists.

Parallel workstreams:
1. **Map the codebase** — `voiceink-explorer`: map all 6 subsystems (PRD §8) → `file:line` for
   injection/output, Ollama enhancement service, Power Mode, ASR/model config, hotkey, permissions.
   This map feeds every later phase; have it save to its project memory.
2. **Build the base** — `build-doctor`: resolve SwiftPM deps (KeyboardShortcuts, whisper.cpp,
   FluidAudio, MediaRemoteAdapter), build & run, triage any compiler/linker/SPM errors → minimal fixes.
3. **Permissions prep** — `general-purpose`: verify `NSMicrophoneUsageDescription` in Info.plist;
   confirm **no App Sandbox entitlement** (it breaks CGEvent injection); produce the Microphone +
   Accessibility checklist. Feed into `/macos-permissions`.
4. **ASR prep** — `general-purpose`: recommend the model to download (Parakeet-TDT v3 via FluidAudio for
   English; whisper-large-v3-turbo for multilingual) and where it lands. Feed into `/asr-config`.

Human: fork+clone (if needed), grant Microphone + Accessibility, download the model in-app, set the
global hotkey. **Verify:** raw-loop test in TextEdit (hotkey → speak → text appears, no AI layer).

---

## Phase 2 — Wire the local Ollama cleanup layer
**Precondition:** fork cloned + mapped. If the enhancement service isn't mapped yet, include workstream 1.

Parallel workstreams:
1. **Locate the enhancement service** — `voiceink-explorer`: find the Ollama HTTP client and prompt
   handling (`11434`, `localhost`, "ollama", "enhancement", the URLSession call, per-profile prompt
   selection) → `file:line`.
2. **Config + prompts** — `general-purpose`: produce the exact settings (provider = **Ollama**, endpoint
   `http://localhost:11434`, model = a pulled small model, e.g. `qwen2.5:3b` or `llama3.2` — check
   `ollama list`) and the two light-touch prompts verbatim from PRD §7. Feed into `/ollama-cleanup`.
3. **Test fixtures** — `general-purpose`: craft filler-heavy input sentences + expected cleaned outputs;
   a latency target (< ~1s); the Ollama-down expectation (raw transcript still injects — ASR ⟂ LLM).

Then **sequence** (same files): apply config/prompt via `/ollama-cleanup` → `build-doctor` build →
`swift-reviewer` on the diff. Human: set the values in the app's AI-enhancement settings; run the
offline cleanup test. **Verify:** `/ollama-cleanup` test, then the cleanup item in `/verify-pipeline`.

---

## Phase 3 — Claude Code / Terminal profile (the core)
**Precondition:** fork cloned + mapped.

Parallel workstreams:
1. **Locate Power Mode + injection mode** — `voiceink-explorer`: find per-app profile matching +
   auto-activation (`NSWorkspace`, `frontmostApplication`, bundle IDs) and the injection-mode selection;
   confirm the **type-out (CGEvent per-character)** path vs clipboard paste, plus Auto-Send and the
   custom dictionary → `file:line`.
2. **Terminal prompt + dictionary** — `general-purpose`: the coding-agent enhancement prompt (PRD §7,
   preserve technical terms/paths/identifiers, no markdown/code fences) + custom-dictionary entries for
   dev jargon Whisper mishears ("Claude Code", "npm", "refactor", lib/file names). Feed into
   `/terminal-injection`.
3. **App matching + guards** — `general-purpose`: terminal bundle identifiers — Terminal.app
   (`com.apple.Terminal`), iTerm2 (`com.googlecode.iterm2`), Ghostty (`com.mitchellh.ghostty`), VS Code
   (`com.microsoft.VSCode`); Auto-Send default **OFF** plan; the bracketed-paste shell-rc fallback
   (`claude() { command claude "$@"; printf '\e[?2004l'; }`) as a note only.

Then **sequence** (same files): apply via `/terminal-injection` → `build-doctor` build → `swift-reviewer`
review — pay attention to CGEvent/Accessibility correctness. **Never** switch the terminal profile to
clipboard paste (paste corruption + bracketed-paste `00~`). Human: create/verify the Power Mode profile,
confirm type-out mode, decide Auto-Send. **Verify:** `/verify-pipeline` core flow + **airplane-mode**
test (the project's whole reason to exist).

---

## Phase 4 — Polish & optional extensions
Lower priority; only after the MVP passes `/verify-pipeline`. Parallel workstreams:
1. **Latency tuning** — `general-purpose` + `/asr-config`: pick the lowest-latency ASR engine/model for
   this machine; measure key-release→text.
2. **Interaction polish** — `voiceink-explorer` (locate) then a scoped editor: push-to-talk vs toggle,
   start/stop sound, menu-bar status.
3. **Optional command words** — `general-purpose`: "new line", "send it", streaming/partial transcripts
   (scope only; defer unless requested).

Human: try each on the real machine. **Verify:** re-run `/verify-pipeline` for regressions.
