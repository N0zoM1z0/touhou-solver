# G3 Stationary Partial-Survival Capsule Gate

Date: 2026-07-27

Status: retained offline Gate 3 complete for the historical 17-action capsule
model; native extraction, complete-mask roots, delivery, and physical
consumption remain open

## Bottom Line

**Observed:** exact retained Lunatic Stage-4A and Stage-6B roots that the
historical Boolean policy marked empty contain three different outcomes under
the completed stationary witness class:

1. a stationary policy can be feasible for the complete 32-frame horizon;
2. no stationary policy completes the horizon, but one guarantees a positive
   12- or 17-frame prefix; or
3. the stationary class guarantees no positive prefix from an already unsafe
   current root.

These outcomes falsify any rule that equates Boolean empty, stationary-policy
exhaustion, and unrestricted exact losing. Every root below therefore retains
`unrestricted_status = unresolved`; no
`POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS` was manufactured from the old
Boolean label.

## Immutable Scope

- Workloads:
  `lunatic_route2_stage4a_unattended_20260726_103856` and
  `lunatic_route2_stage6b_unattended_20260726_011639`.
- Horizon: 32 physical frames.
- Recursive decision-cadence support: `(4, 5, 6)`.
- Root actions: all 17 historical TH08 movement actions in capsule order.
- Continuations: all 17 singleton stationary candidates. The best completed
  continuation is retained independently for every root action.
- Delay support, nominal delay, observed action, pending command/support,
  player position, lattice cell, source/query frame, and clearance volume
  come from each exact retained trace/capsule pair.
- Authority: offline restricted attainable lower witness only.

This is exact for the declared historical movement-action model. It is not an
exact complete-mask issue model: equal-velocity Shot/Focus transitions from
CE-0134 are absent from these older capsules. Stage-4A `103856` also used the
rejected repeated-counter manager-frame guard. Its finite capsule remains
replayable, but the physical run is contaminated for causal survival claims.

## Observed Results

All six selected roots were trace-Boolean-empty and every portfolio completed
all 17 root actions.

| Workload | Mode | Decision/query/source | Capsule | Label | Best root actions |
| --- | --- | --- | --- | --- | --- |
| Stage 4A | full finite feasibility | `761/757/756` | `policy_738_756.npz` | `32`, margin `0x1.eaf6800000000p-3` | `stay`, `down`, `down_fast` |
| Stage 4A | partial on unresolved | `1835/1832/1832` | `policy_1816_1832.npz` | `17`, margin `-0x1.73e0e00000000p-1` | `stay`, `right`, `down`, `down_right`, `down_fast` |
| Stage 4A | no positive stationary witness | `902/900/899` | `policy_883_899.npz` | `0`, margin `-0x1.0e25a00000000p-2` | all root actions tie |
| Stage 6B | full finite feasibility | `410/408/390` | `policy_368_390.npz` | `32`, margin `0x1.7e38d83ad07c0p-2` | eight tied actions retained in JSON |
| Stage 6B | partial on unresolved | `439/437/436` | `policy_414_436.npz` | `12`, margin `-0x1.0418000000000p-2` | `stay`, `down`, `down_fast` |
| Stage 6B | no positive stationary witness | `450/448/436` | `policy_414_436.npz` | `0`, margin `-0x1.a84a000000000p+1` | all root actions tie |

The negative bottleneck on a positive partial label is expected: the first
component counts the guaranteed collision-free prefix, while the bottleneck
also retains the terminal failing branch margin.

Stage-4A supplied 691 exact roots, of which 297 were eligible
Boolean-empty 32-frame roots; the first five contained all three modes.
Stage-6B supplied 14,279 exact roots, of which 6,618 were eligible; its first
five also contained all three modes. This deterministic first-occurrence
selection is a compact counterexample corpus, not a frequency estimate.

## Independent Checks

- Every retained worst branch replays its root/stationary policy choice,
  observation links, nested recurrence labels, and policy/witness digests.
- Selected witness labels were queried again through the native belief
  workspace. All guaranteed-frame values matched. All margin differences
  were below the repository's existing `1e-5` scalar/native tolerance; the
  exact maximum per root is retained in the JSON.
- Two complete regenerations were byte-identical.
- Report content digest:
  `82ae76afac47f556d01865cba4a0342db6c5b1da44e537e6af7b7a9f28d881f8`.
- Report-file SHA-256:
  `3e9c9beb562f33aa66ce2af92c8ef16a7147ab828b1d990612ca4f6edad794ff`.
- Linux and Windows quick suites pass `723/723` in `9.182/13.135 s`;
  Windows retains three platform skips.

Retained report:
`artifacts/viability_audit/g3_stationary_partial_witness_capsule_audit_20260727.json`.

## Interpretation And Remaining Gates

**Inferred:** the full-horizon roots are concrete finite-model witnesses that
the older Boolean-empty label can discard attainable stationary policies.
The partial roots show that exact restricted lower values remain useful when
unrestricted proof is absent. The zero-prefix roots show why candidate
exhaustion cannot be promoted to unrestricted losing.

None of these inferences proves physical survival. The capsules omit unknown
future births/transforms, use the historical movement-only action alphabet,
and retain no fresh alternate-action issue certificate. The scalar audit also
has no publication deadline or live consumer.

The next G3 gates remain:

1. add native worst-branch/policy-witness extraction without changing the
   checked-in 46-symbol ABI until separately reviewed;
2. move future experiments to exact complete-mask augmented roots;
3. measure cancellable background delivery and Windows contention; and
4. require exact-version lookup plus a fresh issue-time hard intersection
   before considering any shadow publication, then separate physical trials.

## Reproduction

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/g3_partial_survival_capsule_audit.py \
  artifacts/viability_audit/g3_stationary_partial_witness_capsule_audit_20260727.json

PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_g3_partial_survival_capsule_report.py'
```
