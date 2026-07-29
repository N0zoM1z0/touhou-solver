# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_161313

## Scope And Integrity

- Valid practice scope: `2..45288` (12639 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[2524, 4207, 7437, 10989, 11297, 12280, 12949, 13623, 23994, 25063, 30911, 31335, 32174, 32597, 33211, 37793, 38688, 41047]`.
- Hard no-Bomb verification: **PASS** across 12639 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2524-T1`. It occurred during a nonspell phase at player (371.121, 82.873), with 267 bullets and 0 lasers. The projectile model reported pipeline clearance -1.808.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 5 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 14
- `playfield_boundary`: 12
- `pool_density_over_1000`: 5
- `corridor_deadline_miss`: 2
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2524 | nonspell | (371.121, 82.873) | `down_left` | 267/0 | -1.808/-2.293 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4207 | nonspell | (376.000, 432.000) | `up_fast` | 534/0 | -3.371/-3.371 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7437 | nonspell | (66.190, 407.798) | `right_fast` | 427/0 | -15.521/-15.521 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10989 | nonspell | (119.854, 418.343) | `up_right_fast` | 887/0 | 10.250/-16.825 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11297 | nonspell | (42.236, 363.813) | `up_fast` | 698/0 | -18.027/-18.027 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12280 | nonspell | (361.858, 432.000) | `down_fast` | 386/0 | -1.663/-1.663 | 6f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12949 | nonspell | (370.343, 355.978) | `up_left_fast` | 348/0 | -3.723/-3.723 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13623 | nonspell | (8.000, 382.978) | `up_right_fast` | 390/0 | 0.233/-6.434 | 9f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23994 | 103 幻波「赤眼催眠(マインドブローイング)」 | (263.157, 432.000) | `stay` | 1084/0 | -2.395/-2.395 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25063 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1041/0 | -1.052/-1.136 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30911 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (142.779, 432.000) | `up_right_fast` | 1003/0 | -5.015/-6.868 | 0f/35f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31335 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (240.662, 432.000) | `down_right_fast` | 1017/0 | -9.289/-9.289 | 44f/57f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32174 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (144.542, 432.000) | `up_left` | 1017/0 | -5.154/-5.154 | 11f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32597 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (219.337, 432.000) | `left_fast` | 987/0 | -5.421/-6.398 | 8f/108f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33211 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 432.000) | `up_left_fast` | 999/0 | -7.244/-7.244 | 4f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37793 | nonspell | (8.000, 416.540) | `down_right` | 454/0 | -3.242/-3.242 | 3f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38688 | nonspell | (8.000, 428.643) | `right_fast` | 439/0 | -1.854/-1.854 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41047 | 111 懶惰「生神停止(マインドストッパー)」 | (165.908, 198.415) | `up_right_fast` | 348/0 | -0.655/-3.711 | 5f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 8288 | 8161 | 5983 | 0 | 2163 | 1105 | 145.339 | 0.198 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 941 | 934 | 499 | 0 | 434 | 170 | 120.529 | 0.286 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 5 | 1149 | 1138 | 936 | 0 | 196 | 238 | 88.109 | 0.329 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1151 | 1143 | 583 | 0 | 550 | 177 | 99.944 | 0.000 |
| 115 | 0 | 1110 | 1099 | 839 | 0 | 241 | 178 | 62.948 | 0.558 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.798 ms median and 24.375 ms p95.
- The full enemy sensor produced 6788 snapshots; capture read time was `{'median': 5.763449997175485, 'p95': 26.864900020882487, 'max': 57.05370008945465}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 14.0}` frames, and 6 phase-counter discontinuities were excluded; 12089 decisions retained at least one robust-union body (maximum 42); 4875 decisions contained latent contact-disabled geometry (maximum 39), and 6234 contained bounded inactive-slot memory (maximum 40). 219 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 3.54534912109375, 'max': 4.707550048828125}` / `{'median': 0.0, 'p95': 3.323399782180786, 'max': 4.707549571990967}` / `{'median': 0.0, 'p95': 1.0000076293945312, 'max': 4.419419288635254}`.
- The issue-time enemy guard retained 12639 observations, detected 2587 during-plan geometry changes, recertified 2587 decisions, and overrode 67 actions. Read/recertificate timing was `{'median': 1.8630999838933349, 'p95': 3.6841999972239137, 'max': 18.35710008163005}` / `{'median': 3.64940008148551, 'p95': 7.199899991974235, 'max': 21.397599950432777}` ms; 4838 issue captures contained latent bodies (maximum 39), and 6240 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2520/2587 planned actions, relaxed 6 fresh/global empty intersections, inherited 12 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9288 observations (9261 contact enabled, 27 anticipatory, 0 errors). 9288 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9288}`.
- The terminal-threat heuristic covered 12639 decisions with horizon counts `{'0': 71, '10': 12417, '32': 151}`; it reported 1 collision and 40 sub-safety-clearance warnings, and relaxed 51 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 311, '3': 9531, '4': 1627, '5': 1170}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1418, '3': 9581, '4': 1536, '5': 104}`.
- Adaptive delay supports were `{'1,2,3': 210, '1,2,3,4': 8, '2,3': 449, '2,3,4': 2270, '2,3,4,5': 4546, '2,3,4,5,6': 3774, '3,4': 1, '3,4,5': 56, '3,4,5,6': 1324, '4,5,6': 1}`; 354 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 36/418.
- Robust viability supplied 12475 available policy queries (0 had new delay support outside the cached policy), constrained 3584 decisions, and exposed 8840 empty queried action sets. Recovery guidance was available/selected on 1049/462 empty-kernel queries; distant-kernel guidance was available/selected on 7064/6671. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 144.0, 'p95': 336.0, 'max': 515.2397500193478}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1939, '1': 1706, '2': 1296, '3': 1432, '4': 1503, '5': 1449, '6': 1587, '7': 1563}`.
- Global-horizon/local-prefix cross-tab covered 8060 decisions: 2 had a winning global state but unsafe selected prefix, 5566 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 22 selected actions were outside the reported winning set. 2029 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1868 unique policies with solve-time statistics `{'median': 108.35895000491291, 'p95': 342.160000000149, 'max': 473.92289992421865}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1811.0}`. Policy status counts were `{'pending_future_epoch': 71, 'queryable': 12477, 'expired': 35}`; 108 robust-mode decisions had no query.
- Of 6894 unambiguous output transitions, 5992 (0.869) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[8, 6, 0, 0, 0, 11, 8, 13, 7, 4, 35, 57, 21, 108, 21, 14, 5, 13]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.397 during the 60 frames preceding a hit versus 0.226 outside those windows.
- Mean selected control-reserve deficit was 12.809 during the 60 frames preceding a hit versus 5.073 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.037 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 23.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
