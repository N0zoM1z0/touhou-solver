# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_finalb_scale_delivery_20260729_233720

## Scope And Integrity

- Valid practice scope: `2..74080` (17282 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[8085, 8710, 11666, 12540, 18463, 19198, 22877, 31005, 41117, 42459, 51809, 54631, 55525, 56897, 58265, 59327, 62582, 65133, 73477]`.
- Hard no-Bomb verification: **PASS** across 17282 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## SEM-SCALE-C5 Disposition

- The strict exact-delivery gate **failed**. No complete source was accepted,
  no exact live origin was published, and no quarter-to-unit schedule was
  delivered to action.
- The last hit at frame 73,477 occurred in spell 190. The player was still in
  phase 3 with predeath residue 7 immediately before the quarter-scale source
  window. The first quarter root at frame 73,600 therefore entered the old
  phase-0-only read-only wait; phase 0 returned only at frame 74,079, when the
  root had already restored to unit.
- This is CE-0188. It falsifies the old source trigger, not the C4 native ECL
  schedule. A stable nonzero player phase must be retained as contamination
  and must not be called normal-player survival.
- Raw JSONL size is 579,579,062 bytes and SHA-256 is
  `11ba10fb1ac771e138627cff0e6faf7855e0858c5cf70b88c0fa2c9966e52b8a`.
  The post-close strict analyzer is schema
  `th08-finalb-scale-live-delivery-physical-report-v3`; its compact report
  SHA-256 is
  `18f26f3f2d27234ae2b419aa01966fd3c646b0268419e4af76c7ac60398ca0a6`.
- No replay was created by this Practice Start trial. The complete native
  trace, compact artifacts, and first-hit ledger are the retained evidence.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F8085-T1`. It occurred during a nonspell phase at player (376.000, 418.924), with 403 bullets and 0 lasers. The projectile model reported pipeline clearance -1.090.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 7 |
| `observed_laser_overlap` | 3 |

Contributing factors:

- `playfield_boundary`: 17
- `fast_mode`: 11
- `pool_density_over_1000`: 4
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8085 | nonspell | (376.000, 418.924) | `up_right` | 403/0 | -1.090/-3.793 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8710 | nonspell | (20.000, 432.000) | `up_fast` | 654/0 | 0.590/-3.452 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11666 | 150 薬符「壺中の大銀河」 | (296.045, 420.686) | `right_fast` | 558/0 | -1.380/-3.167 | 7f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12540 | 150 薬符「壺中の大銀河」 | (371.121, 419.121) | `stay` | 338/0 | -19.448/-22.569 | 56f/73f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18463 | nonspell | (376.000, 427.121) | `up_left` | 1146/0 | -0.132/-2.301 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19198 | nonspell | (19.768, 432.000) | `right_fast` | 1140/0 | -2.046/-2.246 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22877 | 154 神宝「ブリリアントドラゴンバレッタ」 | (176.808, 432.000) | `up_fast` | 125/230 | -2.984/-2.984 | 0f/22f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31005 | 158 神宝「ブディストダイアモンド」 | (8.000, 432.000) | `stay` | 244/33 | -1.013/-1.013 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41117 | 162 神宝「サラマンダーシールド」 | (228.962, 432.000) | `right_fast` | 526/28 | -2.973/-3.308 | 5f/5f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42459 | 162 神宝「サラマンダーシールド」 | (8.000, 426.952) | `up_right_fast` | 526/32 | -4.595/-4.595 | 0f/8f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51809 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 432.000) | `up_left_fast` | 309/52 | -2.874/-2.874 | 3f/7f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 54631 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (235.192, 432.000) | `up` | 336/0 | -5.353/-5.353 | 11f/22f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55525 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 432.000) | `up` | 558/0 | -4.049/-4.049 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56897 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 426.649) | `up_fast` | 558/0 | -1.207/-1.207 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58265 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (14.503, 429.968) | `down_right` | 584/0 | -2.411/-2.411 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59327 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 422.343) | `up_left_fast` | 581/0 | 2.920/-3.254 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 62582 | 174 「永夜返し  -待宵-」 | (376.000, 432.000) | `left_fast` | 1189/0 | -4.264/-4.264 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 65133 | 178 「永夜返し  -子の四つ-」 | (28.000, 432.000) | `up_right` | 1003/0 | -2.331/-2.331 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 73477 | 190 「永夜返し  -世明け-」 | (376.000, 424.000) | `left_fast` | 383/0 | -2.923/-2.923 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 7955 | 7733 | 3744 | 0 | 3919 | 1198 | 94.471 | 0.091 |
| 150 薬符「壺中の大銀河」 | 2 | 871 | 852 | 483 | 0 | 361 | 145 | 176.218 | 0.137 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 1 | 636 | 628 | 242 | 0 | 352 | 118 | 125.947 | 0.183 |
| 158 神宝「ブディストダイアモンド」 | 1 | 1688 | 1681 | 920 | 0 | 645 | 271 | 49.810 | 0.256 |
| 162 神宝「サラマンダーシールド」 | 2 | 1249 | 1243 | 663 | 0 | 575 | 219 | 89.438 | 0.118 |
| 166 神宝「ライフスプリングインフィニティ」 | 1 | 1449 | 1443 | 496 | 0 | 872 | 246 | 145.772 | 0.145 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 5 | 1964 | 1953 | 1006 | 0 | 923 | 320 | 90.483 | 0.232 |
| 174 「永夜返し  -待宵-」 | 1 | 307 | 291 | 153 | 0 | 135 | 50 | 81.722 | 0.177 |
| 178 「永夜返し  -子の四つ-」 | 1 | 216 | 201 | 138 | 0 | 63 | 33 | 77.382 | 0.136 |
| 182 | 0 | 453 | 442 | 366 | 0 | 76 | 68 | 31.308 | 0.355 |
| 186 | 0 | 126 | 113 | 44 | 0 | 68 | 17 | 313.408 | 0.044 |
| 190 「永夜返し  -世明け-」 | 1 | 368 | 356 | 192 | 0 | 164 | 54 | 47.892 | 0.102 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 3 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.429 ms median and 30.474 ms p95.
- The full enemy sensor produced 9326 snapshots; capture read time was `{'median': 5.704050010535866, 'p95': 31.611999962478876, 'max': 74.31619998533279}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 59.0}` frames, and 12 phase-counter discontinuities were excluded; 16678 decisions retained at least one robust-union body (maximum 39); 4517 decisions contained latent contact-disabled geometry (maximum 39), and 5962 contained bounded inactive-slot memory (maximum 35). 161 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.3632965087890625, 'max': 4.7252655029296875}` / `{'median': 0.0, 'p95': 8.726593017578125, 'max': 9.450531005859375}` / `{'median': 0.0, 'p95': 4.3632965087890625, 'max': 4.7252655029296875}`.
- The issue-time enemy guard retained 17282 observations, detected 748 during-plan geometry changes, recertified 748 decisions, and overrode 18 actions. Read/recertificate timing was `{'median': 1.8903000163845718, 'p95': 3.8169999606907368, 'max': 14.801400015130639}` / `{'median': 3.0396999209187925, 'p95': 8.066600072197616, 'max': 25.242700008675456}` ms; 2850 issue captures contained latent bodies (maximum 39), and 5949 contained dormant bodies (maximum 35). Fresh/global transactions preserved 730/748 planned actions, relaxed 1 fresh/global empty intersections, inherited 15 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 15680 observations (14000 contact enabled, 1680 anticipatory, 0 errors). 15680 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 15680}`.
- The terminal-threat heuristic covered 17282 decisions with horizon counts `{'0': 93, '10': 15679, '32': 1510}`; it reported 5 collision and 131 sub-safety-clearance warnings, and relaxed 336 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 63, '3': 7946, '4': 8726, '5': 547}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 77, '3': 13098, '4': 4091, '5': 10, '6': 6}`.
- Adaptive delay supports were `{'1,2,3': 1, '1,2,3,4': 70, '1,2,3,4,5': 119, '2,3': 6, '2,3,4': 1147, '2,3,4,5': 5520, '2,3,4,5,6': 9908, '3': 1, '3,4': 78, '3,4,5': 197, '3,4,5,6': 234, '4,5,6': 1}`; 90 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 32/322.
- Robust viability supplied 16936 available policy queries (0 had new delay support outside the cached policy), constrained 8153 decisions, and exposed 8447 empty queried action sets. Recovery guidance was available/selected on 2074/1059 empty-kernel queries; distant-kernel guidance was available/selected on 5553/5357. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 7.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 102.44998779892558, 'p95': 329.84845004941286, 'max': 520.9222590751906}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2724, '1': 2413, '2': 1743, '3': 1793, '4': 2125, '5': 1994, '6': 1995, '7': 2149}`.
- Global-horizon/local-prefix cross-tab covered 14170 decisions: 3 had a winning global state but unsafe selected prefix, 7232 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 144 selected actions were outside the reported winning set. 620 newer issue-time hazard versions and 1 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2739 unique policies with solve-time statistics `{'median': 95.8587999921292, 'p95': 362.799399998039, 'max': 529.7033999813721}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1803.0}`. Policy status counts were `{'pending_future_epoch': 80, 'queryable': 16940, 'expired': 53}`; 137 robust-mode decisions had no query.
- Of 8595 unambiguous output transitions, 7487 (0.871) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 18, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[10, 8, 19, 73, 7, 5, 22, 5, 5, 8, 7, 22, 6, 8, 5, 8, 9, 8, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.415 during the 60 frames preceding a hit versus 0.136 outside those windows.
- Mean selected control-reserve deficit was 15.828 during the 60 frames preceding a hit versus 6.463 outside those windows.
- Soft recovery was selected on 0.059 of alive decisions in the 60-frame pre-hit windows versus 0.062 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
