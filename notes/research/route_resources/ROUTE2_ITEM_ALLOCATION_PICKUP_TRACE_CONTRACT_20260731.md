# Route-2 Item Allocation And Pickup Trace Contract

Date: 2026-07-31

Taskbook cards: `POWER-ROUTE-01`, `COMBAT-KILL-01`

Status: implemented and synthetic-tested; default-off diagnostic only; no
runtime observation, collection-policy, strategy, or action authority

## Question

Can one ordered native trace connect an immutable route candidate to an exact
enemy generation, a successful defeat-item allocation, and either cull or
same-update pickup/resource commit without treating a static drop request as a
collected resource?

This is a general WS-H transport and evidence checkpoint. It closes the
missing executable join schema. It does not claim that any route action
causes the joined chain, that collection is survival-feasible, or that the
resource improves later combat.

## Revalidated Native Boundaries

The following conclusions are **observed** in the shipped executable through
connected-IDB instruction/dataflow review and exact-byte reads:

| Event | Hook | Exact overwritten bytes | Boundary |
| --- | ---: | --- | --- |
| successful item allocation | `0x0044044D` | `8b4df8894df0` | `[ebp-8]` is the allocated item after effective type, motion, position, velocity, RNG consumption, active-list append, and cursor update |
| non-pickup item cull | `0x00440991` | `8b4ddce8d70d0000` | `[ebp-0x24]` is the current item immediately before unlink; no reward has executed |
| pickup begin | `0x00440A39` | `668990da000000` | collection collision has returned true; `[ebp-0x24]` is the item and type-specific reward has not executed |
| pickup commit | `0x00440C1E` | `8b4ddce84a0b0000` | type-specific reward is complete; the same item is about to be unlinked |

The successful-allocation hook sees exact caller return `[ebp+4]`. The 58
direct shipped return addresses are pinned in
`ITEM_ALLOCATION_RETURN_ADDRESSES`; an unknown caller is rejected instead of
being generalized.

Five return addresses are inside
`enemy_spawn_configured_defeat_items`:

- `0x0042BF0B`;
- `0x0042BF86`;
- `0x0042C087`;
- `0x0042C09B`; and
- `0x0042C166`.

At those five edges, the allocator's saved caller EBP leads to exact source
enemy `[caller_ebp-0x14]`. The trace retains that ordinary-pool pointer.
Other allocation callers retain no source enemy; the decoder forbids an
invented owner.

These findings revalidate the allocation/pickup boundaries used here. They do
not promote inherited function or local-variable names beyond the reviewed
instructions and dataflow. IDA comments at all four hooks retain the observed
boundary.

## Probe And Event Contract

`scripts/th08_runtime/enemy_lifecycle_probe.py` now defines
`th08-enemy-item-damage-lifecycle-probe-v4`:

- fourteen exact-byte-guarded and reversible hook sites: eight enemy
  allocation/end edges, paired resolved-damage begin/commit, and four item
  edges;
- one total uint32 serial order for enemy and item events;
- 128-byte typed events in a 256-entry ring;
- a `0x10000` remote image, with the ring ending at `0xA400`;
- double-header validation and at most two contiguous process-memory reads
  for a wrapped event batch; and
- the existing explicit default-off lifecycle option, priority-17 conflict,
  activation quiescence, reverse rollback, and unsafe-target termination
  boundary.

CE-0224 corrects the initial v3 ring-selector encoding:
`imul ..., imm8` sign-extended `0x80` to `-128`. The stub now uses an imm32
positive stride, and a deterministic byte-level test rejects the old
sequence. No v3 probe was installed before the correction.

A successful item-allocation event retains:

- item pointer and exact 2,096-slot index;
- native stage-route index and exact shipped caller;
- effective post-conversion item type, motion state, Full-Value flag,
  position, and velocity;
- player position/state, Focus logic, and native active input;
- current Power, lives, and Bombs;
- post-allocation RNG state/call count;
- next rotating allocation cursor and active-list previous pointer; and
- exact source-enemy pointer only at the five defeat-helper returns.

The successful hook is after callback RNG consumption. Pre-allocation RNG is
therefore deliberately null rather than reconstructed. The event sees the
effective type after full-Power conversion, not the allocator's original
requested type.

Pickup is one atomic trace transaction. The begin hook copies exact
pre-reward item/player/resource/RNG state into fixed remote scratch. The
commit hook publishes one event only after reward dispatch and requires the
same item pointer and `enemy_manager_frame`. It retains post Power, lives,
Bombs, and RNG. The lowerer requires pickup RNG to be unchanged; a native
counterexample cuts authority instead of being normalized.

CE-0225 additionally guards hot installation between the paired sites.
Commit requires the exact begin marker, item pointer, and manager frame before
selecting a ring slot. A mismatch replays only the shipped unlink call and
publishes nothing. Both paths clear the marker; success does so before
publication.

Cull publishes the terminal item state immediately before unlink and requires
unchanged Power, lives, Bombs, and absent RNG evidence.

## Offline Lowering And Candidate Join

`scripts/analysis/th08_enemy_lifecycle_trace_audit.py` defines report schema
`th08-enemy-item-damage-lifecycle-trace-audit-v4`.

It preserves the existing zero-drop serial-prefix and enemy-generation
contract, then lowers item records per exact pool pointer:

- allocation starts one observed item generation;
- pickup or cull closes it before slot reuse;
- a terminal event without an observed allocation creates an explicit
  partial start;
- a generation cannot cross native stage identity;
- type changes are rejected except native full-Power conversion
  `0/2 -> 8`;
- pickup retains exact Power/lives/Bombs delta and crossed Power thresholds
  `8, 24, 48, 80, 128`; and
- a defeat allocation joins its source enemy only when that exact enemy
  generation interval is present in the authoritative serial prefix.

With the SHA-pinned candidate board, the exact join chain is:

```text
candidate-board (stage, root)
  -> observed enemy generation
  -> observed resolved HP-damage transactions
  -> observed defeat-item generation
  -> observed pickup/resource delta/Power threshold
```

The joined candidate row reports exact damage count/total/manager frames,
source-item allocation/pickup counts, observed Power delta, and thresholds.
It does not compute candidate value, rank an action, or reinterpret an absent
item event as evidence of no drop.

## Formal Authority Answers

1. **Which histories merge?** Enemy histories merge only inside one observed
   pointer generation. Item histories merge only from one exact allocation
   to its exact cull/pickup at the same item pointer without a trace gap or
   reuse. Equal Power or equal item type alone is not sufficient.
2. **Are uncertainty branches omitted?** This is an observer/lowerer, not a
   control recurrence. Overflow, advancing malformed batches, unknown callers,
   missing transaction identity, and broken joins cut authority. They are not
   selected away.
3. **Does exact lowering answer the physical question?** It can answer which
   covered successful allocation and terminal edge executed, whether a
   covered defeat allocation belongs to an observed source generation, and
   what same-update resource delta committed. It does not answer failed
   allocation attempts, survival-feasible collection, causal action benefit,
   or later HP/survival improvement.
4. **What falsifies it?** A retained native capture with a covered allocation,
   cull, or pickup missing from the ring; pointer/frame/resource/RNG
   disagreement; a defeat allocation whose saved-frame owner disagrees with
   an independent full-pool bracket; or a non-defeat caller carrying an
   owner.
5. **Can live control consume it?** No. Installation and reading remain
   default-off diagnostics. The lowerer is offline. Neither trace nor joined
   output has sensing, planner, publication, issue, strategy, or live-action
   authority.

## Verification And Remaining Gate

Focused verification passes:

- 21 probe/transport tests;
- 13 lowerer/join tests;
- 20 live-agent hotkey tests;
- 14 full-route supervisor tests;
- 9 live-CLI tests; and
- 35 practice-supervisor tests.

Ruff passes. Complete Linux discovery passes 1,500 tests in 13.953 seconds.
Complete Windows UNC discovery passes 1,500 tests in 31.615 seconds with the
three existing skips.

No TH08 process, probe installation, runtime batch, replay, controller, or
physical trial was run. The checkpoint grants shipped-instruction,
implementation, and deterministic synthetic-lowering authority only.

On explicit runtime authorization, the next evidence gate is one short
diagnostic:

1. bracket the v4 ring with compatible full-pool/main-VM observation;
2. run no concurrent priority-17 probe;
3. require a complete post-release serial chain;
4. compare enemy generation, exact damage, item allocation, cull/pickup,
   resource, and RNG order against the independent bracket; and
5. join the exact result to the immutable candidate board.

Only after that agreement may same-root pure-survival and
survival-feasible collection branches be compared. A later Power threshold
must still be carried into shot schedule, target HP/kill timing, viable
reserve, and first-hit frontier before any route-strategy promotion.
