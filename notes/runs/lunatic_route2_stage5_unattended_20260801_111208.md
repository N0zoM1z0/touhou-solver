# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_111208

## Scope And Integrity

- Valid practice scope: `2..45528` (11584 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[2118, 2761, 3793, 7248, 8262, 10695, 11379, 12500, 13203, 13633, 13973, 14409, 24823, 29497, 31652, 36179, 40675, 43507, 44839]`.
- Hard no-Bomb verification: **PASS** across 11584 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2118-T1`. It occurred during a nonspell phase at player (8.000, 366.252), with 447 bullets and 0 lasers. The projectile model reported pipeline clearance -1.423.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 9 |
| `modeled_committed_prefix_collision` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 4 |

Contributing factors:

- `fast_mode`: 15
- `playfield_boundary`: 10
- `action_lag_over_model`: 8
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2118 | nonspell | (8.000, 366.252) | `stay` | 447/0 | -1.423/-1.423 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 2761 | nonspell | (192.000, 384.000) | `stay` | 822/0 | -3.622/-3.622 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 3793 | nonspell | (362.415, 425.052) | `down_fast` | 759/0 | 11.878/-26.979 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 7248 | nonspell | (376.000, 432.000) | `up_fast` | 603/0 | -2.459/-2.459 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 8262 | nonspell | (320.484, 353.347) | `up_fast` | 635/0 | 15.489/-13.606 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 10695 | nonspell | (352.907, 420.000) | `up_fast` | 891/0 | -2.643/-3.048 | 0f/14f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11379 | nonspell | (342.742, 432.000) | `left_fast` | 914/0 | 0.258/-9.851 | 19f/29f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12500 | nonspell | (355.268, 432.000) | `left_fast` | 255/0 | -0.195/-1.660 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13203 | nonspell | (203.707, 424.000) | `left_fast` | 129/0 | 1.702/1.702 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 13633 | nonspell | (259.882, 432.000) | `down_right_fast` | 399/0 | -16.557/-16.557 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 13973 | nonspell | (355.980, 16.000) | `stay` | 609/0 | -0.956/-3.172 | 20f/20f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 14409 | nonspell | (367.818, 409.932) | `up_fast` | 539/0 | 10.046/9.900 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 24823 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1105/0 | -1.033/-1.033 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29497 | nonspell | (8.000, 432.000) | `up_fast` | 1114/0 | -2.402/-2.402 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31652 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (99.021, 419.515) | `left_fast` | 1011/0 | -8.561/-8.561 | 8f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36179 | nonspell | (8.000, 422.242) | `down_fast` | 388/0 | -2.362/-2.362 | 4f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 40675 | 111 懶惰「生神停止(マインドストッパー)」 | (185.600, 16.000) | `up_left_fast` | 499/0 | -0.179/-3.170 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43507 | 115 散符「真実の月(インビジブルフルムーン)」 | (199.679, 432.000) | `up_right_fast` | 905/0 | -1.740/-1.740 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44839 | 115 散符「真実の月(インビジブルフルムーン)」 | (360.000, 432.000) | `up_left` | 1299/0 | 0.997/-1.829 | 10f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 14 | 7591 | 3 | 2 | 0 | 7 | 3 | 1181.143 | 0.456 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 901 | 765 | 531 | 0 | 0 | 106 | 105.618 | 0.381 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 966 | 961 | 777 | 0 | 0 | 207 | 78.092 | 0.357 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1049 | 1042 | 645 | 0 | 0 | 178 | 69.786 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1077 | 1070 | 699 | 0 | 0 | 184 | 64.601 | 0.441 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 18.323 ms median and 31.367 ms p95.
- The full enemy sensor produced 6305 snapshots; capture read time was `{'median': 4.711199988378212, 'p95': 25.4852999933064, 'max': 567.2878000186756}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 95.0}` frames, and 14 phase-counter discontinuities were excluded; 10939 decisions retained at least one robust-union body (maximum 51); 8463 decisions contained latent contact-disabled geometry (maximum 51), and 3968 contained bounded inactive-slot memory (maximum 36). 412 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.9766082763671875, 'p95': 4.5774688720703125, 'max': 8.514547348022461}` / `{'median': 0.9807853102684021, 'p95': 4.534294128417969, 'max': 4.70754861831665}` / `{'median': 5.856156349182129e-06, 'p95': 1.8475148337227958, 'max': 5.649997711181641}`.
- The issue-time enemy guard retained 11584 observations, detected 3059 during-plan geometry changes, recertified 3059 decisions, and overrode 52 actions. Read/recertificate timing was `{'median': 0.5987999902572483, 'p95': 1.7321000050287694, 'max': 174.97560000629164}` / `{'median': 3.1676999933551997, 'p95': 6.793799984734505, 'max': 531.4001000078861}` ms; 8444 issue captures contained latent bodies (maximum 51), and 3987 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3009/3061 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9295 observations (9269 contact enabled, 26 anticipatory, 0 errors). 9295 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9295}`.
- The terminal-threat heuristic covered 11584 decisions with horizon counts `{'0': 537, '10': 11047}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 495, '3': 7557, '4': 2317, '5': 1032, '6': 183}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 288, '2': 477, '3': 8818, '4': 1775, '5': 192, '6': 34}`.
- Adaptive delay supports were `{'1,2': 229, '1,2,3': 78, '1,2,3,4': 179, '1,2,3,4,5': 189, '1,2,3,4,5,6': 211, '2,3': 529, '2,3,4': 3915, '2,3,4,5': 2963, '2,3,4,5,6': 1855, '3,4': 48, '3,4,5': 66, '3,4,5,6': 1296, '4,5,6': 5, '5,6': 8, '6': 13}`; 261 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 23/131.
- Robust viability supplied 3841 available policy queries (0 had new delay support outside the cached policy), constrained 7 decisions, and exposed 2654 empty queried action sets. Recovery guidance was available/selected on 237/0 empty-kernel queries; distant-kernel guidance was available/selected on 1644/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 635, '1': 529, '2': 460, '3': 390, '4': 435, '5': 468, '6': 481, '7': 443}`.
- Global-horizon/local-prefix cross-tab covered 1529 decisions: 4 had a winning global state but unsafe selected prefix, 783 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 32 selected actions were outside the reported winning set. 1681 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 678 unique policies with solve-time statistics `{'median': 75.8007499971427, 'p95': 173.43550000805408, 'max': 1482.738499995321}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 71.0}`. Policy status counts were `{'queryable': 3835, 'pending_future_epoch': 90, 'expired': 60}`; 144 robust-mode decisions had no query.
- Of 6060 unambiguous output transitions, 5685 (0.938) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 2, 'missing_pre_hit_alive_decision': 1, 'unresolved_planner_failure': 4, 'robust_action_set_exhausted_before_hit': 7, 'global_viability_kernel_exhausted_before_hit': 5}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[0, 0, 0, 8, 0, 14, 29, 4, 0, 0, 20, 0, 3, 6, 14, 6, 9, 6, 19]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.735 during the 60 frames preceding a hit versus 0.383 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
