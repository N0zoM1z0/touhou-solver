# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_233856

## Scope And Integrity

- Valid practice scope: `2..45800` (11186 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 24, at `[845, 1310, 1950, 2575, 3212, 4161, 9806, 10327, 12687, 13566, 18448, 22470, 23181, 27411, 29278, 35274, 35872, 38392, 38910, 39492, 43328, 43646, 44482, 44853]`.
- Hard no-Bomb verification: **PASS** across 11186 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F845-T1`. It occurred during a nonspell phase at player (376.000, 400.089), with 260 bullets and 0 lasers. The projectile model reported pipeline clearance 3.163.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 13 |
| `observed_bullet_overlap` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 3 |

Contributing factors:

- `fast_mode`: 18
- `playfield_boundary`: 17
- `corridor_deadline_miss`: 11
- `pool_density_over_1000`: 4
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 845 | nonspell | (376.000, 400.089) | `up_fast` | 260/0 | 3.163/-1.294 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 1310 | nonspell | (368.717, 432.000) | `up_left` | 111/0 | 5.179/3.487 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 1950 | nonspell | (11.253, 432.000) | `up` | 117/0 | -2.513/-14.945 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2575 | nonspell | (329.640, 415.029) | `up_left_fast` | 585/0 | 0.957/-1.468 | 3f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3212 | nonspell | (241.495, 432.000) | `left_fast` | 219/0 | 15.379/10.517 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4161 | nonspell | (311.240, 432.000) | `left_fast` | 1113/0 | -3.442/-3.442 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9806 | nonspell | (336.165, 424.000) | `up_fast` | 745/0 | -3.307/-8.265 | 7f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10327 | nonspell | (8.000, 425.495) | `up_left` | 568/0 | -0.976/-1.513 | 4f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12687 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 585/0 | -1.799/-1.799 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13566 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 578/0 | -1.780/-1.780 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18448 | nonspell | (8.000, 421.495) | `up_fast` | 153/0 | -11.621/-12.620 | 26f/32f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22470 | nonspell | (31.476, 432.000) | `up_left_fast` | 816/0 | -2.037/-2.037 | 4f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23181 | nonspell | (8.000, 432.000) | `down` | 693/0 | -1.664/-1.664 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27411 | nonspell | (32.215, 423.063) | `up_left_fast` | 88/0 | -1.626/-1.626 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 29278 | nonspell | (8.000, 428.000) | `up_right_fast` | 188/0 | 0.239/0.239 | 0f/4f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 35274 | nonspell | (376.000, 419.900) | `down_fast` | 88/0 | -3.117/-3.117 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35872 | nonspell | (16.622, 424.000) | `up_fast` | 142/0 | -6.152/-6.269 | 6f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38392 | 69 回霊「夢想封印　侘」 | (376.000, 421.290) | `up_left_fast` | 399/0 | -1.693/-1.693 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38910 | 69 回霊「夢想封印　侘」 | (8.000, 432.000) | `down` | 536/0 | -3.127/-3.127 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39492 | 69 回霊「夢想封印　侘」 | (376.000, 366.630) | `right` | 728/0 | -1.702/-1.746 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 43328 | 73 大結界「博麗弾幕結界」 | (211.731, 383.281) | `left_fast` | 1000/0 | -1.501/-1.501 | 0f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43646 | 73 大結界「博麗弾幕結界」 | (157.247, 370.095) | `up_fast` | 836/0 | 1.598/-1.459 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44482 | 73 大結界「博麗弾幕結界」 | (195.567, 384.823) | `left_fast` | 1308/0 | -1.475/-1.475 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44853 | 73 大結界「博麗弾幕結界」 | (195.472, 428.879) | `right_fast` | 1100/0 | -1.949/-1.949 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 15 | 5884 | 3859 | 2023 | 0 | 196 | 293 | 277.831 | 0.211 |
| 57 夢境「二重大結界」 | 2 | 1143 | 1051 | 387 | 0 | 0 | 123 | 167.921 | 0.357 |
| 61 | 0 | 1052 | 999 | 368 | 0 | 0 | 111 | 125.765 | 0.145 |
| 65 | 0 | 862 | 621 | 522 | 0 | 0 | 71 | 62.667 | 0.428 |
| 69 回霊「夢想封印　侘」 | 3 | 1178 | 709 | 373 | 0 | 0 | 62 | 83.289 | 0.143 |
| 73 大結界「博麗弾幕結界」 | 4 | 1067 | 1003 | 468 | 0 | 0 | 137 | 116.825 | 0.038 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 17.588 ms median and 45.247 ms p95.
- The full enemy sensor produced 6619 snapshots; capture read time was `{'median': 6.823200004873797, 'p95': 53.95709999720566, 'max': 103.6891999974614}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 62.0}` frames, and 7 phase-counter discontinuities were excluded; 10777 decisions retained at least one robust-union body (maximum 59); 6321 decisions contained latent contact-disabled geometry (maximum 59), and 4184 contained bounded inactive-slot memory (maximum 32). 382 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.935699462890625, 'p95': 4.2120513916015625, 'max': 12.196329752604166}` / `{'median': 2.93159818649292, 'p95': 3.922955274581909, 'max': 149.7094268798828}` / `{'median': 0.4601259231567383, 'p95': 1.3118184208869934, 'max': 149.7094268798828}`.
- The issue-time enemy guard retained 11186 observations, detected 4508 during-plan geometry changes, recertified 4508 decisions, and overrode 99 actions. Read/recertificate timing was `{'median': 1.532150010461919, 'p95': 3.114899998763576, 'max': 34.70930000185035}` / `{'median': 3.131400007987395, 'p95': 10.540899995248765, 'max': 45.31519999727607}` ms; 6307 issue captures contained latent bodies (maximum 59), and 4194 contained dormant bodies (maximum 32). Fresh/global transactions preserved 4409/4508 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8792 observations (8757 contact enabled, 35 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 8792}`.
- The terminal-threat heuristic covered 11186 decisions with horizon counts `{'0': 252, '10': 10934}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 182, '3': 3406, '4': 3677, '5': 3279, '6': 642}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 128, '2': 73, '3': 5024, '4': 4406, '5': 1523, '6': 32}`.
- Adaptive delay supports were `{'1,2': 60, '1,2,3': 75, '1,2,3,4': 75, '1,2,3,4,5': 3, '1,2,3,4,5,6': 151, '2,3': 35, '2,3,4': 650, '2,3,4,5': 2687, '2,3,4,5,6': 5996, '3,4': 105, '3,4,5': 370, '3,4,5,6': 878, '4,5': 4, '4,5,6': 96, '5,6': 1}`; 157 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 32/104.
- Robust viability supplied 8242 available policy queries (0 had new delay support outside the cached policy), constrained 196 decisions, and exposed 4141 empty queried action sets. Recovery guidance was available/selected on 1191/0 empty-kernel queries; distant-kernel guidance was available/selected on 2404/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1164, '1': 1154, '2': 932, '3': 967, '4': 1025, '5': 984, '6': 1006, '7': 1010}`.
- Global-horizon/local-prefix cross-tab covered 3770 decisions: 3 had a winning global state but unsafe selected prefix, 1626 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 299 selected actions were outside the reported winning set. 2480 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 797 unique policies with solve-time statistics `{'median': 148.10140000190586, 'p95': 1574.7365999995964, 'max': 2872.696000005817}` and first-observed ages `{'median': 3.0, 'p95': 16.0, 'max': 1913.0}`. Policy status counts were `{'pending_future_epoch': 265, 'queryable': 8172, 'expired': 2466}`; 2661 robust-mode decisions had no query.
- Of 6568 unambiguous output transitions, 6403 (0.975) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 6, 'unresolved_planner_failure': 1, 'global_viability_kernel_exhausted_before_hit': 16, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 21 hit windows with a positive warning lead; those leads were `[4, 0, 5, 14, 0, 11, 18, 8, 3, 5, 32, 18, 10, 0, 4, 5, 13, 4, 9, 10, 6, 10, 11, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.361 during the 60 frames preceding a hit versus 0.215 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact Ordinary Authority Activation

- **Observed:** 119/1,914 future-source projections completed. Stable-capture
  read time over 1,208 samples was 2.309 ms minimum, 7.728 ms median, 35.086
  ms p95, and 77.392 ms maximum; 699 attempts still crossed manager frames.
- **Observed:** 205 decisions were authority-eligible, 196 selected an exact
  constraint, and 193 remained effective at issue. Allowed-set sizes included
  172 all-17 sets, nine empty sets, and 24 nontrivial directional sets.
- **Observed:** before canonical hit 845, 98/393 eligible decisions had
  complete applicable authority and 95 were effective, but every one was an
  all-17 empty-field set. The other 295 were unavailable. No nonempty
  effective set occurred within 80 frames of any hit.
- **Inferred:** this run validates capture, publication, and physical action
  authority, but falsifies useful pressure-wave coverage. Its 24-hit aggregate
  is different-RNG observational evidence and is not a causal rejection of
  the factorized predecessor or observed-body early kill.
- **Observed blocker counts:** 476 legal auxiliary timer roots, 237 uses of
  dynamic float `10069`, and 181 armed phase transitions dominated the reached
  semantic failures after frame crossings. Source v4 now lowers the first two
  classes and exact generic auxiliary delay scheduling; phase successors stay
  fail closed for the next gate.
