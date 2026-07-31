# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_130103

## Scope And Integrity

- Valid practice scope: `1..45746` (12340 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 16, at `[1827, 4112, 10335, 11859, 12424, 12988, 13444, 13863, 22291, 23147, 30698, 31264, 32199, 39016, 43334, 43643]`.
- Hard no-Bomb verification: **PASS** across 12340 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Experiment-Specific Result

- **Observed:** the repaired delivery gate submitted 1,926 global solves,
  completed 1,925, retained 1,915 unique policies, and supplied 12,156
  available viability queries. All 12,340 scale-horizon gates passed and all
  12,253 publications remained diagnostic shadow with no action authority.
- **Observed:** 6,635/12,156 queries were losing/empty. Every one of the 16
  hits followed global-kernel exhaustion; 13 hit rows had a playfield-boundary
  contributor. The first attempt's last winning query was frame 1,471, 356
  frames before the first hit.
- **Observed:** early kill saw 170 low-HP targets and requested 63 unfocused
  peers. It causally selected 39 fresh-safe preferences; 26 were already in a
  losing shadow-global state, and only nine were also inside a winning
  shadow-global action set. One frame where least-bad fallback happened to
  equal the requested peer was a telemetry false positive, not preference
  authority.
- **Interpretation:** rolling publication is fixed, but the narrow rule is
  only locally fresh-safe. This run does not falsify early killing; it shows
  that the intended strategy must act before exhaustion and inside an exact
  global viable set.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1827-T1`. It occurred during a nonspell phase at player (8.000, 432.000), with 320 bullets and 0 lasers. The projectile model reported pipeline clearance -1.484.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 7 |

Contributing factors:

- `fast_mode`: 14
- `playfield_boundary`: 13
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1827 | nonspell | (8.000, 432.000) | `down_fast` | 320/0 | -1.484/-20.380 | 48f/54f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4112 | nonspell | (323.474, 432.000) | `left_fast` | 940/0 | -1.263/-2.061 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10335 | nonspell | (376.000, 405.100) | `up_fast` | 534/0 | -10.405/-17.291 | 7f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11859 | 57 夢境「二重大結界」 | (11.121, 428.000) | `up_right_fast` | 607/0 | 1.037/0.131 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12424 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_fast` | 610/0 | -1.442/-1.442 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12988 | 57 夢境「二重大結界」 | (10.828, 414.313) | `up_right_fast` | 594/0 | 1.167/0.273 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13444 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 573/0 | -1.779/-1.779 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13863 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 612/0 | -2.758/-2.758 | 0f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22291 | nonspell | (16.921, 432.000) | `up_fast` | 693/0 | -2.870/-2.870 | 4f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23147 | nonspell | (371.121, 432.000) | `down_left` | 840/0 | -1.797/-1.797 | 4f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30698 | 65 神技「八方龍殺陣」 | (252.198, 432.000) | `down_left_fast` | 1105/0 | -2.096/-2.096 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31264 | 65 神技「八方龍殺陣」 | (373.172, 429.172) | `up_left_fast` | 1286/0 | -14.129/-14.129 | 4f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32199 | 65 神技「八方龍殺陣」 | (219.475, 402.668) | `up_left` | 1305/0 | 0.057/-2.435 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39016 | 69 回霊「夢想封印　侘」 | (10.828, 403.573) | `up_right_fast` | 560/0 | -2.917/-2.917 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43334 | 73 大結界「博麗弾幕結界」 | (218.253, 383.700) | `down_fast` | 1000/0 | -1.944/-1.944 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43643 | 73 大結界「博麗弾幕結界」 | (150.716, 386.579) | `right_fast` | 796/0 | -1.908/-1.908 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 7264 | 7132 | 4059 | 0 | 0 | 1061 | 113.366 | 0.240 |
| 57 夢境「二重大結界」 | 5 | 1085 | 1078 | 171 | 0 | 0 | 175 | 181.820 | 0.245 |
| 61 | 0 | 1019 | 1010 | 450 | 0 | 0 | 163 | 123.593 | 0.176 |
| 65 神技「八方龍殺陣」 | 3 | 915 | 903 | 760 | 0 | 0 | 162 | 62.702 | 0.433 |
| 69 回霊「夢想封印　侘」 | 1 | 1079 | 1071 | 666 | 0 | 0 | 177 | 86.592 | 0.166 |
| 73 大結界「博麗弾幕結界」 | 2 | 978 | 962 | 529 | 0 | 0 | 177 | 121.334 | 0.042 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.984 ms median and 28.498 ms p95.
- The full enemy sensor produced 6468 snapshots; capture read time was `{'median': 6.118849996710196, 'p95': 28.38509999855887, 'max': 62.542400002712384}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 11814 decisions retained at least one robust-union body (maximum 58); 6711 decisions contained latent contact-disabled geometry (maximum 58), and 5068 contained bounded inactive-slot memory (maximum 31). 323 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.3237075805664062, 'p95': 4.271037578582764, 'max': 18.627884312679893}` / `{'median': 2.4881532192230225, 'p95': 3.975149393081665, 'max': 15.466669082641602}` / `{'median': 0.015274584293365479, 'p95': 2.8531696796417236, 'max': 17.628777011444694}`.
- The issue-time enemy guard retained 12340 observations, detected 4632 during-plan geometry changes, recertified 4632 decisions, and overrode 99 actions. Read/recertificate timing was `{'median': 1.711699995212257, 'p95': 3.319399998872541, 'max': 18.15340000030119}` / `{'median': 2.3986500018509105, 'p95': 3.983599992352538, 'max': 12.521499986178242}` ms; 6713 issue captures contained latent bodies (maximum 58), and 5059 contained dormant bodies (maximum 34). Fresh/global transactions preserved 4533/4632 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9456 observations (9417 contact enabled, 39 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4091, '0x00597600': 5365}`.
- The terminal-threat heuristic covered 12340 decisions with horizon counts `{'0': 526, '10': 11814}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 451, '3': 8595, '4': 3136, '5': 158}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 26, '2': 465, '3': 10748, '4': 1101}`.
- Adaptive delay supports were `{'1,2': 276, '1,2,3': 70, '1,2,3,4': 147, '1,2,3,4,5,6': 60, '2,3': 213, '2,3,4': 2371, '2,3,4,5': 6140, '2,3,4,5,6': 2415, '3,4': 34, '3,4,5': 256, '3,4,5,6': 358}`; 119 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 28/172.
- Robust viability supplied 12156 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 6635 empty queried action sets. Recovery guidance was available/selected on 1724/0 empty-kernel queries; distant-kernel guidance was available/selected on 4011/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1947, '1': 1683, '2': 1219, '3': 1464, '4': 1413, '5': 1439, '6': 1464, '7': 1527}`.
- Global-horizon/local-prefix cross-tab covered 6136 decisions: 2 had a winning global state but unsafe selected prefix, 2775 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 501 selected actions were outside the reported winning set. 3974 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1915 unique policies with solve-time statistics `{'median': 116.4889000065159, 'p95': 324.02850000653416, 'max': 399.91639999789186}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1801.0}`. Policy status counts were `{'pending_future_epoch': 79, 'queryable': 12159, 'expired': 15}`; 97 robust-mode decisions had no query.
- Of 7080 unambiguous output transitions, 6781 (0.958) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 16}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[54, 7, 12, 4, 6, 8, 5, 3, 6, 15, 4, 14, 11, 10, 12, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.559 during the 60 frames preceding a hit versus 0.214 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 9.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
