# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_221253

## Scope And Integrity

- Valid practice scope: `2..13077` (2070 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `runtime_error`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 12, at `[1262, 1804, 2253, 4147, 8816, 9521, 9848, 10341, 10759, 11589, 12130, 12462]`.
- Hard no-Bomb verification: **PASS** across 2070 decisions; mask/flag/action violations are all empty.

This session is **discarded**. It ended at frame 13,077 with
`termination_reason=process_unreadable`, `trial_accepted=false`, and no
verified terminal cleanup by the supervisor. It may support component timing
and individual counterexamples, but it must not be merged into a complete-run
or survival baseline.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1262-T1`. It occurred during a nonspell phase at player (37.274, 432.000), with 215 bullets and 0 lasers. The projectile model reported pipeline clearance -1.334.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 2 |
| `observed_enemy_body_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 9
- `action_lag_over_model`: 1
- `corridor_deadline_miss`: 1
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1262 | nonspell | (37.274, 432.000) | `down_right_fast` | 215/0 | -1.334/-2.576 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 1804 | nonspell | (91.974, 432.000) | `stay` | 418/0 | -1.373/-2.574 | 0f/17f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2253 | nonspell | (331.195, 432.000) | `left` | 297/0 | -3.712/-3.712 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4147 | nonspell | (352.318, 432.000) | `down_right_fast` | 1070/0 | -2.730/-6.609 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8816 | nonspell | (352.000, 432.000) | `up_right_fast` | 769/0 | -32.899/-32.899 | 12f/17f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9521 | nonspell | (52.000, 401.600) | `up` | 128/0 | -2.467/-25.721 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9848 | nonspell | (376.000, 432.000) | `left_fast` | 470/0 | -7.253/-19.616 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10341 | nonspell | (8.000, 405.866) | `up_fast` | 501/0 | -3.611/-6.461 | 6f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10759 | nonspell | (235.958, 404.000) | `up_fast` | 761/0 | 26.577/2.985 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11589 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 534/0 | -0.019/-0.019 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12130 | 57 夢境「二重大結界」 | (8.000, 431.144) | `up_right_fast` | 594/0 | -1.787/-1.787 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12462 | 57 夢境「二重大結界」 | (37.080, 337.598) | `down_left_fast` | 582/0 | -3.556/-3.556 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 9 | 1619 | 1571 | 809 | 0 | 748 | 390 | 165.509 | 0.156 |
| 57 夢境「二重大結界」 | 3 | 451 | 441 | 56 | 0 | 376 | 110 | 259.460 | 0.219 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 5.000 frames median and 6.000 frames p95. The local plan took 32.536 ms median and 60.949 ms p95.
- The full enemy sensor produced 1814 snapshots; capture read time was `{'median': 41.6607500083046, 'p95': 71.47940000868402, 'max': 107.70560000673868}`, snapshot age was `{'median': 6.0, 'p95': 9.0, 'max': 15.0}` frames, and 2 phase-counter discontinuities were excluded; 1819 decisions retained at least one robust-union body (maximum 59); 820 decisions contained latent contact-disabled geometry (maximum 59), and 1012 contained bounded inactive-slot memory (maximum 53). 224 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.968963623046875, 'p95': 3.9988250732421875, 'max': 4.734588623046875}` / `{'median': 3.019639015197754, 'p95': 3.778583526611328, 'max': 3.9928762912750244}` / `{'median': 0.010005205869674683, 'p95': 0.8110580444335938, 'max': 7.985933542251587}`.
- The issue-time enemy guard retained 2070 observations, detected 750 during-plan geometry changes, recertified 750 decisions, and overrode 338 actions. Read/recertificate timing was `{'median': 2.6446999981999397, 'p95': 5.8982000045944005, 'max': 27.04210000229068}` / `{'median': 13.250199976027943, 'p95': 22.945200005779043, 'max': 35.29060000437312}` ms; 820 issue captures contained latent bodies (maximum 59), and 1018 contained dormant bodies (maximum 53).
- The synchronous spell-owner guard retained 451 observations (451 contact enabled, 0 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 451}`.
- The terminal-threat heuristic covered 2070 decisions with horizon counts `{'0': 41, '10': 1887, '32': 142}`; it reported 2 collision and 11 sub-safety-clearance warnings, and relaxed 23 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 42, '3': 14, '4': 159, '5': 176, '6': 1679}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 48, '3': 121, '4': 20, '5': 387, '6': 1494}`.
- Adaptive delay supports were `{'2,3': 43, '2,3,4,5': 98, '2,3,4,5,6': 118, '3,4,5,6': 1099, '4,5,6': 712}`; 398 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 94/111.
- Robust viability supplied 2012 available policy queries (0 had new delay support outside the cached policy), constrained 1124 decisions, and exposed 865 empty queried action sets. Recovery guidance was available/selected on 162/96 empty-kernel queries; distant-kernel guidance was available/selected on 622/580. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 52.5, 'p95': 153.0, 'max': 153.0}`, `{'median': 157.58172482873766, 'p95': 357.77087639996637, 'max': 515.2397500193478}`, and `{'median': 2.5958430767059326, 'p95': 25.372583389282227, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 319, '1': 268, '2': 263, '3': 224, '4': 222, '5': 255, '6': 214, '7': 247}`.
- Global-horizon/local-prefix cross-tab covered 701 decisions: 0 had a winning global state but unsafe selected prefix, 187 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 5 selected actions were outside the reported winning set. 451 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 500 unique policies with solve-time statistics `{'median': 196.0945000028005, 'p95': 354.9023999948986, 'max': 463.8594999851193}` and first-observed ages `{'median': 5.0, 'p95': 9.0, 'max': 1796.0}`. Policy status counts were `{'pending_future_epoch': 26, 'queryable': 2011, 'expired': 9}`; 34 robust-mode decisions had no query.
- Of 1175 unambiguous output transitions, 1021 (0.869) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 11, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[6, 17, 3, 4, 17, 0, 9, 6, 0, 5, 6, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.519 during the 60 frames preceding a hit versus 0.123 outside those windows.
- Mean selected control-reserve deficit was 8.046 during the 60 frames preceding a hit versus 1.889 outside those windows.
- Soft recovery was selected on 0.068 of alive decisions in the 60-frame pre-hit windows versus 0.048 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Do not rerun this strategy merely to complete the trace. Coarse fused survival
returns to shadow together with fine refinement; CE-0103 records the
incomplete isolation result.
