# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_171633

## Scope And Integrity

- Valid practice scope: `2..41630` (12032 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 8, at `[12324, 14116, 24615, 25486, 30504, 33449, 36710, 40462]`.
- Hard no-Bomb verification: **PASS** across 12032 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F12324-T1`. It occurred during a nonspell phase at player (376.000, 424.000), with 355 bullets and 0 lasers. The projectile model reported pipeline clearance 0.531.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 5 |
| `modeled_committed_prefix_collision` | 3 |

Contributing factors:

- `fast_mode`: 6
- `playfield_boundary`: 4
- `pool_density_over_1000`: 2
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 12324 | nonspell | (376.000, 424.000) | `up_fast` | 355/0 | 0.531/-2.250 | 5f/13f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14116 | nonspell | (28.764, 426.343) | `up_right_fast` | 385/0 | -1.373/-18.039 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24615 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `left` | 1103/0 | -4.166/-4.166 | 0f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25486 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right_fast` | 967/0 | -1.991/-1.991 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30504 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (16.485, 344.582) | `up_left_fast` | 1002/0 | -4.945/-5.748 | 8f/8f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33449 | nonspell | (368.000, 410.667) | `left_fast` | 397/0 | -0.396/-1.349 | 4f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36710 | 111 懶惰「生神停止(マインドストッパー)」 | (196.510, 191.286) | `up_fast` | 383/0 | -2.679/-2.679 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40462 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `down` | 962/0 | -1.347/-1.347 | 2f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 8202 | 8073 | 5692 | 0 | 2344 | 1047 | 121.221 | 0.193 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 933 | 926 | 600 | 0 | 319 | 175 | 103.501 | 0.279 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 1 | 695 | 687 | 470 | 0 | 215 | 131 | 82.890 | 0.309 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1025 | 1017 | 410 | 0 | 596 | 151 | 88.776 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1177 | 1159 | 715 | 0 | 424 | 181 | 58.251 | 0.470 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 10.679 ms median and 21.877 ms p95.
- The full enemy sensor produced 6243 snapshots; capture read time was `{'median': 5.714499973692, 'p95': 24.71289993263781, 'max': 47.038499964401126}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11383 decisions retained at least one robust-union body (maximum 42); 4468 decisions contained latent contact-disabled geometry (maximum 41), and 5764 contained bounded inactive-slot memory (maximum 37). 166 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 1.0, 'max': 3.559112548828125}` / `{'median': 0.0, 'p95': 1.0, 'max': 3.5591018199920654}` / `{'median': 0.0, 'p95': 8.742277657347586e-08, 'max': 1.0000076293945312}`.
- The issue-time enemy guard retained 12032 observations, detected 2131 during-plan geometry changes, recertified 2131 decisions, and overrode 46 actions. Read/recertificate timing was `{'median': 1.723150024190545, 'p95': 3.4189000725746155, 'max': 12.044899980537593}` / `{'median': 2.816000021994114, 'p95': 6.101900013163686, 'max': 16.600399976596236}` ms; 4446 issue captures contained latent bodies (maximum 41), and 5772 contained dormant bodies (maximum 37). Fresh/global transactions preserved 2085/2131 planned actions, relaxed 12 fresh/global empty intersections, inherited 19 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8437 observations (8409 contact enabled, 28 anticipatory, 0 errors). 8437 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8437}`.
- The terminal-threat heuristic covered 12032 decisions with horizon counts `{'0': 72, '10': 11708, '32': 252}`; it reported 0 collision and 57 sub-safety-clearance warnings, and relaxed 77 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1047, '3': 9362, '4': 1478, '5': 145}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 4637, '3': 6169, '4': 1226}`.
- Adaptive delay supports were `{'1,2,3': 170, '1,2,3,4': 63, '1,2,3,4,5': 45, '2,3': 2354, '2,3,4': 4361, '2,3,4,5': 2814, '2,3,4,5,6': 1541, '3,4': 4, '3,4,5': 13, '3,4,5,6': 667}`; 84 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 42/337.
- Robust viability supplied 11862 available policy queries (0 had new delay support outside the cached policy), constrained 3898 decisions, and exposed 7887 empty queried action sets. Recovery guidance was available/selected on 1038/442 empty-kernel queries; distant-kernel guidance was available/selected on 6112/5834. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 121.85236969382254, 'p95': 345.39253031876643, 'max': 505.9644256269407}`, and `{'median': 0.0, 'p95': 23.730607986450195, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1862, '1': 1579, '2': 1251, '3': 1398, '4': 1384, '5': 1478, '6': 1487, '7': 1423}`.
- Global-horizon/local-prefix cross-tab covered 8646 decisions: 2 had a winning global state but unsafe selected prefix, 5724 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 37 selected actions were outside the reported winning set. 1916 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1685 unique policies with solve-time statistics `{'median': 98.81220001261681, 'p95': 314.9503000313416, 'max': 459.6795999677852}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1808.0}`. Policy status counts were `{'pending_future_epoch': 67, 'queryable': 11863, 'expired': 34}`; 102 robust-mode decisions had no query.
- Of 6188 unambiguous output transitions, 5651 (0.913) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[13, 5, 4, 8, 8, 9, 5, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.430 during the 60 frames preceding a hit versus 0.213 outside those windows.
- Mean selected control-reserve deficit was 12.424 during the 60 frames preceding a hit versus 4.042 outside those windows.
- Soft recovery was selected on 0.017 of alive decisions in the 60-frame pre-hit windows versus 0.037 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 42.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
