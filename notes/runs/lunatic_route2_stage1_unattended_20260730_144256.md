# TH08 Stage 1 No-Bomb Practice Review: lunatic_route2_stage1_unattended_20260730_144256

## Scope And Integrity

- Valid practice scope: `1..20479` (6683 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[14159]`.
- Hard no-Bomb verification: **PASS** across 6683 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S0-F14159-T1`. It occurred during spell 5 `灯符「ファイヤフライフェノメノン」` at player (376.000, 318.241), with 744 bullets and 0 lasers. The projectile model reported pipeline clearance -3.301.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 1 |

Contributing factors:

- `fast_mode`: 1
- `playfield_boundary`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 14159 | 5 灯符「ファイヤフライフェノメノン」 | (376.000, 318.241) | `left_fast` | 744/0 | -3.301/-3.301 | 0f/9f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 0 | 4322 | 0 | 0 | 0 | 0 | 0 | - | 0.122 |
| 1 | 0 | 652 | 0 | 0 | 0 | 0 | 0 | - | 0.302 |
| 5 灯符「ファイヤフライフェノメノン」 | 1 | 811 | 0 | 0 | 0 | 0 | 0 | - | 0.137 |
| 9 | 0 | 898 | 0 | 0 | 0 | 0 | 0 | - | 0.174 |

## Interpretation

- Retained witnesses classify 0 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 16.127 ms median and 23.393 ms p95.
- The full enemy sensor produced 3278 snapshots; capture read time was `{'median': 4.532050050329417, 'p95': 8.826600038446486, 'max': 40.2181000681594}`, snapshot age was `{'median': 4.0, 'p95': 7.0, 'max': 10.0}` frames, and 3 phase-counter discontinuities were excluded; 6290 decisions retained at least one robust-union body (maximum 27); 4302 decisions contained latent contact-disabled geometry (maximum 13), and 2451 contained bounded inactive-slot memory (maximum 16). 8 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.267009735107422, 'p95': 2.5390472412109375, 'max': 2.5390548706054688}` / `{'median': 2.284139633178711, 'p95': 2.5582351684570312, 'max': 2.5582427978515625}` / `{'median': 0.0296783447265625, 'p95': 0.033233642578125, 'max': 0.033237457275390625}`.
- The issue-time enemy guard retained 6683 observations, detected 790 during-plan geometry changes, recertified 790 decisions, and overrode 3 actions. Read/recertificate timing was `{'median': 1.7794999293982983, 'p95': 3.406899981200695, 'max': 7.24649999756366}` / `{'median': 2.1293500321917236, 'p95': 3.6693000001832843, 'max': 16.60750003065914}` ms; 4296 issue captures contained latent bodies (maximum 13), and 2456 contained dormant bodies (maximum 16). Fresh/global transactions preserved 787/790 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 4637 observations (4569 contact enabled, 68 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4637}`.
- The terminal-threat heuristic covered 6683 decisions with horizon counts `{'0': 393, '10': 6290}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 540, '3': 6118, '4': 25}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 477, '2': 443, '3': 5763}`.
- Adaptive delay supports were `{'1': 46, '1,2': 283, '1,2,3': 63, '1,2,3,4': 199, '1,2,3,4,5': 34, '1,2,3,4,5,6': 111, '2,3': 517, '2,3,4': 1508, '2,3,4,5': 2612, '2,3,4,5,6': 1310}`; 3 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 32/483.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 3326 unambiguous output transitions, 2750 (0.827) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.000 during the 60 frames preceding a hit versus 0.150 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
