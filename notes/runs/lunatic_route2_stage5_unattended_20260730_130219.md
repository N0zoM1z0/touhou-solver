# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260730_130219

## Scope And Integrity

- Valid practice scope: `2..42835` (12281 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[2220, 11712, 23564, 24225, 26979, 30521, 34613, 37210, 39251, 40225, 41113, 42146]`.
- Hard no-Bomb verification: **PASS** across 12281 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2220-T1`. It occurred during a nonspell phase at player (8.000, 422.343), with 607 bullets and 0 lasers. The projectile model reported pipeline clearance -1.206.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 9
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2220 | nonspell | (8.000, 422.343) | `up_left_fast` | 607/0 | -1.206/-1.206 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11712 | nonspell | (364.000, 432.000) | `left_fast` | 875/0 | -15.853/-17.445 | 6f/18f | `observed_enemy_body_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23564 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 1048/0 | -3.050/-3.050 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24225 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 861/0 | -3.681/-3.681 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 26979 | nonspell | (11.832, 432.000) | `up_fast` | 1054/0 | -1.348/-1.348 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30521 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (222.306, 387.720) | `left_fast` | 1000/0 | -6.268/-6.268 | 12f/32f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 34613 | nonspell | (8.000, 410.267) | `stay` | 438/0 | -0.918/-1.487 | 3f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37210 | 111 懶惰「生神停止(マインドストッパー)」 | (184.001, 54.443) | `down_left` | 490/0 | 1.415/-1.598 | 2f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39251 | 111 懶惰「生神停止(マインドストッパー)」 | (257.087, 172.784) | `right` | 337/0 | -1.805/-1.805 | 0f/11f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 40225 | 115 散符「真実の月(インビジブルフルムーン)」 | (119.282, 432.000) | `up_right_fast` | 1102/0 | -2.222/-2.222 | 3f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 41113 | 115 散符「真実の月(インビジブルフルムーン)」 | (249.309, 429.172) | `up_left_fast` | 1135/0 | -0.549/-0.549 | 0f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 42146 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 428.000) | `up_fast` | 1283/0 | -1.662/-1.662 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8744 | 0 | 0 | 0 | 0 | 0 | - | 0.383 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 687 | 0 | 0 | 0 | 0 | 0 | - | 0.396 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 552 | 0 | 0 | 0 | 0 | 0 | - | 0.317 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1120 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1178 | 0 | 0 | 0 | 0 | 0 | - | 0.431 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.142 ms median and 27.170 ms p95.
- The full enemy sensor produced 6272 snapshots; capture read time was `{'median': 4.475000023376197, 'p95': 11.14620000589639, 'max': 44.3059999961406}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 13.0}` frames, and 6 phase-counter discontinuities were excluded; 11495 decisions retained at least one robust-union body (maximum 45); 9049 decisions contained latent contact-disabled geometry (maximum 45), and 4129 contained bounded inactive-slot memory (maximum 37). 243 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 1.993927001953125, 'max': 3.6024627685546875}` / `{'median': 0.0, 'p95': 1.9939277172088623, 'max': 2.616793155670166}` / `{'median': 0.0, 'p95': 1.3113021850585938e-05, 'max': 0.9928417205810547}`.
- The issue-time enemy guard retained 12281 observations, detected 3156 during-plan geometry changes, recertified 3156 decisions, and overrode 41 actions. Read/recertificate timing was `{'median': 1.8373000202700496, 'p95': 3.589100087992847, 'max': 8.478399948216975}` / `{'median': 2.653400006238371, 'p95': 5.816200049594045, 'max': 32.000400009565055}` ms; 9011 issue captures contained latent bodies (maximum 45), and 4132 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3115/3156 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8788 observations (8759 contact enabled, 29 anticipatory, 0 errors). 8788 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8788}`.
- The terminal-threat heuristic covered 12281 decisions with horizon counts `{'0': 659, '10': 11622}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 523, '3': 10028, '4': 1508, '5': 222}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 211, '2': 293, '3': 10686, '4': 1091}`.
- Adaptive delay supports were `{'1,2': 157, '1,2,3': 75, '1,2,3,4': 173, '1,2,3,4,5': 176, '1,2,3,4,5,6': 218, '2,3': 447, '2,3,4': 2392, '2,3,4,5': 3440, '2,3,4,5,6': 4863, '3,4': 1, '3,4,5': 3, '3,4,5,6': 324, '4,5,6': 12}`; 110 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 60/630.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6108 unambiguous output transitions, 4840 (0.792) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[6, 18, 7, 8, 5, 32, 15, 10, 11, 12, 10, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.472 during the 60 frames preceding a hit versus 0.351 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
