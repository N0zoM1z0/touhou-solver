# Stage-5 Enemy Combat-Progress Observation Contract

Date: 2026-07-28

Status: fixed after fresh shipped-instruction revalidation and before runtime
integration. This is a default-off, action-neutral observation gate under
`STAGE5_NONSPELL_COMBAT_PROGRESS_RESEARCH_CONTRACT_20260728.md`. It grants no
target, collection, damage, planner, feasibility, publication, or physical
action authority.

## Narrow Question

Can the already-paid stable first-64 ordinary-enemy pool capture expose a
bounded, reviewable health/damage inventory that is sufficient to begin
measuring nonspell exposure without adding process-memory reads or inferring
that every disappearing slot was killed?

The physical objective remains hard no-Bomb survival. The live Boolean policy,
fresh issue certificate, cadence, complete-mask/no-write semantics, and
fallback remain unchanged.

## Fresh Static Revalidation

All inherited IDA names, comments, types, and earlier notes were treated as
hypotheses. The following conclusions were revalidated directly from shipped
`th08.exe` instructions on 2026-07-28:

- `enemy_ecl_vm_step` dispatch case `0x83`:
  - `0x0041C97A` writes enemy `+0x2E00`;
  - `0x0041C989` writes enemy `+0x2DFC`;
  - `0x0041C998` writes enemy `+0x2E04`;
  - all three receive the same evaluated integer operand.
- `0x0042D070` clears enemy `+0x3354` before player-shot damage processing.
- The damage block requires local enemy flags:
  - player-shot damage bit `0x40` set;
  - blocking mask `0x830` clear;
  - flags2 update-blocked bit `0x80` clear;
  - additional global Bomb/player-transition conditions remain outside a
    slot-only inventory.
- `0x0042D349` subtracts the resolved player-shot damage from enemy
  `+0x2DFC`.
- `0x0042D355` writes the same resolved damage to enemy `+0x3354`.
- `0x0042D54B` tests current health and enters defeat/phase-end handling when
  health is nonpositive unless explicit control flags defer the transition.
- The later three-bit dispatch uses flags `(+0x3324 >> 20) & 7` to select
  different defeat/cleanup behavior.

These instructions operate on the common enemy object used by ordinary and
boss enemies. Existing boss runtime traces corroborate the offsets, but they
are not runtime proof for ordinary-enemy lifecycle classification.

IDA comments at `0x0041C989`, `0x0042D349`, `0x0042D355`, and `0x0042D54B`
were updated to record this revalidation and the remaining runtime boundary.

## Update-Order Consequence

One manager update can:

1. execute the enemy ECL/motion/phase block;
2. clear frame damage;
3. compute and commit player-shot damage;
4. publish that update's damage;
5. observe nonpositive current health; and
6. immediately run defeat/phase cleanup or deactivate the slot.

Therefore an external stable post-update capture may see either:

- an active enemy with positive HP and current-frame damage;
- an active enemy whose transition is explicitly deferred; or
- no active enemy because cleanup completed in the same update.

It is not guaranteed to expose an active `HP <= 0` sample. Slot disappearance,
pointer reuse, a nonpositive last HP, item appearance, or one positive damage
sample alone does not prove a player kill.

## Observation Schema

For each active slot in the fixed first-64 ordinary-enemy prefix, retain:

```text
slot
enemy pointer
raw flags and flags2
current / maximum / phase-start HP
current-update resolved player-shot damage
local damage-flag gate
three-bit defeat mode
```

The local gate means only:

```text
(flags & 0x40) != 0
and (flags & 0x830) == 0
and (flags2 & 0x80) == 0
```

It is not named `damageable`. Exact physical damageability additionally
depends on observed global Bomb/player-transition state, stable scheduling,
shot overlap, and other declared uncertainty.

Every inventory carries:

- schema/layout version;
- scanned and active slot counts;
- manager-frame before/after and attempt count from its owning capture;
- decode and serialization timing;
- exact field offsets/masks; and
- explicit authority `trace_only`.

No row is rejected merely because HP is zero/negative, maximum HP is zero, or
damage exceeds a guessed bound. Raw signed values remain evidence. Malformed
blob size, invalid pool geometry, or non-finite timing fails loudly.

## Identity And State Equivalence

An enemy pointer is the fixed address of one pool slot, not a stable enemy
generation. Two observations are the same combat history only when route,
stage, gameplay epoch, slot, an explicit inactive-to-active generation, and
the relevant source/phase identity agree.

This first checkpoint publishes capture-time rows only. It does not invent a
generation, kill event, despawn reason, damage attribution window, or
counterfactual action. A later tracker must classify:

- verified continuing generation;
- inactive-to-active generation start;
- health/damage progression;
- health defeat candidate;
- timeout/scripted/transition candidate;
- slot reuse; and
- unresolved end.

Hidden branches that produce the same available observation remain merged.
An analyzer may not select a favorable hidden kill/despawn cause.

## Existing Read Boundary

`capture_enemy_pool_prefix_contiguous` already reads
`pool_size * 0x53D0` bytes in one RPM call under a manager-frame bracket. That
blob contains the declared combat fields for every captured slot. The new
decoder must consume that immutable blob and issue zero additional RPM.

Ordinary planning and fresh issue recertification keep the option disabled.
Only an explicit trace option may request the inventory on the pre-plan
capture. The result has no action consumer.

## Independent And Automated Gates

Before physical use:

1. retain an independent scalar fixture decoder in tests;
2. cover inactive/active slots, signed HP, all local gate bits, defeat modes,
   slot boundaries, truncated blobs, and 64-slot dense/adversarial layouts;
3. prove ordinary capture output and body geometry are unchanged with the
   option off and on;
4. prove one existing RPM blob and identical manager-frame bracket;
5. record layout/default-off/supervisor propagation in tests;
6. benchmark decode plus canonical row construction on Linux and Windows:
   - p95 at most `0.10 ms`;
   - p99 at most `0.20 ms`;
   - maximum at most `2.00 ms`;
7. run focused Ruff plus complete Linux/Windows quick suites.

Timing is measured separately for decode and record construction. A timing
miss preserves the useful signal as explicit trace-only research but rejects
physical gate promotion until separately optimized.

The offline gate is accepted in
`STAGE5_ENEMY_COMBAT_PROGRESS_OFFLINE_GATE_20260728.md`. It records the
initial timing failure, representation-only optimization, independent scalar
oracle, cross-platform deterministic digest, and final Linux/Windows timing.
This is authority to integrate the explicit default-off physical observer,
not physical acceptance.

## Physical Stage-5 Gate

Use one supervised Lunatic Stage-5 run with:

- verified executable, foreground, route, difficulty, stage, and patch;
- hard no-Bomb;
- default live action path;
- explicit combat-progress trace option;
- ordinary-prefix frame bracket and zero added RPM;
- exact schema, offsets, masks, slot bounds, and finite timing;
- at least one active ordinary-enemy row, one positive-HP progression, and one
  positive frame-damage observation;
- every disappearance/end classified as candidate or `UNKNOWN`, never
  unconditionally as killed;
- phase-attributed hits, Power/resources, accepted transitions, cleanup, and
  compact evidence; and
- byte-identical strict audit regeneration.

The first focused workload should retain the opening nonspell segment even if
the full Stage-5 practice run continues. One run cannot promote targeting or
estimate a clean-route survival rate.

## Falsifiers And Stop Rules

Reject this observation gate if:

- enabling it changes bodies, actions, hard masks, issue records, or RPM
  count;
- any field crosses the manager-frame bracket without explicit instability;
- a slot address is treated as generation identity;
- disappearance is reported as a verified kill without sufficient evidence;
- global transition/Bomb state is hidden inside the local gate label;
- raw invalid/ambiguous values are silently dropped;
- performance/cadence gates fail and are hidden by averaging;
- a Bomb, missed transition, stale target, hit-evidence loss, or cleanup
  failure occurs.

## Next Gate

After this inventory passes physically, freeze a separate generation/end
tracker and streaming exposure audit. Only then test a survival-filtered
target shadow. G5 auxiliary ECL event lowering remains a separate hazard
completeness line and must not be conflated with combat-progress evidence.
