# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260731_093027

## Scope And Integrity

- Valid practice scope: `1..42823` (12800 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[2124, 7503, 12540, 14123, 24404, 29407, 30791, 31214, 34652, 35630, 36159, 39630]`.
- Hard no-Bomb verification: **PASS** across 12800 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2124-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 674 bullets and 0 lasers. The projectile model reported pipeline clearance 0.088.

The primary class is `sensor_gap_or_unmodeled_hazard`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `modeled_committed_prefix_collision` | 4 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 7
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2124 | nonspell | (376.000, 432.000) | `up_fast` | 674/0 | 0.088/0.088 | 0f/5f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 7503 | nonspell | (372.747, 432.000) | `stay` | 758/0 | -0.532/-10.391 | 2f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12540 | nonspell | (368.000, 432.000) | `left_fast` | 240/0 | 1.279/-3.118 | 2f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 14123 | nonspell | (165.319, 420.616) | `up_left` | 566/0 | -2.397/-4.092 | 3f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24404 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 1105/0 | -3.111/-3.111 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29407 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (57.014, 432.000) | `left_fast` | 800/0 | -5.333/-5.333 | 14f/25f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30791 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (171.001, 353.120) | `left` | 1017/0 | -6.222/-8.428 | 7f/24f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 31214 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (138.110, 412.555) | `right_fast` | 1007/0 | -4.820/-5.853 | 15f/35f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 34652 | nonspell | (376.000, 432.000) | `up_left_fast` | 416/0 | -1.975/-1.975 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35630 | nonspell | (19.253, 432.000) | `right_fast` | 431/0 | -0.142/-3.267 | 5f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36159 | nonspell | (16.000, 416.947) | `right_fast` | 429/0 | 0.620/-2.625 | 2f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39630 | 111 懶惰「生神停止(マインドストッパー)」 | (196.269, 51.400) | `left_fast` | 385/0 | -3.540/-3.540 | 6f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 8835 | 0 | 0 | 0 | 0 | 0 | - | 0.360 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 963 | 0 | 0 | 0 | 0 | 0 | - | 0.403 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 780 | 0 | 0 | 0 | 0 | 0 | - | 0.275 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1102 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 | 0 | 1120 | 0 | 0 | 0 | 0 | 0 | - | 0.585 |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 16.757 ms median and 26.828 ms p95.
- The full enemy sensor produced 6523 snapshots; capture read time was `{'median': 4.152400004386436, 'p95': 8.595999999670312, 'max': 47.062000005098525}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11940 decisions retained at least one robust-union body (maximum 50); 9187 decisions contained latent contact-disabled geometry (maximum 50), and 4664 contained bounded inactive-slot memory (maximum 36). 283 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 3.467529296875, 'max': 4.8784332275390625}` / `{'median': 0.0, 'p95': 2.8991360664367676, 'max': 4.67852783203125}` / `{'median': 0.0, 'p95': 0.9999904632568359, 'max': 6.269680023193359}`.
- The issue-time enemy guard retained 12800 observations, detected 3550 during-plan geometry changes, recertified 3550 decisions, and overrode 60 actions. Read/recertificate timing was `{'median': 1.6171999959624372, 'p95': 2.813400002196431, 'max': 6.703099999867845}` / `{'median': 2.583600002253661, 'p95': 5.0095999977202155, 'max': 13.474500003212597}` ms; 9170 issue captures contained latent bodies (maximum 50), and 4660 contained dormant bodies (maximum 36). Fresh/global transactions preserved 3490/3550 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9026 observations (8996 contact enabled, 30 anticipatory, 0 errors). 9026 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9026}`.
- The terminal-threat heuristic covered 12800 decisions with horizon counts `{'0': 691, '10': 12109}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1777, '3': 9625, '4': 1398}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 329, '2': 6181, '3': 5012, '4': 1278}`.
- Adaptive delay supports were `{'1': 158, '1,2': 99, '1,2,3': 97, '1,2,3,4': 617, '1,2,3,4,5': 101, '1,2,3,4,5,6': 32, '2': 32, '2,3': 1033, '2,3,4': 6210, '2,3,4,5': 2441, '2,3,4,5,6': 1158, '3,4': 81, '3,4,5': 246, '3,4,5,6': 495}`; 87 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 32/230.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6319 unambiguous output transitions, 5683 (0.899) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[5, 15, 6, 13, 3, 25, 24, 35, 4, 10, 8, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.498 during the 60 frames preceding a hit versus 0.341 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 11.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
