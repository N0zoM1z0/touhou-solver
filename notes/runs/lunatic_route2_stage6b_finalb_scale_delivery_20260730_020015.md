# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_finalb_scale_delivery_20260730_020015

## Scope And Integrity

- Valid practice scope: `1..76050` (18332 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 22, at `[7412, 9450, 12006, 12619, 13280, 19335, 19791, 21095, 37294, 37742, 41447, 42976, 49223, 50586, 52216, 55161, 58422, 58897, 59353, 62816, 65821, 71975]`.
- Hard no-Bomb verification: **PASS** across 18332 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F7412-T1`. It occurred during a nonspell phase at player (376.000, 53.049), with 603 bullets and 0 lasers. The projectile model reported pipeline clearance -24.137.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 12 |
| `observed_bullet_overlap` | 8 |
| `observed_laser_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 14
- `fast_mode`: 12
- `corridor_deadline_miss`: 6
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 7412 | nonspell | (376.000, 53.049) | `stay` | 603/0 | -24.137/-24.137 | 18f/26f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9450 | nonspell | (376.000, 409.847) | `up_right_fast` | 307/0 | -2.976/-3.122 | 3f/14f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12006 | 150 薬符「壺中の大銀河」 | (376.000, 408.756) | `down_right` | 801/0 | 0.832/0.040 | 0f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12619 | 150 薬符「壺中の大銀河」 | (14.505, 361.832) | `up_fast` | 631/0 | -4.122/-6.442 | 0f/20f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13280 | 150 薬符「壺中の大銀河」 | (338.858, 432.000) | `up_left_fast` | 760/0 | -9.460/-13.917 | 12f/41f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19335 | nonspell | (15.649, 426.343) | `up_right_fast` | 1094/0 | -1.365/-1.512 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19791 | nonspell | (12.600, 428.401) | `stay` | 1089/0 | -2.842/-2.842 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21095 | nonspell | (371.033, 424.000) | `down_left` | 1093/0 | 0.734/-1.729 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37294 | nonspell | (376.000, 432.000) | `stay` | 630/0 | -4.788/-4.788 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37742 | nonspell | (203.674, 243.967) | `up_right` | 502/0 | -3.421/-5.596 | 13f/29f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41447 | 162 神宝「サラマンダーシールド」 | (25.776, 416.000) | `right` | 542/24 | -4.272/-4.272 | 0f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42976 | 162 神宝「サラマンダーシールド」 | (371.400, 374.852) | `up_left` | 554/28 | -2.563/-2.563 | 3f/8f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49223 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 432.000) | `left_fast` | 282/52 | -2.265/-2.265 | 0f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 50586 | 166 神宝「ライフスプリングインフィニティ」 | (350.482, 414.164) | `right_fast` | 450/52 | -3.068/-8.895 | 3f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52216 | 166 神宝「ライフスプリングインフィニティ」 | (370.343, 432.000) | `up_fast` | 270/52 | -3.092/-3.092 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 55161 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (174.617, 432.000) | `up_left_fast` | 336/0 | -4.889/-4.889 | 7f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58422 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 418.449) | `up_left` | 560/0 | -1.844/-3.617 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58897 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (317.915, 381.484) | `up_left_fast` | 564/0 | -1.890/-1.890 | 0f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59353 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (376.000, 432.000) | `left_fast` | 581/0 | -1.650/-1.650 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 62816 | 174 「永夜返し  -待宵-」 | (8.000, 432.000) | `right_fast` | 894/0 | -2.494/-2.494 | 0f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 65821 | 178 「永夜返し  -子の四つ-」 | (14.505, 432.000) | `down_right_fast` | 1041/0 | -4.433/-4.433 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 71975 | 186 「永夜返し  -寅の四つ-」 | (340.570, 432.000) | `up` | 1062/0 | 1.015/-1.442 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 8150 | 7913 | 3709 | 0 | 4159 | 1223 | 94.083 | 0.081 |
| 150 薬符「壺中の大銀河」 | 3 | 735 | 715 | 176 | 0 | 533 | 118 | 209.833 | 0.151 |
| 154 | 0 | 833 | 824 | 316 | 0 | 437 | 157 | 127.714 | 0.224 |
| 158 | 0 | 1674 | 1666 | 994 | 0 | 560 | 272 | 49.030 | 0.202 |
| 162 神宝「サラマンダーシールド」 | 2 | 1301 | 1295 | 740 | 0 | 544 | 221 | 85.047 | 0.119 |
| 166 神宝「ライフスプリングインフィニティ」 | 3 | 1487 | 1481 | 585 | 0 | 799 | 250 | 146.394 | 0.183 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 4 | 1987 | 1976 | 1057 | 0 | 889 | 320 | 86.535 | 0.239 |
| 174 「永夜返し  -待宵-」 | 1 | 227 | 214 | 73 | 0 | 123 | 35 | 94.820 | 0.043 |
| 178 「永夜返し  -子の四つ-」 | 1 | 359 | 344 | 278 | 0 | 66 | 57 | 65.635 | 0.208 |
| 182 | 0 | 448 | 434 | 359 | 0 | 75 | 66 | 29.795 | 0.263 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 351 | 337 | 248 | 0 | 83 | 63 | 193.010 | 0.189 |
| 190 | 0 | 780 | 691 | 476 | 0 | 210 | 103 | 48.728 | 0.135 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 2 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.394 ms median and 30.751 ms p95.
- The full enemy sensor produced 9828 snapshots; capture read time was `{'median': 5.198200000450015, 'p95': 30.302400002256036, 'max': 84.32319993153214}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 13.0}` frames, and 13 phase-counter discontinuities were excluded; 17712 decisions retained at least one robust-union body (maximum 38); 5046 decisions contained latent contact-disabled geometry (maximum 38), and 6056 contained bounded inactive-slot memory (maximum 34). 151 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.7206878662109375, 'p95': 8.717498779296875, 'max': 9.882980346679688}` / `{'median': 0.8996439576148987, 'p95': 9.81427001953125, 'max': 9.880340576171875}` / `{'median': 1.817941665649414e-06, 'p95': 8.37994384765625, 'max': 9.846633911132812}`.
- The issue-time enemy guard retained 18332 observations, detected 697 during-plan geometry changes, recertified 697 decisions, and overrode 17 actions. Read/recertificate timing was `{'median': 1.8729999428614974, 'p95': 3.7345000309869647, 'max': 19.97769996523857}` / `{'median': 2.995499991811812, 'p95': 7.249100017361343, 'max': 19.676600000821054}` ms; 2677 issue captures contained latent bodies (maximum 38), and 6066 contained dormant bodies (maximum 34). Fresh/global transactions preserved 680/697 planned actions, relaxed 6 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 16698 observations (14331 contact enabled, 2367 anticipatory, 0 errors). 16698 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 16698}`.
- The terminal-threat heuristic covered 18332 decisions with horizon counts `{'0': 103, '10': 16581, '32': 1648}`; it reported 5 collision and 246 sub-safety-clearance warnings, and relaxed 401 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 82, '3': 9708, '4': 7717, '5': 825}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 14, '2': 155, '3': 15331, '4': 2825, '6': 7}`.
- Adaptive delay supports were `{'1,2': 14, '1,2,3': 58, '1,2,3,4': 8, '1,2,3,4,5': 68, '1,2,3,4,5,6': 65, '2,3': 5, '2,3,4': 1182, '2,3,4,5': 6621, '2,3,4,5,6': 10208, '3,4': 9, '3,4,5': 10, '3,4,5,6': 77, '4,5,6': 6, '6': 1}`; 75 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 42/282.
- Robust viability supplied 17890 available policy queries (0 had new delay support outside the cached policy), constrained 8478 decisions, and exposed 9011 empty queried action sets. Recovery guidance was available/selected on 2145/1069 empty-kernel queries; distant-kernel guidance was available/selected on 5902/5693. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 5.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 326.3372488699382, 'max': 489.76729168044693}`, and `{'median': 0.0, 'p95': 20.860107421875, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2881, '1': 2520, '2': 1798, '3': 1960, '4': 2158, '5': 2162, '6': 2115, '7': 2296}`.
- Global-horizon/local-prefix cross-tab covered 14849 decisions: 4 had a winning global state but unsafe selected prefix, 7773 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 128 selected actions were outside the reported winning set. 601 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2885 unique policies with solve-time statistics `{'median': 93.66779995616525, 'p95': 352.5770999258384, 'max': 455.34079999197274}` and first-observed ages `{'median': 3.0, 'p95': 7.0, 'max': 1811.0}`. Policy status counts were `{'pending_future_epoch': 75, 'queryable': 17891, 'expired': 139}`; 215 robust-mode decisions had no query.
- Of 9046 unambiguous output transitions, 7818 (0.864) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 22}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 22 hit windows with a positive warning lead; those leads were `[26, 14, 12, 20, 41, 4, 5, 8, 5, 29, 12, 8, 4, 11, 5, 15, 11, 13, 4, 8, 6, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.220 during the 60 frames preceding a hit versus 0.138 outside those windows.
- Mean selected control-reserve deficit was 10.873 during the 60 frames preceding a hit versus 6.406 outside those windows.
- Soft recovery was selected on 0.031 of alive decisions in the 60-frame pre-hit windows versus 0.059 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 6.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Retained SEM-SCALE-C5 Disposition

- The nested exact-delivery gate **passes** under strict report schema v4.
  One coherent spell-190/sub44 source captured manager frame 75,811, one
  manager frame after controller decision/expected frame 75,810. Causal
  authority begins at sampled offset 1; no offset-zero row is backfilled.
- 111 exact decisions consume the accepted quarter-scale schedule through
  offset 238 with no authority fallback, fresh hit, or Bomb. Source player
  phase 3 and predeath baseline 7 are explicit contamination.
- Callback 18 schedules the unit restore at offset 239. Cadence skips that
  frame; offset 240 observes the unit root together with
  `scene_inactive/status=terminal_unload`.
- Raw JSONL is 634,344,375 bytes with SHA-256
  `cbad986f0bb627d88135e2a4ae31c48389b6e030657ad77e557b882585aedcfc`.
  Strict v4 report SHA-256 is
  `53cddd1162769010dbc467bf9d295e90e5389db3ffb4fce3d1c73c42076b08ec`.
  The rejected original Windows-CRLF strict v3 render hashes to
  `b1aa5a0c27082303a19c7d90f7aba42661006c5892e351b68c3e0a80f65aa2b5`;
  its tracked LF-normalized artifact hashes to
  `9d3652466596f3a49cd67d0ff317f31685c92d23a6640bdf5ed9d47bd9d5dca7`;
  CE-0190 records its noncausal offset-zero/active-restore assumptions.
- This exact-scope pass does not override the complete-stage result: 22 hit
  edges, canonical nonspell hit at frame 7,412, and zero Bomb. It grants no
  clean Final-B, pre-target, Power-0 late-route, Extra, or NMNB authority.
- The aggregate is three hits above C5-1, but the samples are not paired or
  same-seed. Their first hits occur in different positions/classes before
  the spell-190 source path is active, while cadence remains `3/4` frames
  median/p95. There is no causal rollback witness.

## Next Correction Gate

Do not repeat C5 or the unchanged full route. Continue the ordered roadmap at
`SEM-MODE`: revalidate focus/secondary-character transition delay and
action-conditioned enemy contact/damage eligibility against the retained
frame `10065 -> 10075` case plus adversarial focus toggles. Preserve the
whole-stage physical-unit rule for the later immutable-model falsifier.
Policy delivery, delay-support coverage, and viability exhaustion remain
separate survival gates; compare per-phase position and warning lead, not only
aggregate hit count.
