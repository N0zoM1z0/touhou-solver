# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260727_182434

## Scope And Integrity

- Valid practice scope: `2..20663` (7557 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 0, at `[]`.
- Hard no-Bomb verification: **PASS** across 7557 decisions; mask/flag/action violations are all empty.

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
| nonspell | 0 | 4538 | 4437 | 693 | 0 | 3737 | 536 | 162.670 | 0.043 |
| 0 | 0 | 932 | 921 | 353 | 0 | 557 | 111 | 63.625 | 0.155 |
| 4 | 0 | 954 | 945 | 147 | 0 | 790 | 113 | 79.301 | 0.211 |
| 8 | 0 | 1133 | 1122 | 116 | 0 | 995 | 136 | 96.517 | 0.070 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 9.736 ms median and 17.271 ms p95.
- The full enemy sensor produced 3545 snapshots; capture read time was `{'median': 6.062900007236749, 'p95': 23.632000025827438, 'max': 42.26830002153292}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 7318 decisions retained at least one robust-union body (maximum 27); 1065 decisions contained latent contact-disabled geometry (maximum 12), and 3762 contained bounded inactive-slot memory (maximum 17). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7557 observations, detected 520 during-plan geometry changes, recertified 520 decisions, and overrode 2 actions. Read/recertificate timing was `{'median': 1.7648999928496778, 'p95': 3.736899991054088, 'max': 14.111600001342595}` / `{'median': 1.7623500025365502, 'p95': 3.4135999740101397, 'max': 11.459500005003065}` ms; 1072 issue captures contained latent bodies (maximum 12), and 3762 contained dormant bodies (maximum 17). Fresh/global transactions preserved 518/520 planned actions, relaxed 0 fresh/global empty intersections, inherited 2 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 5514 observations (5444 contact enabled, 70 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 3923, '0x00587A90': 1591}`.
- The terminal-threat heuristic covered 7557 decisions with horizon counts `{'0': 74, '10': 7079, '32': 404}`; it reported 0 collision and 31 sub-safety-clearance warnings, and relaxed 37 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 4322, '3': 3235}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 61, '2': 7493, '3': 3}`.
- Adaptive delay supports were `{'1,2': 28, '1,2,3': 69, '1,2,3,4': 334, '1,2,3,4,5': 18, '1,2,3,4,5,6': 31, '2,3': 1998, '2,3,4': 3686, '2,3,4,5': 982, '2,3,4,5,6': 411}`; 3 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 29/164.
- Robust viability supplied 7425 available policy queries (0 had new delay support outside the cached policy), constrained 6079 decisions, and exposed 1309 empty queried action sets. Recovery guidance was available/selected on 456/242 empty-kernel queries; distant-kernel guidance was available/selected on 837/830. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 12.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 81.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 80.0, 'p95': 230.7552816296953, 'max': 475.7141999141922}`, and `{'median': 0.0, 'p95': 13.888373136520386, 'max': 40.653703451156616}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1157, '1': 878, '2': 851, '3': 907, '4': 878, '5': 921, '6': 930, '7': 903}`.
- Global-horizon/local-prefix cross-tab covered 6677 decisions: 0 had a winning global state but unsafe selected prefix, 1154 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 28 selected actions were outside the reported winning set. 512 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 896 unique policies with solve-time statistics `{'median': 123.82864998653531, 'p95': 299.2822999949567, 'max': 425.67359999520704}` and first-observed ages `{'median': 2.0, 'p95': 4.0, 'max': 1791.0}`. Policy status counts were `{'pending_future_epoch': 77, 'queryable': 7427, 'expired': 10}`; 89 robust-mode decisions had no query.
- Of 2870 unambiguous output transitions, 2611 (0.910) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 0 hit windows with a positive warning lead; those leads were `[]` frames.
- Across all phases, bottom-eight-pixel occupancy was - during the 60 frames preceding a hit versus 0.083 outside those windows.
- Mean selected control-reserve deficit was - during the 60 frames preceding a hit versus 2.765 outside those windows.
- Soft recovery was selected on - of alive decisions in the 60-frame pre-hit windows versus 0.033 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 25.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
