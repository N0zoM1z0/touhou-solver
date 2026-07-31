# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_142342

## Scope And Integrity

- Valid practice scope: `1..45506` (12109 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 18, at `[1915, 2738, 4005, 4338, 8911, 9474, 11833, 13031, 13689, 22367, 22814, 27920, 30592, 31339, 32263, 35591, 39986, 43119]`.
- Hard no-Bomb verification: **PASS** across 12109 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F1915-T1`. It occurred during a nonspell phase at player (20.169, 428.031), with 210 bullets and 0 lasers. The projectile model reported pipeline clearance -5.091.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 6 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 13
- `playfield_boundary`: 12
- `corridor_deadline_miss`: 3
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1915 | nonspell | (20.169, 428.031) | `right_fast` | 210/0 | -5.091/-5.091 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2738 | nonspell | (364.071, 432.000) | `up_right_fast` | 518/0 | -3.934/-3.934 | 5f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4005 | nonspell | (356.201, 412.201) | `up_left_fast` | 937/0 | -1.423/-1.459 | 7f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4338 | nonspell | (32.132, 420.000) | `up_fast` | 850/0 | -1.425/-29.281 | 3f/16f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8911 | nonspell | (8.000, 402.767) | `up_fast` | 398/0 | 2.070/-5.048 | 8f/16f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9474 | nonspell | (66.712, 432.000) | `right_fast` | 189/0 | -1.470/-1.470 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11833 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 569/0 | -1.787/-1.787 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13031 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 605/0 | -1.779/-1.779 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13689 | 57 夢境「二重大結界」 | (55.871, 369.481) | `stay` | 581/0 | -2.534/-2.534 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 22367 | nonspell | (363.533, 423.515) | `down_fast` | 766/0 | -1.529/-1.529 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22814 | nonspell | (8.000, 381.177) | `stay` | 695/0 | 1.005/1.005 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 27920 | nonspell | (376.000, 432.000) | `up_left` | 172/0 | -2.781/-2.781 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30592 | 65 神技「八方龍殺陣」 | (167.672, 432.000) | `right_fast` | 1151/0 | 2.152/-2.322 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31339 | 65 神技「八方龍殺陣」 | (49.548, 432.000) | `right_fast` | 1051/0 | -3.479/-3.479 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32263 | 65 神技「八方龍殺陣」 | (296.223, 425.043) | `up` | 1179/0 | -2.080/-7.649 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35591 | nonspell | (370.343, 432.000) | `right_fast` | 83/0 | -3.720/-15.325 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39986 | 69 回霊「夢想封印　侘」 | (376.000, 226.548) | `stay` | 601/0 | -1.480/-1.480 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43119 | 73 大結界「博麗弾幕結界」 | (214.971, 388.929) | `down_left_fast` | 980/0 | -1.905/-1.905 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 7102 | 6976 | 3756 | 0 | 0 | 1034 | 110.754 | 0.217 |
| 57 夢境「二重大結界」 | 3 | 1087 | 1081 | 286 | 0 | 0 | 179 | 178.404 | 0.344 |
| 61 | 0 | 1014 | 1007 | 500 | 0 | 0 | 164 | 124.539 | 0.166 |
| 65 神技「八方龍殺陣」 | 3 | 908 | 900 | 760 | 0 | 0 | 162 | 64.882 | 0.378 |
| 69 回霊「夢想封印　侘」 | 1 | 1064 | 1058 | 740 | 0 | 0 | 177 | 91.107 | 0.198 |
| 73 大結界「博麗弾幕結界」 | 1 | 934 | 925 | 564 | 0 | 0 | 177 | 120.093 | 0.071 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.242 ms median and 28.892 ms p95.
- The full enemy sensor produced 6399 snapshots; capture read time was `{'median': 5.940900009591132, 'p95': 25.389599992195144, 'max': 53.69000000064261}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 11579 decisions retained at least one robust-union body (maximum 54); 6665 decisions contained latent contact-disabled geometry (maximum 54), and 5206 contained bounded inactive-slot memory (maximum 32). 377 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.6999969482421875, 'p95': 4.400001525878906, 'max': 12.090657552083334}` / `{'median': 2.792342185974121, 'p95': 3.9229583740234375, 'max': 63.6358642578125}` / `{'median': 0.012542963027954102, 'p95': 1.293428897857666, 'max': 63.6358642578125}`.
- The issue-time enemy guard retained 12109 observations, detected 4722 during-plan geometry changes, recertified 4722 decisions, and overrode 329 actions. Read/recertificate timing was `{'median': 1.7260999884456396, 'p95': 3.332399995997548, 'max': 15.475300009711646}` / `{'median': 2.4466499889967963, 'p95': 4.070100010721944, 'max': 15.27749998786021}` ms; 6685 issue captures contained latent bodies (maximum 54), and 5216 contained dormant bodies (maximum 32). Fresh/global transactions preserved 4393/4722 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9240 observations (9202 contact enabled, 38 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3968, '0x00587A90': 5272}`.
- The terminal-threat heuristic covered 12109 decisions with horizon counts `{'0': 527, '10': 11582}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 448, '3': 8266, '4': 3195, '5': 200}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 321, '2': 78, '3': 10767, '4': 943}`.
- Adaptive delay supports were `{'1,2': 79, '1,2,3': 152, '1,2,3,4': 167, '1,2,3,4,5': 72, '1,2,3,4,5,6': 36, '2,3': 253, '2,3,4': 1721, '2,3,4,5': 6519, '2,3,4,5,6': 2394, '3,4': 20, '3,4,5': 164, '3,4,5,6': 531, '4,5,6': 1}`; 364 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 18/158.
- Robust viability supplied 11947 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 6606 empty queried action sets. Recovery guidance was available/selected on 1671/0 empty-kernel queries; distant-kernel guidance was available/selected on 4119/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1851, '1': 1668, '2': 1212, '3': 1369, '4': 1456, '5': 1372, '6': 1510, '7': 1509}`.
- Global-horizon/local-prefix cross-tab covered 5976 decisions: 2 had a winning global state but unsafe selected prefix, 2753 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 478 selected actions were outside the reported winning set. 3669 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1893 unique policies with solve-time statistics `{'median': 115.075000008801, 'p95': 332.3806999978842, 'max': 441.2525999941863}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 1800.0}`. Policy status counts were `{'pending_future_epoch': 75, 'queryable': 11950, 'expired': 14}`; 92 robust-mode decisions had no query.
- Of 7029 unambiguous output transitions, 6729 (0.957) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 17, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 16 hit windows with a positive warning lead; those leads were `[3, 11, 13, 16, 16, 6, 4, 6, 0, 6, 3, 3, 6, 9, 0, 6, 6, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.571 during the 60 frames preceding a hit versus 0.205 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Focused Global/Local Investigation

The canonical nonspell hit was primarily an action-authority failure. At
frame 1707 the queried global state was winning with only
`stay/up/up_fast`, but ordinary-stage global authority was false and the
fresh-local transaction selected `down_left`. All 17 local actions were still
fresh-safe. Global loss followed at 1710. The fresh issue set remained
non-empty through frame 1909 and became empty only at 1912, where the
transaction knowingly selected least-bad `right_fast` with one predicted
collision and clearance `-5.255`; collision followed at 1915.

Whole-run delivery confirms that this was architectural rather than an
isolated tie-break. The rolling policy supplied 11,947 queries, 5,341 winning
states, and 4,119 losing states with distant recovery. It constrained zero
decisions and selected zero recoveries; 478 physically selected actions were
outside a reported winning set.

Later spell evidence is discovery-only because it follows deaths and Power
loss, but it matches the observed inability to travel toward distant open
space:

| Spell | Distant recovery queries | Selected | Edge-band occupancy | Recovery distance p50/max |
| --- | ---: | ---: | ---: | ---: |
| 57 夢境「二重大結界」 | 54 | 0 | 0.645 | 35.8/48.0 |
| 65 神技「八方龍殺陣」 | 235 | 0 | 0.633 | 178.9/350.9 |
| 69 回霊「夢想封印　侘」 | 562 | 0 | 0.615 | 80.0/376.6 |
| 73 大結界「博麗弾幕結界」 | 386 | 0 | 0.289 | 48.0/187.3 |

Local collisions separate into different causes. Eleven hits were modeled
committed-prefix collisions: the local checker knew every fresh action was
losing, but too late. One spell-57 hit is a future-hazard coverage failure:
frame 13686 certified `+47.357` clearance with 578 bullets, while three
physical frames later the pool held 581 and a newly present slot overlapped at
`-0.596`. Nonspell hit 22814 retained `+1.005` pipeline clearance with no
exact bullet/laser/body contact candidate and remains a sensor or unmodeled
hazard counterexample.

The early-spawn forecast was physically exercised but falsified as a general
later-wave observer. All 376 forecast observations recycled timeline 0,
instruction time 1, x=30, y=-16; only frames 401, 519, and 528 applied the
preference. The implementation aliases a zero runtime instruction pointer to
timeline start without distinguishing not-yet-started from completed state.
Keep full-health observed-body targeting, but withhold forecast objective
authority until timeline lifecycle is causal.

Primary compact analysis:
`artifacts/runtime_reports/th08_stage4a_global_local_investigation_20260731_142342.json`.
