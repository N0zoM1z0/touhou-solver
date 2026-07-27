# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_173735

## Scope And Integrity

- Valid practice scope: `1..20950` (7680 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 0, at `[]`.
- Hard no-Bomb verification: **PASS** across 7680 decisions; mask/flag/action violations are all empty.

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
| nonspell | 0 | 4527 | 4423 | 614 | 0 | 3787 | 536 | 158.424 | 0.090 |
| 0 | 0 | 1064 | 1054 | 264 | 0 | 785 | 127 | 65.765 | 0.151 |
| 4 | 0 | 959 | 944 | 139 | 0 | 802 | 113 | 81.026 | 0.113 |
| 8 | 0 | 1130 | 1118 | 136 | 0 | 972 | 136 | 98.414 | 0.133 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.677 ms median and 17.330 ms p95.
- The full enemy sensor produced 3602 snapshots; capture read time was `{'median': 6.0744500369764864, 'p95': 24.210200004745275, 'max': 37.55680000176653}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7437 decisions retained at least one robust-union body (maximum 22); 940 decisions contained latent contact-disabled geometry (maximum 10), and 3846 contained bounded inactive-slot memory (maximum 16). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7680 observations, detected 512 during-plan geometry changes, recertified 512 decisions, and overrode 0 actions. Read/recertificate timing was `{'median': 1.775450014974922, 'p95': 3.741299966350198, 'max': 13.891599955968559}` / `{'median': 1.7350499983876944, 'p95': 3.774799988605082, 'max': 12.040600006002933}` ms; 941 issue captures contained latent bodies (maximum 10), and 3835 contained dormant bodies (maximum 16). Fresh/global transactions preserved 512/512 planned actions, relaxed 0 fresh/global empty intersections, inherited 2 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5655 observations (5581 contact enabled, 74 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3932, '0x00587A90': 1723}`.
- The terminal-threat heuristic covered 7680 decisions with horizon counts `{'0': 76, '10': 7196, '32': 408}`; it reported 0 collision and 30 sub-safety-clearance warnings, and relaxed 40 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4181, '3': 3499}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 7424, '3': 256}`.
- Adaptive delay supports were `{'1,2': 78, '1,2,3': 62, '1,2,3,4': 163, '1,2,3,4,5': 95, '2,3': 1942, '2,3,4': 4481, '2,3,4,5': 527, '2,3,4,5,6': 332}`; 0 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 25/155.
- Robust viability supplied 7539 available policy queries (0 had new delay support outside the cached policy), constrained 6346 decisions, and exposed 1153 empty queried action sets. Recovery guidance was available/selected on 378/194 empty-kernel queries; distant-kernel guidance was available/selected on 745/745. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 12.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 81.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 71.55417527999327, 'p95': 176.0, 'max': 242.1239352067449}`, and `{'median': 0.0, 'p95': 15.2347731590271, 'max': 28.448287963867188}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1172, '1': 857, '2': 896, '3': 913, '4': 894, '5': 931, '6': 943, '7': 933}`.
- Global-horizon/local-prefix cross-tab covered 6804 decisions: 0 had a winning global state but unsafe selected prefix, 1017 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 29 selected actions were outside the reported winning set. 506 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 912 unique policies with solve-time statistics `{'median': 117.25564996595494, 'p95': 307.5727000250481, 'max': 401.85780002502725}` and first-observed ages `{'median': 1.0, 'p95': 4.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 79, 'queryable': 7539, 'expired': 10}`; 89 robust-mode decisions had no query.
- Of 2964 unambiguous output transitions, 2738 (0.924) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 0 hit windows with a positive warning lead; those leads were `[]` frames.
- Across all phases, bottom-eight-pixel occupancy was - during the 60 frames preceding a hit versus 0.108 outside those windows.
- Mean selected control-reserve deficit was - during the 60 frames preceding a hit versus 2.400 outside those windows.
- Soft recovery was selected on - of alive decisions in the 60-frame pre-hit windows versus 0.024 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 15.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
