# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260801_134853

## Scope And Integrity

- Valid practice scope: `2..26787` (8708 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 1, at `[7935]`.
- Hard no-Bomb verification: **PASS** across 8708 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F7935-T1`. It occurred during a nonspell phase at player (376.000, 421.494), with 567 bullets and 0 lasers. The projectile model reported pipeline clearance -3.908.

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
| canonical | 7935 | nonspell | (376.000, 421.494) | `left_fast` | 567/0 | -3.908/-3.908 | 2f/5f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 1 | 4751 | 0 | 0 | 0 | 0 | 0 | - | 0.172 |
| 35 | 0 | 892 | 854 | 660 | 0 | 0 | 120 | 43.245 | 0.241 |
| 38 | 0 | 776 | 769 | 365 | 0 | 0 | 121 | 94.183 | 0.136 |
| 42 | 0 | 756 | 749 | 608 | 0 | 0 | 122 | 40.293 | 0.250 |
| 46 | 0 | 884 | 877 | 709 | 0 | 0 | 144 | 52.215 | 0.309 |
| 50 | 0 | 649 | 642 | 467 | 0 | 0 | 117 | 84.679 | 0.334 |

## Interpretation

- Retained witnesses classify 1 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 16.995 ms median and 27.507 ms p95.
- The full enemy sensor produced 4364 snapshots; capture read time was `{'median': 5.428349977592006, 'p95': 15.585999994073063, 'max': 79.69919999595731}`, snapshot age was `{'median': 5.0, 'p95': 7.0, 'max': 13.0}` frames, and 3 phase-counter discontinuities were excluded; 8295 decisions retained at least one robust-union body (maximum 29); 7674 decisions contained latent contact-disabled geometry (maximum 28), and 2832 contained bounded inactive-slot memory (maximum 17). 7 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.0, 'p95': 1.0, 'max': 1.0}` / `{'median': 1.0, 'p95': 1.0, 'max': 1.0}` / `{'median': 2.0, 'p95': 2.0, 'max': 2.0}`.
- The issue-time enemy guard retained 8708 observations, detected 1065 during-plan geometry changes, recertified 1065 decisions, and overrode 2 actions. Read/recertificate timing was `{'median': 1.6165999986696988, 'p95': 3.116400010185316, 'max': 12.427099980413914}` / `{'median': 2.126400009728968, 'p95': 4.264499992132187, 'max': 13.937199983047321}` ms; 7677 issue captures contained latent bodies (maximum 29), and 2833 contained dormant bodies (maximum 17). Fresh/global transactions preserved 1063/1065 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 6502 observations (6433 contact enabled, 69 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4710, '0x005A1DA0': 1792}`.
- The terminal-threat heuristic covered 8708 decisions with horizon counts `{'0': 383, '10': 8325}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 420, '3': 7635, '4': 198, '5': 411, '6': 44}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 428, '2': 235, '3': 7971, '4': 74}`.
- Adaptive delay supports were `{'1,2': 288, '1,2,3': 77, '1,2,3,4': 200, '1,2,3,4,5': 12, '1,2,3,4,5,6': 20, '2,3': 864, '2,3,4': 3522, '2,3,4,5': 2137, '2,3,4,5,6': 1587, '3,4': 1}`; 4 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 36/310.
- Robust viability supplied 3891 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 2809 empty queried action sets. Recovery guidance was available/selected on 874/0 empty-kernel queries; distant-kernel guidance was available/selected on 1772/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 643, '1': 527, '2': 374, '3': 470, '4': 480, '5': 405, '6': 516, '7': 476}`.
- Global-horizon/local-prefix cross-tab covered 3225 decisions: 0 had a winning global state but unsafe selected prefix, 2374 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 181 selected actions were outside the reported winning set. 592 newer issue-time hazard versions and 3 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 624 unique policies with solve-time statistics `{'median': 58.04669999633916, 'p95': 136.6334000194911, 'max': 179.31389997829683}` and first-observed ages `{'median': 3.0, 'p95': 5.0, 'max': 8.0}`. Policy status counts were `{'pending_future_epoch': 47, 'queryable': 3894, 'expired': 2}`; 52 robust-mode decisions had no query.
- Of 5289 unambiguous output transitions, 5036 (0.952) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 1 hit windows with a positive warning lead; those leads were `[5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.182 during the 60 frames preceding a hit versus 0.211 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 128.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact-Authority Audit

- **Observed:** the old retained Stage-3 run had five hits, including three
  ordinary hits, while this run had one ordinary hit and retained Power 128.
  The RNG roots differ, so this is encouraging workload evidence rather than
  causal A/B proof.
- **Observed:** 4,725 ordinary roots passed the player-state gate, but none had
  a completed future policy. Continuation-lease create, renew, select, and
  effective counts were all zero. Early-kill observed 3,840 hostile targets
  but applied zero preferences because no nonempty global viable set existed.
- **Observed:** 1,214 future-source projections contained 701
  `timeline 2 has fractional time` failures, 465 native clock-bracket
  crossings, 40 unsupported active periodic emitters, seven incomplete health
  transitions, and one excessive auxiliary-call depth. In f7695..7935 before
  the only hit, all 49 source attempts failed on the timeline fraction.
- **Observed:** the first nonpositive local pipeline certificate appeared at
  f7933, only two frames before contact; the robust warning lead was five
  frames. The controller oscillated against the right boundary at x=376, but
  no global action authority existed to classify an earlier transfer.
- **Inferred:** the one-hit outcome primarily measures the current fallback
  stack and this RNG root. The publication-to-motion correction may improve
  local certificate fidelity, but this trial does not isolate its hit effect.
- **Next falsifier:** native unit-scale timer advance preserves a finite
  fraction while timeline dispatch reads only integer elapsed. Source
  semantics v12 removes that false UNKNOWN without accepting nonunit or
  nonfinite clocks. Repeat Stage 3 and require actual complete publication and
  lease telemetry before attributing any outcome to recursive authority.
