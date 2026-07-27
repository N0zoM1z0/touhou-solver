# G5 Physical Complete-Mask Capsule Gate

Date: 2026-07-28

Status: same-session physical join complete; finite-model witness retained;
CE-0141 physical recheck passed; future-event coverage and action authority
remain open

## Physical Workload

The supervised diagnostic run
`lunatic_route2_stage4a_unattended_20260728_005108` used the shipped TH08
executable, required SHA-256, no-life-decrement patch, Sakuya/Remilia Route 2,
Lunatic Stage 4A, native runtime sensing, native local kernels, hard no-Bomb,
and opted-in `--viability-audit` capsule retention.

**Observed:** the run completed frames `2..44411`, 14,804 decisions,
`route_complete`, compact dossier materialization, supervisor exit zero, and
identity-scoped cleanup. All 14,804 issued masks kept Bomb bit `0x02` clear.
It retained 1,884 capsule files totaling 79,053,832 bytes locally.

The run took ten hits at:

```text
4259, 11726, 12357, 13405, 19017,
21215, 22063, 31161, 31625, 42033
```

The canonical fresh-attempt contact at frame 4,259 was a modeled
committed-prefix bullet collision after the global viability kernel had
already become empty. Every later contact also followed kernel exhaustion.
The dossier classifies six observed bullet overlaps, three modeled committed
prefix collisions, and one observed enemy-body overlap.

This was a diagnostic I/O workload, not a survival A/B. The ten-hit count
must not be compared causally with the preceding seven-hit Stage-4A run.

## Exact Same-Session Join

The retained raw trace is 455,037,221 bytes with SHA-256:

```text
93037d9febe609accd44eb150150088c29610443783a4434328478409fee41b0
```

The v2 compact audit is:

```text
artifacts/viability_audit/g5_complete_mask_stage4a_20260728.json
report digest:
a67bac60da036813a330483a30d9d93bea90097414926518985f4d9504efc6fe
file SHA-256:
aa76c5424788bd6628fdd275580256153024be9934864f0b392481f0663dfd8b
```

Two complete generations were byte-identical.

**Observed join counts:**

| Measurement | Count |
| --- | ---: |
| accepted canonical root/capsule joins | 12,986 |
| rejected root-frame joins | 1,613 |
| missing named capsules | 0 |
| accepted Boolean-empty roots eligible for a 32-frame audit | 5,896 |
| exact roots retained in the compact report | 1 |

The accepted and rejected rows total all 14,599 available robust-policy
queries reported by the physical dossier.

## Retained Exact Witness

The first accepted Boolean-empty root is decision/query/source
`600/599/598`, joined to `policy_582_598.npz`.

- active mask = held desired mask = issued mask = `0x05`;
- no pending command and empty remaining-delay support;
- all 36 canonical no-Bomb root actions completed;
- continuation = exact held token `th08_mask_05`;
- recursive decision cadence support = `(4, 5, 6)`;
- exact finite-model guarantee = 32 frames;
- bottleneck margin =
  `0x1.f87dd20000000p+3`;
- all 36 deterministic worst paths replay;
- scalar/native label mismatches = 0; and
- maximum native margin error = exactly zero.

**Observed finite-model counterexample extension:** the physical trace's
coarse Boolean policy labeled this root empty, while the complete-mask exact
stationary class retained a full 32-frame witness. This extends CE-0140 from
historical movement-only capsules to a same-session physical complete-mask
root. It still does not prove unrestricted feasibility.

**Observed authority boundary:** hazard coverage is `UNKNOWN` beginning at
frame 600, the first transition after the query root. The report therefore
retains:

```text
physical_model_status = model_unknown
finite_model_authority = exact restricted stationary lower witness
physical_action_authority = none
```

The witness cannot rank or issue live input.

## CE-0141 Root-Frame Mismatch

The audit rejected 1,613 of 14,599 available-query rows because the serialized
coverage root did not equal the canonical query root. The first minimal
physical witness is decision frame 267:

```text
canonical manager frame = 266
canonical query frame   = 267
coverage root frame     = 266
coverage unknown from   = 267
```

Adjacent matching rows and source inspection show that the trace-only shadow
builder used `manager_frame` for coverage while the canonical observation and
policy query used `query_frame`. A sensor read that advanced during capture
therefore serialized two different physical roots under one record.

Checkpoint `d5866c4` corrects the builder to root coverage at
`query_frame`. It also changes the compact audit from thousands of duplicate
failure strings to deterministic counts plus bounded first/last samples.
This changes no planner result, cadence, input, publication, or action
authority.

**Observed regression:** focused shadow/join/pickup tests pass `3/3`, `6/6`,
and `4/4`. After adding the retained-artifact contract, complete
Linux/Windows quick suites pass `733/733` in `8.581/14.794 s`, with three
existing Windows skips.

**Physical verification complete:** post-fix Lunatic Stage-4A run
`20260728_020910` accepted all 15,069 canonical root/capsule joins with zero
coverage/query-root mismatches, validation failures, or missing capsules.
CE-0141's trace construction defect is physically fixed; see
`notes/G5_CE0141_PHYSICAL_RECHECK_20260728.md`. This does not change the
first-successor `UNKNOWN` coverage or action authority.

## Diagnostic Performance

Compared with the most recent complete Stage-4A no-audit workload
`20260727_220330`:

| Metric | no audit | this audit run |
| --- | ---: | ---: |
| local plan median ms | 9.975 | 9.981 |
| local plan p95 ms | 18.025 | 17.662 |
| rolling solve median ms | 108.792 | 106.845 |
| rolling solve p95 ms | 310.049 | 303.617 |
| decision cadence median/p95 frames | 2/3 | 2/3 |

**Inferred:** no material median or p95 contention is visible from capsule
retention in these two workloads. They differ in RNG, deaths, phase length,
geometry, and resource history, so this is not a controlled performance or
survival result. Cancellable native delivery still needs the unchanged
Windows direct-root contention gate.

## Next Gate

1. Keep future-event coverage `UNKNOWN`; model event classes individually,
   beginning with bullet birth.
2. Retain the passing CE-0141 physical report beside the pre-fix failure.
3. Measure earlier immutable completion age without adding a public consumer.
4. Only consider complete-only exact-version shadow lookup after delivery
   passes, with a fresh issue-time local hard intersection and lookup-miss
   fallback.
