# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_230818

## Scope And Integrity

- Valid practice scope: `1..18988` (4207 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 11, at `[1190, 1706, 2093, 4066, 4382, 8900, 11828, 12775, 13223, 13860, 17750]`.
- Hard no-Bomb verification: **PASS** across 4207 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1190-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 264 bullets and 0 lasers. The projectile model reported pipeline clearance -0.084.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 3 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `playfield_boundary`: 9
- `fast_mode`: 8
- `corridor_deadline_miss`: 5
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1190 | nonspell | (376.000, 432.000) | `down_fast` | 264/0 | -0.084/-0.293 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1706 | nonspell | (16.485, 431.205) | `down_fast` | 356/0 | -1.647/-1.647 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2093 | nonspell | (28.968, 432.000) | `down_left_fast` | 380/0 | -1.374/-1.374 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4066 | nonspell | (15.097, 432.000) | `up` | 939/0 | -1.159/-17.535 | 17f/27f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4382 | nonspell | (122.800, 432.000) | `right` | 1138/0 | -1.788/-12.229 | 5f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8900 | nonspell | (8.000, 385.886) | `up_fast` | 436/0 | 0.708/-5.951 | 3f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11828 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 608/0 | -0.891/-0.891 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12775 | 57 夢境「二重大結界」 | (8.000, 416.267) | `up_right_fast` | 603/0 | -1.754/-1.754 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13223 | 57 夢境「二重大結界」 | (24.193, 287.226) | `up_right_fast` | 574/0 | 1.456/1.456 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 13860 | 57 夢境「二重大結界」 | (367.383, 423.515) | `up_left_fast` | 581/0 | 1.230/-1.744 | 4f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 17750 | nonspell | (181.014, 432.000) | `up` | 417/0 | -2.638/-2.638 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 3142 | 3076 | 1357 | 0 | 1677 | 539 | 119.264 | 0.163 |
| 57 夢境「二重大結界」 | 4 | 939 | 932 | 196 | 0 | 720 | 169 | 199.020 | 0.253 |
| 61 | 0 | 126 | 121 | 21 | 0 | 97 | 17 | 205.631 | 0.097 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 19.656 ms median and 35.496 ms p95.
- The full enemy sensor produced 2600 snapshots; capture read time was `{'median': 22.92854999541305, 'p95': 46.53589997906238, 'max': 80.70779999252409}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 3897 decisions retained at least one robust-union body (maximum 43); 1205 decisions contained latent contact-disabled geometry (maximum 40), and 2085 contained bounded inactive-slot memory (maximum 34). 149 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.8148396809895835, 'p95': 4.1105092366536455, 'max': 7.066654205322266}` / `{'median': 2.922031879425049, 'p95': 3.9229581356048584, 'max': 7.066654205322266}` / `{'median': 0.15509683638811111, 'p95': 2.3789150714874268, 'max': 8.699981689453125}`.
- The issue-time enemy guard retained 4207 observations, detected 978 during-plan geometry changes, recertified 978 decisions, and overrode 442 actions. Read/recertificate timing was `{'median': 1.8691000004764646, 'p95': 3.8890999858267605, 'max': 20.82989999325946}` / `{'median': 7.061299998895265, 'p95': 13.016199984122068, 'max': 23.522400006186217}` ms; 1202 issue captures contained latent bodies (maximum 40), and 2077 contained dormant bodies (maximum 34).
- The synchronous spell-owner guard retained 1065 observations (1065 contact enabled, 0 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1065}`.
- The terminal-threat heuristic covered 4207 decisions with horizon counts `{'0': 49, '10': 3721, '32': 437}`; it reported 4 collision and 66 sub-safety-clearance warnings, and relaxed 61 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 53, '3': 305, '4': 3577, '5': 272}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 46, '3': 346, '4': 3814, '5': 1}`.
- Adaptive delay supports were `{'2,3': 3, '2,3,4': 70, '2,3,4,5': 182, '2,3,4,5,6': 438, '3,4': 11, '3,4,5': 99, '3,4,5,6': 3394, '4,5,6': 9, '5,6': 1}`; 480 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 43/222.
- Robust viability supplied 4129 available policy queries (0 had new delay support outside the cached policy), constrained 2494 decisions, and exposed 1574 empty queried action sets. Recovery guidance was available/selected on 544/346 empty-kernel queries; distant-kernel guidance was available/selected on 948/875. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 6.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 35.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 115.37764081484765, 'p95': 350.90739519138094, 'max': 475.7141999141922}`, and `{'median': 0.0, 'p95': 27.414753913879395, 'max': 44.7473087310791}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 633, '1': 582, '2': 485, '3': 454, '4': 521, '5': 496, '6': 485, '7': 473}`.
- Global-horizon/local-prefix cross-tab covered 2293 decisions: 2 had a winning global state but unsafe selected prefix, 843 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 25 selected actions were outside the reported winning set. 704 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 725 unique policies with solve-time statistics `{'median': 148.75629998277873, 'p95': 407.0288999937475, 'max': 527.1851999859791}` and first-observed ages `{'median': 3.0, 'p95': 8.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 36, 'queryable': 4130, 'expired': 12}`; 49 robust-mode decisions had no query.
- Of 2335 unambiguous output transitions, 1927 (0.825) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10, 'unresolved_planner_failure': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[11, 4, 0, 27, 10, 11, 6, 10, 0, 11, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.474 during the 60 frames preceding a hit versus 0.159 outside those windows.
- Mean selected control-reserve deficit was 5.849 during the 60 frames preceding a hit versus 1.407 outside those windows.
- Soft recovery was selected on 0.126 of alive decisions in the 60-frame pre-hit windows versus 0.087 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
