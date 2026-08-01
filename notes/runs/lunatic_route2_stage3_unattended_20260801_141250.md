# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_unattended_20260801_141250

## Scope And Integrity

- Valid practice scope: `1..27463` (8554 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 4, at `[3181, 7956, 8414, 25932]`.
- Hard no-Bomb verification: **PASS** across 8554 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F3181-T1`. It occurred during a nonspell phase at player (13.657, 424.000), with 205 bullets and 0 lasers. The projectile model reported pipeline clearance 3.153.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 2 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `playfield_boundary`: 3
- `fast_mode`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3181 | nonspell | (13.657, 424.000) | `up_left` | 205/0 | 3.153/-1.388 | 2f/4f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 7956 | nonspell | (355.899, 432.000) | `down_right_fast` | 593/0 | -2.432/-2.432 | 0f/8f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 8414 | nonspell | (361.919, 432.000) | `left_fast` | 177/0 | 0.646/-1.671 | 2f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 25932 | 50 虚史「幻想郷伝説」 | (168.620, 432.000) | `down_right` | 265/190 | -4.532/-4.532 | 0f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 4630 | 275 | 19 | 0 | 270 | 16 | 336.237 | 0.206 |
| 35 | 0 | 880 | 854 | 700 | 0 | 0 | 103 | 42.656 | 0.286 |
| 38 | 0 | 766 | 743 | 457 | 0 | 0 | 90 | 96.280 | 0.139 |
| 42 | 0 | 748 | 741 | 602 | 0 | 0 | 121 | 40.924 | 0.249 |
| 46 | 0 | 869 | 862 | 728 | 0 | 0 | 142 | 53.321 | 0.390 |
| 50 虚史「幻想郷伝説」 | 1 | 661 | 653 | 463 | 0 | 0 | 118 | 83.669 | 0.317 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.175 ms median and 30.307 ms p95.
- The full enemy sensor produced 4415 snapshots; capture read time was `{'median': 5.487399990670383, 'p95': 17.607700021471828, 'max': 92.67440001713112}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 42.0}` frames, and 3 phase-counter discontinuities were excluded; 8374 decisions retained at least one robust-union body (maximum 27); 7873 decisions contained latent contact-disabled geometry (maximum 27), and 2501 contained bounded inactive-slot memory (maximum 21). 45 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 1.662994384765625, 'p95': 2.259998321533203, 'max': 3.1722869873046875}` / `{'median': 1.6629819869995117, 'p95': 2.259998321533203, 'max': 3.1722869873046875}` / `{'median': 2.1457672119140625e-06, 'p95': 2.0, 'max': 2.0}`.
- The issue-time enemy guard retained 8554 observations, detected 1140 during-plan geometry changes, recertified 1140 decisions, and overrode 9 actions. Read/recertificate timing was `{'median': 1.560000004246831, 'p95': 2.97359999967739, 'max': 21.779900009278208}` / `{'median': 2.254399994853884, 'p95': 5.11750002624467, 'max': 13.115400011884049}` ms; 7877 issue captures contained latent bodies (maximum 27), and 2499 contained dormant bodies (maximum 22). Fresh/global transactions preserved 1133/1142 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 6706 observations (6636 contact enabled, 70 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 4983, '0x005B1910': 1723}`.
- The terminal-threat heuristic covered 8554 decisions with horizon counts `{'0': 22, '10': 8532}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 24, '3': 7315, '4': 606, '5': 609}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 26, '2': 124, '3': 8302, '4': 102}`.
- Adaptive delay supports were `{'1,2': 25, '1,2,3,4,5': 41, '1,2,3,4,5,6': 61, '2,3': 539, '2,3,4': 3358, '2,3,4,5': 2407, '2,3,4,5,6': 2122, '3,4,5': 1}`; 20 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 31/255.
- Robust viability supplied 4128 available policy queries (0 had new delay support outside the cached policy), constrained 270 decisions, and exposed 2969 empty queried action sets. Recovery guidance was available/selected on 735/0 empty-kernel queries; distant-kernel guidance was available/selected on 2034/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 654, '1': 585, '2': 438, '3': 449, '4': 493, '5': 511, '6': 493, '7': 505}`.
- Global-horizon/local-prefix cross-tab covered 3267 decisions: 0 had a winning global state but unsafe selected prefix, 2414 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 97 selected actions were outside the reported winning set. 636 newer issue-time hazard versions and 2 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 590 unique policies with solve-time statistics `{'median': 56.02460000955034, 'p95': 150.63399999053217, 'max': 1136.8868999998085}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 53.0}`. Policy status counts were `{'pending_future_epoch': 69, 'queryable': 4127, 'expired': 2335}`; 2403 robust-mode decisions had no query.
- Of 5277 unambiguous output transitions, 5030 (0.953) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 3, 'global_viability_kernel_exhausted_before_hit': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 4 hit windows with a positive warning lead; those leads were `[4, 8, 7, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.275 during the 60 frames preceding a hit versus 0.240 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 93.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Exact-Authority Audit

- **Observed:** source semantics v12 completed 692/1,261 future-source roots,
  versus 0/1,214 under v11 in the preceding different-RNG Stage-3 run. It
  submitted 596 roots and completed 595 future policies. Remaining failures
  were 516 native clock-bracket crossings, 41 unsupported periodic emitters,
  11 incomplete health/damage roots, and one auxiliary-depth root.
- **Observed:** ordinary coverage was complete on 281 decisions; 265 exact
  predecessors were applicable and effective. The exact set constrained 270
  local decisions. Five delayed scans found a safe contingent row and four
  were effective at issue.
- **Observed:** those four effective delayed actions created four leases, but
  none was effective as a later no-write continuation. Every lease was revoked
  by `fresh_body_envelope_not_contained`; renewal count remained zero. Early
  kill applied twice inside an exact set.
- **Observed:** before canonical hit f3181, the last effective exact action was
  f1406. All 103 decisions in f2941..3181 reported
  `future_policy_unavailable`, although 14 source captures completed and 12
  crossed their native clock bracket in that window. The hit exhausted the
  local robust action set with four frames of warning.
- **Inferred:** eliminating the false fractional-timer UNKNOWN repaired source
  coverage and physically activated global authority. It did not establish a
  persistent lease into the first pressure window. The four-hit aggregate
  versus the preceding one-hit root is not causal evidence either for or
  against v12.
