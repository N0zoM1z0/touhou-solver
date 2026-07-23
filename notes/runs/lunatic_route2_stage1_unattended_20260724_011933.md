# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260724_011933

## Scope And Integrity

- Valid practice scope: `2..21008` (6306 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 4, at `[1893, 6874, 14118, 20028]`.
- Hard no-Bomb verification: **PASS** across 6306 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F1893-T1`. It occurred during a nonspell phase at player (370.232, 419.299), with 178 bullets and 0 lasers. The projectile model reported pipeline clearance -3.190.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 3 |
| `modeled_committed_prefix_collision` | 1 |

Contributing factors:

- `fast_mode`: 2
- `playfield_boundary`: 2
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1893 | nonspell | (370.232, 419.299) | `left_fast` | 178/0 | -3.190/-3.190 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 6874 | nonspell | (106.101, 158.574) | `stay` | 213/0 | 0.807/-2.500 | 2f/17f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 14118 | 5 灯符「ファイヤフライフェノメノン」 | (318.280, 428.071) | `left_fast` | 625/0 | 2.429/-1.556 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20028 | 9 蠢符「ナイトバグトルネード」 | (16.485, 428.824) | `stay` | 207/0 | -1.821/-1.821 | 4f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 2 | 3793 | 3637 | 896 | 232 | 2555 | 187 | 264.942 | 0.107 |
| 1 | 0 | 892 | 862 | 514 | 39 | 339 | 42 | 98.911 | 0.263 |
| 5 灯符「ファイヤフライフェノメノン」 | 1 | 748 | 726 | 398 | 51 | 301 | 40 | 167.493 | 0.155 |
| 9 蠢符「ナイトバグトルネード」 | 1 | 873 | 849 | 351 | 14 | 498 | 46 | 204.023 | 0.125 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 15.180 ms median and 31.137 ms p95.
- Modeled action hold counts were `{'2': 154, '3': 4460, '4': 1692}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 738, '3': 5514, '4': 54}`.
- Adaptive delay supports were `{'1,2': 27, '1,2,3': 50, '1,2,3,4': 6, '2,3': 469, '2,3,4': 1403, '2,3,4,5': 2282, '2,3,4,5,6': 2023, '3,4,5,6': 46}`; 37 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 39/354.
- Robust viability supplied 6074 available policy queries (336 had new delay support outside the cached policy), constrained 3693 decisions, and exposed 2159 empty queried action sets. Safe-action count and selected repair-volume statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 14.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 315 unique policies with solve-time statistics `{'median': 220.53279998362996, 'p95': 355.3989000211004, 'max': 398.2356000051368}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1800.0}`. Policy status counts were `{'pending_future_epoch': 138, 'queryable': 6073, 'expired': 40}`; 177 robust-mode decisions had no query.
- Of 2961 unambiguous output transitions, 2507 (0.847) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 2, 'robust_action_set_exhausted_before_hit': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[6, 17, 3, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.348 during the 60 frames preceding a hit versus 0.136 outside those windows.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 4.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
