# Final-B SEM-SCALE Stage-Launched Live Delivery Gate

This is the preregistered original-game `SEM-SCALE-C5` falsifier after the
read-only C4 native-replay gate. THPRAC is not available. The existing
unattended Practice Start supervisor selects the whole Lunatic Final B
(`6b`) stage and runs until native spell ID 190. The controller stops
automatically after the predicted quarter-to-unit restore.

This gate separates two scopes:

- **pre-target transport:** an explicit unknown-direction unit-scale
  approximation lets the existing solver traverse Final B from its stage
  start. It is proposal-only and has no hard scale authority; and
- **exact C5 scope:** begins at the coherent spell-190 quarter-scale source
  capture. Only this interval through the first sampled unit-scale row can
  pass the delivery gate.

The run is not a clean Final-B stage pass or Lunatic NMNB result merely
because the exact C5 scope passes. Pre-target hits, Power, position, and
death-patch residue remain visible and are reported separately.

## Fixed launch

- shipped `th08.exe` SHA-256
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
- verified no-life-decrement patch;
- original-game Practice Start, Lunatic, Sakuya/Remilia, Final B (`6b`,
  native stage-route index 7);
- decoded `ecldata7.ecl` SHA-256
  `20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734`;
- hard no-Bomb for the entire trial; and
- no birth, combat, Power, unfocused-shot, ranking, shadow, or other
  experiment flags.

Run non-interactively from WSL:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_finalb_scale_live_trial.bat' \
  --status-seconds 15 --stall-timeout 120
```

The BAT delegates to the existing original-game practice supervisor. It
performs native menu selection, executable/patch/foreground verification,
prewarms the controller before final stage confirm, monitors the exact
interop process and trace, and always releases keys and terminates the
identity-verified game in cleanup.

Do not run Windows CLI probes during gameplay. WSL launch return is not
supervisor completion.

## Pre-target transport boundary

Before exact spell-190 authority exists, a sampled unit root receives a
256-frame constant unit schedule with provenance
`experimental_pretarget_unit_transport_unknown_direction`. This schedule may
drive the local and corridor policies, but its sensing row has
`hard_authority=false`; its repeated 256-frame tuples are omitted from raw
trace rows with `phase_schedule_omitted=true`. It is an explicit physical
transport experiment, not proof that no hidden writer exists.

If a pre-target root is non-unit and complete source is not due, the
controller waits without issuing input. Pre-target hit and resource history
do not become independent clean samples. The first hit of the fresh stage
attempt remains the canonical stage counterexample.

## Exact-scope acceptance

All of the following must pass:

- exact executable, patch, route, difficulty, stage, foreground, and runtime
  ECL identities;
- exactly one Bomb-zero, coherent 480-slot plus spell-owner source capture
  at spell 190 whose capture frame equals the controller root;
- one observed predeath baseline stable inside the source transaction and
  unchanged through the exact scope. Baseline zero is clean; nonzero residue
  is retained contamination and grants no clean-player authority;
- offset-zero exact live authority with the 300-frame schedule;
- every exact consumed row has one immutable
  gameplay/route/difficulty/stage/spell/source identity, the expected native
  root, complete remaining horizon, the same predeath baseline, and
  `live_exact_rebase` provenance;
- non-unit/varying exact coverage never enters the unsupported corridor;
- a sampled quarter row before relative frame 240 and a sampled unit row at
  or after 240, with callback 18 restoring `0.25 -> 1.0` at relative frame
  240 and no callback-28/29 bullet-velocity side effect;
- zero fresh hit edges and zero Bomb masks from exact offset zero through the
  first unit row;
- every pre-target decision is explicitly labeled experimental and every
  decision in the whole trial is no-Bomb;
- no exact-scope authority fallback, context/root/source mismatch, runtime
  error, or foreground loss; and
- automatic `finalb_scale_delivery_complete` termination plus exact
  supervisor/game cleanup.

The first fresh hit after offset zero is the canonical C5 failure witness.
Any mismatch stops promotion and is routed through
`notes/COUNTEREXAMPLES.md`.

## Artifacts and authority

The supervisor retains the normal raw trace/session/dossier/death attribution
without comparing this partial scope to a completed Stage-6B baseline. It
also emits:

```text
artifacts/runtime_reports/lunatic_route2_stage6b_finalb_scale_delivery_TIMESTAMP.scale_delivery_report.json
```

The strict report schema is
`th08-finalb-scale-live-delivery-physical-report-v2`. Raw JSONL remains local
and ignored; retain its SHA-256, the compact strict report, normal summary,
first-hit attribution, resources/Power, timing, and cleanup state.

A strict pass observes exact schedule delivery and no fresh hit/Bomb across
one physical restore interval. It does not prove the pre-target transport,
clean Final-B survival, another RNG/resource history, Stage 3/4A/5, a normal
Power-0 route, Extra, or Lunatic NMNB.
