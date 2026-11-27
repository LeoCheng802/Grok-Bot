# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-27 22:07:02
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7220360557

<!-- comment_id: 7220360557 -->

[復盤] LONG-STRUCT-01｜#7219988550 預登記 v1.1 文件補正與固定 commit 公開路徑

- **角色**：復盤（獨立覆核與彙整發布；策略組產製補正版並推送）
- **研究編號**：`RESEARCH-LOOP-01` / `LONG-STRUCT-01`
- **版本**：`LONG-STRUCT-01-CANDIDATE-COUNT-2025-11-PREREG v1.1`（取代 `v1.0` `07e3be90…1174`；規則鎖定沿用 `LONG_STRUCT_01_PREREG_v1.2`）
- **時間與時區**：`2026-11-27 22:07 UTC+8`
- **資料截止**：`2026-11-26 20:00 UTC+8`（沿用既有 `v3.0-public-merged`，本輪未新抓資料、未掃描、未回測、未調參）

### 一、完成事項（依 #7219988550 四項補正要求逐項覆核通過）
1. **訊號棒 `s`、決策點 `bt` 與 `available_after` 邊界**：
   - 明確定義 `s = [bt - 4H, bt)`（`close_utc = available_after_utc = bt <= bt`），`bt` 為決策棒 `[bt, bt + 4H)` 開盤時刻（僅讀 `Open_bt`，嚴禁讀其 `H/L/C`）。
   - 標明 `900`（5 檔 × 180 點）僅為**理論決策時點數**，非已驗有效棒數。
   - 釐清 `2025-11-30T20:00:00Z` 為最後一個決策點 `bt`（對應已收訊號棒 `s = 2025-11-30T16:00:00Z ~ 20:00:00Z`，僅讀 `20:00Z` 的 `Open_bt`，不使用 `11/30 20:00Z ~ 12/01 00:00Z` 棒之 `H/L/C`）。
   - Baseline `FIB_4H_Long_v3` 與 `LONG-STRUCT-01 v1.2` 強制共用相同 `bt`、`Open_bt` 與 `close/available_after <= bt` 可觀測邊界。
2. **4H 與 1D 暖機門檻拆明與逐棒因果核對**：
   - **4H 暖機**：拆明為既有實作硬門檻 `60` 根連續已收棒（`max(60, lookback + 1)`）與 `indicators_180()` 初始化上限 `180` 根連續已收棒（不更動既有規則）。
   - **1D（UTC+8 日界）暖機**：首個 `bt`（`2025-11-01T00:00:00Z`）對應最後一根已收日棒為 `2025-10-30T16:00:00Z ~ 2025-10-31T16:00:00Z`（`close/available_after = 2025-10-31T16:00:00Z <= bt`），向前 60 根起點為 `2025-09-01T16:00:00Z ~ 2025-09-02T16:00:00Z`；載明須逐棒驗證存在性、連續性與 `close/available_after <= bt`，不憑快取起訖日推定。
3. **價格關卡分列 raw 距離與 tick 置價**：
   - `6a`（raw 距離判定，嚴格先於 tick 對齊）：`Open_bt > 0`、`raw_px = round(L_ref, 4)`、`dist = (op - raw_px) / op`、literal IEEE-754 float `0.0005 <= dist <= 0.10`（報表取整不改變入選結果）。
   - `6b`（tick 置價與取整後拒絕條件）：`Decimal ROUND_DOWN` 至 `tickSz`，明列實作之取整後拒絕條件 `px_d <= 0`（`placed_px_non_positive`）；取整後距離僅供稽核不觸發淘汰。
4. **公開可讀去識別預登記 JSON（固定 40 碼 commit SHA）**：
   - 檔案標記 `status: "PROPOSED_NOT_EXECUTED"`、`window_role: "historical_diagnostic_window"`（`is_independent_oos: false`，歷史診斷窗，不稱獨立樣本外）。
   - 既有 6 檔（commit `3cd4fb670eae32c7bc25c78d635d7a1dc8de4051`）與 61 分片（commit `94348bd549b35c1dd9d6f4e91f337c1764d17749`）僅引用不重交。

### 二、證據與獨立覆核雜湊（復盤實測 HTTP 200／位元組／SHA-256／去識別全數通過）
- **固定 commit**：[`e10f4f8d4534139f5394d3ff0c517eddb39c085a`](https://github.com/LeoCheng802/Grok-Bot/commit/e10f4f8d4534139f5394d3ff0c517eddb39c085a)
- **Raw URL（HTTP 200 實測通過）**：[`LONG_STRUCT_01_CANDIDATE_COUNT_2025_11_PREREG_v1.1.json`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/e10f4f8d4534139f5394d3ff0c517eddb39c085a/research/long_struct_01/LONG_STRUCT_01_CANDIDATE_COUNT_2025_11_PREREG_v1.1.json)
- **位元組大小**：`13,858` B
- **完整 SHA-256**：`605e28538323a815eb3bf045e1bdf28c66a90d00ddc499f17561c15b2e19016a`
- **去識別掃描**：不含私人程式、帳密憑證、實盤持倉／掛單、逐筆紀錄或任何本機路徑。

### 三、缺口與邊界
- 本輪仍屬**預登記準備階段**（`PROPOSED_NOT_EXECUTED`），未執行任何資料抓取、候選掃描、損益回測、調參、下單或部署。
- `2025-11` 為歷史診斷窗，不具獨立樣本外（OOS）效力。

### 四、下一步
- 待 ChatGPT 覆核固定 commit 上的 `v1.1` 預登記 JSON；若確認通過並明示核准，再依預登記方案執行 `2025-11 UTC` 同五檔候選漏斗與獨立邊際計數（不跑損益回測，遇缺口即停）。請回覆時保留 `[ChatGPT研究交接]` 前綴以利自動巡檢辨識。
