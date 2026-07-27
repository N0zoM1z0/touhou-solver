# TH08 Stage 5 No-Bomb Practice Review: hard_route2_stage5_unattended_20260727_185422

## Scope And Integrity

- Valid practice scope: `2..40448` (12602 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 8, at `[11557, 14457, 22900, 24323, 29045, 29503, 32734, 35477]`.
- Hard no-Bomb verification: **PASS** across 12602 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S5-F11557-T1`. It occurred during a nonspell phase at player (364.616, 432.000), with 544 bullets and 0 lasers. The projectile model reported pipeline clearance -2.275.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 6
- `fast_mode`: 5
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11557 | nonspell | (364.616, 432.000) | `up_fast` | 544/0 | -2.275/-2.275 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14457 | nonspell | (344.747, 432.000) | `down_left` | 496/0 | -1.559/-3.237 | 2f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22900 | 102 幻波「赤眼催眠(マインドブローイング)」 | (165.950, 428.000) | `up_right_fast` | 897/0 | -2.142/-2.142 | 2f/2f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24323 | 102 幻波「赤眼催眠(マインドブローイング)」 | (314.638, 428.000) | `up_left_fast` | 840/0 | -2.335/-2.730 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29045 | 106 狂視「狂視調律(イリュージョンシーカー)」 | (306.007, 423.868) | `up_right_fast` | 1016/0 | -5.957/-5.957 | 34f/124f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29503 | 106 狂視「狂視調律(イリュージョンシーカー)」 | (189.257, 432.000) | `down_left` | 1019/0 | -4.559/-5.133 | 11f/26f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32734 | nonspell | (376.000, 428.747) | `up_left_fast` | 483/0 | -2.100/-2.100 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35477 | 110 懶惰「生神停止(マインドストッパー)」 | (207.054, 201.584) | `up_right` | 295/0 | -1.573/-1.573 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 8244 | 8106 | 5381 | 0 | 2670 | 1023 | 126.353 | 0.144 |
| 102 幻波「赤眼催眠(マインドブローイング)」 | 2 | 988 | 976 | 542 | 0 | 419 | 128 | 108.504 | 0.406 |
| 106 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 646 | 637 | 398 | 0 | 239 | 115 | 79.212 | 0.322 |
| 110 懶惰「生神停止(マインドストッパー)」 | 1 | 1297 | 1287 | 651 | 0 | 620 | 178 | 90.668 | 0.000 |
| 114 | 0 | 1427 | 1410 | 1103 | 0 | 291 | 181 | 50.691 | 0.511 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 10.436 ms median and 19.648 ms p95.
- The full enemy sensor produced 6234 snapshots; capture read time was `{'median': 5.364800017559901, 'p95': 22.153400001116097, 'max': 44.330400007311255}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11955 decisions retained at least one robust-union body (maximum 42); 4969 decisions contained latent contact-disabled geometry (maximum 41), and 6533 contained bounded inactive-slot memory (maximum 41). 137 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.600006103515625, 'p95': 4.35321044921875, 'max': 5.220672607421875}` / `{'median': 0.6000000238418579, 'p95': 4.35321044921875, 'max': 4.697332382202148}` / `{'median': 0.0, 'p95': 0.6000070571899414, 'max': 0.6000137329101562}`.
- The issue-time enemy guard retained 12602 observations, detected 2202 during-plan geometry changes, recertified 2202 decisions, and overrode 33 actions. Read/recertificate timing was `{'median': 1.763049978762865, 'p95': 3.541400015819818, 'max': 15.650700021069497}` / `{'median': 2.1615499863401055, 'p95': 5.31739997677505, 'max': 11.811000003945082}` ms; 4927 issue captures contained latent bodies (maximum 41), and 6541 contained dormant bodies (maximum 41). Fresh/global transactions preserved 2169/2202 planned actions, relaxed 10 fresh/global empty intersections, inherited 24 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8961 observations (8932 contact enabled, 29 anticipatory, 0 errors). 8961 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8961}`.
- The terminal-threat heuristic covered 12602 decisions with horizon counts `{'0': 72, '10': 12117, '32': 413}`; it reported 2 collision and 90 sub-safety-clearance warnings, and relaxed 102 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2088, '3': 10163, '4': 287, '5': 64}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 6882, '3': 5430, '4': 290}`.
- Adaptive delay supports were `{'1,2': 29, '1,2,3': 117, '1,2,3,4': 209, '1,2,3,4,5': 59, '2,3': 2074, '2,3,4': 7161, '2,3,4,5': 1459, '2,3,4,5,6': 1244, '3,4': 4, '3,4,5,6': 246}`; 61 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 48/330.
- Robust viability supplied 12416 available policy queries (0 had new delay support outside the cached policy), constrained 4239 decisions, and exposed 8075 empty queried action sets. Recovery guidance was available/selected on 1220/531 empty-kernel queries; distant-kernel guidance was available/selected on 6010/5812. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 116.48175822848829, 'p95': 334.0898082851376, 'max': 465.1021393199563}`, and `{'median': 0.0, 'p95': 17.494617462158203, 'max': 40.94372248649597}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1993, '1': 1545, '2': 1338, '3': 1497, '4': 1483, '5': 1526, '6': 1568, '7': 1466}`.
- Global-horizon/local-prefix cross-tab covered 9356 decisions: 1 had a winning global state but unsafe selected prefix, 6014 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 36 selected actions were outside the reported winning set. 1942 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1625 unique policies with solve-time statistics `{'median': 99.60490005323663, 'p95': 310.12820004252717, 'max': 440.5681000207551}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1802.0}`. Policy status counts were `{'pending_future_epoch': 66, 'queryable': 12419, 'expired': 34}`; 103 robust-mode decisions had no query.
- Of 6443 unambiguous output transitions, 5851 (0.908) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 8}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 8 hit windows with a positive warning lead; those leads were `[7, 6, 2, 4, 124, 26, 5, 8]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.528 during the 60 frames preceding a hit versus 0.193 outside those windows.
- Mean selected control-reserve deficit was 10.223 during the 60 frames preceding a hit versus 3.291 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.041 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 52.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
