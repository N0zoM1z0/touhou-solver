# Complete-Mask Issue-Action Contract

Date: 2026-07-27

Status: offline scalar/native model correction implemented; no live action
authority

This note closes the modeling ambiguity exposed by CE-0134. It refines the
input portion of
`AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` and
`PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md`; it does not weaken
their hazard, cadence, observation, publication, or fallback requirements.

## Evidence And Claim Labels

- **Observed:** Windows Hard Stage-1 trace `153821`, frame/decision 13,133,
  records native active mask `0x05`, held and pending desired mask `0x85`
  with remaining support `[1,2,3]`, and selected mask `0x84`. Releasing Shot
  was a real physical write and estimator issue.
- **Observed in source:** the current live actuator compares and writes
  complete masks, releases keys before presses, samples a new delay on a real
  write, and preserves pending state on complete-mask no-write.
- **Observed in source:** the corrected Python and C++ belief recurrences
  canonicalize pending state only when pending and active *action indices*
  are equal. They do not compare velocities.
- **Observed before correction:** the native belief workspace accepted at
  most 32 action indices and represented action subsets with `uint32_t`.
- **Observed after correction:** belief ABI `create_v7`, `query_v3`, and
  `certify_upper_v3` use 64-bit action masks and accept up to 64 actions.
  Legacy v1-v6 creation and v1-v2 query/certification ABIs remain exported,
  retain their 32-action boundary, and pass a direct runtime compatibility
  smoke.
- **Inferred:** unique complete-mask action tokens can reuse the corrected
  recurrence without changing its information-set quantifiers because action
  index equality already supplies the required issue identity.
- **Not proved:** Python/native parity for the expanded alphabet is not
  physical-model validation. Future hazard coverage, CE-0120's clock
  boundary, scheduler semantics, and deadline delivery remain independent
  gates.

## Physical Objective

Keep the player collision-free under every declared hazard, input-pickup, and
controller-cadence branch while issuing only physically available no-Bomb
input masks. Shot, Focus, and direction bits participate in actuator state
even when two masks have the same instantaneous movement velocity.

Survival remains hard. Releasing Shot is not rewarded, but it remains a
physically available issue action whose pipeline consequences cannot be
silently collapsed.

## State And Observations At A Decision

The finite root contains:

```text
(physical frame,
 float32 player state,
 observed complete active mask,
 held complete desired mask,
 pending complete desired mask or none,
 pending remaining-delay support,
 hazard/model/clock/policy versions,
 resource and horizon state)
```

The controller observes native active input and its own held desired mask. A
pending token and its support are estimator information, not an independently
observed exact delay. Hidden branches that have the same next observation are
merged before the next controller maximization.

Complete masks are mapped injectively to action tokens. Equal
`(velocity_x, velocity_y)` does not imply equal action identity.

## Action Alphabet

For current TH08 no-Bomb authority:

```text
direction ∈ {neutral, up, down, left, right,
             up-left, up-right, down-left, down-right}
focus     ∈ {off, on}
shot      ∈ {off, on}
```

This yields 36 legal complete-mask tokens. Bomb bit `0x02` is excluded.
Opposing direction pairs are not selectable canonical tokens. An observed,
held, or pending mask outside this alphabet is an estimator/model mismatch
and must fail closed rather than alias to an ordered movement direction.

The 36-token alphabet includes focused and unfocused neutral masks. The old
17-action movement alphabet omitted unfocused neutral because both neutral
velocities are zero; that collapse is invalid for issue identity.

## Issue And No-Write Semantics

Let `h` be the held complete desired token and `u` the selected token.

```text
if u == h:
    no physical write
    no new delay sample
    preserve any existing pending token
    decrement its remaining support through elapsed physical frames
else:
    emit the complete ordered key transaction
    sample one declared pickup delay
    held desired / latest pending identity := u
```

Pickup changes the active complete token when the delayed write becomes
visible. Movement during each physical frame uses the velocity attached to
the active token. Two tokens may therefore share every movement endpoint yet
produce different active/pending observations and different future no-write
choices.

The retained recurrence permits an older already-in-flight transition to
become active before the newly written token when their declared remaining
times order that way. At the next decision boundary, the older token is
active—not still the held/pending desired token—and the newly selected token
is the sole pending desired token if it is still unseen. “Last write wins”
refers to held desired identity, not retroactive cancellation of a pickup that
has already advanced far enough to become observable.

### CE-0193 correction to atomic pickup

“Emit the complete ordered key transaction” does not mean that the shipped
game observes one atomic complete-mask change. The runtime orders all
releases by ascending bit, then all presses by ascending bit, and sends the
edge array in one Win32 batch. Physical Stage-5 trace evidence observes
native active mask `0x61` between the two release edges of
`0x65 -> 0x61 -> 0x41`, while the actuator already remembers final desired
mask `0x41`.

Consequently:

- the 36-token alphabet remains the controller action alphabet and final
  desired identity;
- one token issue expands into one ordered transaction, not multiple
  controller decisions;
- native active identity may temporarily be an ordered prefix mask distinct
  from old, older-pending, and final tokens;
- the transaction suffix/prefix uncertainty must be part of the physical
  information state; and
- the current atomic old/final pickup recurrence is rejected for hard,
  publication, or live authority.

The independent scalar correction now represents
`(active, held_final, remaining_ordered_masks, completion_remaining)`.
Before the final deadline, nature may stutter or expose any monotone
non-final prefix; at the deadline final held input is forced. A new write
appends its deterministic release-then-press path after the older suffix.
Selecting held final input remains true no-write and preserves that suffix
and deadline. Observation-compatible hidden states merge on active and held
mask before the next controller choice.

Connected IDA revalidation closes the callback order inside one native
update: priority-9 player processing reads the current word at `0x0044AEE8`;
priority-17 saves previous once at `0x00452339`, writes current from the first
raw sample at `0x00452347`, and on its full path overwrites current from a
second raw sample at `0x004523C7`. All five exits converge at
`0x00452480`. The callback-exit current is the publication observation; the
first store alone is not. This does not close where an asynchronous
capture/issue falls relative to that callback pair, nor prove the scalar
completion deadline against a native publication clock. Manager-frame delta
remains invalid as a substitute.

The default-off priority-17 preflight probe therefore hooks only the common
epilogue and records callback-exit raw/current/previous with a monotone
serial. A real complete-mask transaction retains pre/post serial brackets;
no-write samples nothing. This is trace-only instrumentation. Until a
complete physical report retains every serial in an audited interval, it
does not change the delay support or grant action authority.

## Uncertainty And Transitions

The action correction changes only action identity. It preserves:

- the declared input-pickup delay support;
- recursive controller cadence support;
- observation-compatible belief merging;
- last-write-wins one-pending semantics;
- float32 position and margin behavior;
- hazard branches and coverage classifications;
- horizon, bounds, clearance, and resource constraints.

Nature chooses every declared pickup/cadence/hazard branch. The controller
cannot condition on hidden exact remaining delay before that value becomes
observable under the declared observation contract.

## Horizon, Resources, Safety, Deadline, And Fallback

- Horizon and terminal continuation are unchanged from the parent formal
  contracts.
- Bomb remains forbidden. Other resource state is not converted into a
  scalar safety weight.
- Every transition must retain signed clearance and lattice-sampling error.
- An exact result is consumable only for an identical immutable complete-mask
  alphabet and root identity before issue time.
- Timeout or unsupported masks enlarge the unresolved set.
- Live misses retain the current Boolean policy intersected with a fresh local
  hard certificate. This checkpoint adds no live lookup or issue path.

## Five Required Questions

### 1. Which physical histories map to one model state?

Histories merge only when their observed float32 state, complete active token,
held desired token, pending token/support, versions, resources, and declared
observation context agree. Histories differing only in hidden exact delay may
merge if they produce that same information set. Histories differing in Shot
or Focus bits do not merge merely because their current velocity agrees.

### 2. Are all uncertainty branches causal?

The existing belief recurrence retains controller-exists/nature-for-all
ordering and observation merging. The issue token is selected before pickup
delay and future cadence/hazard branches. Distinct hidden branches cannot be
maximized independently.

### 3. What physical question would an exact finite solve answer?

It would answer no-Bomb survival for the declared finite hazard, movement,
delay, cadence, observation, horizon, and action-alphabet model. It would not
answer survival through missing future births, an invalid clock boundary, or
unmodeled scheduler behavior.

### 4. Does the algorithm solve or bound that recurrence?

The independent scalar belief oracle is the reference exact finite
recurrence. The native belief workspace implements the same recurrence with
64-bit action subsets. Differential comparison covers the state label, all 36
root action labels, best-action masks including indices above 31, and upper
unresolved masks including indices above 31.

Falsifying cases include:

- canonicalizing two equal-velocity, unequal-mask tokens together;
- treating `0x85 -> 0x84` as no-write;
- retaining the older token as held/pending desired after that real write;
- allowing Bomb or contradictory direction masks;
- scalar/native mismatch for any action label or hidden branch.

### 5. Can the result be consumed before issue time?

Not yet. Native 64-bit action support and bounded scalar/native parity now
pass, but this remains an offline recurrence correction. Representative
complete-mask workload performance, exact-version publication, future-hazard
coverage, and CE-0120 must pass independently before any live consumer is
proposed.

## Implementation Boundary And Staged Gate

Checkpoint A introduces:

- game-neutral `CompleteMaskAction` / `CompleteMaskActionSpace`;
- a 36-token TH08 adapter;
- injectivity, no-Bomb, valid-direction, old-movement-projection, and CE-0134
  regressions.

Checkpoint B adds a backward-compatible 64-bit belief-workspace ABI while
leaving legacy direct/viability 32-bit masks unchanged. It proves:

```text
scalar_belief_result(36 complete tokens)
==
native_belief_result(36 complete tokens)
```

field by field for the state label and all 36 action labels.

The retained minimal adversarial fixture has active `0x05`, remaining support
`[1,2]`, delay support `[1,3]`, cadence support `[1,2]`, and a three-token
restricted causal continuation. Changing only the pending identity from
`0x85` to equal-velocity `0x84` swaps the two root values:

```text
pending 0x85: select 0x85 -> (5, +1), select 0x84 -> (2, -1)
pending 0x84: select 0x84 -> (5, +1), select 0x85 -> (2, -1)
```

Python scalar and C++ native labels match exactly. This falsifies any claim
that complete-mask identity can be reconstructed from velocity without
changing finite-game values.

Checkpoint B passes as an offline native solver capability. The legacy
32-bit ABI smoke, exact export manifest, Linux/Windows builds, and action bits
above 31 pass. Until the remaining G1 blockers close, the corrected
recurrence remains offline/shadow only.

Checkpoint C adds the independent ordered-transaction oracle and composes it
with the TH08 SEM-MODE priority-9/11 body-gate transition at a declared
post-priority-17 root boundary. The old atomic SEM-MODE APIs remain available
only as rejected differential baselines. Nine game-neutral and four TH08
ordered regressions pass, including CE-0193, no-write, overwrite, hidden
deadline merging, priority-9-before-priority-17, and fail-closed intermediate
action identity. Complete Linux/Windows discovery passes 1,202 tests in
14.611/30.759 seconds; Windows retains three existing skips.

Checkpoint C is offline conservative model evidence. It changes no live
planner, actuator, input cadence, publication, damage objective, or strategy.
Capture/issue-to-publication phase, physical delay support, optimized/native
parity, immutable future body/geometry versions, and a whole-stage physical
falsifier remain open.
