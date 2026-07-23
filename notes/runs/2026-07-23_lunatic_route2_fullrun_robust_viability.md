# TH08 Lunatic Full-Run Review: lunatic_route2_fullrun_robust_viability_20260723_194644

## Result

- Route: Sakuya/Remilia, Lunatic, Final B / Kaguya.
- Combat completion: yes; gameplay scene unloaded at frame 225973.
- Native phase-2 hit edges, including Last-Spell-saveable edges: 90.
- Deathbomb requests at those edges: 0.
- Hard no-Bomb input verification: passed across 69092 decisions.
- Post-hit Bomb-stock decreases: 44.00; this is respawn-stock reset telemetry, not evidence of Bomb input.
- Agent decisions: 69092.
- Raw trace size: 805388444 bytes across 1 segments.
- JSON decode errors: 0.
- Exact spell-level hit attribution: available from live `g_spell_card_state`.

The run is valid for stage-, death-, resource-, projectile-, latency-, and route-level analysis. Spell names below are the statically reachable Lunatic route inventory; unavailable runtime hit counts remain explicitly unresolved instead of guessed. The no-life patch allows post-hit resource resets to repeat, so resource-stock changes must not be interpreted as Bomb commands.

## Trace Integrity

| Segment | Frames | Decisions | Wall Z | Termination | Runtime error | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 2..225973 | 69092 | 412 | route_complete | - | `a01922392a8ffdefbe0275f5799f7c91a35ce6ee4052470e5acd8aed2dcde80d` |

The route is one continuous agent-controlled trace with no foreground interruption or manual re-arm gap.

## Stage Summary

| Stage | Frames | Decisions | Native hits | Deathbombs | Post-hit Bomb-stock decrease | Power start/end/min | Max bullets | Max lasers |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Stage 1 | 2..20950 | 7035 | 1 | 0 | 0.00 | 0.00/33.00/0.00 | 1181 | 0 |
| Stage 2 | 20950..43324 | 8042 | 5 | 0 | 3.00 | 38.00/66.00/29.00 | 1117 | 0 |
| Stage 3 | 43324..71161 | 8974 | 10 | 0 | 3.00 | 72.00/30.00/0.00 | 1160 | 200 |
| Stage 4A / Reimu | 71161..117077 | 13916 | 28 | 0 | 13.00 | 35.00/2.00/0.00 | 1520 | 0 |
| Stage 5 | 117077..162224 | 13278 | 13 | 0 | 8.00 | 7.00/11.00/0.00 | 1528 | 0 |
| Final B / Kaguya | 162224..225973 | 17847 | 33 | 0 | 17.00 | 16.00/15.00/0.00 | 1239 | 250 |

## Failure Taxonomy

| Primary class | Deaths | Interpretation |
| --- | ---: | --- |
| `modeled_committed_prefix_collision` | 40 | The measured three-frame input pipeline was already unsafe. |
| `observed_bullet_overlap` | 24 | A bullet overlaps the native player AABB in the hit observation. |
| `sensor_gap_or_unmodeled_hazard` | 18 | No observed overlap and positive pipeline clearance; same-frame ECL emission, transform error, or another unmodeled hazard is the leading explanation. |
| `observed_laser_overlap` | 7 | The player overlaps an active laser's exact finite segment; TH08 checks this before the broad bullet pass. |
| `active_laser_without_observed_overlap` | 1 | At least one laser is active, but none of the persisted finite segments overlaps the player in the hit observation. |

Contributing factors:

- `fast_mode`: 62 deaths
- `playfield_boundary`: 34 deaths
- `pool_density_over_1000`: 13 deaths
- `corridor_deadline_miss`: 1 deaths

## High-Risk Clusters

| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at hit |
| --- | --- | ---: | ---: | ---: | ---: |
| cluster-56 | Final B / Kaguya | 210432..212510 | 6 | 0.00 | 479 |
| cluster-12 | Stage 4A / Reimu | 72878..74320 | 4 | 5.00 | 594 |
| cluster-03 | Stage 2 | 23408..24459 | 3 | 51.00 | 506 |
| cluster-08 | Stage 3 | 51505..52391 | 3 | 8.00 | 620 |
| cluster-14 | Stage 4A / Reimu | 80499..81536 | 3 | 11.00 | 606 |
| cluster-16 | Stage 4A / Reimu | 83928..84854 | 3 | 2.00 | 605 |
| cluster-53 | Final B / Kaguya | 201528..202369 | 3 | 0.00 | 570 |
| cluster-07 | Stage 3 | 46003..46422 | 2 | 34.00 | 441 |
| cluster-20 | Stage 4A / Reimu | 102019..102444 | 2 | 0.00 | 1336 |
| cluster-21 | Stage 4A / Reimu | 106431..106885 | 2 | 9.00 | 87 |
| cluster-22 | Stage 4A / Reimu | 107506..107806 | 2 | 10.00 | 145 |
| cluster-24 | Stage 4A / Reimu | 109891..110471 | 2 | 2.00 | 547 |
| cluster-31 | Stage 5 | 124017..124317 | 2 | 12.00 | 550 |
| cluster-32 | Stage 5 | 128209..128732 | 2 | 1.00 | 903 |
| cluster-37 | Stage 5 | 152821..153228 | 2 | 0.00 | 476 |
| cluster-43 | Final B / Kaguya | 180605..181035 | 2 | 86.00 | 1183 |
| cluster-57 | Final B / Kaguya | 216635..217091 | 2 | 10.00 | 584 |
| cluster-59 | Final B / Kaguya | 219763..220123 | 2 | 11.00 | 552 |

## Stage Detail

### Stage 1

- Death frames: 1057
- Cause counts: `{"modeled_committed_prefix_collision": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 351/453.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1057 | 3.00 | 0.00 | 0.00 | 266 | -1.48 | - | `modeled_committed_prefix_collision` | fast_mode |

### Stage 2

- Death frames: 21717, 23408, 23908, 24459, 31227
- Cause counts: `{"modeled_committed_prefix_collision": 1, "sensor_gap_or_unmodeled_hazard": 3, "observed_bullet_overlap": 1}`
- Phase markers: observed 2, reachable static opcode `0x94` 3.
- Bottom/side occupancy decisions: 539/373.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 21717 | 3.00 | 45.00 | 0.00 | 71 | -3.09 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 23408 | 5.00 | 69.00 | 2.00 | 120 | 0.87 | - | `sensor_gap_or_unmodeled_hazard` | - |
| 23908 | 4.00 | 58.00 | 1.00 | 506 | -1.41 | - | `observed_bullet_overlap` | playfield_boundary |
| 24459 | 3.00 | 51.00 | 0.00 | 254 | 20.50 | - | `sensor_gap_or_unmodeled_hazard` | playfield_boundary,fast_mode |
| 31227 | 3.00 | 59.00 | 0.00 | 560 | 0.54 | -19.95 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |

### Stage 3

- Death frames: 44344, 45188, 46003, 46422, 51505, 51990, 52391, 57317, 58929, 70750
- Cause counts: `{"modeled_committed_prefix_collision": 7, "observed_bullet_overlap": 3}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 625/856.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 44344 | 3.00 | 72.00 | 0.00 | 302 | -1.49 | - | `modeled_committed_prefix_collision` | - |
| 45188 | 3.00 | 64.00 | 0.00 | 592 | -3.59 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 46003 | 3.00 | 50.00 | 0.00 | 441 | -1.43 | - | `observed_bullet_overlap` | fast_mode |
| 46422 | 3.00 | 34.00 | 0.00 | 336 | -1.33 | - | `modeled_committed_prefix_collision` | fast_mode |
| 51505 | 3.00 | 26.00 | 0.00 | 564 | -1.72 | - | `observed_bullet_overlap` | - |
| 51990 | 3.00 | 16.00 | 0.00 | 315 | -1.94 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 52391 | 3.00 | 8.00 | 0.00 | 620 | -1.76 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 57317 | 5.00 | 33.00 | 2.00 | 444 | 2.24 | - | `observed_bullet_overlap` | fast_mode |
| 58929 | 3.00 | 27.00 | 0.00 | 222 | -3.36 | - | `modeled_committed_prefix_collision` | fast_mode |
| 70750 | 4.00 | 46.00 | 1.00 | 264 | -4.05 | - | `modeled_committed_prefix_collision` | fast_mode |

### Stage 4A / Reimu

- Death frames: 72878, 73357, 73722, 74320, 75365, 80499, 81012, 81536, 83214, 83928, 84343, 84854, 90006, 93535, 94379, 102019, 102444, 106431, 106885, 107506, 107806, 108605, 109891, 110471, 111260, 111882, 114669, 116436
- Cause counts: `{"modeled_committed_prefix_collision": 10, "observed_bullet_overlap": 9, "sensor_gap_or_unmodeled_hazard": 9}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 686/840.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 72878 | 3.00 | 39.00 | 0.00 | 536 | -1.26 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 73357 | 3.00 | 33.00 | 0.00 | 352 | 1.80 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 73722 | 3.00 | 20.00 | 0.00 | 594 | 2.70 | - | `observed_bullet_overlap` | fast_mode |
| 74320 | 3.00 | 5.00 | 0.00 | 519 | -1.58 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 75365 | 4.00 | 6.00 | 1.00 | 1159 | -0.39 | - | `observed_bullet_overlap` | pool_density_over_1000 |
| 80499 | 4.00 | 11.00 | 1.00 | 606 | 13.92 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 81012 | 3.00 | 13.00 | 0.00 | 481 | -0.18 | - | `modeled_committed_prefix_collision` | - |
| 81536 | 4.00 | 11.00 | 1.00 | 420 | 27.09 | - | `sensor_gap_or_unmodeled_hazard` | - |
| 83214 | 4.00 | 10.00 | 1.00 | 604 | -3.02 | - | `modeled_committed_prefix_collision` | fast_mode |
| 83928 | 3.00 | 2.00 | 0.00 | 605 | 0.80 | - | `observed_bullet_overlap` | fast_mode |
| 84343 | 3.00 | 9.00 | 0.00 | 595 | -0.78 | - | `observed_bullet_overlap` | fast_mode |
| 84854 | 3.00 | 9.00 | 0.00 | 581 | -1.83 | - | `observed_bullet_overlap` | fast_mode |
| 90006 | 3.00 | 2.00 | 0.00 | 443 | 29.35 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 93535 | 3.00 | 4.00 | 0.00 | 640 | -0.98 | - | `modeled_committed_prefix_collision` | - |
| 94379 | 3.00 | 1.00 | 0.00 | 809 | -2.29 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 102019 | 4.00 | 8.00 | 1.00 | 1336 | 3.18 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 102444 | 4.00 | 0.00 | 1.00 | 1202 | 29.66 | - | `sensor_gap_or_unmodeled_hazard` | pool_density_over_1000 |
| 106431 | 3.00 | 10.00 | 0.00 | 53 | 24.39 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 106885 | 4.00 | 9.00 | 1.00 | 87 | 35.83 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 107506 | 4.00 | 10.00 | 1.00 | 119 | 8.60 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 107806 | 4.00 | 11.00 | 1.00 | 145 | 49.74 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 108605 | 4.00 | 11.00 | 1.00 | 175 | 37.67 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 109891 | 4.00 | 12.00 | 1.00 | 480 | -1.95 | - | `modeled_committed_prefix_collision` | fast_mode |
| 110471 | 3.00 | 2.00 | 0.00 | 547 | -3.05 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 111260 | 3.00 | 8.00 | 0.00 | 579 | -1.73 | - | `observed_bullet_overlap` | - |
| 111882 | 3.00 | 10.00 | 0.00 | 668 | -1.81 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 114669 | 4.00 | 22.00 | 1.00 | 1000 | -1.29 | - | `modeled_committed_prefix_collision` | pool_density_over_1000,fast_mode |
| 116436 | 4.00 | 7.00 | 1.00 | 1327 | -1.32 | - | `modeled_committed_prefix_collision` | pool_density_over_1000,fast_mode |

### Stage 5

- Death frames: 119835, 121086, 124017, 124317, 128209, 128732, 130027, 141144, 146897, 148721, 152821, 153228, 160079
- Cause counts: `{"observed_bullet_overlap": 6, "sensor_gap_or_unmodeled_hazard": 4, "modeled_committed_prefix_collision": 3}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1863/1686.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 119835 | 3.00 | 14.00 | 0.00 | 1133 | 2.66 | - | `observed_bullet_overlap` | pool_density_over_1000,fast_mode |
| 121086 | 4.00 | 19.00 | 1.00 | 757 | -3.89 | - | `observed_bullet_overlap` | playfield_boundary |
| 124017 | 4.00 | 17.00 | 1.00 | 365 | 32.07 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 124317 | 4.00 | 12.00 | 1.00 | 550 | 76.91 | - | `sensor_gap_or_unmodeled_hazard` | - |
| 128209 | 3.00 | 1.00 | 0.00 | 868 | 25.15 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 128732 | 4.00 | 12.00 | 1.00 | 903 | 14.47 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 130027 | 3.00 | 3.00 | 0.00 | 353 | -1.83 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 141144 | 6.00 | 19.00 | 3.00 | 1438 | 2.26 | - | `observed_bullet_overlap` | pool_density_over_1000,fast_mode |
| 146897 | 4.00 | 15.00 | 1.00 | 991 | -2.49 | - | `modeled_committed_prefix_collision` | fast_mode |
| 148721 | 3.00 | 1.00 | 0.00 | 997 | -2.99 | - | `observed_bullet_overlap` | fast_mode |
| 152821 | 3.00 | 0.00 | 0.00 | 419 | -1.71 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 153228 | 3.00 | 1.00 | 0.00 | 476 | -1.39 | - | `modeled_committed_prefix_collision` | fast_mode |
| 160079 | 3.00 | 18.00 | 0.00 | 1211 | -1.12 | - | `observed_bullet_overlap` | pool_density_over_1000 |

### Final B / Kaguya

- Death frames: 164904, 170613, 171650, 174528, 180605, 181035, 181719, 182499, 184254, 189769, 192826, 195000, 197502, 198145, 198791, 201528, 202023, 202369, 203273, 204282, 210432, 210818, 211406, 211779, 212173, 212510, 216635, 217091, 219054, 219763, 220123, 223219, 225770
- Cause counts: `{"modeled_committed_prefix_collision": 18, "sensor_gap_or_unmodeled_hazard": 2, "observed_bullet_overlap": 5, "active_laser_without_observed_overlap": 1, "observed_laser_overlap": 7}`
- Phase markers: observed 11, reachable static opcode `0x94` 14.
- Bottom/side occupancy decisions: 1434/1035.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 164904 | 4.00 | 55.00 | 1.00 | 390 | -1.38 | - | `modeled_committed_prefix_collision` | fast_mode |
| 170613 | 3.00 | 101.00 | 0.00 | 340 | 24.48 | - | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 171650 | 4.00 | 95.00 | 1.00 | 332 | -3.87 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 174528 | 4.00 | 92.00 | 1.00 | 600 | -1.75 | - | `modeled_committed_prefix_collision` | fast_mode |
| 180605 | 4.00 | 92.00 | 1.00 | 1055 | -2.24 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 181035 | 4.00 | 86.00 | 1.00 | 1183 | -0.92 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 181719 | 4.00 | 73.00 | 1.00 | 1101 | 0.41 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 182499 | 4.00 | 68.00 | 1.00 | 1108 | -1.54 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000 |
| 184254 | 3.00 | 64.00 | 0.00 | 111 | -3.42 | - | `modeled_committed_prefix_collision` | fast_mode |
| 189769 | 3.00 | 54.00 | 0.00 | 455 | -0.58 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 192826 | 4.00 | 48.00 | 1.00 | 230 | -2.69 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 195000 | 3.00 | 33.00 | 0.00 | 242 | 0.86 | - | `active_laser_without_observed_overlap` | fast_mode |
| 197502 | 3.00 | 24.00 | 0.00 | 0 | 9999.00 | - | `sensor_gap_or_unmodeled_hazard` | - |
| 198145 | 4.00 | 9.00 | 1.00 | 724 | -1.66 | - | `modeled_committed_prefix_collision` | fast_mode |
| 198791 | 4.00 | 12.00 | 1.00 | 712 | -2.10 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 201528 | 4.00 | 11.00 | 1.00 | 570 | -4.95 | - | `observed_laser_overlap` | playfield_boundary |
| 202023 | 3.00 | 3.00 | 0.00 | 540 | -7.19 | - | `observed_laser_overlap` | playfield_boundary,fast_mode |
| 202369 | 3.00 | 0.00 | 0.00 | 486 | -4.50 | - | `observed_laser_overlap` | fast_mode |
| 203273 | 4.00 | 2.00 | 1.00 | 544 | -4.67 | - | `observed_laser_overlap` | playfield_boundary |
| 204282 | 3.00 | 0.00 | 0.00 | 564 | -6.91 | - | `observed_laser_overlap` | playfield_boundary |
| 210432 | 3.00 | 3.00 | 0.00 | 106 | -1.73 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 210818 | 3.00 | 10.00 | 0.00 | 407 | -7.76 | - | `observed_laser_overlap` | fast_mode |
| 211406 | 3.00 | 2.00 | 0.00 | 479 | -2.79 | - | `modeled_committed_prefix_collision` | fast_mode |
| 211779 | 3.00 | 0.00 | 0.00 | 342 | -7.53 | - | `observed_laser_overlap` | - |
| 212173 | 4.00 | 10.00 | 1.00 | 416 | -1.35 | - | `observed_bullet_overlap` | - |
| 212510 | 3.00 | 1.00 | 0.00 | 360 | -1.30 | - | `modeled_committed_prefix_collision` | - |
| 216635 | 3.00 | 18.00 | 0.00 | 563 | 0.12 | - | `observed_bullet_overlap` | fast_mode |
| 217091 | 4.00 | 10.00 | 1.00 | 584 | -1.73 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 219054 | 4.00 | 10.00 | 1.00 | 578 | -2.75 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 219763 | 4.00 | 11.00 | 1.00 | 552 | -2.39 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 220123 | 4.00 | 13.00 | 1.00 | 542 | -2.15 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 223219 | 4.00 | 15.00 | 0.00 | 908 | -1.53 | - | `modeled_committed_prefix_collision` | fast_mode |
| 225770 | 4.00 | 15.00 | 0.00 | 1009 | -6.63 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |

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
| 50 | 虚史「幻想郷伝説」 | 上白沢慧音 | 1 | 0 | 1 | 1 |
| 53 | 未来「高天原」 | 上白沢慧音 | 1 | 0 | 1 | 0 |

### Stage 4A / Reimu

- ECL: `ecldata4a.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 57 | 夢境「二重大結界」 | 博麗霊夢 | 3 | 0 | 0 | 4 |
| 61 | 散霊「夢想封印　寂」 | 博麗霊夢 | 3 | 0 | 0 | 1 |
| 65 | 神技「八方龍殺陣」 | 博麗霊夢 | 7 | 27 | 0 | 2 |
| 69 | 回霊「夢想封印　侘」 | 博麗霊夢 | 2 | 17 | 0 | 4 |
| 73 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 5 | 4 | 0 | 2 |
| 76 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 2 | 5 | 0 | 0 |

### Stage 5

- ECL: `ecldata5.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 103 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 6 | 0 | 0 | 1 |
| 111 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 3 | 0 | 0 | 0 |
| 107 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 3 | 3 | 0 | 2 |
| 115 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 6 | 3 | 0 | 1 |
| 118 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 4 | 2 | 0 | 0 |

### Final B / Kaguya

- ECL: `ecldata7.ecl`
- Observed/expected phase-counter markers: 11/14.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 150 | 薬符「壺中の大銀河」 | 八意永琳 | 4 | 0 | 0 | 1 |
| 154 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 5 | 1 | 5 | 1 |
| 158 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 4 | 4 | 2 | 2 |
| 162 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 4 | 8 | 2 | 5 |
| 166 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 3 | 2 | 2 | 6 |
| 170 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 26 | 3 | 0 | 5 |
| 174 | 「永夜返し  -待宵-」 | 蓬莱山輝夜 | 3 | 1 | 0 | 1 |
| 178 | 「永夜返し  -子の四つ-」 | 蓬莱山輝夜 | 3 | 2 | 0 | 1 |
| 182 | 「永夜返し  -丑の四つ-」 | 蓬莱山輝夜 | 2 | 2 | 0 | 0 |
| 186 | 「永夜返し  -寅の四つ-」 | 蓬莱山輝夜 | 4 | 4 | 0 | 0 |
| 190 | 「永夜返し  -世明け-」 | 蓬莱山輝夜 | 12 | 5 | 0 | 0 |

## Runtime And Harness Findings

- Observed auto-Z stall frames: none.
- Route termination: `route_complete` at completion probe frame 225973.
- Unique robust solutions observed: 1064; solve time median/p95/max 2455.95/4038.64/6141.66 ms.
- First-observed policy age median/p95/max: 152.00/259.00/3899.00 frames.
- Viability queries available: 759/759; robustly constrained decisions: 563/69092.
- Robust-policy decisions without any usable query: 63653/64412.
- Live spell attribution was recorded at every hit edge; exact per-spell counts are preserved below.
- `18` hit edges remain in the `sensor_gap_or_unmodeled_hazard` class and require executor-level same-frame emission/transform evidence.

## Next Regression Work

1. Keep robust backward-reachability solves within the finite policy horizon, then verify nonzero live query and constrained-decision counts.
2. Replay all 90 retained witnesses through the integrated executor and preserve one regression per concrete failure.
3. Re-run focused Stage 4A and Final B practices before another full Lunatic route; compare hit frames, policy age, action-set exhaustion, and cluster recurrence.
4. Add item/Power state and finite Bomb resources only after the no-Bomb movement policy has passed physical validation.

## Post-Run Correction

- The formal artifacts use dossier schema v2. Bomb use is verified from
  controller configuration and input/action evidence; the 44-unit resource
  change is labelled post-hit stock reset, not Bomb spend.
- The offline repair adds exact-below-cap sparse hazard rasterization,
  conservative influence-radius grouping, exact lazy repair-volume queries,
  transition prewarm, and a forecasted rolling policy epoch.
- A Windows 1,500-bullet/250-laser stress benchmark with an 80-frame forecast
  measured 1,237 ms warm median after the repair. This is performance evidence,
  not physical acceptance.
- This run remains the 90-case discovery corpus. The corrected controller has
  not yet been physically tested; focused Stage 4A and Final B are next.
