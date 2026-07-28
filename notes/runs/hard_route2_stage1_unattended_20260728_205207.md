# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260728_205207

## Scope And Integrity

- Valid practice scope: `1..20448` (7401 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 0, at `[]`.
- Hard no-Bomb verification: **PASS** across 7401 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

No native hit edge occurred in this scoped practice trace.

This is a physical no-Bomb pass for the captured scope. It does not by itself establish repeatability; retain repeated clean focused passes before promoting the phase.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |

Contributing factors:


## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 0 | 4302 | 4200 | 557 | 0 | 3625 | 506 | 152.549 | 0.089 |
| 0 | 0 | 1059 | 1049 | 234 | 0 | 812 | 125 | 56.742 | 0.128 |
| 4 | 0 | 947 | 937 | 183 | 0 | 742 | 114 | 72.460 | 0.148 |
| 8 | 0 | 1093 | 1085 | 192 | 0 | 880 | 137 | 93.711 | 0.079 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.503 ms median and 17.094 ms p95.
- The full enemy sensor produced 3482 snapshots; capture read time was `{'median': 5.824449995998293, 'p95': 23.15879997331649, 'max': 38.344700005836785}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7167 decisions retained at least one robust-union body (maximum 28); 1083 decisions contained latent contact-disabled geometry (maximum 11), and 4022 contained bounded inactive-slot memory (maximum 19). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7401 observations, detected 559 during-plan geometry changes, recertified 559 decisions, and overrode 0 actions. Read/recertificate timing was `{'median': 1.690699951723218, 'p95': 3.557800082489848, 'max': 12.561900075525045}` / `{'median': 1.6642999835312366, 'p95': 3.237399971112609, 'max': 9.65430005453527}` ms; 1081 issue captures contained latent bodies (maximum 11), and 4022 contained dormant bodies (maximum 21). Fresh/global transactions preserved 559/559 planned actions, relaxed 0 fresh/global empty intersections, inherited 3 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5371 observations (5298 contact enabled, 73 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5371}`.
- The terminal-threat heuristic covered 7401 decisions with horizon counts `{'0': 74, '10': 6865, '32': 462}`; it reported 1 collision and 24 sub-safety-clearance warnings, and relaxed 46 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3980, '3': 3421}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 13, '2': 7201, '3': 187}`.
- Adaptive delay supports were `{'1,2': 6, '1,2,3': 102, '1,2,3,4': 215, '1,2,3,4,5': 115, '2,3': 2316, '2,3,4': 3813, '2,3,4,5': 466, '2,3,4,5,6': 368}`; 0 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 16/101.
- Robust viability supplied 7271 available policy queries (0 had new delay support outside the cached policy), constrained 6059 decisions, and exposed 1166 empty queried action sets. Recovery guidance was available/selected on 443/255 empty-kernel queries; distant-kernel guidance was available/selected on 672/670. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 11.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 73.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 80.0, 'p95': 213.46662502602135, 'max': 380.3156583681508}`, and `{'median': 0.0, 'p95': 12.0, 'max': 34.0776309967041}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1132, '1': 860, '2': 856, '3': 854, '4': 891, '5': 846, '6': 951, '7': 881}`.
- Global-horizon/local-prefix cross-tab covered 6486 decisions: 0 had a winning global state but unsafe selected prefix, 996 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 39 selected actions were outside the reported winning set. 550 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 882 unique policies with solve-time statistics `{'median': 106.6041499725543, 'p95': 298.71839995030314, 'max': 416.7232000036165}` and first-observed ages `{'median': 1.0, 'p95': 4.0, 'max': 1789.0}`. Policy status counts were `{'pending_future_epoch': 76, 'queryable': 7273, 'expired': 11}`; 89 robust-mode decisions had no query.
- Of 2872 unambiguous output transitions, 2641 (0.920) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 0 hit windows with a positive warning lead; those leads were `[]` frames.
- Across all phases, bottom-eight-pixel occupancy was - during the 60 frames preceding a hit versus 0.101 outside those windows.
- Mean selected control-reserve deficit was - during the 60 frames preceding a hit versus 2.615 outside those windows.
- Soft recovery was selected on - of alive decisions in the 60-frame pre-hit windows versus 0.034 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 27.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
