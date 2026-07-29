# Native Replay Physical Falsification

Use a shipped-game native replay when a hypothesis concerns native runtime
semantics and a repeatable physical scene is more informative than another
static or synthetic fixture. This is a physical observation method: TH08
executes its own replay stream, ECL, scheduler, timers, pools, and collision
state. It is not evidence that the solver can produce the replayed route.

## When this method is useful

- rechecking an IDA-derived field, callback, scheduler order, or ECL branch;
- reproducing a late spell or transition without adding controller input;
- comparing two observer/model versions against the same route and replay
  input;
- distinguishing an incorrect semantic hypothesis from route/RNG variation;
  and
- obtaining a compact causal witness before authorizing live integration.

Prefer the smallest replay and phase that exercises the hypothesis. A native
replay is particularly useful for Stage 3, Stage 4A, Stage 5, and Final B,
but it does not replace fresh normal-start physical acceptance for those
workloads.

## Required protocol

1. Parse the `.rpy` offline first. Retain its SHA-256, route, difficulty,
   represented stages, input-record count, input digest, and Bomb presses.
2. Bind the exact replay slot and file hash before launch. TH08 compacts
   successfully decoded replay entries, so verify the native selected entry
   and stage rather than assuming that a visible row equals an on-disk slot.
3. Before accepting gameplay, verify executable identity, required patch
   bytes, replay-mode flag, route, difficulty, and stage through native state.
4. Input is permitted only for deterministic menu navigation. Once gameplay
   begins, the experiment is read-only: no solver movement, firing, Bomb,
   confirmation, foreground change, or Windows CLI probe.
5. Observe the predeclared native trigger. Bracket every multi-read capture
   with the physical frame/phase and every state field needed by the
   hypothesis. Reject identity drift, frame crossing, partial pool scans, and
   unsupported source multiplicity.
6. Generate a strict compact report independently from the capture. Preserve
   failed attempts as counterexamples when they falsify a trigger, capture, or
   authority assumption.
7. Stop the exact game/supervisor, release all injected menu keys, verify
   cleanup, and retain compact artifacts. Raw captures follow the two-newest
   replay-capable-bundle rule and remain ignored.

Do not probe the Windows process from a foreground-stealing shell during
gameplay. The supervisor owns launch, monitoring, stop, and cleanup.

## Evidence authority

Label separately:

- **Observed:** exact binary/replay/runtime identities and native fields read
  from one coherently bracketed physical execution.
- **Inferred:** the model or schedule reconstructed from those fields under
  its declared continuation and source-completeness assumptions.
- **Not proved:** solver action authority, a clean no-miss/no-Bomb route,
  generalization to another replay/RNG/resource history, or NMNB.

Replay state can contain prior deaths, Bombs, Power changes, or patched death
residue. A stable nonzero predeath/death field is contamination that must be
retained, but it is not automatically a fresh hit at the semantic root.
Conversely, a zero Bomb bit at the observed root does not prove the replay
never Bombed; inspect the replay input stream and relevant history.

Repeated native replay observations reduce route and input confounding, but
they are not independent clean-route samples. The first hit rule still
applies when a replay is used to study survival.

## Retained Final-B example

The first accepted use is `SEM-SCALE-C4` on 2026-07-29:

- replay `th8_13.rpy`, SHA-256
  `1026289ffec9f3dd1858378e81bbbbb84f568f041047a401dd86f74211c4a7f2`;
- Route 2, Lunatic, Final B, 51,711 input records, input SHA-256
  `90c75156cf36a1c1576f082b2fe2b435cec8395af09014a1ad6c10c02e7a060e`,
  and zero replay Bomb presses;
- exact replay/runtime binding plus a read-only spell-190 observer launched by
  `run_th08_finalb_scale_source_replay_trial.bat`; and
- accepted capture/report
  `artifacts/runtime_reports/finalb_scale_source_replay_20260729_215613.json`
  and
  `artifacts/runtime_reports/finalb_scale_source_replay_20260729_215613_report.json`.

The accepted physical root is manager frame 74787 at binary32 scale `0.25`.
It contains one valid spell-owner main VM, no auxiliary VM, no installed
scale callback, and a complete 300-frame schedule whose sole callback-18
write restores unit scale at relative frame 240. The stable predeath counter
is 7, so this passes the source-semantic gate only. It does not establish a
clean player root, survival, or NMNB.

Reproduce the compact report after a capture with:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_finalb_scale_source_trace_report.py \
  artifacts/runtime_reports/finalb_scale_source_replay_20260729_215613.json \
  artifacts/runtime_reports/finalb_scale_source_replay_20260729_215613_report.json
```
