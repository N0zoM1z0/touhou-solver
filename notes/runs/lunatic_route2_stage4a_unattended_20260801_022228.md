# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260801_022228

## Scope And Integrity

- Valid practice scope: `1..45319` (11984 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[1833, 2499, 2959, 3568, 10478, 11594, 12314, 13187, 13757, 20425, 22306, 22773, 29732, 31065, 31576, 35868, 38534, 39120, 42938]`.
- Hard no-Bomb verification: **PASS** across 11984 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1833-T1`. It occurred during a nonspell phase at player (11.253, 267.201), with 282 bullets and 0 lasers. The projectile model reported pipeline clearance -1.426.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 8 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 16
- `fast_mode`: 13
- `corridor_deadline_miss`: 3
- `pool_density_over_1000`: 2
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1833 | nonspell | (11.253, 267.201) | `stay` | 282/0 | -1.426/-1.426 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2499 | nonspell | (8.000, 428.747) | `up_left_fast` | 607/0 | -1.568/-1.714 | 5f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2959 | nonspell | (8.000, 412.000) | `down_left` | 595/0 | 12.414/0.712 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 3568 | nonspell | (373.870, 254.681) | `left_fast` | 178/0 | 0.785/-0.249 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10478 | nonspell | (8.000, 414.343) | `up_fast` | 159/0 | -1.980/-11.242 | 13f/20f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11594 | 57 夢境「二重大結界」 | (272.650, 130.315) | `right_fast` | 602/0 | -2.795/-2.941 | 3f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12314 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 594/0 | -1.552/-1.552 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13187 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 630/0 | -1.451/-1.451 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13757 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 619/0 | -1.447/-1.447 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20425 | 61 散霊「夢想封印　寂」 | (371.060, 432.000) | `left_fast` | 459/0 | -4.349/-4.349 | 0f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22306 | nonspell | (376.000, 422.800) | `left_fast` | 777/0 | -2.645/-2.645 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22773 | nonspell | (30.274, 428.747) | `up_right` | 579/0 | 0.119/-1.141 | 5f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 29732 | nonspell | (16.000, 16.000) | `down_left_fast` | 131/0 | 0.221/-2.991 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 31065 | 65 神技「八方龍殺陣」 | (162.497, 428.880) | `up` | 1291/0 | -1.316/-1.316 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31576 | 65 神技「八方龍殺陣」 | (376.000, 405.373) | `up_fast` | 1254/0 | -12.994/-18.309 | 15f/27f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35868 | nonspell | (8.000, 428.747) | `up_left` | 78/0 | 0.159/-5.464 | 9f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38534 | 69 回霊「夢想封印　侘」 | (17.758, 432.000) | `right_fast` | 560/0 | -1.492/-3.026 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39120 | 69 回霊「夢想封印　侘」 | (374.374, 415.480) | `down_left` | 663/0 | -1.520/-1.520 | 0f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42938 | 73 大結界「博麗弾幕結界」 | (214.237, 376.621) | `left_fast` | 980/0 | -2.824/-2.824 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 6994 | 573 | 77 | 0 | 480 | 38 | 577.861 | 0.227 |
| 57 夢境「二重大結界」 | 4 | 1114 | 1092 | 306 | 0 | 0 | 171 | 185.498 | 0.222 |
| 61 散霊「夢想封印　寂」 | 1 | 1030 | 1024 | 374 | 0 | 0 | 168 | 128.801 | 0.157 |
| 65 神技「八方龍殺陣」 | 2 | 806 | 781 | 610 | 0 | 0 | 116 | 67.372 | 0.364 |
| 69 回霊「夢想封印　侘」 | 2 | 1099 | 1093 | 698 | 0 | 0 | 180 | 92.665 | 0.211 |
| 73 大結界「博麗弾幕結界」 | 1 | 941 | 934 | 537 | 0 | 0 | 180 | 124.803 | 0.016 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.977 ms median and 30.819 ms p95.
- The full enemy sensor produced 6453 snapshots; capture read time was `{'median': 5.552600006922148, 'p95': 21.674800009350292, 'max': 134.46500001009554}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 76.0}` frames, and 7 phase-counter discontinuities were excluded; 11719 decisions retained at least one robust-union body (maximum 39); 6483 decisions contained latent contact-disabled geometry (maximum 38), and 4977 contained bounded inactive-slot memory (maximum 37). 312 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.7787017822265625, 'p95': 4.700314998626709, 'max': 11.042068481445312}` / `{'median': 2.8439263105392456, 'p95': 4.390830039978027, 'max': 10.954437255859375}` / `{'median': 0.005507042010625213, 'p95': 3.5199966430664062, 'max': 7.4945068359375}`.
- The issue-time enemy guard retained 11984 observations, detected 5009 during-plan geometry changes, recertified 5009 decisions, and overrode 114 actions. Read/recertificate timing was `{'median': 1.5641999925719574, 'p95': 2.8866999928141013, 'max': 47.24460000579711}` / `{'median': 2.443599994876422, 'p95': 4.918199992971495, 'max': 151.88940000371076}` ms; 6492 issue captures contained latent bodies (maximum 38), and 4977 contained dormant bodies (maximum 37). Fresh/global transactions preserved 4895/5009 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9725 observations (9683 contact enabled, 42 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4137, '0x0059C9D0': 5588}`.
- The terminal-threat heuristic covered 11984 decisions with horizon counts `{'0': 25, '10': 11959}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 20, '3': 7836, '4': 3174, '5': 795, '6': 159}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 18, '2': 1023, '3': 9535, '4': 1408}`.
- Adaptive delay supports were `{'1,2': 18, '1,2,3': 4, '1,2,3,4,5': 37, '1,2,3,4,5,6': 30, '2,3': 556, '2,3,4': 3519, '2,3,4,5': 4008, '2,3,4,5,6': 2946, '3,4,5': 242, '3,4,5,6': 624}`; 140 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 63/411.
- Robust viability supplied 5497 available policy queries (0 had new delay support outside the cached policy), constrained 480 decisions, and exposed 2602 empty queried action sets. Recovery guidance was available/selected on 755/0 empty-kernel queries; distant-kernel guidance was available/selected on 1404/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 858, '1': 750, '2': 626, '3': 645, '4': 606, '5': 674, '6': 668, '7': 670}`.
- Global-horizon/local-prefix cross-tab covered 3038 decisions: 1 had a winning global state but unsafe selected prefix, 1325 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 207 selected actions were outside the reported winning set. 1188 newer issue-time hazard versions and 4 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 853 unique policies with solve-time statistics `{'median': 123.46260000776965, 'p95': 230.29040000983514, 'max': 1387.3576000041794}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 70, 'queryable': 5478, 'expired': 3886}`; 3937 robust-mode decisions had no query.
- Of 6674 unambiguous output transitions, 6338 (0.950) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 7, 'unresolved_planner_failure': 1, 'global_viability_kernel_exhausted_before_hit': 11}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 17 hit windows with a positive warning lead; those leads were `[5, 11, 0, 5, 20, 8, 3, 3, 5, 3, 8, 8, 4, 0, 27, 15, 3, 12, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.413 during the 60 frames preceding a hit versus 0.201 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 10.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact Ordinary Authority Audit

- **Observed:** 122/1,952 future-source projections completed. Transform and
  opcode-`0x19` failures were eliminated. Dominant remaining classes were 913
  armed phase transitions, 288 installed callbacks, and 258 auxiliary
  opcode-`0x2E` conditional jumps.
- **Observed:** exact authority was eligible/applicable/effective on
  499/480/461 of 6,994 nonspell decisions. The 237 decisions in nine nonspell
  80-frame hit windows included three applicable sets but zero effective sets.
- **Observed directional witness:** frames 3501/3518/3532 allowed 5/8/6
  actions. Post-capture advance was 15/16/12 frames against pickup-support
  high 6, so the deadline guard retained held `up_right`. The five-action set
  at frame 3501 excluded that held action. Hit followed at frame 3568.
- **Observed timing:** 38 unique complete nonspell policies had solve
  median/p95/max 578/1,148/1,387 ms; clearance was 19/562/609 ms and
  viability 390/967/1,173 ms.
- **Inference:** v5 establishes useful pressure-window directionality but not
  issue-time authority. The next falsifier must isolate background solve CPU
  from TH08/sensing/control and preserve those sets through issue.
