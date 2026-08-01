# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_093817

## Scope And Integrity

- Valid practice scope: `2..42827` (10941 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 20, at `[1873, 2265, 2698, 3815, 4251, 12300, 12851, 13370, 13799, 14284, 23218, 24299, 28961, 30212, 30854, 35498, 36153, 37661, 41842, 42518]`.
- Hard no-Bomb verification: **PASS** across 10941 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1873-T1`. It occurred during a nonspell phase at player (376.000, 349.137), with 221 bullets and 0 lasers. The projectile model reported pipeline clearance 3.302.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 6 |

Contributing factors:

- `playfield_boundary`: 12
- `fast_mode`: 11
- `action_lag_over_model`: 8
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1873 | nonspell | (376.000, 349.137) | `right` | 221/0 | 3.302/3.302 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2265 | nonspell | (10.121, 421.663) | `down_left` | 453/0 | -1.708/-1.708 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 2698 | nonspell | (75.256, 432.000) | `stay` | 689/0 | 4.354/4.354 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3815 | nonspell | (352.483, 420.262) | `down_left_fast` | 503/0 | 6.330/0.611 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 4251 | nonspell | (118.717, 416.000) | `stay` | 287/0 | 39.537/39.537 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12300 | nonspell | (372.394, 432.000) | `stay` | 312/0 | -0.855/-0.855 | 0f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12851 | nonspell | (356.717, 411.546) | `left_fast` | 349/0 | -0.783/-17.257 | 0f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13370 | nonspell | (188.283, 380.835) | `stay` | 214/0 | 29.425/29.425 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 13799 | nonspell | (170.270, 399.029) | `stay` | 407/0 | -2.196/-2.196 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 14284 | nonspell | (118.846, 422.343) | `up_right_fast` | 517/0 | 0.048/0.048 | 0f/34f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23218 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 994/0 | -2.479/-2.479 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24299 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 1033/0 | -2.239/-2.239 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 28961 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (21.011, 418.989) | `up_left_fast` | 975/0 | -5.946/-5.946 | 21f/28f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30212 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (210.084, 432.000) | `up_fast` | 1023/0 | -4.682/-5.469 | 5f/158f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30854 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (147.703, 430.374) | `up_right` | 1016/0 | -6.651/-6.927 | 13f/44f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35498 | nonspell | (376.000, 432.000) | `down_left_fast` | 443/0 | -3.373/-3.373 | 3f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36153 | nonspell | (376.000, 388.016) | `down_fast` | 447/0 | 0.047/0.047 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 37661 | 111 懶惰「生神停止(マインドストッパー)」 | (181.555, 123.420) | `right` | 402/0 | 0.360/-1.028 | 0f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41842 | 115 散符「真実の月(インビジブルフルムーン)」 | (364.000, 432.000) | `up_fast` | 966/0 | -1.688/-1.692 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42518 | 115 散符「真実の月(インビジブルフルムーン)」 | (247.277, 432.000) | `up_left_fast` | 1095/0 | -1.250/-1.250 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 12 | 7220 | 38 | 36 | 0 | 11 | 7 | 1400.351 | 0.368 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 810 | 331 | 253 | 0 | 0 | 13 | 76.396 | 0.333 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 844 | 759 | 629 | 0 | 0 | 173 | 76.733 | 0.327 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1013 | 1007 | 597 | 0 | 0 | 177 | 66.596 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1054 | 1047 | 697 | 0 | 0 | 184 | 65.765 | 0.450 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 18.031 ms median and 32.381 ms p95.
- The full enemy sensor produced 5903 snapshots; capture read time was `{'median': 5.209399998420849, 'p95': 26.20690001640469, 'max': 775.4244999960065}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 97.0}` frames, and 7 phase-counter discontinuities were excluded; 10227 decisions retained at least one robust-union body (maximum 51); 7748 decisions contained latent contact-disabled geometry (maximum 51), and 3837 contained bounded inactive-slot memory (maximum 36). 413 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.0, 'p95': 4.6930389404296875, 'max': 8.12791546908292}` / `{'median': 1.0, 'p95': 4.581644058227539, 'max': 11.760002136230469}` / `{'median': 4.371138828673793e-08, 'p95': 3.349987030029297, 'max': 11.760002136230469}`.
- The issue-time enemy guard retained 10941 observations, detected 3086 during-plan geometry changes, recertified 3086 decisions, and overrode 51 actions. Read/recertificate timing was `{'median': 1.492699986556545, 'p95': 2.9196999967098236, 'max': 282.04590000677854}` / `{'median': 3.039349991013296, 'p95': 7.585100014694035, 'max': 316.5490999817848}` ms; 7725 issue captures contained latent bodies (maximum 51), and 3840 contained dormant bodies (maximum 36). Fresh/global transactions preserved 3035/3086 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8341 observations (8315 contact enabled, 26 anticipatory, 0 errors). 8341 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8341}`.
- The terminal-threat heuristic covered 10941 decisions with horizon counts `{'0': 605, '10': 10336}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 689, '3': 6699, '4': 2507, '5': 639, '6': 407}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 267, '2': 1899, '3': 6964, '4': 1427, '5': 334, '6': 50}`.
- Adaptive delay supports were `{'1': 16, '1,2': 63, '1,2,3': 425, '1,2,3,4': 354, '1,2,3,4,5': 66, '1,2,3,4,5,6': 141, '2,3': 909, '2,3,4': 3057, '2,3,4,5': 2450, '2,3,4,5,6': 2050, '3,4': 49, '3,4,5': 419, '3,4,5,6': 829, '4,5,6': 98, '5,6': 3, '6': 12}`; 239 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 19/153.
- Robust viability supplied 3182 available policy queries (0 had new delay support outside the cached policy), constrained 11 decisions, and exposed 2212 empty queried action sets. Recovery guidance was available/selected on 244/0 empty-kernel queries; distant-kernel guidance was available/selected on 1294/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 526, '1': 437, '2': 378, '3': 322, '4': 354, '5': 395, '6': 395, '7': 375}`.
- Global-horizon/local-prefix cross-tab covered 1178 decisions: 1 had a winning global state but unsafe selected prefix, 591 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 14 selected actions were outside the reported winning set. 1244 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 554 unique policies with solve-time statistics `{'median': 69.26905000000261, 'p95': 168.39249999611638, 'max': 5288.5001999966335}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 171.0}`. Policy status counts were `{'queryable': 3168, 'expired': 472, 'pending_future_epoch': 165}`; 623 robust-mode decisions had no query.
- Of 5360 unambiguous output transitions, 5036 (0.940) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 7, 'late_collision_after_positive_causal_margin': 2, 'unresolved_planner_failure': 4, 'robust_action_set_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[0, 0, 0, 0, 0, 11, 6, 0, 0, 34, 7, 7, 28, 158, 44, 10, 5, 7, 3, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.465 during the 60 frames preceding a hit versus 0.329 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Retained Provenance

- Source worktree based on `b47a495`; candidate adds bounded three-action
  terminal reuse, hard local/issue authority, and remaining-horizon causal
  held/no-write certification. Observed-body early kill remained enabled.
- Raw trace SHA-256:
  `e233455a70e0065302f7e89382eff3b31a9ef372e2c2b5f2c5c7878947fb5c3d`.
- Verified replay slot 15 SHA-256:
  `794d9f29f080013ba4a1e0cdbef88d6c37e88ec2b9f16be6d40a57e2a3a55498`;
  Route 2, Lunatic, Stage 5, empty Bomb list.
- Supervisor exited normally; game, controller, replay helper, and injected
  keys were fully cleaned up.
