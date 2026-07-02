---
name: macos-permissions
description: Handle macOS permissions, entitlements, signing, and distribution for the fork — Microphone (NSMicrophoneUsageDescription) and Accessibility (runtime TCC) permissions, Hardened Runtime, Developer ID signing, and notarized/direct distribution (NOT the Mac App Store). Use when handling permission prompts, editing Info.plist/entitlements, debugging "can't record" or "can't type" failures, or preparing a build for distribution (PRD §9).
when_to_use: microphone permission, accessibility permission, TCC, Info.plist, entitlements, code signing, notarization, distribution, App Store rejection, "not typing" / "not recording"
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# macOS permissions, entitlements & distribution (PRD §9)

Two permissions gate the whole app. Distribution is direct/notarized, not Mac App Store.

## Microphone
- Requires `NSMicrophoneUsageDescription` (non-empty reason) in **Info.plist**. Missing/blank → macOS
  denies recording.
- Granted via the standard prompt; user can toggle in System Settings → Privacy & Security → Microphone.
- Symptom of failure: hotkey records nothing / silent transcript.

## Accessibility (required for hotkey CGEvents + keystroke injection)
- **Runtime TCC grant**, not a plist key. Check `AXIsProcessTrusted()`; if false, prompt the user to
  enable the app under System Settings → Privacy & Security → **Accessibility**.
- Symptom of failure: recording works but no text is typed / global hotkey doesn't fire.
- After granting, a relaunch is sometimes needed for CGEvent posting to take effect.

## Entitlements & signing
- **Do NOT add the App Sandbox** (`com.apple.security.app-sandbox`) — it breaks CGEvent injection and
  global event taps, and the Mac App Store rejects Accessibility-API text injection regardless.
- Use **Hardened Runtime** + **Developer ID Application** signing so the app can be **notarized**.
- Sign, notarize, and staple for direct distribution:
  ```
  codesign --deep --force --options runtime --sign "Developer ID Application: <name>" <App>.app
  xcrun notarytool submit <App>.zip --keychain-profile <profile> --wait
  xcrun stapler staple <App>.app
  ```

## Distribution & license
- Ship a **notarized direct build** — not the Mac App Store (Accessibility-API policy blocks it).
- **GPL v3**: fork/modify freely for personal use; if ever distributed, keep GPL notices and publish
  source.

## Debug checklist
- No audio → Microphone permission + `NSMicrophoneUsageDescription`.
- No typed text / hotkey dead → Accessibility grant + `AXIsProcessTrusted()` + relaunch.
- Won't launch after signing → Hardened Runtime/entitlements/notarization mismatch.
