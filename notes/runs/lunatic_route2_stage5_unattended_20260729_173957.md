# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260729_173957

## Scope And Integrity

- Valid practice scope: `1..42021` (11597 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[2069, 4339, 10942, 12268, 12898, 13997, 22831, 23379, 28817, 30275, 35316, 39806]`.
- Hard no-Bomb verification: **PASS** across 11597 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F2069-T1`. It occurred during a nonspell phase at player (376.000, 424.000), with 663 bullets and 0 lasers. The projectile model reported pipeline clearance -2.222.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |
| `observed_enemy_body_overlap` | 1 |

Contributing factors:

- `playfield_boundary`: 11
- `fast_mode`: 8
- `pool_density_over_1000`: 3
- `enemy_body_absent_from_action_snapshot`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2069 | nonspell | (376.000, 424.000) | `up` | 663/0 | -2.222/-2.276 | 2f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4339 | nonspell | (376.000, 432.000) | `up_left_fast` | 328/0 | -3.044/-3.044 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10942 | nonspell | (351.326, 386.023) | `up_left_fast` | 879/0 | -14.196/-14.196 | 0f/0f | `observed_enemy_body_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12268 | nonspell | (376.000, 432.000) | `stay` | 377/0 | -1.398/-1.398 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12898 | nonspell | (376.000, 345.807) | `down_left_fast` | 258/0 | -2.948/-2.948 | 2f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13997 | nonspell | (60.508, 432.000) | `up_right` | 424/0 | -1.880/-11.823 | 6f/13f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 22831 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_fast` | 1048/0 | -3.489/-3.489 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23379 | 103 幻波「赤眼催眠(マインドブローイング)」 | (260.043, 428.000) | `up_left_fast` | 1019/0 | 2.213/-0.140 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 28817 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (46.491, 432.000) | `down_left` | 968/0 | -5.584/-5.584 | 0f/32f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30275 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (91.580, 432.000) | `down_left_fast` | 1004/0 | -6.921/-7.365 | 40f/52f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35316 | nonspell | (8.000, 432.000) | `right_fast` | 401/0 | -2.400/-2.400 | 2f/4f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 39806 | 115 散符「真実の月(インビジブルフルムーン)」 | (20.504, 432.000) | `up_right_fast` | 962/0 | -1.234/-1.929 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 7657 | 7525 | 4993 | 0 | 2488 | 997 | 136.644 | 0.168 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 915 | 900 | 481 | 0 | 416 | 172 | 115.589 | 0.237 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 754 | 744 | 528 | 0 | 214 | 149 | 90.515 | 0.337 |
| 111 | 0 | 1115 | 1108 | 664 | 0 | 439 | 176 | 95.481 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 1156 | 1140 | 727 | 0 | 399 | 179 | 60.918 | 0.462 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 1 exact same-epoch enemy-body overlaps; 1 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.556 ms median and 23.680 ms p95.
- The full enemy sensor produced 6181 snapshots; capture read time was `{'median': 5.649100057780743, 'p95': 26.661999989300966, 'max': 50.51049997564405}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 10927 decisions retained at least one robust-union body (maximum 40); 4481 decisions contained latent contact-disabled geometry (maximum 40), and 5944 contained bounded inactive-slot memory (maximum 38). 188 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.1075286865234375, 'max': 4.707542419433594}` / `{'median': 0.9099338054656982, 'p95': 3.9172096252441406, 'max': 4.707547187805176}` / `{'median': 4.371138828673793e-08, 'p95': 1.0373306274414062, 'max': 5.138305902481079}`.
- The issue-time enemy guard retained 11597 observations, detected 2367 during-plan geometry changes, recertified 2367 decisions, and overrode 40 actions. Read/recertificate timing was `{'median': 1.8527000211179256, 'p95': 3.6457000533118844, 'max': 18.18400004412979}` / `{'median': 3.2037999480962753, 'p95': 6.809200043790042, 'max': 18.470600014552474}` ms; 4460 issue captures contained latent bodies (maximum 39), and 5936 contained dormant bodies (maximum 38). Fresh/global transactions preserved 2327/2367 planned actions, relaxed 6 fresh/global empty intersections, inherited 6 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8140 observations (8113 contact enabled, 27 anticipatory, 0 errors). 8140 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8140}`.
- The terminal-threat heuristic covered 11597 decisions with horizon counts `{'0': 69, '10': 11273, '32': 255}`; it reported 4 collision and 94 sub-safety-clearance warnings, and relaxed 68 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 392, '3': 8640, '4': 1841, '5': 724}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 832, '3': 9450, '4': 1284, '5': 31}`.
- Adaptive delay supports were `{'1,2,3': 196, '1,2,3,4': 64, '2,3': 138, '2,3,4': 2335, '2,3,4,5': 4659, '2,3,4,5,6': 3487, '3,4': 15, '3,4,5': 6, '3,4,5,6': 690, '4,5,6': 7}`; 202 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 28/321.
- Robust viability supplied 11417 available policy queries (0 had new delay support outside the cached policy), constrained 3956 decisions, and exposed 7393 empty queried action sets. Recovery guidance was available/selected on 1086/431 empty-kernel queries; distant-kernel guidance was available/selected on 5721/5479. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 128.0, 'p95': 349.4452746854649, 'max': 499.85597925802585}`, and `{'median': 0.0, 'p95': 21.96969747543335, 'max': 40.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1816, '1': 1529, '2': 1218, '3': 1334, '4': 1373, '5': 1318, '6': 1464, '7': 1365}`.
- Global-horizon/local-prefix cross-tab covered 7786 decisions: 1 had a winning global state but unsafe selected prefix, 4906 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 28 selected actions were outside the reported winning set. 1976 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1673 unique policies with solve-time statistics `{'median': 107.9030999680981, 'p95': 346.4172000531107, 'max': 462.0896999258548}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 66, 'queryable': 11417, 'expired': 21}`; 87 robust-mode decisions had no query.
- Of 5807 unambiguous output transitions, 4994 (0.860) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[6, 5, 0, 5, 6, 13, 8, 0, 32, 52, 4, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.467 during the 60 frames preceding a hit versus 0.186 outside those windows.
- Mean selected control-reserve deficit was 11.643 during the 60 frames preceding a hit versus 4.594 outside those windows.
- Soft recovery was selected on 0.018 of alive decisions in the 60-frame pre-hit windows versus 0.036 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## SEM-TIMER Physical Slice

- This was the fixed observer-off physical falsifier for executable checkpoint
  `e309c81`. It fails the preregistered survival threshold: 12 hits is above
  `<=10`. The result is retained as a failed physical gate, not relabeled as
  a timer pass or an NMNB improvement.
- The timer-aware velocity-lookahead consumer was absent on 7,657 decisions
  and present on 3,940 decisions, first at frame 21,751 and last at frame
  42,018. The canonical hit at frame 2,069 and the first six hits all precede
  the first consumer row. Therefore this run does not causally implicate the
  SEM-TIMER correction in the canonical failure and does not justify rollback.
- All 3,940 consumer rows carry
  `th08-ecl-velocity-lookahead-v2-native-timer-components` and component
  identity `th08-native-timer-components-v1-00447421`; elapsed, fraction, and
  scale identity fields agree on every row. There are 2,794 complete schedules
  and 1,146 explicit `unsupported_control_flow` prefixes, with no recorded
  lookahead error. The trace retains 9,413 prefix events across 2,699 rows.
- Every observed fraction is `0x00000000` and every observed scale is
  `0x3F800000` (`1.0`). This physically exercises delivery and the historical
  zero-fraction/unit-scale slice only. Nonzero-fraction, carry, and nonunit
  scale authority remains offline.
- A fresh affine inference over all 33 unique live roots selects Stage-5
  runtime base `0x0B1D0048`, mapping 33/33 roots to exact instruction
  boundaries in decoded `ecldata5.ecl` SHA-256
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`;
  the runner-up maps 19. The corrected mapping yields 3,835 future-time roots,
  105 exact-equality roots, zero past-time roots, and zero unmapped roots.
  This address correlation is consistent with the IDA equality gate but is
  not a fresh runtime-byte-identity capture.
- An initial manual check incorrectly borrowed Stage-4A runtime base
  `0x0B1D1430` and falsely produced past-time roots. No repository or IDA
  semantic conclusion uses that decode. Runtime-PC normalization must infer
  or capture the base for the current stage/session rather than reuse one
  from another workload.

## Next Correction Gate

Stop physical expansion under CE-0184. Do not repeat this Stage-5 version or
advance to Stage 3, Stage 4A, or Final B from this result. Retain the canonical
frame-2,069 viability/prefix failure independently of SEM-TIMER, then continue
the roadmap at `SEM-SCALE`. The next physical run must belong to a new,
immutable causal correction and compare first-hit state, per-phase position,
warning lead, and consumer exercise—not aggregate count alone.
