# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260728_020910

## Scope And Integrity

- Valid practice scope: `2..45659` (15260 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 14, at `[1099, 1720, 4247, 9001, 10939, 11913, 13365, 13933, 19017, 22350, 22978, 32272, 39520, 40376]`.
- Hard no-Bomb verification: **PASS** across 15260 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1099-T1`. It occurred during a nonspell phase at player (368.000, 385.721), with 349 bullets and 0 lasers. The projectile model reported pipeline clearance 0.029.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 4 |
| `observed_enemy_body_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 12
- `playfield_boundary`: 9
- `corridor_deadline_miss`: 5
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1099 | nonspell | (368.000, 385.721) | `up_fast` | 349/0 | 0.029/-2.665 | 0f/2f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1720 | nonspell | (10.930, 432.000) | `up_left_fast` | 531/0 | -1.688/-1.688 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4247 | nonspell | (372.000, 414.214) | `left_fast` | 940/0 | -3.332/-3.332 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9001 | nonspell | (185.826, 426.343) | `up_fast` | 165/0 | -9.167/-23.374 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10939 | nonspell | (8.000, 432.000) | `down` | 226/0 | -17.682/-17.682 | 9f/15f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11913 | 57 夢境「二重大結界」 | (13.657, 422.343) | `up_right_fast` | 574/0 | 0.785/-0.909 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13365 | 57 夢境「二重大結界」 | (8.000, 397.096) | `right_fast` | 599/0 | -1.787/-1.787 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13933 | 57 夢境「二重大結界」 | (312.153, 364.287) | `left_fast` | 594/0 | -1.267/-1.267 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 19017 | 61 散霊「夢想封印　寂」 | (271.852, 432.000) | `right_fast` | 336/0 | -11.194/-20.830 | 9f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22350 | nonspell | (376.000, 432.000) | `up_right_fast` | 582/0 | -2.841/-2.841 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22978 | nonspell | (16.000, 408.506) | `down_right` | 581/0 | -1.574/-1.691 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32272 | 65 神技「八方龍殺陣」 | (197.218, 432.000) | `left_fast` | 1198/0 | -2.329/-2.329 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39520 | 69 回霊「夢想封印　侘」 | (8.000, 402.456) | `up_right_fast` | 679/0 | -2.911/-2.911 | 0f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40376 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `up_left_fast` | 720/0 | -1.867/-1.867 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 8889 | 8754 | 4402 | 0 | 4281 | 1074 | 100.958 | 0.140 |
| 57 夢境「二重大結界」 | 3 | 1319 | 1311 | 314 | 0 | 965 | 182 | 157.800 | 0.276 |
| 61 散霊「夢想封印　寂」 | 1 | 1367 | 1357 | 398 | 0 | 944 | 167 | 110.684 | 0.186 |
| 65 神技「八方龍殺陣」 | 1 | 1245 | 1231 | 1085 | 0 | 144 | 163 | 55.267 | 0.459 |
| 69 回霊「夢想封印　侘」 | 2 | 1360 | 1352 | 655 | 0 | 675 | 179 | 83.045 | 0.107 |
| 73 | 0 | 1080 | 1065 | 612 | 0 | 435 | 178 | 103.533 | 0.060 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 2 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 10.083 ms median and 17.879 ms p95.
- The full enemy sensor produced 7462 snapshots; capture read time was `{'median': 6.208150007296354, 'p95': 22.534199990332127, 'max': 43.52120001567528}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 9.0}` frames, and 7 phase-counter discontinuities were excluded; 14854 decisions retained at least one robust-union body (maximum 52); 2973 decisions contained latent contact-disabled geometry (maximum 52), and 7900 contained bounded inactive-slot memory (maximum 41). 278 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.8002376556396484, 'p95': 4.242828369140625, 'max': 6.311902046203613}` / `{'median': 2.779624581336975, 'p95': 3.8987717628479004, 'max': 5.72991418838501}` / `{'median': 0.4355354309082031, 'p95': 2.2666587829589844, 'max': 8.5999755859375}`.
- The issue-time enemy guard retained 15260 observations, detected 2700 during-plan geometry changes, recertified 2700 decisions, and overrode 41 actions. Read/recertificate timing was `{'median': 1.717800012556836, 'p95': 3.3996999845840037, 'max': 12.68250000430271}` / `{'median': 1.8582000047899783, 'p95': 3.4872000105679035, 'max': 12.424000015016645}` ms; 2971 issue captures contained latent bodies (maximum 52), and 7905 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2659/2700 planned actions, relaxed 1 fresh/global empty intersections, inherited 17 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11869 observations (11822 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5183, '0x0058CE60': 6686}`.
- The terminal-threat heuristic covered 15260 decisions with horizon counts `{'0': 75, '10': 14217, '32': 968}`; it reported 20 collision and 180 sub-safety-clearance warnings, and relaxed 160 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4519, '3': 10019, '4': 722}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 11559, '3': 3342, '4': 346}`.
- Adaptive delay supports were `{'1,2': 77, '1,2,3': 145, '1,2,3,4': 195, '1,2,3,4,5': 43, '2': 24, '2,3': 2046, '2,3,4': 8976, '2,3,4,5': 3036, '2,3,4,5,6': 717, '3,4': 1}`; 67 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 52/406.
- Robust viability supplied 15070 available policy queries (0 had new delay support outside the cached policy), constrained 7444 decisions, and exposed 7466 empty queried action sets. Recovery guidance was available/selected on 1944/884 empty-kernel queries; distant-kernel guidance was available/selected on 4393/4252. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 7.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 113.13708498984761, 'p95': 318.7977415227404, 'max': 524.8390229394153}`, and `{'median': 0.0, 'p95': 15.223301887512207, 'max': 44.32268404960632}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2326, '1': 1886, '2': 1581, '3': 1864, '4': 1777, '5': 1864, '6': 1877, '7': 1895}`.
- Global-horizon/local-prefix cross-tab covered 10567 decisions: 5 had a winning global state but unsafe selected prefix, 4996 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 104 selected actions were outside the reported winning set. 2270 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1943 unique policies with solve-time statistics `{'median': 103.42930001206696, 'p95': 306.2064999830909, 'max': 390.16529999207705}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1805.0}`. Policy status counts were `{'pending_future_epoch': 78, 'queryable': 15071, 'expired': 30}`; 109 robust-mode decisions had no query.
- Of 7861 unambiguous output transitions, 7307 (0.930) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 13, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[2, 3, 6, 0, 15, 5, 5, 0, 13, 4, 4, 6, 10, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.363 during the 60 frames preceding a hit versus 0.165 outside those windows.
- Mean selected control-reserve deficit was 6.153 during the 60 frames preceding a hit versus 3.351 outside those windows.
- Soft recovery was selected on 0.053 of alive decisions in the 60-frame pre-hit windows versus 0.062 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 11.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
