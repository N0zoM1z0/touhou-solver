# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260801_051939

## Scope And Integrity

- Valid practice scope: `1..44960` (11763 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 15, at `[1957, 2383, 4165, 7039, 10814, 12980, 14449, 23153, 24224, 32085, 32657, 37734, 41028, 42603, 44419]`.
- Hard no-Bomb verification: **PASS** across 11763 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1957-T1`. It occurred during a nonspell phase at player (113.642, 277.218), with 486 bullets and 0 lasers. The projectile model reported pipeline clearance -3.040.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 6 |

Contributing factors:

- `playfield_boundary`: 10
- `fast_mode`: 9
- `pool_density_over_1000`: 4
- `action_lag_over_model`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1957 | nonspell | (113.642, 277.218) | `up_right` | 486/0 | -3.040/-3.040 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 2383 | nonspell | (10.426, 432.000) | `up_fast` | 323/0 | -3.266/-3.266 | 0f/15f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 4165 | nonspell | (374.374, 430.374) | `up_left` | 442/0 | -3.364/-3.364 | 0f/19f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 7039 | nonspell | (363.400, 427.616) | `up_left_fast` | 698/0 | 2.071/-1.801 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 10814 | nonspell | (79.231, 432.000) | `left_fast` | 924/0 | -3.249/-3.249 | 6f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12980 | nonspell | (376.000, 421.100) | `down_left_fast` | 319/0 | -0.524/-0.734 | 6f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 14449 | nonspell | (24.567, 413.600) | `up` | 475/0 | -6.273/-6.273 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23153 | 103 幻波「赤眼催眠(マインドブローイング)」 | (140.677, 432.000) | `up_right` | 870/0 | 0.676/-0.485 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24224 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_left_fast` | 1036/0 | -1.799/-1.799 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32085 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (74.414, 432.000) | `right` | 1002/0 | -5.866/-5.866 | 7f/17f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32657 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (202.065, 387.168) | `up_left_fast` | 1009/0 | -7.289/-7.289 | 54f/65f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37734 | nonspell | (331.511, 432.000) | `up_fast` | 419/0 | -1.947/-2.165 | 0f/3f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 41028 | 111 懶惰「生神停止(マインドストッパー)」 | (224.309, 196.937) | `right_fast` | 345/0 | -1.832/-1.832 | 0f/15f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42603 | 115 散符「真実の月(インビジブルフルムーン)」 | (160.412, 430.374) | `up_right` | 1144/0 | -1.934/-1.934 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 44419 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `up_fast` | 969/0 | -3.564/-3.795 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 8062 | 0 | 0 | 0 | 0 | 0 | - | 0.399 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 692 | 655 | 277 | 0 | 0 | 119 | 120.606 | 0.369 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 977 | 972 | 786 | 0 | 0 | 217 | 74.826 | 0.290 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1017 | 1011 | 599 | 0 | 0 | 179 | 72.177 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 2 | 1015 | 1009 | 695 | 0 | 0 | 183 | 67.802 | 0.436 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.578 ms median and 33.457 ms p95.
- The full enemy sensor produced 6483 snapshots; capture read time was `{'median': 5.518799996934831, 'p95': 26.48659999249503, 'max': 64.21060001594014}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 23.0}` frames, and 7 phase-counter discontinuities were excluded; 11116 decisions retained at least one robust-union body (maximum 42); 8703 decisions contained latent contact-disabled geometry (maximum 41), and 4212 contained bounded inactive-slot memory (maximum 37). 364 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.796295166015625, 'p95': 5.122035980224609, 'max': 7.003364562988281}` / `{'median': 0.7962954044342041, 'p95': 4.110467910766602, 'max': 4.6973161697387695}` / `{'median': 0.0, 'p95': 1.9806594848632812, 'max': 4.1483519077301025}`.
- The issue-time enemy guard retained 11763 observations, detected 3460 during-plan geometry changes, recertified 3460 decisions, and overrode 57 actions. Read/recertificate timing was `{'median': 1.6533000161871314, 'p95': 3.2552000193390995, 'max': 75.50020000780933}` / `{'median': 3.1507999810855836, 'p95': 6.730799999786541, 'max': 111.00879998411983}` ms; 8680 issue captures contained latent bodies (maximum 41), and 4213 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3403/3460 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8730 observations (8704 contact enabled, 26 anticipatory, 0 errors). 8730 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8730}`.
- The terminal-threat heuristic covered 11763 decisions with horizon counts `{'0': 539, '10': 11224}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 486, '3': 6583, '4': 2659, '5': 1318, '6': 717}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 266, '2': 386, '3': 8337, '4': 2706, '5': 68}`.
- Adaptive delay supports were `{'1,2': 161, '1,2,3': 78, '1,2,3,4': 193, '1,2,3,4,5': 21, '1,2,3,4,5,6': 301, '2,3': 709, '2,3,4': 1973, '2,3,4,5': 2691, '2,3,4,5,6': 3802, '3,4': 62, '3,4,5': 523, '3,4,5,6': 1004, '4,5,6': 245}`; 288 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 47/271.
- Robust viability supplied 3647 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2357 empty queried action sets. Recovery guidance was available/selected on 187/0 empty-kernel queries; distant-kernel guidance was available/selected on 1511/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 604, '1': 533, '2': 417, '3': 364, '4': 403, '5': 454, '6': 441, '7': 431}`.
- Global-horizon/local-prefix cross-tab covered 1354 decisions: 1 had a winning global state but unsafe selected prefix, 675 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 14 selected actions were outside the reported winning set. 1514 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 698 unique policies with solve-time statistics `{'median': 75.72165000601672, 'p95': 182.34479997772723, 'max': 269.38139999401756}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 8.0}`. Policy status counts were `{'pending_future_epoch': 38, 'queryable': 3647, 'expired': 3}`; 41 robust-mode decisions had no query.
- Of 6182 unambiguous output transitions, 5798 (0.938) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 1, 'robust_action_set_exhausted_before_hit': 7, 'global_viability_kernel_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 14 hit windows with a positive warning lead; those leads were `[0, 15, 19, 7, 6, 11, 9, 4, 7, 17, 65, 3, 15, 6, 7]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.693 during the 60 frames preceding a hit versus 0.346 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
