# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260730_144830

## Scope And Integrity

- Valid practice scope: `1..45392` (12680 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[2136, 3786, 4423, 7224, 11207, 11704, 12452, 14112, 22208, 23144, 24646, 33186, 33711, 36755, 38174, 38605, 39070, 40569, 41121]`.
- Hard no-Bomb verification: **PASS** across 12680 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2136-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 696 bullets and 0 lasers. The projectile model reported pipeline clearance -2.097.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 9 |

Contributing factors:

- `playfield_boundary`: 16
- `fast_mode`: 14
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2136 | nonspell | (376.000, 432.000) | `stay` | 696/0 | -2.097/-2.097 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 3786 | nonspell | (376.000, 432.000) | `stay` | 441/0 | -4.406/-4.406 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 4423 | nonspell | (8.000, 432.000) | `stay` | 369/0 | -5.089/-5.089 | 5f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 7224 | nonspell | (376.000, 426.343) | `up_fast` | 517/0 | 0.454/-2.452 | 3f/10f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11207 | nonspell | (46.449, 417.858) | `up_right_fast` | 927/0 | 0.119/-7.014 | 16f/24f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11704 | nonspell | (39.516, 432.000) | `up_right` | 896/0 | 1.087/-1.786 | 2f/15f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12452 | nonspell | (366.521, 432.000) | `up_right_fast` | 159/0 | -3.133/-3.133 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 14112 | nonspell | (187.337, 432.000) | `left_fast` | 483/0 | -3.954/-20.699 | 2f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22208 | nonspell | (360.885, 432.000) | `up_fast` | 466/0 | -0.225/-0.225 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23144 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 888/0 | -2.444/-2.444 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24646 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 1101/0 | -1.720/-1.720 | 0f/10f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 33186 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 345.070) | `stay` | 999/0 | -8.533/-8.533 | 10f/26f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 33711 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (194.490, 432.000) | `right_fast` | 1011/0 | -3.111/-6.642 | 27f/44f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36755 | nonspell | (8.000, 432.000) | `up_right_fast` | 390/0 | -2.434/-2.434 | 3f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38174 | nonspell | (8.000, 414.605) | `down_right_fast` | 493/0 | -2.856/-2.856 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38605 | nonspell | (368.000, 432.000) | `left_fast` | 403/0 | 0.505/-2.261 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 39070 | nonspell | (8.000, 417.805) | `down_left_fast` | 432/0 | -2.965/-2.965 | 13f/22f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 40569 | 111 懶惰「生神停止(マインドストッパー)」 | (198.001, 23.179) | `down_right_fast` | 501/0 | 0.208/-2.094 | 3f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 41121 | 111 懶惰「生神停止(マインドストッパー)」 | (199.121, 169.022) | `right_fast` | 350/0 | -2.929/-2.929 | 3f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 13 | 8381 | 0 | 0 | 0 | 0 | 0 | - | 0.375 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 985 | 0 | 0 | 0 | 0 | 0 | - | 0.373 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 1153 | 0 | 0 | 0 | 0 | 0 | - | 0.277 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1094 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 | 0 | 1067 | 0 | 0 | 0 | 0 | 0 | - | 0.556 |

## Interpretation

- Retained witnesses classify 9 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 17.503 ms median and 29.194 ms p95.
- The full enemy sensor produced 6722 snapshots; capture read time was `{'median': 4.464249999728054, 'p95': 13.706899946555495, 'max': 51.102900062687695}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 20.0}` frames, and 6 phase-counter discontinuities were excluded; 11983 decisions retained at least one robust-union body (maximum 47); 9440 decisions contained latent contact-disabled geometry (maximum 47), and 4577 contained bounded inactive-slot memory (maximum 37). 371 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.8057861328125, 'p95': 4.302972793579102, 'max': 9.073040008544922}` / `{'median': 0.8057729601860046, 'p95': 4.327776908874512, 'max': 4.707549571990967}` / `{'median': 8.742277657347586e-08, 'p95': 1.0000064373016357, 'max': 6.599658966064453}`.
- The issue-time enemy guard retained 12680 observations, detected 3797 during-plan geometry changes, recertified 3797 decisions, and overrode 63 actions. Read/recertificate timing was `{'median': 1.8412000499665737, 'p95': 3.573699970729649, 'max': 9.028599946759641}` / `{'median': 3.0400999821722507, 'p95': 6.5330000361427665, 'max': 19.295800011605024}` ms; 9416 issue captures contained latent bodies (maximum 47), and 4576 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3734/3797 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9282 observations (9255 contact enabled, 27 anticipatory, 0 errors). 9282 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9282}`.
- The terminal-threat heuristic covered 12680 decisions with horizon counts `{'0': 596, '10': 12084}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 450, '3': 9362, '4': 1974, '5': 894}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 244, '2': 221, '3': 10397, '4': 1637, '5': 181}`.
- Adaptive delay supports were `{'1,2': 159, '1,2,3': 77, '1,2,3,4': 391, '1,2,3,4,5': 289, '1,2,3,4,5,6': 164, '2,3': 56, '2,3,4': 1798, '2,3,4,5': 3249, '2,3,4,5,6': 5393, '3,4': 25, '3,4,5': 18, '3,4,5,6': 1061}`; 294 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 72/582.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6233 unambiguous output transitions, 5023 (0.806) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 19}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 19 hit windows with a positive warning lead; those leads were `[5, 3, 10, 10, 24, 15, 7, 9, 5, 3, 10, 26, 44, 5, 7, 8, 22, 11, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.674 during the 60 frames preceding a hit versus 0.341 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 26.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
