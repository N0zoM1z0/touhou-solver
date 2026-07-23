# sakuya_remilia_extra

Status: `analysis_target_not_yet_solved`

- Team: Sakuya/Remilia (route ID 2)
- Difficulty: Extra (mask `0x0f`)
- Branch: Extra uses its dedicated ECL; its spell records carry mask 0xFF.
- Player resources: `ply02a.sht` + `ply02as.sht`
- Movement: unfocused 4/2.828427; focused 2.3/1.626346
- Post-spawn/bomb gate reset value: 10
- Difficulty-mask candidate spell IDs: 14
- Statically reachable spell IDs: 14
- Reachable built-in callback indices: [18, 22, 23, 24, 31]

Reachability includes timeline roots, relative jumps, calls, child spawns,
interrupt slots, enemy-end transitions, health/timeout transitions, and auxiliary VMs.
Unknown runtime comparisons retain both
branches, so this is a conservative static set pending replay validation.

## Extra / Mokou

ECL: `ecldata8.ecl` (`a4da962f3621ef626a62fd01c3d1607f11e5706f3ab45480d3e36ac5b7b67741`)

| ID | Name | Owner | Root | Component subs | Bullet | Transform | Laser |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 191 | 旧史「旧秘境史　-オールドヒストリー-」 | 上白沢慧音 | 51 | 51, 52, 53, 54 | 17 | 10 | 0 |
| 192 | 転世「一条戻り橋」 | 上白沢慧音 | 56 | 56, 57, 58 | 2 | 3 | 0 |
| 193 | 新史「新幻想史　-ネクストヒストリー-」 | 上白沢慧音 | 60 | 60, 61, 62, 63 | 17 | 10 | 0 |
| 194 | 時効「月のいはかさの呪い」 | 藤原妹紅 | 93 | 93, 94, 95, 96 | 2 | 2 | 0 |
| 195 | 不死「火の鳥　-鳳翼天翔-」 | 藤原妹紅 | 97 | 97, 98, 99 | 27 | 5 | 0 |
| 196 | 藤原「滅罪寺院傷」 | 藤原妹紅 | 100 | 100, 101, 102 | 1 | 2 | 0 |
| 197 | 不死「徐福時空」 | 藤原妹紅 | 103 | 103, 104, 105, 106, 107 | 3 | 3 | 0 |
| 198 | 滅罪「正直者の死」 | 藤原妹紅 | 108 | 108, 109, 110, 111, 112 | 2 | 0 | 1 |
| 199 | 虚人「ウー」 | 藤原妹紅 | 113 | 85, 113, 114, 115, 116, 117 | 1 | 2 | 0 |
| 200 | 不滅「フェニックスの尾」 | 藤原妹紅 | 118 | 85, 118, 119, 120, 121, 122, 123, 124, 125 | 3 | 4 | 0 |
| 201 | 蓬莱「凱風快晴　-フジヤマヴォルケイノ-」 | 藤原妹紅 | 126 | 85, 126, 127, 128, 129, 130 | 4 | 11 | 0 |
| 202 | 「パゼストバイフェニックス」 | 藤原妹紅 | 131 | 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142 | 3 | 11 | 0 |
| 203 | 「蓬莱人形」 | 藤原妹紅 | 143 | 85, 143, 144, 145, 146, 147, 148 | 4 | 2 | 0 |
| 204 | 「インペリシャブルシューティング」 | 藤原妹紅 | 149 | 85, 149, 150, 151, 152, 153, 154, 155 | 8 | 70 | 0 |
