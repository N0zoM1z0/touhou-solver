# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_175715

## Scope And Integrity

- Valid practice scope: `2..20177` (7305 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[6385]`.
- Hard no-Bomb verification: **PASS** across 7305 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S0-F6385-T1`. It occurred during a nonspell phase at player (337.911, 40.561), with 118 bullets and 0 lasers. The projectile model reported pipeline clearance -2.787.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 1 |

Contributing factors:

- `fast_mode`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 6385 | nonspell | (337.911, 40.561) | `down_left_fast` | 118/0 | -2.787/-34.640 | 4f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 4542 | 4442 | 439 | 0 | 3982 | 534 | 159.180 | 0.071 |
| 0 | 0 | 661 | 650 | 154 | 0 | 496 | 79 | 62.784 | 0.095 |
| 4 | 0 | 962 | 954 | 151 | 0 | 795 | 114 | 71.901 | 0.172 |
| 8 | 0 | 1140 | 1130 | 132 | 0 | 985 | 137 | 94.904 | 0.110 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.728 ms median and 17.430 ms p95.
- The full enemy sensor produced 3442 snapshots; capture read time was `{'median': 6.021550012519583, 'p95': 23.617900034878403, 'max': 39.411199977621436}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7068 decisions retained at least one robust-union body (maximum 32); 1005 decisions contained latent contact-disabled geometry (maximum 11), and 3365 contained bounded inactive-slot memory (maximum 22). 24 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.2734169960021973, 'p95': 3.3403167724609375, 'max': 19.616597493489582}` / `{'median': 2.2734168767929077, 'p95': 3.321969985961914, 'max': 5.65277099609375}` / `{'median': 6.377696990966797e-06, 'p95': 0.70001220703125, 'max': 25.269368489583332}`.
- The issue-time enemy guard retained 7305 observations, detected 488 during-plan geometry changes, recertified 488 decisions, and overrode 7 actions. Read/recertificate timing was `{'median': 1.7552999779582024, 'p95': 3.6266999668441713, 'max': 19.682300044223666}` / `{'median': 1.7548000032547861, 'p95': 3.2848999835550785, 'max': 9.70600004075095}` ms; 1011 issue captures contained latent bodies (maximum 11), and 3357 contained dormant bodies (maximum 22). Fresh/global transactions preserved 481/488 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5255 observations (5184 contact enabled, 71 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5255}`.
- The terminal-threat heuristic covered 7305 decisions with horizon counts `{'0': 74, '10': 6807, '32': 424}`; it reported 0 collision and 19 sub-safety-clearance warnings, and relaxed 42 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3744, '3': 3561}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 7105, '3': 177, '4': 12}`.
- Adaptive delay supports were `{'1,2': 11, '1,2,3': 55, '1,2,3,4': 242, '2,3': 1583, '2,3,4': 3679, '2,3,4,5': 1265, '2,3,4,5,6': 470}`; 10 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 15/92.
- Robust viability supplied 7176 available policy queries (0 had new delay support outside the cached policy), constrained 6258 decisions, and exposed 876 empty queried action sets. Recovery guidance was available/selected on 371/234 empty-kernel queries; distant-kernel guidance was available/selected on 505/505. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 13.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 89.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 86.16263691415206, 'p95': 208.61447696648477, 'max': 279.42798714516766}`, and `{'median': 0.0, 'p95': 18.37365436553955, 'max': 24.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1077, '1': 870, '2': 813, '3': 920, '4': 821, '5': 902, '6': 869, '7': 904}`.
- Global-horizon/local-prefix cross-tab covered 6340 decisions: 0 had a winning global state but unsafe selected prefix, 715 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 33 selected actions were outside the reported winning set. 454 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 864 unique policies with solve-time statistics `{'median': 121.30734999664128, 'p95': 309.822199982591, 'max': 396.90110000083223}` and first-observed ages `{'median': 1.5, 'p95': 4.0, 'max': 1786.0}`. Policy status counts were `{'pending_future_epoch': 74, 'queryable': 7177, 'expired': 12}`; 87 robust-mode decisions had no query.
- Of 2747 unambiguous output transitions, 2500 (0.910) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.000 during the 60 frames preceding a hit versus 0.094 outside those windows.
- Mean selected control-reserve deficit was 0.975 during the 60 frames preceding a hit versus 3.164 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.032 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 23.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
