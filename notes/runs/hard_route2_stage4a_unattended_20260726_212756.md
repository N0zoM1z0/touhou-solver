# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260726_212756

## Scope And Integrity

- Valid practice scope: `1..43052` (13438 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 6, at `[10590, 12270, 12903, 20855, 36138, 36840]`.
- Hard no-Bomb verification: **PASS** across 13438 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F10590-T1`. It occurred during spell 56 `夢境「二重大結界」` at player (13.657, 422.343), with 441 bullets and 0 lasers. The projectile model reported pipeline clearance 0.009.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 4 |
| `modeled_committed_prefix_collision` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 4
- `corridor_deadline_miss`: 2
- `playfield_boundary`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 10590 | 56 夢境「二重大結界」 | (13.657, 422.343) | `up_right_fast` | 441/0 | 0.009/-0.138 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12270 | 56 夢境「二重大結界」 | (37.703, 231.644) | `up_left` | 556/0 | 0.933/-1.713 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 12903 | 56 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 529/0 | -1.010/-1.010 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20855 | nonspell | (370.343, 415.170) | `left_fast` | 152/0 | 2.341/-2.647 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36138 | 68 回霊「夢想封印　侘」 | (244.987, 432.000) | `up_right_fast` | 451/0 | 0.103/-1.537 | 2f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36840 | 68 回霊「夢想封印　侘」 | (12.879, 424.542) | `up_right` | 686/0 | 0.018/-2.942 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 7629 | 7472 | 2698 | 0 | 4716 | 887 | 156.708 | 0.132 |
| 56 夢境「二重大結界」 | 3 | 1233 | 1215 | 219 | 0 | 967 | 168 | 232.994 | 0.210 |
| 60 | 0 | 1299 | 1286 | 331 | 0 | 936 | 159 | 158.714 | 0.176 |
| 64 | 0 | 919 | 904 | 734 | 0 | 170 | 114 | 55.036 | 0.291 |
| 68 回霊「夢想封印　侘」 | 2 | 1262 | 1251 | 466 | 0 | 778 | 172 | 114.047 | 0.127 |
| 72 | 0 | 1096 | 1075 | 547 | 0 | 506 | 170 | 131.341 | 0.051 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 11.686 ms median and 20.830 ms p95.
- The full enemy sensor produced 6704 snapshots; capture read time was `{'median': 7.885750033892691, 'p95': 23.773499997332692, 'max': 51.641799975186586}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 9.0}` frames, and 7 phase-counter discontinuities were excluded; 13025 decisions retained at least one robust-union body (maximum 49); 2725 decisions contained latent contact-disabled geometry (maximum 49), and 6686 contained bounded inactive-slot memory (maximum 45). 28 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 4.145286560058594, 'p95': 5.005729675292969, 'max': 5.1035919189453125}` / `{'median': 4.491515159606934, 'p95': 4.704507827758789, 'max': 4.704509735107422}` / `{'median': 0.39910125732421875, 'p95': 7.79998779296875, 'max': 8.20001220703125}`.
- The issue-time enemy guard retained 13438 observations, detected 2210 during-plan geometry changes, recertified 2210 decisions, and overrode 21 actions. Read/recertificate timing was `{'median': 1.8529499939177185, 'p95': 3.6401000106707215, 'max': 23.176299990154803}` / `{'median': 2.0268000080250204, 'p95': 4.433399997651577, 'max': 13.62929999595508}` ms; 2722 issue captures contained latent bodies (maximum 49), and 6687 contained dormant bodies (maximum 45). Fresh/global transactions preserved 2189/2210 planned actions, relaxed 3 fresh/global empty intersections, inherited 30 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10171 observations (10123 contact enabled, 48 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 10171}`.
- The terminal-threat heuristic covered 13438 decisions with horizon counts `{'0': 72, '10': 12409, '32': 957}`; it reported 16 collision and 130 sub-safety-clearance warnings, and relaxed 135 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1164, '3': 11428, '4': 846}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 60, '2': 6529, '3': 6749, '4': 100}`.
- Adaptive delay supports were `{'1,2': 34, '1,2,3': 150, '1,2,3,4': 216, '1,2,3,4,5': 73, '2,3': 868, '2,3,4': 7015, '2,3,4,5': 3422, '2,3,4,5,6': 1657, '3,4': 1, '3,4,5,6': 1, '4,5,6': 1}`; 34 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 46/244.
- Robust viability supplied 13203 available policy queries (0 had new delay support outside the cached policy), constrained 8073 decisions, and exposed 4995 empty queried action sets. Recovery guidance was available/selected on 1486/725 empty-kernel queries; distant-kernel guidance was available/selected on 3006/2845. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 6.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 31.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 107.33126291998991, 'p95': 339.03392160667346, 'max': 534.7447989461889}`, and `{'median': 0.0, 'p95': 18.95786476135254, 'max': 42.592540979385376}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2008, '1': 1761, '2': 1484, '3': 1606, '4': 1588, '5': 1625, '6': 1549, '7': 1582}`.
- Global-horizon/local-prefix cross-tab covered 10075 decisions: 7 had a winning global state but unsafe selected prefix, 3559 had a losing global state but safe short prefix, 4 selected globally certified actions contradicted the fresh local prefix checker, and 72 selected actions were outside the reported winning set. 2134 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1670 unique policies with solve-time statistics `{'median': 148.2984000176657, 'p95': 420.8664000034332, 'max': 539.641399984248}` and first-observed ages `{'median': 2.0, 'p95': 8.0, 'max': 1811.0}`. Policy status counts were `{'pending_future_epoch': 60, 'queryable': 13202, 'expired': 31}`; 90 robust-mode decisions had no query.
- Of 6710 unambiguous output transitions, 6174 (0.920) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 5, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 5 hit windows with a positive warning lead; those leads were `[6, 0, 4, 6, 10, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.359 during the 60 frames preceding a hit versus 0.144 outside those windows.
- Mean selected control-reserve deficit was 11.794 during the 60 frames preceding a hit versus 4.260 outside those windows.
- Soft recovery was selected on 0.138 of alive decisions in the 60-frame pre-hit windows versus 0.053 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 89.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
