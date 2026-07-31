# Route-2 Message-Cleanup Item-Homing Contract

Date: 2026-07-31

Taskbook cards: `CONTENT-02`, `COMBAT-KILL-01`, `POWER-ROUTE-01`

Status: route-wide static seam inventory and post-allocation item
sub-transition retained; complete message event remains fail closed

## Question

Across the natural Sakuya/Remilia Route-2 Lunatic route, where can timeline
opcode `0x06` invoke scripted enemy cleanup and item homing, and what part of
that same-update transition can the current item-pool recurrence execute
exactly without inventing enemy, message, pickup, or resource state?

This is a general route/combat/resource seam, not an individual hit
investigation. It prevents scripted HP zero from becoming a player kill and
prevents forced item motion from becoming an immediate Power claim.

## Problem Contract

### Physical objective

Preserve NMNB survival while carrying route-faithful item and Power state
through dialogue/message seams. No-Bomb remains hard. The transition must not
manufacture a collection, reward, kill, or later combat benefit.

### State and observations

The exact sub-transition receives the complete stable item pool *after* every
same-update score-item allocation performed by message cleanup:

```text
P = (sorted occupied slots, active-list order, resources, allocation cursor)
```

Each occupied slot retains position, velocity, motion state, timer, type,
full-value flag, and interpolation/scatter fields. The operation consumes no
controller observation or action and has no hidden branch at this boundary.

Enemy eligibility, message selector branches, end-subroutine execution, and
which score-item allocations precede this boundary are inputs owned by a
future complete event consumer. They are not reconstructed here.

### Actions, uncertainty, and transition

There is no controller action inside the native event. For active-list order
`L`, the observed native sub-transition is:

```text
for i in L:
    item[i].motion_state = 1
    item[i].velocity = (0.0, -0.5, 0.0)
```

The two-dimensional solver stores the observed x/y components; native z is
structurally zero. Slot identity, order, cursor, position, timer, type,
full-value/interpolation fields, resources, and RNG state/call count are
unchanged.

### Horizon, resources, safety, and fallback

The horizon is this one sub-transition only. It does not execute the next
`item_manager_update`, so it does not move or collect an item. It cannot
change Power, lives, Bombs, score, or item occupancy.

The integrated simulator remains fail closed at the enclosing
`TimelineEngineEvent`. Missing enemy/message/allocation state returns no
successor; the exact item sub-transition does not weaken that fallback.

## Native Evidence

Reused from the revalidated shipped-build CONTENT-02 checkpoint:

- `stage_timeline_step` case `0x06` at `0x0042ABD2`;
- `frscreen_start_message_script` at `0x0043396D`;
- `enemy_manager_zero_eligible_hp_with_score_items` at `0x0042EFB0`; and
- `item_manager_force_all_homing` at `0x004413E0`.

At `0x004413FE` the helper writes active item `+0x2D7 = 1`; it stores
`(0,-0.5,0)` at item velocity `+0x2B0`. The helper iterates the active linked
list after the enemy cleanup/item-allocation call and returns without pickup
or reward dispatch. These are observed shipped instructions/dataflow, not a
runtime claim that a particular atlas row executed.

## Executable Recurrence

`th08_item_pool.force_all_active_items_homing` validates the stable pool,
walks the declared active-list order, returns the exact successor, and retains
the affected slot order as event-ledger evidence.

`th08_item_pool.allocate_items_before_update` can now construct this boundary
exactly from an already-complete ordered cleanup score-item request batch,
including capacity, rotating-cursor, active-list, and failure semantics. The
enemy/message consumer that must produce that complete batch remains absent,
so the enclosing event still fails closed.

The deterministic falsifier uses:

- sorted occupied slots `1` and `4`;
- active-list order `(4,1)`;
- free and scatter-delay motion states;
- distinct velocity, timer, type, full-value, and interpolation fields;
- nonzero resources and allocation cursor.

Only motion state and x/y velocity change. The input state remains immutable.
No RNG object is accepted by the recurrence, so it cannot consume RNG.

## Route-Wide Static Atlas

The deterministic analyzer validates every ECL against the immutable content
manifest and retains all Lunatic-eligible Route-2 `0x06` occurrences:

| route workload | occurrences |
| --- | ---: |
| Stage 1 | 2 |
| Stage 2 | 2 |
| Stage 3 | 4 |
| Stage 4A | 4 |
| Stage 5 | 2 |
| Final B | 9 |
| **total** | **23** |

Stage 1/2 are included because `POWER-ROUTE-01` starts from natural Power 0
and must carry earned resources forward. The 19 mandatory-stage rows remain
the CONTENT-02 subset.

Retained artifact:

`artifacts/runtime_reports/th08_route2_message_cleanup_seam_atlas_20260731.json`

- SHA-256:
  `8ee48d5a3d25ad77d90a01e1a5373944553ac2fb9366fad854a7d6df0a016f8e`
- internal pre-digest:
  `a5a5b78131d6ec210c9b3b8d52fa1a37145d4c41b86a3a044518530ee51b37a2`
- two generations were byte-identical.

## Authority And Falsification

- **Observed:** shipped instruction/dataflow, exact content hashes, decoded
  occurrence fields, and deterministic scalar item mutation.
- **Inferred:** each listed row is a static route schedule candidate after the
  Lunatic mask; static timing does not prove event execution.
- **Hypothesized:** which items are active at a physical seam, whether they
  are later collected, and whether collection improves later combat/survival.

The claim is falsified by a shipped instruction that mutates another item
field, an active-list/pool identity mismatch, an RNG/resource change, a parser
or content-hash mismatch, or a runtime-image/PC join contradicting the
symbolic row.

This checkpoint grants static seam and exact item-sub-transition authority
only. It grants no full enemy cleanup, event execution, pickup, Power
threshold, kill, prevented birth, planner, or live-action authority.

## Formal Authority Questions

1. **Which histories map to one state?** Only histories with the same complete
   post-allocation item pool. Histories with different enemy cleanup or item
   allocations are not merged.
2. **Are uncertainty branches present?** The item sub-transition is
   deterministic. Upstream enemy/message/allocation uncertainty remains
   unsupported and fail closed.
3. **Does exact solution answer the physical question?** It answers only the
   forced item mutation, not physical collection or route survival.
4. **What falsifies the claim?** The instruction/content/runtime
   contradictions listed above.
5. **Can a live consumer use it before issue?** No. The event has no live
   consumer and the integrated simulator still rejects it.

## Verification

Focused item-pool and atlas tests pass. Complete discovery passes 1,534 tests
on Linux in 14.510 seconds and through the Windows UNC loader in 31.725
seconds, with the three existing Windows skips. No TH08, controller, probe,
native replay, or physical trial was launched.
