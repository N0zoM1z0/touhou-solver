# TH08 Lunatic Full-Run Review: lunatic_route2_fullrun_unattended_20260730_222529

## Result

- Route: Sakuya/Remilia, Lunatic, Final B / Kaguya.
- Combat completion: yes; gameplay scene unloaded at frame 239827.
- Native phase-2 hit edges, including Last-Spell-saveable edges: 68.
- Deathbomb requests at those edges: 0.
- Hard no-Bomb input verification: passed across 64850 decisions.
- Post-hit Bomb-stock decreases: 11.00; this is respawn-stock reset telemetry, not evidence of Bomb input.
- Agent decisions: 64850.
- Raw trace size: 2221733409 bytes across 1 segments.
- JSON decode errors: 0.
- Exact spell-level hit attribution: available from live `g_spell_card_state`.

The run is valid for stage-, death-, resource-, projectile-, latency-, and route-level analysis. Spell names below are the statically reachable Lunatic route inventory; unavailable runtime hit counts remain explicitly unresolved instead of guessed. The no-life patch allows post-hit resource resets to repeat, so resource-stock changes must not be interpreted as Bomb commands.

Replay retention: **NOT ACCEPTED**. Final-B terminal unload occurred before
the long ending/result sequence created a live dynamic `ResultSysInf`.
Immediate replay-save resolution failed closed before menu input; no replay
was written. CE-0215 retains the boundary. The user accepted this run only as
the 68-hit stage-attributed baseline and waived a replay rerun.

## Trace Integrity

| Segment | Frames | Decisions | Wall Z | Termination | Runtime error | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 1..239827 | 64850 | 430 | route_complete | - | `a2ca77291996c4e390c8e403cd78e61edd43cbb1edb8fc27d8d8116ed8dcaada` |

The route is one continuous agent-controlled trace with no foreground interruption or manual re-arm gap.

## Stage Summary

| Stage | Frames | Decisions | Native hits | Deathbombs | Post-hit Bomb-stock decrease | Power start/end/min | Max bullets | Max lasers |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Stage 1 | 1..20950 | 6263 | 2 | 0 | 0.00 | 0.00/32.00/0.00 | 1176 | 0 |
| Stage 2 | 20950..44342 | 7573 | 3 | 0 | 1.00 | 37.00/26.00/26.00 | 1199 | 0 |
| Stage 3 | 44342..72150 | 8715 | 5 | 0 | 2.00 | 32.00/20.00/4.00 | 815 | 200 |
| Stage 4A / Reimu | 72150..117838 | 12015 | 20 | 0 | 5.00 | 25.00/3.00/0.00 | 1360 | 0 |
| Stage 5 | 117838..163122 | 11250 | 15 | 0 | 2.00 | 8.00/0.00/0.00 | 1522 | 0 |
| Final B / Kaguya | 163123..239827 | 19034 | 23 | 0 | 1.00 | 5.00/13.00/0.00 | 1536 | 235 |

## Failure Taxonomy

| Primary class | Deaths | Interpretation |
| --- | ---: | --- |
| `modeled_committed_prefix_collision` | 38 | The measured three-frame input pipeline was already unsafe. |
| `observed_bullet_overlap` | 28 | A bullet overlaps the native player AABB in the hit observation. |
| `observed_enemy_body_overlap` | 1 | A captured lethal enemy-body AABB overlaps the player at action time. |
| `observed_multiple_hazard_overlap` | 1 | More than one captured native hazard family overlaps at the hit edge; the trace does not invent a single causal winner. |

Contributing factors:

- `playfield_boundary`: 54 deaths
- `fast_mode`: 44 deaths
- `pool_density_over_1000`: 16 deaths
- `corridor_deadline_miss`: 15 deaths
- `action_lag_over_model`: 2 deaths

## High-Risk Clusters

| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at hit |
| --- | --- | ---: | ---: | ---: | ---: |
| cluster-15 | Stage 4A / Reimu | 84156..85087 | 3 | 0.00 | 619 |
| cluster-19 | Stage 4A / Reimu | 103357..104230 | 3 | 0.00 | 1250 |
| cluster-53 | Final B / Kaguya | 220003..221024 | 3 | 1.00 | 585 |
| cluster-06 | Stage 3 | 46623..46929 | 2 | 34.00 | 339 |
| cluster-38 | Stage 5 | 160931..161524 | 2 | 7.00 | 1169 |
| cluster-42 | Final B / Kaguya | 175715..176287 | 2 | 55.00 | 668 |
| cluster-43 | Final B / Kaguya | 181909..182367 | 2 | 36.00 | 1141 |
| cluster-44 | Final B / Kaguya | 183203..183724 | 2 | 13.00 | 1102 |

## Stage Detail

### Stage 1

- Death frames: 1692, 7374
- Cause counts: `{"observed_bullet_overlap": 1, "modeled_committed_prefix_collision": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 128/91.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1692 | 3.00 | 0.00 | 0.00 | 214 | 1.06 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 7374 | 3.00 | 33.00 | 0.00 | 150 | -1.92 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |

### Stage 2

- Death frames: 22025, 25994, 39081
- Cause counts: `{"modeled_committed_prefix_collision": 2, "observed_bullet_overlap": 1}`
- Phase markers: observed 2, reachable static opcode `0x94` 3.
- Bottom/side occupancy decisions: 342/123.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 22025 | 4.00 | 45.00 | 1.00 | 164 | -2.51 | -1.89 | `modeled_committed_prefix_collision` | corridor_deadline_miss |
| 25994 | 3.00 | 54.00 | 0.00 | 213 | -2.83 | -4.43 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 39081 | 3.00 | 42.00 | 0.00 | 760 | -1.48 | -3.00 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |

### Stage 3

- Death frames: 46623, 46929, 47999, 52475, 70536
- Cause counts: `{"observed_bullet_overlap": 2, "modeled_committed_prefix_collision": 3}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 450/294.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 46623 | 3.00 | 34.00 | 0.00 | 339 | 1.46 | 2.20 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 46929 | 4.00 | 45.00 | 1.00 | 329 | -1.74 | -12.30 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 47999 | 3.00 | 29.00 | 0.00 | 471 | 1.03 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 52475 | 3.00 | 20.00 | 0.00 | 721 | -2.58 | 12.08 | `modeled_committed_prefix_collision` | playfield_boundary |
| 70536 | 4.00 | 35.00 | 1.00 | 254 | -4.10 | 8.76 | `modeled_committed_prefix_collision` | action_lag_over_model |

### Stage 4A / Reimu

- Death frames: 73867, 74902, 76459, 82142, 83094, 84156, 84686, 85087, 85734, 95429, 101654, 103357, 103783, 104230, 107522, 108337, 111172, 111804, 116182, 117120
- Cause counts: `{"modeled_committed_prefix_collision": 12, "observed_bullet_overlap": 7, "observed_enemy_body_overlap": 1}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 764/551.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 73867 | 3.00 | 35.00 | 0.00 | 535 | -2.66 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 74902 | 3.00 | 27.00 | 0.00 | 544 | -2.91 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 76459 | 4.00 | 16.00 | 1.00 | 1149 | -1.35 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000 |
| 82142 | 3.00 | 7.00 | 0.00 | 147 | -1.82 | 11.12 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 83094 | 3.00 | 1.00 | 0.00 | 196 | -15.54 | - | `observed_enemy_body_overlap` | playfield_boundary,fast_mode |
| 84156 | 3.00 | 9.00 | 0.00 | 619 | -1.39 | 5.72 | `modeled_committed_prefix_collision` | playfield_boundary |
| 84686 | 3.00 | 9.00 | 0.00 | 581 | -1.80 | 1.28 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 85087 | 3.00 | 0.00 | 0.00 | 597 | 0.01 | -1.43 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 85734 | 3.00 | 1.00 | 0.00 | 614 | -1.46 | -0.84 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 95429 | 3.00 | 6.00 | 0.00 | 813 | -3.31 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 101654 | 3.00 | 3.00 | 0.00 | 152 | -1.35 | 0.50 | `modeled_committed_prefix_collision` | playfield_boundary |
| 103357 | 4.00 | 2.00 | 1.00 | 1250 | -2.36 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000 |
| 103783 | 3.00 | 0.00 | 0.00 | 1073 | -3.45 | 1.36 | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000 |
| 104230 | 4.00 | 0.00 | 1.00 | 1242 | -1.29 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000 |
| 107522 | 3.00 | 3.00 | 0.00 | 109 | 4.94 | 5.73 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 108337 | 4.00 | 1.00 | 1.00 | 142 | -2.42 | -14.71 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 111172 | 3.00 | 0.00 | 0.00 | 567 | -4.07 | 10.23 | `observed_bullet_overlap` | playfield_boundary |
| 111804 | 3.00 | 0.00 | 0.00 | 697 | -2.14 | -3.96 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 116182 | 4.00 | 13.00 | 1.00 | 1292 | 2.01 | 6.40 | `observed_bullet_overlap` | pool_density_over_1000 |
| 117120 | 3.00 | 1.00 | 0.00 | 1323 | -3.25 | - | `observed_bullet_overlap` | pool_density_over_1000,fast_mode |

### Stage 5

- Death frames: 119795, 121999, 130397, 131046, 131922, 141038, 141643, 149907, 151518, 156389, 157712, 159519, 160931, 161524, 162587
- Cause counts: `{"modeled_committed_prefix_collision": 11, "observed_bullet_overlap": 4}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1576/497.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 119795 | 3.00 | 10.00 | 0.00 | 608 | -1.64 | 13.99 | `modeled_committed_prefix_collision` | fast_mode |
| 121999 | 3.00 | 7.00 | 0.00 | 582 | -19.82 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 130397 | 3.00 | 2.00 | 0.00 | 311 | -2.32 | - | `observed_bullet_overlap` | - |
| 131046 | 3.00 | 0.00 | 0.00 | 62 | -1.02 | -22.57 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 131922 | 3.00 | 0.00 | 0.00 | 599 | -5.10 | - | `observed_bullet_overlap` | playfield_boundary |
| 141038 | 5.00 | 12.00 | 2.00 | 1264 | -3.07 | - | `modeled_committed_prefix_collision` | action_lag_over_model,pool_density_over_1000,fast_mode |
| 141643 | 3.00 | 0.00 | 0.00 | 858 | -2.98 | 0.78 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 149907 | 3.00 | 2.00 | 0.00 | 1016 | -5.94 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 151518 | 3.00 | 0.00 | 0.00 | 1012 | -5.06 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 156389 | 3.00 | 2.00 | 0.00 | 398 | -3.43 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 157712 | 3.00 | 8.00 | 0.00 | 347 | -1.91 | -2.56 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 159519 | 3.00 | 0.00 | 0.00 | 346 | -2.04 | 0.24 | `modeled_committed_prefix_collision` | fast_mode |
| 160931 | 3.00 | 21.00 | 0.00 | 1169 | -1.92 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 161524 | 3.00 | 7.00 | 0.00 | 1094 | -1.82 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 162587 | 3.00 | 0.00 | 0.00 | 957 | -5.52 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |

### Final B / Kaguya

- Death frames: 170557, 171547, 175715, 176287, 181909, 182367, 183203, 183724, 184723, 187412, 194645, 196135, 200254, 201611, 213980, 215608, 220003, 220518, 221024, 221881, 222707, 223534, 226562
- Cause counts: `{"modeled_committed_prefix_collision": 9, "observed_bullet_overlap": 13, "observed_multiple_hazard_overlap": 1}`
- Phase markers: observed 14, reachable static opcode `0x94` 14.
- Bottom/side occupancy decisions: 1345/1149.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 170557 | 3.00 | 101.00 | 0.00 | 614 | -6.47 | 16.92 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 171547 | 3.00 | 85.00 | 0.00 | 702 | -1.53 | 5.81 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 175715 | 3.00 | 71.00 | 0.00 | 668 | 0.55 | 13.01 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 176287 | 3.00 | 55.00 | 0.00 | 367 | -3.70 | 9.54 | `observed_bullet_overlap` | fast_mode |
| 181909 | 3.00 | 52.00 | 0.00 | 1141 | 1.70 | -1.68 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 182367 | 3.00 | 36.00 | 0.00 | 1095 | -1.85 | -15.61 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,pool_density_over_1000,fast_mode |
| 183203 | 3.00 | 20.00 | 0.00 | 1058 | -1.74 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 183724 | 3.00 | 13.00 | 0.00 | 1102 | -0.29 | 0.63 | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000,fast_mode |
| 184723 | 3.00 | 1.00 | 0.00 | 1071 | -1.78 | 9.59 | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 187412 | 3.00 | 8.00 | 0.00 | 96 | -3.20 | 1.88 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 194645 | 3.00 | 0.00 | 0.00 | 242 | -1.94 | 14.50 | `modeled_committed_prefix_collision` | playfield_boundary |
| 196135 | 3.00 | 0.00 | 0.00 | 252 | -2.12 | 16.00 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 200254 | 4.00 | 9.00 | 1.00 | 684 | -1.75 | -10.18 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 201611 | 3.00 | 1.00 | 0.00 | 653 | -2.13 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 213980 | 3.00 | 1.00 | 0.00 | 288 | -1.85 | 5.42 | `observed_multiple_hazard_overlap` | playfield_boundary,fast_mode |
| 215608 | 3.00 | 0.00 | 0.00 | 446 | -2.85 | -19.76 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 220003 | 3.00 | 3.00 | 0.00 | 585 | 0.33 | 10.21 | `observed_bullet_overlap` | fast_mode |
| 220518 | 3.00 | 9.00 | 0.00 | 561 | -0.73 | 2.43 | `observed_bullet_overlap` | playfield_boundary |
| 221024 | 3.00 | 1.00 | 0.00 | 567 | 0.19 | -1.97 | `observed_bullet_overlap` | corridor_deadline_miss |
| 221881 | 3.00 | 2.00 | 0.00 | 582 | -1.90 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 222707 | 3.00 | 0.00 | 0.00 | 549 | -1.28 | - | `observed_bullet_overlap` | playfield_boundary |
| 223534 | 3.00 | 9.00 | 0.00 | 566 | -3.38 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 226562 | 3.00 | 13.00 | 0.00 | 908 | -0.15 | 15.92 | `observed_bullet_overlap` | playfield_boundary,fast_mode |

## Spell Inventory And Runtime Coverage

Every spell below is statically reachable for route 2 Lunatic Final B. Observed decisions count only rows whose live spell state reported that active spell ID. Zero decisions therefore means the run did not enter that spell; zero hits with nonzero decisions means it entered cleanly. `unresolved` means the trace schema did not persist enough live spell state.

### Stage 1

- ECL: `ecldata1.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | 蛍符「地上の彗星」 | リグル・ナイトバグ | 3 | 6 | 0 | yes | 864 | 0 |
| 5 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 11 | 6 | 0 | yes | 736 | 0 |
| 9 | 蠢符「ナイトバグトルネード」 | リグル・ナイトバグ | 13 | 27 | 0 | yes | 867 | 0 |
| 12 | 隠蟲「永夜蟄居」 | リグル・ナイトバグ | 12 | 27 | 0 | no | 0 | 0 |

### Stage 2

- ECL: `ecldata2.ecl`
- Observed/expected phase-counter markers: 2/3.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 16 | 声符「木菟咆哮」 | ミスティア・ローレライ | 4 | 7 | 0 | yes | 675 | 0 |
| 20 | 猛毒「毒蛾の暗闇演舞」 | ミスティア・ローレライ | 5 | 7 | 0 | yes | 869 | 0 |
| 24 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 6 | 8 | 0 | yes | 860 | 0 |
| 28 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 8 | 9 | 0 | yes | 828 | 0 |
| 31 | 夜雀「真夜中のコーラスマスター」 | ミスティア・ローレライ | 3 | 7 | 0 | no | 0 | 0 |

### Stage 3

- ECL: `ecldata3.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 35 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 3 | 0 | 0 | yes | 902 | 0 |
| 38 | 始符「エフェメラリティ137」 | 上白沢慧音 | 2 | 2 | 0 | yes | 792 | 0 |
| 42 | 野符「GHQクライシス」 | 上白沢慧音 | 3 | 3 | 0 | yes | 780 | 0 |
| 46 | 国体「三種の神器　郷」 | 上白沢慧音 | 3 | 0 | 0 | yes | 895 | 0 |
| 50 | 虚史「幻想郷伝説」 | 上白沢慧音 | 1 | 0 | 1 | yes | 671 | 1 |
| 53 | 未来「高天原」 | 上白沢慧音 | 1 | 0 | 1 | no | 0 | 0 |

### Stage 4A / Reimu

- ECL: `ecldata4a.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 57 | 夢境「二重大結界」 | 博麗霊夢 | 3 | 0 | 0 | yes | 1107 | 4 |
| 61 | 散霊「夢想封印　寂」 | 博麗霊夢 | 3 | 0 | 0 | yes | 1037 | 0 |
| 65 | 神技「八方龍殺陣」 | 博麗霊夢 | 7 | 27 | 0 | yes | 853 | 3 |
| 69 | 回霊「夢想封印　侘」 | 博麗霊夢 | 2 | 17 | 0 | yes | 1089 | 2 |
| 73 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 5 | 4 | 0 | yes | 967 | 2 |
| 76 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 2 | 5 | 0 | no | 0 | 0 |

### Stage 5

- ECL: `ecldata5.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 103 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 6 | 0 | 0 | yes | 864 | 2 |
| 111 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 3 | 0 | 0 | yes | 1075 | 2 |
| 107 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 3 | 3 | 0 | yes | 972 | 2 |
| 115 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 6 | 3 | 0 | yes | 1092 | 3 |
| 118 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 4 | 2 | 0 | no | 0 | 0 |

### Final B / Kaguya

- ECL: `ecldata7.ecl`
- Observed/expected phase-counter markers: 14/14.

| ID | Name | Owner | Emits | Transforms | Lasers | Observed | Decisions | Hits |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 150 | 薬符「壺中の大銀河」 | 八意永琳 | 4 | 0 | 0 | yes | 903 | 2 |
| 154 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 5 | 1 | 5 | yes | 909 | 1 |
| 158 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 4 | 4 | 2 | yes | 1793 | 2 |
| 162 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 4 | 8 | 2 | yes | 1313 | 0 |
| 166 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 3 | 2 | 2 | yes | 1538 | 2 |
| 170 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 26 | 3 | 0 | yes | 2027 | 6 |
| 174 | 「永夜返し  -待宵-」 | 蓬莱山輝夜 | 3 | 1 | 0 | yes | 265 | 1 |
| 178 | 「永夜返し  -子の四つ-」 | 蓬莱山輝夜 | 3 | 2 | 0 | yes | 423 | 0 |
| 182 | 「永夜返し  -丑の四つ-」 | 蓬莱山輝夜 | 2 | 2 | 0 | yes | 470 | 0 |
| 186 | 「永夜返し  -寅の四つ-」 | 蓬莱山輝夜 | 4 | 4 | 0 | yes | 364 | 0 |
| 190 | 「永夜返し  -世明け-」 | 蓬莱山輝夜 | 12 | 5 | 0 | yes | 707 | 0 |

## Runtime And Harness Findings

- Observed auto-Z stall frames: none.
- Route termination: `route_complete` at completion probe frame 239827.
- Unique robust solutions observed: 10148; solve time median/p95/max 92.00/317.48/450.39 ms.
- First-observed policy age median/p95/max: 3.00/6.00/1806.00 frames.
- Viability queries available: 64085/64085; robustly constrained decisions: 29738/64850.
- Robust-policy decisions without any usable query: 316/64401.
- Global-horizon/local-prefix cross-tab: 44018 decisions; winning global state with unsafe selected prefix: 2; losing global state with safe short prefix: 23160; selected globally certified action contradicted by the fresh local prefix checker: 1; selected action outside the reported winning set: 201.
- Live spell attribution was recorded at every hit edge; exact per-spell counts are preserved below.
- `0` hit edges remain in the `sensor_gap_or_unmodeled_hazard` class and require executor-level same-frame emission/transform evidence.

## Next Regression Work

1. Keep robust backward-reachability solves within the finite policy horizon, then verify nonzero live query and constrained-decision counts.
2. Replay all 68 retained witnesses through the integrated executor and preserve one regression per concrete failure.
3. Re-run focused Stage 4A and Final B practices before another full Lunatic route; compare hit frames, policy age, action-set exhaustion, and cluster recurrence.
4. Add item/Power state and finite Bomb resources only after the no-Bomb movement policy has passed physical validation.
