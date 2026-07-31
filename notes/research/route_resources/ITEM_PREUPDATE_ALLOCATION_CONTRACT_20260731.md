# Item Pre-Update Allocation Contract

Date: 2026-07-31

Taskbook cards: `POWER-ROUTE-01`, `CONTENT-02`

Status: exact offline allocation recurrence; no event execution, collection,
resource-benefit, physical-prediction, planner, or live authority

## Question

Can every ordered item source update the persistent item pool, rotating
allocation cursor, active-list order, effective type/motion, and gameplay RNG
before `item_manager_update`, without combining allocation with movement or
inventing a successful time-item spawn?

This is a route-wide resource boundary. It is used by ordinary defeat drops,
message-cleanup score items, and later same-update item motion. It is not an
individual hit investigation.

## Problem Contract

### Physical objective

Preserve NMNB survival while carrying exact route item identity and resource
opportunity forward. No allocation may become a fictional pickup, Power
threshold, score benefit, or combat improvement.

### State and observations

The recurrence receives:

```text
P = (sorted occupied slots, active-list order, resources, allocation cursor)
R = ordered spawn requests (x, y, input type, requested motion state)
G = shared gameplay RNG state/call count
S = native player state used by scatter initialization
```

Each request is one native `item_pool_spawn` call. The sequence is already
ordered by its upstream event consumer; the allocator does not reorder or
merge requests.

### Transition

For each request in order:

1. reject x outside `[-64, 448]` without changing cursor or RNG;
2. resolve effective type rules relevant to allocation control flow;
3. probe the current cursor slot and advance the cursor;
4. if effective type is 7 and that slot is occupied, return failure
   immediately;
5. otherwise continue cyclic probing up to all 2,096 slots;
6. on success, initialize the item, consume only the motion callback's
   declared RNG, and append the slot to active-list order.

Input pseudo-type 10 becomes effective type 7/state 5 before step 4. A full
pool does not end an ordered request batch: a later effective-type-7 request
still advances the cursor once even though it also fails.

The recurrence stops before `item_manager_update`. It performs no item
movement, collision, collection, cull, or resource mutation.

### Uncertainty, horizon, resources, and fallback

The transition is deterministic for the complete state, request sequence, and
RNG input. Missing upstream source requests or an incomplete pool are outside
the state and must fail at their consumer; they are not uncertainty branches
filled by this allocator.

The horizon is the ordered allocation batch only. The enclosing timeline
`0x06` event remains fail closed because message-manager and complete enemy/end
state are still absent from the integrated simulator.

## Revalidated Native Evidence

Observed in shipped TH08 1.00d:

- `item_pool_spawn` starts at `0x004400A0`;
- x rejection precedes type conversion and cursor scanning at
  `0x004400D0..0x004400E7`;
- input type 7 forces state 3, while pseudo-type 10 maps to type 7/state 5 at
  `0x00440119..0x00440131`;
- the current slot is probed and the persistent cursor advances at
  `0x00440138..0x00440178`;
- `0x004401AE` returns failure after one occupied probe for effective type 7;
- successful initialization and motion-specific RNG precede active-list
  append at `0x00440413`; and
- full cyclic failure returns only after 2,096 probes at `0x0044044B`.

The connected IDA database now records the effective-type-7 one-probe branch
at `0x004401AE`. This conclusion is revalidated from assembly control flow,
not inherited decompiler naming.

For message cleanup, revalidated calls at `0x0042F0A2` and `0x0042F141`
request type 6/state 1 before `item_manager_force_all_homing` visits the
resulting active list. The complete enemy/message event is not implemented
here.

## Executable Recurrence And Falsifiers

`th08_item_pool.allocate_items_before_update` exposes:

- exact successor pool;
- successful slot order;
- per-request failure index/reason; and
- whether a failure occurred with a truly full pool.

`step_item_pool` consumes this recurrence before its existing movement,
collection, and cull pass.

The retained deterministic regressions cover:

1. occupied cursor 9/free slot 10 for both input type 7 and pseudo-type 10;
2. a following ordinary request that must receive slot 10 with zero RNG calls;
3. a full pool where a later type-7 failure still advances the cursor once;
4. out-of-range rejection with no cursor/RNG change; and
5. type-6 cleanup allocation followed by forced homing of both old and newly
   appended items.

CE-0228 preserves the old full-scan failure and the correction.

## Authority

- **Observed:** shipped allocation branches, cursor order, success-only
  initialization/RNG/list append, and cleanup type-6/state-1 call sites.
- **Inferred:** none inside the declared scalar transition.
- **Hypothesized:** which requests occur in a physical route history, which
  allocations later collect, and whether any collection improves survival.

This checkpoint grants exact offline pre-update allocation authority only. It
does not grant runtime occurrence, full message cleanup, item pickup, Power
threshold, combat benefit, planner, or live-action authority.

## Formal Authority Questions

1. **Which histories map to one state?** Only histories with identical full
   pool, active order, cursor, resources, player state, ordered request batch,
   and RNG.
2. **Are uncertainty branches present?** The recurrence is deterministic.
   Unknown upstream requests remain unsupported rather than guessed.
3. **Does exact solution answer the physical question?** It answers allocation
   identity and RNG only, not later collection or route survival.
4. **What falsifies the claim?** A native call that scans effective type 7
   past one occupied slot, a cursor/RNG/list mismatch, or an unmodeled
   effective-type branch.
5. **Can a live consumer use it before issue?** No. It has no live consumer,
   and the integrated timeline event remains fail closed.

## Verification

Focused item-pool and item-primitive tests pass. Complete discovery passes
1,537 tests on Linux in 14.064 seconds and through the Windows UNC loader in
30.711 seconds, with the three existing Windows skips. No TH08, controller,
probe, native replay, or physical trial was launched.
