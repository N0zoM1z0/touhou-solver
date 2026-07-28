# Local Pipeline Certificate And Beam Audit

Status: **verified offline/shadow infrastructure; no new live action
authority**.

This checkpoint investigates the local micro-control layer separately from
the global Boolean/belief planner. It fixes one batch-geometry correctness
defect, implements an explicit active/held/pending finite-lease certificate,
and measures two beam-state refinements. It does not claim that the complete
physical solver is now safe or that a local certificate proves recursive
viability.

The base authority and information contract is
`notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`. The frozen
manager-frame boundary remains governed by
`notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.

## Evidence Labels

- **Observed:** retained trace fields, deterministic scalar/packed
  differentials, batch-invariance regressions, replay outputs, and measured
  Linux wall times.
- **Inferred:** active/held/pending roots reconstructed from the previous
  write in old traces whose schema predates explicit local-root telemetry.
- **Hypothesized:** a physical survival improvement, a complete input-clock
  boundary, or a globally optimal local beam. None is claimed here.

## Finite Local Problem Contract

### Physical objective

For each candidate complete movement/focus mask, reject a candidate if any
declared pickup-delay history collides during the finite lease. Among the
remaining candidates, expose robust clearance and risk to the existing local
ranking. Survival remains the hard objective; items, damage, position, and
score do not weaken the certificate.

### State and observation at the decision

The local root is

```text
(player position,
 observed native active action a,
 controller-held desired action h,
 optional older pending action p,
 conditioned remaining-delay support R,
 current projected hazard snapshot)
```

Actions are the complete movement/focus projection of the mask. `SHOT` is a
hard invariant and Bomb is forbidden, so neither is a local choice.
Zero-direction focused `stay` and `stay_unfocused` remain distinct actuator
identities even though both have zero instantaneous velocity.

The current estimator invariant permits at most one older pending command:

- no pending command implies `h == a`;
- a pending command implies `h == p`;
- a root that does not satisfy that invariant is uncertifiable.

The old retained traces contain native `input_current`, issued masks, and
delay-estimator inputs, but not this complete root. Their roots are therefore
reconstructed evidence, not direct observations. New trace rows now retain an
explicit `local_pipeline_root` record with active/held/pending masks, their
motion-action projections, and an estimator-consistency flag. Replay prefers
this record and fails closed on mask/action/snapshot/prior-write disagreement.
The record is telemetry only.

### Actions and actual write semantics

The controller selects one complete action `u`.

- If `u == h`, the actuator receives no write. No new pickup delay is sampled,
  and the older pending command continues with its remaining support.
- If `u != h`, a write occurs and nature selects a new delay `d` from the
  declared support.
- Before the new write becomes active, an older pending command may become
  active. The exact physical prefix is

  ```text
  a, while j <= rho
  p, when j > rho and j <= d
  u, when j > d
  ```

  with absent branches omitted. This is the last-write-wins ordering already
  declared by the base formalization.

The default hard-no-Bomb contract is unchanged.

### Uncertainty and transition

Nature universally selects every conditioned older remaining delay
`rho in R` and, only for a real write, every new pickup delay in the current
support. Player motion is clipped to the TH08 playfield and the existing
bullet, laser, enemy-body, boundary, lag, and transform uncertainty is
evaluated at every physical step.

This local certificate contains no future controller maximization. Therefore
there is no future hidden observation on which separate controller actions
could branch. It neither replaces nor approximates the recursive cadence
recurrence.

### Horizon, resources, and fallback

The finite lease is

```text
action_hold_frames + max(new pickup-delay support)
```

physical steps. It spends no Bomb or other resource. If the explicit root
cannot be established, live code continues to use the existing conservative
fallback boundary in which active and held are both the last desired mask.
The pending-aware result remains shadow-only until an explicit-root physical
shadow and delivery gate pass.

### Safety invariant and deadline

A locally safe action has zero collision count and nonnegative robust
clearance on every enumerated branch. The certificate is useful only if it is
computed from fresh hazards and consumed before issue. A miss, inconsistent
root, stale result, or deadline failure cannot become permission to issue an
otherwise uncertified action.

The manager frame is not assumed to be a universal physical input clock.
Nothing in this checkpoint neutralizes movement, resets an epoch, or changes
the CE-0120 authority boundary.

## Formal Review Questions

### 1. Which histories map to one state?

Histories are merged when they have the same observed active action, held
desired action, optional pending action, conditioned remaining support,
player state, and hazard snapshot. Under the one-pending estimator invariant,
those histories have the same declared finite set of physical action prefixes
and are control-equivalent for this fixed lease.

Histories with different active input or remaining support are not merged.
The older traces do not directly prove their reconstructed roots, which is
why they cannot promote the pending-aware path.

### 2. Are all uncertainty branches causal?

Yes for the declared finite lease: the controller chooses one action before
nature selects older remaining delay and, when a write occurs, new pickup
delay. The controller cannot choose a different continuation for either
hidden value. Holding the desired mask creates no independent new-delay
branch.

Recursive controller cadence, future observations, future hazard births, and
the frozen-manager scheduler boundary are outside this certificate rather
than silently collapsed.

### 3. What physical question does an exact solve answer?

It answers whether one root action survives the current finite local lease
under the existing projected geometry and declared pickup uncertainty. It is
only a proxy for complete physical survival because it omits recursive
cadence, post-lease control, unseen future births, model error, and the
unresolved frozen-manager duration.

### 4. What is exact, and what would falsify it?

`touhou_control/local_pipeline_oracle.py` is an independent scalar
branch-by-branch oracle. The packed TH08 implementation is exact relative to
that finite recurrence, subject to the same float32 geometry functions.
Twenty-four deterministic randomized roots plus focused pending/no-write
cases currently have scalar/packed parity.

The claim is falsified by any root/action for which:

- packed and scalar collision, clearance, risk, or worst-branch metadata
  disagree beyond the declared numeric tolerance;
- adding an unrelated companion position changes a position's hazard result;
- holding the desired action samples a fresh delay or destroys the older
  pending command; or
- a reconstructed explicit root disagrees with new direct telemetry.

The last item is a required future physical-shadow gate.

### 5. Can the result arrive before issue?

The replay certificate timing includes bullet/laser projection and packing
from already decoded TH08 objects, plus all-action induction and
certification. It excludes JSON parsing and trace-to-object decoding. On the
sampled Stage-4A/Stage-6B roots, pending-aware packed certification measured
`3.134/6.372 ms` and `3.936/7.911 ms` median/p95. This is promising but is not
a Windows issue-thread deadline proof, and the pending-aware result is not
yet consumed live.

## Defects Found And Corrections

### CE-0122: batch membership changed hazard clearance

The vectorized bullet and laser coarse filter first selected hazards near
*any* position in the batch, then applied every selected hazard to *every*
position. A position's positive clearance and soft risk could therefore
change when an unrelated far-away candidate was added to the same call.

The correction retains the global coarse slice for performance and adds a
per-position relevance mask before collision, robust-clearance, and risk
reduction. The regression compares a two-position batch with two independent
one-position calls for both bullets and lasers.

This was a real geometry correctness/stability defect. The correction applies
to the existing live local geometry path, but its physical effect has not yet
been measured.

### CE-0123: local certification reset the pending pipeline

The prior local certificate used the last desired mask as if it were the
native active input and sampled a fresh full pickup delay for every candidate,
including the already-held desired mask. It consequently omitted the
observed-active prefix and erased the no-write/pending distinction.

The correction:

- makes active, held desired, optional pending, and remaining support explicit;
- enumerates older/new delay products without hidden controller choices;
- treats a held mask as no-write;
- evaluates all branches in one packed position batch; and
- records write/branch/worst-pending metadata in each certificate.

The existing live call sites do not yet supply this explicit root. Their
default root remains active-equals-held, so the pending-aware semantics have
not silently gained action authority.

## Retained Replay Evidence

Artifact:
`artifacts/benchmarks/local_pipeline_certificate_20260726.json`
(`SHA-256 15e9d2d8b1968dedc6d2cf957506cb4ac6870a43c7e32d04ab70766d3f48ac46`).

The sample deliberately over-represents active/held mismatches and 240-frame
pre-hit windows. Counts below are sample differentials, not population rates
or causal hit-prevention estimates.

| Workload | Sample | Safe-set changes | Ranked-action changes | Recorded old-safe/new-unsafe | Recorded old-unsafe/new-safe | Packed-equivalent hard parity failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage 4A `122014` | 155 | 86 | 76 | 21 | 0 | 0 |
| Stage 6B `011639` | 156 | 85 | 73 | 9 | 2 | 0 |

Pre-hit subsets changed their safe set on `25/41` Stage-4A roots and `23/38`
Stage-6B roots. That association shows materiality of the model difference;
it does not prove that the new label would have prevented a native contact.

The held/no-write certificate changed on `148/155` and `145/156` sampled
roots. This large result is expected because sampling targeted active/held
mismatches, but it confirms that no-write semantics are not a negligible
corner case.

Representative inferred counterexamples include:

- Stage-4A frame `1738`: native active `left_fast`, held/pending `up_fast`,
  remaining support `1..3`; the recorded `left_fast` action changed from zero
  modeled collisions and `+0.028` clearance to five collisions and `-3.953`
  clearance.
- Stage-4A frame `2025`: native active `stay_unfocused`, held/pending
  `down_left_fast`, remaining support `1..3`; the recorded `left_fast` action
  changed from `+6.725` to `-1.760` modeled clearance.

Exact rows and up to sixteen examples per workload are retained in the
artifact.

### Timing

| Workload | Legacy semantics, fixed batch median/p95 | Packed equivalent root median/p95 | Packed pending-aware root median/p95 |
| --- | ---: | ---: | ---: |
| Stage 4A `122014` | `4.786/6.763 ms` | `2.265/3.487 ms` | `3.134/6.372 ms` |
| Stage 6B `011639` | `5.819/11.719 ms` | `2.804/6.094 ms` | `3.936/7.911 ms` |

On the Stage-4A `>=1000` active-bullet bin, pending-aware certification was
`4.533/7.522 ms` median/p95. The Stage-6B timing bins are not monotone with
density and are consistent with host scheduling noise; these are
single-host wall measurements, not deterministic WCET.

## Beam Stability Experiment

Artifact:
`artifacts/benchmarks/local_beam_stability_20260726.json`
(`SHA-256 747e6a39a88233f308f292a0670804992cc4c5e5d703c5da1cfd4576e7ec098f`).

Two default-off research modes were compared with the existing width-24
quantized beam:

1. add the root first-action identity to the quantized deduplication key;
2. preserve exact `(x, y, action, focus, collected, first action)` labels.

A width-256 exact-first-action beam was retained only as a sensitivity
reference. It is not an oracle. A second expensive experiment gave each
allowed first action an independent width-24 continuation beam on the roots
where the baseline hard vector was nonzero.

| Workload | Sample | First-action mode action changes | Hard better/worse | Baseline vs width-256 changes | Exact mode matches width-256 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 4A `122014` | 96 | 5 | `0/0` | 38 | 57 |
| Stage 6B `011639` | 96 | 4 | `0/0` | 30 | 68 |

The independent-first-action partition changed no action and improved no hard
vector on the five Stage-4A and six Stage-6B hard-nonzero roots. Its whole
partition median was `191.795 ms` and `275.649 ms`, respectively.

The default beam took `8.042/12.582 ms` Stage 4A and
`9.007/12.499 ms` Stage 6B median/p95 in this replay boundary. Exact
first-action deduplication took `8.359/13.405 ms` and
`9.358/13.042 ms`; width 256 took `21.988/57.336 ms` and
`37.621/55.826 ms`.

**Decision:** do not promote either first-action mode. They changed soft
ties, showed no hard improvement on the sampled roots, and do not solve beam
optimality. The modes remain default-off experiment hooks; the live
quantized behavior is unchanged.

## C++ Decision

A full local-planner C++ rewrite is **not justified at this gate**.

Observed reasons:

- packing the correct branch recurrence in NumPy reduced equivalent-root
  certificate median time by about half without changing the hard labels on
  any sampled root;
- the correct pending-aware all-action certificate is now around
  `3.1..3.9 ms` median and `6.4..7.9 ms` p95 on these retained workloads;
- the default width-24 local plan remains about `8..9 ms` median and
  `12.5..12.6 ms` p95 in offline row replay;
- wider or separately partitioned beam work is much slower without observed
  hard benefit; and
- Python/C++ parity would only accelerate a wrong recurrence if the explicit
  root, clock, or hazard semantics were still wrong.

This is not a claim that native work will never help. If an explicit-root
Windows shadow still misses the issue deadline, the next defensible native
boundary is compact raw pool decode, trajectory/laser projection, packing,
and all-action certification in one call, checked against the independent
Python scalar oracle. Porting Python objects or the unproved beam wholesale is
not the next gate.

## Reproduction

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/local_pipeline_certificate_audit.py \
  artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_122014.jsonl \
  artifacts/runtime_reports/lunatic_route2_stage6b_unattended_20260726_011639.jsonl \
  --samples-per-trace 128 \
  --output artifacts/benchmarks/local_pipeline_certificate_20260726.json

PYTHONPATH=scripts python3 \
  scripts/analysis/local_beam_stability_audit.py \
  artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_122014.jsonl \
  artifacts/runtime_reports/lunatic_route2_stage6b_unattended_20260726_011639.jsonl \
  --samples-per-trace 96 --wide-beam 256 --partition-roots 12 \
  --output artifacts/benchmarks/local_beam_stability_20260726.json
```

Wall timings will vary; semantic counts should not.

## Promotion And Next Gate

Accepted in this checkpoint:

- the independent scalar local-pipeline oracle;
- packed all-action finite-lease certification;
- the per-position bullet/laser relevance correction;
- reusable TH08 trace-to-hazard replay helpers;
- explicit local-root trace telemetry; and
- retained replay/differential artifacts.

Not promoted:

- supplying the pending-aware root to the live selector or fresh-hazard
  recertifier;
- either first-action beam mode;
- a wider beam;
- a C++ local-planner rewrite; or
- any manager-frame neutralization.

The next local micro-control gate is:

1. run Linux and Windows quick suites for this source checkpoint;
2. collect an explicitly scoped shadow trace whose rows directly retain the
   local root, with no pending-aware action authority;
3. replay direct roots and compare them with estimator reconstruction;
4. measure Windows issue-thread observe/decode/project/certify/issue timing
   and stale-result frequency, not only isolated lookup time;
5. retain every inconsistent root and every scalar/packed mismatch;
6. only after those pass, update `STRATEGY.md` before allowing the explicit
   root to affect live local fallback.

Even a promoted local repair will not by itself solve the route: retained
physical hits still predominantly follow global viable-set exhaustion.
