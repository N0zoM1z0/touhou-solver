# G5 Complete-Mask Capsule Join Gate

Date: 2026-07-28

Status: offline audit implementation and joined physical capsule complete;
future-event modeling, CE-0141 physical recheck, delivery, and
action-authority gates remain open

## Result

Checkpoint `48f7e56` adds a fail-closed offline audit that joins one physical
decision trace row to:

- its content-addressed complete actuator root;
- the exact observed player coordinates and query frame;
- observation, hazard, policy, model, and clock versions;
- the replayed hazard-coverage assessment; and
- the retained corridor hazard capsule named by that same decision.

The audit then evaluates all 36 canonical no-Bomb complete-mask root actions
with the exact augmented belief recurrence. Later decisions use the exact
held complete-mask token as one declared stationary causal continuation.
Every root-action worst path replays, and the labels are checked against the
native belief implementation.

Physical workload `lunatic_route2_stage4a_unattended_20260728_005108` now
supplies both canonical roots and opted-in viability capsules. Its results
are retained in `notes/research/g5/G5_PHYSICAL_COMPLETE_MASK_CAPSULE_GATE_20260728.md`.

## Fail-Closed Join

`analysis.complete_mask_capsule.trace` reconstructs the canonical
`PipelineQueryIdentity` and recomputes its SHA-256 digest instead of trusting
the serialized digest. It also rebuilds `HazardCoverageAssessment` from every
serialized slab and requires the complete record to replay exactly.

A row is rejected from the joined set when any of these conditions holds:

- the identity or coverage record is malformed;
- a coverage slab is malformed, missing, overlapping, or does not replay;
- the viability and canonical query frames differ;
- the coverage root and canonical query frames differ;
- active, held, or pending input contains Bomb, unsupported, or invalid
  opposing-direction bits;
- pending/remaining-delay invariants fail;
- delay support is empty, non-positive, or omits its nominal delay; or
- the named capsule is absent from the requested retained directory.

Malformed JSONL lines and invalid eligible decision rows are retained as
explicit validation failures. They are not silently discarded as successful
roots.

## Exact Finite-Model Boundary

For one accepted root, `analysis.complete_mask_capsule.solve`:

1. checks capsule source/snapshot provenance against the canonical hazard
   version;
2. rebuilds the signed-clearance volume using the existing capsule oracle;
3. reconstructs the exact active/pending complete-mask belief;
4. completes all 36 unrestricted public root actions;
5. uses only the exact held desired token as the stationary continuation;
6. replays every deterministic worst branch; and
7. checks every root-action label against the native implementation.

The compact report labels these results:

```text
finite_model_authority = exact restricted stationary lower witness
physical_action_authority = none
```

An `UNKNOWN` slab intersecting the requested horizon yields
`physical_model_status = model_unknown` even if the finite capsule admits a
full-horizon witness. Missing future events are never interpreted as free
space or physical rescue evidence.

## Validation

**Observed:** focused tests cover digest tampering, exact coverage replay,
malformed slab rejection, malformed JSONL attribution, invalid delay support,
trace/root/capsule joining, all 36 no-Bomb root actions, deterministic
worst-path replay, and scalar/native label parity.

**Observed:** Linux/Windows quick tests pass `732/732` in `8.714/15.121 s`,
with three Windows platform skips. The new focused Windows file passes `6/6`
in `0.096 s`. Ruff, byte compilation, and staged diff checks pass.

**Inferred:** this closes the missing software join between exact
complete-mask physical roots and retained hazard capsules. It does not close
the evidence gate because prior physical traces contain either historical
movement-only capsules or canonical complete-mask roots without opted-in
capsules.

## Physical Evidence Result

The focused Lunatic Stage-4A run retained:

- 12,986 accepted canonical root/capsule joins;
- zero missing named capsules;
- 5,896 accepted Boolean-empty 32-frame roots;
- one retained all-36-action exact stationary witness with exact native
  parity; and
- fail-closed `UNKNOWN` coverage from its first successor frame.

It also exposed CE-0141: 1,613 rows mixed a canonical query root with coverage
rooted at an earlier manager frame. Checkpoint `d5866c4` corrects future trace
construction, but a small post-fix physical recheck remains required.

Cancellable native delivery and Windows contention are now the next
algorithmic gate. Even a successful joined exact witness remains
shadow/offline while future-event coverage is `UNKNOWN`, CE-0120 is open, or
a complete result cannot be looked up before issue time and intersected with
a fresh local hard certificate.
