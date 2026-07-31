# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260731_091104

## Scope And Integrity

- Valid practice scope: `1..27121` (9986 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 5, at `[2150, 6388, 7928, 12873, 14879]`.
- Hard no-Bomb verification: **PASS** across 9986 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F2150-T1`. It occurred during a nonspell phase at player (8.000, 432.000), with 814 bullets and 0 lasers. The projectile model reported pipeline clearance -3.632.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 3 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `fast_mode`: 5
- `playfield_boundary`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2150 | nonspell | (8.000, 432.000) | `right_fast` | 814/0 | -3.632/-3.632 | 0f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 6388 | 35 産霊「ファーストピラミッド」 | (8.000, 426.671) | `up_right_fast` | 570/0 | -8.623/-8.623 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 7928 | nonspell | (347.899, 432.000) | `down_left_fast` | 580/0 | 0.060/-2.548 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12873 | nonspell | (8.000, 432.000) | `right_fast` | 446/0 | -1.799/-1.799 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 14879 | 38 始符「エフェメラリティ137」 | (8.000, 432.000) | `up_right_fast` | 242/0 | -9.040/-9.040 | 2f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 5317 | 0 | 0 | 0 | 0 | 0 | - | 0.202 |
| 35 産霊「ファーストピラミッド」 | 1 | 1023 | 0 | 0 | 0 | 0 | 0 | - | 0.219 |
| 38 始符「エフェメラリティ137」 | 1 | 956 | 0 | 0 | 0 | 0 | 0 | - | 0.188 |
| 42 | 0 | 875 | 0 | 0 | 0 | 0 | 0 | - | 0.248 |
| 46 | 0 | 1043 | 0 | 0 | 0 | 0 | 0 | - | 0.301 |
| 50 | 0 | 772 | 0 | 0 | 0 | 0 | 0 | - | 0.370 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 15.841 ms median and 22.362 ms p95.
- The full enemy sensor produced 4910 snapshots; capture read time was `{'median': 4.555150000669528, 'p95': 8.80209999741055, 'max': 37.19760000240058}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 9.0}` frames, and 3 phase-counter discontinuities were excluded; 9571 decisions retained at least one robust-union body (maximum 29); 8929 decisions contained latent contact-disabled geometry (maximum 29), and 3048 contained bounded inactive-slot memory (maximum 16). 80 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.4105262756347656, 'p95': 3.30047607421875, 'max': 4.811519622802734}` / `{'median': 1.0570831298828125, 'p95': 2.64459228515625, 'max': 4.811519622802734}` / `{'median': 0.0071964263916015625, 'p95': 2.0, 'max': 3.325961112976074}`.
- The issue-time enemy guard retained 9986 observations, detected 1039 during-plan geometry changes, recertified 1039 decisions, and overrode 7 actions. Read/recertificate timing was `{'median': 1.6020500006561633, 'p95': 2.6723000046331435, 'max': 6.125699997937772}` / `{'median': 1.9197000001440756, 'p95': 3.1604999967385083, 'max': 18.59880000120029}` ms; 8925 issue captures contained latent bodies (maximum 29), and 3057 contained dormant bodies (maximum 16). Fresh/global transactions preserved 1032/1039 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 7621 observations (7546 contact enabled, 75 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 1941, '0x00597600': 5680}`.
- The terminal-threat heuristic covered 9986 decisions with horizon counts `{'0': 398, '10': 9588}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1845, '3': 8141}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 482, '2': 5623, '3': 3881}`.
- Adaptive delay supports were `{'1': 285, '1,2': 100, '1,2,3': 22, '1,2,3,4': 198, '1,2,3,4,5': 10, '1,2,3,4,5,6': 18, '2,3': 1539, '2,3,4': 5674, '2,3,4,5': 1015, '2,3,4,5,6': 1125}`; 14 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 38/240.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 5478 unambiguous output transitions, 4988 (0.911) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 5}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 5 hit windows with a positive warning lead; those leads were `[15, 3, 7, 6, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.591 during the 60 frames preceding a hit versus 0.227 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 87.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
