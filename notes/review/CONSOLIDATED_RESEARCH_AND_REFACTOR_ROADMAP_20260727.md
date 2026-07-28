# Touhou Solver：綜合研究、重構與交付路線

日期：2026-07-27

審閱基線：`52f746f744760a059c70fd3731b4952f1ecae6f3`

文件性質：已定下來的執行路線；不改變 `STRATEGY.md` 的 live/shadow/proposed/rejected
狀態，也不替代既有 formal contracts。

## 1. 結論先行

接下來的核心任務不是「再做一個更快的躲彈 heuristic」，也不是把整個 agent
改寫成 C++。真正要解決的是：

> 在每次實際 issue 前，從同一個物理觀測、同一個 input-pipeline root、同一個
> hazard/model version，及時交付一個因果、非 clairvoyant、可重放的 robust
> action；並在完整 horizon witness 不存在或來不及完成時，明確區分 finite-model
> empty、模型未覆蓋、計算未完成、publication 過期與真正可用的 partial-survival
> lower witness。

目前 39 次 Hard full-route contact 中有 38 次發生在 global kernel 已經 empty
之後。這不等於「global empty 已被證明是每次命中的唯一原因」，但足以確定：

1. 局部 decode/geometry 再快一點不是當前第一主因；
2. 必須更早保存可恢復空間，並正確處理 coarse/finite-horizon empty；
3. post-empty fallback 不能再是沒有 formal label 的一般 heuristic；
4. 維護性已經是 correctness 問題：現在數個關鍵函式太長、資料契約混雜，
   每次新增 model、refinement 或 delivery lane 都容易跨越 authority 邊界。

因此採用兩條互相解鎖、但分開驗證的主線：

- **結構線：** 先用純重構 checkpoint 把 corridor、native binding/kernel、
  local planner、issue transaction 和 live session 拆成窄介面；每一步保持
  exact behavior、ABI 與 hard-mask parity。
- **研究線：** 先建立 exact-root causal dossier 和正交狀態分類，再依序做
  model-covered lower/upper、query-local refinement、exact augmented-root
  partial survival，以及由較早 global version 產生的 pre-loss continuation
  reserve。

性能不是只跑一次的附屬 gate，也不受這份 roadmap 已列出的候選方法限制。
任何新 physical tail、publication miss、hit 因果鏈或資源爭用，只要可能影響
survival，都應先保留 evidence、固定單一 intervention contract，再做
Linux/Windows/physical 對照；通過後仍持續尋找下一個可證偽瓶頸。

禁止 big-bang rewrite。任何「搬檔 + 改 recurrence + 做效能優化」的混合提交都
應拆開。

### 2026-07-28 execution checkpoint

- G5 realized birth-to-hit provenance and the first nonspell source
  hypothesis are complete as action-free research checkpoints.
- The visible ready derived-parent hypothesis failed physically with zero
  candidates over 11,801 Stage-5 observations, including reproduced
  30-bullet waves. The separate second pool pass also failed the fixed
  combined performance gate.
- The failed observer is now independently opt-in and cannot add overhead to
  ordinary schema-v9 birth traces. This follows the roadmap rule that
  performance is continuous and failed experimental work must not silently
  become baseline cost.
- Next G5 source work begins with ordinary nonspell enemy main VMs, then
  auxiliary/callback/deferred/native sources. Parallel survival work remains
  the earlier viability-loss problem; zero derived-source signal does not
  reduce CE-0158.

## 2. 審閱材料與證據邊界

本次綜合了兩個外部審閱包：

| 包 | SHA-256 | 範圍 |
| --- | --- | --- |
| `audits/7.27/touhou_solver_deep_review_20260727.zip` | `7fa79e025dade5a0eafcf595a8df5d35031755e695b63eed9e25fd3d0ab7263e` | 架構、演算法、systems、code scan、介面草案 |
| `audits/7.27/touhou_solver_deep_analysis_2026-07-27.zip` | `0e84318eb6278e5cd33c8731b506e6173dc7438ff2e7db99e795c3b4b3a93c62` | 固定 commit 分析、演算法細案、schemas、推薦矩陣 |

兩包都已在 `audits/7.27/` 原位解壓，並通過各自的 `SHA256SUMS.txt`。

證據邊界：

- **Observed（已觀察）：** 第二包指向 exact commit；兩包對 repository
  文件、程式與 retained reports 的摘錄大致準確。
- **Observed（已觀察）：** 第一包主要是 remote/static review；兩包都沒有
  產生新的 shipped-game runtime、Windows contention 或 physical survival
  證據。
- **Inferred（推論）：** 它們能提供架構與演算法候選，不能提升任何策略的
  authority。最終優先級仍以 repository code、retained artifacts、
  counterexamples 和 formal contracts 為準。

本次工作也重新檢查了 current source，並在 Linux 重新通過 quick suite
`584/584`。以下是決策使用的主要 retained evidence：

| 證據 | 結果 | 決策含義 |
| --- | ---: | --- |
| Hard Stage 1 | 7,099 decisions，0 hit，0 Bomb | local/live 基線在聚焦 workload 可用 |
| Hard full route | 70,699 decisions，39 hits，0 Bomb | 尚未達 acceptance |
| contact after global empty | 38/39 | P0 指向 early feasibility 與 degraded fallback |
| Stage4A empty roots | 61；6 spatial、8 primary short-horizon、47 unresolved | `empty` 不能是單一 label |
| full-field 4 px | median/p95 約 1.06/3.51 s | 不進 live 設計 |
| fresh/global transaction gate | 4,627 transactions，0 silent outside-global | 歷史 authority bug 已修，應固化而非假設仍未修 |
| supplemental sync/async | finite parity 成功，但各產生 delivery miss | CE-0131 繼續阻擋 current-issue supplemental |
| semantic fuzzer | retained gate zero hard mismatch | 可作重構與 native parity gate |

## 3. 對外部建議的最終裁決

### 3.1 直接採納

1. **lower 用於 action authority，upper 只決定還要算哪裡。**
2. **query-local 16→8→4 refinement，拒絕 uniform full-field 4 px。**
3. **exact augmented-root partial-survival witness。**
4. **端到端 age ledger；看 p99/p99.9/max，不只看 solve median/p95。**
5. **Python control plane + C++ data plane + independent Python oracle。**
6. **Boolean first、complete-only、exact-version、newest-target-wins。**
7. **future birth/transform 的 model confidence 必須顯式存在。**
8. **bitset、rolling repair、SIMD、process isolation 都只能在語義穩定後
   逐項 gate。**

### 3.2 修正後採納

#### 「Global tri-state」

單一 `VIABLE / PROVED_LOSING / UNRESOLVED` 仍然會混淆不同層次。採用第 6 節
的正交狀態，而不是一個 overloaded enum。裸字串 `PROVED_LOSING` 禁止進
telemetry；至少要說清楚是 declared finite model empty，還是 physical model
也有完整 coverage。

#### 「Issue transaction 是 P0 新功能」

CE-0127/CE-0128 的 fresh/global intersection 已修復並通過 physical gate。
下一步不是重做同一功能，而是：

- 把現有行為抽成 immutable transaction type；
- 消除 `Decision` 內 action-specific stale metadata 的結構性風險；
- 加 commit-time identity/lease checks；
- 用歷史反例和 property tests 固化。

重構 checkpoint 不應偷偷改 fallback 行為。

#### 「Terminal continuation 會救回 empty」

更嚴格的 terminal lower set 只會縮小當下 finite kernel；它不能直接救回已
empty 的 root。它的價值是更早拒絕 horizon cliff，或在 hard-winning action
之間保存未來 option value，從而可能讓後續 rolling roots 更晚耗盡。

因此 terminal/option 工作是 **upstream strategy experiment**，不是 spatial
false-empty 修復，也不能只以「當前 viable root 變多」驗收。

#### 「Partial survival 只可在 upper 也 empty 時使用」

只有 upper 也 empty 時，才可聲稱 declared-model loss 已被排除所有 action。
但是一個完整、可重放的 restricted causal partial-survival policy，本身是可達
lower witness；在 full-horizon status 仍 unresolved 時也可以作 degraded
proposal，只是 mode 必須叫 `PARTIAL_SURVIVAL_WITNESS_ON_UNRESOLVED`，不能叫
`POST_LOSS` 或 `SAFE`。

#### 「Process isolation 立即進 P1」

先做 record-only age ledger、immutable data contract 和 ETW/WPA attribution。
只有證據顯示同進程 executor/native fan-out 造成 issue tail，才移 planner 或
shadow service。否則 IPC、crash recovery 和 snapshot copy 可能增加另一種 tail。

### 3.3 延後

- full main-beam one-call native；
- persistent native worker team；
- bitset recurrence；
- dirty-cone incremental repair；
- AVX2/PGO/LTO；
- density-adaptive full/sparse RPM；
- shared-memory multi-process publication。

這些都有潛力，但目前不能先於模型、狀態與可維護邊界。

### 3.4 拒絕或保持 shadow-only

- **整個 agent 改寫成 C++：** 不解決 model/causality/state explosion。
- **同步 full-field 4 px：** 已有秒級 p95 反證。
- **增加 same-root worker >4：** 現有 contention evidence 不支持。
- **learned/MCTS/RL 直接擁有 hard authority：** 量詞不符。
- **立即把 swept continuous collision 當 physical truth：** TH08 的實際
  collision/update order 可能是離散 native update。連續 sweep 在未驗證前會
  引入未知方向的 conservative error。先以 IDA/native probe/retained trace
  證明同一 update interval 的物理碰撞語義，再決定它是 hard rule、diagnostic
  或不需要。
- **GPU 進 current issue path：** 啟動、同步及 driver tail 不合目前 workload。

## 4. 目前真正要解的四個核心問題

### 4.1 物理根是否正確

完整控制根不是 `(frame, x, y, desired_action)`，而至少是：

```text
(
  physical_time_interval,
  position_interval,
  active_action,
  held_desired_action,
  pending_action?,
  remaining_delay_support,
  observation/clock_epoch,
  immutable model/version
)
```

no-write 必須保留 pending countdown；相同 observation 的 hidden branches
必須先 merge，再讓 controller maximization。當前 formal/oracle/shadow 已涵蓋
這些語義，但 live caller 仍有 active-equals-held estimator fallback。這是
correctness promotion gate，不是一般效能工作。

### 4.2 Finite model 為何 empty

要分開：

- spatial cell conservatism；
- horizon 真正只活不到 80 frames；
- upstream action 把 root 帶進低-option region；
- uncertainty inflation；
- future birth/transform/model coverage；
- wrong root/clock/version；
- timeout/cancel/unvisited work；
- declared finite model 的完整 empty。

這些因素可以重疊。不得強迫每個 root 只有一個「唯一原因」；應保存 factorial
ablation 和最小 sufficient rescue set。

### 4.3 有效答案能否在 issue 前送達

solver kernel 完成時間不是 delivery time。真正的 budget 是：

```text
capture/read/decode
  + queue wait
  + solve
  + publication
  + consumer pickup
  + fresh certificate
  + commit/send guard
```

CE-0131 已證明 isolated kernel 很快不代表 current-issue hybrid 可交付。

### 4.4 程式能否安全擴展與 debug

當 model、planner、service、trace 和 fallback 在同一個 2,000–4,000 行函式中，
一個「小修改」很難被分類為純重構、策略變更或 authority 變更。模組化的目的
不是追求漂亮目錄，而是讓每次差分只跨越一個 formal boundary。

## 5. 問題契約

後續 major planner/model change 必須保持下列 contract：

- **Physical objective：** Sakuya/Remilia，Lunatic 與 Extra 的 no-Bomb
  survival；Hard 是 workload，不是 acceptance target。
- **Observation：** native game state、capture interval、player/pools/ECL
  semantic state、active input evidence；screenshot 不作 runtime authority。
- **Action：** 完整 input mask；持有相同 desired mask 是 no-write；Bomb bit
  `0x02` 預設禁止。
- **Uncertainty：** capture span、input pickup、recursive cadence、
  hidden remaining-delay information set、geometry/model/numeric error、
  future-event support。
- **Transition：** non-clairvoyant；相同 observation 先 merge hidden branches。
- **Horizon/resources：** finite horizon、compute budget、lives/Bombs/Power/
  phase constraints分開記錄。
- **Safety：** survival hard；route、damage、Power、items、graze、score 只在
  hard-admissible set 內排序。
- **Deadline：** exact immutable version 在 issue lease 內 complete-only
  publication；miss 使用已聲明 fallback。
- **Fallback：** ordinary live Boolean + fresh local hard certificate；
  partial-survival 只有在 exact witness 完整、版本新鮮時才可取得 degraded
  authority。

## 6. 不再使用 overloaded `empty`：正交結果模型

每次 global/root query 至少輸出五個正交欄位：

```text
ComputationStatus:
  COMPLETE | INCOMPLETE | CANCELLED | DEADLINE

FiniteModelStatus:
  NONEMPTY | EMPTY | NOT_DETERMINED

CoverageStatus:
  COVERED | SENSOR_INCOMPLETE | FORECAST_UNKNOWN
  | CLOCK_INVALID | MODEL_MISMATCH

DeliveryStatus:
  FRESH | STALE | LATE | WRONG_ROOT | WRONG_EPOCH | NOT_PUBLISHED

AuthorityStatus:
  LIVE_LOWER_MASK | DEGRADED_PARTIAL_WITNESS | TELEMETRY_ONLY | NONE
```

另附可多選的 `DiagnosisTag`：

```text
SPATIAL_AMBIGUITY
SHORT_HORIZON_ONLY
UNCERTAINTY_SENSITIVE
FUTURE_BIRTH_GAP
ROUTE_OR_TUBE_COLLAPSE
TERMINAL_CONTRACT_SENSITIVE
PUBLICATION_MISMATCH
UNRESOLVED_ACTIONS
```

規則：

1. `lower_mask != 0` 才能提供 ordinary lower authority。
2. `lower_mask == 0` 且 `upper_mask != 0` 是 unresolved。
3. `lower_mask == upper_mask == 0` 只在 upper 本身 sound、complete 時說
   `EMPTY`；仍需另看 `CoverageStatus` 才能談 physical meaning。
4. timeout、candidate exhaustion、unvisited actions 永遠不是 empty proof。
5. `COARSE_FALSE_EMPTY` 是跨模型 offline diagnosis，不是單次 live result。

## 7. Current code audit

行數只是 signal；以下問題來自責任與生命週期混合。

| 檔案/符號 | 當前規模 | 實際混合的責任 | 決定 |
| --- | ---: | --- | --- |
| `scripts/corridor_planner.py` | 1,699 行 | hazard types、scalar/native clearance、legacy forward DP、robust build、uniform refinement、rollout、timing | 搬入 game-neutral package；根檔保留薄 facade |
| `_plan_robust_corridor()` | 430 行 / 14 參數 | grid/clearance、query problem、hook side effect、viability、refinement、safety value、rollout、result | 拆成 prepare/solve/refine/rollout |
| `_hazard_clearance_volume()` | 196 行 | backend dispatch、四種 geometry、native fallback | 獨立 clearance builder/backend |
| `scripts/th08_corridor_runtime.py` | 897 行 | solve、audit write、prewarm service、publication query、retirement、commitment | artifact、resource owner、publication 分開 |
| `CorridorSolution` | process-local mutable aggregate | plan、Future、workspace、service、audit、worker settings | 禁止作 IPC/publication；拆 immutable payload 與 closeable handles |
| `scripts/th08_live_dodge_agent.py` | 10,579 行 | address/layout、decode、sensing、local planner、issue、services、scene/clock、trace、CLI | 只保留 CLI/orchestration facade |
| `choose_action()` | 2,225 行 / 48 參數 | validation、projection、certificate、beam、supplemental、selection、damage、retry、Decision build | `LocalPlanRequest -> LocalProposal` staged pipeline |
| `run()` | 3,748 行 | resource ownership、wait/scene、capture、services、plan、issue、trace、cleanup | session context + bounded `step()` stages |
| `Decision` | 約 50 個欄位 | proposal、hard cert、global guidance、issue result、shadow diagnostics、timing | proposal/issued/telemetry 分型 |
| `scripts/touhou_control/native_backend.py` | 3,656 行 | loader、ctypes ABI、array coercion、geometry/local/viability/pipeline/belief wrappers | domain bindings + compatibility facade |
| `native/robust_viability_kernel.cpp` | 4,108 行 | geometry、decode、local hazards、beam、global DP、query survival、C ABI | proper multi-translation-unit library |
| native implementation headers | 873/1,477/2,453 行 | class implementation與 exported ABI 混在 header，依賴 include 順序 | self-contained internal headers + `.cpp` |
| giant tests | 1,270/3,180 行 | 多個 domain 的 fixtures/patch paths | 隨 canonical module 拆分；保留 facade smoke |

### 7.1 `corridor_planner.py` 的具體設計問題

1. `RobustControlSpec.pre_viability_problem_hook` 讓純 planner 在 solve 中途啟動
   runtime service；這是 inverted control。
2. `CorridorPlan(frozen=True)` 仍持有 mutable NumPy policy/problem objects；
   nominal immutability 不等於 publication immutability。
3. `_plan_robust_corridor()` 在 coarse empty 後做 full-field refinement；這條
   legacy shadow path 與未來 query-local AMR 不應共用一個模糊開關。
4. legacy forward corridor 與 authority-bearing robust viability 由同一
   `plan_corridor()` 以 `robust_control is None` 分派，讓兩種 claim 很容易混淆。
5. analysis/tests 直接 import `_axis`、`_hazard_clearance_volume`，以及 patch
   `corridor_planner.build_robust_viability_policy`；搬檔會被 implementation-path
   coupling 阻擋。

### 7.2 Live agent 的具體設計問題

1. `choose_action()` 同時是 request validator、hazard preparer、hard
   certifier、beam engine、optional service client、selector 和 result serializer。
2. recursive `_viability_retry` 以再次呼叫 48-argument function 實作 mode
   change，讓 timing、authority 與 metadata binding 難追蹤。
3. `Decision` 在 proposal 和 issue recertification 之間用 `replace()` 演化；
   雖然目前 recertifier 已修，type 本身仍允許舊 action 的 repair/recovery/
   survival fields 留下。
4. backend mode 是 module-level mutable state，測試和多服務容易產生隱藏依賴。
5. `run()` 直接組裝巨大 JSON dict；trace schema 修改會接觸 issue loop。
6. 多個 executor、Future、workspace 的 close/cancel/retire 邏輯集中在
   `finally`，難以單獨測 crash 與 partial initialization。

### 7.3 Native 的具體設計問題

1. `robust_viability_kernel.cpp` 是 unity translation unit；在檔案中段 include
   `robust_transition_table.hpp`，尾段再 include supplemental/pipeline/belief
   implementation headers。
2. headers 依賴先前已定義的 `Sample`、`PipelineLabel`、`TOUHOU_EXPORT` 和
   status constants，並非 self-contained。
3. 同一 binary 暴露 43 個 `touhou_*` symbols，但沒有一個 checked-in
   authoritative ABI header/manifest。
4. C wrappers、legacy v1-v6 adapters、workspace implementation 和 recurrence
   在同檔，任何整理都可能同時改 ABI 與 algorithm。
5. `thread_local viability_worker_limit` 是隱藏 solve input；setter 必須在真正
   native call 的同一 OS thread 執行。

## 8. 目標目錄與模組邊界

這是目標形狀，不要求一個 commit 全部建立：

```text
scripts/
  corridor_planner.py                 # temporary compatibility facade
  th08_live_dodge_agent.py            # CLI + composition root only

  touhou_control/
    corridor/
      model.py                        # bounds, hazards, configs, result types
      grid.py                         # lattice and conservative transfer helpers
      clearance.py                    # scalar oracle and volume protocol
      prepared.py                     # PreparedCorridorProblem
      robust.py                       # robust finite-model solve
      refinement.py                   # explicit strategy interface
      dual_refinement/
        cells.py                      # spatial lower/upper aggregation
        transitions.py                # explicit causal transition lattice
        scope.py                      # exact-root branch relevance
        patch.py                      # query-local dependency closure
        clearance.py                  # patch geometry evaluation
        result.py                     # validated bound artifact
        scalar_solver.py              # independent small-case oracle
        vector_solver.py              # retained dense-rectangle data plane
        guides.py                     # proposal-only work selection
      rollout.py                      # representative path only
      forward_legacy.py               # non-authoritative legacy planner
      api.py

    local_planner/
      model.py                        # request/proposal/node types
      projection.py
      certificate.py
      beam.py
      ranking.py
      planner.py

    native/
      library.py                      # DLL/SO load and status
      arrays.py                       # dtype/contiguity/capacity validation
      geometry.py
      local.py
      viability.py
      pipeline.py
      belief.py

    authority/
      identity.py
      status.py
      issue_transaction.py

  th08_control/
    layout.py                         # TH08 addresses, strides, masks
    model.py
    sensing/
      snapshot.py
      bullet_pool.py
      laser_pool.py
      enemy_pool.py
      item_pool.py
    projection.py
    local_adapter.py
    corridor_adapter.py
    policy_runtime.py
    scene_clock.py
    trace.py
    session.py
```

Native 目標：

```text
native/
  include/touhou_native/
    export.hpp
    status.hpp
    abi.h
    lattice.hpp
    survival_label.hpp

  src/
    geometry/
      clearance_volume.cpp
      trajectory_clearance.cpp
      local_hazards.cpp
    decode/
      bullet_pool.cpp
    local/
      beam_reduce.cpp
      supplemental_workspace.cpp
    viability/
      transition_table.cpp
      boolean.cpp
      safety_value.cpp
      survival.cpp
      losing_labels.cpp
    pipeline/
      direct_workspace.cpp
      belief_workspace.cpp
      query_local.cpp
    abi/
      geometry_abi.cpp
      local_abi.cpp
      viability_abi.cpp
      pipeline_abi.cpp
```

`scripts/tools/build_native_planner.py` 改用 checked-in explicit `SOURCES`，不用
glob。`robust_viability_kernel.cpp` 最終刪除或只留不含 implementation 的
compatibility entry；不能再是 unity include aggregator。

## 9. 必須建立的窄資料契約

### 9.1 `PreparedCorridorProblem`

```text
PreparedCorridorProblem {
  immutable identity/model/terminal digests
  x_axis, y_axis
  clearance lower volume
  optional upper/ambiguity volume
  action and transition model
  exact root enclosure
  preparation timing
}
```

流程改成：

```text
request
  -> prepare_corridor_problem()
  -> optional background prewarm starts from explicit prepared object
  -> solve_prepared_boolean()
  -> optional refinement/metadata
```

這會移除 `pre_viability_problem_hook`，也讓 coarse、AMR、partial survival 和
benchmark 共用同一 immutable input。

### 9.2 Planner artifact、runtime handles、publication 分離

```text
CorridorSolveArtifact      # process-local arrays/policies/diagnostics
CorridorRuntimeHandles     # Future/workspace/service; explicit close()
PolicyPublication          # small immutable consumer payload
```

publication 不得持有 Future、executor、workspace pointer 或 mutable NumPy view。

### 9.3 Local proposal 與 issued decision 分離

```text
LocalPlanRequest
  -> LocalProposal
  -> fresh capture + all-action certificate
  -> IssueTransaction.commit()
  -> IssuedDecision
```

`LocalProposal` 可以含 ranking/shadow diagnostics，但沒有 issue authority。
`IssuedDecision` 的 selected-action metadata 必須從該 action 的 certificate row
重新建構，不可從舊 proposal `replace()`。

### 9.4 Identity

至少包含：

```text
gameplay/clock epoch
source and target physical-frame interval
hazard/model/uncertainty/terminal digests
grid/action/delay/cadence IDs
exact augmented root
absolute deadline and lease
```

identity 應是 value object；cache、publication、trace、candidate witness 使用
同一 canonical encoding。

## 10. 結構線：逐 checkpoint 重構順序

### R0 — Characterization baseline

在搬檔前建立真正保護語義的 baseline：

1. 固定 corridor deterministic fixtures，記錄：
   - clearance sign/selected samples；
   - viable states 和 safe-action masks；
   - path/gate/reason；
   - query-local labels；
   - 排除 wall-time fields 的 canonical digest。
2. 固定 local `LocalProposal/Decision` 的 action、hard components、certificate
   rows 和 issue transaction record。
3. 保存 Linux/Windows native export manifest；目前 Linux 有 43 個
   `touhou_*` exports。
4. 保存 public import compatibility 清單。
5. characterization tests 不測檔案行數、CLI help 或純 schema plumbing。

退出條件：現有 quick suite 和 retained semantic roots 全過；baseline 能在搬檔
後逐位/逐欄位比較。

### R1 — Corridor package

按四個小 checkpoint：

1. **Types/grid/geometry move：**
   - 搬 hazard/config/result types；
   - 搬 scalar grid/clearance helpers；
   - `corridor_planner.py` re-export 舊 public names。
2. **Prepared problem：**
   - 引入 `PreparedCorridorProblem`；
   - prepare 與 Boolean solve 分離；
   - 移除 callback side effect。
3. **Algorithm split：**
   - robust、representative rollout、legacy forward、uniform full-field
     refinement 分檔；
   - 現有 uniform refinement 明確命名 `LegacyFullFieldRefinement`，保持
     shadow-only。
4. **Runtime ownership split：**
   - `CorridorSolution` 拆 artifact/handles/publication；
   - audit writer 和 prewarm lifecycle 離開 solver。

每個 checkpoint 都先保持結果 exact parity；不得順手改 terminal、grid、
ranking 或 timing policy。

### R2 — Python native bindings

1. 把 library load、function cache、status conversion 移入
   `touhou_control.native.library`。
2. 依 geometry/local/viability/pipeline/belief 拆 ctypes signature 與 wrapper。
3. `native_backend.py` 暫時只做 compatibility re-export。
4. array coercion 統一走 typed helpers，但第一輪必須保持現有 copy/
   `ascontiguousarray` 行為；copy elimination 是另一個 performance checkpoint。

退出條件：每個 wrapper 的 dtype、shape、return code、exception 和 optional
symbol fallback 完全相同。

### R3 — Native C++ proper translation units

順序：

1. 先抽 self-contained `export/status/lattice/survival_label` headers；
2. 再把 C ABI wrappers 與 implementation 分開；
3. 依 domain 搬到多個 `.cpp`；
4. legacy v1-v6 wrappers 只適配到 canonical newest internal params；
5. 更新 explicit build source list；
6. 最後移除 unity include order。

本 checkpoint 禁止同時：

- 改 recurrence；
- 改 float comparison；
- 改 worker count/thread pool；
- 做 squared-math/SIMD；
- 改 C ABI。

退出條件：

- 43-symbol export manifest 相同；
- Linux/Windows 都能 rebuild/load；
- scalar/native/semantic parity zero mismatch；
- ASan/UBSan 的 explicit research build 通過；
- quick suite Linux/Windows 通過。

### R4 — Local planner 與 issue transaction

1. 先建立 nested request types，取代 48 個平坦參數：
   - physical/hazard snapshot；
   - actuator pipeline；
   - global guidance；
   - planner config；
   - objective context；
   - optional completed-service results。
2. 拆 `choose_action()`：
   - request validation；
   - hazard preparation；
   - hard preflight；
   - baseline beam；
   - completed supplemental lookup；
   - ranking；
   - proposal assembly。
3. 把 recursive retry 改成顯式 mode/state transition，不重新進入整個 planner。
4. 把 `recertify_action_for_fresh_hazards()` 變成
   `IssueTransaction.commit()`。
5. 分開 `LocalProposal`、`ActionCertificateSet`、`IssuedDecision`、
   `DecisionTelemetry`。
6. root `choose_action()` 暫作 compatibility wrapper，直到所有 tests/
   benchmarks 遷移。

退出條件：

- fresh/global intersection 歷史反例 0 violation；
- action change 後 metadata 逐欄位重綁；
- no-Bomb invariant；
- planner action/hard vector/canonical telemetry parity；
- local timing不因純重構顯著回歸。

### R5 — Live session

Status: lifecycle/resource/sensor/policy/scene/issue/trace modules and the
22-line entry facade are complete. The live loop now consumes immutable
capture, service-update, publication-guidance, and fresh-issue stage records.
Corridor, candidate, decision-control, sensing, timing, and optional-hazard
trace construction is outside the issue path. Fresh enemy-prefix
recertification and ordered deadline/deathbomb/auto-confirm/no-Bomb overrides
also have focused owners. Lunatic Stage-4A/5/6B retention gates completed
with hard no-Bomb, accepted artifacts, and full cleanup; their hits remain
CE-0136/0137/0138/0139 model/recovery evidence. Action alignment, physical
send/no-write, actuator mutation, and outer scene composition remain inside
`_run_live_session`; R5 therefore continues without changing live strategy.

1. 抽 `LiveSession` context manager，只負責資源 acquire/release。
2. 抽 `Sensor`, `PolicyCoordinator`, `SceneClockCoordinator`,
   `IssueController`, `TraceSink`。
3. 一次 iteration 變成有界 stages：

   ```text
   capture
   -> update epoch/services
   -> query immutable publication
   -> local proposal
   -> fresh issue transaction
   -> send
   -> enqueue trace
   ```

4. root `th08_live_dodge_agent.py` 只保留 parser、composition root 和 `main`。
5. 所有 executor/workspace 有單一 owner；close/cancel idempotent。
6. trace record builder 離開 issue path；第一輪仍可同步寫，binary ring 是後續
   performance experiment。

退出條件：

- identity/foreground/route/scene guards unchanged；
- 所有 exception/stop path 都 release keys；
- exact trace fields 和 supervisor behavior parity；
- Windows focused physical no-strategy-change smoke gate。

## 11. 研究線：演算法與 authority 路線

### G0 — Exact-root loss dossier

Status 2026-07-27: **complete** at `e24544d`. The retained dossier
content-addresses all 61 roots and their fresh/terminal dependencies, replays
549 finite variants plus 122 pipeline variants with zero mismatch, reproduces
the 6 spatial and 8 short-horizon observations, isolates 7
`FUTURE_BIRTH_GAP` witnesses, and records 15 same-epoch exhaustion
transitions. CE-0133 rejects assuming that every transition lies inside a
fixed 240-frame window. See
`notes/EXACT_ROOT_LOSS_DOSSIER_20260727.md`.

先擴充現有 61-root audit，而不是先寫新 planner：

1. 保存每個 hit 前首次 kernel exhaustion root，以及之前至少 240 frames 的
   nonempty→empty transition。
2. 對同一 immutable root 做：
   - 16/8/4 px；
   - H=32/48/64/80；
   - uncertainty factor ablation；
   - delay/cadence support；
   - terminal contract；
   - future-birth coverage；
   - exact root/pipeline variant；
   - complete/incomplete solve。
3. 因素可重疊；報告 minimal sufficient rescue combinations。
4. 七個 source capsule 缺少 later contact projectile 的案例單列
   `FUTURE_BIRTH_GAP`，不可和 false-empty 混合。

退出條件：

- 61 roots 可 deterministic replay；
- 已知 6 spatial 和 8 short-horizon observations 可重現；
- timeout/unvisited 沒有被標 empty；
- 每個結論帶 observed/inferred/hypothesized label。

### G1 — Model coverage、pipeline root 與 clock boundary

Status: G1 shadow instrumentation and physical validation complete at
`ff1af3c` / `e4d994f`; CE-0134's recurrence alias is corrected offline.
Full pipeline promotion remains blocked by missing complete-mask
publication/physical integration, fail-closed future-event `model_unknown`,
open CE-0120, and unmeasured representative performance.

這是 live promotion 的 correctness gate，與 offline solver 工作可平行：

1. 將 active/held/pending/remaining-support root 進入 canonical identity。
2. 驗證 multikey transition、no-write carry、one-pending last-write-wins、
   observed pickup 和 estimator continuity。
3. clock sensor 保持 shadow；CE-0120 沒有物理證據前，manager frame freeze 或
   repeated wall threshold 都不能自動 reset authority。
4. 每個 hazard slab 提供 `DETERMINISTIC / FINITE_SUPPORT /
   BOUNDED_ENVELOPE / UNKNOWN` coverage。
5. unknown future event 進入 root-reachable tube 時，截斷 coverage 或標
   model unknown；不能當 free space。

退出條件：independent scalar belief oracle、packed/native parity、Windows
pickup trace 與 focused physical gate 全過，才可討論完整 pipeline live
authority。

Observed closure:

- canonical identity now joins exact float32 observation, complete
  active/held/pending masks, remaining support, and observation/hazard/policy/
  model/clock versions under SHA-256;
- missing or unknown hazard slabs truncate on the first reachable transition;
- Linux/Windows quick suites pass `653/653`, and the scalar/native bounded
  pipeline gates remain green;
- Hard Stage-1 `153821` retained 7,574 valid identities, 3,106 writes, 4,468
  no-writes, 1,513 multikey transactions, 173 last-write-wins replacements,
  92 pending no-write carries, 2,900 native-observed pickups, and zero audit
  failure;
- all 7,574 roots correctly remain future-event `model_unknown`;
- CE-0134 found one pending `right+SHOT -> right` complete-mask write that the
  movement-only recurrence calls no-write. Therefore the evidence gate
  completed by rejecting promotion, not by granting it. G2 remains
  offline/query-local and must not bypass this root-model blocker.
- Correction checkpoint `4b0f959` defines an injective 36-token TH08
  no-Bomb complete-mask alphabet. Equal-velocity Shot/Focus writes remain
  distinct, unsupported/opposed masks fail closed, and all old 17 movement
  projections are preserved.
- Correction checkpoint `7facf80` adds backward-compatible belief ABI v7/v3
  with 64-bit action subsets, while legacy direct/viability and belief
  v1-v6/v1-v2 boundaries stay 32-bit. A six-frame adversarial case proves
  equal-velocity pending identity changes root value, all 36 scalar/native
  action labels match, and best/unresolved masks retain bits above 31.
  Complete-mask recurrence authority is still offline: future hazard coverage,
  CE-0120, representative performance, publication, and live integration are
  not closed.

### G2 — Dual-bound query-local refinement

Status: the offline semantic gate is complete. The implementation preserves
round-to-even cells, lower/intersection and upper/union action masks, explicit
active/selected/delay branches, branch-fixed forward tubes, optimistic
terminal co-reachability, conservative transition-sample closure, and a
one-layer clearance halo. All six retained spatial roots have completed lower
witnesses with zero false-safe or missing-upper action bits and no full-field
patch. Delivery failed: Linux patch construction takes
`3160.63..14153.12 ms` and vector solving `859.02..4008.67 ms`; one root
requires a 77.47% 4-pixel patch. Sparse/native delivery, Windows timing,
publication, cancellation, and shadow gates remain open; no live authority
changed.

在 `PreparedCorridorProblem` 上實作：

1. 先定義 16 px lower/upper cell 和 transition 量詞；
2. exact root forward tube 與 terminal co-reachable tube；
3. 只細化 `L=0,U=1` 且可影響 root action 的 8 px patch；
4. 必要時 4 px，帶 conservative halo；
5. timeout 只發布已完成 lower mask；
6. root-action mask 一旦足以 issue 即停止，不追求全場完成。

hard gate：

```text
L_mixed ⊆ exhaustive_fine_reference ⊆ U_mixed
```

並逐 root action、pipeline plane 和 hidden branch 比較；不能只比較
`state_viable`。

退出條件：

- zero false-safe；
- 六個 known spatial cases 被 sound lower 解釋；**已通過**；
- policy age/delivery 過 Windows gate；**目前實作明確未通過**；
- uniform full-field 4 px 仍不進 live。

Retained evidence:
`notes/G2_QUERY_LOCAL_REFINEMENT_GATE_20260727.md` and
`artifacts/viability_audit/g2_spatial_refinement_gate_20260727.json`.

The G2 implementation is structurally split under
`corridor/dual_refinement/`; `dual_bounds.py`,
`adaptive_refinement.py`, and `refinement_guides.py` remain stable
compatibility facades. This split changes no recurrence or retained result.

### G3 — Exact partial-survival lower witness

延用 formal belief recurrence：

```text
J(s) = 0                                      if current state unsafe
J(s) = 1 + max_action min_hidden J(successor) otherwise
```

要求：

1. exact augmented root；
2. root actions 不受 proposal pruning；
3. continuation policy causal、observation-compatible；
4. 所有要發布的 root action complete；
5. witness 含 worst branch、guaranteed frames、bottleneck、policy digest；
6. exact version/newest-target/complete-only；
7. issue 前仍與 fresh local hard set 交集。

兩個不同 mode：

- `POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS`
- `PARTIAL_WITNESS_ON_UNRESOLVED`

第二個只表示「目前至少有這個可達 lower bound」，不表示完整 horizon 已證明
無解。

進度（2026-07-27，`5e48f3d`）：

- stationary continuation 的 exact scalar recurrence、complete
  all-root-action portfolio、problem/policy/witness digest 和 deterministic
  worst observation-compatible branch 已完成；
- 四組 deterministic/randomized small volumes 逐 root action 與既有
  independent scalar oracle、native belief workspace 完全一致；
- pending no-write、recursive cadence、unsafe-current、mode/tie、digest
  tamper 均有 focused regression；
- 實作已拆為 31-line facade 與 `partial_witness/` 下的
  digest/portfolio/replay/stationary/types owners，沒有新增另一個巨型
  entry point；
- `ba4e66f` 已保留 Stage-4A/6B exact capsule report。兩個 workload 的
  前五個 eligible Boolean-empty roots 都同時提供 full 32-frame、
  17/12-frame partial-on-unresolved 和 zero-prefix stationary 三種
  counterexample；CE-0140 因此拒絕把 Boolean empty 或 stationary
  exhaustion 稱為 unrestricted losing；
- 44-line analysis entry point 已拆至
  `analysis/partial_witness_capsule/` 的 selection/validation、
  serialization、workload owners；報告兩次生成 byte-identical；
- `25d5f68` 已完成 internal native worst-path extraction：belief state／
  observation types、deterministic hidden-branch merge/tie-break 與 path
  extraction 拆至 `native/src/pipeline/belief_stationary_witness.*`；Linux／
  Windows 對 randomized all-root-action、pending no-write、merged support、
  unsafe root 的完整 path 都與 independent Python witness 一致，公開 ABI
  仍精確維持 46 symbols；
- `48f7e56` 已完成 exact complete-mask capsule join 的 offline
  instrumentation：重算 canonical identity digest 與 coverage record，
  重建 active／held／pending root，逐一完成 36 個 no-Bomb root actions，
  worst path replay 並比對 native labels；malformed slab／JSONL／mask／
  delay／provenance 全部 fail closed；
- `20260728_005108` 已補上同時含 canonical complete-mask roots 與
  opted-in capsules 的 retained physical trace。audit 接受 12,986 個
  exact joins，第一個 eligible Boolean-empty root 完成全部 36 root
  actions 並有 full 32-frame stationary witness；
- 同一 audit 拒絕 1,613 個 query/coverage mixed roots，形成 CE-0141。
  `d5866c4` 已把 future coverage root 對齊 canonical `query_frame`；
- post-fix physical run `20260728_020910` 接受 15,069 個 exact joins，
  root validation failure、mixed root 和 missing capsule 均為零，因此
  CE-0141 的 trace construction 已物理關閉；retained contract 與
  Linux／Windows quick suites 通過 `741/741`；
- future-event coverage、background delivery/contention 與任何 physical
  consumer 仍未完成。

### G4 — 更早保存 feasibility

2026-07-28 delivery gate 已在量測前固定於
`STATIONARY_WITNESS_WINDOWS_DELIVERY_CONTRACT_20260728.md`：

- physical Stage-4A exact-root/capsule reservoir；
- workspace create 到 36 root actions complete publication 的 Windows
  latency；
- normal-priority four-worker viability contention；
- 64 組 rapid newest-wins replacement、active cancellation、zero stale／
  partial publication；
- production 46-symbol ABI 不變；
- 任何 pass 只允許後續 default-off trace-only shadow，不允許 action。

同日實作 checkpoint `f8621bd` 完成同 process research DLL、模組化
newest-wins service、36-action immutable publication、active cancellation 與
exact lookup。初始 decode、unpinned repeat、CPU19 E-core 三個變體均保留為
失敗證據。只 pin below-normal proposal worker 到 Windows maximum
efficiency class 的最高 logical CPU（本機 CPU11）後，兩次固定 gate 連續
通過：

- publication p95 `6.913/6.203 ms`，max `11.358/7.977 ms`；
- authoritative viability p95 ratio `1.034/0.938`；
- throughput ratio `0.929/0.961`；
- cancellation ack p95 `0.164/0.168 ms`；
- stale/partial publication `0/0`，production ABI 仍精確 46 symbols。

這只把 G4 delivery 推進到「可另行 review default-off trace-only shadow」；
future-event coverage、CE-0120、earlier immutable completion age 與 fresh
local intersection 仍阻止 action authority。CE-0142
另記錄 physical float32 equal-label hidden tie，不再錯把 tolerant label
parity 當成每個 nature tie field 的逐 bit equality。

不重啟已被 CE-0131 拒絕的 current-issue supplemental lane。新的方案必須在
較早 causal version 中完成：

1. 在 global solve 內或獨立較早 snapshot 計算 continuation/repair metadata；
2. authoritative Boolean mask 先發布；
3. metadata 只有 exact same version 且已完成時才能參與 hard-winning actions
   之間的排序；
4. terminal reserve 先 shadow，因為它可能縮小當前 kernel；
5. 評估 first exhaustion frame、pre-hit lower volume、min branch、
   boundary depth，而不是只看當前 action change；
6. 若需要 process isolation，先由 age ledger/ETW 證明資源 contention。

這是「避免走進後來的 empty」，不是「把已 empty root 說成 viable」。

### G5 — Future hazard event coverage

進度（2026-07-28，`48f7e56`）：

- exact physical root/capsule join 與 36-action stationary audit 已完成；
- `UNKNOWN` future-event slab 會把結果標為 `model_unknown`，即使 retained
  finite capsule 內存在完整 witness，也保持 `physical_action_authority =
  none`；
- 帶 `--viability-audit` 的 focused Lunatic Stage-4A physical evidence
  gate 已由 `20260728_005108` 完成，保留同一 session 的 canonical
  roots、capsules 與 compact report；
- 該 run 接受 12,986 joins、零 missing capsules；保留的 root 完成 36
  actions、32-frame witness、native zero mismatch，但 coverage 從第一個
  successor 即為 `UNKNOWN`；
- CE-0141 的 1,613 mixed-root rows 已 offline 修正；post-fix physical
  trace `20260728_020910` 的 15,069 joins 全部通過且 zero mixed roots，
  trace construction gate 已關閉；
- bullet-birth 第一個 gate 已由
  `TH08_FUTURE_BULLET_BIRTH_OBSERVATION_CONTRACT_20260728.md` 固定：
  先用既有 persistent pool blob 的 native age 做 retrospective birth
  observation，再與較早 ECL intent 及 same-frame update order 對齊；預設
  關閉、trace-only、不新增 RPM、不改 planner `Bullet`，也不縮小
  first-successor `UNKNOWN`；
- B1 checkpoint `4260113` 已加入獨立 pool-blob age observer；5,000 次
  Linux/Windows full-pool gate 的 p95 為 `0.0318/0.0339 ms`、p99
  `0.0540/0.0453 ms`、max `0.3199/0.1005 ms`，與 planning decode
  交錯的 p95 ratio 為 `0.998/1.007`；B1 當時尚未接入 controller，
  後續 B3/integration checkpoint 見下；
- B2 checkpoint `c3c5a83` 補齊獨立 base-state oracle 的 full-pool
  drop-before-release、next-pass cursor reuse、same-frame move/contact 與
  collision-suppressed birth。這是 IDA-supported executable fixture，不是
  shipped-runtime birth/contact 證據；
- B3 checkpoint `52d0864` 已加入 fail-closed active-spell main-VM
  classifier；只沿 literal path，對 control/source/emission-state 邊界
  停止，並保留 aimed、RNG、dynamic、deferred、pool、template、origin
  等 residual dependencies，不產生未證明的 future geometry；
- checkpoint `98db592` 已用 `--trace-bullet-births` 將 B1/B3 接成
  default-off post-issue audit。它復用既有 pool blob、VM snapshot 與
  instruction cache，epoch reset 完整，Linux/Windows quick suite
  `773/773` 通過；下一步是 B4 Stage-4A physical trace 與 B5
  deterministic residual report；
- B4 首次實機 `20260728_031127` 暴露 CE-0143/0144：observer 在實機
  爭用下 p95 `1.7795 ms`，而 integration 丟失既有 enemy
  `+0x3324` deferred-fire bit，導致 1,641 intents 全部 untimed。
  schema v2 已以 exact capture alignment 傳遞該 bit，所有 optional
  工作移到 current dispatch 後，cold ECL cache miss 直接 fail closed；
- observer scratch-reuse 已把 Linux/Windows steady full-pool p95 降到
  `0.0171/0.0242 ms`，但 592-birth burst p95 仍為
  `2.2671/2.7465 ms`；下一次 B4 會新增 build/pre-emit timing，不能把
  output-linear serialization 或 physical contention 隱藏在 timing
  boundary 外；
- schema v2 實機 `20260728_040144` 已驗證 deferred-state 修復並產生
  timed intent，但 observer p95/p99 `0.4496/0.9314 ms` 仍失敗，且
  temporal match 只在 spell 69；schema v3 改用完整 columnar evidence，
  592-birth Linux/Windows observer p95 降到 `0.1704/0.1528 ms`，JSON
  payload `160077 -> 32956` bytes，保留 scalar 與 v2/v3 parity；
- per-phase residual 找到合法 12-byte header-only ECL instruction 被錯誤
  轉成 zero-byte RPM，且 broad exception 同時丟失已讀 VM snapshot；
  parser 與 modular `th08_live.ecl_capture` 已修，schema-v3 實機
  `20260728_043724` 的 6,101 active-spell rows 全部恢復 classification，
  spell 61 新增 3,054 temporal matches；
- schema-v3 B4 仍以 observer p95/p99/max
  `0.3413/0.6625/10.6158 ms` 失敗；evidence row immediate flush 另造成
  `1.3307..1.9791 ms` emit p95。下一步是 bounded durability flush、
  CPU/wall 分離及 small-candidate gather，不弱化原 gate；
- schema v4 已把 evidence immediate flush 改為 error-immediate 加
  same-iteration decision flush，並同時記錄 thread CPU/wall；1/8/32
  candidate Linux/Windows p95 已降至 `0.0578/0.0627/0.1038` 與
  `0.0495/0.0790/0.0963 ms`。實機 `20260728_050305` 完成 Stage 4A、
  12 hits、hard no-Bomb 與 cleanup；previous emit p95
  `1.1783 -> 0.1708 ms`，但 observer wall p95/p99/max 仍為
  `0.2997/0.5772/10.2234 ms`，B4 不通過。Windows thread CPU 以
  15.625-ms 量化，不能替代 wall gate；下一個 performance experiment
  應比較 parity-gated native extraction 與 exact active-slot handoff，
  移除重複 sparse pool traversal，同時保留 Python scalar oracle、完整
  ordered evidence、no extra RPM 與 fixed wall limits；
- separate trace-only native extractor 已完成，production planner ABI
  不變；16-generation/full-1,536-slot Linux/Windows differential、nonfinite
  geometry、reset/validation 與 atomic error 均通過。第一版 ctypes wrapper
  在 call 1,741 觸發 5.409-ms cyclic-GC tail，CPU-11 affinity 仍失敗；
  persistent blob view/pointers/count storage reuse 在 GC 開啟下將同一
  5,000-call max 降到 0.0988 ms。最終 full-density p95
  `0.0120/0.0109 ms`、592-birth p95 `0.0570/0.0452 ms`，8 profiles
  全過 fixed gate。schema v5 強制 backend provenance；這只允許顯式
  native Stage-4A recheck。實機 `20260728_055104` 將
  p50/p95/p99 降到 `0.0545/0.1393/0.2111 ms`，但 p99.9/max 仍為
  `2.3779/9.0498 ms`；16 個超過 2 ms 的樣本中 10 個是 zero evidence，
  其餘只有 4/6/20 rows，因此不是大 burst output-linear 問題。下一步
  必須分離 native call/materialization 並記錄 overlapping GC，在不關
  GC、不 pin controller、不放寬 max 的條件下定位 CE-0149。schema v6
  已完成這個 split/GC telemetry；forced gen-0 collection attribution、
  fail-closed audit 與 Linux/Windows `797/797` 通過。另發現舊 decode
  ratio 用前後兩個 blocks，Windows identical adjacent runs 會
  `1.077 fail -> 0.940 pass`；CE-0150 改為 iteration 內 ABBA paired
  means 後 Linux/Windows/Windows-repeat 為
  `1.012/1.016/1.025`，均在原 `1.05` gate 內。下一步是 schema-v6
  Stage-4A attribution physical run；該 run `20260728_062321` 已完成
  14,868 decisions、17 hits、hard no-Bomb 與 cleanup。observer
  p50/p95/p99/p99.9/max 為
  `0.0648/0.1493/0.2245/2.1568/8.3514 ms`，仍只在 max 失敗；17 個
  超過 2 ms 的樣本全部由 native-call wall interval 主導，其
  p50/p95/p99/p99.9/max 為
  `0.0365/0.0603/0.1125/2.1281/8.2585 ms`。14,868 rows 的所有
  phase/generation completed-GC counts 都是 0，prepare/materialize/residual
  max 只有 `0.0703/0.7076/0.2362 ms`。因此下一個 performance correction
  是保持同一 C++ recurrence/output、GC、unpinned controller 與 fixed
  wall gate 的 GIL-held/released call-boundary A/B，不再猜 Python copy/GC；
  該 A/B 已以 mode-specific `CDLL`/`PyDLL`、trace schema v7 與
  residual-audit v5 實作；16-generation full-pool 三方 parity 與
  fail-closed provenance 通過。Linux released/held full-density p95
  `0.0119/0.0109 ms`、592-birth p95 `0.0598/0.0588 ms`、ABBA ratio
  `1.0166/1.0293`；Windows 為 `0.0118/0.0098 ms`、
  `0.0465/0.0452 ms`、`1.0382/1.0181`，全部不綁核通過。下一步是第一個
  explicit `gil-held` Stage-4A diagnostic；需要連續兩個完整 physical
  pass 才能關閉 B4；第一個 held run `20260728_065316` 已在 13,896
  observations 上以 p50/p95/p99/p99.9/max
  `0.0659/0.1475/0.2021/0.4001/1.0595 ms` 通過，native-call max 從
  released physical 的 `8.2585` 降到 `0.5008 ms`，zero >2-ms samples、
  zero completed GC；cadence 仍為 2/3 frames，local-plan p50/p95
  `9.764/17.910 ms`。CE-0151 修正 audit-v5 只 validate schema v7 卻在
  aggregation 用 `==6` 丟掉 diagnostics 的 report-only bug；同一 raw
  已 deterministic 重建。第二個 held run `20260728_070838` 也完成
  15,011 observations、15 hits、hard no-Bomb 與 cleanup；其
  p50/p95/p99/p99.9/max 為
  `0.0632/0.1420/0.1967/0.3999/0.9087 ms`，native-call max
  `0.4384 ms`，同樣 zero >2-ms samples、zero completed GC。連續兩次
  held physical pass 共 28,907 observations，因此在 declared
  retrospective observer boundary 內關閉 B4 native-call tail。這不是
  survival promotion：9/15 hits 是 RNG/trajectory/resource-distinct，且
  24 個 contacts 全部發生在 global viability exhaustion 之後；
- CE-0147 顯示 spell 57 的 1,261 rows 全部掃滿 256 callback
  instructions、未覆蓋 horizon 卻輸出可被 live lowering 消費的空 event
  list。這是 unknown-direction future-transform approximation；必須改成
  explicit incomplete/`UNKNOWN`，不能用降低 instruction cap 假裝解決；
- CE-0147 的第一層 consumption 修復已完成：callback 與 birth-intent
  traversal 都輸出 exact frame-support 的 `COMPLETE`/`UNKNOWN`，live
  lowering 只能取得 `complete_events`，prefix 只留 trace；舊 wrapper
  對 incomplete 直接拋錯。schema v8/audit v6 會驗證 stop reason、
  support、result kind 與 lowering status。重審 `20260728_070838`
  得到 3,723 legacy complete、2,405 legacy unknown；975 個 unknown
  rows 有 tagged bullets，max 1,367。Linux/Windows `806/806` 通過。
  這只修正 optimistic consumption，unknown suffix 的 repeated-state
  proof／conservative envelope／certificate-unavailable 三選一仍未完成；
- schema-v8 實機 `20260728_075455` 已在 14,903 rows／6,089
  active-main-VM joins 上驗證 consumption：3,763 complete、2,326
  unknown，所有 unknown 都是 prefix-not-lowered；spell 57 有 1,313
  instruction-limit unknown，spell 73 有 1,013 repeated-state unknown 與
  125 complete。936 個 incomplete rows 有 tagged bullets，max 1,360。
  但同一 run 暴露 CE-0152：observer 唯一 >2-ms row 是 24-evidence
  materialization `8.9333 ms`，native call `0.0335 ms`、zero completed GC；
  因此 B4 performance regression 重新打開。
  `G5_MATERIALIZATION_TAIL_ATTRIBUTION_CONTRACT_20260728.md` 已先固定
  telemetry-only 邊界：用 thread-cycle delta 與三個 background future
  的 before/after state 區分實際 copy cost／deschedule，再另立 contract
  決定 copy packing 或 worker isolation，不靠重跑挑一個 passing max；
- schema-v9/audit-v7 已實作上述邊界：Windows 的 cached GIL-held
  `QueryThreadCycleTime` 提供三段 raw cycle delta，controller 的
  corridor/survival/enemy Future endpoint lookup 全部包含在原 observer
  wall interval。Linux/Windows 八個 overhead profiles 與 ABBA gate
  通過，完整 quick suite 為 `812/812`。GIL-held schema-v9 Stage-4A
  實機 `20260728_083433` 隨後在 p95/max `0.2039/5.1274 ms` 再次失敗；
  唯三的 endpoint transitions 全是 corridor Future `inflight -> done`，
  也恰好是全 run 最大三個 materialization walls
  `5.0415/4.2546/1.1657 ms`。其中兩個 cycle count 普通，另一個是
  run-wide max，支持 completion/GIL handoff 加 mixed executed work，
  不支持 output-size 說法，也還不是 worker causality proof。下一步先
  固定 default-off corridor-worker-priority intervention contract，並用
  publication age、viable-query coverage、observer wall 與 survival
  作 rejection gates。該 contract
  `G5_CORRIDOR_COMPLETION_PRIORITY_EXPERIMENT_20260728.md` 現已在 code
  前固定：只降低 Python corridor parent，四個 native workers、
  recurrence、cadence、issue/fallback 全不變；要求 applied provenance、
  至少一個 completion transition，及兩個連續完整 physical passes；
  這不增加 action authority。該 default-off option、fail-loud check、
  supervisor forwarding 與 deterministic raw-trace audit 已實作；
  Linux/Windows 完整 suite 和 observer/ABBA gate 通過且 native/ABI
  未改。priority-on Stage-4A run `20260728_092619` 雖然把 observer
  max 降到 `0.8925 ms`，但 p95 `0.2049 ms`、expired fraction
  `0.2472%` 超過 fixed gates，且沒有任何 `inflight -> done` witness；
  因此 intervention 已拒絕、不跑第二遍，不能把單一 lower max 當作
  performance 結論；
- spell-57 callback traversal 本身 p95/max `0.5460/10.3328 ms`，即使
  fail-closed 也仍在 issue thread。IDA 後續確認 spell 73 的
  `jump_float_ge` 讀取動態 player/enemy distance `10050`，spell 57 的
  `0x05` 則依賴 snapshot 未包含的 local/RNG loop state，故 naive
  exact-state memoization 已拒絕。CE-0154 修正已讓 callback scanner 在
  unsupported timer/control 當場 fail closed，不降低 256 cap，也不加
  stage shortcut。重放 retained `20260728_092619` 的 5,788/5,803
  callback rows 發現 1,996 個舊 complete spell-61/65 rows 曾跨越
  unmodeled branch；修正後 zero unknown->complete，總 instruction
  `563,466 -> 58,204`（-89.67%），spell 57
  `344,320 -> 3,155`（-99.08%）。Linux/Windows shipped workload
  spell-57 p95 `0.0223/0.0307 ms`，完整 suite 823/823 通過。15 個 late
  transition rows 因 retained decoded image 與當時 runtime bytes
  不對齊而未能 replay，audit 故意 fail all-rows gate；下一步先用 fresh
  physical trace 關閉 exact runtime scope，再研究 dependency-complete
  transfer summary；
- fresh normal-priority Stage-4A run `20260728_101804` now closes that
  runtime scope over all 5,749 callback rows: 1,442 complete horizon
  schedules, 4,307 fail-closed unsupported-control unknowns, no legacy
  instruction-limit/repeated-state stops, and 25/25 valid phase-end rows.
  Spell 57 stops on control in all 1,308 rows with at most 26 instructions.
  The route completed with 13 hits and hard no-Bomb; every contact follows
  global viability exhaustion, so this is correctness/performance evidence,
  not survival promotion. The observer still misses the fixed p95 gate by
  `0.0018 ms` (`0.2018 > 0.2000`) with max `0.7539 ms`, no GC, and no
  endpoint transition. Next contract a capture-aligned VM-local interpreter
  for only an independently verified opcode subset; all dynamic motion,
  uncaptured RNG, call-stack, and interrupt dependencies remain `UNKNOWN`;
- that next contract is now
  `G5_CAPTURE_ALIGNED_VM_LOCAL_SHADOW_CONTRACT_20260728.md`. Phase A only
  retains a compact raw-bit projection from the already existing VM RPM call,
  growing it `0x40 -> 0x68` bytes without changing live analysis. IDA maps
  `10036..10039` to context `+0x58..+0x64` and confirms `0x05` uses the
  post-decrement value. Call/return copies the full `0x228` context and stays
  unsupported. A fresh projected physical trace and independent scalar
  oracle are mandatory before candidate completion or live lowering;
- phase A is now implemented and offline-validated on Linux/Windows. The
  one-call capture/bit-parity gates and all 832 tests pass; isolated projection
  decode median is about `3.9 us` Linux and `4.8 us` Windows. These timings are
  descriptive. Fresh Stage-4A run `20260728_110438` validates all 5,615
  physical projections and observes 12/33/13 distinct `10036` values in
  spells 57/61/65. Coverage remains 1,490 complete / 4,125 unknown. B4 still
  fails at `0.2059 ms` p95, so next build only the independent offline scalar
  oracle while separately attributing matched-path performance;
- the phase-B1 shadow is now modularized under `scripts/th08_ecl_shadow/`.
  An independent test-only raw-tuple/plain-dict oracle agrees on signed-int32
  loop counters, wrap, timer/PC/final locals, and local-aware repeated-state
  detection. Shipped spell-57 integration resolves one `0x05`, then stops
  before direct-fire or RNG. Float add/normalize remains deliberately unknown
  until its rounding path has an independent oracle. No live import or
  authority changed;
- retained physical replay of `20260728_110438` now accounts for all 3,117
  in-scope unknown spell-57/61/65 rows and keeps the 1,008 dynamic spell-73
  rows excluded. It observes 1,730 initial `0x05` rows, canonicalizes them to
  108 unique physical one-step cases, and agrees with the independent oracle
  on every transition. Zero unknown row becomes a verified complete
  schedule. The deterministic replay/fixture hashes are `b280467b...920f`
  and `6c34d097...ab3c`; isolated Linux/Windows one-step p50 is about
  `8.51/10.08 us`. This closes implementation parity for that one
  instruction only, not B4, callback completeness, future-hazard coverage,
  survival, or action authority. Next perform matched live-path attribution
  and establish an independent binary32 oracle before adding float
  add/normalization;
- the parallel B4 line now has a fixed matched-path performance contract.
  Regrouping the same 13,525 physical rows gives zero/nonzero-evidence p95
  `0.1553/0.2516 ms` and no-known/definite-known-future-overlap p95
  `0.2015/0.2112 ms`. Thus nonzero materialization plus fixed telemetry is
  the first systematic target; another priority experiment is not justified.
  The first patch may only remove generator/tuple overhead from exact
  Windows cycle-delta bookkeeping. Both future endpoints, diagnostics, GIL,
  GC, wall boundary, workers, and records remain unchanged. That first patch
  now passes all parity/provenance gates: Windows maximum exact-wrapper p95
  improves `0.04872 -> 0.04680 ms`, repeated at `0.04410 ms`, while Linux
  remains flat. Because physical B4 missed by only `0.0059 ms`, run one fresh
  unchanged normal-priority Stage-4A gate before considering more invasive
  batch-validation or worker changes;
- that physical gate `20260728_121028` now passes p95/p99 at
  `0.1986/0.3400 ms` but fails the unchanged `2.00 ms` maximum with
  `8.3269 ms`. Both over-budget rows are materialization intervals: one has
  ordinary same-cohort current-thread cycles, while one has the run-wide
  maximum cycles and a corridor `inflight -> done` transition. Keep B4 open,
  retain the narrow optimization, and do not retry the rejected priority
  intervention. Before dropping batch validation, fix a native-output
  invariant/failure contract; before process isolation, fix a causal
  delivery/contamination experiment;
- the same trace adds a static-replay evidence rule: after the first
  decoded-file/runtime-image mismatch, all later rows are mapping-unknown
  even if stale bytes decode plausibly. The corrected auditor excludes 27
  late spell-73 rows and deliberately remains failed. Recover them only with
  retained raw instruction bytes or immutable runtime-image identity;
- the next profile-triggered materialization patch retains all batch
  validation/read-only semantics while removing nested prefix-copy calls and
  one finite-flag allocation. Identical profiler work falls
  `1,468,272/1.632 s -> 1,395,171/1.543 s`. Linux's 23-profile gate passes;
  the first Windows ABBA ratio fails narrowly, then two adjacent complete
  repeats pass. This is deterministic work reduction, not a physical B4
  closure. Use Stage 5 only as a harder transfer workload and keep the
  Stage-4A maximum failure open;
- the Stage-5 transfer workload `20260728_124930` now passes B4 on all 13,326
  observations at `0.0973/0.1936/0.3387/0.5376/0.8346 ms`
  p50/p95/p99/p99.9/max with zero completed GC. This retains the optimized
  data path but does not erase CE-0156. The same run has 15 hits, all after
  global viability exhaustion. Earlier short empty episodes recover; the
  viable-to-losing transition of the episode containing the canonical first
  hit starts a 118-frame loss-to-hit interval. Therefore the next
  hit-reduction work is not another aggregate heuristic tune: retain this
  immutable pre-hit loss bracket and compare completed G3/G4 partial-survival
  witnesses per root action. Unvisited or timed-out actions remain unresolved;
- the pre-hit loss experiment is implemented offline. The existing Stage-5
  trace correctly stops unresolved at frame 2049 because it has no viability
  capsules, after counting 15 earlier recovered loss episodes. A
  capsule-bearing Stage-4A implementation gate selects
  `1039 viable -> 1041 losing` before the frame-1099 hit and completes both
  `36 x 36` portfolios with zero scalar/native mismatch. Its issued losing
  mask `0x45` retains only five finite-model frames while `0x50/0x51` retain
  32, but both roots are `model_unknown` from the first successor. This
  validates the discriminator without authorizing a physical conclusion.
  The fresh capsule-enabled Stage-5 gate `20260728_133633` is now complete:
  it selects `3750 viable -> 3752 losing`, 275 frames before the frame-4027
  hit, after 24 recovered episodes. Both `36 x 36` portfolios pass with zero
  parity mismatch. Issued G4/G3 masks `0x55/0x85` retain `30/22` frames
  versus best `0x10/0x11` and `0x20/0x21` at 32. Because both roots are
  `UNKNOWN` from the first successor, the next gate is G5 causal future-hazard
  coverage, not live recovery tuning;
- CE-0159 fixes a separate evidence-boundary defect: unreachable
  `lane=none` plans previously emitted `-Infinity`, making raw and compact
  outputs non-standard JSON. Future trace adapters emit `null` for that known
  sentinel and every JSON publication boundary rejects other nonfinite
  values. Linux/Windows representative strict-encoding overhead is only
  about `0.003/0.008 ms`, but a post-fix no-capsule physical timing gate is
  still required before a B4 conclusion;
- action-free realized provenance is now complete for all 15 hits in Stage-5
  `20260728_124930`. The modular analyzer performs one strict raw-trace pass,
  joins each hit through its exact gameplay epoch, and keeps exact observed
  overlaps separate from nearest-only context. Four hits have exact overlap
  candidates and eleven are nearest-only. The canonical exact overlap
  activated before loss; one later slot-1295 member of a 30-bullet nonspell
  wave activated at native support `13868..13869`, after loss frame 13864,
  and overlapped exactly at frame 14043. No captured intent covers that wave,
  because the current scope is spell-main-VM-only. This fixes a concrete next
  G5 target—contract nonspell source topology—without claiming every hit is a
  birth failure, future coverage, a containing envelope, or action authority.
  Earlier viability preservation and the still-open Stage-4A B4 maximum
  performance gate continue in parallel;
- the first ready-derived-parent source hypothesis is physically rejected.
  Stage-5 run `20260728_150827` reproduced the target two-age waves but all
  11,801 source rows contain zero ready parents, and the separate second scan
  fails the combined p95/p99/max budget. Keep it isolated and do not optimize
  a zero-signal source class into production;
- ordinary main-VM phase A is now physically complete on retained Stage-5 run
  `20260728_155426`. Its schema-v11 inventory is modular, reuses the existing
  first-64 enemy blob, and performs no added pool RPM. All 64 unique physical
  PCs share one complete affine mapping to decoded Stage-5 ECL boundaries.
  Twenty exact direct-fire PC advances align one-to-one with 260 realized
  bullets. IDA and 81 exact opcode-`0x87` advances expose the higher-value
  missing topology: four auxiliary VM contexts rooted at `enemy+0x3384`,
  whose immediate availability overlaps 105 activation batches and 1,520
  bullets. This is strong source availability, not runtime-byte, reachable
  path, geometry, or hit proof. Combined observer p95 is `0.2029 ms`, a
  narrow physical miss to optimize rather than a reason to discard the
  capability. Next retain auxiliary pointers from the already-paid blob,
  contract bounded context capture, and key exact runtime instructions by an
  immutable ECL image before any live lowering;
- the projection audit now has an explicit universal `core` profile and keeps
  Stage-4A-only spell gates as its default. Stage 5 passes all core gates over
  4,871 rows while retaining 1,220 spell-115 unsupported-control rows as
  `UNKNOWN`. This makes Stage-5/6 projection evidence comparable without
  weakening the original Stage-4A acceptance workload;
- 這只完成 coverage plumbing，不代表以下任何 event class 已建模。

逐事件類做，不建立一個未驗證的萬能 ECL simulator：

1. birth；
2. stop/resume；
3. redirect/reversal；
4. laser width/length/phase；
5. player-aim dependency；
6. enemy-body contact enable/disable；
7. unknown callback。

每類都要有 IDA/static conclusion、native runtime trace、update-order fixture、
semantic fuzzer 和 retained residual report。靜態分析結論標 inferred，runtime
trace 才是 observed。

## 12. Performance 路線

### 現在就做

- 在 trace module 抽出後加 record-only QPC age ledger；
- 報 p50/p95/p99/p99.9/max、deadline slack、cancelled work；
- 分 capture/read/decode/queue/solve/publish/pickup/cert/commit/send；
- 保留 persistent RPM destination buffer；
- 記錄 actual worker count 和 executor/native oversubscription。
- 把已關閉的 G5 observer B4 `0.20/0.40/2.00 ms` boundary 保留為
  regression gate；後續 schema-v8 與 Stage-5/6 trace 都要重新報
  p50/p95/p99/p99.9/max，不能因研究線切換而停止性能驗證。
- 目前全庫 Ruff 有 33 個既有結構化/lint debt，集中在 facade re-export
  未標示、Windows `sys.path` bootstrap 的 E402、少量未用 import 與
  lambda style。按模組重構 checkpoint 分批清理，不與語義修復混提交，
  也不盲目刪除 compatibility re-export。

### 只有 profile 觸發才做

- prepared main-beam native workspace；
- hard/soft geometry split；
- scratch reuse；
- persistent worker team；
- process/shared-memory isolation；
- CPU affinity；
- adaptive full/sparse reads；
- SIMD/PGO/LTO。

### recurrence 穩定後才做

- bitset Boolean predecessor；
- dirty-cone rolling repair；
- occupancy/EDT；
- event-aligned time layers。

每個 optimization 必須單獨提交。只要 hard mask 變化，就按 algorithm change
審查，不得叫「純效能 patch」。

## 13. 最先執行的六個 code checkpoints

1. **Corridor characterization + package skeleton。**
   不改結果，建立 canonical digests 和 compatibility facade。
2. **Corridor types/grid/clearance extraction。**
   將 game-neutral code 移入 `touhou_control.corridor`。
3. **Prepared problem + solve/runtime split。**
   移除 `pre_viability_problem_hook`，分開 artifact/handles/publication。
4. **G0 loss dossier v2。**
   用新的 prepared seam 重放 61 roots 和 first-exhaustion windows。
5. **Python native binding split，再做 C++ multi-TU split。**
   先 bindings、後 binary；兩個獨立 checkpoints。
6. **LocalPlanRequest/LocalProposal/IssuedDecision extraction。**
   然後才拆 live `run()`。

G2/G3 的 algorithm implementation 在第 3–4 步的資料契約穩定後開始；不必
等待整個 live agent 重構完成。R5 完成前，任何新 live authority promotion
仍需額外審查。

## 14. 驗證矩陣

| 變更 | 最小 gate | 完整 gate |
| --- | --- | --- |
| Python 純搬檔 | focused owner tests、canonical digest、`git diff --check` | Linux quick suite |
| corridor API split | corridor/runtime/adapter tests、61-root replay sample | full quick suite |
| Python native bindings | wrapper tests、native load、semantic differential | Linux + Windows quick |
| C++ multi-TU | build、43 exports、focused native/oracle | ASan/UBSan research + Linux/Windows quick |
| local planner split | local/certificate/beam/issue property tests | semantic gate + Windows direct roots |
| issue transaction | historical outside-mask/metadata counterexamples | focused physical transaction gate |
| algorithm mask change | independent oracle、adversarial corpus | retained roots + Windows delivery + focused physical |
| process/IPC | torn-read/crash/latest-wins tests | ETW paired Windows gate |

結構 checkpoint 不需要 full physical route；策略、model、authority 或 delivery
行為一旦改變，才進 focused physical gate，再決定是否 full route。

## 15. Stop rules

遇到以下任一情況立即停止 promotion並縮小 counterexample：

1. hard safe-action mask、clearance sign、transition endpoint 或 root label mismatch；
2. action 換了但 metadata 仍來自舊 action；
3. lower/upper containment 失敗；
4. timeout/cancel/unvisited 被標為 empty；
5. exact version/root/epoch/lease 不一致；
6. p99 改善但 policy age、deadline miss 或 game contention 惡化；
7. model confidence 不足卻擴大 horizon authority；
8. process crash/torn publication 可被 issue consumer 接受；
9. 新的 native hit、Bomb、missed transition 或 clock counterexample。

不要為了讓重構通過而弱化測試，也不要用舊 trace 的有限欄位推導未保留的
alternate-action hard safety。

## 16. 明確不做的事

- 不做整倉 C++ rewrite。
- 不在重構 commit 中改策略排序。
- 不把 `corridor_planner.py` 直接刪掉而一次改完所有 import。
- 不用行數測試代替 behavior tests。
- 不讓 analysis/benchmark import canonical module 的 private underscore
  helpers；需要的能力升格成明確 research API。
- 不讓 `CorridorSolution`、Future 或 native workspace 穿過 process
  publication boundary。
- 不把 terminal heuristic、upper set、learned score 或 SIPP proposal 當
  live lower authority。
- 不重啟 CE-0131 已拒絕的 current-issue supplemental 實作。

## 17. 最終路線摘要

最終採用的路線是：

1. 先把可重放行為與 ABI 鎖住；
2. 先拆 corridor，建立 prepared immutable problem；
3. 再拆 Python native binding 與 C++ translation units；
4. 再把 local proposal、fresh certificate、issue transaction 分型；
5. 最後把 live loop 縮成清楚的 session stages；
6. 演算法先做 exact-root loss dossier 和正交狀態；
7. 再做 sound lower/upper query-local refinement；
8. 同時建立 exact partial-survival lower witness；
9. pre-loss reserve 只從較早 global causal version 回來，不走 current-issue
   supplemental；
10. model coverage、clock/pipeline correctness 和 Windows delivery gate
    決定能否 promotion；
11. bitset、incremental、SIMD、process isolation 都是後續加速器，不是當前
    核心答案。

這條路線既直接針對 38/39 post-empty contacts，也降低下一輪研究把 model、
algorithm、delivery 與 code movement 混為一談的風險。
