---
name: typeout-injection-implementation-map
description: Complete file:line map for adding type-out (CGEvent per-character keystroke) injection mode to VoiceInk Phase 3
metadata:
  type: reference
---

## Type-Out Injection Feature Map

### 1. OutputMode Enum Plumbing
**File: /Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk/VoiceInk/Modes/ModeConfig.swift**
- **ModeOutputMode enum**: lines 23-51
  - Cases: `.paste`, `.respond`, `.customCommand` 
  - No `.typeOut` case yet; must add as new case with "Type Out" displayName + "doc.text" iconName
  - `usesPasteOptions` computed property (line 44) returns `true` only for `.paste`
  - `choices(canRespond:)` factory (line 48) determines which modes are available
  - **Codable handling** (lines 23): rawValue auto-derives from case name; old configs without `.typeOut` decode as `.paste` via `decodeIfPresent...?? .paste` (line 171 in init)
- **AutoSendKey enum**: lines 3-21 (separate file would be better but it's here)
  - Cases: `.none`, `.enter`, `.shiftEnter`, `.commandEnter`
  - Used in: ModeConfig.autoSendKey field (line 86)

**Runtime Resolution:**
- **ModeRuntimeConfiguration.swift:129-138** — `outputConfiguration(mode:)` factory
  - Returns `OutputRuntimeConfiguration { outputMode, autoSendKey, customCommand }`
  - Resolved at recognition time before delivery

**Delivery Orchestration:**
- **TranscriptionDelivery.swift:25-52** — `deliver(_:actions:)` main dispatcher
  - Line 36-39: checks `request.output.outputMode == .respond` → call `deliverResponse()`
  - Line 42-44: checks `request.output.outputMode == .customCommand` → call `deliverCustomCommand()`
  - Lines 47-51: **default path** (paste or **typeOut**) → calls `paste()` with output config
  - **Line 150-168** — `paste(_:output:actions:)` implementation
    - Line 157: calls `CursorPaster.startPasteAtCursor(pastedText)`
    - **Must be refactored here** to switch on `output.outputMode` and call type-out path instead for `.typeOut` case

### 2. Paste Implementation & CGEvent Synthesis
**File: /Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk/VoiceInk/Paste/CursorPaster.swift**

**Entry point:**
- Line 24-31: `pasteAtCursor(_ text: String)` — async wrapper
- Line 35-39: `startPasteAtCursor(_ text: String)` — returns Task, @MainActor

**Paste session orchestration:**
- Lines 47-75: `performPasteSession(_:)` private method
  - Snapshots/restores clipboard (lines 48-86)
  - Line 53-60: `ClipboardManager.setClipboard()` sets text via NSPasteboard
  - Line 64: calls `postPasteCommand()` which dispatches to AppleScript or CGEvent

**CGEvent synthesis (paste via Cmd+V):**
- Lines 179-208: `pasteFromClipboard()` async method
  - Line 180: **AXIsProcessTrusted() gate** — returns `.commandNotPosted` if accessibility permission missing
  - Lines 185-193: creates CGEvent Cmd+V sequence
    - Virtual key 0x37 = Command, 0x09 = V
    - Source: `CGEventSource(stateID: .privateState)`
  - Lines 199-205: posts to `.cghidEventTap` (global tap)
  - **Delays**: lines 200-204 have `pasteShortcutEventDelay` (0.01s = 10ms) **between event pairs**

**Clipboard restoration:**
- Lines 97-127: `scheduleClipboardRestore()` — async restoration with 250ms minimum delay

**Auto-Send (Return keystroke):**
- Lines 218-239: `performAutoSend(_ key: AutoSendKey)` static method
  - Line 223-224: creates Return keyDown/keyUp (virtual key 0x24 = Return)
  - Line 230-234: applies shift/command modifiers if needed
  - Line 237-238: posts keyDown then keyUp to `.cghidEventTap`
  - **No delay** between Return down/up events

**Timing constants:**
- Line 20: `prePasteDelay = 0.10` (100ms before posting Cmd+V)
- Line 21: `pasteShortcutEventDelay = 0.01` (10ms between modifier/key/up events)
- Line 22: `minimumClipboardRestoreDelay = 0.25` (250ms before restoring clipboard)

### 3. Existing Keystroke-Typing Code

**SwiftPM Package: KeySender**
- **Path**: `/Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk/.local-build/SourcePackages/checkouts/KeySender/Sources/KeySender/KeySender.swift`
- **Key findings**:
  - Lines 76-91: `init(for string: String) throws` creates per-character KeyEvent array by iterating characters
  - Lines 146-149: `send(to:sendKeyUp:)` loops through events and calls `sendLocally()` per event
  - Lines 125-130: `sendLocally()` posts keyDown then keyUp via `cgEvent(from:keyDown:)` → `postToPid()`
  - **No per-character delay** visible; caller must add delays if needed
  - Uses: `CGEvent(keyboardEventSource:virtualKey:keyDown:)` with `postToPid()` for app-targeted injection

**KeyEvent.swift**:
- Lines 113-122: `cgEvent(from:keyDown:)` creates CGEvent from KeyEvent
  - Uses `.hidSystemState` (not `.privateState` like paste does)
  - Applies modifier flags from KeyEvent.Modifier enum

**No delays observed in KeySender itself** — throttling would be added by caller.

### 4. Auto-Send
**File: /Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk/VoiceInk/Modes/ModeConfig.swift**
- **AutoSendKey enum**: lines 3-21
  - Cases: `.none` (disabled), `.enter`, `.shiftEnter`, `.commandEnter`
  - `isEnabled` computed property (line 18): `self != .none`
  - `displayName` (lines 9-16): user-facing labels (Return ⏎, Shift+Return ⇧⏎, Cmd+Return ⌘⏎)
  - Stored in `ModeConfig.autoSendKey` field (line 86, default `.none`)

**Auto-Send invocation:**
- **TranscriptionDelivery.swift:159-167**
  - Line 159: only enabled if `output.outputMode == .paste` (NOT for `.respond` or `.customCommand`)
  - Line 164: 500ms delay before auto-send (Task.sleep 500_000_000 nanoseconds)
  - Line 165: calls `CursorPaster.performAutoSend(autoSendKey)`

**Keystroke synthesis:**
- **CursorPaster.swift:218-239**
  - Lines 223-224: Return key (virtual key 0x24) keyDown/keyUp
  - Lines 227-235: switch on key variant to add shift/command modifiers
  - Line 237-238: posts both events to `.cghidEventTap`

### 5. Mode UI for Output Mode
**File: /Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk/VoiceInk/Modes/ModeConfigFormView.swift**
- **Advanced section**: lines 511-549
  - Line 513-521: Output mode Picker
    - Selection binding: `$draft.outputMode`
    - Choices: `outputChoices` property (line 497-499) calls `ModeOutputMode.choices(canRespond:)`
    - UI labels + icons from `outputMode.displayName` + `outputMode.iconName`
  - **Auto-Send Picker**: lines 532-543
    - Only visible when `draft.outputMode.usesPasteOptions` (i.e., `.paste` only)
    - Selection binding: `$draft.autoSendKey`
    - Displays all `AutoSendKey.allCases` with their `displayName`

**Where to add new option**:
- Add `.typeOut` case to `ModeOutputMode` enum (ModeConfig.swift:23-51)
- Update `usesPasteOptions` (line 44) to return `false` for `.typeOut` OR to exclude AutoSendKey picker for `.typeOut`
- Form UI automatically shows new case in picker (lines 513-521)

### 6. App-Trigger Matching
**Bundle ID Matching: Exact Equality**
- **ModeConfig.swift:349-356** — `getConfigurationForApp(_:)` method
  - Line 351: `config.allAppConfigs.contains(where: { $0.bundleIdentifier == bundleId })`
  - **Matching is exact**: `==`, not substring/prefix match
  - Frontmost app's bundle ID obtained from `NSWorkspace.shared.frontmostApplication?.bundleIdentifier`

**AppConfig structure:**
- **ModeConfig.swift:227-241**
  - Fields: `id: UUID`, `bundleIdentifier: String`, `appName: String`
  - No prefix/wildcard support

**Auto-activation flow:**
- **ActiveWindowService.swift:19-67** — `beginApplyingConfiguration(modeId:)`
  - Line 30-31: gets frontmost app from `NSWorkspace.shared.frontmostApplication`
  - Line 38: calls `ModeManager.getConfigurationForApp(bundleIdentifier)`
  - Line 39: falls back to default config if no app match
  - Line 41-42: applies matched config via `ModeManager.setActiveConfiguration()`

**App selection UI:**
- **TriggerInstalledApps.swift:6-66** — `InstalledApps.load()` static method
  - Scans `/Applications` at user/local/system domains (lines 8-10)
  - Extracts bundle ID via `bundle.bundleIdentifier` (line 48)
  - Returns array of `InstalledAppInfo = (url, name, bundleId, icon)` sorted by name

**App picker in mode form:**
- **ModeTriggerSelectionView.swift, TriggerSelectionItems.swift** — app selection UI
  - User picks from running or installed apps, app is added as `AppConfig` to `appConfigs` array
  - No wildcarding; exact bundle ID stored

### 7. Per-Character / Typing Delay & CGEvent Throttling Patterns

**Existing delays in paste flow:**
- **CursorPaster.swift:20-22**
  - 100ms (`prePasteDelay`) **before** the entire Cmd+V sequence
  - 10ms (`pasteShortcutEventDelay`) **between** individual modifier/key/release events in Cmd+V (lines 200-205)
  - 250ms minimum (`minimumClipboardRestoreDelay`) before clipboard restore

**Auto-Send delay:**
- **TranscriptionDelivery.swift:164** — 500ms before Return keystroke

**KeySender package (for type-out):**
- **No delays** in the KeySender loops; delays must be injected by caller
- Pattern: loop per event, `sendLocally()` posts keyDown then keyUp

**Recommended type-out delays (not yet implemented):**
- **Per-character delay**: typically 10-50ms between character keystrokes to avoid overwhelming terminal buffers
- **Pre-type delay**: 100ms (reuse `prePasteDelay`) before typing begins (similar to paste)
- **Post-type delay**: before auto-send (already 500ms, covers type completion)

**Thread safety:**
- All CGEvent posting is `@MainActor` in CursorPaster
- KeySender operates on the calling thread; no explicit main-actor annotation (would need wrapping)

---

## Suggested Minimal-Diff Insertion Plan

**Phase 3.1: Enum & Config Updates** (Smallest, safest diffs)
1. **ModeConfig.swift** — Add `.typeOut` case to `ModeOutputMode` enum (1 line + display name + icon)
2. **ModeConfig.swift** — Update CodingKeys if needed (none needed, auto-derived)

**Phase 3.2: Paste Implementation Refactor** (Medium diff, localized)
3. **CursorPaster.swift** — Add `typeOut(_ text: String, ...)` method (new function, ~40 lines)
   - Loops per character
   - Applies delay between characters
   - Uses KeySender or inline CGEvent per-character loop
4. **TranscriptionDelivery.swift** — Refactor `paste()` to dispatch on `output.outputMode`
   - Line 150-168: wrap existing Cmd+V logic in `if output.outputMode == .paste { ... }`
   - Add `else if output.outputMode == .typeOut { ... }` branch

**Phase 3.3: UI Updates** (No logic, safe)
5. **ModeConfigFormView.swift** — No changes needed; picker auto-includes new case
   - Auto-Send picker already guards with `usesPasteOptions`, no update required (unless you want to show/hide for typeOut differently)

**Phase 3.4: Integration Tests & Validation**
6. Add unit test for `CursorPaster.typeOut()` per-character loop
7. Test terminal modes (Terminal.app, iTerm2, VS Code, Ghostty) with type-out mode enabled
8. Verify auto-send delay (500ms) works after type-out completes

---

## Notes for Implementation

- **No clipboard needed for type-out** — avoids clipboard save/restore overhead
- **Accessibility permission still required** — AXIsProcessTrusted() gates keystroke injection
- **App matching remains exact** — bundle ID equality, no wildcard
- **Auto-Send logic** — only enabled for `.paste` mode, might want same for `.typeOut`; decide per UX
- **Realtime transcription** — isRealtimeTranscriptionEnabled is display-mode only, not delivery; type-out flows through `paste()` at end of recording, no streaming during recording
