# Exact Augmented-Root Partial-Survival Witness Contract

Date: 2026-07-27

Status: proposed G3 offline oracle checkpoint; no live or shadow action
authority

## Question

After the declared finite model is losing, or while an unrestricted result is
still unresolved, can the solver retain a completed causal policy that
guarantees a smaller collision-free prefix without turning incomplete work
into a losing or optimality claim?

The answer is yes only when the retained object is an attainable lower
witness for an exact immutable augmented root. The first checkpoint covers
stationary continuation policies because each is completely described,
independently replayable, and already has exact scalar/native label support.
Budgeted and wider causal policy classes remain later extensions.

## Physical Objective

Survival remains hard. For one exact decision root, maximize

```text
(guaranteed collision-free physical frames,
 worst-branch bottleneck signed clearance)
```

inside a declared restricted continuation-policy class. A partial label is a
finite-model lower bound. It is not indefinite physical survival, unrestricted
finite-model optimality, or permission to issue the root action.

## State And Available Observation

The public information state is

```text
b = (frame, row, column, active action,
     pending desired action or none,
     remaining-delay support)
```

plus controller-visible continuation budget when a later checkpoint enables
budgeted policies. Histories merge before the next controller choice when
they produce the same observable frame, lattice cell, active/pending action,
and declared remaining-delay observation bucket. The physical information
set uses no hidden-delay bucket.

The witness key retains:

- a content digest of axes, float32 clearance volume, ordered action
  definitions, delay support, recursive cadence support, clearance
  threshold, boundary semantics, and horizon;
- exact public root fields and pending remaining-delay support;
- the restricted policy definition and digest; and
- exact label and worst-branch witness digest.

## Actions And Actual Issue Semantics

Every public root action is evaluated; proposal pruning at the root is
forbidden. The first checkpoint then uses one declared stationary
continuation action at every later public observation.

Selecting the desired action already held by the actuator is no-write. It
samples no new delay, preserves an existing pending command, and decrements
its remaining-delay support. Selecting another complete action creates the
declared last-write-wins pending command and lets nature choose a pickup delay.

The stationary class is conservative relative to the unrestricted controller
because it removes future controller choices without removing nature
branches.

## Uncertainty, Transition, And Horizon

Nature universally chooses:

- the hidden member of the current remaining-delay support;
- a new pickup delay after an actual desired-action transition; and
- one admitted decision cadence at every recursive decision epoch.

Transitions use the independent Python belief specification from
`touhou_control.variable_cadence_oracle`. Hidden branches that produce the
same next observation are merged before continuation. The witness records the
worst observation group, one deterministic hidden prefix branch attaining
that group's prefix margin, and the merged successor support.

The horizon is the supplied finite clearance volume. Reaching its final frame
does not imply safety afterward.

## Witness Result

For every root action, a completed stationary witness contains:

- exact problem digest and augmented root;
- root and stationary continuation actions;
- policy digest;
- guaranteed frames and bottleneck margin;
- deterministic worst nature/observation branch path;
- evaluated scalar state count; and
- a content digest over the complete witness.

The portfolio chooses the best completed stationary witness independently for
every root action, then reports the best attainable state label and all tied
root actions. A portfolio is complete only when every declared root action
has a completed witness. This checkpoint has no timeout path; later native
or background implementations must preserve completed witnesses, mark
timed-out/unvisited actions unresolved, and never publish a partial root-action
set as complete.

Modes remain distinct:

- `POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS`: the exact unrestricted declared
  model is completed losing, while this restricted policy retains a positive
  shorter prefix;
- `PARTIAL_WITNESS_ON_UNRESOLVED`: unrestricted work is incomplete, while the
  restricted policy supplies an attainable lower bound;
- a completed full-horizon positive witness is finite-model feasibility and
  must not be mislabeled partial.

## Safety And Publication Invariants

- Root actions are exhaustive and ordered exactly as the problem action set.
- Cadence applies recursively.
- Remaining delay is an information set, not separately maximized exact roots.
- Same desired input preserves pending no-write semantics.
- The stationary continuation may depend on no hidden state.
- Float labels retain exact binary content in digests.
- A digest/version/root mismatch, unsafe current state, incomplete root-action
  set, timeout, or unvisited action fails closed.
- Offline witnesses never change `Decision.mask`.
- Any later consumer must exact-match the immutable version and intersect the
  proposed root action with a fresh issue-time hard certificate.
- Bomb bit `0x02` remains forbidden by the live policy.

## Five Required Reviews

### 1. Which histories map to one model state?

Histories merge when all observations declared above agree. They are
control-equivalent only for the finite transition and observation model. A
physical future hazard absent from the clearance volume can break physical
equivalence; G5 coverage and fresh local certification bound but do not
eliminate that risk.

### 2. Are quantifiers causal and complete?

Yes for the declared stationary class if every hidden delay, new pickup
delay, recursive cadence, and merged successor-support branch contributes to
the minimum before continuation. The controller selects the public root
action once and has no hidden-conditioned continuation choice.

### 3. What physical question does an exact solve answer?

It answers whether the declared stationary policy guarantees the reported
finite-model prefix from this exact root. It does not answer indefinite
survival, unmodeled births/transforms, or unrestricted optimality.

### 4. What does the algorithm prove, and what falsifies it?

It proves an attainable lower bound. It is falsified by any scalar/native
label mismatch, omitted nature branch, split hidden branch before the next
observation, nonrecursive cadence, no-write reset, digest instability,
incomplete root-action portfolio marked complete, or worst path whose
replayed label differs from the witness label.

The independent checks are:

1. the existing scalar belief result;
2. the native belief workspace;
3. direct worst-path replay;
4. deterministic action-order and digest stability; and
5. adversarial pending/no-write, cadence, boundary, unsafe-current, and
   tie cases.

### 5. Can it be consumed before issue without changing the problem?

Not in this checkpoint. The scalar witness is offline and may be expensive.
A later native/background service requires cooperative cancellation,
newest-version-first scheduling, exact-version lookup only, complete-only
publication, Windows contention/deadline evidence, and a fresh local hard
intersection. A lookup miss must not start cold work on the issue thread.

## Staged Gates

1. Implement the independent stationary scalar witness and complete
   all-root-action portfolio.
2. Prove label parity against the existing scalar result and native belief
   workspace on deterministic and randomized small cases.
3. Retain a compact G3 report on exact Stage-4A and Stage-6B capsules,
   separating full-horizon feasibility from partial lower witnesses and
   unresolved roots.
4. Add native worst-branch/policy-witness extraction without changing the
   existing 46-symbol ABI until a separately reviewed ABI checkpoint.
5. Measure cancellable background delivery and Windows contention before any
   shadow publication experiment.

No step in this contract promotes S09, S16, candidate witnesses, survival
labels, or partial witnesses into live action authority.
