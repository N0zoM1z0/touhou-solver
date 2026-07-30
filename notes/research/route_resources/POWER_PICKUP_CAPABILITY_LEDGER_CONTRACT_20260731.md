# Power Pickup And Capability Ledger Contract

Date: 2026-07-31

Taskbook card: `POWER-ROUTE-01`

Status: corrected offline resource recurrence and static capability ledger; no
live collection authority

## Question

For every natural Route-2 Power state, what resource state and normal-shot
capability follow a small, large, or Full Power pickup? Which native pool
state must be retained so same-update pickup and full-Power conversion are
causal rather than sorted approximations?

Survival remains hard. This ledger describes capability only; it does not
assign value to a pickup path unless every physical history in that path
remains viable and issue-safe.

## Revalidated Native Semantics

The following are **observed** in shipped instructions and dataflow:

- Power is a float field mutated by integer increments.
- Small Power adds one at `0x00440CF0`; large Power adds eight at
  `0x00441170`.
- When either addition reaches or crosses 128, `0x00406FA0(128)` immediately
  writes canonical Power 128. Power 124 plus a large item is therefore 128,
  not 132.
- At full Power, `0x00441450` walks the active linked list, skips the
  collected source, converts other active type-0/2 items to overflow type 8,
  and, when their `vy > -0.5`, writes `vx=0, vy=-0.5`.
- `item_pool_spawn` starts at a persistent 0..2095 allocation cursor and
  scans cyclically. It does not restart at the lowest free slot.
- Each allocated item is appended to a doubly linked active list.
  `item_manager_update` follows that list, so update/pickup order is allocation
  order rather than numeric slot order.
- An x position outside `[-64, 448]` rejects the spawn before cursor advance,
  slot scan, or callback RNG.
- Power drops requested at Power 128 are converted to overflow type 8 during
  spawn.
- Normal-shot thresholds are the exact shipped dwords 8, 24, 48, 80, and 128.

Six durable IDA comments were added at `0x00406FB0`, `0x004400BD`,
`0x00440413`, `0x00440D5F`, `0x004411D8`, and `0x00441496`.

## Corrected Recurrence

CE-0220 records three concrete old-model failures:

1. large Power at 124 returned 132;
2. allocation always chose the lowest free slot and update sorted slots;
3. full-Power conversion omitted its conditional velocity rewrite.

`ItemPoolState` now carries:

- sorted slot storage for stable serialization;
- `next_allocation_index`, the native cyclic allocation cursor; and
- `active_order`, the allocation/list order used by the update.

For backward-compatible deterministic fixtures that omit active order, the
model infers numeric slot order once. Every stepped successor publishes an
explicit order and cursor.

The small same-frame adversary is:

- Power 120;
- active order `(slot 10 large Power, slot 2 small Power)`;
- both items overlap the player.

Native order collects slot 10 first, reaches Power 128, converts slot 2 to
overflow, and then collects slot 2 as overflow. Numeric slot sorting would
collect slot 2 as small Power first and produce a different resource, score,
motion, and pickup ledger.

## Static Capability Ledger

`scripts/analysis/th08_route2_power_capability_ledger.py` exhaustively
enumerates:

- every integer Power state 0..128;
- requested small Power, large Power, and Full Power pickups;
- effective spawn type, including full-Power overflow conversion;
- capped Power result and exact thresholds crossed;
- full-Power conversion activation; and
- before/after unfocused-primary and focused-secondary SHT level, nominal
  20-tick emission count, raw base damage, and callback RNG consumption.

The retained report has 387 transitions and SHA-256
`06a12eb6f2de97823286613322f6da9fbeac7abec490099ee3298bc6acf1dcf9`.

Small Power crosses a threshold in five source states. Large Power crosses a
threshold in 40 source states. The marginal small-item capability deltas at
each threshold are:

| Threshold | Unfocused raw damage | Focused raw damage | Focused RNG u16 |
| --- | ---: | ---: | ---: |
| 8 | +40 | +104 | +8 |
| 24 | +80 | +43 | +4 |
| 48 | +88 | +32 | +4 |
| 80 | +92 | +4 | 0 |
| 128 | +80 | +185 | +8 |

These are empty-pool raw SHT opportunities, not delivered HP damage. The
Power-80 threshold is especially useful as a coarse-rule falsifier: its
focused raw damage changes by only four while unfocused changes by 92.
Collection benefit is profile-, target-, pool-, and world-state-dependent.

## Formal Authority Answers

Physical histories map to one ledger row only when current Power, requested
pickup identity, effective type, allocation cursor, active order, active item
states, and pre-item world are identical. Histories with the same visible
Power but different active order are not control-equivalent because a
full-Power crossing can convert later list entries before their update.

The corrected item recurrence is causal and follows one declared active-list
order. The static pickup ledger does not branch nature or optimize actions.
It therefore makes no clairvoyant choice, but it also does not represent the
uncertain physical route or prove a pickup.

If solved exactly, the 0..128 ledger answers the finite resource/SHT question.
It answers only a proxy for the physical objective because item generation,
motion, target collision, survival viability, enemy HP, and later world state
are absent.

The enumeration is exact for the declared integer pickup arithmetic and SHT
selection. Nominal emission/base-damage values assume an empty shot pool and
omit collision, the separate 50-point hit-feedback increment cap, target
motion, native damage scaling, and enemy lifetime. Returned ordinary-shot
damage itself is not capped at 50. The nominal sums' direction as
delivered-damage estimates is unknown. A native result outside the declared
Power/SHT transition table falsifies the resource recurrence; a physical route
with no later benefit does not.

The ledger is offline and has no issue deadline or live consumer. The
unchanged live Boolean policy plus fresh hard certificate remains the
fallback.

## Authority And Next Gate

This checkpoint grants:

- revalidated resource cap, conversion, cursor, and active-order semantics;
- deterministic item-pool implementation authority;
- a complete static pickup-to-SHT capability table.

It grants no:

- observed runtime item allocation or pickup attribution;
- safe collection preference;
- later HP, kill, emission-prevention, or first-hit-frontier benefit;
- live or physical predictive authority.

The default-off v4 lifecycle ring and offline lowerer now implement exact
resolved damage plus the missing successful-allocation, cull, same-update
pickup/resource, exact defeat-source, and candidate-board join schema. This
is implementation and synthetic-test authority only; no runtime damage or
item event has been retained.
Detailed boundary:
`ROUTE2_ITEM_ALLOCATION_PICKUP_TRACE_CONTRACT_20260731.md`.

Complete Linux discovery passes 1,500 tests in 13.953 seconds. Complete
Windows UNC discovery passes 1,500 tests in 31.615 seconds with the three
existing skips.

The causal gate remains:

1. retain a natural first-hit-bounded Power-0 root;
2. on explicit runtime authorization, execute the v4 diagnostic and verify
   generation, exact HP damage, effective item type, allocation cursor/order,
   motion,
   same-update pickup/retirement, resource delta, and shared RNG against an
   independent full-pool bracket;
3. branch only actions already in the unchanged exact viable set;
4. carry the immutable world through a threshold; and
5. join later shot schedule, target HP/kill timing, viable reserve, and
   first-hit frontier.

No post-hit Power state may train or justify the accepted NMNB policy.
