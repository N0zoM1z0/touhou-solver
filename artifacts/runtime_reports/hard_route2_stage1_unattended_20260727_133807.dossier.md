# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_133807

## Scope And Integrity

- Valid practice scope: `1..20892` (7541 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[5262]`.
- Hard no-Bomb verification: **PASS** across 7541 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `HARD-S0-F5262-T1`. It occurred during spell 0 `蛍符「地上の流星」` at player (232.731, 432.000), with 208 bullets and 0 lasers. The projectile model reported pipeline clearance -1.956.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 1 |

Contributing factors:

- `fast_mode`: 1
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 5262 | 0 蛍符「地上の流星」 | (232.731, 432.000) | `up_left_fast` | 208/0 | -1.956/-3.107 | 7f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 0 | 4444 | 4341 | 1042 | 0 | 3268 | 534 | 164.623 | 0.094 |
| 0 蛍符「地上の流星」 | 1 | 1021 | 1013 | 239 | 0 | 770 | 123 | 64.698 | 0.165 |
| 4 | 0 | 946 | 938 | 252 | 0 | 683 | 115 | 75.503 | 0.115 |
| 8 | 0 | 1130 | 1121 | 183 | 0 | 926 | 136 | 91.504 | 0.053 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.839 ms median and 18.090 ms p95.
- The full enemy sensor produced 3548 snapshots; capture read time was `{'median': 5.883100035134703, 'p95': 23.958500009030104, 'max': 39.86880002776161}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7302 decisions retained at least one robust-union body (maximum 23); 1011 decisions contained latent contact-disabled geometry (maximum 12), and 3851 contained bounded inactive-slot memory (maximum 16). 5 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.64447021484375, 'p95': 1.96771240234375, 'max': 1.96771240234375}` / `{'median': 1.6444637775421143, 'p95': 1.9677150249481201, 'max': 1.9677150249481201}` / `{'median': 2.6226043701171875e-06, 'p95': 3.039836883544922e-06, 'max': 6.4373016357421875e-06}`.
- The issue-time enemy guard retained 7541 observations, detected 476 during-plan geometry changes, recertified 476 decisions, and overrode 4 actions. Read/recertificate timing was `{'median': 1.7383999656885862, 'p95': 3.600900003220886, 'max': 12.291099992580712}` / `{'median': 1.9099500204902142, 'p95': 3.6761999945156276, 'max': 6.122899998445064}` ms; 1010 issue captures contained latent bodies (maximum 12), and 3851 contained dormant bodies (maximum 16). Fresh/global transactions preserved 472/476 planned actions, relaxed 0 fresh/global empty intersections, inherited 2 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5562 observations (5491 contact enabled, 71 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3890, '0x0058CE60': 1672}`.
- The terminal-threat heuristic covered 7541 decisions with horizon counts `{'0': 74, '10': 6944, '32': 523}`; it reported 0 collision and 42 sub-safety-clearance warnings, and relaxed 50 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 2741, '3': 4800}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 26, '2': 5865, '3': 1647, '5': 3}`.
- Adaptive delay supports were `{'1,2': 51, '1,2,3': 77, '1,2,3,4': 235, '1,2,3,4,5': 177, '1,2,3,4,5,6': 67, '2,3': 1494, '2,3,4': 3943, '2,3,4,5': 957, '2,3,4,5,6': 539, '5,6': 1}`; 7 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 17/129.
- Robust viability supplied 7413 available policy queries (0 had new delay support outside the cached policy), constrained 5647 decisions, and exposed 1716 empty queried action sets. Recovery guidance was available/selected on 504/307 empty-kernel queries; distant-kernel guidance was available/selected on 1147/1142. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 10.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 62.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 81.58431221748455, 'p95': 208.0, 'max': 401.2779585275025}`, and `{'median': 0.0, 'p95': 19.757580518722534, 'max': 39.64679455757141}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1129, '1': 927, '2': 795, '3': 931, '4': 864, '5': 932, '6': 893, '7': 942}`.
- Global-horizon/local-prefix cross-tab covered 6565 decisions: 0 had a winning global state but unsafe selected prefix, 1431 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 37 selected actions were outside the reported winning set. 468 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 908 unique policies with solve-time statistics `{'median': 121.90024997107685, 'p95': 300.4208999918774, 'max': 400.4211000283249}` and first-observed ages `{'median': 2.0, 'p95': 3.0, 'max': 1791.0}`. Policy status counts were `{'pending_future_epoch': 76, 'queryable': 7411, 'expired': 13}`; 87 robust-mode decisions had no query.
- Of 3156 unambiguous output transitions, 2875 (0.911) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[12]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.448 during the 60 frames preceding a hit versus 0.098 outside those windows.
- Mean selected control-reserve deficit was 7.583 during the 60 frames preceding a hit versus 3.287 outside those windows.
- Soft recovery was selected on 0.034 of alive decisions in the 60-frame pre-hit windows versus 0.039 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
