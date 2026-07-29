# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_113124

## Scope And Integrity

- Valid practice scope: `1..42928` (11797 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 14, at `[1567, 2718, 4209, 8234, 10711, 12350, 12981, 24216, 25064, 29453, 29865, 30544, 35533, 38699]`.
- Hard no-Bomb verification: **PASS** across 11797 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1567-T1`. It occurred during a nonspell phase at player (8.173, 312.683), with 78 bullets and 0 lasers. The projectile model reported pipeline clearance -1.732.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 6 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 10
- `pool_density_over_1000`: 3
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1567 | nonspell | (8.173, 312.683) | `down` | 78/0 | -1.732/-1.732 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2718 | nonspell | (376.000, 416.520) | `up_fast` | 915/0 | -4.048/-4.048 | 4f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4209 | nonspell | (376.000, 427.400) | `up_fast` | 389/0 | -3.156/-3.302 | 2f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8234 | nonspell | (267.528, 420.747) | `up_left_fast` | 633/0 | 1.872/-1.374 | 2f/2f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10711 | nonspell | (38.056, 401.944) | `up_right_fast` | 881/0 | 0.343/-22.853 | 40f/50f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12350 | nonspell | (376.000, 424.000) | `up_fast` | 327/0 | 0.187/-2.303 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12981 | nonspell | (376.000, 223.120) | `down_left` | 315/0 | -1.517/-1.517 | 5f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24216 | 103 幻波「赤眼催眠(マインドブローイング)」 | (229.777, 432.000) | `left_fast` | 1317/0 | 1.693/-3.346 | 3f/10f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25064 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 973/0 | -1.633/-1.633 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29453 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (170.782, 432.000) | `up_right_fast` | 979/0 | -5.580/-5.580 | 13f/34f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29865 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (219.789, 432.000) | `up_right` | 1017/0 | -5.052/-7.293 | 13f/24f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30544 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (155.502, 432.000) | `up_fast` | 1012/0 | -3.958/-5.440 | 14f/23f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35533 | nonspell | (16.485, 410.898) | `up_right_fast` | 490/0 | 1.304/-2.532 | 11f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38699 | 111 懶惰「生神停止(マインドストッパー)」 | (141.386, 202.818) | `down_left_fast` | 340/0 | -1.934/-1.934 | 0f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 7814 | 7677 | 5451 | 0 | 2205 | 1028 | 131.471 | 0.205 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 875 | 868 | 480 | 0 | 386 | 161 | 115.644 | 0.388 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 3 | 888 | 878 | 673 | 0 | 205 | 180 | 88.265 | 0.323 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1138 | 1129 | 564 | 0 | 552 | 178 | 97.878 | 0.000 |
| 115 | 0 | 1082 | 1071 | 844 | 0 | 223 | 177 | 62.053 | 0.548 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.390 ms median and 24.001 ms p95.
- The full enemy sensor produced 6341 snapshots; capture read time was `{'median': 5.553300026804209, 'p95': 25.58620006311685, 'max': 55.707500083372}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 13.0}` frames, and 7 phase-counter discontinuities were excluded; 11213 decisions retained at least one robust-union body (maximum 42); 4796 decisions contained latent contact-disabled geometry (maximum 42), and 6103 contained bounded inactive-slot memory (maximum 41). 221 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 2.2627410888671875, 'max': 5.599998474121094}` / `{'median': 0.0, 'p95': 2.1573257446289062, 'max': 5.599997520446777}` / `{'median': 0.0, 'p95': 3.2342409499279863, 'max': 11.199995994567871}`.
- The issue-time enemy guard retained 11797 observations, detected 2468 during-plan geometry changes, recertified 2468 decisions, and overrode 43 actions. Read/recertificate timing was `{'median': 1.8177999882027507, 'p95': 3.4333999501541257, 'max': 15.237700077705085}` / `{'median': 3.17605008604005, 'p95': 6.960300030186772, 'max': 18.46819999627769}` ms; 4773 issue captures contained latent bodies (maximum 42), and 6102 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2425/2468 planned actions, relaxed 7 fresh/global empty intersections, inherited 4 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8369 observations (8342 contact enabled, 27 anticipatory, 0 errors). 8369 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8369}`.
- The terminal-threat heuristic covered 11797 decisions with horizon counts `{'0': 71, '10': 11549, '32': 177}`; it reported 5 collision and 31 sub-safety-clearance warnings, and relaxed 40 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 347, '3': 8594, '4': 2010, '5': 846}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 1081, '3': 9006, '4': 1203, '5': 507}`.
- Adaptive delay supports were `{'1,2,3': 46, '1,2,3,4': 39, '1,2,3,4,5': 133, '1,2,3,4,5,6': 34, '2,3': 466, '2,3,4': 2542, '2,3,4,5': 4676, '2,3,4,5,6': 3077, '3,4': 13, '3,4,5,6': 740, '4,5,6': 31}`; 241 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 33/237.
- Robust viability supplied 11623 available policy queries (0 had new delay support outside the cached policy), constrained 3571 decisions, and exposed 8012 empty queried action sets. Recovery guidance was available/selected on 1044/423 empty-kernel queries; distant-kernel guidance was available/selected on 6171/5887. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 135.7645019878171, 'p95': 339.03392160667346, 'max': 502.41019097944263}`, and `{'median': 0.0, 'p95': 24.0, 'max': 42.91260623931885}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1815, '1': 1611, '2': 1203, '3': 1347, '4': 1365, '5': 1395, '6': 1396, '7': 1491}`.
- Global-horizon/local-prefix cross-tab covered 7645 decisions: 3 had a winning global state but unsafe selected prefix, 5348 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 21 selected actions were outside the reported winning set. 2102 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1724 unique policies with solve-time statistics `{'median': 104.12305005593225, 'p95': 342.9632999468595, 'max': 450.39410004392266}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1787.0}`. Policy status counts were `{'pending_future_epoch': 62, 'queryable': 11623, 'expired': 15}`; 77 robust-mode decisions had no query.
- Of 6235 unambiguous output transitions, 5475 (0.878) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 14}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 14 hit windows with a positive warning lead; those leads were `[8, 8, 7, 2, 50, 5, 13, 10, 8, 34, 24, 23, 15, 17]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.378 during the 60 frames preceding a hit versus 0.236 outside those windows.
- Mean selected control-reserve deficit was 11.496 during the 60 frames preceding a hit versus 4.469 outside those windows.
- Soft recovery was selected on 0.003 of alive decisions in the 60-frame pre-hit windows versus 0.042 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 15.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
