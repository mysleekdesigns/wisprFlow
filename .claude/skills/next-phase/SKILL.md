---
name: next-phase
description: Advance the build by one PRD phase using sub-agents launched in parallel. Detects the current phase from repo state + PRD §6 checkboxes, decomposes the next unfinished phase into independent workstreams, launches the right sub-agents (voiceink-explorer, build-doctor, general-purpose, swift-reviewer) concurrently, then synthesizes their output into a concrete change set and the human-in-the-loop steps that remain. Use to kick off or drive the next phase of the project.
when_to_use: "what's next", start/advance the next phase, parallelize phase work, "work on phase N", move the build forward, fan out agents on the PRD
---

# Advance the PRD by one phase (parallel fan-out)

Purpose: take the project to the **next unfinished PRD phase** by fanning out its independent
workstreams to sub-agents that run **concurrently**, then merging their output into a concrete change
set plus the human steps only Simon can do (speak into the mic, grant TCC, click Build in Xcode).

## The one invariant
Everything stays **100% local / offline** (PRD §2, CLAUDE.md §"The one invariant"). No agent may
introduce a cloud ASR or cloud LLM. Keep the GPL-v3 fork changes minimal and rebase-friendly.

## Step 1 — Detect the current phase
Determine it from state; don't ask the user unless truly blocked. Run these probes:
- **Fork cloned?** `find . -maxdepth 3 -name '*.xcodeproj' -o -name 'BUILDING.md' 2>/dev/null | head`.
  Also check the session env status line ("VoiceInk fork: NOT cloned yet").
- **PRD progress:** read `PRD.md` §6 and compare `[x]` vs `[ ]` per phase.
- **Ollama up?** session env status, or `curl -s localhost:11434/api/tags`.

**Next phase = the lowest-numbered phase in §6 that is not fully checked.** If the user passed a number
(e.g. `/next-phase 3`), use that instead. State the detected phase in one line before fanning out.

**Gate:** if the next phase needs the fork and it isn't cloned, do NOT fan out — route to
`/voiceink-setup`. Cloning needs Simon's fork URL + a GitHub fork (a human step). Say so and stop.

## Step 2 — Load the fan-out plan
Read `references/phase-plans.md` and pick the block for the detected phase. It lists the independent
workstreams, which sub-agent runs each, the exact task each gets, and the human/verify steps.

## Step 3 — Launch the sub-agents IN PARALLEL
Issue all of the phase's read-only + build agents as **multiple Agent tool calls in a single message**
so they run concurrently (per the harness guidance on parallel agents). Give each a tight,
self-contained prompt: repo path, what to produce, and "return `file:line` + a concrete recommendation;
change nothing unless your task explicitly says to."

Rules:
- `voiceink-explorer` and `swift-reviewer` are **read-only** — they map and review, they don't edit.
- **One editor per file.** If two workstreams touch the same Swift file, sequence them
  (map → edit → build → review); never run parallel edits on the same file.
- Keep each agent scoped to a single subsystem (PRD §8) so their contexts don't overlap.
- Prefer the matching per-phase skill for the actual wiring (`/ollama-cleanup`, `/terminal-injection`,
  `/asr-config`, `/macos-permissions`) — the fan-out gathers the facts; the skill applies them.

## Step 4 — Synthesize & report
Merge the agents' results into:
- **(a) Change set** — `file:line` + what to change, per subsystem.
- **(b) Config / prompts** — exact values and prompt text to set (from PRD §5/§7).
- **(c) Test plan** — the phase's PASS/FAIL checks.
- **(d) Human-in-the-loop steps** — build in Xcode, grant Microphone/Accessibility, speak the test
  sentence, toggle Auto-Send. These can't be automated; list them explicitly.

Then point to verification: run `/verify-pipeline` once the phase is wired, and offer to check off the
completed `[ ]` items in `PRD.md` §6.

## After
Re-run `/next-phase` to advance again once the human steps and `/verify-pipeline` for this phase pass.
