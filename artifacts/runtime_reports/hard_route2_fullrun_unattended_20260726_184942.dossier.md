# TH08 Hard Full-Run Review: hard_route2_fullrun_unattended_20260726_184942

## Result

- Route: Sakuya/Remilia, Hard, Final B / Kaguya.
- Combat completion: yes; gameplay scene unloaded at frame 228661.
- Native phase-2 hit edges, including Last-Spell-saveable edges: 39.
- Deathbomb requests at those edges: 0.
- Hard no-Bomb input verification: passed across 70699 decisions.
- Post-hit Bomb-stock decreases: 13.00; this is respawn-stock reset telemetry, not evidence of Bomb input.
- Agent decisions: 70699.
- Raw trace size: 1839043557 bytes across 1 segments.
- JSON decode errors: 0.
- Exact spell-level hit attribution: available from live `g_spell_card_state`.

The run is valid for stage-, death-, resource-, projectile-, latency-, and route-level analysis. Spell names below are the statically reachable Hard route inventory; unavailable runtime hit counts remain explicitly unresolved instead of guessed. The no-life patch allows post-hit resource resets to repeat, so resource-stock changes must not be interpreted as Bomb commands.

## Trace Integrity

| Segment | Frames | Decisions | Wall Z | Termination | Runtime error | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 1..228661 | 70699 | 411 | route_complete | - | `2ec3a10df72fbad493cf80014b37028c4b24b26f7f2c0e2866c67d8550e0cb83` |

The route is one continuous agent-controlled trace with no foreground interruption or manual re-arm gap.

## Stage Summary

| Stage | Frames | Decisions | Native hits | Deathbombs | Post-hit Bomb-stock decrease | Power start/end/min | Max bullets | Max lasers |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Stage 1 | 1..20979 | 7231 | 1 | 0 | 0.00 | 0.00/9.00/0.00 | 704 | 0 |
| Stage 2 | 20979..44074 | 8380 | 1 | 0 | 1.00 | 14.00/26.00/14.00 | 828 | 0 |
| Stage 3 | 44074..71940 | 9394 | 8 | 0 | 3.00 | 32.00/8.00/0.00 | 771 | 220 |
| Stage 4A / Reimu | 71940..117482 | 12839 | 11 | 0 | 2.00 | 13.00/0.00/0.00 | 1079 | 0 |
| Stage 5 | 117482..162852 | 13064 | 9 | 0 | 7.00 | 18.00/22.00/0.00 | 1231 | 0 |
| Final B / Kaguya | 162853..228661 | 19791 | 9 | 0 | 0.00 | 27.00/23.00/16.00 | 1206 | 256 |

## Failure Taxonomy

| Primary class | Deaths | Interpretation |
| --- | ---: | --- |
| `modeled_committed_prefix_collision` | 23 | The measured three-frame input pipeline was already unsafe. |
| `observed_bullet_overlap` | 14 | A bullet overlaps the native player AABB in the hit observation. |
| `observed_enemy_body_overlap` | 1 | A captured lethal enemy-body AABB overlaps the player at action time. |
| `sensor_gap_or_unmodeled_hazard` | 1 | No observed overlap and positive pipeline clearance; same-frame ECL emission, transform error, or another unmodeled hazard is the leading explanation. |

Contributing factors:

- `playfield_boundary`: 30 deaths
- `fast_mode`: 29 deaths
- `corridor_deadline_miss`: 13 deaths
- `pool_density_over_1000`: 4 deaths
- `action_lag_over_model`: 1 deaths
- `enemy_body_absent_from_action_snapshot`: 1 deaths

## High-Risk Clusters

| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at hit |
| --- | --- | ---: | ---: | ---: | ---: |
| cluster-24 | Stage 5 | 148867..149780 | 3 | 0.00 | 1022 |
| cluster-04 | Stage 3 | 46460..46801 | 2 | 6.00 | 259 |
| cluster-12 | Stage 4A / Reimu | 83796..84336 | 2 | 0.00 | 573 |
| cluster-23 | Stage 5 | 131641..132050 | 2 | 1.00 | 515 |

## Stage Detail

### Stage 1

- Death frames: 20606
- Cause counts: `{"observed_bullet_overlap": 1}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 238/269.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 20606 | 3.00 | 16.00 | 0.00 | 248 | 1.76 | 1.00 | `observed_bullet_overlap` | fast_mode |

### Stage 2

- Death frames: 39083
- Cause counts: `{"observed_bullet_overlap": 1}`
- Phase markers: observed 2, reachable static opcode `0x94` 3.
- Bottom/side occupancy decisions: 436/393.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 39083 | 4.00 | 32.00 | 1.00 | 81 | -2.68 | -4.04 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |

### Stage 3

- Death frames: 45769, 46460, 46801, 52333, 58392, 60131, 62008, 70394
- Cause counts: `{"observed_bullet_overlap": 3, "modeled_committed_prefix_collision": 5}`
- Phase markers: observed 3, reachable static opcode `0x94` 4.
- Bottom/side occupancy decisions: 663/531.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 45769 | 3.00 | 37.00 | 0.00 | 416 | -2.14 | - | `observed_bullet_overlap` | playfield_boundary |
| 46460 | 3.00 | 22.00 | 0.00 | 254 | -3.90 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 46801 | 3.00 | 6.00 | 0.00 | 259 | -3.55 | 10.06 | `modeled_committed_prefix_collision` | playfield_boundary |
| 52333 | 3.00 | 4.00 | 0.00 | 519 | -1.68 | 14.18 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 58392 | 5.00 | 17.00 | 2.00 | 330 | 3.41 | -9.20 | `observed_bullet_overlap` | corridor_deadline_miss,fast_mode |
| 60131 | 3.00 | 2.00 | 0.00 | 149 | 1.30 | 9.25 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 62008 | 4.00 | 2.00 | 1.00 | 527 | -1.41 | 8.46 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 70394 | 3.00 | 2.00 | 0.00 | 350 | -1.91 | -6.53 | `modeled_committed_prefix_collision` | corridor_deadline_miss,action_lag_over_model |

### Stage 4A / Reimu

- Death frames: 74492, 82904, 83796, 84336, 95259, 103082, 108187, 110013, 111688, 112489, 117256
- Cause counts: `{"modeled_committed_prefix_collision": 5, "sensor_gap_or_unmodeled_hazard": 1, "observed_bullet_overlap": 5}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 1162/892.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 74492 | 4.00 | 14.00 | 1.00 | 307 | -10.99 | -4.93 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 82904 | 3.00 | 21.00 | 0.00 | 106 | 1.74 | 5.63 | `sensor_gap_or_unmodeled_hazard` | fast_mode |
| 83796 | 3.00 | 8.00 | 0.00 | 573 | 0.47 | -1.87 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 84336 | 3.00 | 0.00 | 0.00 | 547 | -0.89 | 1.02 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 95259 | 3.00 | 6.00 | 0.00 | 351 | -11.95 | - | `modeled_committed_prefix_collision` | fast_mode |
| 103082 | 3.00 | 5.00 | 0.00 | 871 | 2.54 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 108187 | 3.00 | 2.00 | 0.00 | 92 | 1.15 | 5.90 | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 110013 | 3.00 | 1.00 | 0.00 | 189 | -3.45 | -7.00 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 111688 | 3.00 | 1.00 | 0.00 | 704 | 3.30 | - | `observed_bullet_overlap` | playfield_boundary,fast_mode |
| 112489 | 3.00 | 9.00 | 0.00 | 678 | -2.03 | -12.50 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 117256 | 4.00 | 15.00 | 1.00 | 1067 | -1.21 | -0.98 | `observed_bullet_overlap` | corridor_deadline_miss,pool_density_over_1000,fast_mode |

### Stage 5

- Death frames: 124692, 125616, 130265, 131641, 132050, 148867, 149337, 149780, 154179
- Cause counts: `{"modeled_committed_prefix_collision": 8, "observed_enemy_body_overlap": 1}`
- Phase markers: observed 7, reachable static opcode `0x94` 8.
- Bottom/side occupancy decisions: 2099/1152.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 124692 | 4.00 | 26.00 | 1.00 | 392 | -13.81 | 1.23 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 125616 | 3.00 | 10.00 | 0.00 | 344 | -13.16 | 3.52 | `observed_enemy_body_overlap` | fast_mode,enemy_body_absent_from_action_snapshot |
| 130265 | 4.00 | 10.00 | 1.00 | 220 | -2.26 | -13.49 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss |
| 131641 | 4.00 | 1.00 | 1.00 | 287 | -2.64 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 132050 | 3.00 | 1.00 | 0.00 | 515 | -2.70 | -1.65 | `modeled_committed_prefix_collision` | corridor_deadline_miss,fast_mode |
| 148867 | 6.00 | 21.00 | 3.00 | 991 | -7.37 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 149337 | 3.00 | 6.00 | 0.00 | 977 | -5.46 | - | `modeled_committed_prefix_collision` | playfield_boundary |
| 149780 | 4.00 | 0.00 | 1.00 | 1022 | -6.16 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000,fast_mode |
| 154179 | 3.00 | 1.00 | 0.00 | 473 | -2.61 | - | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |

### Final B / Kaguya

- Death frames: 174782, 176033, 183959, 186296, 204199, 217973, 218850, 225840, 228457
- Cause counts: `{"observed_bullet_overlap": 4, "modeled_committed_prefix_collision": 5}`
- Phase markers: observed 11, reachable static opcode `0x94` 14.
- Bottom/side occupancy decisions: 1794/1311.

| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | Corridor slack | Cause | Factors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 174782 | 3.00 | 118.00 | 0.00 | 342 | -17.32 | -14.11 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss |
| 176033 | 3.00 | 103.00 | 0.00 | 451 | -2.51 | -15.03 | `observed_bullet_overlap` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 183959 | 3.00 | 92.00 | 0.00 | 823 | -2.76 | -8.70 | `modeled_committed_prefix_collision` | playfield_boundary,corridor_deadline_miss,fast_mode |
| 186296 | 3.00 | 76.00 | 0.00 | 117 | -4.73 | 4.15 | `modeled_committed_prefix_collision` | playfield_boundary |
| 204199 | 3.00 | 63.00 | 0.00 | 562 | -4.54 | 1.98 | `modeled_committed_prefix_collision` | playfield_boundary,fast_mode |
| 217973 | 3.00 | 47.00 | 0.00 | 336 | -2.42 | 0.50 | `observed_bullet_overlap` | fast_mode |
| 218850 | 3.00 | 32.00 | 0.00 | 478 | -3.83 | 6.60 | `modeled_committed_prefix_collision` | playfield_boundary |
| 225840 | 3.00 | 23.00 | 0.00 | 1182 | -1.56 | - | `modeled_committed_prefix_collision` | playfield_boundary,pool_density_over_1000 |
| 228457 | 3.00 | 23.00 | 0.00 | 1121 | -4.63 | - | `observed_bullet_overlap` | playfield_boundary,pool_density_over_1000 |

## Spell Inventory And Runtime Coverage

Every spell below is statically reachable for route 2 Hard Final B. `unresolved` means this run did not persist the live spell ID; it does not mean the spell was absent.

### Stage 1

- ECL: `ecldata1.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 0 | 蛍符「地上の流星」 | リグル・ナイトバグ | 3 | 6 | 0 | 0 |
| 4 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 11 | 6 | 0 | 0 |
| 8 | 蠢符「ナイトバグストーム」 | リグル・ナイトバグ | 13 | 27 | 0 | 1 |
| 11 | 隠蟲「永夜蟄居」 | リグル・ナイトバグ | 12 | 27 | 0 | 0 |

### Stage 2

- ECL: `ecldata2.ecl`
- Observed/expected phase-counter markers: 2/3.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 15 | 声符「木菟咆哮」 | ミスティア・ローレライ | 4 | 7 | 0 | 0 |
| 19 | 毒符「毒蛾の鱗粉」 | ミスティア・ローレライ | 5 | 7 | 0 | 0 |
| 23 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 4 | 8 | 0 | 0 |
| 27 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 7 | 9 | 0 | 0 |
| 30 | 夜雀「真夜中のコーラスマスター」 | ミスティア・ローレライ | 3 | 7 | 0 | 0 |

### Stage 3

- ECL: `ecldata3.ecl`
- Observed/expected phase-counter markers: 3/4.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 34 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 3 | 0 | 0 | 0 |
| 37 | 始符「エフェメラリティ137」 | 上白沢慧音 | 2 | 2 | 0 | 1 |
| 41 | 野符「義満クライシス」 | 上白沢慧音 | 3 | 3 | 0 | 1 |
| 45 | 国符「三種の神器　鏡」 | 上白沢慧音 | 3 | 2 | 0 | 0 |
| 49 | 虚史「幻想郷伝説」 | 上白沢慧音 | 1 | 0 | 1 | 1 |
| 52 | 未来「高天原」 | 上白沢慧音 | 1 | 0 | 1 | 0 |

### Stage 4A / Reimu

- ECL: `ecldata4a.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 56 | 夢境「二重大結界」 | 博麗霊夢 | 3 | 0 | 0 | 2 |
| 60 | 散霊「夢想封印　寂」 | 博麗霊夢 | 3 | 0 | 0 | 0 |
| 64 | 神技「八方鬼縛陣」 | 博麗霊夢 | 7 | 27 | 0 | 1 |
| 68 | 回霊「夢想封印　侘」 | 博麗霊夢 | 2 | 17 | 0 | 3 |
| 72 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 5 | 4 | 0 | 1 |
| 75 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 2 | 5 | 0 | 0 |

### Stage 5

- ECL: `ecldata5.ecl`
- Observed/expected phase-counter markers: 7/8.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 102 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 6 | 0 | 0 | 0 |
| 110 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 3 | 0 | 0 | 0 |
| 106 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 3 | 3 | 0 | 3 |
| 114 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 6 | 3 | 0 | 0 |
| 117 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 4 | 2 | 0 | 0 |

### Final B / Kaguya

- ECL: `ecldata7.ecl`
- Observed/expected phase-counter markers: 11/14.

| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 149 | 薬符「壺中の大銀河」 | 八意永琳 | 4 | 0 | 0 | 2 |
| 153 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 5 | 1 | 5 | 1 |
| 157 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 4 | 4 | 2 | 0 |
| 161 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 4 | 8 | 1 | 1 |
| 165 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 3 | 2 | 2 | 0 |
| 169 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 26 | 3 | 0 | 2 |
| 173 | 「永夜返し  -上つ弓張-」 | 蓬莱山輝夜 | 3 | 1 | 0 | 1 |
| 177 | 「永夜返し  -子の三つ-」 | 蓬莱山輝夜 | 3 | 2 | 0 | 1 |
| 181 | 「永夜返し  -丑三つ時-」 | 蓬莱山輝夜 | 2 | 2 | 0 | 0 |
| 185 | 「永夜返し  -寅の三つ-」 | 蓬莱山輝夜 | 4 | 4 | 0 | 0 |
| 189 | 「永夜返し  -明けの明星-」 | 蓬莱山輝夜 | 12 | 5 | 0 | 0 |

## Runtime And Harness Findings

- Observed auto-Z stall frames: none.
- Route termination: `route_complete` at completion probe frame 228661.
- Unique robust solutions observed: 9265; solve time median/p95/max 121.64/422.51/593.17 ms.
- First-observed policy age median/p95/max: 2.00/8.00/1817.00 frames.
- Viability queries available: 69728/69728; robustly constrained decisions: 36638/70699.
- Robust-policy decisions without any usable query: 367/70095.
- Global-horizon/local-prefix cross-tab: 56196 decisions; winning global state with unsafe selected prefix: 13; losing global state with safe short prefix: 24917; selected globally certified action contradicted by the fresh local prefix checker: 6; selected action outside the reported winning set: 429.
- Live spell attribution was recorded at every hit edge; exact per-spell counts are preserved below.
- `1` hit edges remain in the `sensor_gap_or_unmodeled_hazard` class and require executor-level same-frame emission/transform evidence.

## Next Regression Work

1. Keep robust backward-reachability solves within the finite policy horizon, then verify nonzero live query and constrained-decision counts.
2. Replay all 39 retained witnesses through the integrated executor and preserve one regression per concrete failure.
3. Re-run focused Stage 4A and Final B practices before another full Hard route; compare hit frames, policy age, action-set exhaustion, and cluster recurrence.
4. Add item/Power state and finite Bomb resources only after the no-Bomb movement policy has passed physical validation.
