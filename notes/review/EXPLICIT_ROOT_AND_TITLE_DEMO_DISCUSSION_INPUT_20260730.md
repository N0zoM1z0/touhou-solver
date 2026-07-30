# Explicit-Root And Title-Demo Discussion Input

Date: 2026-07-30

This is the verbatim retained discussion previously stored at
`/tmp/vc_sth.txt`. It is strategic/research input, not native or physical
authority. The clone paths mentioned below were subsequently moved to
`references/external/20260730/`; see
`EXTERNAL_REFERENCE_SNAPSHOT_INDEX_20260730.md`.

有個idea：遊戲本身有自動打的（長時間不懂，首頁會進入自動play的展示模式），這裡有可能給我們一些可借鑑的思路麼？不知道這裡是錄製的還是真的決策在打
• 已 clone 完，六個 repo 都以 shallow clone 放在 /tmp/th08-external-research-17wrD4，沒有污染正在被其他 agent 修改的 workspace。/tmp 重啟後可能消失，但目前所有 agent 都
  可以直接讀。

  - th08-decomp — 84738749bdcf
  - thtk — 892114a0fcaa
  - PyTouhou — fbfba5269cfc
  - thprac — 8b3338f4d2cc
  - libTAS — a1bffe9f9907
  - hourglass-win32 — 78fa7c6d2be1

  完整只讀審計在 /tmp/TH08_EXPLICIT_ROOT_AND_TITLE_DEMO_READ_ONLY_REVIEW_20260730.md，25,477 bytes，SHA-256：

  b88fd1f52aa570eff3dd75608f501d2b9cdecff4ece8b29666a4a27bc61df99e

  核心結論如下。

  ### 1. Native snapshot 可以實現，但目前的 v5 capture 還不是

  目前的 root artifact 只證明「process suspend 期間讀到了一組原子 bytes」，尚未證明它是：

  - 固定 scheduler phase
  - 可完整 restore
  - 可從那裡繼續執行
  - restore 後同 action 得到完全相同 future

  目前仍缺 ECL VM、timeline、player/input/shot、資源與 damage、callback/transition、physical clock 等七類狀態，還有大量 pointer 只捕獲了指標本身。因此不能直接 memcpy 回
  去便稱為 explicit root。

  我認為正確的第一版是：

  正常 replay 跑一次到 canonical pre-input boundary
                      ↓
          捕獲 TH08-specific native root
                      ↓
   restore → action A → 跑 1 native tick → fingerprint
   restore → action B → 跑 1 native tick → fingerprint
   restore → action C → 跑 1 native tick → fingerprint
                      ↓
          再逐步擴成 2/4/8/16/60 frames

  它應該是一個注入遊戲內的 narrow native rollback stepper：

  - 固定在已重新驗證的 replay-input publisher／controller pickup 邊界。
  - 使用原版 x86/x87 遊戲邏輯計算 bullets、enemy、ECL、collision。
  - 用 dirty-page journal 或 copy-on-write baseline 快速回復。
  - 遇到未追蹤 allocation、callback、stage transition、async side effect 時直接回 UNKNOWN。
  - harness 自己的 stack/control state 放在 restore 區域外。

  Microsoft 的 Process Snapshotting (https://learn.microsoft.com/en-us/windows/win32/api/processsnapshot/ne-processsnapshot-pss_capture_flags) 可以幫忙取得 VA clone/COW
  baseline，但它本身不是受支援的「任意 restore 後繼續跑」executor；Hyper-V checkpoints
  (https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints) 則太重，只適合粗粒度備用。

  以 root frame 12316、36 masks、60-frame horizon 計算：

  - 每個 action 都重跑 replay prefix：約 445,536 native updates。
  - prefix 一次、snapshot 後分叉：約 14,476 updates。
  - 純 update 數約少 30.8×；在 root 已捕獲後，內層分叉約少 206×。

  實際 wall time 還要加入 restore/fingerprint 成本，但量級上確實會從「一個下午看幾個樣本」變成「同一 failure root 做大量可重現實驗」。

  ### 2. Title autoplay 可以確定是預錄 replay，不是遊戲 AI

  原版 title idle 超過約 1500 frames 後，會輪流載入：

  demo/demorpy0.rpy
  demo/demorpy1.rpy
  demo/demorpy2.rpy
  demo/demorpy3.rpy

  它們經普通 T8RP replay decoder 解碼，恢復 recorded route、difficulty、resources、stage RNG seed，再由正常 replay input publisher 每幀把錄製 mask 寫入
  g_input_current。這和反編譯的 TitleScreen.cpp (https://github.com/GensokyoClub/th08/blob/main/src/TitleScreen.cpp) 及 ReplayManager.cpp
  (https://github.com/GensokyoClub/th08/blob/main/src/ReplayManager.cpp) 相符。

  四個 demo 都是 Lunatic 單關 replay，而且全部包含 Bomb press。因此：

  - 沒有隱藏的 dodge decision logic。
  - 不是 NMNB policy。
  - 但它提供了很有價值的 deterministic bootstrap 與 input substitution seam。

  實作風洞時最好用「普通 replay mode」，不必真的走 title demo mode。跑到指定 root 後，hook replay cursor，把下一個 recorded mask 換成分叉 action。action 改變後，後續輸
  入必須由該 branch 的 observation 重新決策，不能接回原 replay suffix，否則只是 open-loop 假想路徑。

  ### 3. 外部 repo 最值得借鑑的是 checkpoint 工程，不是 solver

  - GensokyoClub/th08 (https://github.com/GensokyoClub/th08)：title/replay 路徑很有用，但核心 Enemy/Bullet/Player 更新仍不完整，不能當 engine。
  - thtk (https://github.com/thpatch/thtk)：適合 archive/replay 格式與 fixture，不含 gameplay semantics。
  - PyTouhou：展示了把每幀 gameplay step 與 renderer/window 解耦，但主要是 TH06。
  - thprac：可借鑑 scene/practice bootstrap；TH06–10 並沒有完整 mid-game replay savestate。
  - libTAS (https://clementgallet.github.io/libTAS/guides/how/)：dirty/incremental savestate、deterministic time、thread/context 管理很值得學；Wine 支援仍屬實驗性。
  - Hourglass (https://github.com/TASEmulators/hourglass-win32)：確實做過 Windows writable-memory/thread-context savestate、D3D8/DirectSound hooks，也有 TH08 TAS
    歷史；但其事後分析 (https://tasvideos.org/Forum/Topics/20210)正好說明通用 Windows rerecord 為何容易被 kernel/external state 拖垮。

  所以需要修正之前一個說法：Touhou/Windows 的手動離線 rerecord 並不新；真正很超前的是「自動全 action 分叉、因果 policy、robust delay/cadence、exact witness 再 physical
  promotion」。

  下一個最有決定性的 milestone 不是做完整 60-frame solver，而是：

  1. A → restore → A 每個 byte/semantic fingerprint 完全一致。
  2. A → restore → B 在 input pickup 前完全一致，只在宣告的作用點後分叉。
  3. horizon 依次擴為 2、4、8、16 frames。
  4. 同一 immutable root 跑完 36 個 no-Bomb masks。
  5. 才接 branch-specific controller 和 exact no-hit witness。

  這條路不能保證 NMNB 一定成功，但它很可能消除目前最大問題：不同 RNG、不同 root、整輪 physical feedback 混在一起，導致每次改動的因果訊號極弱。這次只按 native-semantics
  audit 邊界做了調研與報告，沒有改 workspace、IDA 或啟動 physical trial。

─ Worked for 31m 24s ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
