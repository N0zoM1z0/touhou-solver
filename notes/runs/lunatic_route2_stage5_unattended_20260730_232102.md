# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260730_232102

## Scope And Integrity

- Valid practice scope: `1..44861` (13571 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 19, at `[3493, 4417, 11990, 12570, 23761, 24632, 27977, 29259, 29571, 30173, 32402, 32826, 35941, 36581, 39503, 40179, 41245, 42848, 44117]`.
- Hard no-Bomb verification: **PASS** across 13571 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

Replay retention: **ACCEPTED**. Dynamic save states
`10 -> 12 -> 14 -> 13 -> 2` wrote slot 15 and retained
`artifacts/replays/archive/th8_15_4a31f868c2214235bde019d17c47f733236c16dc7cbf89db3fd073f6c1b783de.rpy`.
Decoded identity is Route 2/Lunatic/single Stage 5, RNG seed 38,179,
33,728 frames, and no Bomb press. The prior slot-15 replay was already
present in its content-addressed archive.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F3493-T1`. It occurred during a nonspell phase at player (16.000, 432.000), with 530 bullets and 0 lasers. The projectile model reported pipeline clearance -1.308.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 10 |
| `observed_bullet_overlap` | 8 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 17
- `playfield_boundary`: 14
- `pool_density_over_1000`: 7

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3493 | nonspell | (16.000, 432.000) | `right_fast` | 530/0 | -1.308/-1.413 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 4417 | nonspell | (8.000, 432.000) | `up_fast` | 296/0 | -5.591/-12.520 | 2f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11990 | nonspell | (361.495, 428.747) | `up_left` | 292/0 | 0.572/-1.369 | 4f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12570 | nonspell | (376.000, 418.059) | `up_fast` | 341/0 | -3.490/-3.490 | 0f/22f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23761 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 1106/0 | -1.267/-1.267 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24632 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_left_fast` | 976/0 | -1.233/-1.233 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 27977 | nonspell | (8.000, 432.000) | `up_fast` | 1005/0 | -2.498/-2.498 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29259 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (172.962, 380.842) | `left_fast` | 909/0 | -5.489/-5.961 | 8f/16f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29571 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (259.451, 386.745) | `up_left_fast` | 1005/0 | -5.494/-6.398 | 8f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30173 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (198.918, 432.000) | `up_fast` | 1005/0 | -3.498/-3.971 | 8f/18f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 32402 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (8.000, 432.000) | `up_right_fast` | 995/0 | -6.654/-6.654 | 7f/61f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 32826 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (311.656, 432.000) | `right_fast` | 1005/0 | -6.332/-6.332 | 15f/22f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 35941 | nonspell | (16.910, 432.000) | `right_fast` | 432/0 | -2.577/-2.577 | 0f/2f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36581 | nonspell | (376.000, 399.518) | `left_fast` | 490/0 | -1.812/-1.812 | 10f/20f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 39503 | 111 懶惰「生神停止(マインドストッパー)」 | (186.744, 195.435) | `up` | 1058/0 | -1.759/-1.759 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 40179 | 111 懶惰「生神停止(マインドストッパー)」 | (238.247, 192.018) | `right_fast` | 338/0 | 0.448/-0.725 | 5f/14f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 41245 | 111 懶惰「生神停止(マインドストッパー)」 | (195.568, 33.053) | `left_fast` | 388/0 | -1.424/-3.604 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 42848 | 115 散符「真実の月(インビジブルフルムーン)」 | (267.099, 428.000) | `up_fast` | 1080/0 | 0.763/0.125 | 0f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 44117 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 425.947) | `right_fast` | 952/0 | 0.851/-2.053 | 4f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 8794 | 0 | 0 | 0 | 0 | 0 | - | 0.378 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 950 | 0 | 0 | 0 | 0 | 0 | - | 0.453 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 5 | 1385 | 0 | 0 | 0 | 0 | 0 | - | 0.359 |
| 111 懶惰「生神停止(マインドストッパー)」 | 3 | 1225 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1217 | 0 | 0 | 0 | 0 | 0 | - | 0.430 |

## Interpretation

- Retained witnesses classify 8 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 16.964 ms median and 26.314 ms p95.
- The full enemy sensor produced 6995 snapshots; capture read time was `{'median': 4.310600001190323, 'p95': 10.75950000085868, 'max': 37.30569999970612}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 12847 decisions retained at least one robust-union body (maximum 47); 10238 decisions contained latent contact-disabled geometry (maximum 47), and 4990 contained bounded inactive-slot memory (maximum 38). 441 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 3.5408897399902344, 'max': 5.278530120849609}` / `{'median': 0.0, 'p95': 3.459514617919922, 'max': 4.697328090667725}` / `{'median': 0.0, 'p95': 1.0, 'max': 5.138305902481079}`.
- The issue-time enemy guard retained 13571 observations, detected 4028 during-plan geometry changes, recertified 4028 decisions, and overrode 67 actions. Read/recertificate timing was `{'median': 1.5683000019635074, 'p95': 2.61079999836511, 'max': 8.321900000737514}` / `{'median': 2.5374500000907574, 'p95': 5.406599997513695, 'max': 14.602799998101545}` ms; 10209 issue captures contained latent bodies (maximum 47), and 4989 contained dormant bodies (maximum 38). Fresh/global transactions preserved 3961/4028 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9833 observations (9803 contact enabled, 30 anticipatory, 0 errors). 9833 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9833}`.
- The terminal-threat heuristic covered 13571 decisions with horizon counts `{'0': 628, '10': 12943}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1979, '3': 9881, '4': 1711}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 337, '2': 5818, '3': 5599, '4': 1817}`.
- Adaptive delay supports were `{'1': 158, '1,2': 100, '1,2,3': 35, '1,2,3,4': 713, '1,2,3,4,5': 45, '1,2,3,4,5,6': 183, '2,3': 1017, '2,3,4': 6188, '2,3,4,5': 1836, '2,3,4,5,6': 1976, '3,4': 1, '3,4,5': 254, '3,4,5,6': 1065}`; 94 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 75/435.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6699 unambiguous output transitions, 6028 (0.900) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 18, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 18 hit windows with a positive warning lead; those leads were `[8, 9, 8, 22, 7, 6, 3, 16, 8, 18, 61, 22, 2, 20, 0, 14, 8, 5, 4]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.450 during the 60 frames preceding a hit versus 0.354 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
