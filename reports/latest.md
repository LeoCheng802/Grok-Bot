# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 02:53:19
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7225973610

<!-- comment_id: 7225973610 -->

【2026-11-28 02:52 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.1｜首輪候選優先排序、負證據分析、具體阻礙與下一步提案

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`（對應 [Issue #1 #7225850828](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7225850828)）
- **版本**：`v1.1`（策略組首輪分析與阻礙盤點；純靜態審查，未改動策略碼、未執行行情掃描／歷史計數／回測）
- **時間與時區**：2026-11-28 02:52 台北時間（UTC+8）｜靜態分析起迄（UTC）：`2026-11-27T18:50:00Z` → `2026-11-27T18:52:33Z`
- **固定對照基準**：
  - `main`：`1f38b000fe881044f02d0469ab08a6239f91bb31`（`CANDIDATES.md` / `CANDIDATES.json`）
  - [PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6)（Open Draft）：`3f67bd87fe5db2ec64d97b543fe780fa2f505f6f`
  - `LONG-STRUCT-02` 預登記 `v1.2`：`5ca80cbcf45ebe9425516f658a7de838882403f1`（SHA-256 `246cda1c8a23bea5d580b8b1e20bc53393dcd8483db85137fe5389a6d46bb06e`）

### 一、既有候選與基準現況、負證據與首輪優先排序
1. **基準 `FIB-4H-LONG-V3`（淘汰 `NO-GO`，僅作接線驗證對照）**
   - 檔案：`research/long_struct_01/code/FIB_4H_Long_v3.py`（PR #6 `3f67bd87`，SHA-256 `17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7`）
   - 現有 adapter：`run_l1_tp_study.py`（`e920b95356db3636cc6083b1b6254042ee1f78fa963d4f7a66e86c52b23c75eb`；執行組正依 v1.1 A 段整理有界入口）
   - 結論：`L1` 與 `LONG-LOOP-01` 負證據已確立，維持 `NO-GO`、停止原多單結構續調，僅供 ChatGPT 驗證離線接線與撮合／成本口徑。

2. **第一優先（P1，空單凍結候選）：`RETEST24-R1-R2 v1.5`**
   - 檔案：`research/long_struct_01/code/RETEST24_R1_R2_Switchable_v1_5_auditfix.py`（PR #6 `3f67bd87`，SHA-256 `c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04`）
   - 既有研究去重與負證據：`R1`／`R2` 屬同訊號倉位對照；既有 `B1–B8` 已測試維度含去 `EMA55`（B1）、`TTL`（B2）、`RSI` 區間（B3）、進場 offset（B4）、觸價 vs 穿價 1 tick（B5）、1-bar 延遲進場（B6）、tick 與出場順序敏感度（B7/B8），後續優化不得重複堆疊這些軸線。核心負證據為保守延遲進場（`delay1bar_cross_1tick`）下邊際優勢翻負，顯示原始訊號對進場時效高度敏感。
   - **具體缺口**：目前公開庫 PR #6 僅含底層 `engine/` 4 支模組，**尚無 `RETEST24-R1-R2 v1.5` 的獨立離線有界回測 adapter**（`run_l1_tp_study.py` 僅接 `FIB-4H-LONG-V3`）。

3. **第二優先（P2，多單凍結候選）：`LONG-STRUCT-01 v1.2`**
   - 檔案：`research/long_struct_01/code/long_struct_01_v1_2_isolated.py`（commit `fbe475402ff568eac2684bf4d97f49de579e9a6b`，SHA-256 `4ea731a4f5b62dfa0b435e5a03a028c5c2bb0b190a6076e03442f5856fca073b`）
   - 負證據保留：2025-11 五檔診斷窗（分母 900 棒）中，獨立通過 `EMA60`（169）、`EMA60+RSI(55–85)`（123）與獨立通過 `sweep`（109）皆非零，但同棒交集為 `0`。完整保留負證據，**不採放寬門檻換取交易量**。
   - **具體缺口**：目前僅有訊號構建器與接線測試，尚無對應離線回測 adapter；且問題核心為同棒結構碰撞，不建議對 `v1.2` 做純參數微調。

4. **第三優先（P3，多單結構假說，受阻待去重）：`LONG-STRUCT-02 v1.2`**
   - 檔案：`research/long_struct_01/LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json`（`PROPOSED_NOT_EXECUTED`，`has_script: false`）
   - 核心假說：維持多單限價與 EMA 允許前提，將掃破收復（`t_sweep`）與動能確認（`t_confirm`，`k∈[1,6]`）分時點解耦，對症處理 `LONG-STRUCT-01` 同棒零交集問題。
   - **具體阻礙（硬卡點）**：已盤點公開庫與現有工作區，**均無 `B24H` 與 `A60＋量縮` 之可讀規則或腳本檔**，因此同版設計去重尚無法完成；依 `#7225850828` 紅線，未完成去重前**不得直接實作腳本**。

### 二、尚未由 ChatGPT 回測之項目與已做靜態檢查
- **已做靜態檢查**：僅完成上述既有固定 commit 檔案與負證據文獻之靜態比對，零程式碼異動、零行情掃描／計數／回測。
- **尚未由 ChatGPT 獨立回測**：`FIB-4H-LONG-V3` 完整基準接線回測、`RETEST24-R1-R2 v1.5` 離線基準回測、`LONG-STRUCT-01 v1.2` 全期離線回測，以及任何新優化候選（皆維持 `待驗`／`live_approved: false`）。

### 三、具體缺口與建議下一步
1. **解除 `LONG-STRUCT-02` 去重阻礙**：請提供 `B24H` 與 `A60＋量縮` 之可讀規則摘要或對應檔案，策略組即可補完同版去重對照，再決定是否進入隔離實作。
2. **P1 路線準備（空單 `RETEST24-R1-R2`）**：待執行組完成 v1.1 A 段共用有界離線入口與資料／manifest 契約後，策略組將優先對齊同一介面，準備 **(a)** `RETEST24-R1-R2 v1.5` 凍結基準之純離線有界 adapter（供 ChatGPT 獨立跑出基線），並提出 **(b)** 不重複 `B1–B8` 軸線之單一主要假說隔離優化提案供 ChatGPT 審核後實作。
3. **紅線重申**：PR #6 維持 Open Draft、不合併、不部署、不交易、不改實盤風控。
