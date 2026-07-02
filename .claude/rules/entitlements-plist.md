---
paths:
  - "**/*.plist"
  - "**/*.entitlements"
---

# Info.plist & entitlements (permissions + distribution)

This app needs Microphone and Accessibility access and is distributed **outside** the Mac App Store.
Get these right or the app silently fails to record or inject text.

## Required Info.plist keys
- `NSMicrophoneUsageDescription` — user-facing reason for mic access. Must be present and non-empty or
  recording is denied. Keep any existing string; don't blank it.
- Do **not** expect an Accessibility Info.plist key — Accessibility is a **runtime TCC grant**
  (`AXIsProcessTrusted()` / System Settings → Privacy & Security → Accessibility), not a plist entry.

## Entitlements & signing
- **Do not add the App Sandbox entitlement** (`com.apple.security.app-sandbox`). The sandbox blocks
  the CGEvent keystroke injection and global event taps this app depends on, and Mac App Store review
  rejects Accessibility-API text injection anyway.
- Use **Hardened Runtime** and **Developer ID** signing so the app can be **notarized** for direct
  distribution.
- Keep the microphone/audio-input hardened-runtime entitlement if the fork sets it.

## Distribution
- Ship a **notarized, direct/Developer-ID build** — not the Mac App Store.
- License is **GPL v3**: if the build is ever distributed, publish the source and keep GPL notices.

Before editing any permission string or entitlement, prefer running `/macos-permissions` for the full
context and the exact keys/flags.
