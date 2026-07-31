# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260731_133852

## Scope And Integrity

- Valid practice scope: `2..42313` (10992 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 11, at `[4148, 4449, 9011, 11122, 13311, 20905, 21621, 29194, 29545, 35425, 36046]`.
- Hard no-Bomb verification: **PASS** across 10992 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F4148-T1`. It occurred during a nonspell phase at player (315.235, 432.000), with 997 bullets and 0 lasers. The projectile model reported pipeline clearance -2.097.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 5 |

Contributing factors:

- `playfield_boundary`: 11
- `fast_mode`: 10
- `corridor_deadline_miss`: 4
- `pool_density_over_1000`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 4148 | nonspell | (315.235, 432.000) | `left` | 997/0 | -2.097/-2.097 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4449 | nonspell | (130.279, 432.000) | `up_left_fast` | 939/0 | -3.863/-13.839 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 9011 | nonspell | (166.437, 432.000) | `up_left_fast` | 154/0 | -9.896/-9.896 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11122 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_right_fast` | 449/0 | -1.791/-1.791 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 13311 | 57 夢境「二重大結界」 | (8.000, 428.000) | `up_right_fast` | 611/0 | -1.780/-1.780 | 0f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20905 | nonspell | (16.132, 432.000) | `right_fast` | 766/0 | -3.350/-3.350 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21621 | nonspell | (8.000, 432.000) | `up_left_fast` | 793/0 | -2.061/-2.061 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29194 | 65 神技「八方龍殺陣」 | (197.859, 432.000) | `down_right_fast` | 1292/0 | -2.529/-2.729 | 3f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 29545 | 65 神技「八方龍殺陣」 | (151.296, 430.595) | `up_left_fast` | 1148/0 | -1.115/-2.167 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 35425 | 69 回霊「夢想封印　侘」 | (373.172, 424.260) | `up_left_fast` | 552/0 | -1.599/-1.599 | 0f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 36046 | 69 回霊「夢想封印　侘」 | (8.000, 388.016) | `right_fast` | 685/0 | -2.582/-2.702 | 15f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 6637 | 6505 | 3653 | 0 | 0 | 962 | 110.009 | 0.235 |
| 57 夢境「二重大結界」 | 2 | 1048 | 1040 | 294 | 0 | 0 | 174 | 178.449 | 0.403 |
| 61 | 0 | 700 | 693 | 294 | 0 | 0 | 112 | 137.260 | 0.202 |
| 65 神技「八方龍殺陣」 | 2 | 590 | 583 | 451 | 0 | 0 | 103 | 65.034 | 0.360 |
| 69 回霊「夢想封印　侘」 | 2 | 1103 | 1095 | 627 | 0 | 0 | 178 | 95.816 | 0.171 |
| 73 | 0 | 914 | 897 | 612 | 0 | 0 | 173 | 120.924 | 0.053 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.260 ms median and 28.768 ms p95.
- The full enemy sensor produced 5799 snapshots; capture read time was `{'median': 6.445099992561154, 'p95': 29.95379999629222, 'max': 51.45579999953043}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 11.0}` frames, and 5 phase-counter discontinuities were excluded; 10447 decisions retained at least one robust-union body (maximum 50); 6024 decisions contained latent contact-disabled geometry (maximum 50), and 4058 contained bounded inactive-slot memory (maximum 29). 270 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 2.4779624938964844, 'p95': 4.166656494140625, 'max': 4.5697021484375}` / `{'median': 2.4837889671325684, 'p95': 3.8987693786621094, 'max': 4.499996185302734}` / `{'median': 0.6467132568359375, 'p95': 1.3193912506103516, 'max': 7.940028190612793}`.
- The issue-time enemy guard retained 10992 observations, detected 4304 during-plan geometry changes, recertified 4304 decisions, and overrode 182 actions. Read/recertificate timing was `{'median': 1.7073000053642318, 'p95': 3.2767000084277242, 'max': 16.940400004386902}` / `{'median': 2.4311000015586615, 'p95': 4.074199998285621, 'max': 14.80930000252556}` ms; 6020 issue captures contained latent bodies (maximum 50), and 4070 contained dormant bodies (maximum 29). Fresh/global transactions preserved 4122/4304 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8145 observations (8107 contact enabled, 38 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 8145}`.
- The terminal-threat heuristic covered 10992 decisions with horizon counts `{'0': 526, '10': 10466}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 460, '3': 7581, '4': 2830, '5': 121}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 132, '2': 280, '3': 9732, '4': 845, '5': 3}`.
- Adaptive delay supports were `{'1,2': 249, '1,2,3': 71, '1,2,3,4': 116, '1,2,3,4,5': 74, '2,3': 325, '2,3,4': 2176, '2,3,4,5': 5513, '2,3,4,5,6': 1832, '3,4': 13, '3,4,5': 235, '3,4,5,6': 385, '4,5,6': 2, '5,6': 1}`; 212 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 16/138.
- Robust viability supplied 10813 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 5931 empty queried action sets. Recovery guidance was available/selected on 1635/0 empty-kernel queries; distant-kernel guidance was available/selected on 3621/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 0.0, 'max': 0.0}`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1702, '1': 1496, '2': 1099, '3': 1248, '4': 1337, '5': 1250, '6': 1331, '7': 1350}`.
- Global-horizon/local-prefix cross-tab covered 5607 decisions: 0 had a winning global state but unsafe selected prefix, 2514 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 459 selected actions were outside the reported winning set. 3692 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1702 unique policies with solve-time statistics `{'median': 118.68220000178553, 'p95': 336.4320999971824, 'max': 467.6560000079917}` and first-observed ages `{'median': 3.0, 'p95': 6.0, 'max': 1808.0}`. Policy status counts were `{'pending_future_epoch': 65, 'queryable': 10815, 'expired': 20}`; 87 robust-mode decisions had no query.
- Of 6343 unambiguous output transitions, 6087 (0.960) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 10, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 10 hit windows with a positive warning lead; those leads were `[6, 0, 9, 6, 4, 6, 6, 3, 6, 9, 18]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.643 during the 60 frames preceding a hit versus 0.220 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 33.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Nonspell Early-Kill Causal Review

- **Observed physical:** this run exercised immutable code checkpoint
  `aae641f9c42d77ff78915d67f6c8b620c366fc75`. Before the canonical first
  hit, the rule saw 722 targets, proposed 176 preferences, and physically
  applied 124 after both a winning shadow-global query and fresh issue
  certification. Of those applications, 123 changed horizontal alignment and
  one selected the same-direction unfocused action. There were no spell
  targets/applications and no Bomb.
- **Observed:** the first attempt's last winning query was frame 3679, 469
  frames before the hit at 4148. The rule made no application without a
  winning queried action set.
- **Observed:** the user's middle-wave diagnosis is supported by the trace.
  Enemy `0x006443D0` was already visible in the body trace at decision frame
  3864 near `(319.4, -0.7)` with maximum HP 200, but the old HP gate did not
  select it until frame 3900 at 15 HP. That was 221 frames after the last
  winning query. From 3679 through 4148 there were zero winning queries, 82
  target decisions, 690.5 mean active bullets, and 0.367 bottom occupancy.
- **Observed shipped content:** Stage-4A timeline 0 contains fixed spawns at
  times/positions `3560/64`, `3660/320`, `3810/64`, and `3860/320`; runtime
  bodies appeared two to four manager frames later.
- **Inferred:** the hard losing-state veto is correct. The missing mechanic is
  earlier causal observation: recognize full-health ordinary non-boss
  enemies and use the live native timeline clock plus byte-verified shipped
  ECL to expose a fixed birth location before body observation. The actual
  body remains preferable once observed, and every optional alignment still
  requires winning-global membership plus fresh issue certification.
- **Not yet physical:** the full-health/forecast correction was implemented
  only after this run. Retained-trace replay found 18 pre-exhaustion forecast
  proposals in frames 3400..4148, 15 also inside the old retained fresh-safe
  set. This is eligibility evidence, not physical validation.

Compact experiment-specific evidence is
`artifacts/runtime_reports/th08_nonspell_preexhaustion_early_kill_stage4a_20260731_133852.json`.
