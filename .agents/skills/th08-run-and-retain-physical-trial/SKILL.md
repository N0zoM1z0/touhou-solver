---
name: th08-run-and-retain-physical-trial
description: Run, supervise, clean up, and retain one explicitly authorized TH08 physical gameplay trial with a task-scoped preflight. Use only when the current user request asks to run or repeat a Lunatic, Extra, stage-practice, observer, or full-route physical gate. Do not use for analysis, documentation, handoff, or speculative gameplay.
---

# Run And Retain A TH08 Physical Trial

Run one authorized experiment without turning its preflight into a workspace
audit.

## Fix The Gate Once

1. Stop unless the current request explicitly authorizes physical gameplay.
2. Reuse current-turn context. If anything is missing, load only the current
   physical command, named gate/candidate, and direct baseline. Never reload
   every entrypoint, historical run, or counterexample.
3. Pin checkpoint, workload, route/team/difficulty/stage, candidate/version,
   flags, timeout, metric, fallback, and outputs in one concise update. Do not
   narrate each checklist step.
4. Keep hard no-Bomb. Never emit bit `0x02` unless the user explicitly
   authorizes a separately scoped Bomb experiment.

## Targeted Preflight

1. Use `START_HERE.md` and
   `notes/operations/UNATTENDED_PRACTICE_AUTOMATION.md` for the canonical
   wrapper and operating rules.
2. Check only affected dependencies: native builds only when changed; ECL
   identity only for Final-B/full-route or a consumer. Do not run broad
   suites, audits, or unrelated platform gates.
3. Always verify wrapper/output/disk space, no stale game or controller
   process, and a warm daemon. Before injection verify executable/patch,
   foreground, route/team/difficulty/stage, gameplay state, and no-Bomb.
4. Fail closed on any mismatch. Retain a failed attempt separately; do not
   silently retry with changed flags.

## Run And Retain

1. Launch one non-TTY supervisor. WSL return means creation, not completion.
   Monitor its exact process, trace, foreground, terminal summary, and session;
   avoid foreground-stealing Windows probes.
2. Record manual input, auto-confirm/focus/route failures, unexpected Bombs,
   and other contamination.
3. On success or error, use the supported stop, release all keys, and verify
   game/controller/supervisor/helper cleanup.
4. Keep raw logs ignored. Retain the compact scope, checkpoint/candidate,
   cleanup, hits/first hit, Bombs/resources/Power, phase, delivery/fallback,
   and replay/raw-bundle identity required by `AGENTS.md`.
5. Route concrete failures to
   `notes/counterexamples/CE-0220-0269.md`, as named by
   `notes/COUNTEREXAMPLES.md`, and chronology to `notes/RESEARCH_LOG.md`.
   Update handoff/strategy only when changed; make one focused commit without
   unrelated checks, reports, or documentation.
