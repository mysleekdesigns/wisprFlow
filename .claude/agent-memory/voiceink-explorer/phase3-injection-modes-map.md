---
name: phase3-injection-modes-map
description: VoiceInk Phase 3 code map — Power Mode routing, CGEvent injection paths, auto-send, vocabulary, type-out insertion points
metadata:
  type: project
---

# Phase 3 Code Map — Power Mode + Injection Routing

**As of:** 2026-07-08
**Verified against:** VoiceInk fork at `/Users/simonlacey/Documents/GitHub/wisprFlow/VoiceInk`

## 1. Power Mode / Modes System (Auto-Activation + Profile Selection)

**Entry point:** `VoiceInk/Modes/ActiveWindowService.swift:19–67`
- Line 30: `NSWorkspace.shared.frontmostApplication` detects app switch
- Line 38: `getConfigurationForApp(bundleId)` queries ModeManager for matching profile
- Line 42: `setActiveConfiguration()` activates the matched profile

**Data model:** `VoiceInk/Modes/ModeConfig.swift:66–90`
- Line 70: `appConfigs: [AppConfig]?` — bundle-ID configs for matching
- Line 85: `outputMode: ModeOutputMode = .paste` — per-profile output method
- Line 86: `autoSendKey: AutoSendKey = .none` — per-profile auto-submit key

**Matching logic:** `VoiceInk/Modes/ModeConfig.swift:349–356`
- `getConfigurationForApp(_:)` — exact bundle-ID match against appConfigs array
- Falls back to default profile if no match

**Runtime resolution:** `VoiceInk/Modes/ModeRuntimeConfiguration.swift:129–138`
- `outputConfiguration(mode:)` — reads active mode's outputMode + autoSendKey, returns OutputRuntimeConfiguration
- Defaults: `.paste`, `.none`

**UI for profile creation/editing:** `VoiceInk/Modes/ModeConfigFormView.swift:513–521`
- Output picker shows ModeOutputMode choices
- Auto-Send picker appears only if outputMode == .paste (line 532–543)

---

## 2. Injection / Output Path (Currently Clipboard Cmd+V Only)

**Entry point:** `VoiceInk/Transcription/Engine/TranscriptionDelivery.swift:150–168`
- Line 48: Routes to `paste()` if outputMode == .paste (the default)
- Line 157: Calls `CursorPaster.startPasteAtCursor()`
- Line 159: Gets autoSendKey from output config (only if paste mode)

**Paste implementation:** `VoiceInk/Paste/CursorPaster.swift:24–31` (entry)
- `pasteAtCursor()` — public async entry point
- Delegates to `startPasteAtCursor()` → `performPasteSession()` (lines 33–75)

**CGEvent Cmd+V:** `VoiceInk/Paste/CursorPaster.swift:179–208`
- Line 185: Creates CGEventSource
- Lines 187–190: Creates Cmd (0x37) + V (0x09) key events
- Lines 199–205: Posts events via `.cghidEventTap`
- NO per-character typing code; all text enters via clipboard

**AppleScript variant:** `VoiceInk/Paste/CursorPaster.swift:161–173`
- Used when keyboard layout switches to QWERTY on Command (e.g., "X – QWERTY ⌘")
- Key code 9 bypasses layout translation

**Key methods:**
- `pasteFromClipboard()` (async CGEvent) — line 179–208
- `pasteUsingAppleScript()` (sync) — line 161–173
- Both gate on `AXIsProcessTrusted()` for Accessibility permission

**Confirmed missing:** No `CGEventKeyboardSetUnicodeString`, `typeOut`, or per-character keystroke injection anywhere in codebase. grep verified.

---

## 3. Auto-Send (Return / Shift+Return / Cmd+Return after Paste)

**Data model:** `VoiceInk/Modes/ModeConfig.swift:3–21`
- Enum AutoSendKey: `.none`, `.enter`, `.shiftEnter`, `.commandEnter`
- Default: `.none` (line 86)

**Runtime resolution:** `VoiceInk/Modes/ModeRuntimeConfiguration.swift:129–138`
- Line 135: `autoSendKey: mode?.autoSendKey ?? .none`

**Execution:** `VoiceInk/Transcription/Engine/TranscriptionDelivery.swift:159–166`
- Line 159: Gets autoSendKey only if outputMode == .paste
- Line 163: Checks `autoSendKey.isEnabled` (true if != .none)
- Line 164: Delays 500 ms (hardcoded; could make configurable)
- Line 165: Calls `CursorPaster.performAutoSend(autoSendKey)`

**Implementation:** `VoiceInk/Paste/CursorPaster.swift:218–239`
- Lines 223–224: Creates Enter keyDown/keyUp (virtualKey 0x24)
- Lines 228–234: Applies flags based on key type (.maskShift / .maskCommand)
- Lines 237–238: Posts both events

**Notes:** Auto-send only fires for paste mode; respond and custom-command modes ignore it.

---

## 4. Custom Dictionary / Word Replacements

### Vocabulary (for LLM prompt injection)

**Data model:** `VoiceInk/Models/VocabularyWord.swift:4–13`
- SwiftData @Model: `word: String`, `dateAdded: Date`

**Service layer:** `VoiceInk/Services/CustomVocabularyService.swift:10–30`
- `getCustomVocabulary(from:)` — fetches all words, returns "Important Vocabulary: word1, word2, ..."
- `getCustomVocabularyWords()` (private) — SwiftData fetch + map

**LLM injection:** `VoiceInk/Services/AIEnhancement/AIEnhancementService.swift:137–149`
- Line 137: Calls customVocabularyService.getCustomVocabulary()
- Lines 139–149: Injects as "# Custom Vocabulary" markdown section in system message
- Instructions at line 142–145 tell LLM to use exact spellings for replacement

**UI for adding words:** `VoiceInk/Views/Dictionary/VocabularyView.swift:9–120`
- Line 45: Text input for new word(s)
- Line 97–106: `addWords()` — calls DictionaryService.addVocabularyWords()
- Line 77–83: Display vocabulary as tags with delete buttons

**Service for persistence:** `VoiceInk/Services/DictionaryService.swift:13–43`
- `addVocabularyWords()` — parses comma-separated input, deduplicates, inserts VocabularyWord records
- Line 29: Single word path
- Lines 32–42: Batch path (multiple comma-separated words)

**Pipeline position:** After ASR transcription, **before** LLM enhancement. Vocabulary is injected into the LLM's system prompt so Ollama can use it to correct/bias cleanup.

### Word Replacements (TextReplacement model)

**Data model:** `VoiceInk/Models/` — model exists (referenced in DictionaryService.swift:82–97)
- Fields: `originalText`, `replacementText`, `dateAdded`

**Status:** Model layer exists, but **no consumption logic found** in the codebase. Word replacements are collected but not applied to transcripts. Appears incomplete/future work.

---

## 5. Recommended Insertion Points for Type-Out Mode

**Currently:** No per-character keystroke injection exists. To add:

### Step 1: Extend data model
- **File:** `VoiceInk/Modes/ModeConfig.swift:23–27`
- **Change:** Add `case typeOut` to ModeOutputMode enum after `.paste`
- **Impact:** UI (ModeConfigFormView line 513–521 Picker) automatically shows new option via CaseIterable

### Step 2: Implement injection function
- **File:** `VoiceInk/Paste/CursorPaster.swift` (extend or new function)
- **New function signature:** `typeOutText(_ text: String, delayPerChar: TimeInterval = 0.01) async -> PasteResult`
- **Implementation:**
  ```
  Loop each character:
    - Create CGEventSource
    - Create CGEventCreateKeyboardEvent(source, 0, keyDown: true)
    - Call CGEventKeyboardSetUnicodeString(event, 1, char)
    - Post keyDown event
    - Sleep delayPerChar
    - Post keyUp event
    - Sleep delayPerChar
  Gate on AXIsProcessTrusted() (line 180 model)
  ```

### Step 3: Route in delivery pipeline
- **File:** `VoiceInk/Transcription/Engine/TranscriptionDelivery.swift:47–51`
- **Change:** Add branch before paste() call:
  ```swift
  if request.output.outputMode == .typeOut,
     let text = request.text {
      await typeOut(text, output: request.output, actions: actions)
      return
  }
  ```
- **New function:** `typeOut()` — similar structure to paste(), calls CursorPaster.typeOutText(), does NOT apply autoSendKey

### Step 4: Optional UI enhancements
- **File:** `VoiceInk/Modes/ModeConfigFormView.swift:532–543`
- **Option A (minimal):** No additional UI; accept default character delay
- **Option B:** Add expandable "Character Delay" setting visible only when outputMode == .typeOut (mirrors auto-send picker pattern)
- **File:** `VoiceInk/Modes/ModeConfigFormView.swift:507–509` (applyOutputRules)
- **Change:** Disable autoSendKey when outputMode == .typeOut (character typing handles submission differently than paste)

### Summary of insertion points
1. **Enum + UI:** ModeConfig.swift:23–27, ModeConfigFormView.swift:513–521 (automatic)
2. **Injection logic:** CursorPaster.swift (new typeOutText function)
3. **Pipeline routing:** TranscriptionDelivery.swift:47–51 (new branch before paste)
4. **Optional UI:** ModeConfigFormView.swift:532–543 (character delay field) + applyOutputRules logic
