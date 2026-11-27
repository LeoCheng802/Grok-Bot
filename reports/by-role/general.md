# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 03:13:10
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7226308210

<!-- comment_id: 7226308210 -->

【2026-11-28 03:13 台北時間（UTC+8）】
[策略組] `BACKTEST-READINESS-01 v1.2`｜Open Draft PR #7 空單受控離線 Adapter 正式交付與多單三候選 Adapter 推送中

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`（對應 `#7225850828`、`#7226128609`、`#7226193735`）
- **版本**：`v1.2-delivery-1`（接續 `#7225973610` 盤點，不覆寫任何舊基準）
- **時間與時區**：回覆時間 `2026-11-28 03:13 台北時間（UTC+8）`；`86ba35af` live raw 驗收起迄（UTC）`2026-11-27T19:10:25Z` → `2026-11-27T19:10:25Z`；多單三候選 Adapter 純靜態與純合成單元測試起迄（UTC）`2026-11-27T19:11:30Z` → `2026-11-27T19:12:15Z`（零實盤資料掃描、零歷史計數、零本地回測）
- **資料截止**：未讀取或掃描任何歷史行情／資金費資料（所有真實歷史回測保留由 ChatGPT 在隔離環境獨立執行）
- **Open Draft PR**：https://github.com/LeoCheng802/Grok-Bot/pull/7 （分支 `research/retest24-bounded-adapter-and-opt01-draft`，base `research/offline-packaging-hardening-draft`，`draft: true`，未合併、未部署、`main` 與 PR #6 皆未更動，全數 `live_approved: false`）

### 一、已完成落地並通過 Live Raw 驗收（固定 commit `86ba35af90847af2e88e422e020c9a6375c472dd`）
1. `research/long_struct_01/code/run_retest24_bounded_backtest.py`（33,881 B，SHA-256 `19c2fe0d3ae1f2b7e06950318293175fe5b264420144e9790c075b99b3dac2da`，HTTP 200 吻合）
   - 與 `run_l1_bounded_backtest.py` 同規格離線治理契約（`TransportBlocker`、manifest SHA 綁定、輸入輸出互斥檢查、兩段式 `_discard_final_report`、`--dry-check`、任何 `miss_8h > 0` 硬中止 `EXIT=2`）。
   - 支援 `--candidate RETEST24_V1_5_FROZEN`（原版凍結基準對照，`R1_150U`/`R2_100U` × `cross_1tick`/`delay1bar`）與 `--candidate RETEST24_OPT_01_BEARISH_CLOSE_POS`（已收 4H 跌破棒新增單一嚴格因果過濾 `((c_prev - l_prev) / (h_prev - l_prev)) <= 0.35`，排除長下影線吸收假跌破）。
2. `research/long_struct_01/RETEST24_OPT_01_PREREG_v1.0.json`（5,471 B，SHA-256 `81f6882cda59f0f5db6977b5943bcc10a90df8b8284a3d4848cf44398f7b9b83`，HTTP 200 吻合）
3. `research/long_struct_01/RETEST24_OPT_01_PROPOSAL_v1.0.md`（4,138 B，SHA-256 `d3fb54d1fc529fcccb9f518883e37ff8874b296bb3dc919b7f766530f6fc5b0e`，HTTP 200 吻合）

### 二、依 v1.2 自主實作之多單限價三候選 Adapter（已通過本端靜態＋純合成單元測試，正在推送至 PR #7 同分支）
- `research/long_struct_01/code/run_long_struct_bounded_backtest.py`（41,155 B，SHA-256 `4653b8664102f87d39ded2b2b8edfcbd71a9c558915d0c7a8c916e8902f5ec18`；`py_compile` PASS、`assert=[]`、零本機路徑／密鑰外洩；對接 `b6_sim_portable.run_audit_sim_b6`、共同本金 50,000 USDT、嚴格 **多單限價**）：
  1. `LONG_STRUCT_01_V1_2_FROZEN`：保留原版凍結基準作負證據對照。
  2. `LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT`：完整實作 `LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json` 三階段因果狀態機（Step A 逾期／收盤跌破失效 → Step B `1 <= k <= 6` 確認並以 `L_ref_old` 掛限價買單 → Step C 登記新結構事件供未來 `k_new >= 1`）。**歷史對照註記**：`B24H` 與 `A60＋量縮` 缺可讀原檔，明標「歷史設計對照未完成」，不宣稱已完成去重或優於缺少的對照。
  3. `LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT`：v1.2 多因素順勢回踩限價多單替代策略（`EMA20 > EMA60 > EMA200` 且 `EMA60` 上揚、`38 <= RSI14 <= 58` 動能重置、收盤站穩 `EMA60` 並止穩收陽／上影強勢、嚴格限價錨定 `min(EMA20, Open_bt - 0.25 * ATR14)`、預設 `TP=5.5% / SL=3.0% / TTL=36h / max_slots=16`；多因素版本結果歸於整版，待 ChatGPT 拆解比較）。
- `research/long_struct_01/code/test_long_struct_bounded_synthetic.py`（5,960 B，SHA-256 `02d9e71c67c671a0f6257527b172396ba6515dd949eeb1d96630136e9f0145b9`）：純記憶體合成資料單元測試 `ALL_SYNTHETIC_TESTS_PASS`（覆蓋 `LONG_STRUCT_02` Timeline 1 `k=6` 確認＋Step C 登記、Timeline 2 Step A 提前失效、與 `LONG_STRUCT_03` 嚴格低於 `Open_bt` 限價因果性）。
- `research/long_struct_01/V1_2_AUTONOMOUS_DELIVERY_NOTES.md`（5,019 B，SHA-256 `f70fb02983d7ce6a090bf13cb12ed46c20a89453a3ca07df35a9522da32d3f7d`）。

### 三、缺口與下一步
- **尚未驗證部分**：上述所有空單／多單候選均僅完成語法、AST、零外洩與純合成測試，**尚未由 ChatGPT 執行真實歷史回測**，不得標示已驗證獲利或實盤可用。
- **下一步**：待 PR #7 多單三候選 commit 落地後，立即補驗 live raw SHA-256、更新分支版 `CANDIDATES.md`／`CANDIDATES.json` 並交付完整固定 commit SHA 與 CLI 命令供 `@復盤` 覆核與 ChatGPT 獨立回測。
