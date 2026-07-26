# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260726_211210

## Scope And Integrity

- Valid practice scope: `3..42059` (12726 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 7, at `[3296, 4004, 12913, 13294, 30079, 33658, 35440]`.
- Hard no-Bomb verification: **PASS** across 12726 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F3296-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 100 bullets and 0 lasers. The projectile model reported pipeline clearance -1.715.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 1 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 5
- `playfield_boundary`: 4
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3296 | nonspell | (376.000, 432.000) | `up_left_fast` | 100/0 | -1.715/-1.715 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4004 | nonspell | (376.000, 427.100) | `right_fast` | 450/0 | -1.735/-1.735 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12913 | 56 夢境「二重大結界」 | (15.882, 432.000) | `up_fast` | 538/0 | -1.320/-1.320 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13294 | 56 夢境「二重大結界」 | (371.400, 414.605) | `down_left_fast` | 546/0 | 0.572/-1.584 | 3f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30079 | 64 神技「八方鬼縛陣」 | (52.347, 384.862) | `up_left` | 910/0 | -12.977/-12.977 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33658 | nonspell | (74.012, 413.849) | `left_fast` | 100/0 | -2.274/-2.274 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35440 | 68 回霊「夢想封印　侘」 | (8.000, 429.700) | `up` | 546/0 | -3.098/-3.098 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 7438 | 7294 | 3193 | 0 | 4046 | 884 | 142.447 | 0.129 |
| 56 夢境「二重大結界」 | 2 | 1180 | 1174 | 261 | 0 | 884 | 170 | 238.033 | 0.386 |
| 60 | 0 | 937 | 925 | 160 | 0 | 749 | 115 | 189.189 | 0.080 |
| 64 神技「八方鬼縛陣」 | 1 | 998 | 986 | 890 | 0 | 96 | 129 | 56.433 | 0.234 |
| 68 回霊「夢想封印　侘」 | 1 | 1202 | 1195 | 599 | 0 | 594 | 171 | 121.944 | 0.088 |
| 72 | 0 | 971 | 948 | 428 | 0 | 501 | 147 | 133.556 | 0.052 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 12.155 ms median and 21.486 ms p95.
- The full enemy sensor produced 6391 snapshots; capture read time was `{'median': 8.401500002946705, 'p95': 24.76669999305159, 'max': 50.584099953994155}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 10.0}` frames, and 6 phase-counter discontinuities were excluded; 12354 decisions retained at least one robust-union body (maximum 58); 2742 decisions contained latent contact-disabled geometry (maximum 58), and 6467 contained bounded inactive-slot memory (maximum 52). 98 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.2529067993164062, 'p95': 4.118438720703125, 'max': 4.54547119140625}` / `{'median': 2.390542984008789, 'p95': 3.8505539894104004, 'max': 3.994140625}` / `{'median': 0.6467084884643555, 'p95': 1.997538447380066, 'max': 1.9999996423721313}`.
- The issue-time enemy guard retained 12726 observations, detected 2417 during-plan geometry changes, recertified 2417 decisions, and overrode 30 actions. Read/recertificate timing was `{'median': 1.8321499810554087, 'p95': 3.48030001623556, 'max': 15.668499981984496}` / `{'median': 2.1717000054195523, 'p95': 4.703500017058104, 'max': 16.833500005304813}` ms; 2742 issue captures contained latent bodies (maximum 58), and 6471 contained dormant bodies (maximum 52). Fresh/global transactions preserved 2387/2417 planned actions, relaxed 10 fresh/global empty intersections, inherited 18 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9585 observations (9540 contact enabled, 45 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9585}`.
- The terminal-threat heuristic covered 12726 decisions with horizon counts `{'0': 62, '10': 11760, '32': 904}`; it reported 12 collision and 176 sub-safety-clearance warnings, and relaxed 121 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 734, '3': 10972, '4': 1020}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 4542, '3': 7917, '4': 267}`.
- Adaptive delay supports were `{'1,2': 56, '1,2,3': 58, '1,2,3,4': 131, '1,2,3,4,5,6': 2, '2,3': 764, '2,3,4': 6365, '2,3,4,5': 3736, '2,3,4,5,6': 1613, '3,4': 1}`; 45 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 37/251.
- Robust viability supplied 12522 available policy queries (0 had new delay support outside the cached policy), constrained 6870 decisions, and exposed 5531 empty queried action sets. Recovery guidance was available/selected on 1495/685 empty-kernel queries; distant-kernel guidance was available/selected on 3407/3281. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 3.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 15.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 113.13708498984761, 'p95': 336.3807366660582, 'max': 466.47615158762403}`, and `{'median': 0.0, 'p95': 16.0, 'max': 40.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1946, '1': 1639, '2': 1399, '3': 1555, '4': 1510, '5': 1483, '6': 1531, '7': 1459}`.
- Global-horizon/local-prefix cross-tab covered 9208 decisions: 4 had a winning global state but unsafe selected prefix, 3587 had a losing global state but safe short prefix, 3 selected globally certified actions contradicted the fresh local prefix checker, and 71 selected actions were outside the reported winning set. 2179 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1616 unique policies with solve-time statistics `{'median': 145.07584998500533, 'p95': 421.7062999960035, 'max': 556.4910999964923}` and first-observed ages `{'median': 2.0, 'p95': 8.0, 'max': 1802.0}`. Policy status counts were `{'pending_future_epoch': 52, 'queryable': 12523, 'expired': 24}`; 77 robust-mode decisions had no query.
- Of 6711 unambiguous output transitions, 6139 (0.915) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[5, 4, 3, 8, 0, 4, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.259 during the 60 frames preceding a hit versus 0.142 outside those windows.
- Mean selected control-reserve deficit was 8.312 during the 60 frames preceding a hit versus 4.078 outside those windows.
- Soft recovery was selected on 0.029 of alive decisions in the 60-frame pre-hit windows versus 0.054 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 69.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
