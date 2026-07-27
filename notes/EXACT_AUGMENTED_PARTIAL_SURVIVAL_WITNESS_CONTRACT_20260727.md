# Exact Augmented-Root Partial-Survival Witness Contract

Date: 2026-07-27

Status: G3 stationary scalar/oracle parity, retained-capsule, internal native
extraction, and complete-mask capsule audit implementation complete; joined
physical evidence and delivery remain open; no live or shadow action authority

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
   all-root-action portfolio. **Complete in `5e48f3d`.**
2. Prove label parity against the existing scalar result and native belief
   workspace on deterministic and randomized small cases. **Complete for four
   deterministic/randomized seeds plus pending/no-write, cadence, digest,
   unsafe-current, tie/mode, and tamper cases.**
3. Retain a compact G3 report on exact Stage-4A and Stage-6B capsules,
   separating full-horizon feasibility from partial lower witnesses and
   unresolved roots. **Complete for the historical 17-action capsule model in
   `ba4e66f`; CE-0134 complete-mask roots remain a later model gate.**
4. Add native worst-branch/policy-witness extraction without changing the
   existing 46-symbol ABI until a separately reviewed ABI checkpoint.
   **Complete internally in `25d5f68`; full-path Python/native differentials
   pass and the production export manifest remains exactly 46 symbols.**
5. Join one physical canonical complete-mask root to its same-session
   retained hazard capsule while keeping unknown future events fail closed.
   **Audit implementation complete in `48f7e56`; joined physical evidence is
   pending because the prior traces contain only one side of the join.**
6. Measure cancellable background delivery and Windows contention before any
   shadow publication experiment.

No step in this contract promotes S09, S16, candidate witnesses, survival
labels, or partial witnesses into live action authority.

## Implemented Stationary Checkpoint

Checkpoint `5e48f3d` keeps the public import in the 31-line
`touhou_control.partial_survival_witness` facade and separates immutable
records/canonical payloads, problem digesting, recurrence, replay, and
portfolio construction under `touhou_control.partial_witness`.

**Observed:** the new witness labels match both the existing scalar belief
oracle and the native belief workspace for every root action in four
small randomized clearance volumes. Focused adversarial cases retain
same-desired pending no-write, recursive cadence, complete ordered root
actions, stationary-candidate maximization, mode separation, exact float32
problem identity, deterministic content digests, unsafe-current failure, and
tamper rejection. Worst-path replay checks policy choices, root identity,
successor links, nested labels, and policy/witness digests.

**Observed:** the focused `touhou_control` suite passes `167/167`. Complete
quick suites pass `720/720` on Linux in `9.678 s` and Windows in `13.093 s`
with three pre-existing platform skips.

**Inferred:** these checks establish implementation parity and an attainable
lower bound for the declared stationary class. They do not establish physical
hazard completeness, unrestricted optimality, issue-time delivery, or live
action authority.

Checkpoint `ba4e66f` completes Gate 3 for exact retained historical
17-movement-action capsules. The first five eligible Boolean-empty roots in
both Lunatic Stage 4A and Stage 6B contain full 32-frame feasibility, positive
12/17-frame partial witnesses on unresolved roots, and no-positive stationary
roots. All root-action portfolios complete; selected witnesses replay and
match native guaranteed frames with margin error below `1e-5`. CE-0140 records
the resulting rejection of Boolean-empty or stationary exhaustion as
unrestricted exact losing. Complete-mask roots, delivery, and physical
consumption remain open. Retained evidence and the exact reproduction command
are in `G3_STATIONARY_PARTIAL_SURVIVAL_CAPSULE_GATE_20260727.md`.

Checkpoint `25d5f68` completes Gate 4 behind the existing public ABI. The
native transition records hidden remaining delay, recursive cadence, and
pickup/no-write; a separate deterministic module merges
observation-compatible branches and extracts the complete worst path. Linux
and Windows probes match the independent Python path on randomized
all-root-action, pending no-write, merged-support, and unsafe-root cases.
Delivery/contention remains Gate 5; details are in
`G3_NATIVE_STATIONARY_WITNESS_GATE_20260728.md`.

Checkpoint `48f7e56` implements the exact complete-mask physical
root/capsule audit boundary. It rebuilds the content-addressed root and
coverage record, completes every one of the 36 no-Bomb root actions under the
exact held-mask stationary continuation, replays every worst path, and checks
native labels. Unknown future-event coverage still yields
`physical_action_authority = none`. Joined physical evidence and delivery
remain open; details are in
`G5_COMPLETE_MASK_CAPSULE_JOIN_GATE_20260728.md`.
