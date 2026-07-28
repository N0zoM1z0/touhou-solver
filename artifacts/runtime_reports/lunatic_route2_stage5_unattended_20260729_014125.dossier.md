# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_014125

## Scope And Integrity

- Valid practice scope: `2..41804` (11805 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[1481, 11138, 12721, 13823, 14468, 24813, 29980, 35419, 36449, 40039, 40717]`.
- Hard no-Bomb verification: **PASS** across 11805 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1481-T1`. It occurred during a nonspell phase at player (376.000, 406.528), with 68 bullets and 0 lasers. The projectile model reported pipeline clearance 40.776.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 4 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 8
- `fast_mode`: 7
- `pool_density_over_1000`: 4
- `action_lag_over_model`: 3
- `corridor_deadline_miss`: 1
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1481 | nonspell | (376.000, 406.528) | `right_fast` | 68/0 | 40.776/40.776 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 11138 | nonspell | (312.394, 380.380) | `down_left_fast` | 871/0 | -9.831/-9.831 | 0f/2f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12721 | nonspell | (21.816, 432.000) | `right_fast` | 300/0 | -2.040/-2.040 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13823 | nonspell | (300.408, 402.680) | `up_left` | 476/0 | -4.408/-16.915 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14468 | nonspell | (376.000, 16.000) | `down_fast` | 495/0 | -5.640/-5.640 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24813 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 431.713) | `stay` | 1123/0 | -2.447/-2.447 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29980 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (81.541, 432.000) | `down_right` | 1010/0 | -5.271/-5.271 | 14f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35419 | nonspell | (376.000, 432.000) | `left_fast` | 447/0 | -2.533/-2.533 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36449 | 111 懶惰「生神停止(マインドストッパー)」 | (189.798, 200.314) | `left_fast` | 349/0 | -1.924/-1.924 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40039 | 115 散符「真実の月(インビジブルフルムーン)」 | (64.569, 432.000) | `down_right_fast` | 1237/0 | -1.548/-10.329 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40717 | 115 散符「真実の月(インビジブルフルムーン)」 | (233.800, 432.000) | `right` | 1182/0 | -0.626/-0.847 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 6 | 7789 | 7684 | 5443 | 0 | 2219 | 915 | 117.933 | 0.182 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 914 | 902 | 571 | 0 | 331 | 172 | 105.736 | 0.307 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 729 | 721 | 507 | 0 | 205 | 139 | 83.815 | 0.331 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1210 | 1202 | 581 | 0 | 610 | 178 | 86.471 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1163 | 1122 | 769 | 0 | 352 | 135 | 60.163 | 0.343 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.047 ms median and 22.428 ms p95.
- The full enemy sensor produced 6166 snapshots; capture read time was `{'median': 6.647799978964031, 'p95': 27.09550003055483, 'max': 217.79749996494502}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 41.0}` frames, and 7 phase-counter discontinuities were excluded; 11253 decisions retained at least one robust-union body (maximum 42); 4707 decisions contained latent contact-disabled geometry (maximum 41), and 6140 contained bounded inactive-slot memory (maximum 41). 195 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.999969482421875, 'p95': 4.707550048828125, 'max': 8.948239300702069}` / `{'median': 1.0, 'p95': 4.534283638000488, 'max': 4.710229396820068}` / `{'median': 3.814697265625e-06, 'p95': 3.7000043392181396, 'max': 7.600003004074097}`.
- The issue-time enemy guard retained 11805 observations, detected 2540 during-plan geometry changes, recertified 2540 decisions, and overrode 59 actions. Read/recertificate timing was `{'median': 1.756999990902841, 'p95': 3.250099951401353, 'max': 28.17389997653663}` / `{'median': 2.7350500458851457, 'p95': 6.492499960586429, 'max': 46.106599969789386}` ms; 4687 issue captures contained latent bodies (maximum 41), and 6137 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2481/2540 planned actions, relaxed 10 fresh/global empty intersections, inherited 13 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8403 observations (8372 contact enabled, 31 anticipatory, 0 errors). 8403 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8403}`.
- The terminal-threat heuristic covered 11805 decisions with horizon counts `{'0': 20, '10': 11501, '32': 284}`; it reported 1 collision and 61 sub-safety-clearance warnings, and relaxed 43 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1236, '3': 8818, '4': 1007, '5': 343, '6': 401}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 3939, '3': 6629, '4': 1188, '6': 49}`.
- Adaptive delay supports were `{'1,2,3,4,5': 1, '1,2,3,4,5,6': 224, '2,3': 1200, '2,3,4': 4470, '2,3,4,5': 2898, '2,3,4,5,6': 2214, '3,4,5': 23, '3,4,5,6': 774, '4,5,6': 1}`; 130 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 70/402.
- Robust viability supplied 11631 available policy queries (0 had new delay support outside the cached policy), constrained 3717 decisions, and exposed 7871 empty queried action sets. Recovery guidance was available/selected on 1071/503 empty-kernel queries; distant-kernel guidance was available/selected on 6126/5863. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.9961239727768, 'p95': 362.7450895601483, 'max': 534.7447989461889}`, and `{'median': 0.0, 'p95': 22.186676502227783, 'max': 44.7473087310791}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1800, '1': 1549, '2': 1211, '3': 1421, '4': 1347, '5': 1447, '6': 1435, '7': 1421}`.
- Global-horizon/local-prefix cross-tab covered 7973 decisions: 2 had a winning global state but unsafe selected prefix, 5283 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 12 selected actions were outside the reported winning set. 2197 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1539 unique policies with solve-time statistics `{'median': 100.50359996967018, 'p95': 326.30410010460764, 'max': 2197.9411999927834}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1808.0}`. Policy status counts were `{'queryable': 11626, 'expired': 92, 'pending_future_epoch': 15}`; 102 robust-mode decisions had no query.
- Of 6234 unambiguous output transitions, 5555 (0.891) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 1, 'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[0, 2, 4, 0, 7, 8, 23, 4, 7, 0, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.350 during the 60 frames preceding a hit versus 0.194 outside those windows.
- Mean selected control-reserve deficit was 8.091 during the 60 frames preceding a hit versus 4.204 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.044 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 38.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
