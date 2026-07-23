# Robust Viability And Backward Reachability

Status: implementation contract for the game-neutral global survival layer.
The first physical target is TH08 route 2 spell 46, followed by complete
Sakuya/Remilia Lunatic and Extra runs.

## Why The Previous Planner Plateaued

The local beam MPC searches roughly ten frames and the old corridor planner
propagates one optimistic reachable path forward. Both can choose a locally
clear state whose remaining escape set is already collapsing. The accepted
Stage-3 run demonstrates this boundary: all six hits were preceded by complete
robust first-action-set exhaustion three to seven frames earlier.

Changing weights, adding Bombs, or reducing `SendInput` latency cannot recover
from a state that has no delay-robust successor. The global layer must preserve
a set of states from which survival remains controllable.

## State And Quantifiers

The abbreviated recurrence is:

```text
V[t, x, y] =
    safe(t, x, y)
    and exists action
        such that for every delay in D
        successor(t, x, y, action, delay) is in V[t + 1]
```

Actuation delay requires one additional state dimension. The exact finite
lattice used here is:

```text
V[k, active_action, y, x] =
    safe at the current layer
    and exists next_action
        such that for every delay in learned support D:
          every intermediate physical frame is safe
          and
          V[k + 1, next_action, successor_y, successor_x]
```

`active_action` is the input that continues moving the player until the newly
issued action becomes visible. For a delay `d`, physical frames `1..d` use
`active_action`; later frames in the control layer use `next_action`.
Omitting this state would incorrectly assume that a command acts immediately.

The quantifier order is deliberate:

```text
exists next_action, for every delay
```

Selecting a different action after learning which delay occurred is not
physically available and would produce an optimistic, invalid policy.

## Finite Lattice

The reusable kernel receives:

- monotonically increasing x/y lattice axes;
- a per-physical-frame clearance volume;
- named actions with per-frame velocity;
- frames per control layer and finite horizon;
- a sorted discrete delay support;
- a required clearance threshold.

It returns:

- the boolean viability kernel for every layer and active action;
- a safe-action bit mask at every state;
- the worst-branch successor state-action volume for every safe action;
- query metadata for live use.

Backward induction starts with all collision-free terminal states. At every
earlier layer, an action is admitted only when every modeled delay branch stays
collision-free at all intermediate frames and lands in the next kernel.

The successor-volume score counts viable state-action pairs in a small
neighborhood around each branch endpoint, then takes the minimum over delay
branches. This is a repair-space measure, not a soft survival penalty. The
local controller first remains inside the viable action set, then prefers more
repair volume, and only then optimizes clearance, movement smoothness, items,
graze, and position.

## Asynchronous Policy Use

The corridor worker must return the kernel/policy, not only a waypoint.
A live query uses:

```text
(current frame - source frame,
 current projected position,
 currently active input)
```

to select the appropriate layer and lattice state. Therefore an asynchronous
result can still constrain the current action while it is within the modeled
horizon. A stale waypoint alone cannot provide that guarantee.

The trace must retain policy age/layer, whether the queried state is viable,
safe action names/count, per-action repair volume, selected repair volume, and
the learned delay support. Empty queried action sets are explicit viability
exhaustion events.

## Approximation Boundary

This first kernel is a finite-horizon lattice abstraction, not yet a proof over
continuous TH08 dynamics:

- position and action endpoints are quantized to the configured grid;
- moving bullets use the live snapshot velocity and uncertainty growth;
- unresolved transforms and future ECL emissions are not fully predicted;
- laser geometry is finite but its future phase changes remain approximate;
- the learned delay support is empirical and interval censoring is still open.

Intermediate collision checks subtract the distance between a continuous
sample and its nearest lattice point from the sampled clearance. This uses the
Lipschitz property of distance fields to avoid optimistic nearest-cell safety.
Endpoint quantization and incomplete future hazard generation remain explicit
model risk and require native-game regression.

The architecture is game-neutral despite these TH08 limitations. Another game
supplies its bounds, action velocities, hazard clearance volume, delay support,
and runtime adapter without changing the backward-induction kernel.

## Staged Acceptance

1. Synthetic tests distinguish optimistic reachability from robust viability,
   exercise the `exists action / forall delay` ordering, and verify that the
   active-action dimension changes the result.
2. Offline TH08 tests validate action-name/mask lowering and policy queries.
3. A focused spell-46 thprac run records whether viability exhaustion appears
   earlier than the three retained spell-46 hits.
4. Tune grid/horizon and future-hazard prediction until three clean focused
   runs complete with hard no-Bomb.
5. Re-run complete Stage 3, then complete Lunatic, then Extra, retaining the
   full artifact set required by `AGENTS.md`.

Bomb/resource dynamic programming is a later outer layer. A no-Bomb successor
is always preferred; a Bomb edge is considered only when the no-Bomb kernel is
empty and stock plus phase timing make the transition feasible.
