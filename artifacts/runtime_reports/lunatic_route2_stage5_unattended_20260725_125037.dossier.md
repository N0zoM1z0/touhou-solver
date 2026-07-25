# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260725_125037

## Scope And Integrity

- Valid practice scope: `2..43338` (7921 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[2134, 11711, 12446, 13027, 14114, 21301, 23357, 25278, 29487, 29919, 30319, 31173, 31588, 35615, 36024, 38665, 39759, 40935]`.
- Hard no-Bomb verification: **PASS** across 7921 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2134-T1`. It occurred during a nonspell phase at player (31.029, 432.000), with 745 bullets and 0 lasers. The projectile model reported pipeline clearance -0.063.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 15
- `fast_mode`: 12
- `pool_density_over_1000`: 4
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2134 | nonspell | (31.029, 432.000) | `up_right` | 745/0 | -0.063/-1.016 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11711 | nonspell | (376.000, 432.000) | `down` | 883/0 | -1.376/-28.052 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12446 | nonspell | (94.374, 395.352) | `up_fast` | 271/0 | 3.724/0.347 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13027 | nonspell | (369.495, 432.000) | `down_left_fast` | 275/0 | -3.283/-3.283 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14114 | nonspell | (14.900, 432.000) | `up_right_fast` | 381/0 | -6.923/-28.183 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21301 | nonspell | (376.000, 432.000) | `stay` | 479/0 | -2.337/-2.337 | 5f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23357 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 994/0 | -2.205/-2.205 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25278 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 1112/0 | -2.834/-2.834 | 5f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29487 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (196.199, 432.000) | `up_left_fast` | 885/0 | -8.171/-8.171 | 6f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29919 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (263.519, 432.000) | `up_right_fast` | 994/0 | -6.337/-10.728 | 10f/39f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30319 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (221.270, 432.000) | `left_fast` | 1004/0 | -8.083/-9.611 | 95f/95f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31173 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (49.544, 432.000) | `down_left_fast` | 992/0 | -6.036/-7.305 | 30f/48f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31588 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (178.034, 432.000) | `right_fast` | 1013/0 | -8.708/-8.708 | 34f/48f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35615 | nonspell | (186.047, 432.000) | `stay` | 503/0 | -3.254/-3.254 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36024 | nonspell | (376.000, 426.447) | `left_fast` | 447/0 | -3.564/-3.564 | 0f/43f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38665 | 111 懶惰「生神停止(マインドストッパー)」 | (183.908, 24.132) | `right` | 365/0 | -2.186/-2.433 | 8f/30f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39759 | 111 懶惰「生神停止(マインドストッパー)」 | (189.815, 165.366) | `up` | 383/0 | -2.881/-3.128 | 4f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40935 | 115 散符「真実の月(インビジブルフルムーン)」 | (125.817, 432.000) | `down_left_fast` | 1083/0 | -2.662/-18.451 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 5146 | 5044 | 3443 | 0 | 1588 | 921 | 156.571 | 0.203 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 646 | 633 | 335 | 0 | 295 | 155 | 125.880 | 0.344 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 5 | 616 | 605 | 457 | 0 | 138 | 172 | 98.086 | 0.205 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 750 | 739 | 393 | 0 | 339 | 158 | 102.959 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 763 | 751 | 500 | 0 | 240 | 168 | 62.586 | 0.438 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 6.000 frames p95. The local plan took 22.710 ms median and 42.741 ms p95.
- The full enemy sensor produced 6107 snapshots; capture read time was `{'median': 22.028099978342652, 'p95': 43.53089997312054, 'max': 79.29480000166222}`, snapshot age was `{'median': 6.0, 'p95': 10.0, 'max': 14.0}` frames, and 6 phase-counter discontinuities were excluded; 7376 decisions retained at least one robust-union body (maximum 41); 3031 decisions contained latent contact-disabled geometry (maximum 40), and 3899 contained bounded inactive-slot memory (maximum 40). 237 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.569153149922689, 'max': 3.61322021484375}` / `{'median': 0.0, 'p95': 2.4513022899627686, 'max': 3.1112680435180664}` / `{'median': 0.0, 'p95': 3.2526878118515015, 'max': 6.198965152104696}`.
- The issue-time enemy guard retained 7921 observations, detected 2161 during-plan geometry changes, recertified 2161 decisions, and overrode 915 actions. Read/recertificate timing was `{'median': 1.865199999883771, 'p95': 3.9727999828755856, 'max': 18.838099960703403}` / `{'median': 9.306499967351556, 'p95': 18.069099984131753, 'max': 33.4469000226818}` ms; 3006 issue captures contained latent bodies (maximum 40), and 3900 contained dormant bodies (maximum 40).
- The synchronous spell-owner guard retained 5665 observations (5646 contact enabled, 19 anticipatory, 0 errors). 5665 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 5665}`.
- The terminal-threat heuristic covered 7921 decisions with horizon counts `{'0': 48, '10': 7707, '32': 166}`; it reported 1 collision and 43 sub-safety-clearance warnings, and relaxed 44 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 54, '3': 207, '4': 2620, '5': 3927, '6': 1113}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 58, '3': 502, '4': 4296, '5': 2079, '6': 986}`.
- Adaptive delay supports were `{'2,3': 54, '2,3,4,5': 215, '2,3,4,5,6': 532, '3,4,5': 267, '3,4,5,6': 5839, '4,5,6': 578, '5,6': 436}`; 1166 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 166/300.
- Robust viability supplied 7772 available policy queries (0 had new delay support outside the cached policy), constrained 2600 decisions, and exposed 5128 empty queried action sets. Recovery guidance was available/selected on 753/416 empty-kernel queries; distant-kernel guidance was available/selected on 3866/3617. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 131.93938001976514, 'p95': 354.17509793885847, 'max': 452.831094338717}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1202, '1': 1100, '2': 984, '3': 903, '4': 936, '5': 902, '6': 903, '7': 842}`.
- Global-horizon/local-prefix cross-tab covered 4470 decisions: 0 had a winning global state but unsafe selected prefix, 2924 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 8 selected actions were outside the reported winning set. 1705 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1574 unique policies with solve-time statistics `{'median': 114.91389997536317, 'p95': 425.220699980855, 'max': 537.2277999995276}` and first-observed ages `{'median': 4.0, 'p95': 10.0, 'max': 1798.0}`. Policy status counts were `{'pending_future_epoch': 38, 'queryable': 7771, 'expired': 15}`; 52 robust-mode decisions had no query.
- Of 4509 unambiguous output transitions, 3670 (0.814) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[5, 4, 5, 8, 17, 8, 7, 11, 19, 39, 95, 48, 48, 8, 43, 30, 4, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.552 during the 60 frames preceding a hit versus 0.207 outside those windows.
- Mean selected control-reserve deficit was 14.194 during the 60 frames preceding a hit versus 5.133 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.053 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
