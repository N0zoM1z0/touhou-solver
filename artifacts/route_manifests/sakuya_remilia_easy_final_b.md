# sakuya_remilia_easy_final_b

Status: `analysis_target_not_yet_solved`

- Team: Sakuya/Remilia (route ID 2)
- Difficulty: Easy (mask `0x01`)
- Branch: Original Game Start Easy route 2 ending at Final B.
- Player resources: `ply02a.sht` + `ply02as.sht`
- Movement: unfocused 4/2.828427; focused 2.3/1.626346
- Post-spawn/bomb gate reset value: 10
- Difficulty-mask candidate spell IDs: 33
- Statically reachable spell IDs: 30
- Reachable built-in callback indices: [0, 1, 2, 3, 4, 5, 6, 7, 12, 13, 14, 15, 18]

Reachability includes timeline roots, relative jumps, calls, child spawns,
interrupt slots, enemy-end transitions, health/timeout transitions, and auxiliary VMs.
Unknown runtime comparisons retain both
branches, so this is a conservative static set pending replay validation.

## Stage 1

ECL: `ecldata1.ecl` (`6b44a0ea36648edcdeae522a2ac16d1f09bf2097d3ddaa1a61c8c1703bad68ea`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 2 | 灯符「ファイヤフライフェノメノン」 | リグル・ナイトバグ | 38 | 38, 39, 40, 41, 42, 43 | 7 | 6 | 0 |
| 6 | 蠢符「リトルバグ」 | リグル・ナイトバグ | 44 | 44, 45, 46, 47 | 7 | 27 | 0 |

## Stage 2

ECL: `ecldata2.ecl` (`a1b183c4e1c9d939290192f84e50ac551e31a5abe91ac396e5b056a813051a10`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 13 | 声符「梟の夜鳴声」 | ミスティア・ローレライ | 23 | 23, 24 | 2 | 7 | 0 |
| 17 | 蛾符「天蛾の蠱道」 | ミスティア・ローレライ | 33 | 33, 34, 35, 36, 37 | 3 | 6 | 0 |
| 21 | 鷹符「イルスタードダイブ」 | ミスティア・ローレライ | 44 | 44, 45, 46, 47, 49, 50, 53 | 3 | 4 | 0 |
| 25 | 夜盲「夜雀の歌」 | ミスティア・ローレライ | 52 | 46, 49, 52, 53, 54, 55, 56 | 6 | 9 | 0 |

## Stage 3

ECL: `ecldata3.ecl` (`113e52b73dfdd94408b99dd7646ac973554cef76f1b7bd6686a773da6e974ce8`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 32 | 産霊「ファーストピラミッド」 | 上白沢慧音 | 30 | 30, 31, 32, 33 | 3 | 0 | 0 |
| 39 | 野符「武烈クライシス」 | 上白沢慧音 | 47 | 47, 48, 49 | 3 | 2 | 0 |
| 43 | 国符「三種の神器　剣」 | 上白沢慧音 | 50 | 50, 51, 52, 53 | 3 | 0 | 0 |
| 47 | 終符「幻想天皇」 | 上白沢慧音 | 67 | 67, 68, 69, 70 | 1 | 0 | 1 |

## Stage 4A / Reimu

ECL: `ecldata4a.ecl` (`797c83391c77d386abd264249224821be3d878fcf73b2bd71189dbfd3776f6cf`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 54 | 夢符「二重結界」 | 博麗霊夢 | 28 | 28 | 2 | 0 | 0 |
| 58 | 霊符「夢想封印　散」 | 博麗霊夢 | 30 | 21, 30, 31, 32 | 3 | 0 | 0 |
| 62 | 夢符「封魔陣」 | 博麗霊夢 | 33 | 21, 33, 34, 36, 37, 38 | 7 | 27 | 0 |
| 66 | 霊符「夢想封印　集」 | 博麗霊夢 | 41 | 41, 42, 43, 44 | 1 | 17 | 0 |
| 70 | 境界「二重弾幕結界」 | 博麗霊夢 | 46 | 46, 47, 48, 49, 50, 51, 52 | 3 | 4 | 0 |

## Stage 5

ECL: `ecldata5.ecl` (`3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 100 | 波符「赤眼催眠(マインドシェイカー)」 | 鈴仙・Ｕ・イナバ | 62 | 62, 85, 86 | 6 | 0 | 0 |
| 108 | 懶符「生神停止(アイドリングウェーブ」 | 鈴仙・Ｕ・イナバ | 63 | 63, 64, 65, 85, 86 | 2 | 0 | 0 |
| 104 | 狂符「幻視調律(ビジョナリチューニング)」 | 鈴仙・Ｕ・イナバ | 66 | 66, 67, 68, 69, 71, 72, 85, 86 | 2 | 2 | 0 |
| 112 | 散符「真実の月(インビジブルフルムーン)」 | 鈴仙・Ｕ・イナバ | 75 | 75, 85, 86 | 5 | 0 | 0 |

## Final B / Kaguya

ECL: `ecldata7.ecl` (`20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 147 | 薬符「壺中の大銀河」 | 八意永琳 | 19 | 19, 20, 21, 22, 23 | 4 | 0 | 0 |
| 151 | 難題「龍の頸の玉  -五色の弾丸-」 | 蓬莱山輝夜 | 50 | 50, 51, 52, 53 | 5 | 1 | 5 |
| 155 | 難題「仏の御石の鉢  -砕けぬ意思-」 | 蓬莱山輝夜 | 55 | 55, 56, 57, 58, 59, 60 | 3 | 4 | 2 |
| 159 | 難題「火鼠の皮衣  -焦れぬ心-」 | 蓬莱山輝夜 | 61 | 61, 62, 63, 64, 65 | 4 | 8 | 1 |
| 163 | 難題「燕の子安貝  -永命線-」 | 蓬莱山輝夜 | 67 | 43, 67, 68, 69 | 3 | 2 | 2 |
| 167 | 難題「蓬莱の弾の枝  -虹色の弾幕-」 | 蓬莱山輝夜 | 71 | 43, 71, 72, 74, 75, 76 | 26 | 3 | 0 |
| 171 | 「永夜返し  -初月-」 | 蓬莱山輝夜 | 77 | 43, 77, 78, 79 | 3 | 1 | 0 |
| 175 | 「永夜返し  -子の刻-」 | 蓬莱山輝夜 | 80 | 43, 80, 81 | 3 | 2 | 0 |
| 179 | 「永夜返し  -丑の刻-」 | 蓬莱山輝夜 | 82 | 43, 82, 83 | 2 | 2 | 0 |
| 183 | 「永夜返し  -寅の刻-」 | 蓬莱山輝夜 | 84 | 43, 84, 85, 86 | 4 | 4 | 0 |
| 187 | 「永夜返し  -朝靄-」 | 蓬莱山輝夜 | 87 | 43, 87, 88 | 12 | 5 | 0 |
