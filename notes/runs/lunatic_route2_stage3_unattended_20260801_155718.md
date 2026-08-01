# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260801_155718

## Scope And Integrity

- Valid practice scope: `2..27367` (8547 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 7, at `[1263, 2136, 6695, 7711, 13011, 13860, 25791]`.
- Hard no-Bomb verification: **PASS** across 8547 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F1263-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 231 bullets and 0 lasers. The projectile model reported pipeline clearance -2.842.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 5 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 7
- `fast_mode`: 6
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1263 | nonspell | (376.000, 432.000) | `left_fast` | 231/0 | -2.842/-2.842 | 4f/12f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 2136 | nonspell | (8.000, 432.000) | `up_right_fast` | 595/0 | -2.598/-2.598 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 6695 | 35 産霊「ファーストピラミッド」 | (376.000, 424.887) | `up_fast` | 308/0 | -2.888/-2.888 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 7711 | nonspell | (8.000, 420.000) | `up_fast` | 337/0 | 1.380/-3.872 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13011 | nonspell | (376.000, 432.000) | `up_fast` | 407/0 | -1.595/-1.595 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13860 | nonspell | (146.153, 432.000) | `left_fast` | 410/0 | -1.790/-1.790 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 25791 | 50 虚史「幻想郷伝説」 | (192.178, 432.000) | `stay` | 273/199 | -2.497/-2.497 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 4584 | 307 | 27 | 0 | 322 | 17 | 31.968 | 0.218 |
| 35 産霊「ファーストピラミッド」 | 1 | 916 | 884 | 671 | 0 | 0 | 91 | 45.225 | 0.263 |
| 38 | 0 | 766 | 759 | 376 | 0 | 0 | 120 | 94.877 | 0.201 |
| 42 | 0 | 756 | 749 | 599 | 0 | 0 | 121 | 41.555 | 0.234 |
| 46 | 0 | 867 | 860 | 739 | 0 | 0 | 143 | 54.837 | 0.430 |
| 50 虚史「幻想郷伝説」 | 1 | 658 | 651 | 456 | 0 | 0 | 118 | 83.712 | 0.354 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 17.227 ms median and 30.305 ms p95.
- The full enemy sensor produced 4406 snapshots; capture read time was `{'median': 5.505749984877184, 'p95': 17.075899988412857, 'max': 80.73570000124164}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 35.0}` frames, and 3 phase-counter discontinuities were excluded; 8361 decisions retained at least one robust-union body (maximum 25); 7888 decisions contained latent contact-disabled geometry (maximum 25), and 2699 contained bounded inactive-slot memory (maximum 14). 99 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.0, 'p95': 2.616790771484375, 'max': 3.616790771484375}` / `{'median': 1.0, 'p95': 2.5952930450439453, 'max': 2.616792917251587}` / `{'median': 9.5367431640625e-07, 'p95': 1.177947998046875, 'max': 2.3697519302368164}`.
- The issue-time enemy guard retained 8547 observations, detected 1123 during-plan geometry changes, recertified 1123 decisions, and overrode 6 actions. Read/recertificate timing was `{'median': 1.6058000037446618, 'p95': 2.9113999917171896, 'max': 18.692699988605455}` / `{'median': 2.2757999831810594, 'p95': 4.954400006681681, 'max': 19.599800027208403}` ms; 7888 issue captures contained latent bodies (maximum 25), and 2696 contained dormant bodies (maximum 14). Fresh/global transactions preserved 1117/1123 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 6672 observations (6605 contact enabled, 67 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x00587A90': 4983, '0x005AC540': 1689}`.
- The terminal-threat heuristic covered 8547 decisions with horizon counts `{'0': 20, '10': 8527}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 20, '3': 7601, '4': 404, '5': 522}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 1, '2': 111, '3': 8222, '4': 205, '5': 8}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3': 39, '1,2,3,4': 31, '2,3': 413, '2,3,4': 3096, '2,3,4,5': 2724, '2,3,4,5,6': 2238, '5,6': 5}`; 14 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 33/244.
- Robust viability supplied 4210 available policy queries (0 had new delay support outside the cached policy), constrained 322 decisions, and exposed 2868 empty queried action sets. Recovery guidance was available/selected on 589/0 empty-kernel queries; distant-kernel guidance was available/selected on 2018/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 665, '1': 592, '2': 432, '3': 473, '4': 502, '5': 498, '6': 517, '7': 531}`.
- Global-horizon/local-prefix cross-tab covered 3227 decisions: 0 had a winning global state but unsafe selected prefix, 2306 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 96 selected actions were outside the reported winning set. 605 newer issue-time hazard versions and 8 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 610 unique policies with solve-time statistics `{'median': 61.51149998186156, 'p95': 150.67820000695065, 'max': 1980.5783999909181}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 60.0}`. Policy status counts were `{'pending_future_epoch': 64, 'queryable': 4209, 'expired': 2272}`; 2335 robust-mode decisions had no query.
- Of 5125 unambiguous output transitions, 4857 (0.948) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 5, 'global_viability_kernel_exhausted_before_hit': 2}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 7 hit windows with a positive warning lead; those leads were `[12, 9, 6, 5, 5, 3, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.516 during the 60 frames preceding a hit versus 0.251 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 99.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Lease v4 passed its narrow physical mechanism gate but the ordinary global
outcome did not improve. One lease was created, one was renewed, 31 decisions
captured a lease, 30 selected it, and 29 issues retained the exact
`down_left_fast` direction with no physical input write. The only revocation
was finite terminal expiry. Thus the former false geometry/action/local-veto
seams are closed without widening direction or focus.

All five ordinary hits nevertheless had zero effective prepublication,
delayed, or lease authority in their preceding 240-frame windows; the common
status was `future_policy_unavailable`. Many source roots called themselves a
complete causal prefix but were truncated before H268 by main ECL opcode
`0x05`/`0x06` or captured enemy movement state 2. Before the canonical f1263
hit, the first nontruncated full-H268 root arrived at f1249, only 14 frames
before collision and too late to solve and publish. The next correction gate
is exact closure for those reached source semantics. Preserve UNKNOWN for any
state that still cannot be reconstructed; do not compensate with a local
ranking or stage waypoint.
