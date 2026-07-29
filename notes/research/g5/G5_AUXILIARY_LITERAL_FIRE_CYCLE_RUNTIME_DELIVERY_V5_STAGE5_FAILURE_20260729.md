# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V5 Stage-5 Failure

Date: 2026-07-29

Status: exact physical semantics accepted; separate synchronous publication
and survival rejected

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V5_CONTRACT_20260729.md`

## Result

**Observed:** fresh run
`lunatic_route2_stage5_unattended_20260729_120859`, from code checkpoint
`35d3163`, completed Lunatic Route-2 Stage-5 practice over frames `2..42725`
with 11,746 decisions. Executable identity, route, difficulty, Sakuya/Remilia
team, no-life-decrement patch, foreground ownership, hard no-Bomb input,
accepted artifacts, route completion, and exact cleanup passed.

The run took 14 hits:

- nonspell: 5;
- spell 103: 1;
- spell 107: 5;
- spell 111: 2; and
- spell 115: 1.

This is outside the fixed single-run maximum of ten and contributes no pass
to the two-consecutive-run requirement.

## Exact Semantic Evidence

**Observed:** all 154 schema-v8 batches were successful. The strict
independent decoder reconstructed and replayed all 4,238 requests with zero
unknown:

- target 69: 1,046;
- target 72: 1,073;
- target 73: 2,119;
- six valid empty prefixes;
- cache misses: 46;
- persistent hits: 1,970;
- request-local hits: 2,222; and
- evictions: zero.

The one pre-game preparation completed in `0.095 ms`. Runtime program
identity, observation epoch, exact source rows, status proof, raw replay
bundle, recurrence commitments, cache behavior, and the independent byte
oracle all agree. V5 therefore has physical trace-only semantic authority for
this selected workload. It has no geometry, future-birth, planner, damage,
source-life, transform, or action authority.

## Representation And Timing Failure

Physical schema-v8 line p50/p95/p99/max was
`13935.5/14899.1/14982.47/15453` bytes. It passes the unchanged 24,576-byte
maximum with substantial margin.

All values below are milliseconds:

| Component | p50 | p95 | p99 | max | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| event derive | 0.245 | 0.382 | 0.491 | 0.676 | pass |
| replay compact | 0.336 | 0.507 | 0.593 | 8.452 | **fail** |
| previous auxiliary emit | 1.029 | 1.412 | 1.568 | 1.596 | **fail** |
| transaction total | 1.669 | 2.462 | 3.126 | 9.470 | pass |

Decision cadence p50/p95/p99 was `2/4/5` frames versus baseline `2/4/4`;
the fixed p95 regression gate passes. The existing decision-record trace p95
was `4.434 ms` versus baseline `4.340 ms`; this does not erase the independent
auxiliary publication failure.

**Observed diagnostic:** previous auxiliary emit correlates `0.730` with
preceding line size and `0.717` with record count. Rows with at most 15
records had median `0.101 ms` emit, while groups with 16 or more records had
median approximately `1.03 ms`. The controller emits the auxiliary row as a
separate trace write, then emits and flushes the ordinary decision record
later in the same loop.

**Inferred:** V5 removed repeated keys correctly, but a roughly 14--15 KiB
separate row still crosses the effective buffered-write boundary of this
Windows/UNC path. Reducing V4's roughly 25 KiB rows to V5's roughly 15 KiB
rows therefore did not remove the fixed extra write cost. This is a delivery
composition failure, not a recurrence or column-schema failure.

The `8.452 ms` compact outlier occurred on a ten-record, 8,221-byte row and
does not correlate with row size. Scheduling, allocation, or collection is a
hypothesis only; one tail sample does not establish a cause.

As a representation diagnostic only, canonical V5 JSON from the largest row
compressed with zlib level 6 fits in an approximately 7.4 KiB base64
envelope. This is not an accepted design or physical timing result.

## Survival Evidence

**Observed:** 13 of 14 contacts follow global viability-kernel exhaustion;
one lacks a pre-hit alive decision. Bottom-eight-pixel occupancy is `0.448`
inside the 60-frame pre-hit windows versus `0.210` outside. Mean selected
control-reserve deficit is `11.001` versus `4.463`. The first hit is a
nonspell contact at frame 1,914, but spells 107 and 111 contribute seven
further hits. Survival therefore cannot be repaired by declaring this solely
a nonspell targeting problem.

**Hypothesized, separate experiment:** within the unchanged viable and
issue-safe set, ordinary-enemy phases may benefit from killing verified
damageable sources before dense emissions. When precise micro-dodging is not
required, releasing Focus/Shift may widen Sakuya's shot coverage. Native shot
mode, damage, kill/despawn reason, exposure, Power, and survival margin must
be measured first; dense geometry or reduced margin must return to focused
control. This hypothesis gains no authority from V5.

## Invalid Assumptions And Correction

Invalid assumptions:

1. keeping a separate auxiliary row below 16 KiB would make its synchronous
   UNC publication fit the 1.000-ms p95 gate;
2. further column-level field removal was necessarily the next delivery
   bottleneck; and
3. survival would remain inside ten hits while an action-neutral trace
   observer was enabled.

Before implementation, fix a separately reviewed coalesced-publication
contract that:

- preserves schema-v8 V5 as the exact decoded inner evidence;
- canonicalizes, compresses, hashes, sizes, and independently decodes the
  complete inner row, rejecting truncation, substitution, and identity/order
  mismatches;
- carries the envelope in the already-required decision publication for the
  same physical iteration instead of issuing a second OS write;
- measures pack time and the combined decision publication/cadence boundary;
- forbids deferred, stale, cross-frame, cross-epoch, or partial evidence from
  being interpreted as current;
- changes no sensing, recurrence, planner, action, no-Bomb, or survival
  behavior; and
- reuses the independent V5 byte oracle after exact inner reconstruction.

Do not loosen V5's historical gate or rename a removed metric as a pass.
Coalescing is a changed delivery contract and needs its own falsifiers,
isolated Linux/Windows replay, and fresh physical gate.

Survival remains a separate correction after delivery is side-effect free.
Handoff still requires two consecutive corrected Stage-5 runs with at most
ten hits, independent Stage-3 evidence, cross-stage checks, and a full
Lunatic Route-2 run.

## Retained Evidence

- raw trace SHA-256:
  `4f2505ff84753e07fa5bf827dc71f770c8190e4aafc01e536819d87b23d50088`;
- strict failed report:
  `artifacts/viability_audit/g5_auxiliary_ecl_event_runtime_delivery_v5_stage5_20260729_120859.json`,
  SHA-256
  `1c3018c4831063bd645594856c7e5dc3384e4fd50a54f35b06f5da764d922d6e`;
- compact dossier:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260729_120859.dossier.json`,
  SHA-256
  `d09f91a40a76e32e4c610d18dc92e487af5fdfb2e6187245ff84e5ea097fda16`;
- normalized session:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260729_120859.session.json`,
  SHA-256
  `26a9f37fcda3026eed8f3f870e9a9a7d51a320ec88352a2b1e0bf2f1240adb66`;
- run review:
  `notes/runs/lunatic_route2_stage5_unattended_20260729_120859.md`,
  SHA-256
  `11080c1bfb03bb59d39d3847eeb741095597d6f88539a8f501f7256a1ee15ad8`.
