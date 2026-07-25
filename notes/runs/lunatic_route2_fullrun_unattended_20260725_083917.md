# TH08 Lunatic Full-Run Review: lunatic_route2_fullrun_unattended_20260725_083917

## Evidence Boundary

- **Observed:** This is one continuous original-game Lunatic
  Sakuya/Remilia Route-2 trace from Stage 1 through the Final-B terminal
  unload. It has no manual re-arm, foreground interruption, runtime error,
  JSON decode error, Bomb input, or deathbomb request.
- **Observed comparison:** Total native hit edges changed `90 -> 77` against
  the retained 2026-07-23 complete hard no-Bomb baseline. Stage deltas are
  `+2, 0, -4, -9, +7, -9`; Stage 1 and Stage 5 are adverse samples.
- **Observed performance:** Global solve median/p95 changed
  `2455.95/4038.64 -> 99.99/386.09 ms`; first-observed solution age changed
  `152/259 -> 3/9` frames. Current clearance median/p95 is
  `12.11/33.53 ms`, while viability is `74.63/372.11 ms`.
- **Inferred:** The packed clearance work removed the former dominant global
  bottleneck and made the background policy serviceable in this physical
  run. Viability induction, not clearance construction, now dominates the
  global tail.
- **Limitation:** This is not a causal strategy A/B or cross-RNG acceptance.
  RNG, Power/resource history, phase duration, and attribution schema differ.
  Local read/action latency also increased, and the Stage-5 regression must
  be investigated before claiming a generally stronger controller.
- **Postprocessing correction:** The physical run completed normally. The
  first finalizer temporarily marked the session discarded because it
  expected `route_complete` on the inactive edge; the native guard writes
  `terminal_unload` there and promotes only the following summary. CE-0105
  records the corrected contract and the session retains the recovery reason.

## Result

- Route: Sakuya/Remilia, Lunatic, Final B / Kaguya.
- Combat completion: yes; gameplay scene unloaded at frame 226864.
- Native phase-2 hit edges, including Last-Spell-saveable edges: 77.
- Deathbomb requests at those edges: 0.
- Hard no-Bomb input verification: passed across 52479 decisions.
- Post-hit Bomb-stock decreases: 15.00; this is respawn-stock reset telemetry, not evidence of Bomb input.
- Agent decisions: 52479.
- Raw trace size: 1291391386 bytes across 1 segments.
- JSON decode errors: 0.
- Exact spell-level hit attribution: available from live `g_spell_card_state`.

The run is valid for stage-, death-, resource-, projectile-, latency-, and route-level analysis. Spell names below are the statically reachable Lunatic route inventory; unavailable runtime hit counts remain explicitly unresolved instead of guessed. The no-life patch allows post-hit resource resets to repeat, so resource-stock changes must not be interpreted as Bomb commands.

## Trace Integrity

| Segment | Frames | Decisions | Wall Z | Termination | Runtime error | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 1..226864 | 52479 | 407 | route_complete | - | `b87645ae3aa0d11039543ca0d492aecb5956701996f460d8fd7df66fad79a756` |

The route is one continuous agent-controlled trace with no foreground interruption or manual re-arm gap.

## Stage Summary

| Stage | Frames | Decisions | Native hits | Deathbombs | Post-hit Bomb-stock decrease | Power start/end/min | Max bullets | Max lasers |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Stage 1 | 1..20949 | 5082 | 3 | 0 | 0.00 | 0.00/10.00/0.00 | 1175 | 0 |
| Stage 2 | 20949..44679 | 6368 | 5 | 0 | 0.00 | 15.00/7.00/0.00 | 1197 | 0 |
| Stage 3 | 44679..72487 | 7227 | 6 | 0 | 3.00 | 13.00/38.00/0.00 | 990 | 200 |
| Stage 4A / Reimu | 72487..118200 | 10186 | 19 | 0 | 2.00 | 43.00/6.00/0.00 | 1536 | 0 |
| Stage 5 | 118200..162339 | 8984 | 20 | 0 | 5.00 | 11.00/10.00/0.00 | 1510 | 0 |
| Final B / Kaguya | 162342..226864 | 14632 | 24 | 0 | 5.00 | 15.00/6.00/0.00 | 1237 | 240 |

## Failure Taxonomy

| Primary class | Deaths | Interpretation |
| --- | ---: | --- |
| `modeled_committed_prefix_collision` | 49 | The measured three-frame input pipeline was already unsafe. |
| `observed_bullet_overlap` | 21 | A bullet overlaps the native player AABB in the hit observation. |
| `observed_enemy_body_overlap` | 3 | A captured lethal enemy-body AABB overlaps the player at action time. |
| `observed_laser_overlap` | 3 | The player overlaps an active laser's exact finite segment; TH08 checks this before the broad bullet pass. |
| `sensor_gap_or_unmodeled_hazard` | 1 | No observed overlap and positive pipeline clearance; same-frame ECL emission, transform error, or another unmodeled hazard is the leading explanation. |

Contributing factors:

- `playfield_boundary`: 62 deaths
- `fast_mode`: 58 deaths
- `corridor_deadline_miss`: 15 deaths
- `pool_density_over_1000`: 12 deaths
- `enemy_body_absent_from_action_snapshot`: 2 deaths

## High-Risk Clusters

| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at hit |
| --- | --- | ---: | ---: | ---: | ---: |
| cluster-40 | Stage 5 | 149497..150786 | 4 | 1.00 | 1008 |
| cluster-62 | Final B / Kaguya | 221782..222814 | 3 | 0.00 | 598 |
| cluster-05 | Stage 2 | 23537..23967 | 2 | 0.00 | 413 |
| cluster-10 | Stage 3 | 52782..53105 | 2 | 1.00 | 805 |
| cluster-13 | Stage 4A / Reimu | 73404..73746 | 2 | 31.00 | 222 |
| cluster-15 | Stage 4A / Reimu | 76542..76930 | 2 | 0.00 | 1458 |
| cluster-18 | Stage 4A / Reimu | 84275..84661 | 2 | 0.00 | 592 |
| cluster-31 | Stage 5 | 121720..122296 | 2 | 0.00 | 954 |
| cluster-34 | Stage 5 | 130433..130923 | 2 | 0.00 | 356 |
| cluster-35 | Stage 5 | 132280..132823 | 2 | 0.00 | 566 |
| cluster-51 | Final B / Kaguya | 184464..184845 | 2 | 14.00 | 112 |

## Stage Detail

### Stage 1

- Death frames: 1096, 6873, 18423
- Cause counts: `{"observed_bullet_overlap": 2, "modeled_committed_prefix_collision": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 279/356.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1096 | 3.00 | 1.00 | 0.00 | 265 | -1.30 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 6873 | 3.00 | 3.00 | 0.00 | 259 | -1.89 | -42.22 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 18423 | 3.00 | 4.00 | 0.00 | 282 | 0.84 | 5.49 | `observed_bullet_overlap` | fast_mode |

### Stage 2

- Death frames: 21991, 23537, 23967, 24646, 26161
- Cause counts: `{"modeled_committed_prefix_collision": 5}`
- Phase markers: observed 2, reachable static opcode `0x94` 3.
- Bottom/side occupancy decisions: 443/563.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 21991 | 3.00 | 16.00 | 0.00 | 136 | -3.90 | -11.17 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 23537 | 3.00 | 6.00 | 0.00 | 129 | -2.27 | -10.66 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 23967 | 3.00 | 0.00 | 0.00 | 413 | -3.69 | 2.53 | `modeled_committed_prefix_collision` | playfield_boundary |
| 24646 | 3.00 | 0.00 | 0.00 | 260 | -1.70 | -22.17 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 26161 | 3.00 | 2.00 | 0.00 | 243 | -17.34 | -0.00 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |

### Stage 3

- Death frames: 46963, 47648, 52782, 53105, 53706, 61238
- Cause counts: `{"observed_bullet_overlap": 3, "modeled_committed_prefix_collision": 3}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 628/528.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 46963 | 4.00 | 23.00 | 1.00 | 345 | -2.01 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 47648 | 3.00 | 10.00 | 0.00 | 462 | -1.08 | 2.69 | `observed_bullet_overlap` | playfield_boundary |
| 52782 | 3.00 | 7.00 | 0.00 | 805 | -2.43 | 8.51 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 53105 | 3.00 | 1.00 | 0.00 | 308 | -3.37 | 2.55 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 53706 | 3.00 | 1.00 | 0.00 | 463 | -1.76 | 9.14 | `modeled_committed_prefix_collision` | playfield_boundary |
| 61238 | 5.00 | 33.00 | 2.00 | 238 | -0.10 | 3.81 | `observed_bullet_overlap` | - |

### Stage 4A / Reimu

- Death frames: 73404, 73746, 75233, 76542, 76930, 81842, 82712, 84275, 84661, 85425, 89015, 89784, 94890, 95779, 103925, 104574, 108644, 110057, 112533
- Cause counts: `{"modeled_committed_prefix_collision": 14, "sensor_gap_or_unmodeled_hazard": 1, "observed_bullet_overlap": 2, "observed_enemy_body_overlap": 2}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1164/662.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 73404 | 3.00 | 43.00 | 0.00 | 129 | -1.54 | 6.83 | `modeled_committed_prefix_collision` | playfield_boundary |
| 73746 | 3.00 | 31.00 | 0.00 | 222 | -3.05 | -2.73 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 75233 | 3.00 | 17.00 | 0.00 | 517 | -2.78 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 76542 | 3.00 | 6.00 | 0.00 | 995 | -3.30 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 76930 | 3.00 | 0.00 | 0.00 | 1458 | -3.04 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 81842 | 3.00 | 3.00 | 0.00 | 583 | 0.34 | 0.65 | `sensor_gap_or_unmodeled_hazard` | playfield_boundary |
| 82712 | 4.00 | 8.00 | 1.00 | 181 | -1.17 | - | `modeled_committed_prefix_collision` | fast_mode |
| 84275 | 3.00 | 0.00 | 0.00 | 590 | -3.37 | -4.38 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 84661 | 3.00 | 0.00 | 0.00 | 592 | -3.34 | 2.58 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 85425 | 3.00 | 1.00 | 0.00 | 590 | -2.82 | -1.37 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 89015 | 3.00 | 1.00 | 0.00 | 213 | -2.32 | 7.43 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 89784 | 4.00 | 10.00 | 1.00 | 462 | -2.53 | 1.72 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 94890 | 3.00 | 1.00 | 0.00 | 797 | -1.39 | -5.91 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 95779 | 3.00 | 6.00 | 0.00 | 655 | -1.78 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 103925 | 3.00 | 2.00 | 0.00 | 1160 | -21.07 | - | `observed_enemy_body_overlap` | pool_density_over_1000,enemy_body_absent_from_action_snapshot |
| 104574 | 3.00 | 0.00 | 0.00 | 1148 | -29.59 | - | `observed_enemy_body_overlap` | pool_density_over_1000,fast_mode |
| 108644 | 3.00 | 0.00 | 0.00 | 64 | -4.53 | 14.30 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 110057 | 3.00 | 0.00 | 0.00 | 129 | -1.92 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 112533 | 3.00 | 0.00 | 0.00 | 681 | -6.86 | 8.22 | `observed_bullet_overlap` | playfield_boundary,fast_mode |

### Stage 5

- Death frames: 119515, 120385, 121720, 122296, 126407, 129062, 130433, 130923, 132280, 132823, 142060, 142895, 143504, 147800, 149497, 149914, 150333, 150786, 157383, 160387
- Cause counts: `{"modeled_committed_prefix_collision": 15, "observed_enemy_body_overlap": 1, "observed_bullet_overlap": 4}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1499/820.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 119515 | 3.00 | 11.00 | 0.00 | 87 | -2.96 | -9.09 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 120385 | 3.00 | 0.00 | 0.00 | 654 | -12.74 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 121720 | 3.00 | 3.00 | 0.00 | 954 | -4.60 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 122296 | 3.00 | 0.00 | 0.00 | 660 | -6.20 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 126407 | 4.00 | 11.00 | 1.00 | 553 | -1.56 | 4.16 | `modeled_committed_prefix_collision` | fast_mode |
| 129062 | 3.00 | 1.00 | 0.00 | 888 | -10.60 | - | `observed_enemy_body_overlap` | playfield_boundary,fast_mode,enemy_body_absent_from_action_snapshot |
| 130433 | 3.00 | 0.00 | 0.00 | 356 | -2.73 | -14.63 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 130923 | 3.00 | 0.00 | 0.00 | 295 | -1.73 | -4.49 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 132280 | 3.00 | 0.00 | 0.00 | 566 | -3.82 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 132823 | 3.00 | 0.00 | 0.00 | 460 | -9.39 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 142060 | 6.00 | 21.00 | 3.00 | 1428 | -4.45 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 142895 | 3.00 | 5.00 | 0.00 | 1360 | -2.15 | 5.14 | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 143504 | 3.00 | 2.00 | 0.00 | 857 | -2.48 | 14.18 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 147800 | 3.00 | 2.00 | 0.00 | 1018 | -1.54 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 149497 | 3.00 | 2.00 | 0.00 | 992 | -6.70 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 149914 | 3.00 | 8.00 | 0.00 | 1004 | -5.15 | 13.28 | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000 |
| 150333 | 4.00 | 1.00 | 1.00 | 1005 | -8.29 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 150786 | 3.00 | 2.00 | 0.00 | 1008 | -8.41 | - | `modeled_committed_prefix_collision` | pool_density_over_1000,fast_mode |
| 157383 | 3.00 | 0.00 | 0.00 | 330 | -2.52 | 3.86 | `modeled_committed_prefix_collision` | fast_mode |
| 160387 | 3.00 | 5.00 | 0.00 | 1166 | -0.90 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |

### Final B / Kaguya

- Death frames: 163053, 164428, 165105, 167637, 174326, 175342, 181619, 183136, 184464, 184845, 196821, 203057, 204530, 205277, 213385, 214057, 214776, 218925, 219583, 220715, 221782, 222275, 222814, 226661
- Cause counts: `{"observed_bullet_overlap": 10, "modeled_committed_prefix_collision": 11, "observed_laser_overlap": 3}`
- Phase markers: observed 10, reachable static opcode `0x94` 14.
- Bottom/side occupancy decisions: 1270/839.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 163053 | 3.00 | 15.00 | 0.00 | 609 | -3.12 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 164428 | 3.00 | 1.00 | 0.00 | 645 | -1.13 | 11.20 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 165105 | 3.00 | 0.00 | 0.00 | 498 | -1.86 | 9.17 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 167637 | 3.00 | 3.00 | 0.00 | 250 | -2.83 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 174326 | 4.00 | 78.00 | 1.00 | 847 | -2.34 | 1.75 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 175342 | 3.00 | 64.00 | 0.00 | 466 | -3.42 | 1.48 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 181619 | 3.00 | 51.00 | 0.00 | 1154 | -0.46 | 8.85 | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 183136 | 4.00 | 35.00 | 1.00 | 1113 | -1.17 | 0.96 | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000 |
| 184464 | 3.00 | 29.00 | 0.00 | 112 | -3.06 | -11.52 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss |
| 184845 | 4.00 | 14.00 | 1.00 | 106 | -1.32 | 5.18 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 196821 | 3.00 | 0.00 | 0.00 | 233 | -3.86 | 14.38 | `observed_laser_overlap` | fast_mode |
| 203057 | 4.00 | 0.00 | 1.00 | 557 | -2.16 | -0.42 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss |
| 204530 | 3.00 | 0.00 | 0.00 | 574 | -3.50 | 10.51 | `modeled_committed_prefix_collision` | fast_mode |
| 205277 | 3.00 | 0.00 | 0.00 | 544 | -0.38 | 8.15 | `observed_laser_overlap` | fast_mode |
| 213385 | 3.00 | 0.00 | 0.00 | 364 | -4.08 | 6.96 | `modeled_committed_prefix_collision` | fast_mode |
| 214057 | 3.00 | 8.00 | 0.00 | 437 | -0.24 | 12.27 | `observed_bullet_overlap` | - |
| 214776 | 3.00 | 0.00 | 0.00 | 487 | -1.30 | - | `observed_laser_overlap` | playfield_boundary |
| 218925 | 3.00 | 3.00 | 0.00 | 336 | -2.72 | 5.67 | `observed_bullet_overlap` | fast_mode |
| 219583 | 3.00 | 9.00 | 0.00 | 544 | -3.38 | 1.95 | `observed_bullet_overlap` | playfield_boundary |
| 220715 | 3.00 | 3.00 | 0.00 | 566 | -2.74 | 1.65 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 221782 | 3.00 | 0.00 | 0.00 | 598 | -2.92 | 12.77 | `observed_bullet_overlap` | playfield_boundary |
| 222275 | 3.00 | 2.00 | 0.00 | 560 | -2.98 | -0.64 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 222814 | 4.00 | 0.00 | 1.00 | 558 | -2.85 | 10.05 | `modeled_committed_prefix_collision` | playfield_boundary |
| 226661 | 3.00 | 6.00 | 0.00 | 894 | -1.71 | 13.28 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |

## Spell Inventory And Runtime Coverage

Every spell below is statically reachable for route 2 Lunatic Final B. `unresolved` means this run did not persist the live spell ID; it does not mean the spell was absent.

### Stage 1

- ECL: `ecldata1.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | 蛍符「地上の彗星」 | リグル・ナイトバグ | 3 | 6 | 0 | 0 |
| 5 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 11 | 6 | 0 | 0 |
| 9 | 蠢符「ナイトバグトルネード」 | リグル・ナイトバグ | 13 | 27 | 0 | 0 |
| 12 | 隠蟲「永夜蟄居」 | リグル・ナイトバグ | 12 | 27 | 0 | 0 |

### Stage 2

- ECL: `ecldata2.ecl`
- Observed/expected phase-counter markers: 2/3.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 16 | 声符「木菟咆哮」 | ミスティア・ローレライ | 4 | 7 | 0 | 0 |
| 20 | 猛毒「毒蛾の暗闇演舞」 | ミスティア・ローレライ | 5 | 7 | 0 | 0 |
| 24 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 6 | 8 | 0 | 0 |
| 28 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 8 | 9 | 0 | 0 |
| 31 | 夜雀「真夜中のコーラスマスター」 | ミスティア・ローレライ | 3 | 7 | 0 | 0 |

### Stage 3

- ECL: `ecldata3.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 35 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 3 | 0 | 0 | 0 |
| 38 | 始符「エフェメラリティ137」 | 上白沢慧音 | 2 | 2 | 0 | 1 |
| 42 | 野符「GHQクライシス」 | 上白沢慧音 | 3 | 3 | 0 | 0 |
| 46 | 国体「三種の神器　郷」 | 上白沢慧音 | 3 | 0 | 0 | 0 |
| 50 | 虚史「幻想郷伝説」 | 上白沢慧音 | 1 | 0 | 1 | 0 |
| 53 | 未来「高天原」 | 上白沢慧音 | 1 | 0 | 1 | 0 |

### Stage 4A / Reimu

- ECL: `ecldata4a.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 57 | 夢境「二重大結界」 | 博麗霊夢 | 3 | 0 | 0 | 3 |
| 61 | 散霊「夢想封印　寂」 | 博麗霊夢 | 3 | 0 | 0 | 0 |
| 65 | 神技「八方龍殺陣」 | 博麗霊夢 | 7 | 27 | 0 | 2 |
| 69 | 回霊「夢想封印　侘」 | 博麗霊夢 | 2 | 17 | 0 | 1 |
| 73 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 5 | 4 | 0 | 0 |
| 76 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 2 | 5 | 0 | 0 |

### Stage 5

- ECL: `ecldata5.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 103 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 6 | 0 | 0 | 3 |
| 111 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 3 | 0 | 0 | 1 |
| 107 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 3 | 3 | 0 | 4 |
| 115 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 6 | 3 | 0 | 1 |
| 118 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 4 | 2 | 0 | 0 |

### Final B / Kaguya

- ECL: `ecldata7.ecl`
- Observed/expected phase-counter markers: 10/14.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 150 | 薬符「壺中の大銀河」 | 八意永琳 | 4 | 0 | 0 | 2 |
| 154 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 5 | 1 | 5 | 2 |
| 158 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 4 | 4 | 2 | 1 |
| 162 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 4 | 8 | 2 | 2 |
| 166 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 3 | 2 | 2 | 3 |
| 170 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 26 | 3 | 0 | 6 |
| 174 | 「永夜返し  -待宵-」 | 蓬莱山輝夜 | 3 | 1 | 0 | 1 |
| 178 | 「永夜返し  -子の四つ-」 | 蓬莱山輝夜 | 3 | 2 | 0 | 0 |
| 182 | 「永夜返し  -丑の四つ-」 | 蓬莱山輝夜 | 2 | 2 | 0 | 0 |
| 186 | 「永夜返し  -寅の四つ-」 | 蓬莱山輝夜 | 4 | 4 | 0 | 0 |
| 190 | 「永夜返し  -世明け-」 | 蓬莱山輝夜 | 12 | 5 | 0 | 0 |

## Runtime And Harness Findings

- Observed auto-Z stall frames: none.
- Route termination: `route_complete` at completion probe frame 226864.
- Unique robust solutions observed: 9308; solve time median/p95/max 99.99/386.09/540.90 ms.
- First-observed policy age median/p95/max: 3.00/9.00/1810.00 frames.
- Viability queries available: 51747/51747; robustly constrained decisions: 23260/52479.
- Robust-policy decisions without any usable query: 285/52032.
- Global-horizon/local-prefix cross-tab: 36014 decisions; winning global state with unsafe selected prefix: 12; losing global state with safe short prefix: 19395; selected globally certified action contradicted by the fresh local prefix checker: 6; selected action outside the reported winning set: 293.
- Live spell attribution was recorded at every hit edge; exact per-spell counts are preserved below.
- `1` hit edges remain in the `sensor_gap_or_unmodeled_hazard` class and require executor-level same-frame emission/transform evidence.

## Next Regression Work

1. Keep robust backward-reachability solves within the finite policy horizon, then verify nonzero live query and constrained-decision counts.
2. Replay all 77 retained witnesses through the integrated executor and preserve one regression per concrete failure.
3. Re-run focused Stage 4A and Final B practices before another full Lunatic route; compare hit frames, policy age, action-set exhaustion, and cluster recurrence.
4. Add item/Power state and finite Bomb resources only after the no-Bomb movement policy has passed physical validation.
