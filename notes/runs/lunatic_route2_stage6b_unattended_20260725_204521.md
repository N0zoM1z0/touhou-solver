# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260725_204521

## Scope And Integrity

- Valid practice scope: `2..76235` (15536 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 31, at `[2166, 8338, 8885, 12012, 12869, 13335, 13664, 18670, 20211, 21630, 22180, 22916, 33813, 38866, 44193, 49861, 51085, 51672, 52222, 52915, 53471, 56256, 56886, 57731, 58241, 59154, 59681, 61081, 64086, 66639, 72128]`.
- Hard no-Bomb verification: **PASS** across 15536 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F2166-T1`. It occurred during a nonspell phase at player (197.491, 432.000), with 384 bullets and 0 lasers. The projectile model reported pipeline clearance -1.438.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 19 |
| `observed_bullet_overlap` | 5 |
| `observed_laser_overlap` | 5 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 25
- `playfield_boundary`: 21
- `corridor_deadline_miss`: 7
- `pool_density_over_1000`: 5
- `action_lag_over_model`: 1
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2166 | nonspell | (197.491, 432.000) | `up_fast` | 384/0 | -1.438/-1.438 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8338 | nonspell | (331.318, 376.582) | `down_left_fast` | 476/0 | 10.127/4.927 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8885 | nonspell | (51.565, 418.761) | `right_fast` | 370/0 | 16.067/9.654 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12012 | 150 薬符「壺中の大銀河」 | (364.686, 432.000) | `up_left_fast` | 741/0 | -12.198/-12.198 | 5f/31f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12869 | 150 薬符「壺中の大銀河」 | (8.000, 432.000) | `up_right_fast` | 434/0 | -3.881/-22.515 | 17f/21f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13335 | 150 薬符「壺中の大銀河」 | (33.784, 24.485) | `down_right` | 392/0 | -1.511/-12.656 | 3f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13664 | 150 薬符「壺中の大銀河」 | (266.894, 432.000) | `left_fast` | 408/0 | -1.850/-2.201 | 0f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 18670 | nonspell | (8.000, 432.000) | `up` | 1083/0 | -2.781/-2.781 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20211 | nonspell | (376.000, 432.000) | `up_left_fast` | 1003/0 | -0.466/-1.510 | 4f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21630 | nonspell | (13.303, 432.000) | `up_fast` | 1245/0 | -1.597/-1.597 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22180 | 154 神宝「ブリリアントドラゴンバレッタ」 | (160.110, 411.300) | `up` | 99/230 | -1.771/-1.771 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22916 | 154 神宝「ブリリアントドラゴンバレッタ」 | (244.517, 432.000) | `up_fast` | 119/205 | -3.378/-3.378 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33813 | 158 神宝「ブディストダイアモンド」 | (12.879, 432.000) | `right` | 245/33 | -1.824/-1.824 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38866 | nonspell | (376.000, 432.000) | `up_left_fast` | 677/0 | -5.862/-5.862 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44193 | 162 神宝「サラマンダーシールド」 | (8.000, 391.905) | `down_fast` | 558/28 | -5.109/-5.109 | 0f/12f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 49861 | 166 神宝「ライフスプリングインフィニティ」 | (188.893, 388.669) | `stay` | 288/52 | -4.346/-4.346 | 0f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51085 | 166 神宝「ライフスプリングインフィニティ」 | (8.000, 432.000) | `stay` | 280/52 | -2.499/-11.885 | 0f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 51672 | 166 神宝「ライフスプリングインフィニティ」 | (8.000, 432.000) | `up_fast` | 297/52 | -2.439/-2.439 | 0f/7f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52222 | 166 神宝「ライフスプリングインフィニティ」 | (321.208, 360.287) | `right_fast` | 455/52 | -4.273/-4.273 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 52915 | 166 神宝「ライフスプリングインフィニティ」 | (20.000, 411.570) | `down_right_fast` | 483/52 | -2.885/-2.885 | 0f/4f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 53471 | 166 神宝「ライフスプリングインフィニティ」 | (376.000, 432.000) | `up_left_fast` | 265/52 | -1.905/-1.905 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56256 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (162.670, 432.000) | `up_fast` | 336/0 | -5.903/-5.903 | 10f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 56886 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (21.011, 432.000) | `up_right_fast` | 558/0 | -1.300/-1.300 | 0f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 57731 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (56.385, 432.000) | `down_fast` | 577/0 | -2.999/-2.999 | 0f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 58241 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (72.215, 384.857) | `up_right_fast` | 564/0 | -1.329/-1.329 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59154 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 425.100) | `up_left_fast` | 594/0 | -1.307/-1.453 | 3f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 59681 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (8.000, 432.000) | `down_fast` | 569/0 | -2.358/-2.358 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 61081 | 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | (107.469, 236.075) | `left_fast` | 589/0 | -2.989/-4.260 | 13f/19f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 64086 | 174 「永夜返し  -待宵-」 | (376.000, 432.000) | `left_fast` | 918/0 | -3.694/-3.694 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 66639 | 178 「永夜返し  -子の四つ-」 | (28.485, 432.000) | `up_right_fast` | 1001/0 | -2.808/-3.575 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 72128 | 186 「永夜返し  -寅の四つ-」 | (233.164, 423.442) | `down_right_fast` | 1534/0 | -1.556/-1.556 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 6800 | 6572 | 2961 | 0 | 3547 | 1125 | 95.319 | 0.089 |
| 150 薬符「壺中の大銀河」 | 4 | 737 | 717 | 300 | 0 | 414 | 138 | 213.605 | 0.096 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 2 | 768 | 753 | 312 | 0 | 404 | 183 | 142.578 | 0.176 |
| 158 神宝「ブディストダイアモンド」 | 1 | 1295 | 1290 | 735 | 0 | 478 | 260 | 47.496 | 0.300 |
| 162 神宝「サラマンダーシールド」 | 1 | 1062 | 1056 | 603 | 0 | 447 | 214 | 76.130 | 0.113 |
| 166 神宝「ライフスプリングインフィニティ」 | 6 | 1319 | 1310 | 394 | 0 | 822 | 246 | 156.968 | 0.178 |
| 170 神宝「蓬莱の玉の枝  -夢色の郷-」 | 7 | 1833 | 1816 | 827 | 0 | 981 | 312 | 85.916 | 0.152 |
| 174 「永夜返し  -待宵-」 | 1 | 248 | 236 | 95 | 0 | 122 | 38 | 86.576 | 0.062 |
| 178 「永夜返し  -子の四つ-」 | 1 | 213 | 193 | 136 | 0 | 57 | 28 | 59.859 | 0.335 |
| 182 | 0 | 421 | 401 | 327 | 0 | 74 | 62 | 24.193 | 0.249 |
| 186 「永夜返し  -寅の四つ-」 | 1 | 143 | 126 | 72 | 0 | 54 | 19 | 295.546 | 0.073 |
| 190 | 0 | 697 | 679 | 451 | 0 | 228 | 112 | 61.893 | 0.117 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 5 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 18.971 ms median and 37.703 ms p95.
- The full enemy sensor produced 9676 snapshots; capture read time was `{'median': 19.02249999693595, 'p95': 43.636900023557246, 'max': 119.91830001352355}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 14.0}` frames, and 12 phase-counter discontinuities were excluded; 14863 decisions retained at least one robust-union body (maximum 34); 4332 decisions contained latent contact-disabled geometry (maximum 33), and 5013 contained bounded inactive-slot memory (maximum 33). 194 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 10.243732452392578, 'max': 12.592464447021484}` / `{'median': 0.0, 'p95': 10.265533447265625, 'max': 12.592464447021484}` / `{'median': 0.0, 'p95': 0.2732696533203125, 'max': 0.8241424560546875}`.
- The issue-time enemy guard retained 15536 observations, detected 952 during-plan geometry changes, recertified 952 decisions, and overrode 457 actions. Read/recertificate timing was `{'median': 1.7225499905180186, 'p95': 3.6567000206559896, 'max': 38.04489999311045}` / `{'median': 8.386249974137172, 'p95': 19.00759997079149, 'max': 31.147999980021268}` ms; 2377 issue captures contained latent bodies (maximum 33), and 5030 contained dormant bodies (maximum 33).
- The synchronous spell-owner guard retained 14119 observations (12180 contact enabled, 1939 anticipatory, 0 errors). 12661 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 12661, '0x00597600': 1458}`.
- The terminal-threat heuristic covered 15536 decisions with horizon counts `{'0': 79, '10': 14305, '32': 1152}`; it reported 7 collision and 200 sub-safety-clearance warnings, and relaxed 308 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 50, '3': 3121, '4': 9897, '5': 1753, '6': 715}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 71, '3': 6001, '4': 8724, '5': 483, '6': 257}`.
- Adaptive delay supports were `{'2,3': 53, '2,3,4': 233, '2,3,4,5': 1458, '2,3,4,5,6': 1024, '3': 2, '3,4': 398, '3,4,5': 3406, '3,4,5,6': 8740, '4,5,6': 222}`; 575 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 152/613.
- Robust viability supplied 15149 available policy queries (0 had new delay support outside the cached policy), constrained 7628 decisions, and exposed 7213 empty queried action sets. Recovery guidance was available/selected on 1828/1048 empty-kernel queries; distant-kernel guidance was available/selected on 4665/4476. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 2.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 10.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 336.0, 'max': 522.3944869540643}`, and `{'median': 0.0, 'p95': 22.60529136657715, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2402, '1': 2135, '2': 1917, '3': 1589, '4': 1785, '5': 1794, '6': 1779, '7': 1748}`.
- Global-horizon/local-prefix cross-tab covered 11404 decisions: 3 had a winning global state but unsafe selected prefix, 5778 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 116 selected actions were outside the reported winning set. 705 newer issue-time hazard versions and 4 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 2737 unique policies with solve-time statistics `{'median': 97.40960004273802, 'p95': 418.13089995412156, 'max': 569.1354000009596}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1800.0}`. Policy status counts were `{'pending_future_epoch': 45, 'queryable': 15150, 'expired': 54}`; 100 robust-mode decisions had no query.
- Of 8046 unambiguous output transitions, 6903 (0.858) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 31}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 27 hit windows with a positive warning lead; those leads were `[0, 0, 0, 31, 21, 3, 18, 9, 12, 5, 0, 10, 6, 9, 12, 4, 6, 7, 9, 4, 10, 18, 19, 16, 9, 15, 15, 19, 3, 9, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.283 during the 60 frames preceding a hit versus 0.129 outside those windows.
- Mean selected control-reserve deficit was 11.354 during the 60 frames preceding a hit versus 5.934 outside those windows.
- Soft recovery was selected on 0.055 of alive decisions in the 60-frame pre-hit windows versus 0.066 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 14.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Offline Belief Upper-Certificate Replay

This instrumented run retained ignored viability capsules. The live
Boolean/local controller remained authoritative; belief lower labels and
upper certificates were replayed only after the game exited.

The deterministic cohort selected the available root closest to 30 frames
before each of the 31 hits plus one stratified non-hit root, then reconstructed
a 32-frame exact observed/pending-input problem with cadence `(4,5,6)`.

- Uncapped: 31/32 roots certified, one root retained eight unresolved
  actions, and 30/31 pre-hit roots certified. Certificate median/p95/max was
  `0.039/88.33/1907.33 ms`.
- 100-ms anytime: 29/32 roots certified; the same eight-action gap remained;
  two expired roots conservatively returned all 17 actions unresolved.
  Certificate median/p95/max was `0.040/91.59/100.18 ms`.
- The trace Boolean policy was already losing at 28/31 sampled pre-hit roots.
  All three trace-viable pre-hit roots had a complete 32-frame attainable
  lower label.

Therefore selective upper certification removes routine complete-upper work
but does not remove unrestricted growth on every margin-only root. The
deadline contract converts that tail into explicit uncertainty. The physical
priority remains earlier prevention of global-kernel collapse, followed by
targeted refinement of only unresolved actions.

Compact evidence:
`artifacts/viability_audit/stage6b_20260725_204521_belief_upper_certification.json`
and
`artifacts/viability_audit/stage6b_20260725_204521_belief_upper_certification_uncapped.json`.
