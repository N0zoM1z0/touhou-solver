# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_133633

## Scope And Integrity

- Valid practice scope: `1..44822` (13304 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 23, at `[4027, 10523, 11024, 12524, 12943, 13833, 14407, 22898, 23551, 24208, 28226, 29418, 30731, 32554, 32956, 35817, 37541, 39344, 40277, 42363, 42982, 43515, 44100]`.
- Hard no-Bomb verification: **PASS** across 13304 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F4027-T1`. It occurred during a nonspell phase at player (8.000, 415.609), with 715 bullets and 0 lasers. The projectile model reported pipeline clearance -1.459.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 13 |
| `observed_bullet_overlap` | 10 |

Contributing factors:

- `fast_mode`: 21
- `playfield_boundary`: 16
- `pool_density_over_1000`: 7
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4027 | nonspell | (8.000, 415.609) | `down_right_fast` | 715/0 | -1.459/-1.459 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10523 | nonspell | (22.228, 412.000) | `up` | 893/0 | -16.448/-16.448 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11024 | nonspell | (281.377, 388.000) | `up_fast` | 892/0 | -1.379/-21.355 | 33f/39f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12524 | nonspell | (8.000, 432.000) | `up_fast` | 256/0 | -2.550/-2.550 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12943 | nonspell | (8.000, 431.992) | `down_right_fast` | 121/0 | -2.173/-2.173 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13833 | nonspell | (376.000, 417.022) | `down_right_fast` | 450/0 | 0.145/-1.302 | 2f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14407 | nonspell | (376.000, 424.000) | `up_fast` | 488/0 | -2.399/-2.399 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22898 | 103 幻波「赤眼催眠(マインドブローイング)」 | (134.411, 432.000) | `right_fast` | 973/0 | -1.254/-1.499 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23551 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 853/0 | -3.630/-3.630 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24208 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 424.000) | `up_fast` | 860/0 | 2.448/-2.046 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28226 | nonspell | (364.044, 425.172) | `up_left_fast` | 1081/0 | -0.373/-1.382 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29418 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (176.884, 364.169) | `up_fast` | 989/0 | -6.254/-6.261 | 31f/62f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30731 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (155.285, 432.000) | `up_left` | 1017/0 | -5.421/-8.003 | 8f/20f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32554 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (356.285, 432.000) | `up_right_fast` | 1020/0 | -5.432/-7.088 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32956 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (185.766, 432.000) | `left_fast` | 1024/0 | -5.991/-5.991 | 27f/64f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35817 | nonspell | (13.657, 426.343) | `up_right_fast` | 475/0 | 0.324/-2.805 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37541 | nonspell | (8.000, 432.000) | `up_right_fast` | 416/0 | -3.623/-3.623 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39344 | 111 懶惰「生神停止(マインドストッパー)」 | (185.365, 198.974) | `left_fast` | 384/0 | -2.012/-5.705 | 2f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40277 | 111 懶惰「生神停止(マインドストッパー)」 | (195.945, 59.536) | `right_fast` | 489/0 | -2.292/-2.414 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42363 | 115 散符「真実の月(インビジブルフルムーン)」 | (15.262, 428.000) | `up_right_fast` | 1153/0 | 1.508/-7.113 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42982 | 115 散符「真実の月(インビジブルフルムーン)」 | (206.333, 432.000) | `up_left_fast` | 884/0 | -1.721/-8.888 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43515 | 115 散符「真実の月(インビジブルフルムーン)」 | (191.457, 432.000) | `up_left_fast` | 1075/0 | -3.214/-3.214 | 3f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44100 | 115 散符「真実の月(インビジブルフルムーン)」 | (272.691, 432.000) | `up_left_fast` | 1075/0 | -2.592/-4.388 | 7f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 8564 | 8433 | 5892 | 0 | 2518 | 1093 | 122.263 | 0.214 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 3 | 860 | 850 | 276 | 0 | 572 | 138 | 157.853 | 0.275 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 1337 | 1330 | 1110 | 0 | 212 | 274 | 82.009 | 0.375 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1211 | 1204 | 510 | 0 | 683 | 180 | 102.436 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 1332 | 1315 | 506 | 0 | 807 | 185 | 61.759 | 0.198 |

## Interpretation

- Retained witnesses classify 10 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.192 ms median and 23.328 ms p95.
- The full enemy sensor produced 6979 snapshots; capture read time was `{'median': 7.061699987389147, 'p95': 26.1473999125883, 'max': 46.358700026758015}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 12487 decisions retained at least one robust-union body (maximum 42); 4904 decisions contained latent contact-disabled geometry (maximum 41), and 6486 contained bounded inactive-slot memory (maximum 40). 413 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.41998291015625, 'max': 5.307546615600586}` / `{'median': 0.0, 'p95': 4.419981002807617, 'max': 4.707546710968018}` / `{'median': 0.0, 'p95': 1.0000190734863281, 'max': 5.70399284362793}`.
- The issue-time enemy guard retained 13304 observations, detected 2619 during-plan geometry changes, recertified 2619 decisions, and overrode 64 actions. Read/recertificate timing was `{'median': 1.7518000677227974, 'p95': 3.398000029847026, 'max': 13.528799987398088}` / `{'median': 3.2214000821113586, 'p95': 6.423200014978647, 'max': 18.89169996138662}` ms; 4879 issue captures contained latent bodies (maximum 41), and 6485 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2555/2619 planned actions, relaxed 6 fresh/global empty intersections, inherited 11 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9702 observations (9675 contact enabled, 27 anticipatory, 0 errors). 9702 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9702}`.
- The terminal-threat heuristic covered 13304 decisions with horizon counts `{'0': 73, '10': 13098, '32': 133}`; it reported 1 collision and 41 sub-safety-clearance warnings, and relaxed 46 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1298, '3': 10272, '4': 1501, '5': 233}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 65, '2': 4088, '3': 7446, '4': 1705}`.
- Adaptive delay supports were `{'1,2': 19, '1,2,3': 99, '1,2,3,4': 243, '1,2,3,4,5,6': 11, '2': 8, '2,3': 781, '2,3,4': 5831, '2,3,4,5': 3327, '2,3,4,5,6': 2029, '3,4': 8, '3,4,5': 81, '3,4,5,6': 867}`; 158 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 38/230.
- Robust viability supplied 13132 available policy queries (0 had new delay support outside the cached policy), constrained 4792 decisions, and exposed 8294 empty queried action sets. Recovery guidance was available/selected on 1116/505 empty-kernel queries; distant-kernel guidance was available/selected on 6744/6508. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 143.10835055998655, 'p95': 337.5203697556638, 'max': 489.76729168044693}`, and `{'median': 0.0, 'p95': 20.7473087310791, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2038, '1': 1744, '2': 1385, '3': 1589, '4': 1508, '5': 1629, '6': 1624, '7': 1615}`.
- Global-horizon/local-prefix cross-tab covered 8174 decisions: 5 had a winning global state but unsafe selected prefix, 5165 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 19 selected actions were outside the reported winning set. 1936 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1870 unique policies with solve-time statistics `{'median': 101.9759500049986, 'p95': 317.69970001187176, 'max': 431.8190000485629}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1807.0}`. Policy status counts were `{'pending_future_epoch': 80, 'queryable': 13133, 'expired': 25}`; 106 robust-mode decisions had no query.
- Of 6554 unambiguous output transitions, 6008 (0.917) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 23}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 21 hit windows with a positive warning lead; those leads were `[6, 0, 39, 4, 3, 9, 5, 7, 6, 6, 4, 62, 20, 11, 64, 5, 8, 12, 9, 0, 5, 6, 14]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.502 during the 60 frames preceding a hit versus 0.196 outside those windows.
- Mean selected control-reserve deficit was 10.097 during the 60 frames preceding a hit versus 3.993 outside those windows.
- Soft recovery was selected on 0.015 of alive decisions in the 60-frame pre-hit windows versus 0.036 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact G3/G4 Pre-Hit Loss Audit

- `--viability-audit` retained 1,879 readable capsules totaling 104,461,318
  bytes. Their sorted `SHA-256 basename` manifest digest is
  `065b7da853125239f1389dc1077f562199da1509ace886c7474db25cee43779f`.
- After 24 earlier recovered loss episodes, the exact canonical bracket is
  decision/query `3750/3749 viable -> 3752/3751 losing`. First contact is
  frame 4027, 275 frames later.
- Both roots complete all 36 no-Bomb root actions against all 36 stationary
  continuations. Worst paths replay and scalar/native mismatches are zero.
- G4 issued mask `0x55` retains 30 frames while best `0x10/0x11` retain 32.
  G3 issued `0x85` retains 22 while best `0x20/0x21` retain 32.
- Both roots have unseen-future-hazard coverage `UNKNOWN` from the first
  successor. This passes the finite-model implementation gate only; physical
  survival and strategy promotion remain unavailable.
- Report internal/file digests are
  `8a1efd3ecaf38f215c9a739befef674e95ae83de4a723cd27c0a8707c2678a2b` /
  `122db4b26be6f36416a3eb69e72c88faeae195c77a784265bd9696d20502aa1e`.
  Raw trace SHA-256 is
  `5a40e13e0979fc484f41147e15730c23ebf4876e463e1428fc4ac9ad80fc9bdd`.

## Artifact Serialization Correction

The immutable raw trace contains 9,104 historical `-Infinity` lane sentinels
and is not rewritten. Its derived summary/session originally repeated 98 such
sentinels; these two compact artifacts were mechanically normalized to JSON
`null`, and all retained compact JSON now passes a strict parser. CE-0159
changes future trace and compact publication boundaries only; it does not
change this run's controller actions or give the contaminated run timing
authority.
