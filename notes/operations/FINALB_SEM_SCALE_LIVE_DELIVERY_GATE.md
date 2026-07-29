# Final-B SEM-SCALE Live Delivery Gate

This is the preregistered smallest input-injecting falsifier after the
read-only `SEM-SCALE-C4` replay gate. It tests only exact scale-source
delivery through the native Final-B spell-190 quarter-to-unit transition.
It is not a Final-B stage pass or Lunatic NMNB attempt.

## Fixed scope

- shipped `th08.exe` SHA-256
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
- no-life-decrement patch verified before F8;
- THPRAC Lunatic Sakuya/Remilia Final-B checkpoint whose native spell ID is
  190;
- decoded `ecldata7.ecl` SHA-256
  `20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734`;
- hard no-Bomb; no observer, birth, combat, Power, unfocused-shot, ranking, or
  corridor experiment flags; and
- one fresh gameplay epoch. Manual pre-target movement is contamination
  outside the acceptance scope and must stop before source capture.

The controller may wait read-only while spell 190 is still at unit scale.
`finalb_scale_source_wait` changes no input. A fresh hit, Bomb-active state,
nonzero predeath counter, or any route/difficulty/stage/spell mismatch during
that wait terminates the run. The acceptance scope begins only when a
coherent clean-predeath quarter-scale source is captured and offset-zero live
authority is published.

## Launch and handoff

Prewarm the daemon before selecting the THPRAC checkpoint:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_finalb_scale_live_hotkey.bat' \
  --duration 600
```

Then:

1. start the exact patched game and THPRAC;
2. select Lunatic, Sakuya/Remilia, Final B, spell 190;
3. enter gameplay, release manual movement/fire keys, and press F8 once;
4. do not use a Windows console or foreground-stealing probe;
5. press F9 immediately after a physically observed unit-scale authority row
   beyond the predicted restore, or on any contamination; and
6. allow the one-shot daemon to finish and release all keys. F10 exits a
   daemon that was never armed.

Do not save or merge this THPRAC scope into a route result.

## Required acceptance evidence

All of the following must pass:

- exact executable, patch, route, difficulty, stage, foreground, and runtime
  ECL identity;
- controller config records hard no-Bomb and
  `finalb_scale_source_authority=true`;
- exactly one clean-predeath, Bomb-zero, coherent 480-slot plus spell-owner
  source capture whose capture frame equals the current controller root;
- offset-zero live authority with the exact 300-frame source schedule;
- each consumed row has the same immutable gameplay/route/difficulty/stage/
  spell/source version, expected physical root, complete remaining horizon,
  and `live_exact_rebase` provenance;
- no non-unit/varying corridor submission; the local planner consumes the
  schedule directly;
- a sampled quarter-scale row before relative frame 240 and a sampled
  unit-scale row at or after 240, with the callback-18 schedule write fixed at
  relative frame 240;
- zero native hit edges, zero Bomb decisions, and no issued mask containing
  bit `0x02` from offset zero through the first observed unit-scale row;
- no `time_scale_authority_unknown`, context mismatch, source mismatch,
  observed-root mismatch, deadline/epoch failure, or foreground loss; and
- exact supervisor/daemon/game cleanup.

The first fresh hit is the canonical failure witness. Any mismatch stops
physical promotion and is routed to `notes/COUNTEREXAMPLES.md`.

## Strict report

After the run:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_finalb_scale_live_delivery_report.py \
  artifacts/runtime_reports/TRACE.jsonl \
  artifacts/runtime_reports/TRACE_scale_delivery_report.json
```

The raw JSONL remains local and ignored. Retain the compact strict report,
the normal summary/dossier required by the physical-run contract, raw
SHA-256, exact scope, timings, cleanup state, and the two newest compatible
raw bundles.

## Authority on pass

A pass observes one clean physical transition with exact live schedule
delivery and no hit/Bomb in that bounded scope. It does not prove the rest of
Final B, another resource/RNG history, Stage 3/4A/5, a normal Power-0 route,
Extra, or Lunatic NMNB.
