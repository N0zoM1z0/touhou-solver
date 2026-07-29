# TH08 Lunatic Full-Run Review: lunatic_route2_fullrun_unattended_20260730_002115

## Result

- Route: Sakuya/Remilia, Lunatic, Final B / Kaguya.
- Combat completion: yes; gameplay scene unloaded at frame 229992.
- Native phase-2 hit edges, including Last-Spell-saveable edges: 74.
- Deathbomb requests at those edges: 0.
- Hard no-Bomb input verification: passed across 60877 decisions.
- Post-hit Bomb-stock decreases: 20.00; this is respawn-stock reset telemetry, not evidence of Bomb input.
- Agent decisions: 60877.
- Raw trace size: 2009399974 bytes across 1 segments.
- JSON decode errors: 0.
- Exact spell-level hit attribution: available from live `g_spell_card_state`.

The run is valid for stage-, death-, resource-, projectile-, latency-, and route-level analysis. Spell names below are the statically reachable Lunatic route inventory; unavailable runtime hit counts remain explicitly unresolved instead of guessed. The no-life patch allows post-hit resource resets to repeat, so resource-stock changes must not be interpreted as Bomb commands.

## Trace Integrity

| Segment | Frames | Decisions | Wall Z | Termination | Runtime error | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 1..229992 | 60877 | 411 | route_complete | - | `ffe52f97e959a92ec0adb06e418c17e2a97c8e2209f0978a1249f1b66e8a69d0` |

The route is one continuous agent-controlled trace with no foreground interruption or manual re-arm gap.

## Stage Summary

| Stage | Frames | Decisions | Native hits | Deathbombs | Post-hit Bomb-stock decrease | Power start/end/min | Max bullets | Max lasers |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Stage 1 | 1..20979 | 5867 | 3 | 0 | 0.00 | 0.00/1.00/0.00 | 1172 | 0 |
| Stage 2 | 20979..44709 | 7377 | 4 | 0 | 0.00 | 6.00/1.00/0.00 | 1147 | 0 |
| Stage 3 | 44709..72575 | 8234 | 6 | 0 | 3.00 | 7.00/0.00/0.00 | 947 | 200 |
| Stage 4A / Reimu | 72575..118404 | 11682 | 21 | 0 | 4.00 | 5.00/5.00/0.00 | 1393 | 0 |
| Stage 5 | 118404..163338 | 10833 | 17 | 0 | 8.00 | 10.00/0.00/0.00 | 1436 | 0 |
| Final B / Kaguya | 163339..229992 | 16884 | 23 | 0 | 5.00 | 5.00/6.00/0.00 | 1245 | 250 |

## Failure Taxonomy

| Primary class | Deaths | Interpretation |
| --- | ---: | --- |
| `modeled_committed_prefix_collision` | 44 | The measured three-frame input pipeline was already unsafe. |
| `observed_bullet_overlap` | 25 | A bullet overlaps the native player AABB in the hit observation. |
| `observed_enemy_body_overlap` | 2 | A captured lethal enemy-body AABB overlaps the player at action time. |
| `observed_laser_overlap` | 2 | The player overlaps an active laser's exact finite segment; TH08 checks this before the broad bullet pass. |
| `active_laser_without_observed_overlap` | 1 | At least one laser is active, but none of the persisted finite segments overlaps the player in the hit observation. |

Contributing factors:

- `playfield_boundary`: 52 deaths
- `fast_mode`: 50 deaths
- `corridor_deadline_miss`: 20 deaths
- `pool_density_over_1000`: 14 deaths
- `action_lag_over_model`: 1 deaths

## High-Risk Clusters

| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at hit |
| --- | --- | ---: | ---: | ---: | ---: |
| cluster-13 | Stage 4A / Reimu | 73877..75344 | 4 | 0.00 | 546 |
| cluster-20 | Stage 4A / Reimu | 94915..95848 | 3 | 2.00 | 798 |
| cluster-45 | Final B / Kaguya | 175710..176607 | 3 | 46.00 | 588 |
| cluster-57 | Final B / Kaguya | 213312..214167 | 3 | 0.00 | 482 |
| cluster-09 | Stage 3 | 46718..47098 | 2 | 5.00 | 491 |
| cluster-14 | Stage 4A / Reimu | 76548..76873 | 2 | 0.00 | 1081 |
| cluster-18 | Stage 4A / Reimu | 85322..85788 | 2 | 0.00 | 596 |
| cluster-22 | Stage 4A / Reimu | 104777..105313 | 2 | 1.00 | 1296 |

## Stage Detail

### Stage 1

- Death frames: 2022, 6800, 14412
- Cause counts: `{"observed_bullet_overlap": 2, "modeled_committed_prefix_collision": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 279/182.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 2022 | 3.00 | 5.00 | 0.00 | 222 | -3.31 | -2.23 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 6800 | 3.00 | 7.00 | 0.00 | 83 | -3.05 | 2.58 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 14412 | 3.00 | 4.00 | 0.00 | 453 | -0.96 | - | `observed_bullet_overlap` | - |

### Stage 2

- Death frames: 23386, 25724, 33535, 39097
- Cause counts: `{"modeled_committed_prefix_collision": 4}`
- Phase markers: observed 2, reachable static opcode `0x94` 3.
- Bottom/side occupancy decisions: 600/259.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 23386 | 3.00 | 11.00 | 0.00 | 159 | -3.05 | -8.89 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 25724 | 3.00 | 1.00 | 0.00 | 206 | -2.44 | -22.87 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 33535 | 3.00 | 3.00 | 0.00 | 451 | -2.60 | 7.47 | `modeled_committed_prefix_collision` | - |
| 39097 | 3.00 | 0.00 | 0.00 | 114 | -1.24 | 3.33 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |

### Stage 3

- Death frames: 45508, 46718, 47098, 60307, 69538, 70966
- Cause counts: `{"observed_bullet_overlap": 1, "modeled_committed_prefix_collision": 4, "active_laser_without_observed_overlap": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 687/308.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 45508 | 3.00 | 7.00 | 0.00 | 263 | 0.29 | -4.65 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss |
| 46718 | 3.00 | 15.00 | 0.00 | 491 | -2.13 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 47098 | 4.00 | 5.00 | 1.00 | 368 | -3.32 | 6.46 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 60307 | 4.00 | 31.00 | 1.00 | 224 | -10.86 | -7.05 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 69538 | 4.00 | 25.00 | 1.00 | 473 | -2.72 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 70966 | 3.00 | 10.00 | 0.00 | 261 | 4.17 | -3.27 | `active_laser_without_observed_overlap` | corridor_deadline_miss,action_lag_over_model |

### Stage 4A / Reimu

- Death frames: 73877, 74300, 74840, 75344, 76548, 76873, 81590, 83526, 84164, 85322, 85788, 86412, 94915, 95400, 95848, 103669, 104777, 105313, 112318, 113242, 117478
- Cause counts: `{"modeled_committed_prefix_collision": 12, "observed_bullet_overlap": 7, "observed_enemy_body_overlap": 2}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1100/717.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 73877 | 3.00 | 5.00 | 0.00 | 192 | -1.61 | 9.50 | `modeled_committed_prefix_collision` | playfield_boundary |
| 74300 | 4.00 | 1.00 | 1.00 | 474 | -2.45 | -2.29 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 74840 | 3.00 | 0.00 | 0.00 | 300 | -3.28 | -7.16 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 75344 | 3.00 | 0.00 | 0.00 | 546 | -3.43 | 11.61 | `modeled_committed_prefix_collision` | fast_mode |
| 76548 | 3.00 | 3.00 | 0.00 | 865 | -0.60 | -1.10 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 76873 | 3.00 | 0.00 | 0.00 | 1081 | -0.49 | 8.14 | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000 |
| 81590 | 3.00 | 3.00 | 0.00 | 138 | -12.13 | -0.17 | `observed_enemy_body_overlap` | corridor_deadline_miss,fast_mode |
| 83526 | 3.00 | 1.00 | 0.00 | 173 | -8.81 | 3.03 | `observed_enemy_body_overlap` | playfield_boundary |
| 84164 | 3.00 | 2.00 | 0.00 | 536 | -1.46 | 0.17 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 85322 | 3.00 | 0.00 | 0.00 | 595 | -1.46 | 5.92 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 85788 | 3.00 | 0.00 | 0.00 | 596 | -1.39 | -0.93 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 86412 | 3.00 | 2.00 | 0.00 | 633 | -3.43 | -6.50 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 94915 | 3.00 | 5.00 | 0.00 | 622 | -2.32 | - | `observed_bullet_overlap` | playfield_boundary |
| 95400 | 3.00 | 2.00 | 0.00 | 790 | 0.04 | - | `observed_bullet_overlap` | - |
| 95848 | 4.00 | 3.00 | 1.00 | 798 | -1.83 | 14.96 | `modeled_committed_prefix_collision` | - |
| 103669 | 3.00 | 1.00 | 0.00 | 1243 | -0.66 | - | `observed_bullet_overlap` | pool_density_over_1000,fast_mode |
| 104777 | 4.00 | 1.00 | 1.00 | 1093 | -1.42 | - | `modeled_committed_prefix_collision` | pool_density_over_1000,fast_mode |
| 105313 | 4.00 | 1.00 | 1.00 | 1296 | -2.72 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 112318 | 3.00 | 1.00 | 0.00 | 694 | -1.44 | 4.28 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 113242 | 3.00 | 3.00 | 0.00 | 677 | -2.78 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 117478 | 3.00 | 20.00 | 0.00 | 1329 | 2.05 | 9.13 | `observed_bullet_overlap` | pool_density_over_1000,fast_mode |

### Stage 5

- Death frames: 120209, 130745, 131416, 132912, 141970, 142851, 148140, 150001, 151250, 154062, 155490, 156507, 157910, 158654, 159403, 161773, 162473
- Cause counts: `{"modeled_committed_prefix_collision": 11, "observed_bullet_overlap": 6}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1632/675.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 120209 | 3.00 | 10.00 | 0.00 | 589 | -3.22 | 1.15 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 130745 | 3.00 | 6.00 | 0.00 | 366 | 0.11 | -11.45 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 131416 | 4.00 | 0.00 | 1.00 | 301 | -2.92 | 4.58 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 132912 | 4.00 | 1.00 | 1.00 | 524 | -31.43 | 10.15 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 141970 | 6.00 | 21.00 | 3.00 | 1052 | -1.20 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 142851 | 4.00 | 14.00 | 1.00 | 946 | -2.41 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 148140 | 3.00 | 3.00 | 0.00 | 1036 | -0.23 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 150001 | 3.00 | 1.00 | 0.00 | 1004 | -10.46 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000 |
| 151250 | 4.00 | 1.00 | 1.00 | 1001 | -6.33 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 154062 | 4.00 | 11.00 | 1.00 | 381 | -1.87 | - | `observed_bullet_overlap` | playfield_boundary |
| 155490 | 3.00 | 8.00 | 0.00 | 432 | -1.53 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 156507 | 3.00 | 10.00 | 0.00 | 474 | -0.89 | - | `observed_bullet_overlap` | fast_mode |
| 157910 | 3.00 | 2.00 | 0.00 | 365 | 2.73 | 2.82 | `observed_bullet_overlap` | fast_mode |
| 158654 | 3.00 | 1.00 | 0.00 | 337 | -1.40 | -2.76 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 159403 | 3.00 | 9.00 | 0.00 | 337 | -1.45 | -4.73 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 161773 | 3.00 | 4.00 | 0.00 | 1177 | -0.77 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 162473 | 3.00 | 9.00 | 0.00 | 1145 | 0.15 | - | `observed_bullet_overlap` | pool_density_over_1000 |

### Final B / Kaguya

- Death frames: 166752, 175052, 175710, 176232, 176607, 177240, 182567, 183607, 184544, 186454, 187205, 194546, 200740, 201834, 203197, 206012, 213312, 213670, 214167, 219289, 222030, 222798, 227050
- Cause counts: `{"modeled_committed_prefix_collision": 12, "observed_bullet_overlap": 9, "observed_laser_overlap": 2}`
- Phase markers: observed 11, reachable static opcode `0x94` 14.
- Bottom/side occupancy decisions: 1657/1067.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 166752 | 3.00 | 31.00 | 0.00 | 457 | -1.44 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 175052 | 4.00 | 92.00 | 1.00 | 564 | -1.91 | 1.36 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 175710 | 3.00 | 77.00 | 0.00 | 588 | -3.11 | -8.47 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 176232 | 4.00 | 62.00 | 1.00 | 370 | -28.86 | - | `modeled_committed_prefix_collision` | - |
| 176607 | 3.00 | 46.00 | 0.00 | 548 | -12.43 | 9.92 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 177240 | 3.00 | 30.00 | 0.00 | 790 | -2.77 | -18.82 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 182567 | 3.00 | 19.00 | 0.00 | 1122 | -1.80 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 183607 | 4.00 | 3.00 | 1.00 | 1194 | -1.45 | 6.71 | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 184544 | 4.00 | 2.00 | 1.00 | 1169 | 0.14 | 8.15 | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 186454 | 3.00 | 2.00 | 0.00 | 102 | -2.58 | 1.43 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 187205 | 4.00 | 9.00 | 1.00 | 117 | 0.26 | 3.16 | `observed_bullet_overlap` | playfield_boundary |
| 194546 | 3.00 | 1.00 | 0.00 | 245 | -2.24 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 200740 | 3.00 | 2.00 | 0.00 | 716 | -3.48 | 5.30 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 201834 | 3.00 | 1.00 | 0.00 | 706 | -3.89 | -10.09 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 203197 | 3.00 | 1.00 | 0.00 | 625 | 0.05 | 8.01 | `observed_bullet_overlap` | fast_mode |
| 206012 | 3.00 | 0.00 | 0.00 | 526 | -1.48 | -13.93 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 213312 | 3.00 | 1.00 | 0.00 | 341 | -0.03 | 3.06 | `observed_bullet_overlap` | - |
| 213670 | 3.00 | 0.00 | 0.00 | 218 | -1.83 | -0.49 | `observed_laser_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 214167 | 3.00 | 0.00 | 0.00 | 482 | -2.90 | 7.24 | `observed_laser_overlap` | fast_mode |
| 219289 | 3.00 | 3.00 | 0.00 | 336 | -5.63 | 5.76 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 222030 | 3.00 | 2.00 | 0.00 | 577 | -0.66 | 13.17 | `observed_bullet_overlap` | playfield_boundary |
| 222798 | 3.00 | 9.00 | 0.00 | 563 | -2.48 | 11.02 | `modeled_committed_prefix_collision` | playfield_boundary |
| 227050 | 3.00 | 6.00 | 0.00 | 879 | -2.26 | 13.84 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |

## Spell Inventory And Runtime Coverage

Every spell below is statically reachable for route 2 Lunatic Final B. Observed decisions count only rows whose live spell state reported that active spell ID. Zero decisions therefore means the run did not enter that spell; zero hits with nonzero decisions means it entered cleanly. `unresolved` means the trace schema did not persist enough live spell state.

### Stage 1

- ECL: `ecldata1.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | 蛍符「地上の彗星」 | リグル・ナイトバグ | 3 | 6 | 0 | yes | 794 | 0 |
| 5 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 11 | 6 | 0 | yes | 709 | 1 |
| 9 | 蠢符「ナイトバグトルネード」 | リグル・ナイトバグ | 13 | 27 | 0 | yes | 817 | 0 |
| 12 | 隠蟲「永夜蟄居」 | リグル・ナイトバグ | 12 | 27 | 0 | no | 0 | 0 |

### Stage 2

- ECL: `ecldata2.ecl`
- Observed/expected phase-counter markers: 2/3.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 16 | 声符「木菟咆哮」 | ミスティア・ローレライ | 4 | 7 | 0 | yes | 660 | 0 |
| 20 | 猛毒「毒蛾の暗闇演舞」 | ミスティア・ローレライ | 5 | 7 | 0 | yes | 822 | 0 |
| 24 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 6 | 8 | 0 | yes | 818 | 0 |
| 28 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 8 | 9 | 0 | yes | 821 | 0 |
| 31 | 夜雀「真夜中のコーラスマスター」 | ミスティア・ローレライ | 3 | 7 | 0 | no | 0 | 0 |

### Stage 3

- ECL: `ecldata3.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 35 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 3 | 0 | 0 | yes | 853 | 0 |
| 38 | 始符「エフェメラリティ137」 | 上白沢慧音 | 2 | 2 | 0 | yes | 757 | 1 |
| 42 | 野符「GHQクライシス」 | 上白沢慧音 | 3 | 3 | 0 | yes | 734 | 0 |
| 46 | 国体「三種の神器　郷」 | 上白沢慧音 | 3 | 0 | 0 | yes | 877 | 1 |
| 50 | 虚史「幻想郷伝説」 | 上白沢慧音 | 1 | 0 | 1 | yes | 611 | 1 |
| 53 | 未来「高天原」 | 上白沢慧音 | 1 | 0 | 1 | no | 0 | 0 |

### Stage 4A / Reimu

- ECL: `ecldata4a.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 57 | 夢境「二重大結界」 | 博麗霊夢 | 3 | 0 | 0 | yes | 1068 | 4 |
| 61 | 散霊「夢想封印　寂」 | 博麗霊夢 | 3 | 0 | 0 | yes | 1010 | 0 |
| 65 | 神技「八方龍殺陣」 | 博麗霊夢 | 7 | 27 | 0 | yes | 863 | 3 |
| 69 | 回霊「夢想封印　侘」 | 博麗霊夢 | 2 | 17 | 0 | yes | 1066 | 2 |
| 73 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 5 | 4 | 0 | yes | 922 | 1 |
| 76 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 2 | 5 | 0 | no | 0 | 0 |

### Stage 5

- ECL: `ecldata5.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 103 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 6 | 0 | 0 | yes | 838 | 2 |
| 111 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 3 | 0 | 0 | yes | 1039 | 3 |
| 107 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 3 | 3 | 0 | yes | 783 | 2 |
| 115 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 6 | 3 | 0 | yes | 1003 | 2 |
| 118 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 4 | 2 | 0 | no | 0 | 0 |

### Final B / Kaguya

- ECL: `ecldata7.ecl`
- Observed/expected phase-counter markers: 11/14.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 150 | 薬符「壺中の大銀河」 | 八意永琳 | 4 | 0 | 0 | yes | 911 | 5 |
| 154 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 5 | 1 | 5 | yes | 907 | 2 |
| 158 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 4 | 4 | 2 | yes | 1706 | 1 |
| 162 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 4 | 8 | 2 | yes | 1277 | 1 |
| 166 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 3 | 2 | 2 | yes | 1502 | 3 |
| 170 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 26 | 3 | 0 | yes | 1957 | 3 |
| 174 | 「永夜返し  -待宵-」 | 蓬莱山輝夜 | 3 | 1 | 0 | yes | 299 | 1 |
| 178 | 「永夜返し  -子の四つ-」 | 蓬莱山輝夜 | 3 | 2 | 0 | yes | 311 | 0 |
| 182 | 「永夜返し  -丑の四つ-」 | 蓬莱山輝夜 | 2 | 2 | 0 | no | 0 | 0 |
| 186 | 「永夜返し  -寅の四つ-」 | 蓬莱山輝夜 | 4 | 4 | 0 | no | 0 | 0 |
| 190 | 「永夜返し  -世明け-」 | 蓬莱山輝夜 | 12 | 5 | 0 | no | 0 | 0 |

## Runtime And Harness Findings

- Observed auto-Z stall frames: none.
- Route termination: `route_complete` at completion probe frame 229992.
- Unique robust solutions observed: 9768; solve time median/p95/max 104.75/345.87/526.42 ms.
- First-observed policy age median/p95/max: 3.00/7.00/1811.00 frames.
- Viability queries available: 60167/60167; robustly constrained decisions: 28695/60877.
- Robust-policy decisions without any usable query: 315/60482.
- Global-horizon/local-prefix cross-tab: 44030 decisions; winning global state with unsafe selected prefix: 6; losing global state with safe short prefix: 22494; selected globally certified action contradicted by the fresh local prefix checker: 2; selected action outside the reported winning set: 292.
- Live spell attribution was recorded at every hit edge; exact per-spell counts are preserved below.
- `0` hit edges remain in the `sensor_gap_or_unmodeled_hazard` class and require executor-level same-frame emission/transform evidence.

## Next Regression Work

1. Keep robust backward-reachability solves within the finite policy horizon, then verify nonzero live query and constrained-decision counts.
2. Replay all 74 retained witnesses through the integrated executor and preserve one regression per concrete failure.
3. Re-run focused Stage 4A and Final B practices before another full Lunatic route; compare hit frames, policy age, action-set exhaustion, and cluster recurrence.
4. Add item/Power state and finite Bomb resources only after the no-Bomb movement policy has passed physical validation.

## Retained Causal Disposition

- **Observed:** This was the original Game Start path from Power 0, not a
  max-Power practice. It completed all six route stages, produced 60,877
  decisions and 74 native hit edges, emitted no Bomb action/mask, had no
  foreground interruption or JSON decode error, and terminated normally at
  frame 229,992. The first fresh-attempt hit is Stage-1 nonspell frame 2,022.
- **Observed:** Stage hit counts are `3/4/6/21/17/23` for
  Stage 1/2/3/4A/5/Final B. Stage 4A is the largest single-stage failure.
  Final B and Stage 5 are the next largest; this ordering, not one isolated
  spell, defines the current physical workload priority.
- **Observed:** The model already reported a committed-prefix collision for
  44/74 contacts. There were also 25 exact bullet, two exact laser, and two
  exact enemy-body overlap witnesses. The dominant failure is therefore not
  explained by one missing collision sensor alone. Empty robust action sets
  occurred in 1,636/3,840/4,949/5,062/7,163/8,135 stage decisions.
- **Observed:** The no-life-decrement patch makes later lives/Bomb/Power
  histories contaminated after the first hit. Entry Power was
  `0/6/7/5/10/5`; these values describe this failed continuation, not an NMNB
  resource route. Stage 1 reached only Power 7 and ended at Power 1, so
  collection and nonspell combat progress remain material route constraints.
- **Observed:** The C5 observer never saw a quarter-scale root or accepted an
  exact source. Final B entered spells 174 and 178 for 299 and 311 decisions,
  respectively, but never entered spells 182, 186, or 190. The strict C5
  report correctly has zero authority rows and fails while the stage and
  route evidence remain complete.
- **Inferred:** Route completion is not sufficient to prove that one failed
  full-route history exercises the complete statically reachable Final-B
  spell inventory. The exact native resource/time branch that omitted
  182/186/190 is not established by this run and remains an explicit
  hypothesis.
- **Observed:** No new native replay was created. The ignored raw trace is
  2,009,399,974 bytes with SHA-256
  `ffe52f97e959a92ec0adb06e418c17e2a97c8e2209f0978a1249f1b66e8a69d0`.
  The strict C5 report SHA-256 is
  `47337406a0aaa4ff6a819b2614f94907613b951d44ae058bf3472634517fe7d8`.
- **Authority:** This is accepted physical whole-route/no-Bomb evidence and a
  C5 target-reachability counterexample. It is not a C5 delivery pass,
  stage-survival promotion, clean resource route, or Lunatic NMNB result.
