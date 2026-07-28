# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_110438

## Scope And Integrity

- Valid practice scope: `2..42763` (13525 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 14, at `[2189, 4221, 8883, 9533, 9959, 11488, 13337, 13845, 21517, 33483, 36211, 36901, 37425, 40372]`.
- Hard no-Bomb verification: **PASS** across 13525 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2189-T1`. It occurred during a nonspell phase at player (376.000, 426.343), with 355 bullets and 0 lasers. The projectile model reported pipeline clearance 4.497.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 5 |
| `observed_enemy_body_overlap` | 2 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 11
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2189 | nonspell | (376.000, 426.343) | `up_fast` | 355/0 | 4.497/-2.518 | 2f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4221 | nonspell | (361.373, 432.000) | `left` | 960/0 | -1.651/-1.651 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8883 | nonspell | (77.025, 428.747) | `right_fast` | 508/0 | 1.102/-3.314 | 2f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9533 | nonspell | (248.234, 426.343) | `up_left_fast` | 125/0 | 1.543/-7.813 | 5f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9959 | nonspell | (187.728, 432.000) | `up_right_fast` | 189/0 | -13.891/-13.891 | 7f/11f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11488 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 530/0 | -1.456/-1.456 | 0f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13337 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 595/0 | -0.901/-0.901 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13845 | 57 夢境「二重大結界」 | (372.747, 432.000) | `up_fast` | 579/0 | -1.827/-1.827 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21517 | nonspell | (8.000, 378.700) | `stay` | 629/0 | -1.358/-4.299 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33483 | nonspell | (13.657, 344.255) | `up_fast` | 117/0 | 17.837/6.394 | 0f/0f | `observed_enemy_body_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 36211 | 69 回霊「夢想封印　侘」 | (11.253, 432.000) | `right` | 576/0 | -0.081/-1.101 | 5f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36901 | 69 回霊「夢想封印　侘」 | (17.826, 432.000) | `up_right_fast` | 612/0 | -2.057/-2.057 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37425 | 69 回霊「夢想封印　侘」 | (250.611, 432.000) | `right_fast` | 661/0 | -2.848/-2.848 | 0f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40372 | 73 大結界「博麗弾幕結界」 | (225.089, 399.300) | `right_fast` | 988/0 | -0.122/-0.122 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 7910 | 7762 | 3701 | 0 | 4012 | 957 | 99.221 | 0.134 |
| 57 夢境「二重大結界」 | 3 | 1296 | 1288 | 363 | 0 | 906 | 182 | 161.599 | 0.373 |
| 61 | 0 | 1224 | 1216 | 324 | 0 | 881 | 159 | 109.899 | 0.141 |
| 65 | 0 | 634 | 624 | 465 | 0 | 159 | 99 | 62.621 | 0.308 |
| 69 回霊「夢想封印　侘」 | 3 | 1359 | 1350 | 641 | 0 | 704 | 183 | 84.590 | 0.095 |
| 73 大結界「博麗弾幕結界」 | 1 | 1102 | 1091 | 573 | 0 | 504 | 179 | 103.573 | 0.036 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.887 ms median and 18.116 ms p95.
- The full enemy sensor produced 6657 snapshots; capture read time was `{'median': 5.859100027009845, 'p95': 23.264600022230297, 'max': 54.157699982170016}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 7 phase-counter discontinuities were excluded; 13136 decisions retained at least one robust-union body (maximum 41); 2926 decisions contained latent contact-disabled geometry (maximum 41), and 6553 contained bounded inactive-slot memory (maximum 37). 222 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.9432120439079075, 'p95': 4.072113037109375, 'max': 4.49725341796875}` / `{'median': 2.9357370138168335, 'p95': 3.778592109680176, 'max': 4.3424072265625}` / `{'median': 0.11607016954157087, 'p95': 1.293428897857666, 'max': 3.720184326171875}`.
- The issue-time enemy guard retained 13525 observations, detected 2626 during-plan geometry changes, recertified 2626 decisions, and overrode 38 actions. Read/recertificate timing was `{'median': 1.7510000034235418, 'p95': 3.475499979685992, 'max': 13.809800031594932}` / `{'median': 1.865199999883771, 'p95': 3.656200016848743, 'max': 15.359100012574345}` ms; 2927 issue captures contained latent bodies (maximum 41), and 6541 contained dormant bodies (maximum 37). Fresh/global transactions preserved 2588/2626 planned actions, relaxed 8 fresh/global empty intersections, inherited 16 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10178 observations (10133 contact enabled, 45 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4636, '0x0059C9D0': 5542}`.
- The terminal-threat heuristic covered 13525 decisions with horizon counts `{'0': 73, '10': 12653, '32': 799}`; it reported 21 collision and 152 sub-safety-clearance warnings, and relaxed 98 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1352, '3': 11157, '4': 1016}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 7726, '3': 5265, '4': 534}`.
- Adaptive delay supports were `{'1,2,3': 191, '1,2,3,4': 199, '1,2,3,4,5': 13, '1,2,3,4,5,6': 55, '2,3': 2474, '2,3,4': 6925, '2,3,4,5': 2815, '2,3,4,5,6': 772, '3,4': 13, '3,4,5': 68}`; 49 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 22/201.
- Robust viability supplied 13331 available policy queries (0 had new delay support outside the cached policy), constrained 7166 decisions, and exposed 6067 empty queried action sets. Recovery guidance was available/selected on 1813/893 empty-kernel queries; distant-kernel guidance was available/selected on 3594/3481. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 14.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 96.0, 'p95': 294.15642097360376, 'max': 461.5105632593906}`, and `{'median': 0.0, 'p95': 15.423193216323853, 'max': 36.15270471572876}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2119, '1': 1664, '2': 1375, '3': 1626, '4': 1582, '5': 1665, '6': 1671, '7': 1629}`.
- Global-horizon/local-prefix cross-tab covered 9028 decisions: 0 had a winning global state but unsafe selected prefix, 3954 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 56 selected actions were outside the reported winning set. 2144 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1759 unique policies with solve-time statistics `{'median': 106.16769996704534, 'p95': 321.3380000088364, 'max': 430.04790000850335}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1802.0}`. Policy status counts were `{'pending_future_epoch': 69, 'queryable': 13331, 'expired': 10}`; 79 robust-mode decisions had no query.
- Of 6786 unambiguous output transitions, 6403 (0.944) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[10, 5, 10, 7, 11, 2, 7, 7, 9, 0, 7, 5, 3, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.353 during the 60 frames preceding a hit versus 0.147 outside those windows.
- Mean selected control-reserve deficit was 8.631 during the 60 frames preceding a hit versus 3.316 outside those windows.
- Soft recovery was selected on 0.093 of alive decisions in the 60-frame pre-hit windows versus 0.066 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## ECL VM-Local Projection Gate

- **Observed:** all 5,615 callback rows contain a valid 104-byte v1 local
  projection. Layout/range/tag parity and coverage metadata have zero
  violations.
- **Observed:** coverage remains 1,490 complete / 4,125 unknown. No
  incomplete prefix is lowered; no instruction-limit or repeated-state stop
  reappears.
- **Observed:** variable `10036` takes 12/33/13 distinct values during
  spells 57/61/65. This physically confirms that the old seven-field
  snapshot aliased distinct loop-counter histories.
- **Observed:** actual projection record p50/p95 is 238/249 bytes.
- **Authority:** trace-only. No local interpreter, callback completion,
  survival, or physical action authority is added.

## ECL And B4 Performance Gate

- Per-spell ECL read/lookahead p50/p95/max for spells 57/61/65/69/73 is
  `0.0849/0.1989/1.1745`, `0.0959/0.2098/2.0083`,
  `0.0969/0.1960/1.6761`, `0.1111/0.2185/2.6370`, and
  `0.0906/0.2177/2.4713 ms`.
- Native birth-observer p50/p95/p99/p99.9/max is
  `0.1038/0.2059/0.3486/0.5555/1.2276 ms`. Fixed B4 p95 fails; p99/max pass.
  There was no completed GC and no dominant over-budget segment.
- The prior run used different physical paths. These totals do not isolate
  projection cost; matched-path attribution remains required.
- Raw/projection/control/birth SHA-256 values are
  `aa86ba40f2b2141ff5212ffca7374d27d73ca6680c21cad22e09a9520ad1cf9e`,
  `cbfb75db83988e48b1c5305124a31383218c426df3bcde18e9a6d3f34ed09b3e`,
  `aedbe0fece76b7cf4bfe8722babd1093694e07b4e6ee4da33547157bd97166ba`,
  and `91c25c9594e8a5711bb5cf742765bd5b46741436ef55ae96d204dde198d0cccb`.
