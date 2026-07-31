---
name: th08-run-and-retain-physical-trial
description: Run, supervise, clean up, and retain one authorized TH08 physical gameplay trial. Use when the user explicitly asks to run or repeat a Lunatic, Extra, stage-practice, observer, or full-route physical gate and preserve reviewable evidence. Do not use to launch gameplay during analysis-only, documentation-only, or handoff work.
---

# Run And Retain A TH08 Physical Trial

Perform one explicitly authorized live-game experiment without broadening its
scope. Keep survival authority, observation authority, and offline evidence
separate.

## Establish The Contract

1. Resolve the repository root and read `AGENTS.md`, `GOAL.MD`,
   `START_HERE.md`, `STRATEGY.md`, the named experiment contract, and the
   latest relevant run and counterexample notes.
2. Stop before launch if the user did not authorize a physical trial in the
   current request.
3. Fix the code checkpoint, workload, route/team/difficulty/stage/phase,
   immutable model and observer versions, flags, timeout, acceptance gates,
   fallback, and evidence paths.
4. Preserve hard no-Bomb behavior. Never authorize or emit bit `0x02` unless
   the experiment contract and user explicitly require it.

## Preflight Without Side Effects

1. Use the current canonical commands from `START_HERE.md` and the operating
   contract in `notes/operations/UNATTENDED_PRACTICE_AUTOMATION.md`; do not
   copy a volatile launch command into this skill.
2. Validate Python imports, affected native libraries, BAT locations, output
   paths, executable identity, immutable ECL path/file/hash, and required
   patches before starting the game or controller.
3. Verify that no stale TH08, controller, or supervisor process can
   contaminate the trial.
4. Confirm the daemon is warm and the target window, route, difficulty,
   gameplay state, foreground ownership, and no-life-decrement patch are
   correct before injection.

## Run And Supervise

1. Launch exactly one non-TTY supervisor. Treat WSL launch return as process
   creation, not trial completion.
2. Monitor the exact interop/supervisor process, trace growth, foreground
   state, terminal summary, and session status. Avoid Windows CLI probes that
   can steal foreground during gameplay.
3. Record every manual confirmation, auto-confirm failure, foreground loss,
   route mismatch, unexpected Bomb, or other contamination.
4. Fail closed on identity, focus, schema, cadence, or evidence failure. Do
   not silently retry with changed flags; retain each attempt separately.

## Stop, Retain, And Report

1. Stop or exit through the supported control path, release all injected
   keys on success or error, and verify that the game, controller,
   supervisor, and helper processes are gone.
2. Keep raw JSONL and launch logs local and ignored. Preserve the two newest
   compatible replay-capable bundles required by `AGENTS.md`.
3. Retain compact scope, provenance, checkpoint, immutable versions,
   completion/cleanup status, hits, canonical first hit, Bombs, resources,
   items/Power, phase attribution, cadence, timing, and viability health.
4. Classify conclusions as observed, inferred, or hypothesized. A completed
   run does not promote a model or strategy by itself.
5. Route concrete failures directly to the current shard
   `notes/counterexamples/CE-0220-0269.md`, as named by
   `notes/COUNTEREXAMPLES.md`, and chronology through
   `notes/RESEARCH_LOG.md`. Update `START_HERE.md`, `STRATEGY.md`, compact
   evidence, and the focused counterexample only when the trial changes them,
   then make one focused English research-checkpoint commit.
