# TH08 Lunatic Full-Run Review: 20260723-lunatic-route2-final-b

## Result

- Route: Sakuya/Remilia, Lunatic, Final B / Kaguya.
- Combat completion: yes; gameplay scene unloaded at frame 209373.
- Native phase-2 hit edges, including Last-Spell-saveable edges: 91.
- Deathbomb requests at those edges: 62; observed Bomb spend: 98.00.
- Agent decisions: 53335.
- Raw trace size: 557065721 bytes across 2 segments.
- JSON decode errors: 0.
- Exact spell-level hit attribution: unavailable in this run because the live schema did not record `g_spell_card_state`.

The run is valid for stage-, death-, resource-, projectile-, latency-, and route-level analysis. Spell names below are the statically reachable Lunatic route inventory; unavailable runtime hit counts remain explicitly unresolved instead of guessed. Because the no-life patch allows post-hit resource resets to repeat, observed Bomb spend is a failure metric, not a feasible finite-stock route budget.

## Trace Integrity

| Segment | Frames | Decisions | Wall Z | Termination | Runtime error | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 1..158850 | 42029 | 0 | agent_error | TH08 lost foreground; refusing to send or retain keys | `3d6f461e31c275584651873251b09e6b76537a387a8c69113b6989190f7c81b2` |
| 2 | 160535..209373 | 11306 | 0 | external_stop | - | `d139c58e0f04c2d9ad7c25422c4417e7cfce64844d8f67cbcfdcef85285fc2bf` |

The segment gap is a foreground-loss/manual-rearm interval. It is not scored as agent-controlled play.

## Stage Summary

| Stage | Frames | Decisions | Native hits | Deathbombs | Bomb spend | Power start/end/min | Max bullets | Max lasers |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Stage 1 | 1..19382 | 5551 | 2 | 2 | 3.00 | 0.00/49.00/0.00 | 1166 | 0 |
| Stage 2 | 19384..42137 | 7388 | 4 | 2 | 4.00 | 54.00/112.00/54.00 | 1175 | 0 |
| Stage 3 | 42139..68117 | 7284 | 13 | 9 | 15.00 | 118.00/113.00/109.00 | 1010 | 200 |
| Stage 4A / Reimu | 68119..110426 | 10789 | 21 | 14 | 21.00 | 118.00/88.00/85.00 | 1362 | 0 |
| Stage 5 | 110428..151701 | 9783 | 22 | 15 | 23.00 | 93.00/73.00/61.00 | 1527 | 0 |
| Final B / Kaguya | 151703..209373 | 12540 | 29 | 20 | 32.00 | 78.00/19.00/3.00 | 1220 | 240 |

## Failure Taxonomy

| Primary class | Deaths | Interpretation |
| --- | ---: | --- |
| `observed_bullet_overlap` | 35 | A bullet overlaps the native player AABB in the hit observation. |
| `modeled_committed_prefix_collision` | 20 | The measured three-frame input pipeline was already unsafe. |
| `sensor_gap_or_unmodeled_hazard` | 20 | No observed overlap and positive pipeline clearance; same-frame ECL emission, transform error, or another unmodeled hazard is the leading explanation. |
| `observed_laser_overlap` | 11 | The player overlaps an active laser's exact finite segment; TH08 checks this before the broad bullet pass. |
| `active_laser_without_observed_overlap` | 5 | At least one laser is active, but none of the persisted finite segments overlaps the player in the hit observation. |

Contributing factors:

- `corridor_deadline_miss`: 74 deaths
- `fast_mode`: 68 deaths
- `playfield_boundary`: 32 deaths
- `pool_density_over_1000`: 16 deaths
- `action_lag_over_model`: 14 deaths

## High-Risk Clusters

| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at hit |
| --- | --- | ---: | ---: | ---: | ---: |
| cluster-15 | Stage 3 | 66537..67877 | 5 | 109.00 | 332 |
| cluster-62 | Final B / Kaguya | 187413..189223 | 5 | 20.00 | 562 |
| cluster-19 | Stage 4A / Reimu | 76867..78395 | 4 | 111.00 | 746 |
| cluster-58 | Final B / Kaguya | 173355..174419 | 4 | 47.00 | 92 |
| cluster-42 | Stage 5 | 140177..140994 | 3 | 84.00 | 1011 |
| cluster-63 | Final B / Kaguya | 195434..196247 | 3 | 10.00 | 416 |
| cluster-20 | Stage 4A / Reimu | 79563..79866 | 2 | 96.00 | 594 |
| cluster-22 | Stage 4A / Reimu | 88067..88503 | 2 | 113.00 | 961 |
| cluster-26 | Stage 4A / Reimu | 101510..101903 | 2 | 101.00 | 145 |

## Stage Detail

### Stage 1

- Death frames: 5028, 18320
- Cause counts: `{"sensor_gap_or_unmodeled_hazard": 1, "observed_bullet_overlap": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 75/149.

| Frame | Bombs | Power | Bomb cost | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 5028 | 3.00 | 44.00 | 2.00 | 290 | 12.51 | -12.22 | `sensor_gap_or_unmodeled_hazard` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 18320 | 1.00 | 49.00 | 1.00 | 590 | 2.65 | -11.01 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |

### Stage 2

- Death frames: 21214, 22343, 24595, 30969
- Cause counts: `{"observed_bullet_overlap": 1, "sensor_gap_or_unmodeled_hazard": 3}`
- Phase markers: observed 2, reachable static opcode `0x94` 3.
- Bottom/side occupancy decisions: 320/196.

| Frame | Bombs | Power | Bomb cost | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 21214 | 0.00 | 86.00 | 0.00 | 183 | 2.09 | -22.59 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 22343 | 4.00 | 95.00 | 2.00 | 353 | 17.21 | -26.11 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss |
| 24595 | 2.00 | 98.00 | 2.00 | 281 | 9.20 | -13.14 | `sensor_gap_or_unmodeled_hazard` | playfield_boundary,corridor_deadline_miss |
| 30969 | 0.00 | 105.00 | 0.00 | 414 | 21.27 | -13.77 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |

### Stage 3

- Death frames: 47372, 48301, 49172, 50035, 54974, 58164, 62153, 64242, 66537, 66833, 67217, 67562, 67877
- Cause counts: `{"modeled_committed_prefix_collision": 4, "observed_bullet_overlap": 5, "sensor_gap_or_unmodeled_hazard": 1, "observed_laser_overlap": 1, "active_laser_without_observed_overlap": 2}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 403/184.

| Frame | Bombs | Power | Bomb cost | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 47372 | 3.00 | 128.00 | 2.00 | 281 | -2.43 | -19.78 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 48301 | 1.00 | 128.00 | 1.00 | 294 | 2.00 | -35.90 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 49172 | 0.00 | 128.00 | 0.00 | 836 | -3.51 | -29.12 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 50035 | 3.00 | 113.00 | 2.00 | 707 | -3.12 | -31.62 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 54974 | 2.00 | 128.00 | 2.00 | 417 | -0.19 | -3.89 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 58164 | 0.00 | 128.00 | 0.00 | 473 | 0.38 | -6.26 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 62153 | 3.00 | 121.00 | 2.00 | 162 | 0.61 | -7.86 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 64242 | 1.00 | 121.00 | 1.00 | 430 | 4.80 | -16.45 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss |
| 66537 | 0.00 | 128.00 | 0.00 | 325 | -5.97 | -3.47 | `observed_laser_overlap` | playfield_boundary,corridor_deadline_miss,action_lag_over_model,fast_mode |
| 66833 | 3.00 | 113.00 | 2.00 | 280 | 5.19 | - | `active_laser_without_observed_overlap` | action_lag_over_model,fast_mode |
| 67217 | 1.00 | 125.00 | 1.00 | 332 | -5.55 | - | `modeled_committed_prefix_collision` | playfield_boundary,action_lag_over_model,fast_mode |
| 67562 | 0.00 | 125.00 | 0.00 | 296 | 3.23 | - | `active_laser_without_observed_overlap` | playfield_boundary,action_lag_over_model,fast_mode |
| 67877 | 3.00 | 109.00 | 2.00 | 306 | -2.44 | - | `modeled_committed_prefix_collision` | playfield_boundary,action_lag_over_model,fast_mode |

### Stage 4A / Reimu

- Death frames: 69798, 71971, 72620, 76867, 77451, 77925, 78395, 79563, 79866, 87358, 88067, 88503, 96572, 97473, 98209, 101510, 101903, 104277, 104937, 108839, 109568
- Cause counts: `{"sensor_gap_or_unmodeled_hazard": 9, "modeled_committed_prefix_collision": 7, "observed_bullet_overlap": 5}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 282/278.

| Frame | Bombs | Power | Bomb cost | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 69798 | 1.00 | 124.00 | 1.00 | 465 | 5.38 | -13.92 | `sensor_gap_or_unmodeled_hazard` | playfield_boundary,corridor_deadline_miss |
| 71971 | 0.00 | 128.00 | 0.00 | 328 | -1.41 | -20.73 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 72620 | 3.00 | 113.00 | 2.00 | 1079 | -4.53 | -10.14 | `observed_bullet_overlap` | corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 76867 | 1.00 | 124.00 | 1.00 | 216 | 17.89 | -7.52 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss |
| 77451 | 0.00 | 124.00 | 0.00 | 713 | 57.68 | -9.27 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 77925 | 3.00 | 111.00 | 2.00 | 746 | 50.74 | -4.20 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss |
| 78395 | 1.00 | 111.00 | 1.00 | 746 | 19.49 | -8.15 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 79563 | 0.00 | 111.00 | 0.00 | 594 | -3.00 | -13.89 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 79866 | 3.00 | 96.00 | 2.00 | 509 | 49.52 | -21.54 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 87358 | 1.00 | 128.00 | 1.00 | 613 | -0.01 | -4.78 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 88067 | 0.00 | 128.00 | 0.00 | 840 | -2.31 | -17.87 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 88503 | 3.00 | 113.00 | 2.00 | 961 | -3.54 | -22.71 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 96572 | 1.00 | 116.00 | 1.00 | 1238 | -2.42 | -16.41 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 97473 | 0.00 | 116.00 | 0.00 | 1280 | -0.17 | -21.97 | `observed_bullet_overlap` | corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 98209 | 3.00 | 101.00 | 2.00 | 1208 | 3.39 | -11.15 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 101510 | 1.00 | 101.00 | 1.00 | 145 | 52.08 | 0.69 | `sensor_gap_or_unmodeled_hazard` | - |
| 101903 | 0.00 | 101.00 | 0.00 | 64 | 19.81 | -13.30 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 104277 | 3.00 | 88.00 | 2.00 | 715 | -0.38 | -35.46 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 104937 | 1.00 | 88.00 | 1.00 | 638 | -1.80 | -27.45 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 108839 | 0.00 | 102.00 | 0.00 | 1273 | -1.57 | -14.61 | `modeled_committed_prefix_collision` | corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 109568 | 3.00 | 88.00 | 2.00 | 1345 | -1.27 | -8.65 | `observed_bullet_overlap` | corridor_deadline_miss,pool_density_over_1000,fast_mode |

### Stage 5

- Death frames: 110998, 112405, 113694, 117428, 121493, 122795, 124723, 130865, 131708, 134052, 135735, 140177, 140528, 140994, 143744, 144559, 146226, 146963, 147679, 148412, 149775, 150614
- Cause counts: `{"observed_bullet_overlap": 15, "sensor_gap_or_unmodeled_hazard": 2, "modeled_committed_prefix_collision": 5}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1130/574.

| Frame | Bombs | Power | Bomb cost | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 110998 | 1.00 | 93.00 | 1.00 | 517 | -1.56 | -24.94 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 112405 | 0.00 | 98.00 | 0.00 | 726 | -1.07 | -11.72 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 113694 | 3.00 | 98.00 | 2.00 | 213 | -0.36 | -24.02 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 117428 | 1.00 | 104.00 | 1.00 | 791 | -3.50 | -1.19 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 121493 | 0.00 | 104.00 | 0.00 | 926 | 0.50 | -27.17 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 122795 | 3.00 | 89.00 | 2.00 | 342 | 0.76 | -31.01 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 124723 | 1.00 | 95.00 | 1.00 | 283 | 1.23 | -1.27 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 130865 | 2.00 | 107.00 | 2.00 | 397 | 2.44 | -15.90 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 131708 | 0.00 | 107.00 | 0.00 | 426 | 0.69 | -22.05 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 134052 | 3.00 | 100.00 | 2.00 | 1496 | -2.72 | -10.80 | `observed_bullet_overlap` | corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 135735 | 1.00 | 100.00 | 1.00 | 1487 | -1.14 | -9.21 | `modeled_committed_prefix_collision` | corridor_deadline_miss,action_lag_over_model,pool_density_over_1000,fast_mode |
| 140177 | 0.00 | 100.00 | 0.00 | 1011 | -5.06 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 140528 | 3.00 | 84.00 | 2.00 | 1004 | -7.77 | - | `observed_bullet_overlap` | pool_density_over_1000,fast_mode |
| 140994 | 1.00 | 84.00 | 1.00 | 1010 | -1.50 | - | `modeled_committed_prefix_collision` | playfield_boundary,action_lag_over_model,pool_density_over_1000 |
| 143744 | 0.00 | 84.00 | 0.00 | 493 | -1.97 | -24.40 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 144559 | 3.00 | 77.00 | 2.00 | 409 | 1.14 | -17.58 | `observed_bullet_overlap` | corridor_deadline_miss |
| 146226 | 1.00 | 77.00 | 1.00 | 245 | -0.13 | -3.94 | `observed_bullet_overlap` | corridor_deadline_miss |
| 146963 | 0.00 | 77.00 | 0.00 | 341 | 2.04 | -12.53 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss |
| 147679 | 3.00 | 70.00 | 2.00 | 340 | -1.11 | -18.12 | `observed_bullet_overlap` | corridor_deadline_miss |
| 148412 | 1.00 | 70.00 | 1.00 | 338 | -1.21 | -17.20 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 149775 | 0.00 | 87.00 | 0.00 | 1157 | -0.27 | -16.08 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 150614 | 3.00 | 73.00 | 2.00 | 1173 | -1.33 | -11.17 | `modeled_committed_prefix_collision` | corridor_deadline_miss,pool_density_over_1000,fast_mode |

### Final B / Kaguya

- Death frames: 161147, 163663, 164288, 164994, 170663, 171585, 172681, 173355, 173733, 174091, 174419, 177723, 180491, 181287, 187413, 187845, 188331, 188689, 189223, 195434, 195845, 196247, 199039, 199814, 200492, 201242, 201875, 202617, 203556
- Cause counts: `{"sensor_gap_or_unmodeled_hazard": 4, "modeled_committed_prefix_collision": 4, "observed_bullet_overlap": 8, "observed_laser_overlap": 10, "active_laser_without_observed_overlap": 3}`
- Phase markers: observed 11, reachable static opcode `0x94` 14.
- Bottom/side occupancy decisions: 984/418.

| Frame | Bombs | Power | Bomb cost | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 161147 | 4.00 | 77.00 | 2.00 | 239 | 17.36 | -10.65 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 163663 | 2.00 | 77.00 | 2.00 | 723 | -1.29 | -13.51 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 164288 | 0.00 | 77.00 | 0.00 | 670 | 1.75 | -21.62 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,fast_mode |
| 164994 | 3.00 | 63.00 | 2.00 | 316 | 0.96 | -10.36 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 170663 | 2.00 | 66.00 | 2.00 | 1125 | 1.85 | -38.07 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,pool_density_over_1000 |
| 171585 | 0.00 | 66.00 | 0.00 | 1126 | 1.80 | -33.04 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss,pool_density_over_1000 |
| 172681 | 3.00 | 61.00 | 2.00 | 1161 | -3.06 | -21.26 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 173355 | 1.00 | 61.00 | 1.00 | 68 | -7.60 | -4.30 | `observed_laser_overlap` | playfield_boundary,corridor_deadline_miss,action_lag_over_model,fast_mode |
| 173733 | 0.00 | 61.00 | 0.00 | 78 | 11.71 | - | `active_laser_without_observed_overlap` | playfield_boundary,action_lag_over_model,fast_mode |
| 174091 | 3.00 | 47.00 | 2.00 | 92 | -1.78 | - | `observed_laser_overlap` | playfield_boundary,action_lag_over_model |
| 174419 | 1.00 | 47.00 | 1.00 | 30 | -5.08 | - | `observed_laser_overlap` | action_lag_over_model,fast_mode |
| 177723 | 0.00 | 52.00 | 0.00 | 440 | -3.55 | -16.06 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 180491 | 3.00 | 46.00 | 2.00 | 144 | -3.39 | - | `observed_laser_overlap` | - |
| 181287 | 1.00 | 46.00 | 1.00 | 243 | 0.62 | - | `active_laser_without_observed_overlap` | playfield_boundary,action_lag_over_model,fast_mode |
| 187413 | 0.00 | 51.00 | 0.00 | 562 | -3.84 | -34.27 | `observed_laser_overlap` | corridor_deadline_miss |
| 187845 | 3.00 | 35.00 | 2.00 | 542 | -7.68 | 9.98 | `observed_laser_overlap` | playfield_boundary,fast_mode |
| 188331 | 1.00 | 35.00 | 1.00 | 540 | -7.29 | -5.84 | `observed_laser_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 188689 | 0.00 | 35.00 | 0.00 | 302 | -3.91 | -20.58 | `observed_laser_overlap` | corridor_deadline_miss,fast_mode |
| 189223 | 3.00 | 20.00 | 2.00 | 522 | -6.42 | -9.74 | `observed_laser_overlap` | playfield_boundary,corridor_deadline_miss |
| 195434 | 1.00 | 25.00 | 1.00 | 330 | -4.33 | - | `observed_laser_overlap` | fast_mode |
| 195845 | 0.00 | 25.00 | 0.00 | 345 | 1.42 | - | `active_laser_without_observed_overlap` | action_lag_over_model |
| 196247 | 3.00 | 10.00 | 2.00 | 416 | 0.41 | - | `observed_bullet_overlap` | action_lag_over_model |
| 199039 | 1.00 | 25.00 | 1.00 | 284 | -3.46 | -16.33 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 199814 | 0.00 | 25.00 | 0.00 | 594 | 0.08 | -11.91 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 200492 | 3.00 | 19.00 | 2.00 | 560 | 0.07 | -29.97 | `observed_bullet_overlap` | corridor_deadline_miss |
| 201242 | 1.00 | 19.00 | 1.00 | 566 | 2.62 | -14.13 | `sensor_gap_or_unmodeled_hazard` | corridor_deadline_miss |
| 201875 | 0.00 | 19.00 | 0.00 | 554 | -2.33 | -6.03 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 202617 | 3.00 | 14.00 | 2.00 | 565 | -1.17 | -16.83 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 203556 | 1.00 | 14.00 | 1.00 | 568 | -2.38 | -15.01 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |

## Spell Inventory And Runtime Coverage

Every spell below is statically reachable for route 2 Lunatic Final B. `unresolved` means this run did not persist the live spell ID; it does not mean the spell was absent.

### Stage 1

- ECL: `ecldata1.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | 蛍符「地上の彗星」 | リグル・ナイトバグ | 3 | 6 | 0 | unresolved |
| 5 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 11 | 6 | 0 | unresolved |
| 9 | 蠢符「ナイトバグトルネード」 | リグル・ナイトバグ | 13 | 27 | 0 | unresolved |
| 12 | 隠蟲「永夜蟄居」 | リグル・ナイトバグ | 12 | 27 | 0 | unresolved |

### Stage 2

- ECL: `ecldata2.ecl`
- Observed/expected phase-counter markers: 2/3.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 16 | 声符「木菟咆哮」 | ミスティア・ローレライ | 4 | 7 | 0 | unresolved |
| 20 | 猛毒「毒蛾の暗闇演舞」 | ミスティア・ローレライ | 5 | 7 | 0 | unresolved |
| 24 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 6 | 8 | 0 | unresolved |
| 28 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 8 | 9 | 0 | unresolved |
| 31 | 夜雀「真夜中のコーラスマスター」 | ミスティア・ローレライ | 3 | 7 | 0 | unresolved |

### Stage 3

- ECL: `ecldata3.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 35 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 3 | 0 | 0 | unresolved |
| 38 | 始符「エフェメラリティ137」 | 上白沢慧音 | 2 | 2 | 0 | unresolved |
| 42 | 野符「GHQクライシス」 | 上白沢慧音 | 3 | 3 | 0 | unresolved |
| 46 | 国体「三種の神器　郷」 | 上白沢慧音 | 3 | 0 | 0 | unresolved |
| 50 | 虚史「幻想郷伝説」 | 上白沢慧音 | 1 | 0 | 1 | unresolved |
| 53 | 未来「高天原」 | 上白沢慧音 | 1 | 0 | 1 | unresolved |

### Stage 4A / Reimu

- ECL: `ecldata4a.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 57 | 夢境「二重大結界」 | 博麗霊夢 | 3 | 0 | 0 | unresolved |
| 61 | 散霊「夢想封印　寂」 | 博麗霊夢 | 3 | 0 | 0 | unresolved |
| 65 | 神技「八方龍殺陣」 | 博麗霊夢 | 7 | 27 | 0 | unresolved |
| 69 | 回霊「夢想封印　侘」 | 博麗霊夢 | 2 | 17 | 0 | unresolved |
| 73 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 5 | 4 | 0 | unresolved |
| 76 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 2 | 5 | 0 | unresolved |

### Stage 5

- ECL: `ecldata5.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 103 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 6 | 0 | 0 | unresolved |
| 111 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 3 | 0 | 0 | unresolved |
| 107 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 3 | 3 | 0 | unresolved |
| 115 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 6 | 3 | 0 | unresolved |
| 118 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 4 | 2 | 0 | unresolved |

### Final B / Kaguya

- ECL: `ecldata7.ecl`
- Observed/expected phase-counter markers: 11/14.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 150 | 薬符「壺中の大銀河」 | 八意永琳 | 4 | 0 | 0 | unresolved |
| 154 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 5 | 1 | 5 | unresolved |
| 158 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 4 | 4 | 2 | unresolved |
| 162 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 4 | 8 | 2 | unresolved |
| 166 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 3 | 2 | 2 | unresolved |
| 170 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 26 | 3 | 0 | unresolved |
| 174 | 「永夜返し  -待宵-」 | 蓬莱山輝夜 | 3 | 1 | 0 | unresolved |
| 178 | 「永夜返し  -子の四つ-」 | 蓬莱山輝夜 | 3 | 2 | 0 | unresolved |
| 182 | 「永夜返し  -丑の四つ-」 | 蓬莱山輝夜 | 2 | 2 | 0 | unresolved |
| 186 | 「永夜返し  -寅の四つ-」 | 蓬莱山輝夜 | 4 | 4 | 0 | unresolved |
| 190 | 「永夜返し  -世明け-」 | 蓬莱山輝夜 | 12 | 5 | 0 | unresolved |

## Runtime And Harness Findings

- Observed auto-Z stall frames: 19382, 27728, 42137, 68117, 74880, 128708, 151701.
- Auto-Z was frame-driven, but dialogue can freeze the enemy manager counter. The post-run fix adds a foreground-checked wall-clock release/press edge and restores held Z without a new gameplay frame.
- The first segment stopped on foreground loss at frame 158850. The continuation begins at 160535; that interval is excluded from agent scoring.
- Gameplay scene unload at frame 209373 also froze the counter. The post-run loop now checks scene state while waiting for frame advance and emits `gameplay_ended` without an external stop.
- The post-run recorder now persists active flags, exact ID, enemy pointer, and decoded name from `g_spell_card_state`.
- 56 of 91 hit edges have no observed same-frame bullet overlap. The highest-priority model fix remains injecting enemy-ECL same-frame emissions and exact transforms into the committed-input horizon.

## Next Regression Work

1. Explain the five active-laser/no-overlap and twenty sensor-gap cases with exact same-frame ECL/transform executor traces.
2. Replay all 91 retained witnesses through the integrated executor before deduplicating equivalent root causes.
3. Physically validate gate-first local ordering and fixed-expiry lane commitment on the same Lunatic Final B route.
4. Add Bomb/Power/item state to phase-level component search, then compare native hits, Bomb spend, Power curve, per-spell exposure, and cluster recurrence.
