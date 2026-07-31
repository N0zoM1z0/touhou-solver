# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_152921

## Scope And Integrity

- Valid practice scope: `1..45169` (12029 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 17, at `[914, 2250, 4167, 8871, 10948, 11557, 12034, 12599, 13248, 22759, 28173, 28965, 31230, 35545, 36211, 39547, 43067]`.
- Hard no-Bomb verification: **PASS** across 12029 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F914-T1`. It occurred during a nonspell phase at player (376.000, 426.343), with 136 bullets and 0 lasers. The projectile model reported pipeline clearance -2.824.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Experiment Activation Audit

- The pre-exhaustion flag was enabled on all 12,029 decisions, but supplied
  zero authority-eligible, applicable, selected-authority, or effective-at-
  issue decisions.
- All 7,202 nonspell decisions failed as
  `player_transition_or_predeath`; the other 4,827 decisions were correctly
  excluded as active spells. Early kill consequently applied zero
  preferences.
- Native code at `0x0044AB40`, `0x0044C390`, and `0x0044C650` shows that
  player `+0xE2A68` retains the deathbomb-window limit installed on a hit. It
  is not a zero-when-alive predicate. The trace confirms 5,862 normal
  phase-0/action-phase-0 decisions with retained value 10.
- Removing only that bad gate offline does not rescue the witness. The filter
  still permits active/issued `down_left` at global exhaustion frame 835,
  permits all 17 actions when the uncontrollable prefix dominates at frame
  850, and permits all 17 actions at the saturated corner at frame 910.
- Contact bullet slot 455 first enters the retained nearby set at decision
  frame 817. The policy used through frame 833 was rooted in hazard snapshot
  801 and still called `down_left` winning; the snapshot-818 policy first
  delivered at frame 835 and reported an empty action set. The compact trace
  does not establish whether slot 455 was already outside the nearby set in
  snapshot 801, but the hazard-version/pre-publication seam is observed.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 11 |
| `observed_bullet_overlap` | 5 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 15
- `fast_mode`: 14
- `corridor_deadline_miss`: 5
- `pool_density_over_1000`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 914 | nonspell | (376.000, 426.343) | `up_left_fast` | 136/0 | -2.824/-2.824 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 2250 | nonspell | (180.450, 432.000) | `right_fast` | 62/0 | -2.394/-5.612 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4167 | nonspell | (8.000, 405.586) | `up_left_fast` | 1114/0 | -3.568/-3.568 | 4f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8871 | nonspell | (22.442, 432.000) | `up_left_fast` | 580/0 | -1.518/-2.836 | 3f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10948 | nonspell | (8.000, 420.000) | `up_fast` | 168/0 | -14.334/-26.316 | 6f/11f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11557 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 442/0 | -1.791/-1.791 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12034 | 57 夢境「二重大結界」 | (8.000, 432.000) | `right_fast` | 598/0 | -3.378/-3.378 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12599 | 57 夢境「二重大結界」 | (32.485, 345.183) | `up_fast` | 617/0 | -1.032/-1.032 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13248 | 57 夢境「二重大結界」 | (10.828, 427.704) | `down_right_fast` | 594/0 | 0.995/-1.317 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22759 | nonspell | (69.058, 432.000) | `down_right_fast` | 549/0 | 0.378/-1.856 | 3f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28173 | nonspell | (376.000, 432.000) | `up_left_fast` | 126/0 | -2.434/-2.434 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28965 | nonspell | (24.000, 432.000) | `right_fast` | 147/0 | -2.749/-2.749 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31230 | 65 神技「八方龍殺陣」 | (248.178, 432.000) | `down_left` | 1052/0 | -2.264/-2.264 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35545 | nonspell | (376.000, 416.000) | `up_fast` | 123/0 | -3.543/-6.429 | 10f/15f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36211 | nonspell | (376.000, 412.000) | `up_left` | 111/0 | 1.326/-9.435 | 14f/19f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39547 | 69 回霊「夢想封印　侘」 | (376.000, 432.000) | `up_left_fast` | 689/0 | -1.703/-1.703 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43067 | 73 大結界「博麗弾幕結界」 | (159.318, 376.316) | `down` | 1240/0 | -3.422/-3.422 | 3f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 10 | 7202 | 7072 | 3819 | 0 | 0 | 1046 | 111.196 | 0.249 |
| 57 夢境「二重大結界」 | 4 | 1109 | 1100 | 200 | 0 | 0 | 180 | 179.953 | 0.343 |
| 61 | 0 | 940 | 932 | 430 | 0 | 0 | 150 | 130.740 | 0.241 |
| 65 神技「八方龍殺陣」 | 1 | 781 | 772 | 635 | 0 | 0 | 145 | 65.041 | 0.454 |
| 69 回霊「夢想封印　侘」 | 1 | 1068 | 1062 | 712 | 0 | 0 | 177 | 90.349 | 0.190 |
| 73 大結界「博麗弾幕結界」 | 1 | 929 | 920 | 546 | 0 | 0 | 175 | 121.370 | 0.070 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.112 ms median and 28.991 ms p95.
- The full enemy sensor produced 6376 snapshots; capture read time was `{'median': 6.280499990680255, 'p95': 29.973899989272468, 'max': 56.55829999886919}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 6 phase-counter discontinuities were excluded; 11501 decisions retained at least one robust-union body (maximum 58); 6729 decisions contained latent contact-disabled geometry (maximum 58), and 4878 contained bounded inactive-slot memory (maximum 25). 271 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.758575439453125, 'p95': 4.1184234619140625, 'max': 10.072265625}` / `{'median': 2.797915458679199, 'p95': 3.8505401611328125, 'max': 55.821083068847656}` / `{'median': 0.009016156196594238, 'p95': 1.293428897857666, 'max': 55.821083068847656}`.
- The issue-time enemy guard retained 12029 observations, detected 4508 during-plan geometry changes, recertified 4508 decisions, and overrode 71 actions. Read/recertificate timing was `{'median': 1.712699988274835, 'p95': 3.339400005643256, 'max': 13.818799998261966}` / `{'median': 2.448500003083609, 'p95': 4.2092999938176945, 'max': 13.651000001118518}` ms; 6722 issue captures contained latent bodies (maximum 58), and 4885 contained dormant bodies (maximum 25). Fresh/global transactions preserved 4437/4508 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9156 observations (9119 contact enabled, 37 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 9156}`.
- The terminal-threat heuristic covered 12029 decisions with horizon counts `{'0': 528, '10': 11501}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 464, '3': 7864, '4': 3554, '5': 147}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 101, '2': 325, '3': 10320, '4': 1279, '5': 4}`.
- Adaptive delay supports were `{'1,2': 221, '1,2,3': 61, '1,2,3,4': 176, '1,2,3,4,5': 52, '1,2,3,4,5,6': 46, '2,3': 292, '2,3,4': 2044, '2,3,4,5': 5253, '2,3,4,5,6': 3037, '3,4': 20, '3,4,5': 617, '3,4,5,6': 205, '4,5,6': 5}`; 95 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 41/308.
- Robust viability supplied 11858 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 6342 empty queried action sets. Recovery guidance was available/selected on 1707/0 empty-kernel queries; distant-kernel guidance was available/selected on 3680/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1918, '1': 1562, '2': 1278, '3': 1361, '4': 1434, '5': 1386, '6': 1450, '7': 1469}`.
- Global-horizon/local-prefix cross-tab covered 5916 decisions: 0 had a winning global state but unsafe selected prefix, 2760 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 442 selected actions were outside the reported winning set. 3776 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1873 unique policies with solve-time statistics `{'median': 117.30650000390597, 'p95': 329.47080000303686, 'max': 437.85879999632016}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 1791.0}`. Policy status counts were `{'pending_future_epoch': 70, 'queryable': 11860, 'expired': 17}`; 89 robust-mode decisions had no query.
- Of 6805 unambiguous output transitions, 6502 (0.955) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 17}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 15 hit windows with a positive warning lead; those leads were `[4, 0, 11, 13, 11, 4, 4, 3, 9, 9, 3, 5, 0, 15, 19, 6, 10]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.482 during the 60 frames preceding a hit versus 0.238 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 10.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Do not rerun after merely removing the predeath check. Replace scalar minimum
boundary reserve with a causal, set-valued pre-publication predecessor that
retains hazard-space reachability across active/held/pending pickup order,
solver publication lead, and bounded ordinary hostile births. Keep the
shadow future slab non-authoritative until that coverage is established.
Only then repeat Stage 4A; the conditional Stage-5 follow-up was not earned.
