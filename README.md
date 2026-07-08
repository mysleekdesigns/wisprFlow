# wisprFlow — local voice input for Claude Code (macOS)

A **local, private, offline** voice-dictation tool whose primary purpose is **talking to Claude
Code in the terminal**: hold a hotkey → speak → clean text is *typed* into the Claude Code TUI.
It also works system-wide, like Wispr Flow — but without the cloud.

**The one invariant: everything runs on your Mac.** The whole pipeline works with airplane mode
on. Speech recognition is a local Whisper-family model; the optional text cleanup is a small
local model served by [Ollama](https://ollama.com). No audio or text ever leaves the machine.
(Claude Code's native `/voice` streams audio to Anthropic's servers; Wispr Flow is also
cloud-based. That gap is why this project exists.)

The app itself is a fork of [VoiceInk](https://github.com/Beingpax/VoiceInk) (native macOS
Swift, GPL v3) with a type-out injection mode and a Claude Code terminal profile added. See
`PRD.md` for the full spec.

## How it works

```
[hotkey down] record mic            KeyboardShortcuts + AVAudioEngine (Microphone permission)
[hotkey up]   local ASR             Parakeet-TDT v3 (Apple Neural Engine) or whisper.cpp (Metal)
              optional cleanup      Ollama @ localhost:11434, small model, light-touch prompt
              inject at cursor      type-out mode (CGEvent per-character) — NOT clipboard paste
              [profile]             auto-activates for Terminal / iTerm2 / Ghostty / VS Code / Cursor
              [Auto-Send: optional] presses Return for you (default OFF)
```

Type-out mode matters: clipboard paste into a terminal TUI triggers bracketed-paste wrapping
and leaves stray `00~` / `201~` characters in the input. The terminal profile always types.

## What's in this repo

This repo is the project workspace — docs, restore scripts, and Claude Code tooling. The app
source lives in a **separate nested repo** at `VoiceInk/` that is git-ignored here, so **cloning
this repo does not give you the app** — you clone the fork in step 3 below.

| Path | What it is |
|---|---|
| `PRD.md` | Full product spec, phase log, file:line map of the fork changes |
| `CLAUDE.md` | Project instructions for Claude Code |
| `scripts/` | Python scripts that restore in-app configuration (see below) |
| `.claude/` | Claude Code skills, subagents, rules, and hooks for working on this project |
| `VoiceInk/` | *(you create this)* the forked app — nested git repo, ignored by this one |

## Requirements

- **Apple Silicon Mac** running **macOS 14.4+** (the recommended ASR model runs on the Neural
  Engine; Intel works only via the slower whisper.cpp path)
- **Xcode** (latest; `xcodebuild -version` to confirm) — a free Apple ID is enough, builds are
  ad-hoc signed
- **Git**, **Homebrew**
- **Ollama** (installed in step 2)
- A working **Claude Code** install in Terminal.app / iTerm2 / Ghostty / VS Code / Cursor
  (only needed for the headline use case — the app dictates into any app)

No API keys, accounts, or network access are needed to run the pipeline.

## Setup

### 1. Clone this repo

```sh
git clone https://github.com/mysleekdesigns/wisprFlow.git
cd wisprFlow
```

### 2. Install Ollama and create the cleanup model

```sh
brew install ollama
ollama serve   # leave running; `brew services start ollama` keeps it running at login
```

(Or install the [Ollama desktop app](https://ollama.com/download) instead — its menu-bar item
runs the server for you.)

In another shell, pull the base model and create the derived `wispr-cleanup` model the app's
Claude Code profile uses (a `qwen2.5:3b` with temperature baked in — the app's HTTP client
can't pass temperature reliably, so it lives in the model):

```sh
ollama pull qwen2.5:3b
printf 'FROM qwen2.5:3b\nPARAMETER temperature 0.2\nPARAMETER num_predict 512\n' > /tmp/wispr-cleanup.Modelfile
ollama create wispr-cleanup -f /tmp/wispr-cleanup.Modelfile
ollama run wispr-cleanup "say hi"   # must respond before you continue
```

Cleanup is an optional layer: if Ollama is down the raw transcript still gets typed. Ollama is
text-only — it never does the speech recognition.

### 3. Clone the VoiceInk fork into `VoiceInk/`

From the repo root (the directory name must be `VoiceInk`):

```sh
git clone https://github.com/mysleekdesigns/VoiceInk.git
git -C VoiceInk checkout wisprflow                                            # active development branch
git -C VoiceInk remote add upstream https://github.com/Beingpax/VoiceInk.git  # optional, for rebases
```

The fork adds the type-out (per-character CGEvent) output mode, the menu-bar recording badge,
and the terminal-profile plumbing on top of upstream VoiceInk.

### 4. Build the app

```sh
cd VoiceInk
make local
```

`make local` checks prerequisites, builds the whisper.cpp XCFramework if missing, does an
ad-hoc-signed Debug build (no Apple Developer cert needed), and copies the app to
`~/Downloads/VoiceInk.app`. Dependencies land in `~/VoiceInk-Dependencies/`.

**whisper.cpp caveat:** upstream's `build-xcframework.sh` also builds iOS/tvOS/visionOS slices,
which fail unless you have those SDKs installed in Xcode. Either install the extra platform
SDKs (Xcode → Settings → Components), or edit
`~/VoiceInk-Dependencies/whisper.cpp/build-xcframework.sh` to delete the non-macOS build
sections and remove their slices from the final `-create-xcframework` call — only the macOS
slice is needed. Note `make clean` deletes `~/VoiceInk-Dependencies/` entirely, including that
edit.

If every compile fails with `No CMAKE_C_COMPILER` or plug-in load errors (typical after an
Xcode update), run `sudo xcodebuild -runFirstLaunch` and retry.

Alternatively, open `VoiceInk.xcodeproj` in Xcode and hit ⌘R — see the fork's `BUILDING.md`.
Note that plain Xcode builds don't set the `LOCAL_BUILD` flag, so the fork's local-build
guards (including the one that stops Sparkle from offering upstream updates that would
replace the fork) are inactive — prefer `make local`.

### 5. First launch — permissions, ASR model, hotkey

```sh
open ~/Downloads/VoiceInk.app
```

Walk through onboarding — **complete it, don't use the Skip button** (onboarding creates the
default "Dictation" mode that step 7's restore script requires):

1. **Microphone** — grant the standard prompt (recording is silent without it).
2. **Accessibility** — enable VoiceInk under System Settings → Privacy & Security →
   Accessibility. Required for the global hotkey and keystroke injection; nothing types
   without it. Relaunch the app after granting.
3. **Download an ASR model** in the app's transcription settings:
   - **Parakeet-TDT v3** (`parakeet-tdt-0.6b-v3`, FluidAudio / Apple Neural Engine) —
     recommended: fastest (~0.1 s key-release-to-text), English-only.
   - **whisper-large-v3-turbo** (whisper.cpp / Metal) — if you need multilingual.
4. **Set the global hotkey.** This project uses the left ⌥ Option key in hybrid mode
   (hold = push-to-talk, quick tap = hands-free toggle).

### 6. Test the raw loop

Open TextEdit, hold the hotkey, say a sentence, release. The transcript should appear at the
cursor within ~a second — no AI cleanup yet, and at this stage it arrives via paste (type-out
injection only kicks in with the terminal profile from step 7). If nothing records, check
Microphone; if it records but nothing appears, check Accessibility.

### 7. Configure cleanup + the Claude Code terminal profile

The fastest path is the restore script, which recreates the whole Phase 2+3 configuration
(the two cleanup prompts, the Ollama wiring, the "Claude Code" type-out profile for six
terminal apps, and 17 dev-jargon dictionary corrections):

```sh
osascript -e 'quit app "VoiceInk"'     # the app must NOT be running
python3 scripts/restore_phase3.py      # from the wisprFlow repo root
open ~/Downloads/VoiceInk.app
```

The script requires onboarding to have been completed (step 5 — it needs the default
"Dictation" mode onboarding creates) and aborts before changing anything if a "Claude Code"
mode already exists. It assumes the `wispr-cleanup` model from step 2 and the Parakeet ASR
model from step 5.

<details>
<summary>Prefer to configure it by hand? (click to expand)</summary>

In the app's settings:

1. **Enhancement provider:** Ollama, endpoint `http://localhost:11434`, model
   `wispr-cleanup:latest`.
2. **Two custom prompts**, with *Use System Template / Instructions* turned **OFF** (the
   wrapper template degrades small models). Use these verbatim — do not "improve" them:
   - *General:* "You clean up dictated speech. Remove filler words (um, uh, like), fix
     grammar, punctuation, and capitalization. Preserve the speaker's meaning and wording.
     Output ONLY the cleaned text."
   - *Claude Code terminal:* "You clean up a spoken instruction to a coding assistant. Remove
     filler words and fix punctuation and capitalization only. Do NOT rephrase, summarize,
     translate to prose, or add markdown/code fences. Preserve technical terms, file paths,
     command names, and identifiers exactly as heard. Output ONLY the cleaned instruction."
3. **A "Claude Code" Power Mode profile** that auto-activates for your terminal apps
   (Terminal, iTerm2, Hyper, Ghostty, VS Code, Cursor), with output mode **type-out**
   (never clipboard paste — it corrupts TUIs), the *Claude Code terminal* prompt,
   **Auto-Send off**, and **text formatting off**.
4. **Custom dictionary** entries for jargon the ASR mishears: "Claude Code", "npm",
   "refactor", "SwiftUI", "CGEvent", plus your own repo and file names.

</details>

### 8. Verify

Focus a live Claude Code session, hold the hotkey, and say: *"um can you refactor the auth
module and add tests"*. On release, the cleaned instruction (no filler, no `00~` garbage)
should be typed into the Claude Code input with the terminal profile activating by itself. You
press Enter to send.

Then the robustness checks: quit Ollama → the raw transcript still injects; turn **airplane
mode on** → the entire flow still works. That last test is the point of the project.

## Rebuilding / updating

Pull and re-run `make local` — local builds never self-update: the fork gates upstream's
Sparkle auto-updater behind the `LOCAL_BUILD` flag that `make local` sets, so the updater
never starts and the "Check for Updates" buttons stay disabled. (If you are still running an
older local build, decline any "Update Available" prompt — accepting would replace the fork
with stock upstream VoiceInk.) Two things commonly break after a rebuild:

- **Accessibility grant is invalidated** by ad-hoc re-signing. Toggling the checkbox is not
  enough — remove VoiceInk with the "−" button in System Settings → Accessibility and re-add
  it. (Symptom: `Failed to install global shortcut event tap` in the logs, hotkey dead.)
- **In-app configuration can be wiped** (prompts, modes, dictionary). Quit the app and re-run
  `python3 scripts/restore_phase3.py` (everything) or `python3 scripts/restore_dictionary.py`
  (dictionary only — aborts unless the dictionary is empty; don't run it after
  `restore_phase3.py`, which already inserts the entries).

## Troubleshooting

| Symptom | Fix |
|---|---|
| Hotkey records nothing | Microphone permission (System Settings → Privacy & Security) |
| Records, but no text is typed | Accessibility permission; relaunch the app after granting |
| Hotkey dead after a rebuild | Remove ("−") and re-add the app in Accessibility settings |
| `00~` / `201~` garbage in the terminal | Profile is using clipboard paste — switch it to type-out |
| `No CMAKE_C_COMPILER` / plug-in errors | `sudo xcodebuild -runFirstLaunch` |
| `build-xcframework.sh` fails on iOS/tvOS/visionOS | Install those SDK components, or patch the script macOS-only (step 4) |
| Dictation works but text is raw / uncleaned | Ollama not running, or `wispr-cleanup` model missing — this is the designed fallback |
| Config gone after rebuild | `scripts/restore_phase3.py` (quit the app first) |

## Developing with Claude Code

The `.claude/` directory ships skills (`/voiceink-setup`, `/terminal-injection`,
`/ollama-cleanup`, `/asr-config`, `/macos-permissions`, `/verify-pipeline`), subagents, and
hooks for working on this project with Claude Code — see `CLAUDE.md`. The git-ignored `.env` /
`.mcp.json` hold keys for optional web-crawling MCP tooling only; the voice pipeline never
needs them.

## License

The VoiceInk fork is **GPL v3** — keep license headers, and if you distribute builds, publish
the source. Distribution must be direct/notarized: the Mac App Store rejects Accessibility-API
text injection, and the App Sandbox entitlement breaks CGEvent injection, so neither is an
option.
