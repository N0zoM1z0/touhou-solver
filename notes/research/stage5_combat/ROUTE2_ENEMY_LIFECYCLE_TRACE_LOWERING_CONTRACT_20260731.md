# Route-2 Enemy And Item Lifecycle Trace-Lowering Contract

Date: 2026-07-31

## Question

Can one default-off lifecycle-ring JSONL trace be lowered into
generation-aware ordinary-enemy lifetimes, exact end classifications, item
generations, and same-update pickup/resource transactions without silently
bridging dropped events, unstable reads, slot reuse, or a mid-stage
attachment?

## Evidence Boundary

**Revalidated native evidence** is inherited from
`ORDINARY_ENEMY_LIFECYCLE_EVENT_RING_CONTRACT_20260731.md`: two ordinary-pool
allocation edges, five exact active-bit clears, one distinct forced-HP-zero
edge, native frame damage, the four shipped forced-zero callers, one
successful item-allocation edge, one non-pickup cull, and the paired
pickup-begin/commit boundary. Five defeat-helper allocation returns expose an
exact source enemy.

**Implemented offline evidence:**

- `scripts/analysis/th08_enemy_lifecycle_trace_audit.py`;
- report schema `th08-enemy-item-lifecycle-trace-audit-v3`; and
- twelve independent deterministic tests in
  `tests/test_th08_enemy_lifecycle_trace_audit.py`.

No TH08 process, runtime hook, replay, controller, or physical trial was run
for this checkpoint. Therefore the lowerer has offline/synthetic
implementation authority only.

## Serial And Batch Contract

The lowerer begins only from one valid `baseline` batch:

- `previous_serial` is null;
- `observed_serial` is uint32;
- no event or dropped count is present; and
- the record explicitly denies action authority.

For every advancing batch it requires:

- `previous_serial` equals the last accepted serial;
- uint32 forward distance is less than `2^31`;
- `dropped_event_count == 0`;
- event count equals serial distance;
- event serials are consecutive, including wrap from `0xffffffff` to zero;
- each pointer equals the declared enemy/item pool base plus exact slot
  stride;
- stage-route index is native `0..8`; enemy allocation root is a nonnegative
  signed word, while other enemy roots are null; and
- all event fields and lifecycle kinds use the exact probe schema.

`read_error` and `race_unknown` are recoverable only when they do not advance
the serial. A later exact batch may cover the unchanged interval. If the
trace ends before recovery, the stream is incomplete.

`overflow_or_trace_truncation`, an advancing malformed batch, a chain
mismatch, or an invalid event ends the authoritative prefix immediately.
Later events are not joined across that gap. Exact completed lifetimes before
the gap remain separately visible; no whole-stream authority is claimed.

`--require-complete` returns status 2 unless an installed probe has a complete
post-baseline chain and a final post-key-release batch.

## Generation And End Lowering

Each observed allocation starts one new per-slot observed generation. A
second allocation while that pointer still has an open generation is an
error, not implicit reuse.

The generation retains the exact native stage-route index and allocation root
subroutine. A later forced-zero or retirement event cannot change stage
identity inside that open lifetime.

A forced-HP-zero event:

- must preserve active bit 0x01;
- must end at HP zero;
- is mapped through one of the four shipped return addresses; and
- remains an effect inside the current lifetime, not a retirement.

Each retirement must clear active bit 0x01. The lowerer reuses
`classify_enemy_retirement`:

- initial/main VM returns are scripted ends;
- the offscreen edge is an offscreen cull;
- a mode-0 defeat following forced zero is not a player kill;
- mode-0 defeat is a verified player-shot kill only when
  `pre_hp = post_hp + frame_damage` is positive and post HP is nonpositive;
  and
- every other mode-0 defeat remains unattributed.

If the baseline serial is nonzero or a retirement appears before an observed
allocation, the lifetime is retained with `start_observed == false`. Its
ordered retirement classification may still be exact, but its generation
start and duration are unknown.

## Item Generation And Resource Lowering

The same accepted serial prefix is lowered per exact 2,096-slot item pointer:

- a successful allocation starts one observed item generation;
- pickup or cull closes it before slot reuse;
- a terminal event without an observed allocation creates an explicit
  partial start;
- a second allocation while a generation is open is an error;
- a generation cannot cross native stage identity;
- type changes are rejected except native full-Power conversion
  `0/2 -> 8`; and
- pickup pre/post RNG must agree because the reviewed reward path consumes no
  RNG.

Each allocation retains effective type/motion/position/velocity, player and
resource state, post-RNG state/call count, allocation cursor/list predecessor,
exact shipped caller, and exact source enemy only for one of the five
defeat-helper returns. A source pointer is joined only to an enemy generation
whose observed serial interval contains that allocation. Missing prefix
history leaves the owner-generation key null rather than inventing one.

Pickup retains Power/lives/Bombs before and after, their exact deltas, and
crossed Power thresholds `8, 24, 48, 80, 128`. Cull requires no resource
delta. The report separately counts allocations, culls, pickups, defeat
allocations, exact owner joins, and threshold crossings.

The optional immutable candidate-board join now follows:

```text
candidate board stage/root
  -> exact enemy generation
  -> exact source item generations
  -> pickup/resource delta/Power thresholds
```

It extends matched lifetime rows and summary counts only. It computes no
candidate score and grants no action or strategy authority.

## Formal Authority Questions

1. **Which histories merge?** Events merge into one lifetime only while the
   same exact ordinary-pool pointer remains open between an observed
   allocation and retirement. Item events merge only between one exact
   successful allocation and cull/pickup at the same item pointer. A missing
   allocation creates an explicit partial start; a gap forbids merging.
2. **Are uncertainty branches omitted?** No unknown batch is chosen away.
   Recoverable nonadvancing reads remain pending; dropped or malformed
   advancing intervals cut authority.
3. **Does exact lowering answer the physical question?** It answers native
   allocation/forced-zero/retirement order, concrete stage/root program
   identity, the bounded end classifier, covered successful item allocation,
   exact defeat-source identity, and covered same-update pickup/resource
   commit. It does not prove child ownership, emitted-projectile persistence,
   prevented births, failed allocation attempts, survival-feasible
   collection, causal action benefit, or later survival benefit.
4. **What falsifies it?** A retained exact native capture whose ring serials,
   pointer/slot relation, active transition, HP arithmetic, item owner,
   pickup resource/RNG transaction, or independent full-pool bracket
   disagrees with the lowerer.
5. **Can live control consume it?** No. It is an offline report tool. Its
   output has no sensing, planner, strategy, publication, or issue authority.

## Current Result And Next Gate

Synthetic cases cover exact forced-zero and lethal-damage generations,
recoverable read failure, overflow prefix cutting, uint32 wrap, mid-generation
baseline attachment, atomic rejection of one malformed batch, and an
unrecovered final read. New cases require allocation root identity, forbid a
lifetime from crossing native stage identity, and join a Stage-5 root exactly
to the pinned combat/resource candidate board while retaining non-timeline
roots as explicit unmatched programs. Item cases cover exact source enemy
generation to allocation to pickup/resource/Power-threshold to candidate
join, plus cull followed by slot reuse. Decoder and lowerer failures cover
unknown callers/owners, transaction identity, resource/RNG disagreement, and
invalid type/stage transitions.

Complete discovery passes 1,497 tests in 14.888 seconds on Linux and 30.680
seconds through the Windows UNC loader, with the three existing skips.

On explicit runtime authorization, the next gate is one short diagnostic
capture with:

1. lifecycle tracing enabled;
2. compatible full-pool/main-VM observation;
3. no concurrent priority-17 probe;
4. exact post-run lowering with `--require-complete`; and
5. independent agreement on enemy allocation/stage/root/forced-zero/
   retirement and item allocation/cull/pickup/resource/RNG order.

The optional `--candidate-board` join is now implemented and SHA-pinned.
Only after runtime agreement may its matched generation labels be used to
select same-root causal branches. The join schema can carry item pickup and
Power threshold evidence, but no runtime item event has been observed.
Prevented hostile birth, survival-feasible collection, causal Power benefit,
and exposure reduction remain unresolved.

The item-specific evidence boundary is
`../route_resources/ROUTE2_ITEM_ALLOCATION_PICKUP_TRACE_CONTRACT_20260731.md`.
