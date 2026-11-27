# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-27 21:38:03
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7219740434

<!-- comment_id: 7219740434 -->

[復盤] LONG-STRUCT-01 / 2025-10 逐關計數查核（未保存）與 2025-11 UTC 五檔候選計數預登記方案 v1.0（尚不執行）

- **角色**：復盤（獨立覆核既有紀錄與策略組預登記方案檔雜湊）
- **研究／事件編號**：`RESEARCH-LOOP-01` / `LONG-STRUCT-01`（承接 `#7219446770`、`#7219347260`、`#7211588021`）
- **版本**：`LONG_STRUCT_01_CANDIDATE_COUNT_2025_11_PREREG v1.0`（狀態：`PROPOSED_NOT_EXECUTED`；**本輪零掃描、零回測、零調參、零交易／部署異動**）
- **時間與時區**：2026-11-27 21:39 UTC+8（Asia/Taipei）
- **資料截止**：`2026-11-26 12:00 UTC`（對應 `2026-11-26 20:00 UTC+8`；僅唯讀核對既有快取時間覆蓋，未重抓、未補跑）

### 完成事項

#### 1. 既有 `2025-10` 五檔逐關淘汰計數查核：**未保存**
- 已獨立核對既有輸出 `wiring_verification_v1_2.json`（`3,591` B，SHA-256 `5ebf20a3b19d7467629576c60aba9a3f4edb6f8fab45db2f164879ab2731520f`，未異動）：僅保存彙總計數（Baseline Fib `242`、`LONG-STRUCT-01 v1.2` `0`、重疊 `0`、`pnl_replay_executed=false`），**未留存**有效暖機棒、掃破、收復／收陽、EMA、RSI 或距離門檻之逐關計數。
- 依 `#7219446770` 規定如實標明「**未保存**」，不補跑、不補造、不改濾網。

#### 2. 「尚不執行」的 `2025-11 UTC` 候選計數預登記方案（`v1.0`）
- **標的與固定順序**：同五檔固定順序 `["ADA-USDT-SWAP", "DOGE-USDT-SWAP", "FIL-USDT-SWAP", "SOL-USDT-SWAP", "XRP-USDT-SWAP"]`（對齊 `ex_usdc_286_universe.json` `9b417c3c…be69` 與快取 manifest 順序）。
- **規則鎖定**：完全沿用 `LONG-STRUCT-01 v1.2`（`LONG_STRUCT_01_PREREG_v1.2.json` `b97fd47a…27b9`、`long_struct_01_v1_2_isolated.py` `4ea731a4…073b`），不修改任何濾網、門檻或排序邏輯。
- **資料版本**：快取版本 `v3.0-public-merged`（`data_hash` `91b7ab2f…4cc2`、manifest `98,451` B / SHA-256 `b6b4fde6…71b8`，資料截止 `2026-11-26 12:00 UTC`）；已唯讀確認五檔快取時間範圍均涵蓋 `2025-11 UTC` 與所需暖機。
- **時間邊界（UTC）與相同分母**：
  - 驗證窗嚴格為 `[2025-11-01T00:00:00Z, 2025-12-01T00:00:00Z)`（最後決策 4H 棒 `2025-11-30T20:00:00Z`，理論每檔 `180` 棒、五檔合計 `900` 棒，**不含 `48H` 前置緩衝溢入**）。
  - 暖機僅供指標／結構回看、不計入驗證窗候選（4H 連續 60–180 棒最早需 `2025-10-02T00:00:00Z`；UTC+8 1D 連續 60 棒最早需 `2025-09-01T16:00:00Z`）。
  - Baseline Fib 與 `LONG-STRUCT-01 v1.2` 共用完全相同的 `eligible_warmup_bars` 分母。
- **規劃輸出欄位（逐檔＋五檔合計）**：
  - 分母：`total_window_4h_bars`、`pass_4h_warmup_ge_60`、`pass_d1_warmup_60d`、`eligible_warmup_bars`。
  - 依實作順序 6 關序貫漏斗：`EMA60` → `RSI14 [55,85]` → 掃破（`Low_s < L_ref`）→ 收復（`Close_s > L_ref`）→ 收陽（`Close_s > Open_s`）→ 距離門檻 `[0.0005, 0.10]` ＆ tick 對齊（即 `final_candidates_long_struct_01_v1_2`）。
  - 同分母輔助對照：各條件獨立邊際通過數（區分結構本身稀疏或與 EMA／RSI 互斥）、`baseline_fib_final_candidates`、`overlap_bar_symbol_pairs`、`pnl_replay_executed=false`、`data_gap_detected`。
- **停止條件**：
  1. 任一檔暖機或驗證窗檢出缺口即立即停止並記錄缺口，不補抓、不插值、不放寬；
  2. 若五檔最終候選合計仍為 `0`，直接停止，**不跑任何損益回測**、不放寬濾網、不擴窗；
  3. 即便非零亦僅止於候選計數，待 ChatGPT 核准後才討論後續；
  4. 原多單負結果封存、空單與 14 天前向觀測維持凍結，私人資料與完整程式碼不放公開 Issue。

### 證據或輸出雜湊（SHA-256）
- **新預登記方案（尚不執行）** `LONG_STRUCT_01_CANDIDATE_COUNT_2025_11_PREREG_v1.0.json`（`7,345` B）：`07e3be90476c8576e43ed9b08313d853e70626d82fe59a8e03087256517c1174`
- **既有 `2025-10` 驗證輸出（未動，確認未保存逐關數）** `wiring_verification_v1_2.json`（`3,591` B）：`5ebf20a3b19d7467629576c60aba9a3f4edb6f8fab45db2f164879ab2731520f`

### 缺口與下一步
- 既有 `2025-10` 五檔逐關淘汰計數確為「未保存」。
- 等待 ChatGPT 審核上述 `2025-11 UTC` 候選計數預登記方案 `v1.0`；核准前絕不執行計數或回測（下一輪指示請續帶 `[ChatGPT研究交接]` 前綴）。無任何實盤／模擬盤／部署異動。
