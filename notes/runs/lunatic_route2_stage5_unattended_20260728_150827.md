# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260728_150827

## Scope And Integrity

- Valid practice scope: `2..42172` (11801 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 12, at `[1394, 10828, 12454, 12890, 25036, 30586, 30965, 37844, 38532, 40009, 40617, 41904]`.
- Hard no-Bomb verification: **PASS** across 11801 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F1394-T1`. It occurred during a nonspell phase at player (376.000, 383.758), with 100 bullets and 0 lasers. The projectile model reported pipeline clearance -1.343.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 5 |

Contributing factors:

- `fast_mode`: 9
- `playfield_boundary`: 7
- `pool_density_over_1000`: 6
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1394 | nonspell | (376.000, 383.758) | `down_fast` | 100/0 | -1.343/-1.490 | 2f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10828 | nonspell | (114.022, 416.000) | `up_fast` | 909/0 | 0.109/-20.142 | 27f/34f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12454 | nonspell | (376.000, 425.823) | `down_left` | 261/0 | -2.897/-2.897 | 3f/7f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12890 | nonspell | (354.080, 152.673) | `down_fast` | 245/0 | -2.168/-2.508 | 5f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25036 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 1130/0 | -2.404/-2.404 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30586 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (28.119, 432.000) | `up_fast` | 1021/0 | -5.616/-5.616 | 7f/11f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30965 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (189.193, 364.765) | `up_fast` | 1012/0 | -6.627/-6.662 | 25f/42f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 37844 | 111 懶惰「生神停止(マインドストッパー)」 | (102.983, 201.302) | `down_fast` | 327/0 | -2.572/-2.572 | 3f/18f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 38532 | 111 懶惰「生神停止(マインドストッパー)」 | (203.288, 175.435) | `up_right` | 352/0 | -2.174/-2.174 | 0f/3f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40009 | 115 散符「真実の月(インビジブルフルムーン)」 | (355.955, 429.172) | `up_right_fast` | 1104/0 | -5.168/-14.600 | 5f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 40617 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `up_fast` | 1292/0 | -1.835/-1.835 | 4f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41904 | 115 散符「真実の月(インビジブルフルムーン)」 | (8.000, 429.700) | `up_right` | 1297/0 | -0.786/-0.865 | 3f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 7460 | 7330 | 5214 | 0 | 2089 | 954 | 106.550 | 0.175 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 1 | 880 | 867 | 618 | 0 | 249 | 173 | 103.475 | 0.309 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 1078 | 1069 | 825 | 0 | 237 | 215 | 83.433 | 0.333 |
| 111 懶惰「生神停止(マインドストッパー)」 | 2 | 1185 | 1178 | 543 | 0 | 620 | 179 | 92.019 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1198 | 1187 | 748 | 0 | 421 | 184 | 61.470 | 0.416 |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 11.206 ms median and 23.186 ms p95.
- The full enemy sensor produced 6268 snapshots; capture read time was `{'median': 5.711450008675456, 'p95': 25.83200007211417, 'max': 50.02229998353869}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 12.0}` frames, and 6 phase-counter discontinuities were excluded; 11166 decisions retained at least one robust-union body (maximum 42); 4858 decisions contained latent contact-disabled geometry (maximum 42), and 6332 contained bounded inactive-slot memory (maximum 40). 205 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 1.995574951171875, 'max': 6.341462135314941}` / `{'median': 0.0, 'p95': 1.9756078720092773, 'max': 5.4666643142700195}` / `{'median': 0.0, 'p95': 0.5333292782306671, 'max': 9.300048828125}`.
- The issue-time enemy guard retained 11801 observations, detected 2619 during-plan geometry changes, recertified 2619 decisions, and overrode 57 actions. Read/recertificate timing was `{'median': 1.7465000273659825, 'p95': 3.430600045248866, 'max': 14.809199958108366}` / `{'median': 3.436699975281954, 'p95': 6.631399970501661, 'max': 18.703099922277033}` ms; 4835 issue captures contained latent bodies (maximum 42), and 6331 contained dormant bodies (maximum 40). Fresh/global transactions preserved 2562/2619 planned actions, relaxed 10 fresh/global empty intersections, inherited 7 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8295 observations (8264 contact enabled, 31 anticipatory, 0 errors). 8295 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8295}`.
- The terminal-threat heuristic covered 11801 decisions with horizon counts `{'0': 71, '10': 11488, '32': 242}`; it reported 11 collision and 88 sub-safety-clearance warnings, and relaxed 67 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 585, '3': 9208, '4': 1353, '5': 655}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 2949, '3': 7244, '4': 1382, '5': 215}`.
- Adaptive delay supports were `{'1,2,3': 281, '1,2,3,4': 8, '2,3': 698, '2,3,4': 3845, '2,3,4,5': 3076, '2,3,4,5,6': 2646, '3,4,5': 81, '3,4,5,6': 1164, '4,5,6': 2}`; 169 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 63/305.
- Robust viability supplied 11631 available policy queries (0 had new delay support outside the cached policy), constrained 3616 decisions, and exposed 7948 empty queried action sets. Recovery guidance was available/selected on 936/429 empty-kernel queries; distant-kernel guidance was available/selected on 6304/5977. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 143.10835055998655, 'p95': 357.77087639996637, 'max': 544.9403637096449}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1759, '1': 1630, '2': 1197, '3': 1343, '4': 1372, '5': 1422, '6': 1431, '7': 1477}`.
- Global-horizon/local-prefix cross-tab covered 7685 decisions: 3 had a winning global state but unsafe selected prefix, 5088 had a losing global state but safe short prefix, 2 selected globally certified actions contradicted the fresh local prefix checker, and 30 selected actions were outside the reported winning set. 2256 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1705 unique policies with solve-time statistics `{'median': 93.23720005340874, 'p95': 322.96430005226284, 'max': 431.275499984622}` and first-observed ages `{'median': 2.0, 'p95': 6.0, 'max': 1794.0}`. Policy status counts were `{'pending_future_epoch': 63, 'queryable': 11631, 'expired': 21}`; 84 robust-mode decisions had no query.
- Of 6220 unambiguous output transitions, 5583 (0.898) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[7, 34, 7, 12, 5, 11, 42, 18, 3, 12, 9, 5]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.355 during the 60 frames preceding a hit versus 0.199 outside those windows.
- Mean selected control-reserve deficit was 7.899 during the 60 frames preceding a hit versus 4.574 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.039 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## G5 Derived-Pattern Source Experiment

- This pre-split checkpoint enabled the native ready-parent source shadow
  whenever native bullet-birth tracing was enabled. The compact session
  provenance was corrected to state `trace_derived_pattern_sources=true`;
  raw schema-v10 rows are immutable.
- All 11,801 source observations validated and all returned zero candidates.
  The target nonspell topology was reproduced: frame 13861 has 30 activation
  edges split into 15 age-two and 15 age-one children, but its source
  candidate count is zero. Frame 13879 repeats the same negative result.
- The deterministic offline next-observation join therefore has zero source
  rows, zero edges, and empty-edge digest
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
  Hit outcome is not consumed by this join.
- Combined birth/source p50/p95/p99/p99.9/max is
  `0.1346/0.2633/0.4982/3.7388/9.0368 ms`, so the fixed
  `0.20/0.40/2.00 ms` observer gate fails. The run used native
  `gil-released`; its extreme scheduler tail is not a GIL-held B4 comparison.
- This rejects only a parent that is ready in a captured observation. A
  transform that becomes ready and executes between observations remains
  unresolved. Future ordinary birth traces do not enable this failed shadow
  unless the separate explicit source flag is provided.
