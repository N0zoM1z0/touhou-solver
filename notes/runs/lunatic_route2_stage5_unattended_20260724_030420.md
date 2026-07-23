# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_030420

## Scope And Integrity

- Valid practice scope: `2..43536` (10428 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 24, at `[2063, 4395, 10983, 11717, 14174, 20513, 22142, 25044, 29745, 30220, 30842, 31350, 34090, 34628, 35015, 37133, 37657, 38183, 38794, 39552, 40431, 41729, 42584, 43258]`.
- Hard no-Bomb verification: **PASS** across 10428 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2063-T1`. It occurred during a nonspell phase at player (363.615, 429.627), with 555 bullets and 0 lasers. The projectile model reported pipeline clearance -0.100.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 9 |
| `sensor_gap_or_unmodeled_hazard` | 4 |
| `enemy_body_contact_candidate` | 1 |

Contributing factors:

- `fast_mode`: 9
- `corridor_deadline_miss`: 8
- `playfield_boundary`: 7
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2063 | nonspell | (363.615, 429.627) | `up_left` | 555/0 | -0.100/-3.104 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4395 | nonspell | (102.263, 425.861) | `down_left_fast` | 451/0 | -3.866/-3.866 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10983 | nonspell | (346.306, 387.320) | `left_fast` | 886/0 | 10.901/-1.788 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11717 | nonspell | (33.818, 423.966) | `stay` | 898/0 | 10.270/3.644 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14174 | nonspell | (12.338, 424.913) | `up_right_fast` | 292/0 | -4.138/-4.138 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20513 | nonspell | (187.301, 419.786) | `left_fast` | 378/0 | -3.103/-3.103 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22142 | nonspell | (164.904, 370.261) | `left_fast` | 438/0 | -0.318/-3.956 | 3f/29f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 25044 | 103 幻波「赤眼催眠(マインドブローイング)」 | (127.823, 427.551) | `up_right` | 1077/0 | -3.472/-3.472 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29745 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (51.108, 430.225) | `up` | 995/0 | -8.090/-8.090 | 4f/12f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30220 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (195.590, 419.564) | `up_left_fast` | 1000/0 | -2.627/-8.432 | 20f/112f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30842 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (21.177, 428.384) | `up` | 1012/0 | -7.209/-7.209 | 17f/25f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31350 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (145.906, 94.546) | `up_left` | 991/0 | 10.951/-5.144 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34090 | nonspell | (374.328, 367.680) | `left` | 397/0 | -3.125/-3.125 | 2f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 34628 | nonspell | (169.868, 428.823) | `stay` | 495/0 | -2.334/-2.334 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35015 | nonspell | (246.675, 376.837) | `left_fast` | 452/0 | -3.026/-4.057 | 0f/16f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 37133 | nonspell | (37.166, 403.694) | `down_left_fast` | 460/0 | 0.810/-2.165 | 3f/17f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37657 | 111 懶惰「生神停止(マインドストッパー)」 | (188.789, 224.112) | `stay` | 241/0 | -1.597/-1.744 | 4f/17f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38183 | 111 懶惰「生神停止(マインドストッパー)」 | (184.726, 103.398) | `down` | 458/0 | 56.451/44.296 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 38794 | 111 懶惰「生神停止(マインドストッパー)」 | (192.564, 222.692) | `left` | 337/0 | -3.456/-3.456 | 0f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39552 | 111 懶惰「生神停止(マインドストッパー)」 | (206.016, 229.824) | `down_left` | 336/0 | -3.048/-3.048 | 5f/17f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 40431 | 115 散符「真実の月(インビジブルフルムーン)」 | (179.475, 118.213) | `down_fast` | 0/0 | 9999.000/1.050 | 0f/0f | `enemy_body_contact_candidate` | `unresolved_planner_failure` |
| discovery | 41729 | 115 散符「真実の月(インビジブルフルムーン)」 | (371.744, 414.212) | `stay` | 1202/0 | -3.151/-3.151 | 3f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 42584 | 115 散符「真実の月(インビジブルフルムーン)」 | (374.208, 393.180) | `left` | 1034/0 | -2.029/-2.029 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 43258 | 115 散符「真実の月(インビジブルフルムーン)」 | (11.854, 420.906) | `stay` | 1179/0 | -2.653/-2.653 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 11 | 6264 | 6077 | 3067 | 130 | 2966 | 375 | 294.568 | 0.225 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 1001 | 962 | 541 | 0 | 421 | 61 | 351.723 | 0.413 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 977 | 963 | 833 | 18 | 130 | 63 | 269.613 | 0.149 |
| 111 懶惰「生神停止(マインドストッパー)」 | 4 | 1092 | 1071 | 267 | 0 | 804 | 63 | 291.621 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 4 | 1094 | 1058 | 655 | 0 | 403 | 64 | 238.242 | 0.352 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 16.362 ms median and 31.369 ms p95.
- The full enemy sensor produced 1826 snapshots; capture read time was `{'median': 16.643900002236478, 'p95': 26.878599979681894, 'max': 49.22040001838468}`, snapshot age was `{'median': 11.0, 'p95': 19.0, 'max': 25.0}` frames, and 8 phase-counter discontinuities were excluded; 239 decisions retained at least one contact-enabled body (maximum 35).
- Modeled action hold counts were `{'2': 55, '3': 2188, '4': 8136, '5': 49}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 1, '2': 11, '3': 3817, '4': 6599}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3': 29, '1,2,3,4': 42, '1,2,3,4,5': 31, '2,3': 1, '2,3,4': 586, '2,3,4,5': 2505, '2,3,4,5,6': 5527, '3,4': 55, '3,4,5': 146, '3,4,5,6': 1505}`; 429 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 88/595.
- Robust viability supplied 10131 available policy queries (148 had new delay support outside the cached policy), constrained 4724 decisions, and exposed 5363 empty queried action sets. Recovery guidance was available/selected on 738/400 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 1.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 626 unique policies with solve-time statistics `{'median': 291.40935000032187, 'p95': 422.07929998403415, 'max': 509.30990002234466}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 1786.0}`. Policy status counts were `{'pending_future_epoch': 126, 'queryable': 10132, 'expired': 74}`; 201 robust-mode decisions had no query.
- Of 5410 unambiguous output transitions, 4642 (0.858) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12, 'robust_action_set_exhausted_before_hit': 10, 'unresolved_planner_failure': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[10, 11, 0, 0, 6, 6, 29, 8, 12, 112, 25, 0, 9, 10, 16, 17, 17, 0, 13, 17, 0, 9, 10, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.220 during the 60 frames preceding a hit versus 0.235 outside those windows.
- Soft recovery was selected on 0.034 of alive decisions in the 60-frame pre-hit windows versus 0.041 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Causal Review

- The 16-frame asynchronous sensor passed its latency gate. Relative to the
  synchronous full-pool run `20260724_023923`, total read median fell from
  24.91 to 12.03 ms, cadence p95 fell from five to four frames, and available
  policy queries rose from 7,920 to 10,131. It is close to the pre-sensor
  `20260724_022420` baseline of 11.10 ms read median and four-frame cadence
  p95.
- The sensor retained 1,826 unique snapshots. Operational snapshot age was
  11/19/25 frames at median/p95/max after excluding eight phase-counter
  discontinuities; capture read time was 16.64/26.88/49.22 ms. Contact-enabled
  bodies appeared in 239 decisions, with a maximum of 35 simultaneous bodies.
- Hits increased from 18 to 24 against the last complete trial. The native RNG
  seed and phase durations differed, so this rejects an aggregate survival
  improvement claim but does not causally indict asynchronous sensing. Only
  2.3 percent of decisions contained bodies, while 19 of 24 hits were already
  classified as observed bullets or committed-prefix bullet collisions.
- The surviving general defect is long-range hazard incompleteness: twelve hit
  windows had already left the global viability kernel, and four hits still
  had no current bullet/laser/body witness. Present-state pool scans cannot
  predict future ECL spawns or contact-bit activation.
- The generated comparison was rebuilt against complete run `20260724_023923`.
  The supervisor now excludes discarded/failed sessions when selecting a
  baseline, preventing partial latency experiments from corrupting future
  comparisons.
