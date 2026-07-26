# TH08 Stage 1 No-Bomb Practice Review: hard_route2_stage1_unattended_20260726_175049

## Scope And Integrity

- Valid practice scope: `1..20468` (7099 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 0, at `[]`.
- Hard no-Bomb verification: **PASS** across 7099 decisions; mask/flag/action violations are all empty.

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
| nonspell | 0 | 4153 | 4042 | 618 | 0 | 3389 | 480 | 199.631 | 0.063 |
| 0 | 0 | 1009 | 1001 | 322 | 0 | 669 | 125 | 76.957 | 0.131 |
| 4 | 0 | 908 | 889 | 151 | 0 | 727 | 109 | 92.729 | 0.061 |
| 8 | 0 | 1029 | 1017 | 68 | 0 | 939 | 133 | 117.051 | 0.067 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 12.117 ms median and 20.208 ms p95.
- The full enemy sensor produced 3483 snapshots; capture read time was `{'median': 10.452600021380931, 'p95': 25.084400025662035, 'max': 42.81200002878904}`, snapshot age was `{'median': 4.0, 'p95': 6.0, 'max': 8.0}` frames, and 3 phase-counter discontinuities were excluded; 6857 decisions retained at least one robust-union body (maximum 31); 992 decisions contained latent contact-disabled geometry (maximum 10), and 3340 contained bounded inactive-slot memory (maximum 25). 0 body samples retained observed world-motion estimates; world/internal speed and disagreement were `None` / `None` / `None`.
- The issue-time enemy guard retained 7099 observations, detected 530 during-plan geometry changes, recertified 530 decisions, and overrode 197 actions. Read/recertificate timing was `{'median': 1.7798999906517565, 'p95': 3.285999991931021, 'max': 15.1968999998644}` / `{'median': 2.3383499938063323, 'p95': 4.684899991843849, 'max': 11.053800000809133}` ms; 990 issue captures contained latent bodies (maximum 10), and 3339 contained dormant bodies (maximum 25).
- The synchronous spell-owner guard retained 5114 observations (5040 contact enabled, 74 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 5114}`.
- The terminal-threat heuristic covered 7099 decisions with horizon counts `{'0': 79, '10': 6548, '32': 472}`; it reported 0 collision and 25 sub-safety-clearance warnings, and relaxed 66 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1722, '3': 5377}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 87, '2': 6223, '3': 789}`.
- Adaptive delay supports were `{'1,2': 160, '1,2,3': 23, '1,2,3,4': 218, '1,2,3,4,5': 128, '1,2,3,4,5,6': 80, '2': 1, '2,3': 518, '2,3,4': 3669, '2,3,4,5': 1409, '2,3,4,5,6': 892, '3,4': 1}`; 199 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 22/131.
- Robust viability supplied 6949 available policy queries (0 had new delay support outside the cached policy), constrained 5724 decisions, and exposed 1159 empty queried action sets. Recovery guidance was available/selected on 484/285 empty-kernel queries; distant-kernel guidance was available/selected on 640/634. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 12.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 79.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 81.58431221748455, 'p95': 224.57070156189118, 'max': 458.4495610206209}`, and `{'median': 0.0, 'p95': 16.0, 'max': 38.73690152168274}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1059, '1': 873, '2': 838, '3': 878, '4': 795, '5': 867, '6': 817, '7': 822}`.
- Global-horizon/local-prefix cross-tab covered 6206 decisions: 0 had a winning global state but unsafe selected prefix, 974 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 41 selected actions were outside the reported winning set. 523 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 847 unique policies with solve-time statistics `{'median': 142.07310002529994, 'p95': 378.95769998431206, 'max': 495.8521999651566}` and first-observed ages `{'median': 2.0, 'p95': 7.0, 'max': 1789.0}`. Policy status counts were `{'pending_future_epoch': 66, 'queryable': 6949, 'expired': 13}`; 79 robust-mode decisions had no query.
- Of 2924 unambiguous output transitions, 2639 (0.903) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 0 hit windows with a positive warning lead; those leads were `[]` frames.
- Across all phases, bottom-eight-pixel occupancy was - during the 60 frames preceding a hit versus 0.073 outside those windows.
- Mean selected control-reserve deficit was - during the 60 frames preceding a hit versus 3.689 outside those windows.
- Soft recovery was selected on - of alive decisions in the 60-frame pre-hit windows versus 0.040 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 11.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
