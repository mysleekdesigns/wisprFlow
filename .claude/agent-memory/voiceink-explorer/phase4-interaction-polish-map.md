---
name: phase4-interaction-polish-map
description: VoiceInk Phase 4 interaction-polish code map — hotkey modes, recording feedback sounds, menu-bar status UI
metadata:
  type: project
---

# Phase 4 Code Map — Interaction Polish Features

**As of:** 2026-07-08
**Verified against:** VoiceInk fork at `/Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk`

---

## 1. Push-to-Talk vs Toggle vs Hybrid Hotkey Behavior

### Overview
VoiceInk supports three hotkey modes for the primary/secondary recording shortcuts:
- **Toggle:** Press and release to start hands-free recording; press again to stop
- **Push-to-Talk:** Hold to record, release to stop (classic paradigm)
- **Hybrid:** Short press toggles hands-free; hold ≥0.5s stops if recording (threshold at line 359)

Current hotkey: **left ⌥ (Option) modifier-only, held** as noted in CLAUDE.md.

### Location & Configuration

**Mode enum definition:** `VoiceInk/Shortcuts/RecordingShortcutManager.swift:62–74`
- Line 62: `enum Mode: String, CaseIterable`
- Cases: `.toggle`, `.pushToTalk`, `.hybrid`
- Display names for UI localization

**Default:** `VoiceInk/Shortcuts/ShortcutMigration.swift:18–19`
- `return .hybrid` — hardcoded fallback when no prior setting exists
- Not in AppDefaults.swift (is set dynamically on init)

**User defaults keys:** `VoiceInk/Shortcuts/RecordingShortcutManager.swift:22–30`
- `"primaryRecordingShortcutMode"` — persisted for primary hotkey (line 23)
- `"secondaryRecordingShortcutMode"` — persisted for secondary hotkey (line 29)
- Stored as string enum rawValue

### UI for User Configuration

**Settings UI:** `VoiceInk/Views/Settings/SettingsView.swift:1300–1340` (approx.)
- `shortcutModePicker()` function (line ~1340)
- Picker shows `RecordingShortcutManager.Mode.allCases` with `displayName` labels
- Binding to `$recordingShortcutManager.primaryRecordingShortcutMode` / secondary variant
- Primary picker: ~line 1305, Secondary picker: ~line 1315
- **Config-only:** Simon toggles mode in Settings → Shortcuts → "Primary Shortcut" → dropdown picker

### Hotkey Behavior Logic

**Entry point:** `VoiceInk/Shortcuts/RecordingShortcutManager.swift:224–259`
- `onKeyDown:` / `onKeyUp:` handlers for shortcut monitor
- Calls `shortcutModeHandler.handleKeyDown()` and `handleKeyUp()` with current mode

**Mode-specific logic:** `VoiceInk/Shortcuts/RecordingShortcutManager.swift:384–462` (RecordingShortcutModeHandler)
- Line 384: `handleKeyDown()` — decides when to show recorder panel on key press
- Line 430: `handleKeyUp()` — decides when to hide recorder panel / enter hands-free mode
- Line 359: `hybridPressThreshold = 0.5` — 500 ms threshold for hybrid mode (line 452 checks `pressDuration >= hybridPressThreshold`)

**Toggle behavior (lines 409–420, 442–443):**
- keyDown: If hands-free was on, toggle off (stop). Else, show recorder if not visible.
- keyUp: Set `isHandsFreeRecording = true` (now recording hands-free)

**Push-to-Talk behavior (lines 422–426, 445–449):**
- keyDown: Show recorder if not visible
- keyUp: Hide recorder if visible (stops recording on release)

**Hybrid behavior (lines 408–427, 451–458):**
- keyDown: Same as toggle (show if not visible)
- keyUp: If held ≥0.5s and recording, stop. Else toggle hands-free on (short press)

### Current Default & Defaults Read

**Current setting:** `defaults read com.prakashjoshipax.VoiceInk primaryRecordingShortcutMode`
- Returns: `"hybrid"` (the default from ShortcutMigration)
- User can override by changing it in Settings → Shortcuts

**Notes for editor:**
- `activeShortcutCanCancelAccidentalStart` (line 355) gates accidental-start cancellation
- `shortcutPressCooldown = 0.5` (line 358) prevents rapid re-triggering
- No Swift change needed if only changing defaults; config-only if Simon flips the setting

---

## 2. Start/Stop Recording Sounds (Feedback)

### Overview
Upstream **already implements** start/stop feedback sounds. Configurable per-user, with built-in + custom sound support.

### Location & Config

**Sound playback API:** `VoiceInk/SoundManager.swift:36–49`
- `playStartSound()` — plays on record start if enabled (line 36)
- `playStopSound()` — plays on record stop if enabled (line 41)
- `playEscSound()` — plays when recording is cancelled (line 46)
- All methods check `CustomSoundManager.shared.isSoundEnabled(for: type)` before playing

**Sound engine:** `VoiceInk/SoundPlaybackEngine.swift`
- Wraps AVAudioPlayer for sound playback
- `playStartSound()`, `playStopSound()`, `playEscSound()` methods

**Sound configuration:** `VoiceInk/CustomSoundManager.swift:60–87`
- Enum `SoundSelection`: `.none`, `.builtIn(BuiltInSound)`, `.custom(String)`
- Two sound types: `.start`, `.stop` (line 42)
- Built-in sounds: 7 choices (`sound1..sound7`) as WAV/MP3 (line 8–39)
- Default sounds: `sound5` for start, `sound6` for stop (line 50–56)
- Custom sounds stored at `~/Library/Application Support/VoiceInk/CustomSounds/` (line 190)

**User defaults persistence:** `VoiceInk/CustomSoundManager.swift:90–116`
- `@Published` properties persist via didSet
- Keys: `selectedStartSoundSelection`, `selectedStopSoundSelection`, `selectedStartBuiltInSound`, etc.
- On init: reads UserDefaults and constructs current SoundSelection (lines 126–153)

**UI for configuration:** `VoiceInk/Views/Settings/CustomSoundSettingsView.swift`
- Settings page to toggle sounds on/off
- Picker for built-in sound selection
- Option to upload custom audio file
- Preview buttons (`playStartSound()` / `playStopSound()` called on tap, line ~visibility in view)

### Where Sounds Trigger

**Start sound:** `VoiceInk/Transcription/Engine/RecorderUIManager.swift:216–224` (approx.)
- Called when showing recorder panel and starting record: `SoundManager.shared.playStartSound()`
- Triggered in `toggleRecorderPanel()` → `toggleRecord()` flow

**Stop sound:** `VoiceInk/Transcription/Engine/TranscriptionDelivery.swift` (multiple call sites)
- Line ~48–50: `SoundManager.shared.playStopSound()` after successful delivery
- Line ~160: playStopSound on error/cancellation
- Called at end of transcription/enhancement pipeline

**Escape sound:** `VoiceInk/Notifications/NotificationManager.swift`
- `SoundManager.shared.playEscSound()` — played when recording is cancelled via notification

### Current Default Behavior

**Default:** Start & stop sounds are **enabled** with built-in sound5 and sound6
- No toggle in AppDefaults; sounds initialized on-demand in CustomSoundManager.init()
- If user has never configured, sounds play by default

**Is it a Swift change or config-only?**
- **Config-only:** Simon can toggle sounds on/off in Settings → Custom Sounds, or select different built-in sounds
- **Swift change if needed:** To add haptic feedback or change default built-in sounds, modify CustomSoundManager.swift lines 50–56

### Notes for editor

- Sound playback is async via AVAudioPlayer; no blocking on main thread
- `playEscSound()` plays only if `CustomSoundManager.shared.hasAnyRecordingSoundEnabled` (line 47 in SoundManager)
- **No interaction with type-out injection:** Sounds play after text is delivered, not during keystroke injection
- Custom sounds are validated for duration (max 3.0 seconds, line 88 in CustomSoundManager)

---

## 3. Menu-Bar Status Icon

> **UPDATE 2026-07-08 pm:** the static-icon gap below is now closed in the fork — new
> `VoiceInk/Views/MenuBarStatusLabel.swift` observes `engine.recordingState` and swaps the label
> (starting/recording → `record.circle.fill`, transcribing/enhancing/busy → `waveform`, idle →
> upstream "menuBarIcon" asset); the MenuBarExtra label in `VoiceInk.swift` is now the one-liner
> `MenuBarStatusLabel(engine: engine)`. Sections below describe upstream as-was.

### Overview
Menu-bar icon uses SwiftUI's **MenuBarExtra**. Static icon; dropdown menu shows current mode + actions. **No animated state change** to icon itself during recording/transcribing/enhancing.

### Location & Behavior

**Menu-bar definition:** `VoiceInk/VoiceInk.swift:342–364`
- SwiftUI `MenuBarExtra(isInserted: $showMenuBarIcon)` container
- Label image: "menuBarIcon" asset (line 360: `NSImage(named: "menuBarIcon")!`)
- Content: `MenuBarView()` (dropdown menu)
- Style: `.menuBarExtraStyle(.menu)` (line 364)

**Icon rendering:** `VoiceInk/VoiceInk.swift:355–362`
- Fixed 22×22 size (maintains aspect ratio)
- SVG/image asset "menuBarIcon" — **static, no color/animation changes**
- Resized at runtime to fit menu bar

**Menu content:** `VoiceInk/Views/MenuBarView.swift:19–157`
- "Toggle Recorder" button (line 45–47) — instant action
- "Mode:" submenu (line 51–84) — shows all enabled modes; current mode has "✓" checkmark
- "Audio Input:" submenu (line 86–108) — select microphone
- History, Settings, Quit, etc.
- **No recording-state badge or color indicator on the icon itself**

### State Transitions (Published)

**Recording state changes are published in engine:**
- `VoiceInk/Transcription/Engine/VoiceInkEngine.swift`: `@Published var recordingState: RecordingState = .idle`
- States: `.idle`, `.starting`, `.recording`, `.transcribing`, `.enhancing`, `.busy` (enum RecordingState)
- Observed by UI components, but **not by the menu-bar icon**

**Menu-bar currently shows:**
- Active mode name (line 80: `modeManager.currentEffectiveConfiguration?.name`)
- No real-time feedback (e.g., "recording", "transcribing") in the icon or menu label

### Current Default

**Menu-bar icon is always visible** unless user toggled `showMenuBarIcon` (line 27 in VoiceInk.swift)
- `@State private var showMenuBarIcon = true`
- Set to `$showMenuBarIcon` binding in MenuBarExtra (line 342)

**"Menu Bar Only" mode** (separate concept):
- `MenuBarManager.isMenuBarOnly` toggles dock/window visibility (not icon visibility)
- Located in Menu → "Hide Dock Icon" (MenuBarView.swift line 131–134)

### Configuration & Customization

**Is it config-only or needs Swift change?**
- **Config-only (minor):** Toggle menu-bar icon visibility via binding (would need UI control, not yet exposed)
- **Swift change if enhancement desired:** To animate icon / show state badge:
  - Extend `MenuBarExtra(label:)` to use computed property that reacts to `@ObservedObject engine.recordingState`
  - Or add a colored badge/overlay to NSImage based on recording state
  - Would modify VoiceInk.swift:355–362 to check engine.recordingState and swap icon/add overlay

### Notes for editor

- SwiftUI MenuBarExtra is macOS 13.0+; deployment target is 14.4+, so fully compatible
- Menu-bar icon and menu-bar-only mode are orthogonal concepts (confusing naming)
- **No interaction with type-out injection:** Menu-bar is purely UI indicator; recording happens independently
- If adding state animation: ensure it doesn't interfere with keyboard input detection during recording
- Current design is minimal/stable; state feedback is in the recorder panel itself, not menu bar

---

## Summary Table

| Feature | Location | Type | Current Default | Configurable in UI? | Swift Change for Enhancement? |
|---------|----------|------|-----------------|-------|-----------|
| **Hotkey Mode (toggle/push/hybrid)** | RecordingShortcutManager.swift:62–74; ShortcutMigration.swift:18 | Config (UserDefaults) | `.hybrid` | Yes (Settings → Shortcuts) | No, unless changing default logic |
| **Start Sound** | SoundManager.swift:36; CustomSoundManager.swift:50 | Config (UserDefaults) | Enabled, sound5 | Yes (Settings → Custom Sounds) | No, unless adding haptic feedback |
| **Stop Sound** | SoundManager.swift:41; CustomSoundManager.swift:55 | Config (UserDefaults) | Enabled, sound6 | Yes (Settings → Custom Sounds) | No, unless adding haptic feedback |
| **Menu-Bar Icon** | VoiceInk.swift:342–364 | UI (static) | Always visible, static | No UI yet | Yes, to add state animation/badge |

---

## Rebase-Friendly Recommendations

1. **Hotkey modes:** Already complete; no changes needed. If adding new mode, extend enum at line 62 and update Mode.allCases automatically.
2. **Recording sounds:** Already complete; fully configurable. For haptic feedback, add optional `hapticFeedback()` calls in RecorderUIManager and TranscriptionDelivery alongside sound calls (minimal, isolated diffs).
3. **Menu-bar status:** Currently minimal. If adding state animation, keep it in VoiceInk.swift lines 355–362 (don't refactor MenuBarView); upstream likely won't add animated status icon, so diff stays small.

All three features are **stable and upstream-compatible** with minimal fork diffs.
