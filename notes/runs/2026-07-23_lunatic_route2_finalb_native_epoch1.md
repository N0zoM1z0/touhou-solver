# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_finalb_practice_native_epoch1_20260723_222808

## Scope And Integrity

- Valid practice scope: `0..72341` (17722 decisions).
- Selected frame epoch: 1 of 2; 16964 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary is not scope-valid because thprac reset the manager counter before the external stop.
- Native hit edges: 31, at `[8398, 8909, 11931, 18387, 19119, 20135, 20622, 21446, 23644, 30925, 31421, 33634, 34281, 34823, 37608, 38356, 38756, 39838, 40166, 46704, 47170, 47712, 48312, 52267, 52743, 53175, 56004, 56499, 59284, 68030, 71858]`.
- Hard no-Bomb verification: **PASS** across 17722 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F8398-T1`. It occurred during a nonspell phase at player (265.179, 419.191), with 319 bullets and 0 lasers. The projectile model reported pipeline clearance 16.379.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 14 |
| `observed_bullet_overlap` | 9 |
| `observed_laser_overlap` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 3 |
| `observed_multiple_hazard_overlap` | 1 |

Contributing factors:

- `fast_mode`: 26
- `playfield_boundary`: 9
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8398 | nonspell | (265.179, 419.191) | `down_right` | 319/0 | 16.379/3.628 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 8909 | nonspell | (367.473, 420.744) | `up_right_fast` | 270/0 | -2.971/-2.971 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11931 | 150 薬符「壺中の大銀河」 | (376.000, 407.365) | `left_fast` | 423/0 | -2.542/-2.542 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 18387 | nonspell | (9.505, 16.061) | `down_fast` | 1079/0 | -1.817/-1.817 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 19119 | nonspell | (8.409, 425.127) | `up_right_fast` | 1145/0 | -0.007/-1.654 | 0f/14f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20135 | nonspell | (18.441, 424.574) | `up_left_fast` | 1180/0 | -1.881/-2.478 | 4f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 20622 | nonspell | (369.015, 423.843) | `up_fast` | 1171/0 | 0.471/-1.351 | 3f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 21446 | nonspell | (11.253, 428.211) | `up_right_fast` | 1211/0 | -1.636/-1.636 | 2f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23644 | 154 神宝「ブリリアントドラゴンバレッタ」 | (136.271, 425.259) | `up_fast` | 127/251 | -2.477/-7.893 | 0f/44f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30925 | 158 神宝「ブディストダイアモンド」 | (42.454, 427.294) | `up_fast` | 236/33 | -3.240/-3.240 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31421 | 158 神宝「ブディストダイアモンド」 | (191.632, 425.321) | `up_right_fast` | 205/33 | -2.414/-6.356 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 33634 | nonspell | (191.849, 141.345) | `up_left_fast` | 0/0 | 9999.000/8.752 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 34281 | nonspell | (97.572, 165.347) | `left_fast` | 688/0 | -2.360/-2.360 | 3f/16f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 34823 | nonspell | (371.855, 425.994) | `up_fast` | 575/0 | -2.899/-2.899 | 4f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37608 | 162 神宝「サラマンダーシールド」 | (364.331, 401.890) | `up_left_fast` | 534/16 | -5.285/-7.810 | 7f/7f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38356 | 162 神宝「サラマンダーシールド」 | (40.748, 357.769) | `down_left_fast` | 558/28 | -6.767/-8.207 | 20f/34f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38756 | 162 神宝「サラマンダーシールド」 | (34.987, 308.392) | `up_fast` | 496/32 | -5.877/-8.307 | 17f/17f | `observed_multiple_hazard_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39838 | 162 神宝「サラマンダーシールド」 | (89.220, 420.177) | `up_right_fast` | 570/28 | -6.148/-8.235 | 9f/12f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 40166 | 162 神宝「サラマンダーシールド」 | (356.113, 337.674) | `up_left` | 466/32 | -5.508/-7.913 | 12f/24f | `observed_laser_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 46704 | 166 神宝「ライフスプリングインフィニティ」 | (8.000, 19.475) | `down_fast` | 262/52 | -2.758/-2.758 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 47170 | 166 神宝「ライフスプリングインフィニティ」 | (237.275, 429.875) | `up_fast` | 326/52 | -2.266/-5.778 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 47712 | 166 神宝「ライフスプリングインフィニティ」 | (217.672, 425.100) | `up_fast` | 459/52 | -2.296/-5.906 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 48312 | 166 神宝「ライフスプリングインフィニティ」 | (208.263, 424.489) | `up_fast` | 440/52 | -2.996/-3.256 | 20f/86f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 52267 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (346.093, 418.117) | `left_fast` | 563/0 | 1.707/-2.230 | 7f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 52743 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.953, 406.876) | `down_right` | 562/0 | -2.543/-2.543 | 0f/2f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 53175 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (128.566, 415.025) | `up_right` | 583/0 | -0.786/-1.329 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 56004 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (212.003, 213.161) | `right_fast` | 595/0 | -3.219/-3.219 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 56499 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (14.185, 432.000) | `up_fast` | 585/0 | 1.235/1.235 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 59284 | 174 「永夜返し  -待宵-」 | (26.304, 427.431) | `stay` | 898/0 | -2.270/-2.270 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 68030 | 186 「永夜返し  -寅の四つ-」 | (10.178, 432.000) | `right_fast` | 1062/0 | -2.595/-2.595 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 71858 | 190 「永夜返し  -世明け-」 | (19.722, 426.833) | `right_fast` | 610/0 | -2.298/-2.445 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 8563 | 0 | 0 | 0 | 0 | 0 | - | 0.119 |
| 150 薬符「壺中の大銀河」 | 1 | 853 | 0 | 0 | 0 | 0 | 0 | - | 0.004 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 1 | 539 | 0 | 0 | 0 | 0 | 0 | - | 0.279 |
| 158 神宝「ブディストダイアモンド」 | 2 | 859 | 0 | 0 | 0 | 0 | 0 | - | 0.483 |
| 162 神宝「サラマンダーシールド」 | 5 | 1275 | 0 | 0 | 0 | 0 | 0 | - | 0.356 |
| 166 神宝「ライフスプリングインフィニティ」 | 4 | 978 | 0 | 0 | 0 | 0 | 0 | - | 0.345 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 5 | 2057 | 0 | 0 | 0 | 0 | 0 | - | 0.272 |
| 174 「永夜返し  -待宵-」 | 1 | 341 | 0 | 0 | 0 | 0 | 0 | - | 0.271 |
| 178 | 0 | 508 | 0 | 0 | 0 | 0 | 0 | - | 0.234 |
| 182 | 0 | 535 | 0 | 0 | 0 | 0 | 0 | - | 0.224 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 298 | 0 | 0 | 0 | 0 | 0 | - | 0.554 |
| 190 「永夜返し  -世明け-」 | 1 | 916 | 65 | 62 | 0 | 3 | 5 | 4149.531 | 0.154 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 4 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.610 ms median and 35.008 ms p95.
- Modeled action hold counts were `{'2': 1391, '3': 10666, '4': 5306, '5': 159, '6': 200}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 1, '2': 873, '3': 14000, '4': 2473, '5': 264, '6': 111}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3': 436, '1,2,3,4': 582, '1,2,3,4,5': 470, '1,2,3,4,5,6': 237, '2,3': 751, '2,3,4': 2609, '2,3,4,5': 5875, '2,3,4,5,6': 3960, '3,4': 79, '3,4,5': 1303, '3,4,5,6': 1332, '4,5,6': 87}`; 531 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 115/1114.
- Robust viability supplied 65 available policy queries (0 had new delay support outside the cached policy), constrained 3 decisions, and exposed 62 empty queried action sets. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 0.0, 'max': 17.0}` and `{'median': 0.0, 'p95': 0.0, 'max': 93.0}`.
- The rolling worker produced 5 unique policies with solve-time statistics `{'median': 4149.531300005037, 'p95': 4871.137300011469, 'max': 8562.75650000316}` and first-observed ages `{'median': 73.0, 'p95': 114.0, 'max': 339.0}`. Policy status counts were `{'pending_future_epoch': 60, 'queryable': 63, 'expired': 452}`; 510 robust-mode decisions had no query.
- Of 9362 unambiguous output transitions, 7984 (0.853) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'unresolved_planner_failure': 2, 'robust_action_set_exhausted_before_hit': 29}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 29 hit windows with a positive warning lead; those leads were `[0, 5, 8, 3, 14, 6, 6, 7, 44, 10, 6, 0, 16, 8, 7, 34, 17, 12, 24, 4, 10, 3, 86, 15, 2, 8, 7, 5, 5, 7, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.366 during the 60 frames preceding a hit versus 0.186 outside those windows.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 18.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Scope Qualification

- **Observed:** The raw `222808` trace contains two complete Final-B frame
  epochs. The operator identified the later `0..72341` epoch as the intended
  trial; the earlier 16,964 decisions are excluded. The raw agent summary
  aggregates both attempts and is not scope-valid for this dossier.
- **Observed:** The selected epoch has 31 hard-no-Bomb hit edges. Phase hit
  counts are nonspell 10, spell 150 one, 154 one, 158 two, 162 five, 166 four,
  170 five, 174 one, 186 one, and 190 one. Spells 178 and 182 have no hit.
- **Observed:** Pre-hit bottom-eight-pixel occupancy remained high at 36.6%,
  versus 18.6% outside the 60-frame pre-hit windows. Native input visibility
  remained 85.3% on the next observation, so SendInput pickup is not the
  primary explanation.

## Cross-Attempt Planner Failure

- **Observed:** The selected epoch had no corridor record in nonspells or
  spells 150 through 186. Its first corridor record appeared only at frame
  70,798 during spell 190, with a future policy source at frame 70,925.
- **Observed:** Only 575 decisions exposed a global policy, with 65 queries
  and three viable queried states. The previous rolling-epoch baseline had
  17,914 policy decisions and 8,454 queries.
- **Root cause:** `corridor_last_submit` retained the first attempt's roughly
  70k frame timestamp across terminal unload and restart. The new attempt's
  manager counter restarted at zero, so
  `current_frame - corridor_last_submit >= corridor_every` could not become
  true until the new attempt also reached roughly frame 70k.
- **Disposition:** This is a valid local-planner death corpus but an invalid
  physical acceptance test of the native global policy. The aggregate
  `25 -> 31` hit change must not be attributed to the native viability
  correction.

## Solver Performance Finding

- **Observed:** The five late native solutions took 4,150/4,871/8,563 ms
  median/p95/max. Median phase timing was 105 ms clearance and 4,027 ms
  viability. The worker had a negative 544-frame median serial margin.
- **Observed:** The original 1,500-AABB/250-segment benchmark made most
  lattice states unsafe early, so the backward kernel pruned quickly. A
  hazard-free workload exercised the real worst branch and reproduced
  approximately 1.6 seconds on WSL before correction; live sparse/open
  patterns could take several seconds.
- **Correction:** The native kernel now precomputes and caches every
  hazard-independent lattice transition for all physical delays in a control
  layer. The daemon performs the cold build before F8. Post-correction Windows
  warm medians are 294 ms for an open field, 184 ms for 600 AABBs plus 52
  segments, and 446 ms for 1,500 AABBs plus 250 segments.

## Offline Correction

- Scene resume now resets the submit timestamp, active/pending policy,
  commitment, delay estimator, and local timing state.
- Async context is `(gameplay_epoch, stage, spell)`. A completed future from
  an earlier attempt is rejected even when the restarted thprac stage and
  spell identifiers are identical.
- The practice dossier can explicitly select `--frame-epoch last` and records
  excluded earlier decisions. Practice comparison is phase-generic rather
  than hard-coded to Stage-3 spell 50.
- Physical acceptance remains pending. The next focused Final-B run must begin
  with a freshly loaded daemon/DLL and show submissions near the beginning of
  the attempt, sustained queryable coverage, positive serial margin, and hard
  no-Bomb evidence.
