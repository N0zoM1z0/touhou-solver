# TH08 Stage 4A / Reimu No-Bomb Practice Review: lunatic_route2_stage4a_unattended_20260724_231637

## Scope And Integrity

- Session status: **discarded** (`external_stop`). This is the intentionally
  truncated, subsequently rejected Boss-x alignment experiment, not an
  accepted stage baseline.
- Valid practice scope: `2..17014` (3585 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 7, at `[2704, 4248, 9541, 10747, 11812, 12684, 16069]`.
- Hard no-Bomb verification: **PASS** across 3585 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S3-F2704-T1`. It occurred during a nonspell phase at player (17.263, 409.198), with 269 bullets and 0 lasers. The projectile model reported pipeline clearance 0.326.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |
| `observed_bullet_overlap` | 2 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 5
- `playfield_boundary`: 4
- `corridor_deadline_miss`: 2

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2704 | nonspell | (17.263, 409.198) | `up_left_fast` | 269/0 | 0.326/-2.437 | 3f/3f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4248 | nonspell | (376.000, 419.023) | `up_right` | 952/0 | -2.914/-2.914 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 9541 | nonspell | (55.046, 432.000) | `up_left_fast` | 111/0 | -3.372/-8.721 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10747 | 57 夢境「二重大結界」 | (8.000, 432.000) | `up_fast` | 440/0 | 0.028/0.028 | 0f/3f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 11812 | 57 夢境「二重大結界」 | (362.989, 432.000) | `left_fast` | 605/0 | -2.605/-2.605 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12684 | 57 夢境「二重大結界」 | (264.414, 292.268) | `down_right_fast` | 578/0 | -1.800/-1.800 | 4f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 16069 | nonspell | (120.599, 396.229) | `left` | 483/0 | -3.471/-3.471 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 4 | 2628 | 2555 | 971 | 0 | 1561 | 425 | 123.459 | 0.136 |
| 57 夢境「二重大結界」 | 3 | 906 | 896 | 219 | 0 | 660 | 165 | 195.642 | 0.243 |
| 61 | 0 | 51 | 40 | 0 | 0 | 40 | 5 | 437.576 | 0.000 |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 19.135 ms median and 35.441 ms p95.
- The full enemy sensor produced 2229 snapshots; capture read time was `{'median': 22.694700019201264, 'p95': 44.34940000646748, 'max': 64.52620000345632}`, snapshot age was `{'median': 5.0, 'p95': 9.0, 'max': 12.0}` frames, and 3 phase-counter discontinuities were excluded; 3280 decisions retained at least one robust-union body (maximum 41); 1232 decisions contained latent contact-disabled geometry (maximum 41), and 1616 contained bounded inactive-slot memory (maximum 36). 74 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 3.0595550537109375, 'p95': 4.1827748616536455, 'max': 5.500004768371582}` / `{'median': 3.0911879539489746, 'p95': 3.8987667560577393, 'max': 5.500004768371582}` / `{'median': 0.34224192301432294, 'p95': 0.9543431599934895, 'max': 1.2934308052062988}`.
- The issue-time enemy guard retained 3585 observations, detected 871 during-plan geometry changes, recertified 871 decisions, and overrode 404 actions. Read/recertificate timing was `{'median': 1.8877999973483384, 'p95': 4.135299997869879, 'max': 14.108600007602945}` / `{'median': 7.012799993390217, 'p95': 13.733500003581867, 'max': 21.993500005919486}` ms; 1232 issue captures contained latent bodies (maximum 41), and 1618 contained dormant bodies (maximum 36).
- The synchronous spell-owner guard retained 2007 observations (2007 contact enabled, 0 anticipatory, 0 errors). 0 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x005826C0': 2007}`.
- The terminal-threat heuristic covered 3585 decisions with horizon counts `{'0': 49, '10': 3213, '32': 323}`; it reported 6 collision and 38 sub-safety-clearance warnings, and relaxed 40 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 54, '3': 336, '4': 2937, '5': 258}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 157, '3': 609, '4': 2819}`.
- Adaptive delay supports were `{'1,2,3': 7, '1,2,3,4': 1, '2,3': 138, '2,3,4': 27, '2,3,4,5': 122, '2,3,4,5,6': 380, '3,4': 38, '3,4,5': 256, '3,4,5,6': 2614, '4,5,6': 2}`; 710 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 53/256.
- Robust viability supplied 3491 available policy queries (0 had new delay support outside the cached policy), constrained 2261 decisions, and exposed 1190 empty queried action sets. Recovery guidance was available/selected on 428/286 empty-kernel queries; distant-kernel guidance was available/selected on 666/619. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 9.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 48.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 97.32420048477151, 'p95': 317.5909318604673, 'max': 475.1757569573599}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 525, '1': 509, '2': 408, '3': 391, '4': 434, '5': 407, '6': 402, '7': 415}`.
- Global-horizon/local-prefix cross-tab covered 2019 decisions: 2 had a winning global state but unsafe selected prefix, 659 had a losing global state but safe short prefix, 1 selected globally certified actions contradicted the fresh local prefix checker, and 21 selected actions were outside the reported winning set. 714 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 595 unique policies with solve-time statistics `{'median': 162.2575999936089, 'p95': 436.43359999987297, 'max': 559.404400002677}` and first-observed ages `{'median': 3.0, 'p95': 11.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 33, 'queryable': 3488, 'expired': 15}`; 45 robust-mode decisions had no query.
- Of 2119 unambiguous output transitions, 1727 (0.815) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 7}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[3, 7, 6, 3, 8, 7, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.336 during the 60 frames preceding a hit versus 0.151 outside those windows.
- Mean selected control-reserve deficit was 4.634 during the 60 frames preceding a hit versus 1.053 outside those windows.
- Soft recovery was selected on 0.069 of alive decisions in the 60-frame pre-hit windows versus 0.082 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 50.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.
