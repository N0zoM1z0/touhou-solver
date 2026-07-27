# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_144128

## Scope And Integrity

- Valid practice scope: `1..20768` (7502 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 0, at `[]`.
- Hard no-Bomb verification: **PASS** across 7502 decisions; mask/flag/action violations are all empty.

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
| nonspell | 0 | 4363 | 4263 | 514 | 0 | 3713 | 516 | 171.855 | 0.092 |
| 0 | 0 | 1057 | 1049 | 309 | 0 | 731 | 127 | 64.131 | 0.094 |
| 4 | 0 | 954 | 945 | 194 | 0 | 746 | 113 | 76.103 | 0.102 |
| 8 | 0 | 1128 | 1121 | 152 | 0 | 953 | 137 | 93.144 | 0.099 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.972 ms median and 18.166 ms p95.
- The full enemy sensor produced 3536 snapshots; capture read time was `{'median': 6.096149998484179, 'p95': 24.11779999965802, 'max': 37.074799998663366}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7270 decisions retained at least one robust-union body (maximum 28); 1158 decisions contained latent contact-disabled geometry (maximum 11), and 3449 contained bounded inactive-slot memory (maximum 23). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7502 observations, detected 481 during-plan geometry changes, recertified 481 decisions, and overrode 0 actions. Read/recertificate timing was `{'median': 1.7697500006761402, 'p95': 3.674300038255751, 'max': 12.3668999876827}` / `{'median': 1.8848000327125192, 'p95': 3.799700003582984, 'max': 11.874399962835014}` ms; 1169 issue captures contained latent bodies (maximum 11), and 3452 contained dormant bodies (maximum 24). Fresh/global transactions preserved 481/481 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5508 observations (5436 contact enabled, 72 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3808, '0x00587A90': 1700}`.
- The terminal-threat heuristic covered 7502 decisions with horizon counts `{'0': 72, '10': 6986, '32': 444}`; it reported 0 collision and 23 sub-safety-clearance warnings, and relaxed 66 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 3084, '3': 4418}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 12, '2': 6829, '3': 661}`.
- Adaptive delay supports were `{'1,2,3': 222, '1,2,3,4': 238, '1,2,3,4,5,6': 140, '2,3': 1684, '2,3,4': 3763, '2,3,4,5': 833, '2,3,4,5,6': 622}`; 0 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 26/176.
- Robust viability supplied 7378 available policy queries (0 had new delay support outside the cached policy), constrained 6143 decisions, and exposed 1169 empty queried action sets. Recovery guidance was available/selected on 480/234 empty-kernel queries; distant-kernel guidance was available/selected on 646/646. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 12.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 84.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 64.0, 'p95': 172.32527382830412, 'max': 268.2088738278434}`, and `{'median': 0.0, 'p95': 7.133289098739624, 'max': 28.255536556243896}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1139, '1': 888, '2': 823, '3': 933, '4': 833, '5': 941, '6': 898, '7': 923}`.
- Global-horizon/local-prefix cross-tab covered 6669 decisions: 0 had a winning global state but unsafe selected prefix, 1028 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 47 selected actions were outside the reported winning set. 474 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 893 unique policies with solve-time statistics `{'median': 113.17520000739023, 'p95': 321.8139000236988, 'max': 434.6279000164941}` and first-observed ages `{'median': 2.0, 'p95': 5.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 76, 'queryable': 7378, 'expired': 10}`; 86 robust-mode decisions had no query.
- Of 2756 unambiguous output transitions, 2488 (0.903) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 0 hit windows with a positive warning lead; those leads were `[]` frames.
- Across all phases, bottom-eight-pixel occupancy was - during the 60 frames preceding a hit versus 0.094 outside those windows.
- Mean selected control-reserve deficit was - during the 60 frames preceding a hit versus 2.827 outside those windows.
- Soft recovery was selected on - of alive decisions in the 60-frame pre-hit windows versus 0.032 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 8.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
