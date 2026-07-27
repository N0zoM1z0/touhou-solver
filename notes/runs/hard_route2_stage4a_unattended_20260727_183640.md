# TH08 Stage 4A / Reimu No-Bomb Practice Review: hard_route2_stage4a_unattended_20260727_183640

## Scope And Integrity

- Valid practice scope: `2..45392` (15122 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 8, at `[8957, 12004, 12430, 12955, 19187, 29011, 32526, 36193]`.
- Hard no-Bomb verification: **PASS** across 15122 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S3-F8957-T1`. It occurred during a nonspell phase at player (125.566, 432.000), with 176 bullets and 0 lasers. The projectile model reported pipeline clearance -2.343.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 5 |
| `modeled_committed_prefix_collision` | 2 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 7
- `playfield_boundary`: 5
- `corridor_deadline_miss`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 8957 | nonspell | (125.566, 432.000) | `up_right_fast` | 176/0 | -2.343/-9.644 | 10f/14f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12004 | 56 夢境「二重大結界」 | (13.657, 423.753) | `up_fast` | 545/0 | 0.068/-2.126 | 2f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12430 | 56 夢境「二重大結界」 | (29.958, 341.788) | `right` | 552/0 | -3.493/-3.493 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 12955 | 56 夢境「二重大結界」 | (8.000, 427.400) | `up_right_fast` | 526/0 | -1.328/-1.328 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19187 | 60 散霊「夢想封印　寂」 | (48.928, 407.831) | `up_fast` | 227/0 | -15.937/-15.937 | 0f/2f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 29011 | nonspell | (11.253, 44.709) | `down_right_fast` | 114/0 | 1.205/-2.925 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32526 | 64 神技「八方鬼縛陣」 | (214.515, 432.000) | `up_left_fast` | 852/0 | -1.272/-2.954 | 2f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36193 | nonspell | (189.356, 432.000) | `up_right_fast` | 108/0 | -1.293/-2.086 | 2f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 8757 | 8617 | 3124 | 0 | 5438 | 1055 | 130.389 | 0.115 |
| 56 夢境「二重大結界」 | 3 | 1319 | 1312 | 226 | 0 | 1047 | 183 | 183.391 | 0.224 |
| 60 散霊「夢想封印　寂」 | 1 | 1345 | 1337 | 359 | 0 | 967 | 166 | 138.099 | 0.091 |
| 64 神技「八方鬼縛陣」 | 1 | 1285 | 1275 | 1098 | 0 | 135 | 163 | 51.038 | 0.247 |
| 68 | 0 | 1260 | 1253 | 535 | 0 | 709 | 177 | 86.257 | 0.098 |
| 72 | 0 | 1156 | 1146 | 604 | 0 | 528 | 177 | 104.070 | 0.029 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 10.112 ms median and 18.426 ms p95.
- The full enemy sensor produced 7379 snapshots; capture read time was `{'median': 6.274500046856701, 'p95': 23.346800007857382, 'max': 46.765999984927475}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 14712 decisions retained at least one robust-union body (maximum 43); 2847 decisions contained latent contact-disabled geometry (maximum 43), and 7619 contained bounded inactive-slot memory (maximum 39). 88 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.7048569169155385, 'p95': 7.10727194081182, 'max': 17.453258090549046}` / `{'median': 2.831246852874756, 'p95': 3.1998026371002197, 'max': 12.229461669921875}` / `{'median': 1.4692544937133789e-05, 'p95': 4.863706707954407, 'max': 20.13872652583652}`.
- The issue-time enemy guard retained 15122 observations, detected 2401 during-plan geometry changes, recertified 2401 decisions, and overrode 30 actions. Read/recertificate timing was `{'median': 1.7798500193748623, 'p95': 3.6346999695524573, 'max': 21.424999984446913}` / `{'median': 1.893899985589087, 'p95': 3.7400000146590173, 'max': 12.13579997420311}` ms; 2844 issue captures contained latent bodies (maximum 43), and 7610 contained dormant bodies (maximum 39). Fresh/global transactions preserved 2371/2401 planned actions, relaxed 4 fresh/global empty intersections, inherited 17 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 11742 observations (11696 contact enabled, 46 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 11742}`.
- The terminal-threat heuristic covered 15122 decisions with horizon counts `{'0': 73, '10': 14016, '32': 1033}`; it reported 27 collision and 150 sub-safety-clearance warnings, and relaxed 170 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3115, '3': 11550, '4': 457}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 11061, '3': 4048}`.
- Adaptive delay supports were `{'1,2,3': 123, '1,2,3,4': 180, '1,2,3,4,5': 45, '1,2,3,4,5,6': 69, '2,3': 2553, '2,3,4': 8132, '2,3,4,5': 2908, '2,3,4,5,6': 1097, '3,4': 15}`; 44 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 38/218.
- Robust viability supplied 14940 available policy queries (0 had new delay support outside the cached policy), constrained 8824 decisions, and exposed 5946 empty queried action sets. Recovery guidance was available/selected on 1627/764 empty-kernel queries; distant-kernel guidance was available/selected on 3711/3550. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 23.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 112.0, 'p95': 314.350123270216, 'max': 522.3944869540643}`, and `{'median': 0.0, 'p95': 16.0, 'max': 41.55301237106323}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2327, '1': 1869, '2': 1596, '3': 1791, '4': 1798, '5': 1850, '6': 1847, '7': 1862}`.
- Global-horizon/local-prefix cross-tab covered 11307 decisions: 1 had a winning global state but unsafe selected prefix, 4229 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 83 selected actions were outside the reported winning set. 2270 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1921 unique policies with solve-time statistics `{'median': 121.3576000300236, 'p95': 314.61230001877993, 'max': 398.6449000076391}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1795.0}`. Policy status counts were `{'pending_future_epoch': 84, 'queryable': 14940, 'expired': 13}`; 97 robust-mode decisions had no query.
- Of 7527 unambiguous output transitions, 6975 (0.927) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 6, 'late_collision_after_positive_causal_margin': 1, 'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 7 hit windows with a positive warning lead; those leads were `[14, 4, 0, 6, 2, 6, 8, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.241 during the 60 frames preceding a hit versus 0.120 outside those windows.
- Mean selected control-reserve deficit was 9.542 during the 60 frames preceding a hit versus 3.380 outside those windows.
- Soft recovery was selected on 0.134 of alive decisions in the 60-frame pre-hit windows versus 0.049 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 21.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
