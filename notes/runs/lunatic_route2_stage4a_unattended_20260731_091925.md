# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_091925

## Scope And Integrity

- Valid practice scope: `2..44375` (14131 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[2555, 4083, 8903, 11571, 12075, 12920, 13463, 21974, 22638, 31516, 37270, 38170, 41989]`.
- Hard no-Bomb verification: **PASS** across 14131 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2555-T1`. It occurred during a nonspell phase at player (376.000, 423.515), with 296 bullets and 0 lasers. The projectile model reported pipeline clearance -2.277.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 5 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 10
- `playfield_boundary`: 9
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2555 | nonspell | (376.000, 423.515) | `up_fast` | 296/0 | -2.277/-2.277 | 0f/2f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 4083 | nonspell | (376.000, 432.000) | `up_left` | 906/0 | -2.105/-2.105 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 8903 | nonspell | (68.209, 432.000) | `right_fast` | 424/0 | 2.390/-4.728 | 6f/19f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 11571 | 57 夢境「二重大結界」 | (13.657, 422.343) | `up_right_fast` | 571/0 | 0.014/-1.179 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12075 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 606/0 | -1.697/-1.697 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12920 | 57 夢境「二重大結界」 | (13.657, 422.343) | `up_right_fast` | 630/0 | 0.175/-0.653 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 13463 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 586/0 | -1.781/-1.781 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 21974 | nonspell | (27.885, 432.000) | `up_fast` | 712/0 | 0.680/0.680 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `robust_action_set_exhausted_before_hit` |
| discovery | 22638 | nonspell | (33.309, 432.000) | `stay` | 573/0 | -1.053/-1.283 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 31516 | 65 神技「八方龍殺陣」 | (214.407, 427.121) | `down_right_fast` | 1218/0 | -0.188/-1.833 | 4f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 37270 | 69 回霊「夢想封印　侘」 | (8.000, 425.100) | `up_fast` | 514/0 | -3.989/-3.989 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 38170 | 69 回霊「夢想封印　侘」 | (8.000, 363.084) | `down_right` | 637/0 | -3.228/-3.228 | 4f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 41989 | 73 大結界「博麗弾幕結界」 | (219.549, 391.826) | `down_left_fast` | 1000/0 | -1.427/-1.427 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 8419 | 0 | 0 | 0 | 0 | 0 | - | 0.210 |
| 57 夢境「二重大結界」 | 4 | 1293 | 0 | 0 | 0 | 0 | 0 | - | 0.351 |
| 61 | 0 | 1209 | 0 | 0 | 0 | 0 | 0 | - | 0.174 |
| 65 神技「八方龍殺陣」 | 1 | 846 | 0 | 0 | 0 | 0 | 0 | - | 0.372 |
| 69 回霊「夢想封印　侘」 | 2 | 1243 | 0 | 0 | 0 | 0 | 0 | - | 0.229 |
| 73 大結界「博麗弾幕結界」 | 1 | 1121 | 0 | 0 | 0 | 0 | 0 | - | 0.016 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 16.282 ms median and 22.719 ms p95.
- The full enemy sensor produced 6963 snapshots; capture read time was `{'median': 4.597300001478288, 'p95': 7.947699996293522, 'max': 39.63179999846034}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 9.0}` frames, and 6 phase-counter discontinuities were excluded; 13404 decisions retained at least one robust-union body (maximum 50); 7704 decisions contained latent contact-disabled geometry (maximum 50), and 5496 contained bounded inactive-slot memory (maximum 29). 234 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.6176223754882812, 'p95': 4.3929595947265625, 'max': 6.007991790771484}` / `{'median': 2.779696822166443, 'p95': 3.8987724781036377, 'max': 4.157550811767578}` / `{'median': 0.6467118263244629, 'p95': 2.0633621215820312, 'max': 8.20001220703125}`.
- The issue-time enemy guard retained 14131 observations, detected 4941 during-plan geometry changes, recertified 4941 decisions, and overrode 33 actions. Read/recertificate timing was `{'median': 1.618000002054032, 'p95': 2.657199998793658, 'max': 6.39690000389237}` / `{'median': 2.0644000032916665, 'p95': 3.3174999989569187, 'max': 12.29320000129519}` ms; 7688 issue captures contained latent bodies (maximum 50), and 5487 contained dormant bodies (maximum 35). Fresh/global transactions preserved 4908/4941 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 10654 observations (10607 contact enabled, 47 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 10654}`.
- The terminal-threat heuristic covered 14131 decisions with horizon counts `{'0': 727, '10': 13404}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2014, '3': 11140, '4': 977}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 503, '2': 6894, '3': 6734}`.
- Adaptive delay supports were `{'1': 271, '1,2': 147, '1,2,3': 436, '1,2,3,4': 181, '1,2,3,4,5': 39, '1,2,3,4,5,6': 51, '2,3': 1827, '2,3,4': 7088, '2,3,4,5': 1991, '2,3,4,5,6': 1656, '3,4': 247, '3,4,5': 181, '3,4,5,6': 16}`; 46 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 43/240.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 7414 unambiguous output transitions, 6909 (0.932) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 13}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 13 hit windows with a positive warning lead; those leads were `[2, 8, 19, 5, 5, 5, 4, 3, 8, 7, 6, 13, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.610 during the 60 frames preceding a hit versus 0.201 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
