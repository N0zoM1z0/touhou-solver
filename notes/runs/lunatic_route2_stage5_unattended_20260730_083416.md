# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260730_083416

## Scope And Integrity

- Valid practice scope: `1..43376` (12109 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- The supervisor selected no-save; no compatible native replay was created.
- Native hit edges: 11, at `[4323, 10886, 11402, 12256, 23249, 25167, 30956, 31980, 41571, 42205, 43073]`.
- Hard no-Bomb verification: **PASS** across 12109 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Priority-17 Publication Evidence

- The corrected deterministic report retains 30,904 native priority-17
  callback-exit events across 6,565 real ordered writes and 5,544 no-writes.
- All 6,565 pre/post-dispatch serial intervals are complete. Callback exit
  occurred inside 1,223 writes, and 478 events directly observed a
  non-final ordered mask during its controller dispatch.
- Consecutive retained callbacks contain 122 edges whose serial advances
  while `enemy_manager_frame` is unchanged. This is direct physical evidence
  that manager frame is not the universal publication clock.
- Among fully retained transaction prefixes, the held final mask was first
  observed after callback-step counts `{1: 4893, 2: 1648, 3: 17, 4: 2, 5: 1}`.
  One transaction was replaced after one complete callback interval without
  its transient final mask being observed. This censor prevents an
  unconditional completion-deadline upper bound.
- Four capture batches overflowed during three long non-decision gaps and the
  after-key-release final drain. Their unretained event counts were
  `46/296/520/852`. The compact report therefore correctly has
  `integrity.passed=false`; these gaps forbid global negative claims but do
  not erase the retained positive witnesses above.
- The report is
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260730_083416.priority17_publication_report.json`,
  SHA-256
  `395ce5384e14e815afe6a5ce1977b165a94344906f3eb483a56c2484056be9b8`.
  Its source is the ignored 501,784,095-byte raw JSONL, SHA-256
  `319b22f94dfdb2ce5322a0779839f94e6d03b6866c2d985e75e7c323473cae2f`.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F4323-T1`. It occurred during a nonspell phase at player (84.751, 432.000), with 462 bullets and 0 lasers. The projectile model reported pipeline clearance -5.043.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 9
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4323 | nonspell | (84.751, 432.000) | `up` | 462/0 | -5.043/-5.043 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 10886 | nonspell | (43.989, 417.858) | `up_right_fast` | 926/0 | -2.463/-6.764 | 14f/23f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 11402 | nonspell | (8.000, 412.000) | `up_fast` | 896/0 | -1.781/-6.394 | 19f/29f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 12256 | nonspell | (348.025, 426.343) | `up_right_fast` | 229/0 | -2.160/-3.702 | 3f/8f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23249 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_right_fast` | 1049/0 | -2.992/-2.992 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 25167 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 432.000) | `up_right` | 1105/0 | -3.862/-3.862 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30956 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (129.794, 432.000) | `right_fast` | 1001/0 | -5.369/-6.767 | 4f/25f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31980 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (191.244, 432.000) | `up_fast` | 992/0 | -3.843/-5.960 | 5f/21f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 41571 | 115 散符「真実の月(インビジブルフルムーン)」 | (32.172, 429.172) | `up_right_fast` | 1195/0 | 1.124/-0.541 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 42205 | 115 散符「真実の月(インビジブルフルムーン)」 | (106.521, 432.000) | `up_fast` | 1070/0 | -2.734/-2.734 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 43073 | 115 散符「真実の月(インビジブルフルムーン)」 | (273.609, 428.000) | `up_fast` | 1072/0 | 0.149/-0.425 | 0f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 8132 | 0 | 0 | 0 | 0 | 0 | - | 0.408 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 916 | 0 | 0 | 0 | 0 | 0 | - | 0.460 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 827 | 0 | 0 | 0 | 0 | 0 | - | 0.338 |
| 111 | 0 | 1054 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1180 | 0 | 0 | 0 | 0 | 0 | - | 0.430 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.222 ms median and 28.822 ms p95.
- The full enemy sensor produced 6370 snapshots; capture read time was `{'median': 4.3876999989151955, 'p95': 11.880400008521974, 'max': 54.7927999868989}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 7 phase-counter discontinuities were excluded; 11376 decisions retained at least one robust-union body (maximum 42); 8820 decisions contained latent contact-disabled geometry (maximum 42), and 4381 contained bounded inactive-slot memory (maximum 36). 300 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.8057785034179688, 'p95': 3.510457992553711, 'max': 15.39216533460115}` / `{'median': 0.8466530442237854, 'p95': 3.135854959487915, 'max': 4.707546710968018}` / `{'median': 6.556708243010689e-08, 'p95': 0.9622166156768799, 'max': 16.22435656346773}`.
- The issue-time enemy guard retained 12109 observations, detected 3531 during-plan geometry changes, recertified 3531 decisions, and overrode 46 actions. Read/recertificate timing was `{'median': 1.8138999585062265, 'p95': 3.6348000867292285, 'max': 9.111599996685982}` / `{'median': 2.953800023533404, 'p95': 6.4749999437481165, 'max': 22.429700009524822}` ms; 8793 issue captures contained latent bodies (maximum 42), and 4374 contained dormant bodies (maximum 36). Fresh/global transactions preserved 3485/3531 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8638 observations (8610 contact enabled, 28 anticipatory, 0 errors). 8638 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8638}`.
- The terminal-threat heuristic covered 12109 decisions with horizon counts `{'0': 616, '10': 11493}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 542, '3': 9118, '4': 1655, '5': 794}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 329, '2': 279, '3': 10012, '4': 1464, '5': 25}`.
- Adaptive delay supports were `{'1': 2, '1,2': 189, '1,2,3': 256, '1,2,3,4': 87, '1,2,3,4,5': 350, '1,2,3,4,5,6': 292, '2,3': 328, '2,3,4': 1935, '2,3,4,5': 3306, '2,3,4,5,6': 4445, '3,4': 1, '3,4,5': 47, '3,4,5,6': 871}`; 175 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 54/451.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6350 unambiguous output transitions, 5113 (0.805) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 10, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[9, 23, 29, 8, 7, 4, 25, 21, 0, 6, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.800 during the 60 frames preceding a hit versus 0.359 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
