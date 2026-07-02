---
name: asr-config
description: Choose and tune the local ASR (speech-to-text) engine — whisper.cpp (Metal) vs FluidAudio/Parakeet-TDT (Apple Neural Engine), model selection (parakeet-tdt-v3, whisper-large-v3-turbo), downloads, and latency tuning. Use when configuring transcription, picking or downloading a model, choosing between engines, or reducing dictation latency (PRD §5, §8).
when_to_use: ASR, speech-to-text, transcription, whisper.cpp, Parakeet, FluidAudio, model selection, latency, key-release-to-text delay
allowed-tools: Read, Grep, Glob, Bash
---

# Local ASR engine selection & tuning (PRD §5, §8)

The ASR engine turns recorded audio into a raw transcript, fully on-device. Two families ship in the
VoiceInk lineage.

## Choose the engine
- **Parakeet-TDT v3 (Apple Neural Engine, via FluidAudio)** — fastest on Apple Silicon, **English**.
  Recommended default for the Claude Code use case (English coding prompts, lowest latency;
  ~100ms key-release→text is achievable, cf. the `parakey` reference project).
- **whisper.cpp (Metal)** — mature, broad model choice. Use **whisper-large-v3-turbo** when you need
  **multilingual** or want whisper's accuracy profile.

Rule of thumb: English-only + latency-sensitive → Parakeet-TDT v3. Multilingual → whisper-large-v3-turbo.

## Configure & download
- Pick the engine in the app's transcription settings, then download the model in-app.
- Keep models on-device; verify no network is needed at inference time (airplane-mode test).
- Set the global hotkey (KeyboardShortcuts) if not already set.

## Tune for lowest latency
- Prefer the ANE (Parakeet) path on Apple Silicon over CPU/Metal when English suffices.
- Smaller/turbo models reduce end-to-end delay; measure key-release → text.
- Keep the optional Ollama cleanup fast and independent so ASR latency isn't compounded
  (see `/ollama-cleanup`).
- (Later/optional) streaming or partial transcripts for perceived speed.

## Where to implement
Model/engine config and download live in the ASR layer. Use `voiceink-explorer` to locate the
whisper.cpp vs FluidAudio/Parakeet code paths and model-selection logic before changing defaults.
