# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260801_163434

## Scope And Integrity

- Valid practice scope: `1..27563` (8728 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 4, at `[1253, 2141, 8884, 16134]`.
- Hard no-Bomb verification: **PASS** across 8728 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F1253-T1`. It occurred during a nonspell phase at player (376.000, 432.000), with 219 bullets and 0 lasers. The projectile model reported pipeline clearance -2.407.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |

Contributing factors:

- `playfield_boundary`: 4
- `fast_mode`: 3

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1253 | nonspell | (376.000, 432.000) | `up_left_fast` | 219/0 | -2.407/-11.915 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 2141 | nonspell | (316.229, 432.000) | `right_fast` | 567/0 | -8.914/-8.914 | 6f/13f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 8884 | nonspell | (372.468, 432.000) | `up_left` | 406/0 | -1.604/-1.604 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 16134 | 38 始符「エフェメラリティ137」 | (309.853, 432.000) | `up_right_fast` | 211/0 | -1.798/-1.798 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 4751 | 336 | 13 | 0 | 329 | 22 | 166.706 | 0.229 |
| 35 | 0 | 899 | 863 | 718 | 0 | 0 | 83 | 41.791 | 0.255 |
| 38 始符「エフェメラリティ137」 | 1 | 799 | 786 | 472 | 0 | 0 | 109 | 99.302 | 0.225 |
| 42 | 0 | 755 | 748 | 597 | 0 | 0 | 121 | 42.085 | 0.265 |
| 46 | 0 | 874 | 868 | 734 | 0 | 0 | 142 | 54.765 | 0.336 |
| 50 | 0 | 650 | 642 | 466 | 0 | 0 | 116 | 82.371 | 0.334 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.045 ms median and 31.264 ms p95.
- The full enemy sensor produced 4515 snapshots; capture read time was `{'median': 5.473700002767146, 'p95': 18.47559999441728, 'max': 85.6742000032682}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 37.0}` frames, and 3 phase-counter discontinuities were excluded; 8542 decisions retained at least one robust-union body (maximum 30); 7973 decisions contained latent contact-disabled geometry (maximum 30), and 2538 contained bounded inactive-slot memory (maximum 17). 78 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.7320556640625, 'p95': 3.4675445556640625, 'max': 3.767486572265625}` / `{'median': 1.732049584388733, 'p95': 2.616792917251587, 'max': 3.7674901485443115}` / `{'median': 5.900859832763672e-06, 'p95': 1.6629791259765625, 'max': 4.2806396484375}`.
- The issue-time enemy guard retained 8728 observations, detected 1157 during-plan geometry changes, recertified 1157 decisions, and overrode 14 actions. Read/recertificate timing was `{'median': 1.4982499997131526, 'p95': 2.7483000012580305, 'max': 107.87469998467714}` / `{'median': 2.258399996208027, 'p95': 5.265300016617402, 'max': 104.52610001084395}` ms; 7977 issue captures contained latent bodies (maximum 30), and 2535 contained dormant bodies (maximum 17). Fresh/global transactions preserved 1143/1157 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 6861 observations (6791 contact enabled, 70 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0058CE60': 1797, '0x00605610': 5064}`.
- The terminal-threat heuristic covered 8728 decisions with horizon counts `{'0': 22, '10': 8706}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 23, '3': 7426, '4': 860, '5': 336, '6': 83}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 1, '2': 410, '3': 7989, '4': 328}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3,4': 31, '2,3': 910, '2,3,4': 2708, '2,3,4,5': 3044, '2,3,4,5,6': 2015, '3,4': 19}`; 22 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 37/291.
- Robust viability supplied 4243 available policy queries (0 had new delay support outside the cached policy), constrained 329 decisions, and exposed 3000 empty queried action sets. Recovery guidance was available/selected on 770/0 empty-kernel queries; distant-kernel guidance was available/selected on 2000/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 649, '1': 595, '2': 467, '3': 460, '4': 520, '5': 479, '6': 547, '7': 526}`.
- Global-horizon/local-prefix cross-tab covered 3381 decisions: 0 had a winning global state but unsafe selected prefix, 2441 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 145 selected actions were outside the reported winning set. 608 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 593 unique policies with solve-time statistics `{'median': 59.29819997982122, 'p95': 150.79149999655783, 'max': 2352.884499996435}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 89.0}`. Policy status counts were `{'pending_future_epoch': 70, 'queryable': 4246, 'expired': 3322}`; 3395 robust-mode decisions had no query.
- Of 5467 unambiguous output transitions, 5229 (0.956) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 3, 'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[8, 13, 5, 3]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.640 during the 60 frames preceding a hit versus 0.250 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 117.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

This run is the source-v14/lease-v4 physical gate. Source projections were
complete for 801/1,275 roots versus 645/1,235 in source-v13 `155718`; 58
roots carried the full H268 versus 47. The targeted main `0x05`/`0x06` and
captured movement-state-2 failures disappeared. This is observed semantic
closure, not a causal hit-count win: the 4/3 total/ordinary result and the
prior 7/5 result use different RNG roots.

Exact prepublication, delayed, and lease authority was effective on
316/7/5 issues. Three leases were created and four renewed, but every
ordinary hit's prior 240-frame window still contained zero exact authority
and reported `future_policy_unavailable`. Before canonical hit f1253, the
first full-H268 root was f1223. Its source became ready/submitted at f1230,
but the 2352.884 ms solve completed only at f1371, after the hit and after
the policy epoch had expired. The 30-frame physical warning cannot cover the
observed roughly 141-frame publication pipeline.

The next correction must increase causally complete source lead by lowering
the newly reached exact main/auxiliary semantics. Dominant reached blockers
are dynamic type/color, auxiliary `0x25`, main/auxiliary `0x6F`, main
float-add `0x19`, auxiliary return `0x35`, and later transform programs.
Unsupported or hidden state remains fail closed. Do not compensate with a
stage waypoint, scalar reserve, or local-ranking relaxation.

Accepted replay SHA-256:
`0c65e8835b7cd9c6837cc0cbf37575552dc86e660d11d1e6c0cc7cc057bda80e`.
It is Route 2, Lunatic, Stage 3, RNG seed 29213, with an empty Bomb-press
list. Process/input cleanup completed.
