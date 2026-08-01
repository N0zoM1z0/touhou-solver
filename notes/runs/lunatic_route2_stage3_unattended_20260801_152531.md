# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260801_152531

## Scope And Integrity

- Valid practice scope: `2..27029` (8437 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 6, at `[1255, 1991, 7576, 8339, 23938, 25481]`.
- Hard no-Bomb verification: **PASS** across 8437 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F1255-T1`. It occurred during a nonspell phase at player (376.000, 428.000), with 276 bullets and 0 lasers. The projectile model reported pipeline clearance -2.234.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 3 |
| `observed_bullet_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 5
- `playfield_boundary`: 5
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1255 | nonspell | (376.000, 428.000) | `up_fast` | 276/0 | -2.234/-13.269 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 1991 | nonspell | (334.313, 428.747) | `left_fast` | 279/0 | -1.230/-2.504 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 7576 | nonspell | (335.642, 432.000) | `down_right_fast` | 268/0 | 5.005/3.526 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8339 | nonspell | (376.000, 428.000) | `left_fast` | 341/0 | -3.173/-3.173 | 2f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23938 | 46 国体「三種の神器　郷」 | (373.172, 424.572) | `up_left_fast` | 470/0 | 0.211/-0.069 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25481 | 50 虚史「幻想郷伝説」 | (158.740, 404.000) | `stay` | 310/190 | -1.527/-1.527 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 4463 | 332 | 57 | 0 | 284 | 21 | 610.045 | 0.199 |
| 35 | 0 | 883 | 859 | 657 | 0 | 0 | 104 | 42.708 | 0.221 |
| 38 | 0 | 785 | 768 | 446 | 0 | 0 | 103 | 94.141 | 0.233 |
| 42 | 0 | 756 | 749 | 616 | 0 | 0 | 121 | 40.543 | 0.246 |
| 46 国体「三種の神器　郷」 | 1 | 895 | 889 | 653 | 0 | 0 | 144 | 57.271 | 0.332 |
| 50 虚史「幻想郷伝説」 | 1 | 655 | 648 | 443 | 0 | 0 | 119 | 85.906 | 0.334 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.068 ms median and 30.169 ms p95.
- The full enemy sensor produced 4355 snapshots; capture read time was `{'median': 5.420200002845377, 'p95': 18.2994999922812, 'max': 67.0764000096824}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 56.0}` frames, and 3 phase-counter discontinuities were excluded; 8251 decisions retained at least one robust-union body (maximum 31); 7717 decisions contained latent contact-disabled geometry (maximum 31), and 2532 contained bounded inactive-slot memory (maximum 19). 81 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.3650054931640625, 'p95': 2.7650070190429688, 'max': 3.616790771484375}` / `{'median': 1.1742093563079834, 'p95': 2.609626531600952, 'max': 2.7650070190429688}` / `{'median': 5.245208740234375e-06, 'p95': 1.406890630722046, 'max': 2.7650070190429688}`.
- The issue-time enemy guard retained 8437 observations, detected 1101 during-plan geometry changes, recertified 1101 decisions, and overrode 13 actions. Read/recertificate timing was `{'median': 1.5159999893512577, 'p95': 2.9155999945942312, 'max': 32.458400004543364}` / `{'median': 2.2490999836008996, 'p95': 5.170700023882091, 'max': 21.7930999933742}` ms; 7719 issue captures contained latent bodies (maximum 31), and 2540 contained dormant bodies (maximum 19). Fresh/global transactions preserved 1087/1102 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 6585 observations (6521 contact enabled, 64 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0058CE60': 1680, '0x00592230': 4905}`.
- The terminal-threat heuristic covered 8437 decisions with horizon counts `{'0': 21, '10': 8416}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 20, '3': 7255, '4': 596, '5': 566}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 650, '3': 7669, '4': 118}`.
- Adaptive delay supports were `{'1,2,3': 40, '1,2,3,4': 32, '2,3': 646, '2,3,4': 3196, '2,3,4,5': 2673, '2,3,4,5,6': 1850}`; 24 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 57/412.
- Robust viability supplied 4245 available policy queries (0 had new delay support outside the cached policy), constrained 284 decisions, and exposed 2872 empty queried action sets. Recovery guidance was available/selected on 749/0 empty-kernel queries; distant-kernel guidance was available/selected on 1902/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 654, '1': 610, '2': 441, '3': 479, '4': 500, '5': 503, '6': 538, '7': 520}`.
- Global-horizon/local-prefix cross-tab covered 3278 decisions: 0 had a winning global state but unsafe selected prefix, 2309 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 136 selected actions were outside the reported winning set. 578 newer issue-time hazard versions and 5 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 612 unique policies with solve-time statistics `{'median': 61.71570000879001, 'p95': 152.4187000177335, 'max': 1205.8322000084445}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 59.0}`. Policy status counts were `{'pending_future_epoch': 64, 'queryable': 4239, 'expired': 3040}`; 3098 robust-mode decisions had no query.
- Of 5124 unambiguous output transitions, 4893 (0.955) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 3, 'global_viability_kernel_exhausted_before_hit': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[8, 6, 0, 4, 9, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.569 during the 60 frames preceding a hit versus 0.227 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 110.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Source-v13 delivered 653/1,190 complete roots, 267 effective
prepublication issues, and 13 effective delayed issues. Ten leases were
created and three renewed. Thirteen later decisions captured one and two
selected lease authority, but effective lease consumption remained zero.

The retained failure split is structural: six capture geometry revocations
had zero contact-enabled bodies; three action-change revocations retained the
same direction/focus after ignoring `+deadline_hold` and SHOT; one selected
lease passed pipeline and body geometry but was rejected by the separate
fresh-local transaction check. The next focused run must correct only these
false revocation seams and show nonzero lease-effective issues. Unknown future
coverage, true contact-body escape, focus/direction changes, and Bomb remain
fail closed.
