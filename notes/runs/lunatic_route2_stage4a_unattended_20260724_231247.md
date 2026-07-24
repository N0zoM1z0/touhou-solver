# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_231247

## Scope And Integrity

- Session status: **discarded** (`external_stop`). This is an intentionally
  truncated shadow Boss-telemetry capture, not a completed phase/stage
  baseline.
- Valid practice scope: `2..13840` (3094 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 10, at `[1006, 1805, 3980, 4301, 9395, 11500, 11936, 12507, 13118, 13513]`.
- Hard no-Bomb verification: **PASS** across 3094 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1006-T1`. It occurred during a nonspell phase at player (16.132, 416.126), with 218 bullets and 0 lasers. The projectile model reported pipeline clearance 2.702.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 9
- `fast_mode`: 5
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1006 | nonspell | (16.132, 416.126) | `up_right_fast` | 218/0 | 2.702/2.702 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1805 | nonspell | (77.687, 432.000) | `up_right` | 472/0 | -3.085/-3.085 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3980 | nonspell | (254.631, 432.000) | `right_fast` | 873/0 | -10.266/-11.766 | 4f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4301 | nonspell | (376.000, 403.807) | `up_right` | 843/0 | -0.110/-2.717 | 0f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9395 | nonspell | (8.422, 424.000) | `up` | 421/0 | -3.098/-3.098 | 4f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11500 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 462/0 | -0.648/-0.648 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11936 | 57 夢境「二重大結界」 | (8.000, 432.000) | `stay` | 578/0 | -0.574/-0.574 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12507 | 57 夢境「二重大結界」 | (376.000, 432.000) | `up_left_fast` | 577/0 | -0.651/-0.651 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13118 | 57 夢境「二重大結界」 | (369.079, 432.000) | `right` | 626/0 | -2.234/-2.234 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13513 | 57 夢境「二重大結界」 | (376.000, 421.817) | `up_right_fast` | 618/0 | -1.938/-1.938 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 2221 | 2165 | 1147 | 0 | 1012 | 375 | 105.094 | 0.130 |
| 57 夢境「二重大結界」 | 5 | 873 | 867 | 128 | 0 | 725 | 149 | 208.801 | 0.300 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 5.000 frames p95. The local plan took 20.000 ms median and 37.479 ms p95.
- The full enemy sensor produced 1961 snapshots; capture read time was `{'median': 21.338899998227134, 'p95': 47.17760000494309, 'max': 99.31479999795556}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 13.0}` frames, and 2 phase-counter discontinuities were excluded; 2764 decisions retained at least one robust-union body (maximum 59); 1108 decisions contained latent contact-disabled geometry (maximum 59), and 1425 contained bounded inactive-slot memory (maximum 53). 154 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.832151412963867, 'p95': 4.142120361328125, 'max': 4.600006103515625}` / `{'median': 2.93157958984375, 'p95': 3.898770570755005, 'max': 5.5}` / `{'median': 0.5097999572753906, 'p95': 3.004601160685221, 'max': 9.100006103515625}`.
- The issue-time enemy guard retained 3094 observations, detected 904 during-plan geometry changes, recertified 904 decisions, and overrode 456 actions. Read/recertificate timing was `{'median': 1.9271999772172421, 'p95': 3.9781000232324004, 'max': 22.81090000178665}` / `{'median': 7.676049994188361, 'p95': 15.541000000666827, 'max': 27.920400025323033}` ms; 1109 issue captures contained latent bodies (maximum 59), and 1428 contained dormant bodies (maximum 53).
- The synchronous spell-owner guard retained 1575 observations (1575 contact enabled, 0 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1575}`.
- The terminal-threat heuristic covered 3094 decisions with horizon counts `{'0': 45, '10': 2841, '32': 208}`; it reported 9 collision and 40 sub-safety-clearance warnings, and relaxed 20 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 48, '3': 278, '4': 2222, '5': 478, '6': 68}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 40, '3': 315, '4': 2587, '5': 152}`.
- Adaptive delay supports were `{'1,2,3': 25, '1,2,3,4': 22, '2,3': 51, '2,3,4': 54, '2,3,4,5': 87, '2,3,4,5,6': 162, '3,4': 27, '3,4,5': 114, '3,4,5,6': 2552}`; 480 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 50/219.
- Robust viability supplied 3032 available policy queries (0 had new delay support outside the cached policy), constrained 1737 decisions, and exposed 1275 empty queried action sets. Recovery guidance was available/selected on 310/185 empty-kernel queries; distant-kernel guidance was available/selected on 854/821. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 7.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 41.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.0, 'p95': 337.5203697556638, 'max': 499.85597925802585}`, and `{'median': 0.0, 'p95': 24.0, 'max': 43.40000009536743}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 436, '1': 446, '2': 387, '3': 332, '4': 352, '5': 361, '6': 366, '7': 352}`.
- Global-horizon/local-prefix cross-tab covered 1416 decisions: 0 had a winning global state but unsafe selected prefix, 548 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 3 selected actions were outside the reported winning set. 665 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 524 unique policies with solve-time statistics `{'median': 160.16975001548417, 'p95': 439.66840000939555, 'max': 533.9774000167381}` and first-observed ages `{'median': 3.0, 'p95': 9.0, 'max': 1787.0}`. Policy status counts were `{'pending_future_epoch': 29, 'queryable': 3034, 'expired': 11}`; 42 robust-mode decisions had no query.
- Of 1686 unambiguous output transitions, 1380 (0.819) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[0, 10, 10, 5, 7, 7, 8, 3, 3, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.490 during the 60 frames preceding a hit versus 0.136 outside those windows.
- Mean selected control-reserve deficit was 5.048 during the 60 frames preceding a hit versus 1.297 outside those windows.
- Soft recovery was selected on 0.098 of alive decisions in the 60-frame pre-hit windows versus 0.051 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
