---
name: ollama-cleanup
description: Wire and tune the local Ollama cleanup/enhancement layer — endpoint localhost:11434, a small text model, and the light-touch cleanup prompts (a general one and a Claude Code / terminal one). Use when configuring or editing the AI enhancement service, writing/adjusting the cleanup prompt, or testing offline text cleanup (Phase 2, PRD §7).
when_to_use: Ollama, enhancement/cleanup layer, cleanup prompt, filler-word removal, local LLM formatting, Phase 2
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Local Ollama cleanup layer (PRD Phase 2 + §7)

Optional post-ASR pass that removes filler and fixes punctuation. **Text-only** — Ollama cannot
transcribe. Must run fully offline.

## Configure
- Provider: **Ollama**. Endpoint: `http://localhost:11434`. Model: a small pulled model
  (`llama3.2:3b` or `qwen2.5:3b`).
- Confirm reachable: `curl -s http://localhost:11434/api/tags` and `ollama list`.
- Target latency: cleanup **< ~1s**. If slower, use a smaller/quantized model or shorten the prompt.
- The ASR path must be **independent** of Ollama: if Ollama is down, the raw transcript still injects.

## Prompts (use verbatim; keep them minimal)
**General (non-terminal apps):**
> You clean up dictated speech. Remove filler words (um, uh, like), fix grammar, punctuation, and
> capitalization. Preserve the speaker's meaning and wording. Output ONLY the cleaned text.

**Claude Code / Terminal profile (light-touch — this is what matters for coding):**
> You clean up a spoken instruction to a coding assistant. Remove filler words and fix punctuation and
> capitalization only. Do NOT rephrase, summarize, translate to prose, or add markdown/code fences.
> Preserve technical terms, file paths, command names, and identifiers exactly as heard. Output ONLY
> the cleaned instruction.

Key point: for prompts *to a coding agent* we want filler removal + punctuation ONLY — never reformat
into prose/markdown or "helpfully" rewrite the instruction.

## Test
1. Speak a filler-heavy sentence → confirm cleaned output.
2. Do it with **network off** (airplane mode) → still works.
3. Speak a technical instruction with a file path and identifier → confirm they survive verbatim under
   the terminal prompt.
4. Stop Ollama (`ollama stop` / quit) → confirm the raw transcript still injects.

## Where to implement
The enhancement service (URLSession call + per-profile prompt selection) is the **main
customization**. Use `voiceink-explorer` to find it, then keep edits minimal (GPL fork).
