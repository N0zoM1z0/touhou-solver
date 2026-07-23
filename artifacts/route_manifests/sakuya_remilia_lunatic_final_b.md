# sakuya_remilia_lunatic_final_b

Status: `analysis_target_not_yet_solved`

- Team: Sakuya/Remilia (route ID 2)
- Difficulty: Lunatic (mask `0x08`)
- Branch: Primary full Lunatic acceptance branch; includes Kaguya and Last Spells.
- Player resources: `ply02a.sht` + `ply02as.sht`
- Movement: unfocused 4/2.828427; focused 2.3/1.626346
- Post-spawn/bomb gate reset value: 10
- Difficulty-mask candidate spell IDs: 40
- Statically reachable spell IDs: 37
- Reachable built-in callback indices: [0, 1, 2, 5, 6, 7, 12, 13, 14, 15, 18, 20, 21]

Reachability includes timeline roots, relative jumps, calls, child spawns,
interrupt slots, enemy-end transitions, health/timeout transitions, and auxiliary VMs.
Unknown runtime comparisons retain both
branches, so this is a conservative static set pending replay validation.

## Stage 1

ECL: `ecldata1.ecl` (`6b44a0ea36648edcdeae522a2ac16d1f09bf2097d3ddaa1a61c8c1703bad68ea`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 1 | 蛍符「地上の彗星」 | リグル・ナイトバグ | 22 | 21, 22, 23, 24 | 3 | 6 | 0 |
| 5 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 38 | 38, 39, 40, 41, 42, 43 | 11 | 6 | 0 |
| 9 | 蠢符「ナイトバグトルネード」 | リグル・ナイトバグ | 44 | 44, 45, 46, 47 | 13 | 27 | 0 |
| 12 | 隠蟲「永夜蟄居」 | リグル・ナイトバグ | 48 | 48, 49 | 12 | 27 | 0 |

## Stage 2

ECL: `ecldata2.ecl` (`a1b183c4e1c9d939290192f84e50ac551e31a5abe91ac396e5b056a813051a10`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 16 | 声符「木菟咆哮」 | ミスティア・ローレライ | 23 | 23, 24 | 4 | 7 | 0 |
| 20 | 猛毒「毒蛾の暗闇演舞」 | ミスティア・ローレライ | 38 | 38, 39, 40, 41, 42, 43 | 5 | 7 | 0 |
| 24 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 44 | 44, 45, 46, 47, 48, 49, 50, 53 | 6 | 8 | 0 |
| 28 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 52 | 48, 49, 52, 53, 54, 55, 56 | 8 | 9 | 0 |
| 31 | 夜雀「真夜中のコーラスマスター」 | ミスティア・ローレライ | 58 | 58, 59, 60, 61 | 3 | 7 | 0 |

## Stage 3

ECL: `ecldata3.ecl` (`113e52b73dfdd94408b99dd7646ac973554cef76f1b7bd6686a773da6e974ce8`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 35 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 30 | 30, 31, 32, 33 | 3 | 0 | 0 |
| 38 | 始符「エフェメラリティ137」 | 上白沢慧音 | 44 | 44, 45 | 2 | 2 | 0 |
| 42 | 野符「GHQクライシス」 | 上白沢慧音 | 47 | 47, 48, 49 | 3 | 3 | 0 |
| 46 | 国体「三種の神器　郷」 | 上白沢慧音 | 62 | 62, 63, 64, 65 | 3 | 0 | 0 |
| 50 | 虚史「幻想郷伝説」 | 上白沢慧音 | 67 | 67, 68, 69, 70 | 1 | 0 | 1 |
| 53 | 未来「高天原」 | 上白沢慧音 | 71 | 71, 72, 73, 74 | 1 | 0 | 1 |

## Stage 4A / Reimu

ECL: `ecldata4a.ecl` (`797c83391c77d386abd264249224821be3d878fcf73b2bd71189dbfd3776f6cf`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 57 | 夢境「二重大結界」 | 博麗霊夢 | 28 | 28, 29 | 3 | 0 | 0 |
| 61 | 散霊「夢想封印　寂」 | 博麗霊夢 | 30 | 21, 30, 31, 32 | 3 | 0 | 0 |
| 65 | 神技「八方龍殺陣」 | 博麗霊夢 | 33 | 21, 33, 35, 36, 37, 38 | 7 | 27 | 0 |
| 69 | 回霊「夢想封印　侘」 | 博麗霊夢 | 41 | 41, 42, 43, 44 | 2 | 17 | 0 |
| 73 | 大結界「博麗弾幕結界」 | 博麗霊夢 | 46 | 46, 47, 48, 49, 50, 51, 52 | 5 | 4 | 0 |
| 76 | 神霊「夢想封印　瞬」 | 博麗霊夢 | 54 | 31, 54, 55, 56, 57 | 2 | 5 | 0 |

## Stage 5

ECL: `ecldata5.ecl` (`3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 103 | 幻波「赤眼催眠(マインドブローイング)」 | 鈴仙・Ｕ・イナバ | 62 | 62, 85, 86 | 6 | 0 | 0 |
| 111 | 懶惰「生神停止(マインドストッパー)」 | 鈴仙・Ｕ・イナバ | 63 | 63, 64, 65, 85, 86 | 3 | 0 | 0 |
| 107 | 狂視「狂視調律(イリュージョンシーカー)」 | 鈴仙・Ｕ・イナバ | 66 | 66, 67, 68, 69, 71, 72, 73, 85, 86 | 3 | 3 | 0 |
| 115 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 75 | 75, 76, 77, 85, 86 | 6 | 3 | 0 |
| 118 | 月眼「月兎遠隔催眠術(テレメスメリズム)」 | 鈴仙・Ｕ・イナバ | 78 | 78, 79, 80, 81, 82, 83, 84, 85, 86 | 4 | 2 | 0 |

## Final B / Kaguya

ECL: `ecldata7.ecl` (`20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 150 | 薬符「壺中の大銀河」 | 八意永琳 | 19 | 19, 20, 21, 22, 23 | 4 | 0 | 0 |
| 154 | 神宝「ブリリアントドラゴンバレッタ」 | 蓬莱山輝夜 | 50 | 50, 51, 52, 53 | 5 | 1 | 5 |
| 158 | 神宝「ブディストダイアモンド」 | 蓬莱山輝夜 | 55 | 55, 56, 57, 58, 59, 60 | 4 | 4 | 2 |
| 162 | 神宝「サラマンダーシールド」 | 蓬莱山輝夜 | 61 | 61, 62, 63, 64, 65, 66 | 4 | 8 | 2 |
| 166 | 神宝「ライフスプリングインフィニティ」 | 蓬莱山輝夜 | 67 | 43, 67, 68, 69 | 3 | 2 | 2 |
| 170 | 神宝「蓬莱の玉の枝  -夢色の郷-」 | 蓬莱山輝夜 | 71 | 43, 71, 72, 73, 75, 76 | 26 | 3 | 0 |
| 174 | 「永夜返し  -待宵-」 | 蓬莱山輝夜 | 77 | 43, 77, 78, 79 | 3 | 1 | 0 |
| 178 | 「永夜返し  -子の四つ-」 | 蓬莱山輝夜 | 80 | 43, 80, 81 | 3 | 2 | 0 |
| 182 | 「永夜返し  -丑の四つ-」 | 蓬莱山輝夜 | 82 | 43, 82, 83 | 2 | 2 | 0 |
| 186 | 「永夜返し  -寅の四つ-」 | 蓬莱山輝夜 | 84 | 43, 84, 85, 86 | 4 | 4 | 0 |
| 190 | 「永夜返し  -世明け-」 | 蓬莱山輝夜 | 87 | 43, 87, 88 | 12 | 5 | 0 |
