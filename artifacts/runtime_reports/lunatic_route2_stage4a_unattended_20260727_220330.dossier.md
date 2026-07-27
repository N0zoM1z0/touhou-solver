# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260727_220330

## Scope And Integrity

- Valid practice scope: `2..41645` (13295 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 7, at `[2775, 4158, 10484, 11966, 20720, 35517, 36397]`.
- Hard no-Bomb verification: **PASS** across 13295 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2775-T1`. It occurred during a nonspell phase at player (374.345, 432.000), with 544 bullets and 0 lasers. The projectile model reported pipeline clearance -1.305.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 5 |
| `modeled_committed_prefix_collision` | 2 |

Contributing factors:

- `fast_mode`: 6
- `playfield_boundary`: 5
- `corridor_deadline_miss`: 1
- `pool_density_over_1000`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2775 | nonspell | (374.345, 432.000) | `up_left_fast` | 544/0 | -1.305/-1.305 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4158 | nonspell | (313.331, 432.000) | `up_left_fast` | 1134/0 | -3.037/-3.037 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10484 | nonspell | (146.009, 403.268) | `up_fast` | 140/0 | -2.935/-2.935 | 2f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11966 | 57 夢境「二重大結界」 | (372.747, 432.000) | `up_fast` | 581/0 | -2.996/-2.996 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20720 | nonspell | (376.000, 400.198) | `left_fast` | 827/0 | -1.450/-14.961 | 2f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35517 | 69 回霊「夢想封印　侘」 | (300.668, 432.000) | `left` | 709/0 | 0.673/-1.921 | 2f/2f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36397 | 69 回霊「夢想封印　侘」 | (13.657, 407.626) | `down_right_fast` | 708/0 | -2.937/-2.937 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8015 | 7871 | 3705 | 0 | 4101 | 966 | 105.724 | 0.178 |
| 57 夢境「二重大結界」 | 1 | 1284 | 1275 | 446 | 0 | 806 | 179 | 159.663 | 0.417 |
| 61 | 0 | 800 | 788 | 186 | 0 | 598 | 96 | 111.345 | 0.142 |
| 65 | 0 | 766 | 755 | 693 | 0 | 62 | 100 | 57.768 | 0.475 |
| 69 回霊「夢想封印　侘」 | 2 | 1345 | 1336 | 691 | 0 | 641 | 181 | 90.935 | 0.075 |
| 73 | 0 | 1085 | 1075 | 686 | 0 | 376 | 177 | 105.336 | 0.072 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.975 ms median and 18.025 ms p95.
- The full enemy sensor produced 6489 snapshots; capture read time was `{'median': 5.88640000205487, 'p95': 22.409599972888827, 'max': 34.36990000773221}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 10.0}` frames, and 7 phase-counter discontinuities were excluded; 12893 decisions retained at least one robust-union body (maximum 59); 2950 decisions contained latent contact-disabled geometry (maximum 59), and 6361 contained bounded inactive-slot memory (maximum 53). 136 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.125335693359375, 'p95': 4.1184234619140625, 'max': 4.5454864501953125}` / `{'median': 3.0331568717956543, 'p95': 3.898771047592163, 'max': 3.961994171142578}` / `{'median': 0.5245990753173828, 'p95': 1.2934441566467285, 'max': 7.4000244140625}`.
- The issue-time enemy guard retained 13295 observations, detected 2178 during-plan geometry changes, recertified 2178 decisions, and overrode 39 actions. Read/recertificate timing was `{'median': 1.7326000379398465, 'p95': 3.4728999598883092, 'max': 14.920499990694225}` / `{'median': 1.8255499890074134, 'p95': 3.4841999877244234, 'max': 13.665599981322885}` ms; 2943 issue captures contained latent bodies (maximum 50), and 6360 contained dormant bodies (maximum 53). Fresh/global transactions preserved 2139/2178 planned actions, relaxed 2 fresh/global empty intersections, inherited 20 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9917 observations (9868 contact enabled, 49 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4228, '0x0059C9D0': 5689}`.
- The terminal-threat heuristic covered 13295 decisions with horizon counts `{'0': 78, '10': 12393, '32': 824}`; it reported 18 collision and 167 sub-safety-clearance warnings, and relaxed 109 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3141, '3': 9368, '4': 786}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 64, '2': 9191, '3': 3605, '4': 433, '5': 2}`.
- Adaptive delay supports were `{'1,2': 49, '1,2,3': 142, '1,2,3,4': 212, '1,2,3,4,5': 65, '1,2,3,4,5,6': 10, '2,3': 2246, '2,3,4': 7516, '2,3,4,5': 2099, '2,3,4,5,6': 951, '3,4': 4, '3,4,5': 1}`; 54 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 18/162.
- Robust viability supplied 13100 available policy queries (0 had new delay support outside the cached policy), constrained 6584 decisions, and exposed 6407 empty queried action sets. Recovery guidance was available/selected on 1959/899 empty-kernel queries; distant-kernel guidance was available/selected on 3746/3631. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 1.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 9.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 96.0, 'p95': 295.0254226333724, 'max': 502.41019097944263}`, and `{'median': 0.0, 'p95': 15.120963096618652, 'max': 35.586291551589966}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 2068, '1': 1614, '2': 1383, '3': 1596, '4': 1577, '5': 1584, '6': 1678, '7': 1600}`.
- Global-horizon/local-prefix cross-tab covered 9914 decisions: 2 had a winning global state but unsafe selected prefix, 4629 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 70 selected actions were outside the reported winning set. 1931 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1699 unique policies with solve-time statistics `{'median': 108.79229998681694, 'p95': 310.04859996028244, 'max': 415.58270005043596}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1792.0}`. Policy status counts were `{'pending_future_epoch': 75, 'queryable': 13100, 'expired': 11}`; 86 robust-mode decisions had no query.
- Of 6847 unambiguous output transitions, 6326 (0.924) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 7 hit windows with a positive warning lead; those leads were `[9, 9, 19, 5, 8, 2, 6]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.415 during the 60 frames preceding a hit versus 0.195 outside those windows.
- Mean selected control-reserve deficit was 9.010 during the 60 frames preceding a hit versus 3.492 outside those windows.
- Soft recovery was selected on 0.045 of alive decisions in the 60-frame pre-hit windows versus 0.070 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 54.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
