# Asynchronous Ordered Input Publication Contract

Date: 2026-07-30

Status: **Physical evidence accepted / scalar and bounded native parity
passed / no live authority**

This contract refines the complete-mask action and CE-0193 ordered-input
model. It does not change the live controller, actuator, cadence, hazard
producer, damage objective, or strategy.

## 1. Physical Objective And Authority

The hard physical objective remains:

> choose one complete no-Bomb input mask at each controller decision so every
> physically possible native update history remains collision-free.

One complete-mask controller choice is implemented by ordered per-key release
and press events. The shipped priority-17 callback can execute while that
dispatcher is still running. Therefore a causal transition must include
native updates during issue, not place the entire dispatch atomically between
two physical steps.

The accepted evidence is original-game Lunatic Stage-5 run
`lunatic_route2_stage5_unattended_20260730_083416`:

- raw source: 501,784,095 bytes, SHA-256
  `319b22f94dfdb2ce5322a0779839f94e6d03b6866c2d985e75e7c323473cae2f`;
- retained priority-17 report SHA-256
  `395ce5384e14e815afe6a5ce1977b165a94344906f3eb483a56c2484056be9b8`;
- 6,565 real ordered writes and 5,544 complete-mask no-writes;
- every real-write pre/post-dispatch serial bracket retained exactly;
- 1,223 writes with at least one callback exit during dispatch;
- 478 direct callback-exit observations of a non-final ordered mask; and
- 122 consecutive callback edges with no `enemy_manager_frame` advance.

The hook and diagnostic scale proxy are perturbing with unknown direction.
The evidence establishes occurrence and finite observed supports, not a
universal physical bound, survival improvement, or NMNB authority.

## 2. Revalidated Native Order

Connected IDA and runtime evidence establish one shipped update cycle:

1. priority 9 consumes the previously published `g_input_current` at
   `0x0044AEE8` and updates player movement/mode;
2. priority 11 updates enemy mode/body gates;
3. priority 17 saves previous at `0x00452339`, samples raw input, and leaves
   final callback-exit current at the common epilogue `0x00452480`.

If a priority-17 exit occurs during controller dispatch, the world update of
that cycle has already consumed the active mask from before that exit. The
newly published path mask can affect the next priority-9 cycle.

`enemy_manager_frame` is not this publication clock. Callback serial is
trace evidence only; the production model must eventually use a verified
scheduler/actuator automaton rather than retain the hook.

## 3. Decision State And Observation

At a controller observation boundary, the actuator component of one exact
hidden state is:

```text
X = (u, g, q, r)
```

where:

- `u` is native active input last published by priority 17;
- `g` is the final complete mask held by the controller/OS actuator;
- `q = (q1,...,qm)` is the remaining ordered mask suffix not yet known to
  have become native active;
- `r` is the positive number of post-dispatch publication steps remaining
  before the latest held final mask must be published.

Invariants:

- adjacent values in `(u,q1,...,qm)` differ by one supported non-Bomb bit;
- if `q` is nonempty, its final entry equals `g` and `r > 0`;
- if `q` is empty, `u = g` and `r` is absent.

The controller observation is at least:

```text
O(X) = (u, g)
```

plus the native player/mode/world observation declared by the enclosing TH08
model. Hidden suffix/deadline histories with the same complete observation
must merge before the next controller maximization.

The old exact state shape remains useful. The correction changes when and
how its suffix is consumed.

## 4. Actions And No-Write

The controller chooses one complete supported mask `a`.

### No-write

If `a = g`:

- no key event is emitted;
- no new delay or dispatch-interleaving support is sampled;
- `(u,g,q,r)` is preserved at issue;
- ordinary later native publications decrement/consume the existing pending
  suffix under the cadence recurrence.

Callbacks that happen during a no-write controller iteration belong to the
ordinary scheduler/cadence transition, not a fictitious dispatch phase.

### Real write

If `a != g`, construct:

```text
p = ordered_mask_path(g, a)
q+ = q || p
```

where releases precede presses and each group uses ascending bit order.
The new issue supersedes the old final-completion deadline, but it does not
erase already possible unobserved ordered masks. Its latest final entry is
`a`.

Bomb bit `0x02` is forbidden in `u`, `g`, every suffix mask, every action,
and every native publication.

## 5. Asynchronous Dispatch Microphase

Nature chooses a dispatch callback count:

```text
d in D_issue
```

For each of the `d` callbacks, nature chooses a monotone cut through the
currently remaining suffix:

- it may stutter at the current active mask;
- it may consume any positive prefix of the suffix;
- it may not move backward or invent a mask outside the ordered path;
- consuming the complete suffix publishes the latest held final mask.

For callback `j`:

1. the physical world transition consumes the active mask before callback
   `j`;
2. priority 17 publishes nature's selected monotone path mask;
3. that mask becomes active for the next physical world transition.

The scalar actuator oracle records both:

- masks consumed by the physical updates during issue; and
- masks published at each callback exit during issue.

This distinction is mandatory for TH08 composition.

After `d` callbacks:

- if the suffix is empty, the actuator is settled;
- otherwise nature selects a new post-dispatch completion support value
  `r in R_post`.

The controller may observe the pre/post serial count in a diagnostic trace,
but production action authority cannot depend on the injected hook.

## 6. Post-Dispatch Publication

For a pending state after dispatch:

- before the deadline, nature may stutter or consume any non-final ordered
  prefix;
- at the deadline, nature may skip every remaining intermediate mask but must
  publish the latest held final mask;
- a newer real write appends its path and replaces this deadline;
- therefore a superseded transient final target need not ever become native
  active.

This preserves CE-0193 intermediate masks while admitting the retained
overwrite witness:

```text
active/held 0x05
issue 0x04
callback during dispatch still publishes 0x05
before any post-dispatch callback, issue 0x05
next callback publishes 0x05
```

The transient `0x04` target is not forced to appear.

## 7. Physical Support Evidence

The retained trace yields the following **observed**, source-reproducible
counts over fully retained prefixes:

```text
dispatch callbacks -> first final step from pre-dispatch serial
0 -> 1 : 4893
0 -> 2 : 446
1 -> 2 : 1202
1 -> 3 : 1
2 -> 3 : 16
2 -> 4 : 1
3 -> 4 : 1
4 -> 5 : 1
```

Equivalently, first-final distance from the post-dispatch serial is:

```text
1 callback: 6113
2 callbacks: 448
```

All 6,561 exact first-final witnesses occur after dispatch returns. The first
post-dispatch callback observes:

- latest final mask: 6,114 times;
- old held path position: 102 times;
- non-final ordered intermediate: 347 times; and
- one event outside the path only across a known serial-overflow gap.

One write is replaced before any post-dispatch callback. Three other
first-final observations follow unretained gaps. These are censored or
unknown, not upper-bound violations.

Current proposal supports are therefore:

```text
D_issue = {0,1,2,3,4}
R_post  = {1,2}
```

Their direction as finite physical supports is **unknown** outside this
Stage-5 sample. They may be used in the independent scalar implementation
and later shadow differentials, but not for hard/live authority. Promotion
requires a conservative derivation or compatible physical coverage across
Lunatic Stage 3, Stage 4A, Stage 5, and Final B.

## 8. Horizon, Resources, And Safety

The issue microphase consumes physical update steps. Those steps must count
against:

- survival horizon;
- cadence budget;
- command pickup/publication support;
- player movement and mode recurrence;
- enemy/body/geometry evolution; and
- computation/publication deadline.

They are not free bookkeeping transitions.

Safety invariants:

- Bomb is never emitted;
- one controller action is uniform across all hidden branches;
- hidden issue schedules merge by actual next observation;
- survival remains hard;
- damage, Power, items, graze, score, and position are ranked only inside the
  viable set;
- unknown support, missing future geometry, stale immutable version, or
  missed deadline cannot gain hard action authority.

## 9. Algorithm And Falsifiers

The independent scalar oracle must enumerate every monotone dispatch
publication history for each declared callback count. It may canonicalize
identical exact successor states only after retaining the physical masks
consumed/published during issue.

Required adversarial regressions:

1. CE-0193 `0x65 -> 0x61 -> 0x41` during one callback in dispatch;
2. the superseded `0x05 -> 0x04 -> 0x05` target that is never published;
3. multi-release/multi-press paths with zero through four dispatch callbacks;
4. Focus and Shot acquire/release;
5. direction reversal;
6. callback stutter and multi-edge skip;
7. final publication during dispatch;
8. pending overwrite;
9. complete-mask no-write;
10. observation-compatible hidden-history merging;
11. unsupported bits and Bomb fail-closed.

The 2026-07-30 offline implementation checkpoint closes the first bounded
implementation gate:

- the independent Python scalar oracle enumerates exact dispatch consumption,
  publication, successor suffix, and post-dispatch deadline branches;
- the TH08 composition consumes the pre-publication mask at priority 9,
  projects priority-11 contact/damage body identities, and only then applies
  the priority-17 publication for the next physical step;
- a separate C++ exact-state enumerator is exposed through
  `touhou_async_ordered_input_issue_v1`; it does not call or share the scalar
  recurrence;
- the public production ABI grows from 46 to 47 checked symbols;
- the bounded native lane rejects more than 1,024 queued masks, 64 support
  values, 16 callbacks in one dispatch, or an upper estimate above 100,000
  branches. Rejected/exhausted inputs are unresolved, never losing;
- 115 physical/adversarial exact-state/action cases and 2,405 complete branch
  histories match scalar/native on both Linux and Windows with zero
  mismatch; and
- the two retained physical cases publish their exact histories, not only
  aggregate counts.

The retained reports are:

- Linux:
  `artifacts/runtime_reports/async_ordered_input_native_differential_linux_20260730.json`,
  SHA-256
  `f9fbe98bac5fe9481e8baf4bc09c51b328b12fb744d724132dd0d7adb7e3e4b0`;
- Windows:
  `artifacts/runtime_reports/async_ordered_input_native_differential_windows_20260730.json`,
  SHA-256
  `91df49e10f919e4c1681cb617563c311c55902b0500ee2ba5b379a23b391885a`.

After removing platform/native-binary identity, both reports are structurally
identical. This is implementation parity for the declared finite supports;
it is not evidence that `D_issue`, `R_post`, or the independent cadence
Cartesian product is physically complete.

Focused scalar/TH08/native/report/ABI gates, strict Linux/Windows compiler
warnings, and Linux sanitizer execution pass. Complete Linux/Windows
discovery passes 1,247/1,247 in 14.990/30.874 seconds; Windows retains the
three existing skips.

Concrete falsifiers include:

- a physical callback mask outside the controller's ordered path in a fully
  retained interval;
- a backward path position without a newer issued transaction;
- a fully retained compatible workload whose post-dispatch final pickup lies
  outside the declared hard support;
- a scalar history omitted or added by an optimized implementation;
- TH08 composition applying a newly published mask to the same priority-9
  cycle instead of the next one.

## 10. Formal Review Questions

1. **State equivalence:** states merge only when active and held masks plus
   the enclosing native observation agree. Hidden suffix/deadline branches
   remain nature branches, not separate controller choices.
2. **Causality:** one selected complete mask is applied uniformly. Nature
   chooses dispatch callback count and monotone publications; the controller
   cannot condition on a callback that occurs after its action.
3. **Physical relevance:** the recurrence includes issue-time physical
   updates and ordered publication. It still answers only a proxy until
   `D_issue`, `R_post`, scheduler cadence, and future world evolution have
   conservative physical authority.
4. **Algorithm validity:** exhaustive scalar enumeration is exact for the
   declared finite supports. The bounded native enumerator has exact
   differential implementation parity on the retained corpus; inputs beyond
   its explicit cap remain unresolved. Neither implementation validates the
   physical completeness of the supports.
5. **Delivery:** results must be consumed under one immutable problem version
   before issue. A diagnostic serial hook may validate evidence but cannot be
   a production dependency.

## 11. Staged Exit Gate

1. **Passed:** independent game-neutral scalar issue microphase.
2. **Passed:** TH08 priority-9/11/17 composition with explicit physical-step
   count.
3. **Passed, bounded:** independent native exact-state enumerator with
   explicit exhaustion caps.
4. **Passed:** exact Linux/Windows state/history/action differentials for the
   adversarial set and two retained physical witnesses.
5. **Open:** bind a complete immutable future body/flag/geometry schedule.
6. **Open:** run one newly versioned whole-stage physical falsifier without
   fail-close.

The first four finite implementation gates pass. Until gates 5 and 6 pass,
the asynchronous model remains offline/shadow only.
