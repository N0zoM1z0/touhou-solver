# Pipeline Root Identity And Hazard Coverage Contract

Date: 2026-07-27

Status: implemented and physically audited G1 offline/shadow specification;
full pipeline promotion remains blocked. This note adds no live action,
epoch-reset, clock, or publication authority. It refines
`AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` and preserves the
boundary in `FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.

## Outcome

Two independent questions must be answered before a pipeline-aware result can
be consumed:

1. Is this exactly the observable physical/pipeline root for which the result
   was computed?
2. Does the immutable hazard model conservatively cover every physical hazard
   transition reachable from that root through the claimed horizon?

The canonical identity answers the first question. A frame-slab coverage
contract answers the second. Exact identity cannot repair missing hazard
physics, and complete hazard coverage cannot repair a stale or inconsistent
pipeline root.

The current TH08 forecast has no exhaustive model of unseen future births.
Therefore its complete physical hazard coverage becomes `UNKNOWN` when an
unseen event can first enter the root-reachable tube. At the current
checkpoint this is a shadow blocker, not free space and not a reason to
shorten an unknown-direction proof into a safety claim.

## Evidence Labels

- **Observed:** existing retained traces and unit/differential tests directly
  show the behavior.
- **Inferred:** required by the formal recurrence and joined observed
  mechanisms, but not itself a physical trace.
- **Hypothesized:** proposed classification or future authority that still
  requires evidence.

## Problem Contract

### Physical objective

Keep the player collision-free while selecting complete desired input masks
under delayed native pickup, variable controller cadence, modeled hazard
uncertainty, and the unresolved manager-frame/input-clock boundary. Survival
is hard. No G1 shadow result may emit Bomb or override the live Boolean policy
and fresh issue-time local certificate.

### State

The one-pending physical input state remains:

```text
(active mask a, held desired mask g, pending mask p or none,
 remaining-delay support R)
```

The observable query specialization additionally contains:

```text
(gameplay epoch, route/stage, spell id,
 manager frame, query frame, target frame,
 exact float32 player x/y,
 observation version, hazard version, policy version,
 model version, clock-boundary version)
```

Complete supported masks, rather than movement action names, determine
whether an actuator write occurs. This distinction retains multikey,
focus/unfocus, and Shot-bit transitions even when two masks project to the
same movement velocity.

The identity is serialized as canonical JSON and addressed by SHA-256.
Changing any root mask, remaining-delay support, exact coordinate, physical
context, or immutable version changes the digest.

The finite recurrence may project masks into a smaller action alphabet only
after the complete-mask write/no-write transition has been decided.

### Observations

The controller observes native `input_current` as active-mask evidence,
remembers the complete desired mask held by the actuator, and carries the
pending estimate and possible positive remaining delays from the delay
estimator. The current compact root is valid only under:

```text
p is none  => g == a and R is empty
p exists   => p == g and R is sorted, unique, and positive
```

An overdue, unsupported-bit, missing-support, multiple-unobserved-write, or
otherwise inconsistent root is not canonicalized into a best guess. It is
unavailable and falls back.

`enemy_manager_frame` remains only a versioned proxy within an ordinary
gameplay epoch. Equality of the identity across a semantic manager freeze
does not establish equality of the physical state because hidden player
updates can continue. The clock version must retain the open CE-0120 boundary.

### Actions and actual issue semantics

For selected complete mask `u`:

```text
u == g  => no write, no new delay sample, preserve/decrement old pending
u != g  => real write, sample declared pickup delay, newest write supersedes p
```

Until native `input_current` shows the held mask, the old active mask remains
active-action evidence. If an older pending command becomes visible before a
new write, the modeled physical sequence is:

```text
active -> older pending -> newly selected
```

The one-pending last-write-wins model is acceptable only while trace evidence
shows that every new complete-mask write replaces the estimator's previous
pending intent and that no second hidden edge can later reappear.

CE-0193 falsifies the stronger atomic-mask part of this root. The retained
native trace observes the first edge of ordered transaction
`0x65 -> 0x61 -> 0x41` as active `0x61`, while held/pending final desired is
already `0x41`. Thus

```text
(a, g, p, R)
```

is not a complete physical root for a multi-edge issue unless it also carries
the ordered transaction's delivered/sampled prefix or a conservative finite
support over every attainable prefix. Existing canonical identities with
model component `issue_semantics=complete-mask-no-write` identify only the
old atomic finite model; they must not be silently interpreted as the
corrected ordered-transaction version.

No-write remains unchanged: selecting `u == g` emits no edge transaction and
must preserve any older pending transaction. The controller still chooses
one complete mask, not each intermediate prefix. Exact transaction timing
relative to native player/input update remains unresolved and therefore
`UNKNOWN` for hard authority.

### Uncertainty and transition

The scalar belief oracle remains the independent recurrence authority for:

- recursively variable cadence;
- conditional write/no-write;
- every declared new-command delay;
- every current remaining-delay branch; and
- observation-compatible merging before the next controller maximization.

Python/C++ parity proves this finite recurrence only. It does not prove the
complete-mask estimator invariant, physical pickup behavior, hazard coverage,
or the manager-frame clock.

Hazard coverage is declared per inclusive physical-frame slab for the
complete physical hazard set:

| Class | Required meaning |
| --- | --- |
| `DETERMINISTIC` | The exact physical footprint and transition are known for every hazard in the slab. |
| `FINITE_SUPPORT` | A declared finite set exhausts every physical branch and the recurrence quantifies over all of it. |
| `BOUNDED_ENVELOPE` | A proved conservative envelope contains every physical footprint even when the exact branch is unknown. |
| `UNKNOWN` | No exhaustive branch set or conservative containing envelope is established. |

These are semantic claims, not confidence levels. A missing slab is
`UNKNOWN`. A component forecast for already observed bullets does not make
the complete slab known when future births, transforms, lasers, or contact
bodies can enter the reachable tube without cover.

For a root at frame `t`, coverage is required for every transition frame
`t+1..H`. The first missing or `UNKNOWN` slab produces:

```text
covered_through = first_unknown - 1
model_unknown_from = first_unknown
```

No clearance sample beyond that point may be interpreted as physical free
space. A solver may truncate its claim before the unknown point or return
`model_unknown`; it may not retain the original horizon claim.

### Horizon and resource constraints

The identity is for one exact query and target frame, one immutable policy,
one hazard version, and one model/clock version. It does not authorize reuse
by geometric proximity or nearby frames.

Hazard coverage is evaluated only over the root-reachable physical transition
horizon. Coverage slabs outside that interval provide no additional claim.
Timeout, cancellation, incomplete construction, or an unvisited branch
remains unresolved.

### Safety invariants

- Hard no-Bomb remains active; no `0x02` action authority is added.
- Inconsistent pipeline roots are unavailable, not repaired optimistically.
- Unknown or missing hazard coverage is never free space.
- The semantic clock sensor remains shadow-only.
- Repeated manager frame or a wall-duration threshold cannot reset gameplay
  epoch, delay state, policy version, or input authority.
- Policy consumers require an exact identity digest and immutable version.
- A future live consumer would still require a fresh issue-time local hard
  certificate and fail-closed fallback.

### Computation, publication, and fallback deadline

Identity construction and lookup must finish before issue time. Hazard
coverage construction may run offline or in a background service, but a
consumer performs lookup-only exact-version matching. It cannot start cold
coverage expansion on the issue thread.

Any identity mismatch, estimator inconsistency, coverage unknown, timeout,
stale policy, clock-boundary ambiguity, or missed deadline falls back to the
current live Boolean guidance plus a fresh local hard certificate. G1 does
not change current cadence, sensor reads, or actuator behavior.

## Formal Review

1. **Which physical histories map to one model state?** Histories merge only
   when their observable context, exact float32 position, complete
   active/held/pending masks, remaining-delay support, and every immutable
   version match. This is control-equivalent for the declared one-pending
   ordinary-manager-clock finite model. It is explicitly not claimed across
   CE-0120 semantic freezes.
2. **Are all uncertainty branches causal?** The independent scalar belief
   recurrence branches cadence, new delay, and hidden remaining support,
   merges equal observations, and only then maximizes the next action.
   Coverage classes require exhaustive finite support or a conservative
   containing envelope; unknown branches stop the claim.
3. **What physical question does an exact solve answer?** With complete
   coverage and a valid root it answers robust survival in the declared
   finite movement/pipeline/hazard model. Without physical coverage or clock
   equivalence it answers only a proxy.
4. **What is solved or bounded, and what falsifies it?** The scalar/native
   solver is exact for its finite recurrence when completed. A
   `BOUNDED_ENVELOPE` is conservative only if every physical footprint is
   contained. Falsifiers include a native pickup outside carried support, an
   old hidden write reappearing, a future hazard entering outside its
   declared support/envelope, or a semantic freeze changing position under
   an allegedly equivalent identity.
5. **Can the result be consumed before issue time?** G1 is shadow-only.
   Eventual authority requires exact-version lookup before issue time without
   changing cadence, sensor state, clock epoch, or the immutable problem.

## G1 Validation Sequence

1. Unit-test canonical mask identities, version invalidation, multikey roots,
   no-pending and one-pending invariants.
2. Unit-test complete, finite-support, bounded-envelope, missing, and unknown
   coverage slabs, including unknown on the first reachable transition.
3. Add trace-only identity and coverage records without changing action
   choice, writes, estimator state, sensor cadence, or epoch handling.
4. Build an independent chronological audit for:
   - multikey complete-mask transitions;
   - no-write pending carry;
   - one-pending last-write-wins replacement;
   - observed native pickup;
   - remaining-support/estimator continuity;
   - clock shadow/no-reset authority; and
   - fail-closed hazard coverage.
5. Retain Linux scalar/native differentials and run the Windows pickup trace
   gate. Then perform one focused hard-no-Bomb physical shadow run and audit
   the resulting trace.

Only after all gates pass may a separate proposal discuss full pipeline live
authority. Passing G1 does not itself promote one.

## Observed G1 Shadow Result

Commits `ff1af3c` and `e4d994f` implemented the canonical identity,
fail-closed slab contract, TH08 trace adapter, exact issue-transaction
telemetry, and independent chronological audit.

Automated evidence:

- the new identity/coverage/adapter/audit tests add 18 deterministic cases;
- the complete quick suite passes `653/653` on Linux in `5.628 s`;
- the same `653/653` pass on Windows in `8.784 s` with three existing
  platform skips;
- the independent scalar variable-cadence suite passes all eight tests;
- the quick belief workspace profile has 16 scalar/native differential cases
  with zero lower, upper, candidate, or certification failure; and
- the bounded formal audit retains its known legacy/no-write counterexamples
  without a new causal-recurrence failure.

Physical shadow:

```text
hard_route2_stage1_unattended_20260727_153821
```

The accepted Hard Stage-1 run completed 7,574 decisions through
`route_complete`, hard no-Bomb verification, supervisor cleanup, and no
residual game/controller process. The same raw trace was independently
audited by Linux and Windows Python with identical results:

| Measurement | Count |
| --- | ---: |
| valid canonical identities | 7,574 |
| continuity pairs | 7,573 |
| trace/identity/continuity failures | 0 |
| complete-mask writes / no-writes | 3,106 / 4,468 |
| multikey transactions | 1,513 |
| last-write-wins replacements | 173 |
| pending no-write carries | 92 |
| native-observed pickups | 2,900 |
| target already active, not pickup proof | 33 |
| roots with fail-closed future-event `model_unknown` | 7,574 |

This validates trace identity, issue ordering, estimator continuity, native
pickup observation, and unknown-coverage handling for this physical
workload. It does not validate physical survival: the attempt took one hit at
frame 2,651 after kernel exhaustion and is appended to CE-0132.

### Newly observed promotion blocker

The audit also found 135 real complete-mask writes whose movement/focus
projection did not change. One occurred while a different native movement
was active and a command was pending:

```text
frame 13133
active       = 0x05  (stay + Focus + Shot)
held/pending = 0x85  (right + Focus + Shot)
selected     = 0x84  (right + Focus, Shot released)
```

The physical dispatch released the Shot key and called
`delay_estimator.issued`. The current scalar/native movement recurrence sees
only `selected_action == held_desired_action == right` and therefore calls it
no-write. The immediate movement can happen to remain equivalent because the
older and newer desired movement are both right, but the complete observed
mask, pending identity, remaining support, and later issue semantics are not
the same finite state.

This is CE-0134. Its approximation direction is unknown for a recursive
policy. Full pipeline live authority remains blocked until either:

1. complete desired masks (or an equivalent issue token) participate in
   action, observation, pending, and memo identity throughout the scalar and
   native recurrences; or
2. a physically verified actuator invariant forbids every movement-equivalent
   complete-mask reissue while a command is pending.

The first option is the preferred model correction. Until it is implemented,
scalar/native parity proves only the movement-action recurrence. In addition,
all physical roots remain coverage-truncated by unseen future hazards and
CE-0120 remains open. The G1 instrumentation/validation checkpoint is
complete; its live-promotion result is explicitly **not ready**.
