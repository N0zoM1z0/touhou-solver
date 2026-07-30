# NMNB Feasibility And First-Hit Iteration Perspective

Date: 2026-07-30

Retained discussion input. This is strategic perspective, not physical or
finite-model authority.

> 那你覺得我們能真的達到目標麽？NMNB，，，感覺還需要很久的迭代優化啊，也可能是我們之前的迭代方式/速度的問題 🤔


• 我的真實判斷是：技術上很有希望，但目前還不能說「照現在路線繼續磨就一定會成」。最大的風險未必是目標本身太難，而是迭代方法把大量時間花在低資訊量的 physical feedback
  上。

  74 hits 到 0 看似天文距離，但它不是 74 個獨立問題：第一次 miss 之後，Power、位置、無敵時間、phase timing、敵人存活與 RNG history 全部被改寫，後面很多 hit 都是污染後的
  連鎖結果。真正該看的距離是：

  > 每次 fresh attempt 的第一個 hit，能否在相同 native root 下找到可驗證的避開 witness？

  我覺得有希望的原因是：

  - end-to-end 已經能跑完整 Route 2、hard no-Bomb、處理轉場並可靠 cleanup；基礎 plumbing 不是空的。
  - 有些 coarse Boolean model 判定 losing 的 root，離線 exact restricted solver 卻能找到更長的 survival witness。這說明部分失敗來自模型離散化、future coverage 或
    planner class，不全是物理上無路可走。

  - native audit 找到的是具體可修的缺口：time scale、Focus/body gate、shared RNG、laser geometry、bullet lifecycle、physical bounds、callback coverage，而不是完全無法解
    釋的隨機失敗。

  - Controller 能讀 native state；只要 prediction 和 actuation 正確，它理論上比純畫面反應有更好的資訊條件。

  但目前也確實離 NMNB 很遠：

  - action-conditioned future producer 還不完整；
  - Stage 4A、Stage 5、Final B 都還有實質 survival gap；
  - live cadence／input pickup／publication deadline 可能讓「模型中可躲」變成「實際來不及」；
  - Extra 不是 Lunatic 完成後順手附送的驗收，它會是另一組獨立 workload。

  所以我的 verdict 是：

  如果繼續「改一點 → 跑一整輪不同 RNG → 看總 hit 數」：可能真的會拖非常久，而且容易反覆誤判。

  如果改成「固定 native roots → offline 全 action 分叉 → first-mismatch differential → 只把已勝出的 immutable candidate 送 physical」：達成 NMNB 是合理、可檢驗的研究目
  標。

  下一個真正有決定性的里程碑，不是把 74 hits 降到 60，而是做到：

  1. 對 canonical first-hit root 建立完整 causal root。
  2. 全 36 masks 離線分叉，不重用 action-incompatible future。
  3. 找到一個 exact no-hit witness。
  4. 用原版 native replay／fixed-root diagnostic 重現它。
  5. 再讓 live controller 在 focused physical scene 執行成功。
  6. 對同一類 root 重複多次，才擴到下一個 first hit。

  如果這條鏈能在幾個 Stage 4A／Stage 5 canonical first hits 上閉環，我會對最終 NMNB 明顯樂觀；如果連完整模型下所有 action 都被證明在輸入延遲內不可行，那也會很快告訴我們
  必須改 cadence、anticipation 或 planner architecture，而不是繼續盲調。

  所以不是「快完成了」，但也不像無底洞。眼下更像是：我們已經做出了一架能飛完全程但會反覆失速的飛機；現在需要風洞和模擬器，而不是每改一顆螺絲就再飛一趟跨洋航線。
