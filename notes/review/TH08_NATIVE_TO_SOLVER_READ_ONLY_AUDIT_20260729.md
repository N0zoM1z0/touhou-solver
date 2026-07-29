# TH08 Native-To-Solver／IDA 唯讀審計

日期：2026-07-29
工作區：`/home/pentester/coding/codex_ida/th08`
原始暫存來源：`/tmp/ths_analysis.md`（移入 repository 前 SHA-256
`6e5a81f41ef4866c294ef0ab5db937efe614de2b8a3179a559fc878b4a65cb21`）
審計範圍：現有 IDA 命名、型別、註釋、靜態語義主張，以及承接這些主張的 Python／C++ 實作。
限制：唯讀；不修改 repository、IDA database 或物理控制 authority；不使用 REA。
審計快照：branch `main`，HEAD
`d85cca19060f8b95dcdd5924f5caedca33f8d391`；最新已接受完整物理 workload
為 `lunatic_route2_stage5_unattended_20260729_125453`。工作樹同時由其他
agent更新文件／artifact；本審計沒有修改或stage其中任何內容。

## 證據標籤

- **Observed**：直接由目前 shipped executable bytes、IDA instructions/dataflow、
  repository source 或已保留 runtime evidence 看見。
- **Inferred**：由多個 observed fact 支持，但尚非完整 runtime proof。
- **Hypothesized**：合理候選，仍缺關鍵證據。

## 執行摘要

結論不是「整套分析錯了」，也不是「Python/C++ parity足以證明正確」。
核心 binary身分、`10036..10039` scratch locals、`10050` distance、
runtime-ECL relocation、default SHT shot公式及 boss-width反縮放均經指令級
重驗成立；但目前 solver仍有數個會影響 model authority的原生語義缺口。

最應優先處理的 correctness 問題是：

1. **F-013**：live player transition不乘 global time scale；slowdown時可把
   native可達距離高估2–4倍，方向是unsafe optimistic；
2. **F-011**：enemy contact可由本幀 Focus／secondary-character action切換，
   但 recurrence把 geometry當 action-independent；Stage-5已有16-body、
   10-frame retained witness；
3. **F-010/F-014**：laser projection漏 time scale／float32 timer，碰撞又把
   native rotated AABB改成capsule，既非exact也非單向保守；
4. **F-007**：VM-local shadow與名義上的獨立oracle共同實作了錯的 opcode
   `0x04/0x05` timer transition，parity是共同錯誤；
5. **F-008/F-017**：未命名 callback table中仍有 custom lethal rectangles、
   freeze、bullet→enemy birth及slowdown；route-2 focused normal shots另有
   action-dependent shared RNG consumer，future-birth因果模型尚不完整；
6. **F-012/F-015/F-019**：player lethal half extent、bullet lifecycle
   state 5、callback collision-suppression gate均被過度保守建模，會壓縮
   viable set並增加計算；它們不應被誤說成現成的unsafe false negative；
7. **F-018**：trace-only native observer對 `INT_MAX` queue cursor可直接
   SIGSEGV；雖沒有 action authority，仍可能殺死controller process。

效能上，最值得做的是 **P-001**：active no-item native beam每個10-step
request仍明示配置約190個NumPy buffers並在Python建draft tuples；retained
physical telemetry的beam/search仍是local planner最大可歸因熱點。先修上述
物理語義，再以完全相同的rank/certificate contract做persistent SoA或fused
native step，收益比繼續微調已約1–3 ms的certificate geometry更可信。

本報告共列20項 findings（含兩項可重現 native robustness crash/parity
缺陷）、3項正面 revalidation及3項性能結論。每項均區分
Observed／Inferred／Hypothesized及目前 authority邊界。

## F-001 — IDB 輸入雜湊不同，但可精確解釋為已知單位元組 patch

嚴重度：資訊性／邊界風險（已釐清）
狀態：**Observed**

- 連線中的 IDA metadata：
  - path：`D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)\th08.exe`
  - base：`0x00400000`
  - file size：`840704`
  - SHA-256：`ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`
  - MD5：`454c96e08fe3c14df7064d104c26accf`
- `START_HERE.md` 與目前磁碟上的物理 target：
  - SHA-256：
    `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
  - MD5：`77b6785e04a3406e50be68714a193650`
  - file size 同為 `840704`
- 精確重建：把 clean target 的 PE raw offset `0x4CEFA`
  （VA `0x0044D0FA`）從 `0xFF` 改成 `0x00`，所得 SHA-256／MD5 **逐字等於**
  IDA metadata。
- 該位置正是 workspace 已知的 no-life-decrement patch。抽查目前審計中的
  `0x004184B0`、`0x0041CDFF`、`0x0041EBBC`、`0x0042D070`、
  `0x0042D349`、`0x0042D54B` 等程式碼 bytes，IDB 與 clean target 相同。

結論：

- IDB 不是未知版本；它精確對應「clean target + 已知 `0x44D0FA: FF→00`
  patch」。
- 除 player miss/life-decrement 分支附近外，可把 IDB 指令地址用於 clean
  target；涉及 `0x44D0FA` 的分析必須明示 patched/unpatched 版本。
- 建議日後在 `START_HERE.md` 或 IDA database banner 同時記錄
  `clean_sha256`、`idb_input_sha256` 與唯一 patch tuple，避免後續審計先誤判成
  binary drift。

## F-002 — `10036..10039` 的映射重驗正確

嚴重度：無 correctness defect；IDA 型別品質可改善
狀態：**Observed（重新驗證）**

在 `ecl_resolve_int_lvalue` (`0x0041FE10`)：

- `10036 -> active_vm + 0x58`
- `10037 -> active_vm + 0x5C`
- `10038 -> active_vm + 0x60`
- `10039 -> active_vm + 0x64`

在 `ecl_eval_int` (`0x0041F420`) 亦讀取相同四個位置。這支持：

- `scripts/th08_ecl_vm_state.py` 的 `ECL_VM_SCRATCH_INTEGERS_OFFSET = 0x58`；
- `ECL_VM_SCRATCH_INTEGER_FIRST = 10036`；
- 讀到 `+0x67` 所需 projection size `0x68`；
- `G5_CAPTURE_ALIGNED_VM_LOCAL_SHADOW_CONTRACT_20260728.md` 的欄位映射。

注意：Hex-Rays 目前仍顯示 `a1[2856] + 88` 之類裸指標運算，而不是具名
`Th08Enemy`／`Th08EclVm` 欄位；語義正確主要靠註釋，不靠 type system 保護。

## F-003 — `10050` 的動態距離語義正確，但應精確稱為 3-component norm

嚴重度：低
狀態：**Observed（重新驗證）**

`ecl_eval_float` (`0x00420120`) 的 variable `10050` 路徑：

1. 以全域 player position (`0x017D61AC`) 與 `enemy+0x2D88` 呼叫
   `vec3_subtract`；
2. 對差向量呼叫 `vec3_length`；
3. 回傳結果供 conditional jump 使用。

`ecl_eval_int` 的同一 variable 也經相同 subtract/length 路徑，再走 native
數值轉換。

因此「current player/enemy Euclidean distance」是正確的；更精確的描述是
**三分量向量的 Euclidean norm**。若目前物理狀態保證 z 相同，它才等同 2D
距離。無論如何它是 capture 後會改變的 dynamic dependency，現有
fail-closed／不 memoize 決策是正確的。

## F-004 — IDA Local Types 對核心 ECL／enemy runtime 結構覆蓋不足

嚴重度：中（分析維護風險，不是當前 runtime bug）
狀態：**Observed**

目前 IDA 有 13 個 `Th08*` structures，包括 ECL file/instruction、
bullet emission、transform、laser、SHT、spell-card 與 FRScreen partial
structures；但沒有：

- `Th08Enemy`（至少 critical partial layout）；
- `Th08EclVm` (`0x228`)；
- auxiliary context (`0x24B0`)；
- active/saved-frame union or wrapper；
- enemy main-context selector fields（例如 `enemy+0x2CA0`）；
- combat-critical flags/HP/frame-damage partial structure。

後果：

- `enemy_ecl_vm_step`、`ecl_eval_int`、lvalue resolver 與 call/return 的
  decompile 仍以 `a1 + 11424`、`a1[2856]`、`+88` 等形式呈現；
- 即使註釋目前正確，錯誤 inherited local name／offset interpretation 很難被
  type propagation 自動暴露；
- CE-0163 的 `context+0x230` 誤標為 live locals 正是此類風險。

建議（此次不修改 IDB）：建立最小、明確標記 partial 的 runtime types，
只包含已重驗欄位；不要一次填滿 speculative struct。對 active VM pointer、
call depth、PC/timer、locals、aux marker、saved-frame base，以及 enemy 的
main/aux context roots做 type propagation，再重看 pseudocode。

## F-005 — `0x87` 是 auxiliary VM replacement，不是 interrupt；原生 handler 不檢查 slot，且會重複求值 target

嚴重度：中（目前 shipped corpus 未觸發）
狀態：**Observed（重新驗證）＋ Corrected（命名）**

IDA 的 `enemy_ecl_vm_step` case `0x87` 顯示：

- 第一個參數選擇 `enemy + 0x3384 + 4 * slot`；
- 若該槽已有 `0x24B0` context，先釋放；
- target 非負時配置並清零新 context，以 `context + 0x08` 啟動 ECL VM；
- 複製父 VM 的 `+0x18..+0x8F`（`0x78` bytes）到子 VM同位置；
- auxiliary scheduler 在 main VM 之後依 slot 0..3 執行，將
  `active_vm + 0x220` 設為 `slot + 1`。

因此 `scripts/th08_ecl_opcodes.py` 將 `0x87` 命名為
`start_interrupt_subroutine` 是具體的語義誤導：真正的 interrupt-slot
dispatch 是 `0x7D`。`0x87` 建議改為 `replace_auxiliary_vm` 或
`start_auxiliary_subroutine`；目前 flow/model 實作把它當作 `aux_vm`
則是正確的。

另有兩個必須保留在模型邊界中的原生事實：

1. handler 對 `slot` **沒有 0..3 bounds check**；「四槽安全」不是
   interpreter 保證，而是 shipped program invariant。
2. target/subroutine 參數在非負路徑會被求值兩次（一次判斷，一次寫入
   context）。若參數是動態/RNG 表達式，兩次結果理論上可不同。

我用 repository parser 掃描 `artifacts/decoded/*.ecl` 的全部 `0x87`
記錄：共 625 條，parameter mask 全為 0；slot 分佈為
`0:463, 1:100, 2:33, 3:29`，無越界 slot；32 條 target 為負數（停止/
清槽語義）。所以目前 exact shipped corpus 不會觸發上述兩個危險條件，
現有 shipped-image 分析仍可成立；但任何通用 interpreter、fuzzer 或
非 shipped ECL 都不應把這兩條假設靜默泛化。

## F-006 — call-depth 邊界分析基本正確，但「16-entry stack／saturates」容易掩蓋原生丟幀語義

嚴重度：低（capture 實作正確；描述需更精確）
狀態：**Observed（重新驗證）**

`ecl_call_subroutine` (`0x00421BD0`) 與
`ecl_return_subroutine` (`0x00421CB0`) 的實際順序是：

1. call 先把 return PC 寫進 active VM；
2. 若 enemy flag `+0x3324` bit 26 未設，將完整 `0x228`-byte active VM
   寫到 `saved_base + signed_i16(depth) * 0x228`；
3. 啟動 callee，並把 `0x004ECE20` 的 `0x20` bytes 複製到 callee
   `VM+0x70..+0x8F`；
4. 僅當 depth `< 15` 時才把 depth 加一；
5. return 先把 depth 減一；非負則恢復該 index，負數則結束 auxiliary
   context／回 main context。

所以 context 確實配置了 16 個 physical saved slots（0..15），但正常
可恢復鏈只有 slot 0..14。若在 depth 15 再 call，native 仍會寫 slot 15、
啟動 callee、depth 保持 15；下一次 return 卻減成 14 並恢復 slot 14，
**slot 15 的 immediate caller 被跳過**。這不是無損的 stack saturation。

目前 `scripts/th08_live/auxiliary_vm/{model,scalar,native}.py` 與 native batch
只輸出 `active + depth` 個 `0x228` frames，depth 15 時捕獲 slots 0..14；
這與 native 下一次可恢復的鏈一致，沒有發現 capture bug。VM-local shadow
對 call/return 明確回報 `unsupported_control_flow`，也沒有假裝精確。

但 `scripts/th08_ecl_opcodes.py` 將 `0x34` 描述為普通
“16-entry VM context stack” 不夠精確；文件中使用 “saturates at 15” 時
也應同步寫明 saturated call 會丟掉 immediate caller。若未來實作 call
interpretation，應重現這個異常語義或在 depth 15 call 前 fail closed。

## F-007 — VM-local shadow 與其「獨立」oracle 的 timer transition 都不等同 native

嚴重度：高（exactness claim）；目前 operational 影響受 shadow-only 與
retained workload `time_scale=1, fraction=0` 限制
狀態：**Corrected understanding / observed source defect**

IDA 指令級重驗：

- opcode `0x04` 與 **taken opcode `0x05`** 共用
  `0x004186F1..0x0041870F`：只把 target time 寫到 active VM `+0x0C`
  的 integer elapsed，保留 `+0x08` 的 float32 fraction；
- `timer_advance` 最終在目前未命名的 `sub_447421`
  (`0x00447421`) 使用 gameplay time scale (`0x017CE8E0`)：
  - scale `> 0.99000001f` 時 elapsed 直接 `+1`，fraction 不變；
  - 否則以 x87 計算後存回 float32 `fraction += scale`；若
    `fraction >= 1.0f`，elapsed `+1` 並做 float32 `fraction -= 1.0f`。

但 `scripts/th08_ecl_shadow/interpreter.py`：

- 只維護 Python double `timer_value = elapsed + fraction`；
- `0x04` 及 post-decrement positive 的 `0x05` 均執行
  `timer_value = float(target_time)`，直接丟掉 fraction；
- 等待時用 `ceil((instruction.time - timer_value) / time_scale - 1e-9)`，
  再做 double `timer_value += delta * time_scale`；
- 沒有 native 的 `>0.99000001f` 分支，也沒有逐 tick float32 round/carry。

更嚴重的是 `tests/th08_ecl_vm_local_oracle.py` 對 `0x04` 和 taken
`0x05` 同樣做 `timer = float(target_time)`，所以 Python/“independent
oracle” parity無法發現這個共同錯誤。retained 108 個 physical op05
fixture 的 `timer_fraction` 全為 0，亦沒有覆蓋 falsifier。

最小反例：elapsed=10、fraction=0.75、scale=0.5，執行 `0x04` 跳到
target time 4，successor timestamp=5。native 保留 0.75，下一 tick
變成 elapsed=5/fraction=0.25；現 shadow 從 4.0 起算，會預測兩 tick，
晚一個 physical frame。scale 位於 `(0.99000001, 1)` 或大於 1 時也會因
native fast path 與連續乘法不同而分歧。

建議後續修正時讓 production shadow 和 formal oracle 各自維護
`int32 elapsed + float32 fraction`，以逐 physical tick 的 native transition
作 oracle；新增 nonzero-fraction、threshold 兩側、float32 carry、jump 後
successor timing cases。這是 exact shadow 在擴大 authority 前的必要 gate。

### IDA coverage 補漏（與 F-007 直接相關）

`0x00447421` 目前仍叫 `sub_447421`，且 Hex-Rays prototype 把它錯解成
`void __thiscall sub_447421(float *this, _DWORD *a2, float *a3)`。
實際 `this` 是含 `+0x188 gameplay_time_scale` 的全域 timing object，
兩個 stack 參數分別是 `int32 *elapsed` 與 `float *fraction`。此 helper
是所有 Timer exactness 的核心，應列為優先 retype/rename 候選，例如
`advance_scaled_timer_components`；目前團隊只命名 wrapper，忽略核心
transition，使錯誤 shadow 仍可通過 parity。

另有一個 IDA annotation精度問題：現 `0x004186F1` 註釋只稱此處為
“opcode 0x04”，但該 basic block同時由 `case 5` 在
`ecl_resolve_int_lvalue(mask, operand 2)`、dword decrement、以
parameter-mask bit 2重讀 post-decrement值並判斷 `>0` 後進入。註釋應改成
“unconditional 0x04 / taken decrement-jump 0x05 shared body”，否則看
pseudocode時很容易漏掉 0x05 的 fraction-preservation義務。現 shadow對
shipped mask `0x04` 的 lvalue index、signed-int32 wrap及 `>0` 判斷本身
是正確的；錯的是 taken branch的 timer representation。

## F-008 — 32-entry ECL callback table 仍有重要 native 程式未命名／未列語義；其中包含額外 lethal collision 與全域 hazard transition

嚴重度：高（若 authority 泛化到相應 shipped workloads）；目前 active
route 的部分風險受 workload 範圍與 fail-closed shadow 限制
狀態：**Observed（IDA + shipped corpus）；部分 inferred domain naming**

`scripts/th08_ecl_callback_model.py` 雖列出了 32 個 callback address，但
`_TARGET_NAMES` 只為 19 個 index 提供語義。完整 shipped ECL 掃描顯示，
缺名的 index 並非全是 dead/visual-only code。`0x88` 的 182 次 immediate
invoke 中，實際使用而未命名的 index 為：

`3, 10, 19, 26, 27, 28, 29, 30`；

`0x89` 的 95 次 install/clear 中，實際安裝而未命名的 index 為：

`4, 8, 9, 11, 25`。

最重要的 instruction-level observations：

- **index 9 — `0x00424730`、index 11 — `0x00424820`、index 25 —
  `0x00424910`**：各自構造 enemy/VM-local-relative 的長方形，直接呼叫
  `player_test_collision_and_graze`，並在一條路徑開啟 graze。它們不是
  generic `enemy+0x2D70` contact box。現 `enemy_sensor.py` 只讀 generic
  position/contact-size/flags，沒有 callback pointer、callback index 或這些
  VM-local geometry，故不能把這三類 contact 當作已被 enemy-body sensor
  覆蓋。index 9/11 出現在 `ecldata4b*`，index 25 出現在
  `ecldata4bsp.ecl`；active route2 目前跑 Stage-4A，所以不是已觀察的
  Stage-4A defect，但任何對 Stage-4B／Spell Practice 的完整性聲明都會有
  明確缺口。
- **index 26 — `0x00425070`**：把 ECL argument 寫入
  `g_ecl_scripted_global_update_freeze` (`0x0160F534`)。該 global 會使
  `spell_card_update` 與 `frscreen_update` early-return、阻止 player update
  （包括 input/movement）、阻止 bullet position integration，並停止部分
  enemy timers；death handler 會清零它。現 runtime input-clock shadow 有
  讀此 global，這點正確；但 callback writer 仍叫 `sub_425070` 且 callback
  model 沒有名稱，導致「哪段 shipped ECL 改變 clock semantics」未被
  source-level provenance 串起。shipped `ecldata_sk.ecl` 以 `(26,1)` /
  `(26,0)` 各呼叫一次。
- **index 27 — `0x004250D0`**：掃描全部 1536 bullets；對 active 且
  `flags & 0x100000` 的 bullet，把 bullet state 寫入 caller VM local，
  以 bullet position 呼叫 `0x0042A680` 配置／啟動一個 `0x53D0` enemy，
  複製父 VM `+0x18..+0x8F`，然後清該 bullet flag。這是
  **bullet-to-enemy / new hazard birth transition**，不是單純 effect。
  shipped `ecldata_sk.ecl` 呼叫一次。
- **index 28 — `0x004251B0`**：設定 `time_scale=1/divisor`，掃描 active
  bullets 並以該 scale 乘其三分量 velocity，同時替部分 bullet sprite
  state保存/切換；shipped `ecldata_ym.ecl` 以 divisor 3 呼叫一次。
- **index 29 — `0x00425290`**：以目前 time scale 的 reciprocal 恢復全部
  active bullet velocity／sprite state，處理一個 global mode bit，最後把
  gameplay time scale恢復 1；shipped `ecldata_ym.ecl` 呼叫兩次。
- **index 8 — `0x004244F0`**：按共享 VM group/local state遍歷 linked
  enemies，維護組內 index/count/epoch，並逐 update 將非首 enemy 的
  motion angle朝 group-relative target 以 0.02 比例調整。這會改變
  enemy-origin future geometry，不能標成 presentation-only。
- **index 4 — `0x00423A60`** 是全 bullet portal/region transition：
  比較 current 與 previous position所在區域，跨區時設 2-frame cooldown、
  反轉 velocity、縮放/映射 position 並正規化 angle。repository 已有
  `portal_callback_step` 類模型，但 callback address/name 沒有連回 index 4，
  應補 provenance，不能說完全未實作。
- index 19 (`0x00424FC0`) 只把一個 global short 複製到 active VM int
  local 0；index 30 (`0x00424A00`) 寫一個 global dword；index 3/10
  還涉及 effect/global callback setup。它們優先度較低，但仍應命名或明示
  unknown effect，避免 32-address table 被誤讀為 32-semantics-complete。

目前 `th08_ecl_shadow/interpreter.py` 對 callback 只接受已支持的 index 12，
其餘會 `unsupported_callback`，所以沒有發現它把上述 transition 樂觀地
當成無事發生；這個 fail-closed 邊界應保留。問題是 static callback catalog、
IDA names/types 與 hazard completeness 文件會讓讀者低估缺口。

建議 IDA 優先 rename/retype：

- `0x425070 -> ecl_cb_set_scripted_global_update_freeze`
- `0x4250D0 -> ecl_cb_spawn_enemies_from_flagged_bullets`（domain noun 可先標
  inferred）
- `0x4251B0 -> ecl_cb_apply_global_slowdown_and_scale_bullets`
- `0x425290 -> ecl_cb_restore_bullets_and_time_scale`
- `0x424730/0x424820/0x424910 -> ecl_cb_test_custom_rect_*`
- `0x423D70 -> vec3_scale_inplace`

callback table應套同一個正確 function-pointer prototype；目前
`0x4250D0`／`0x42A680` 被 Hex-Rays 誤判出 x87 `st0` 參數，會嚴重干擾
caller/callee dataflow閱讀。

## F-009 — HP／frame-damage offsets 正確，但一條 IDA gate 註釋貼錯指令；boss `damageable` 尚未包含 player-transition 條件

嚴重度：中（IDA 可讀性與 objective gating）；no-Bomb、正常 gameplay
frame 下影響較小
狀態：**Observed（shipped instructions + source）；一項 conservative
implementation boundary**

重新按原生控制流而不是現有註釋核查 `enemy_manager_update`：

- `0x0042C94C..0x0042C95D` 讀的是 enemy `+0x3328`，右移 7，故當下
  branch 實際測試 **flags2 bit `0x80`**；非零會跳過 VM／motion／phase／
  damage update。
- 另一條較早的路徑 `0x0042C928..0x0042C94A` 才測 enemy flags
  bit `0x40000000`；只有該 bit 已設且 Bomb-active global 或
  player-transition state 非零時才跳過整個 update。
- `0x0042CEE8..0x0042CF27` 分別拒絕 flags bits `0x10`、`0x20`、
  `0x800`；`0x0042CF2D..0x0042CF47` 額外在 flags bit
  `0x80000000` 且 Bomb active 時拒絕 damage/hurtbox block。
- `0x0042D07D..0x0042D08B` 最後要求 player-shot damage bit `0x40`；
  `0x42D070 / 0x42D349 / 0x42D355` 的 clear、HP subtraction、resolved
  frame-damage publication，以及 defeat path 的 offsets／順序均與 repository
  文件及 decoder 相符。

因此 `enemy_combat_progress.py` 明確命名為
`local_damage_flags_open` 且宣告 `damageability_authority:
local_flags_only` 是準確的；`0x830` 正是 `0x10|0x20|0x800`。

但 IDA 在 `0x0042C95D` 現有註釋寫成「Enemy bit `0x40000000`
gates ... during Bomb/transition」。這句描述的是前一個 flags branch，
而它黏附的實際指令是 flags2 `0x80` test，容易讓讀者漏掉後者是
**無條件的 update-block bit**。應把兩種 gate 分別註釋在
`0x42C936/0x42C94A` 與 `0x42C95D`，或至少在 `0x42C95D` 明寫
“flags2 bit 0x80 independently blocks update”。

另有一個較窄的 source-level 邊界：
`BossPhaseSnapshot.as_progress_state()` 把 local gate、`not bomb_active`
及 stable 組成欄位名 `damageable`，但沒有接收／檢查 native
player-transition state。若 enemy flags bit `0x40000000` 已設，transition
期間 native 會跳過 damage，這個 Boolean 仍可能為 true。現 no-Bomb
正常 gameplay 決策大多避開該窗口，而且 blanket `not bomb_active`
對部分 enemy 反而是保守的；因此不是已證實的 live survival defect。
在把 damage objective 提升 authority 前，應增加 transition sensor，
或把欄位改名／文件化為 `stable_local_damage_candidate`，並保留實際
HP delta 作驗證。

## F-010 — Live 雷射 projection 完全忽略 global time scale，且多個「exact」Timer model 未做逐次 float32 store

嚴重度：高（live hazard projection / exactness claim）
狀態：**Observed implementation defect；shipped reachable trigger**

原生 laser loop 的直接證據：

- `0x00431BC9` 載入 `g_gameplay_time_scale`，乘 laser `+0x56C`
  speed，再加到 `+0x55C` head distance，結果存回 float32；
- `0x004320E2..0x004320ED` 對 laser `Th08Timer +0x588` 呼叫
  `timer_advance`；
- `timer_advance -> sub_406660 -> sub_447421` 使用同一個 global
  scale 與 F-007 所述逐 tick float32 fraction 語義。

`step_laser()` 本身雖有 `time_scale` 參數，但真正給 live corridor 使用的
`laser_collision_geometry_frames()` 沒有這個參數；其 cached loop 固定
呼叫 `step_laser(state)`，即預設 `time_scale=1.0`。
`lower_lasers()`、`lower_lasers_packed()` 與
`lower_th08_corridor_hazards()` 也都沒有傳入或攜帶 global time scale。
這會同時錯估：

1. head/tail segment 位置；
2. warmup／active／fade phase 到期時刻；
3. collision enable/disable 與 graze cadence。

錯誤方向不保守：例如真實 scale `0.25` 時，預測 tail/head 向前移動四倍，
既可能在真實 segment 前方製造假 hazard，也可能把仍在玩家後方的真實
segment 提早移走；phase 又會提早結束。不能用單向 uncertainty 解釋。

這不是純 synthetic 條件。shipped route manifests 中 callback index 18
可達：

- Lunatic Final A/F​​inal B；
- Extra；
- 且 manifest 明列 Extra subroutine 86 在 time 0 設 divisor 4、time 10
  恢復 divisor 1。完整 corpus 的 index 18 divisor 是 4、1、2。

index 28（見 F-008）另在 shipped `ecldata_ym` 設置 divisor 3。
是否每個 slowdown window 都恰與 active laser 重疊尚未由 runtime trace
證實，但現 API 在任何重疊時都必錯，且 acceptance target 包含 Extra。

第二層 exactness 問題是即使 caller 正確傳入 scale：

- `th08_laser_model._advance_timer`
- `th08_option_model._advance_timer`
- `th08_route2_player_runtime._advance_timer/_decrement_timer`

均以 Python double 累加 fraction，沒有像 native `sub_447421` 每次存回
float32。laser head/tail kinematics 亦在 Python double 中跨 frame 累積，
而 native 每次寫回 dword。現 tests 只用 `0.5` 這類二進位精確倍率，沒有
獨立 float32 oracle。

已執行的最小 deterministic falsifier：

```text
scale = float32(1/12), elapsed=0, fraction=0, advance 12 ticks
native: elapsed=0, fraction=0.9999998807907104
laser/option/player Python: elapsed=1, fraction=2.9802322387695312e-08
```

對 shipped divisor 3，3 ticks 後兩者 elapsed 都是 1，但 native fraction
恰為 0，三個 Python model 留下 `2.9802322387695312e-08`；長 horizon
仍非 byte/transition exact。

`th08_ecl_auxiliary_core/timer.py` 已有正確、可參考但不應直接充當獨立
oracle 的 `float32(fraction + scale)` transition；其獨立 byte oracle也
另行實作了 float32。修正應：

- 將 captured global time-scale 納入 immutable laser projection key/API；
- 每個 native dword write 明確 float32 round；
- 用獨立 scalar oracle 驗證 phase transition、collision calls 與 segment
  geometry，至少覆蓋 `1, 1/2, 1/3, 1/4, 1/12`、非零 fraction 和
  threshold 兩側；
- 在此以前刪除／收窄 `th08_laser_runtime.py` 的
  “Exact native LaserState projection has no measured horizon drift” 及
  corridor 中 “exact target frame / no model drift” 的 authority wording，
  或對 `time_scale != 1` fail closed 並加入雙向保守 envelope。

## V-001 — Runtime-ECL relocation normalization 經指令級重驗，現實作正確且 fail closed

結論：**Observed / revalidated；未發現理解偏差**

`ecl_load_file` (`0x00418330`) 的 shipped instructions 顯示：

- 驗證 magic `0x800` 後，`0x418393..0x4183C8` **固定遍歷 16 次**，
  將 runtime base 加到 header `+0x08 + 4*i` 的每個 slot；不是只處理
  `timeline_count` 個 active timeline。
- `0x4183CA..0x4183D5` 把 context 第二個 dword 設為
  `runtime_base + 0x48`。
- `0x4183D8..0x418415` 按 header `+4` 的 signed 16-bit subroutine count，
  對 `+0x48` table 的每一項加 runtime base。
- 沒有第三類 relocation site。

`scripts/th08_live/runtime_ecl_image.py` 恰好反轉這兩組 relocation：
16 個 timeline/end slots與 declared subroutine table；使用
`slot[timeline_count]` 的 relocated pointer 導出 bounded image length，
要求 normalize 後 sentinel 等於 length，並逐 byte 對 static decoded
image。它不會把其他 body bytes「合理化」，一個 non-relocation mutation
會保留並使 identity 失敗。context before/after、重讀 header prefix、base
範圍、8 MiB upper bound、table pointer及每個 relocation target也都
fail closed。

`MAXIMUM_ECL_SUBROUTINES=4096` 比 native signed-i16 可表示範圍更嚴，
不會擴大接受集合。完整 shipped Stage-5 capture又已得到 normalized/static
47,224 bytes byte-for-byte equality。就目前 immutable-image contract 而言，
沒有必要修改 normalization algorithm。

僅有一個低優先度 ABA 理論邊界：若 stage unload/reload 在四次 RPM 之間
恰好重用同一 base/context 值、header 相同而 body 被改寫，現 bracket
可能看不出；目前沒有 observed runtime 證據，ECL body 在正常 active
stage 亦視為 immutable。若未來要在 transition 中捕獲，可用 gameplay
epoch/manager frame bracket 或第二個 digest read排除此情形，不應把它
誤報成現有 bug。

## F-011 — `sub_42C420` 的 focus/character-dependent enemy contact gate 未進 solver recurrence；已有 retained trace 顯示 16 個 lethal bodies 在 action 後 10 frames 才「突然」出現

嚴重度：高（action-conditioned future hazard completeness）
狀態：**Observed native semantics + observed retained runtime witness +
observed implementation omission**

這是目前團隊在 IDA 中仍未命名、但對 solver 很重要的 native 程式：

- `sub_40BC40` (`0x0040BC40`) 只是讀取 player object `+0x05` byte。
- `sub_42C420` (`0x0042C420`) 對帶 enemy flags bit `0x100` 的 enemy
  執行 character-mode同步；函式結尾
  `0x42C568` 將 enemy flags bit `0x800` 精確設為
  `(player[+5] & 1) << 11`。
- `enemy_manager_update` 在 `0x42C974..0x42C98A` 對 active enemy
  flags bit `0x100` 每 update 呼叫此 helper。
- 同一 manager 後續在 `0x42CF02..0x42CF10` 測 bit `0x800`；
  非零直接跳過 contact與 player-shot damage block。故它不是 render
  mode，而是 lethal-contact及damageability gate。
- `player_update_input_movement` 的 shipped instructions重新確認：
  focus entry後 transition counter `player+0x08` 達 7 才在
  `0x44B1D9` 寫 `player+0x05 = 1`；focus release後達 7 才在
  `0x44B42C` 寫 `player+0x05 = 0`。這個 delayed character state 與
  immediate focus byte `+0x03` 不同。

因此對 route 2 而言，選擇 focused／unfocused action 可以在 7 個 player
callbacks 後改變 bit-`0x100` enemy 的 contact/damage gate。它必須是
policy branch的一部分，不是 snapshot 時不變的 enemy flag。

### 現 solver 為何漏掉

`enemy_sensor.py`：

- `ENEMY_CONTACT_BLOCKING_FLAGS = 0x830`，讀當下 flags 的 bit
  `0x800` 是正確的；
- 但 `decode_enemy_bodies(..., include_contact_disabled=True)` 仍先把
  `flags & 0x830` 的 record完全排除。`include_contact_disabled` 只保留
  bit `0x04` 暫時未開的 geometry，不能保留 character-blocked bit
  `0x800` geometry；
- `EnemyBodyModeMemory` 只保留「最近曾看過」的 record，80-frame TTL
  後即消失；
- `lower_enemy_bodies` 將當下 tuple作固定 future moving AABB，沒有
  player `+5/+8`、enemy bit `0x100` 或 action-conditioned enable event。

所以玩家 focused 超過 80 frames 後，這些 enemy 既不在 current snapshot，
也不在 dormant memory。solver 若選 unfocused，native 在約 7 callbacks
後重新開 contact；cached/global/local/issue-time certificate都無法從
當下 hazard tuple看到它。issue guard只在它真正出現後補救，不能驗證此前
已發出的 action。

### Retained physical witness

讀取既有、未修改的
`artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_212622.jsonl`
得到：

- focused run `frame 9855..10063`，超過 200 frames，dormant count為 0；
- frame `10065` 首次選 unfocused；frames
  `10065,10068,10071,10073` 的同步 issue prefix均報：
  `body_count=0, contact_enabled_count=0, changes=[]`；
- frame `10075` 一次出現 ordinary slots 0..15 共 16 bodies，
  每個 flags 都是 `0x0100114D`：bit `0x100`、active bit與contact
  bit `0x04`均設，bit `0x800` 已清；issue guard這時才 recertify；
- 該 10-frame delay與 native `player+5` 七-callback transition一致。
  這個 witness沒有在該處造成 hit，故它證實 **model omission**，不是
  已證實的該次死亡原因。

同一 raw trace中，長於 80 frames的 focused interval後約 10..20 frames
出現 bit-`0x100` rings並非只一次；例如 `1..411 -> first bit8 at 421`、
`2533..2630 -> 2640`、`4246..4444 -> 4454`、
`30414..32528 -> 32538`。有些 rings當時只有 anticipatory geometry，
但上述 frame 10075 的 16 個全部已是 native contact-enabled。

### 修正方向與 IDA 命名

最低風險的 correctness gate：

1. first-64 contiguous capture保留所有 active、finite、nonnegative-size
   enemy geometry，即使 bit `0x800` 當下阻擋；另保留 raw flags／gate
   class，不要把「觀察」與「當下 lethal」在 decoder先合併；
2. 將 route-2 `Route2FocusState` 已有的 `remilia_character_active`、
   transition counter與選擇 action帶入 hazard recurrence；
3. 對 flags bit `0x100` 精確預測 bit `0x800` gate，或在完成前對其
   latent geometry採 action/time-indexed conservative union；
4. 加一個由上述 frame `10065..10075` 縮小的 deterministic fixture，
   驗證 unfocus root在 gate-open frame之前已包含16-body ring；
5. damage objective也要套同一 transition，因 bit `0x800` 同時阻擋
   player-shot damage。

IDA 建議在仍保留 domain不確定性的前提下：

- `sub_40BC40 -> player_get_secondary_character_active`
- `sub_42C420 -> enemy_sync_character_mode_contact_damage_gate`

“Remilia” noun 對 route 2 是已知，但 helper供所有 route使用；函式名宜用
game-mechanical `secondary_character`，註釋再列各 route角色。這兩個地址
比純 UI/effect的大函式更應優先補名／型別／caller註釋。

## F-012 — solver 把 SHT 的「全寬 2.0」直接當作半徑 2.0；native 真正 lethal half-extent 是 1.0

嚴重度：中高（安全方向的系統性過保守；會縮小 viable set、製造 false
collision／empty kernel，亦使文件中的 finite-model proxy 與 native 不同）
狀態：**Observed native instructions + observed decoded shipped resources +
observed retained runtime confirmation + observed implementation mismatch**

這不是依名稱猜測；native 的完整資料流為：

1. `player_initialize_resources` (`0x0044D650`) 在
   `0x44D7E3..0x44D7F5` 讀 primary SHT header `+0x0C`，執行浮點除
   `2.0`，然後把結果同時存入 player `+0x3D4/+0x3D8`；
2. `player_update_input_movement` 在每次移動、clamp 後的
   `0x44BBEC..0x44BC52`，用
   `player_position(+0x2B4) ± player(+0x3D4)` 更新 cached lethal
   AABB `+0x38C/+0x390/+0x398/+0x39C`；
3. `player_test_collision_and_graze` (`0x0044A6A0`) 的
   `0x44A748..0x44A784` 亦直接以 `player+0x3D4` 為半 extent，然後
   在 `0x44A81D` 作 inclusive overlap。這裡沒有再乘二或額外半徑。

shipped route-2 resources的 parser輸出：

- `ply02a.sht`：header `+0x0C = 2.0`；
- `ply02as.sht`：header `+0x0C = 2.0`。

因此 Sakuya／Remilia route 的 native lethal AABB是玩家中心每軸
`±1.0`，完整寬高 `2.0 × 2.0`。這也已由既有 physical captures獨立
確認：掃描 route-2 Stage 4A/5/6B dossier中的 2,208 個
`player_lethal_aabb`，2,201 個精確是 `2 × 2`，其餘僅有
`<1.6e-5` 的 float差。

現 repository卻在以下 authority-bearing路徑統一使用半徑 `2.0`：

- `scripts/th08_live/movement.py::PLAYER_RADIUS`
- `scripts/th08_laser_runtime.py::PLAYER_RADIUS`
- `scripts/th08_corridor_adapter.py::TH08_CORRIDOR_CONFIG`
- `scripts/th08_simulator.py` 的 bullet／laser player config defaults
- Python local hazard、corridor clearance、semantic differential，
  以及所有對應 native C++ ABI/kernel都接收這個值。

也就是每個 bullet、laser及enemy-body Minkowski AABB在四邊都比 native
多膨脹 1 pixel。nearest-lattice sampling error已在 viability recurrence
中另行逐 transition扣除，不能把這個差值解釋為同一補償。搜索
repository亦未找到把 `2.0` 明確聲明為額外 safety margin的 authority
contract；相反，formal/foundation notes稱其為 “player's SHT half
extents”，與上述 instructions不符。

影響方向很重要：

- 這個 mismatch是保守的，不會單獨導致 native hit；
- 但會把 native 尚有最多 1 pixel 軸向餘量的狀態判成碰撞，壓縮 safe
  action mask及 attainable lower bound，增加
  `global_viability_kernel_exhausted`／false terminal threat，並可能迫使
  controller走更差的迂迴動作；
- 它也使 “semantic differential” 只能證明 Python/C++共同實作同一個
  2.0 proxy，不能證明 native semantics。

修正不應只改一個常數。建議：

1. 將 SHT parser欄位改成不含糊的 `player_hitbox_full_width`，另由
   route manifest導出 `player_lethal_half_extent =
   player_hitbox_full_width / 2`；
2. 讓 live config使用 immutable route/SHT-derived value；若團隊仍要
   額外 1 pixel margin，另設有名稱、有 contract的
   `model_margin`／uncertainty，不能藏在 “radius” 裡；
3. 加 native-boundary fixture：center `(100,100)`、hazard edge距中心
   `1.5 + hazard_half_extent` 時 native不碰撞，而 current solver會碰撞；
4. 重新發布依賴此值的 viability/certificate version，並分開報告
   native-exact `1.0` 與額外 margin ablation；舊 2.0 witness不能被稱為
   native-exact，但其 universal winning結果仍是較保守模型下的有效證據。

## F-013 — live planner沒有把 global time scale帶入玩家 transition；Final／Extra可把可達距離高估 2–4 倍

嚴重度：嚴重（optimistic action reachability；會讓 local hard
certificate、delay prefix與corridor recurrence證明 native實際走不到的位置）
狀態：**Observed native instructions + observed reachable shipped ECL +
observed implementation omission**

native `player_update_input_movement` 的順序已由 instructions確認：

- `0x44B641/0x44B65C`：SHT速度先乘 player axis scales
  `+0x404/+0x408`；
- `0x44BA4F/0x44BA61`：保存 pre-time-scale速度；
- `0x44BA73/0x44BA85`：真正本 frame displacement
  `player+0x3F8/+0x3FC = scaled_speed * g_gameplay_time_scale`；
- `0x44BAB6/0x44BAE6` 才把這兩個 float32 delta加到 position。

repository其實已有正確的離線 primitive：
`scripts/movement_model.py::step_axis_aligned_movement(..., time_scale=...)`
會在相同 write boundaries套 scale。但 live authority路徑沒有接它：

- `th08_live/movement.py::project_player_for_read_lag` 直接
  `x/y + speed * frames`；
- `th08_local_planner/beam.py` 每層直接 `node + action.dx/dy`；
- `th08_live/local_certificates.py` 的 committed prefix及每個 root
  certificate均直接累加固定 `action.dx/dy`；
- `th08_corridor_adapter.py::TH08_VIABILITY_ACTIONS` 建立固定正常速度
  actions；Python/C++ viability recurrence都只接收這些 action velocities；
- `minimum_travel_frames`、local objectives及supplemental native beam也沿用
  同一固定速度。

controller已透過 main-ECL snapshot讀到
`g_gameplay_time_scale`（trace的
`bullet_velocity_lookahead.time_scale`），但只交給 ECL/bullet-event
lowering，沒有進玩家 transition。

這不是不可達的理論狀態。shipped route manifests顯示：

- Lunatic Final B subroutine 44：callback 18在 ECL time 0設 divisor 4，
  time 70設回 divisor 1；
- Extra subroutine 86：time 0設 divisor 4，time 10設回 1；
- Final A/B/Extra的 reachable callback集合均含 index 18；全 corpus另有
  divisor 2。

IDA中的 callback 18 `ecl_cb_set_time_scale_reciprocal`
(`0x00424F90`) 在 `0x424FAE..0x424FB4` 精確執行
`g_gameplay_time_scale = 1.0 / argument_1`。此外仍未命名的 callback 28
`sub_4251B0` (`0x004251B0`) 也會寫相同 global，並同步縮放既有 bullets；
callback 29 `sub_425290` 負責恢復／重設。這兩個是應優先命名與列入
effect catalog的 native 程式。

最小 falsifier：scale `0.25`、unfocused right、無 clamp、4個 player
callbacks。native每 callback位移 `4 * 0.25 = 1`，合計 4；current live
projection及所有 action certificates預測 16。這個方向是
**optimistic**：例如 certificate認為玩家已越過一個 incoming hazard，
native卻仍留在其路徑上。F-010所述 laser head/timer漏 scale是同一 physical
interval的另一個錯誤，兩者不能互相抵消或當作共同慢放，因量化、phase、
不同 hazard class與 collision order都不同。

修正／promotion gate：

1. 建立每個 immutable observation的 physical time-scale欄位；不能只依
   「恰好有可讀 main VM」才取得 global；
2. action transition、held-prefix、pending-delay、local beam、
   supplemental beam、corridor actions及所有 scalar/native oracles共用
   float32-scaled displacement；
3. 對預測 horizon內 callback 18/28/29造成的 future scale change分支或
   fail-close；只使用 root snapshot常數仍會跨 event錯誤；
4. retain divisor `4 -> 1` 與 `2 -> 1` boundary fixtures，包含
   ECL timer fraction、player clamp、laser lifecycle及native/Python/C++
   differential；
5. 在完成前，所有 `time_scale != 1` 的 hard certificate必須退出
   authority或使用「玩家最慢、hazard最不利」的保守包絡，不能繼續把固定
   正常速度標作 exact。

## F-014 — native laser碰撞是 rotated local AABB，local/C++ kernels卻改成 capsule；目前主要造成頭尾過度封鎖

嚴重度：中高（finite-model geometry不等價、顯著 false positives及額外
`hypot`成本；與 F-012 玩家半徑修正有耦合）
狀態：**Observed native instructions + observed implementation
approximation；目前 live constants下方向可證為保守，未見 unsafe physical
witness**

native `player_test_collision_and_graze` (`0x0044A6A0`) 的
`0x44A6E3..0x44A81D` 做的是：

1. 以 laser origin為 pivot，把玩家中心逆旋轉 `-angle`；
2. 以 incoming laser full-size除 2 建立 axis-aligned local rectangle；
3. 以 player SHT half extents擴張該 rectangle；
4. 作 inclusive x/y AABB overlap。

`scripts/th08_laser_model.py::laser_collision_box` 及
`laser_overlaps_player` 已正確表達這個 scalar語義。但 live lowering到
`th08_laser_runtime.PackedLaserFrame` 後，只保留 start、segment vector及
一個 `collision_radius`。隨後：

- NumPy `_numpy_hazards_for_positions`；
- C++ `native/src/local/hazards.cpp`；
- corridor `SegmentHazard`／packed segment volume

全都用「point-to-segment Euclidean distance minus radius」，即 capsule
而非 native rectangle。

令 lethal segment為 local `[s,e]`、laser transverse half extent為
`h`。route-2 native player half extent為 `p=1`，所以 native region是
`[s-1,e+1] × [-(h+1),h+1]`。current kernel則以 segment為軸、
半徑 `h+2`（另加 0.75 base uncertainty）畫 capsule。結果：

- segment中段是較保守的 transverse expansion；
- 頭尾中心線可延伸到 `h+2`，native只延伸 1；例如 `h=4`、player在
  endpoint外5 pixels時，native明確不碰撞，current kernel仍報 collision；
- native方角被 capsule圓角改形。以目前錯誤的 player radius 2，
  `sqrt(1²+(h+1)²) <= h+2`，故 native rectangle仍被 capsule包含；
  但若 F-012單獨改成1、又移除／調小 uncertainty，native corner
  `(e+1,h+1)` 會落在 radius `h+1` capsule之外，反而變成 unsafe false
  negative。

因此目前它主要是安全側的過保守與性能損失，卻不能稱為 native-exact。
`th08_laser_runtime.Laser` 上 “Exact native LaserState projection has no
measured horizon drift” 的註釋最多只適用 lifecycle state，不適用最終
collision geometry或float rounding。

建議把 lifecycle投影保留成 local rectangle的
`center_longitudinal/full_length/full_height/angle/pivot`，kernel對候選
玩家點先作一次 local rotation，再用與 bullet相同的 signed AABB
clearance。這會：

- 精確保留 native flat ends及square corners；
- 消除大部分 endpoint false positives；
- 以 multiply/add/abs/max取代每個 candidate-laser pair的 projection
  clamp與 `hypot`，很可能同時更快；
- 允許 player native half extent、明示 uncertainty、lattice error各自
  版本化，不再靠兩個錯誤偶然互相補償。

promotion前應用 `laser_overlaps_player` 作真正獨立 scalar oracle，覆蓋
角度 0/π/4、零長度、tail>0 的0.7長度、warmup/fade窄盒、flat endpoint
外側及四個inclusive corners；現有 NumPy/C++ capsule parity只證明兩個
實作一致。

## V-002 — `player_dead_handler` 的 native caller closure 已閉合；原生致死幾何入口可分成四類

結論：**Observed / revalidated；這是一個正面的 completeness 邊界，不代表
四類 future transition 都已被 solver 建模**

我從 `player_dead_handler` (`0x0044AB40`) 反向列出全部 direct callers，
再逐一向上追其 callers。direct miss helpers其實只有三個；依上游物理來源
可分成四個 lethal source families：

1. 普通 hostile bullets，經
   `player_test_bullet_collision_or_cancel` (`0x0044A230`) 的AABB；
2. generic enemy bodies，經
   `enemy_test_player_contact_at_position` (`0x0044A360`) 的AABB；
3. bullet manager laser loop，經
   `player_test_collision_and_graze` (`0x0044A6A0`) 的rotated rectangle；
4. callback 9/11/25 (`0x424730/0x424820/0x424910`) 的custom rectangles，
   同樣經 `player_test_collision_and_graze`。

三個direct helpers都只在overlap且player phase允許時進
`player_dead_handler`。目前 shipped executable中沒有第四個direct helper
或第五個上游 source family。

這個 closure 有兩個用途：

- solver 的「現在是否有完整 lethal source class」可用這四類作 checklist，
  不必無限猜測另有未找到的直接 miss routine；
- F-008 已指出 custom callback rectangles尚未進 sensor/model，所以 closure
  **反而精確界定了現缺口**；不能因 bullet/body/laser三個常用 tuple已存在，
  就宣稱 native lethal geometry完整。

應在 IDA／notes 保留這條 caller-closure 證據及日期。若日後發現 indirect
call、patch或不同 executable hash，才重新開放結論；目前 connected IDB
的 direct xref closure是完整的。

## F-015 — live bullet decoder把 native state 5 fade records當成 lethal bullets；state欄位甚至沒有保留到規劃 snapshot

嚴重度：中（安全側 false hazard、viable-set/性能污染；不是單獨的 unsafe
false negative）
狀態：**Observed native control flow + observed Python/C++ omission**

`bullet_manager_update` (`0x00431240`) 對每個 nonzero state先 switch：

- state 1 進 `LABEL_8`，才會執行 transform、position integration、
  playfield lifecycle，以及 `0x4315F7/0x431699` 的 graze/lethal collision；
- state 2/3/4 是各自的 transition/cancel animation；動畫結束時可能在同一
  update改回 state 1並落入 collision，未結束則直接跳到尾端；
- **state 5** 在 `0x431AB4..0x431ADF` 只更新其 fade animation；動畫結束
  就 deactivate，否則直接到 `LABEL_97`。它不會經過普通 bullet collision
  block；
- default nonzero state也直接到尾端。

現三條 live decoder路徑卻都以 `state != 0` 作唯一 active predicate：

- `planning_bullet_active_slots()` 用 NumPy `flatnonzero(uint16 state)`；
- scalar `decode_planning_bullets()`／diagnostic `decode_bullets()`；
- `native/src/local/bullet_decode.cpp`。

之後 `Bullet` 和 `PackedBulletSnapshot` 均**不保存 native state**，因此
`_build_bullet_frames()`、local/issue certificate、corridor與 C++ kernel
無法在後段排除 state 5；它們把 fade sprite AABB按當下 velocity投影成
每一個 horizon frame的 lethal rectangle。tests又只檢查 Python/native
decoder共同接受 nonzero state，沒有以原生 manager collision call作 oracle。

shipped transform kind `0x040000` 會明確進 state 5，普通 collision/cancel
也會寫 state 5，所以不是無法到達的 synthetic value。當場的錯誤方向是
保守：會增加 bullet count、製造 false collision及空 safe-action mask，
也讓所有 candidate-bullet pair多做無效運算；state-5密集的 cancel/fade
窗口尤其浪費。尚未保留含 raw state histogram的 runtime witness，故不在
此虛構實際比例。

修正時不能簡單只讀 `state == 1`：

1. state 2/3/4 是否會在「下一個 manager call」轉為 state 1取決於各自
   animation VM結果；若不捕獲該狀態，需用明示的短期保守 transition；
2. state 5及 unknown/default可從 lethal collision set排除，但可另留在
   diagnostics/birth attribution，避免破壞 slot lifecycle；
3. 將 raw `uint16 state`加入 packed ABI與 immutable model，讓
   sensing和hazard lowering分層，而不是 decoder先丟掉分類；
4. 新增 scalar oracle，逐 state核對某一 manager update是否實際呼叫
   bullet collision helper；不要再只做 Python/C++ decoder parity；
5. benchmark應分開報 `allocated_nonzero_count` 與
   `lethal_or_transitioning_count`，量化可省去的 pairwise kernel工作。

## F-016 — offline route-2 player runtime使用錯誤 playfield bounds；可生成 native clamp 不可達的位置

嚴重度：中高（離線 replay/simulator exactness、由其產生的 fixtures與
hash；live planner本身使用另一組正確 bounds）
狀態：**Observed source inconsistency + observed native clamp dataflow +
observed physical boundary values**

IDA 的 `player_update_input_movement` (`0x0044AEC0`) 在
`0x44BB03..0x44BBE9` 明確把更新後的中心位置 clamp 到四個 runtime值：

```text
x ∈ [origin_x, origin_x + width]
y ∈ [origin_y, origin_y + height]
```

這四個值位於 runtime BSS／screen state，IDB file image中的靜態 dword是
`0xffffffff`，所以不能從未啟動的 IDB data假造常數。但兩套 repository
實作及 retained physical evidence足以暴露目前矛盾：

- live `scripts/th08_live/movement.py` 和 corridor使用
  `x=[8,376], y=[16,432]`；
- 大量保留的跨 Stage 1/3/4A/5/Final B captures在實際 movement clamp後
  精確出現 `x=8.0/376.0`、`y=16.0/432.0`，且未見中心位置到達
  0/384/0/448；
- 但 `scripts/th08_movement_model.py` 把
  `TH08_PLAYFIELD_BOUNDS` 寫成
  `MovementBounds(0.0, 0.0, 384.0, 448.0)`；
- `step_route2_player()`、integrated `th08_simulator` 及
  `th08_replay_player_projection.py` 都把這組值作默認；foundation notes又
  把它們描述為 recovered/executable native subset。

故離線模型從例如 `x=376` 持續按 right時會走到384，而 native仍停在376；
`y=432` 向下同理會到448。這不是座標系的等價平移，因初始位置、shot/
enemy world coordinates及live model都未同步平移。replay projection輸出的
position hash、邊界時的option/shot origin、collision及任何由此生成的
deterministic fixture都可能錯。

修正建議：

1. 將 `TH08_PLAYFIELD_BOUNDS` 改成 route/runtime capture導出的
   `(8,16,376,432)`，或明確傳入一個由 captured runtime origin/extents
   建立的 immutable bounds；
2. live與offline不要各自維護四個裸常數；route adapter應輸出同一版本化
   physical-boundary object；
3. 加四邊 clamp differential，包含 overshoot、diagonal、time-scale及
   float32 store；
4. 既有 replay projection hash/fixtures需重算並標示舊版本使用錯誤 bounds；
5. 如果 `0..384 × 0..448` 原意是渲染相對座標，應另取名
   `render_playfield_extent`，不得作 player center clamp。

## F-017 — route-2 Focus/Shot 會改變共享 gameplay RNG 消耗；蕾米莉亞正常使魔射擊 callback 7 尚未進因果模型

嚴重度：高（完整 deterministic replay、動作／敵彈因果、任何跨 future
birth 的 policy authority）；目前 local snapshot-only hard certificate已把
unseen future birth標成 UNKNOWN，故**不能僅憑本 finding宣稱現 live
certificate已產生 unsafe false negative**
狀態：**Observed native dataflow + observed shipped SHT corpus + observed solver
omission；其對特定敵彈／hit的實際影響仍待 native differential trace**

IDA 中 `player_sht_load` (`0x0044DD70`) 會把每個56-byte SHT record
`+0x28/+0x2c/+0x30/+0x34` 的四個 callback index經 executable callback
tables重定位。callback-0 table的 index 7（table entry `0x004C7EFC`）指向
目前仍未命名的 `sub_4501B0`：

```c
if (cadence % record->period != record->phase)
    return 0;
player_shot_initialize(...);
shot->angle =
    rng_next_signed_unit(&g_gameplay_rng) * PI / 48.0f - PI / 2.0f;
vec2_set_from_polar(&shot->velocity, shot->angle, record->speed);
return 1;
```

也就是每個到期 shot會呼叫一次 `rng_next_signed_unit`；repo已正確恢復該
helper為一個 `next_u32()`，所以實際消耗**兩次16-bit RNG transition**，
並把原本正上方的角度改成約 `-90° ± 3.75°`。這裡使用的就是其他
ECL/item/bullet callback共用的 `g_gameplay_rng`，不是獨立 cosmetic RNG。

shipped `ply02as.sht` 提供了可達性證據：

- 正常 power levels 0..5 的中央 player shot callback全為0；
- 同六個 levels 的所有 Remilia option shots callback-0均為7（依 power
  會有2或4個該類 record，各自按 period/phase到期）；
- Bomb/Last-Spell special levels 6/7 callback均為0，故目前
  `th08_player_shot_model.py` 對這兩個特殊 level的窄範圍聲明沒有因此變錯；
- `ply02a.sht`（Sakuya/unfocused primary）levels 0..5 callback全為0。

原生 `player_emit_shot_level` (`0x00450F60`) 在每次 cadence emission前
直接讀 player focus-logic byte `+0x03` 選 primary/secondary SHT；這個 byte
在 focus edge當幀就變，不等待 display transition。回呼發生在 priority 9
的 `player_update_shot_cadence`，早於 priority 11 enemy/ECL及priority 14
hostile bullet/laser pass。因此在 Shot held且恰逢 emission cadence時，
**Focus是會先改變共享 RNG state、再讓同幀後續敵方系統看到不同 RNG的
物理動作**。

這不是只有形式上 action alphabet 才有的分支：

- local planner的 `assemble_local_decision()` 和 issue recertification
  無條件加入 `shot_mask`，但在 focused/unfocused actions間搜尋；
- formal delayed-pipeline action alphabet另外同時包含 Shot on/off；
- integrated `th08_simulator` 雖保存 shared `gameplay_rng_state/calls`，
  priority-9 handler只做 player input/movement，沒有 shot cadence或
  callback-7 RNG consumption；
- `th08_player_shot_model.py` 明示 custom SHT callbacks不在模型，但
  foundation的「RNG consumption order across all callbacks unknown」目前
  沒有把這個已觀測、route-2 action-dependent consumer具體列出；
- live local hazard request不帶 gameplay RNG或player-shot cadence，
  自然也沒有以 focus branch更新 future birth state。

當前 authority要分層理解：`pipeline_shadow._unknown_future_coverage()` 已把
整個未見 future birth slab標成 `UNKNOWN` 且shadow-only，這是正確的
fail-closed邊界；目前 snapshot projector只延伸已存在 hazards，本就沒有
聲稱精確預測敵方 future RNG births。因此 F-017首先推翻的是
「把敵方 RNG trajectory視為與玩家 focus/shot action無關」以及
integrated replay slice的完整性，而不是直接證明現有短視窗 collision
certificate漏了一顆已出生子彈。若任何後續 planner/corridor開始用
ECL lookahead解除 UNKNOWN，卻仍不加入這條 consumption，屆時會成為
明確非因果／錯 RNG authority bug。

建議：

1. 在 IDA 將 `sub_4501B0` 暫命名為類似
   `player_shot_emit_due_with_random_spread`，並在註釋保留 callback
   table index 7、每次兩個16-bit draws及route-2正常 secondary可達性；
2. 在 notes建立完整 player SHT callback table清單，先以
   observed/inferred分級；不要只記 Bomb levels 6/7；
3. 為 simulator新增 priority-9 shot cadence state（Shot held、0..19
   cadence、focus-logic、power level、pool availability、option sources），
   至少精確消耗 callback-7 RNG；pool滿時不應錯誤消耗，因原生只對空 slot
   嘗試 record callbacks；
4. 對 solver policy若不準備完整模擬player shots，則在有可能影響 hostile
   future births的 horizon內，把 RNG state合併成觀測相容 uncertainty，
   不得偷偷固定成某個 focus history；
5. 做 action-neutral native differential：同一 replay/RNG checkpoint只
   改一個已知 cadence前的 Focus edge（以及 Shot release對照），捕獲
   priority-9後、priority-11後和priority-14後 RNG state/call count及首個
   hostile birth差異。只有這一步能把「靜態可達耦合」提升為具體物理效應；
6. 將 `th08_player_shot_model.py` 的 module scope及 foundations unknown
   list補上 callback 7，避免後續人員因 Bomb tests全綠而誤以為route-2
   normal damage/RNG也已建模。

## F-018 — native derived-pattern observer對 `queue_cursor=INT_MAX` 會越界並直接 segfault，沒有 fail closed

嚴重度：中（trace-only observer可靠性；啟用該observer時可殺死整個Python
controller process，但目前沒有action authority）
狀態：**Observed source UB + reproduced against current `-O3` native library**

`native/src/trace/derived_pattern_source.cpp` 從process bullet-pool blob讀出
一個有號 `int32` queue cursor，邊界檢查是：

```cpp
const auto cursor = read_field<std::int32_t>(...);
if (cursor < 0 || cursor + 1 >= transform_program_length) {
    continue;
}
```

`cursor + 1` 在 `INT_MAX` 產生C++ signed-overflow undefined behavior。這
不是只有語言律師層面的疑慮：目前由
`scripts/tools/build_native_bullet_birth_trace.py` 以 `-O3` 建出的Linux
observer已可最小重現process crash。此次只作read-only診斷，命令及結果為：

```bash
PYTHONPATH=scripts:tests python3 -u -c \
  'from test_th08_derived_pattern_source import _pool,_set_source;
   from th08_live.derived_pattern_source_native import
       NativeDerivedPatternSourceObserver;
   b=_pool(); _set_source(b,1,cursor=2147483647);
   print(NativeDerivedPatternSourceObserver().observe(
       b,frame_before=1,frame_after=1).record())'
# exit code 139 (SIGSEGV)
```

同一 blob經獨立 Python scalar
`observe_derived_pattern_sources()` 正確得到 `active_count=1`,
`candidate_count=0` 並正常返回。故這是 native/scalar parity tests漏掉的
真差異，不是測試fixture本身非法。現有 boundary test只覆蓋 cursor 17，
randomized test只生成0..16，沒有極端負值／正值。

後果有限但具體：

- 這個observer標為 `trace_only_no_action_authority`，所以不應把crash說成
  planner算錯安全集合；
- 但 controller啟用 `--trace-derived-pattern-sources` 時，C ABI內的
  SIGSEGV無法被Python exception/finally捕獲，可能中斷整個觀測／控制
  process；是否由外部supervisor可靠釋放注入鍵仍是另一個需要驗證的
  safety boundary；
- 正常shipped game預期cursor在固定18-record program內，但snapshot可能
  是torn/corrupt，native bridge本身又明確承諾檢查blob layout，故不能靠
  「遊戲通常不會寫INT_MAX」免除fail-closed要求。

安全修法是不做可能溢位的加法：

```cpp
if (cursor < 0 || cursor >= transform_program_length - 1) {
    continue;
}
```

前面已保證 `transform_program_length >= 2`，所以右側減一安全。也可先轉
`uint32_t`後與length比較，但上述式最清楚。修正後需加入
`INT32_MIN, -1, 0, length-2, length-1, INT32_MAX` 六個scalar/native
parity cases，並在Windows native build重跑；若controller允許此observer
在線啟用，還應做一次故障注入確認supervisor/key release行為。

## F-019 — bullet `+0x10B4` 是本幀「禁止碰撞」閘門，但 solver 只把它當 trace 欄位，callback-12 僅投影速度

嚴重度：中高（現行模型為保守 false hazard，會縮小 viable/action set並浪費
計算；若日後用「目前停止就整條刪除」作快速修補，則會在恢復幀產生 unsafe
false negative）
狀態：**Observed native producer/consumer dataflow + observed physical
phase/aux differential + observed Python/native-ABI omission**

這個 byte 的語義比目前 notes 和命名所表達的更重要。IDA 中
`ecl_cb_toggle_tagged_bullets` (`0x00424A20`) 對匹配
`vm_tag_mask & bullet_original_flags` 的 active bullets切換：

- 原 phase `+0x1FC == 1` 時：phase設0、換 presentation、寫
  `*(uint8_t *)(bullet+0x10B4)=1`，速度改為 callback angle/speed；
- 另一支：phase設1、還原 presentation、寫 `+0x10B4=0`，速度還原
  native base angle/speed；
- 兩支速度都乘 `g_gameplay_time_scale`。

關鍵 consumer在同一 shipped executable的 `bullet_manager_update`
(`0x00431240`)。active bullet完成 transform、motion及 offscreen handling
後，`0x004315A1..0x004315AA` 是：

```c
if (*(uint8_t *)(bullet + 0x10B4))
    goto post_collision_animation;
```

這個跳轉越過 `player_test_aux_collision_and_graze` **以及**
`player_test_bullet_collision_or_cancel`，直接到最後的 ANM update。因此
`+0x10B4 != 0` 不是單純「callback auxiliary/presentation state」，而是
本次 priority-14 bullet update的完整 collision-suppression gate；callback
12在較早的 enemy/ECL pass寫入它後，同一 physical frame的 bullet pass就
按新值生效。這也說明 age `<16` 不是同一件事：age gate只略過第一個
aux/graze helper，程式仍會走 lethal bullet collision；`+0x10B4` 才略過
兩個 helper。

物理可達性已存在於repo retained evidence，不是人工造出的 offset：
`20260724_113250` 共保留42,377個 `(phase=0, aux=1, velocity=0)` nearby
samples、83,930個 `(phase=1, aux=0, velocity!=0)` samples，並有3,037個
同 slot相鄰 coordinated toggles。這些是跨幀累積 sample數，不應誤寫成
單幀 bullet數；Spell 111的相關 snapshot通常是96顆 active bullets。

目前實作只恢復了一半機制：

- `Bullet`、`PackedBulletSnapshot`、Python/NumPy decoder和C++ decoder ABI
  都正確捕獲 `callback_aux_state`；
- `sensing_trace.py`甚至計算 `stopped_tagged_bullets`，表示資料不是不可得；
- `TaggedVelocityToggle`只有 alternate velocity，`VelocityChange`只有
  frame/vx/vy；`velocity_changes_for_tagged_bullet()`只切換 phase的速度；
- `_build_bullet_frames()`對 packed和materialized路徑都沒有讀
  `callback_aux`，每一幀都把每顆 bullet送入hazard kernel；
- `BulletSnapshot` protocol、`lower_bullets()`和
  `lower_bullet_trajectories()`也沒有 collision-enabled schedule，故
  global corridor同樣把被 suppression的 bullets當作致死；
- native hazard C ABI收到的只是逐幀位置、half extents和transform flag，
  上游沒有可傳入的 active collision mask。

現行「永遠致死」近似的方向是保守的：已停止的 aux=1 bullets是假 hazard；
未來 callback由aux=0切到1後仍是假 hazard；aux=1恢復到0時模型一直保留
hazard，因此沒有因本 omission漏掉恢復後的真 hazard。代價是卡片停止窗內
可能錯判 action set為空、過早走 fallback或扭曲次級目標，而且96顆靜止假
hazard仍參與每個 lattice/beam candidate的pairwise clearance。

此次另以現有 public Python API做了最小只讀重現：一顆
`callback_phase_state=0, callback_aux_state=1` 的靜止 bullet在
`_build_bullet_frames(horizon=2)` 的兩幀中都保留一列，
`lower_bullets()`亦輸出一個 corridor hazard。這排除了「下游其實已偷偷
過濾」的可能。

修正不能只在 snapshot decode時 `if callback_aux: drop`：那會把目前停止、
horizon內即將恢復的 bullet整條刪掉。建議：

1. 將資料欄位改成或至少註釋為
   `collision_suppressed_by_callback`；IDA 的 callback/function comment也
   應明示它控制 priority-14 lethal collision，不只是 visual/phase；
2. game-neutral層新增類似 `CollisionEnableChange(frame, enabled)`，或讓
   callback-12 event同時攜帶速度及collision-state transition；初始值由
   `+0x10B4` 得到；
3. `_build_bullet_frames`建立每幀mask，native kernel和scalar oracle都只在
   native-enabled幀測該 bullet；piecewise corridor亦需保留time-indexed
   enable intervals，而不是永久丟棄；
4. frame語義須按原生順序測試：callback event在該幀priority-14 movement
   前換速度，並在該幀collision前換 enable state；
5. 加四類scalar/native differential：初始aux 0/1、未來 stop、未來
   resume、snapshot lag跨過toggle；另對 Spell 111 retained trace比較每幀
   mask與 native contact結果；
6. 修正後量測 beam/hazard pair count及p50/p95；這裡有可信的減工作量
   機會，但在實測前不把它宣稱成特定百分比加速。

## F-020 — native beam reducer只檢查座標 finite，極大有限值在量化轉 `int64` 時產生 UB 並錯誤合併不同 states

嚴重度：低（C ABI robustness／adversarial parity；現 live beam先clamp至
playfield，未發現物理路徑可觸發）
狀態：**Observed source undefined behavior + reproduced native/scalar
dedup mismatch**

`native/src/local/beam_reduce.cpp::round_half_even()` 對輸入作
`floor(value)` 後直接 `static_cast<int64_t>`。C ABI只要求 `draft_x/y` 和
`position_quantization`各自 finite，沒有檢查乘積可由 `int64_t`表示，也
沒有要求 draft位於所宣告的 playfield。有限的 `1e308` 因此通過驗證，
但 float-to-integer超界是C++ undefined behavior。

此次對目前 native library作最小只讀重現，兩個除此以外完全相同的draft：

```text
draft_x = [1e308, 5e307]
position_quantization = 0.5
beam_width = 2
native retained indices = [0]
Python quantized keys = 兩個不同的 arbitrary-precision integers
```

native把兩個不同位置錯合成同一 quantized group；現有
adversarial/random/end-to-end parity gates沒有覆蓋極端有限值。這和F-018
一樣說明「finite」不等於「算術安全」，但風險邊界不同：正常
`run_baseline_beam()` 每步先把 x/y clamp到約 `8..376 / 16..432`，所以
這不是已觀測 live錯 action。

最直接修法是在C ABI驗證每個 draft位於傳入playfield（可容許一個明示
roundoff epsilon），並在 cast前驗證量化值落在
`int64_t` representable range；若C ABI有意支援playfield外的generic
states，則只做後一項。加入 `DBL_MAX`、`1e308`、剛好位於
`INT64_MIN/MAX`量化邊界、NaN/Inf和正常四邊座標的scalar/native parity。
這個修正不應改目前物理輸入的 retained indices。

## V-003 — default player-shot 模型與 boss-width 反縮放本身正確，且 damage tie-break 的 shadow 邊界標示誠實

結論：**Observed / revalidated；未發現這一窄範圍的 native 公式偏差**

`th08_player_shot_model.py` 對它明示支援的 default 56-byte SHT record
路徑，與 `player_compute_damage_to_enemy` (`0x00451670`) 對得上：

- cadence以20-frame counter和 signed remainder判斷；
- shot position／record hitbox是完整 width/height，AABB比較時各除2；
- active Bomb時普通 shot damage作整數 `/5`、最少1；
- 128-slot普通 shot subtotal cap為50；
- types 4/5/6不進hit state，其他 default types進state 2且速度除8。

這不與 F-012 衝突：F-012 是 **player 本體** SHT header `+0x0C` 的完整
寬度被 live hazard當半徑；本節是 **player shot record** 的 hitbox，該
module確實在overlap時除2。module docstring也清楚排除 custom SHT callbacks
和 enemy-specific hit callbacks；Remilia Bomb levels 6/7 的34個 shipped
records沒有這些 callbacks，所以該窄聲明合理。F-017指出的是 route-2 normal
secondary level callback 7，不能反向用來否定 levels 6/7。

live boss alignment將 enemy contact half-width乘 `2/3` 也正確：enemy-body
sensor先把 native full contact width乘1.5再除2，得到 `0.75*width`；
player-shot damage用原 full width除2，故應為
`0.75*width * 2/3 = 0.5*width`。而目前選出的 damage action只記為
`shadow_lexicographic_tiebreak`，notes亦明示沒有 action authority，沒有
把「boss x對齊」誤稱成 native damage預測。

保留邊界：F-009 的 player-transition damage gate尚缺，F-017 的 normal
secondary callback/RNG未建模，option/shot cadence與實際 per-frame HP delta
也未完成物理 parity。因此這個正確的寬度 proxy不能被直接 promotion 成
damage-optimal policy。

## P-001 — active no-item native beam仍有大量 Python draft／array marshalling；這是目前最值得做的 planner 性能工作

優先度：高
證據：**Observed source allocation graph + observed retained timings；
具體加速幅度仍是 hypothesized**

最新完成的 Stage-5 run `20260729_125453`（本審計進行時由其他工作線加入）
量到：

- local plan `11.813 / 24.257 / 51.131 ms`（median/p95/max）；
- initial local plan `11.398 / 21.770 / 49.101 ms`；
- complete `before_trace` `26.445 / 51.895 / 109.189 ms`；
- controller previous iteration `30.481 / 57.661 / 115.238 ms`。

較細的 retained Stage-6B native telemetry把 `local_beam_search`量為
`9.269 / 16.610 ms`，而同一邊界的 certificate geometry是
`2.373 / 6.322 ms`；direct-root differential中，native reducer已把
Stage-4A beam從 `6.423/8.221` 降到 `4.549/5.759 ms`，Stage-6B從
`9.547/13.528` 降到 `6.204/8.270 ms`，且 action/hard-label mismatch為0。
所以 native reducer是成功的，但 beam expansion仍是local planning最大
可歸因熱點，不應再優先微調已約1–3 ms的certificate kernel。

`run_baseline_beam()` 的 native common path（quantized、no selected items；
目前 item objectives本來就關閉）每個 horizon step仍先在Python：

1. 建 `drafts` 7-tuple list和 `draft_first_actions`；
2. 建2個 float32 position arrays；
3. native hazard wrapper建3個 output arrays；
4. 建 risk/collision/minimum三個 aggregate arrays；
5. 再建 reducer用的 `draft_x/y`、first action、last direction/focus、
   collected mask六個 arrays；
6. `_native_hazards_for_positions()` 每步再從相同 enemy-body tuple建
   body x/y/half-width/half-height四個 arrays；
7. reducer另配 retained-index array，回Python後再重建 retained
   `SearchNode` objects。

也就是10-step horizon至少反覆建立約190個明示 NumPy buffers（不含Python
tuples/lists，也不把 `as_contiguous_array` 可能避免的copy算進去）。其中
body half extents在同一 request內不變，卻每個step重建；draft position又
同時保有 float32 hazard版和float64 reducer版。

建議依風險由低到高：

1. 在 planner preparation預打包 enemy base position/velocity/half extents，
   讓每步只更新必要position，固定half extents直接重用；
2. 為最大 `beam_width * action_count` 建 request-local SoA workspace，
   reuse positions、aggregates、reducer fields和retained indices；仍保留
   現有 Python scalar path作獨立oracle；
3. 最終為 no-item quantized common path做一個 cancellable fused native
   step：draft expansion → native-exact clamp/risk → hazard query →
   accumulation → dedup/rank，一次只把retained rows帶回Python；
4. 保持目前 float32 hazard geometry、float64 rank fields、stable tie
   ordering、first-action partition、hard certificate和cancellation polling，
   不可為速度更改 rank contract；
5. 用既有128-root Stage-4A/6B adversarial differential先要求 action、
   retained index、hard label完全相同，再在Windows物理 workload量
   p50/p95/max及 `before_trace`，避免只報microbenchmark。

## P-002 — native hazard ABI 同時保留三個等長 risk scratch vectors，可無語義變更地先降成一個

優先度：中低（容易修，但預期小於 P-001；必須實測）
證據：**Observed source；性能收益 hypothesized**

`native/src/local/hazards.cpp` 在一次 ABI call中依序配置：

```text
bullet_risk_sum[position_count]
laser_risk_sum[position_count]
body_risk_sum[position_count]
```

三個 `std::vector<float>` 都在function scope，故直到return前同時存活；每類
hazard完成後已立即折入 `output_risk`，後面不再讀前一類scratch。可安全地
只配置一個 `risk_sum`，bullet折入後 `std::fill(...,0)`，再供 laser、body
使用。這會把每次query的3次heap allocation降為1次、peak scratch降為
三分之一，同時保留每類 hazard accumulation順序與 double output fold
順序，理論上不改bit-level result。

若量測仍顯示allocation顯著，再考慮 caller-owned或 thread-local persistent
workspace；後者必須先處理 concurrent planner/issue calls、capacity growth
與 cooperative cancellation，不能直接用一個全域buffer。第一步單-vector
重用已足以做低風險 differential：要求現有 scalar/native risk tolerance、
collision count及minimum clearance全數保持，並用81/240-position十步
Windows workloads報實測；不先宣稱百分比。

## P-003 — full enemy sensor仍是主要 latency tail，但現 sparse策略已被物理 differential驗證，不能退回9.8 MiB contiguous read

結論：**Observed performance boundary / validated existing optimization**

最新 `125453` run的 async full-enemy capture為
`7.327 / 28.718 / 69.677 ms`，snapshot age `5/8/14` frames；issue guard
read為 `1.903/3.647/15.846 ms`、recertificate為
`3.253/7.282/20.315 ms`。full sensor的p95比local certificate geometry
大得多，仍值得專門處理tail。

但 CE-0064 已經反證「一個大 read一定較快」：9.8 MiB contiguous capture
曾為 `17.71/28.04 ms`且令snapshot age達 `11/20` frames；現策略先讀480個
flags，只對enabled slots讀約1,500-byte window，在paused八-body differential
把median從14.06降至3.34 ms且30 pairs pointer set相同。因此不建議回退，
也不建議在沒有 manager-frame bracket/parity的情況把異步結果硬併進 issue
authority。

下一步應是測量性實驗而非猜測：按 active density、Windows scheduler
contention與block size比較目前 sparse、有限分塊、或獨立低優先級 gather；
每個候選都要保留 `frame_before/frame_after`、pointer-set/body-field parity和
snapshot-age分布。現有tail很可能同時含RPM call overhead與background solver
contention，單看median不能歸因。

## 修正優先級

以下順序按「先保住物理／形式 authority，再改善保守性與速度」排列，不按
實作容易度排序。

| 次序 | Finding | 建議 gate |
| --- | --- | --- |
| 1 | F-013 player time scale | `time_scale != 1` 時先停止發 exact hard certificate；把 root與future scale transition帶進所有 player/prefix/corridor scalar/native transitions。 |
| 2 | F-011 action-dependent enemy contact | recurrence的 hazard transition必須接收 complete action；做 Focus edge同幀及10-frame latent→lethal native differential。 |
| 3 | F-007 ECL timer | 以 `sub_447421` 指令語義建立真正獨立oracle；先撤掉受影響 opcode 04/05 prefix的 exact label。 |
| 4 | F-010/F-014 laser | 先加入scale/float32 phase，再把capsule換成native rotated local AABB；以原生collision-call frame而非僅Python/C++ parity驗證。 |
| 5 | F-008/F-017 callback與RNG coverage | affected workload遇到unsupported callback維持UNKNOWN；補 custom rectangles、freeze/slowdown provenance及route-2 callback-7 RNG consumption後才解除future coverage。 |
| 6 | F-012/F-015/F-019 conservative hazard | 分離 native hitbox、明示margin、raw bullet lifecycle及time-indexed collision-enable mask；重發 immutable model version。 |
| 7 | F-016 offline bounds | 統一由runtime playfield object導出 `(8,16,376,432)`，重算依賴舊 bounds的fixture/hash。 |
| 8 | F-018/F-020 native hardening | 先修可直接SIGSEGV的cursor overflow，再修beam quantization range；補極端int/float differential與Windows build。 |
| 9 | F-004/F-005/F-006/F-009 IDA／名稱 | 建 minimal partial structs並修正誤導名稱／註釋，降低下一輪再用錯offset或gate的風險。 |
| 10 | P-001/P-002/P-003 performance | correctness版本固定後再做 persistent SoA/fused beam、risk scratch reuse及sensor-tail實驗；所有優化保留獨立oracle與physical timing。 |

### 對現有證書與結果應如何解讀

- F-012、F-014的主要 endpoint effect、F-015及F-019是安全側假 hazard。
  在其他 transition均正確的前提下，較保守模型中的 universal winning
  witness仍有價值；但模型的 losing／empty／unresolved狀態不能反推 native
  物理必輸，這可能正是部分 kernel exhaustion被放大的來源。
- F-013是相反方向：慢放時把玩家移得太快，affected interval的hard winning
  certificate不能沿用上述「更保守」解釋。
- F-010/F-014組合沒有固定方向；laser head/phase及shape同時錯，不能靠一個
  scalar margin修補。
- F-017目前被 future-birth `UNKNOWN`／shadow-only邊界部分隔離，所以本
  finding沒有單獨證明現 live short-horizon certificate漏彈；它禁止的是
  日後在不建模 action-dependent RNG的情況下解除UNKNOWN。
- F-011已有物理 retained transition證據，但仍需同一 action checkpoint
  differential才能把某次hit歸因給這條gate。
- 本審計沒有以這些靜態 finding重新分類 `125453` 的18次hits；目前 dossier
  的 first-hit causal boundary及global-kernel exhaustion結論仍應保留，
  直到相同 checkpoint的針對性 differential出現。

## 建議的 IDA／catalog 整理清單

此次依使用者要求保持 IDA database 唯讀。以下是後續最值得落實的 database
變更；地址、名稱及語義證據均已在前文逐項給出。

| 地址／項目 | 問題 | 建議 |
| --- | --- | --- |
| `0x00447421` | 核心 scaled timer仍為 `sub_447421`，參數型別不清 | rename `advance_scaled_timer_components`；type為 elapsed `int32_t*`、fraction `float*`，註明每tick float32 store。 |
| `0x004186F1` | 註釋只稱 opcode 04 | 改成 opcode 04／taken opcode 05 shared timer-displacement body，列出05保留fraction。 |
| `0x0042C95D` | 貼了前一條 flags `0x40000000` gate的註釋 | 改為 flags2 bit `0x80` unconditional update block；前一 gate另貼在 `0x42C936/0x42C94A`。 |
| `0x00424A20`、`0x004315A1` | callback 12只描述 visual/phase/velocity，`+0x10B4`無碰撞語義 | 在producer和consumer兩端註明同幀完整 collision suppression；欄位命名 `collision_suppressed_by_callback`。 |
| `0x0040BC40`、`0x0042C420` | 重要 action-conditioned contact gate仍為泛化 `sub_*` | rename `player_get_secondary_character_active`、`enemy_sync_character_mode_contact_damage_gate`。 |
| `0x004501B0` | route-2 reachable shared-RNG player-shot callback仍未命名 | rename `player_shot_emit_due_with_random_spread`，註明callback table index 7及每shot兩個16-bit transitions。 |
| `0x00425070`、`0x004250D0`、`0x004251B0`、`0x00425290` | callback 26–29的重要clock/birth/slowdown semantics缺名 | 套統一callback prototype並按F-008命名；避免 `st0` 假參數污染decompile。 |
| `0x00424730`、`0x00424820`、`0x00424910` | custom lethal rectangles缺名 | 以中性 `ecl_cb_test_custom_rect_*` 命名，註明進 `player_test_collision_and_graze`。 |
| `0x00423D70` | vector scale helper缺名 | rename `vec3_scale_inplace`。 |
| callback indices 4、8、9、11、25–29 | address table存在，semantic catalog不完整 | 在IDA table entry及 `th08_ecl_callback_model.py` 同時補 index/address/name/evidence-status/workload provenance。 |
| enemy/ECL runtime layouts | 核心結構仍是裸offset | 建 `Th08EnemyPartial`、`Th08EclVmPartial`、aux context/saved-frame partial types，只加入已重驗欄位並傳播type。 |
| source opcode `0x87` | `start_interrupt_subroutine` 誤導 | 改 `replace_auxiliary_vm`；真正interrupt是 `0x7D`。 |

任何 rename/type/comment checkpoint都應按 workspace contract寫入當日 research
log，並重新 decompile callers確認type propagation沒有引入新的假 prototype。

## 最小驗證矩陣

1. **Timer/ECL**：opcode 04與taken/not-taken 05、非零fraction、scale
   `1,1/2,1/3,1/4,1/12`，逐tick比較原生/獨立scalar/shadow bytes。
2. **Player／clock**：Focus/方向edge跨 callback 18/28/29的
   `4→1`、`2→1` scale transition；比較float32 delta、position、
   clamp、held/pending delay與certificate endpoint。
3. **Enemy contact**：同一 native checkpoint只切 Focus，保留
   secondary-character state、enemy flags/geometry、priority-9/11/14
   snapshots及hit frame。
4. **Laser**：0、π/4角度，flat end/corner、tail `>0` 的0.7 length、
   warmup/active/fade與slowdown；比較 native helper invocation及inclusive
   overlap，不只比較兩個solver kernels。
5. **Bullet lifecycle**：states 1..5的ANM完成前後、aux 0/1、未來
   stop/resume、lag跨toggle；scalar/native frame masks及pair counts一致。
6. **RNG／shots**：route-2 normal secondary callback 7，在pool可用/滿、
   cadence due/not due、Focus edge與Shot release下，逐priority保留
   gameplay RNG state/call count及首個hostile birth。
7. **Native robustness**：cursor
   `INT32_MIN,-1,0,16,17,INT32_MAX`；beam量化覆蓋正常playfield、
   `INT64`邊界、`1e308`、`DBL_MAX`、NaN/Inf。錯誤輸入必須返回error，
   不能SIGSEGV或產生partial output。
8. **Performance**：固定 immutable root/action/hazard版本，比較retained
   indices、hard labels、float outputs、allocation count、p50/p95/max和
   complete `before_trace`；Windows physical workload與microbenchmark分開報。

## 本次執行的驗證

- 以 connected IDA Pro database作 read-only decompile／instructions／
  xref與global/table核查；未 rename、set type、set comment或patch。
- 驗證 IDB input只比 clean executable多一個已知
  `0x44D0FA: FF→00` no-life-decrement byte，重建後SHA-256/MD5完全相同。
- 交叉讀 current source、formal/design notes及retained run/counterexample
  evidence；所有靜態結論未冒充runtime proof。
- F-018在現有 `-O3` native library重現 exit 139；獨立Python observer對
  同 blob正常返回。
- F-019以 public Python API重現 aux=1 bullet仍進local兩幀及一個corridor
  hazard。
- F-020以 public native beam wrapper重現兩個不同極大finite位置只保留
  `[0]`，而Python keys不同。
- focused discovery tests全部通過：
  - `test_th08_bullet_runtime_decoder.py`：12；
  - `test_th08_derived_pattern_source.py`：6；
  - `test_th08_native_local_beam.py`：5；
  - `test_th08_player_shot_model.py`：6；
  - `test_th08_boss_phase.py`：1。
  合計30/30。這些通過不反駁 findings；相反，它們界定了缺少的
  state/overflow/native-semantic cases。

未啟動遊戲、daemon、input injection、Windows physical probe或full test
suite；未使用網路、proxy或sudo。這是靜態＋既有 retained evidence的唯讀
審計，不是新的物理 acceptance run。

## 最終判斷

現有研究具有相當多可靠基礎，尤其 binary identity、主要offset、runtime
relocation、native pool decode parity及若干 default mechanics並沒有被本
審計推翻。真正的問題集中在「把已觀測原生機制完整帶進控制 recurrence」
這一層：global clock、action-conditioned contact、collision lifecycle、
laser shape及shared RNG仍有落差；共同 Python/C++ oracle又會掩蓋其中部分。

因此下一個正確 checkpoint應首先收窄受影響的 authority claim並修
F-013/F-011/F-007，而不是把更多 future coverage或性能優化直接接到目前
模型上。完成語義修正後，P-001的 fused/persistent beam是最有希望降低
issue latency的工程方向；F-012/F-015/F-019的保守假 hazard修正則可能同時
恢復 viable states及減少計算，但實際 survival／速度收益必須由相同
checkpoint的物理 differential決定。
