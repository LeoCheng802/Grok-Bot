# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-27 11:32:55
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7209076758

<!-- comment_id: 7209076758 -->

[復盤] RESEARCH-LOOP-01 v1.3｜全庫資金費 61 分片＋持倉名冊已上傳（commit `94348bd5`）、零重跑補正與新多單結構提案

- **角色**：復盤（總召／獨立覆核）
- **研究編號／版本**：`RESEARCH-LOOP-01 v1.3`（承接 `#7208941231`）｜公開全庫分片 `funding_archive_v1`｜`LONG-LOOP-01 v1.1-corrected`｜新多單結構構想 `LONG-STRUCT-01`（僅提案，未執行）
- **時間與時區**：2026-11-27 11:34（Asia/Taipei, UTC+8）
- **資料截止**：資金費歸檔 `2021-08`～`2026-11`（`EX_USDC_286`、`2023-01-01`～`2026-11-26 12:00 UTC` 為本輪研究區間；全程 **0 新增策略 replay**、未重抓資金費、未補零、未公開完整策略／風控碼或憑證）
- **各交付狀態總覽**：
  - `funding_pilot_v1`（commit `8bf4c15ed50d5dc3f1f66a01dd3df83f5521b668`）：`ChatGPT 已取得驗證`
  - `funding_mixed_shard_v1`（commit `9b3d93768c1581b985bf01283af353d59c9f93cc`）：`ChatGPT 已取得驗證`
  - `funding_archive_v1`（commit `94348bd549b35c1dd9d6f4e91f337c1764d17749`）：`已上傳，待 ChatGPT 取得驗證`
  - 私人離線包 `RESEARCH-LOOP-01-PACK v1.1`（20 檔，`136,828` bytes，SHA-256 `87dc925b8025c3bcaba87debb4d1bf8a86b794a8e47921f6ac2208b04e17da0d`）：`待收（僅走私人交付，不公開）`
  - `LONG-LOOP-01`：`四組負結果封存 NO-GO，停止原結構參數掃描；已完成零重跑補正與 BTC 1D 時間可用性稽核`

---

### 1. 既有資金費全庫 61 分片＋實際持倉資金費名冊（經復盤獨立驗證 HTTP 200、大小、雜湊與零路徑／憑證洩漏）
- **固定 Commit**：[`94348bd549b35c1dd9d6f4e91f337c1764d17749`](https://github.com/LeoCheng802/Grok-Bot/commit/94348bd549b35c1dd9d6f4e91f337c1764d17749)（目錄 `research/RESEARCH-LOOP-01/funding_archive_v1/`，共新增 64 檔：61 個月度 `.csv.gz` 分片 `2021-08`～`2026-11` 共 `829,157` 筆、`9.33 MB` ＋ 3 份 JSON；前兩批已驗證試點未更動、未重複上傳）
- **[manifest.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/94348bd549b35c1dd9d6f4e91f337c1764d17749/research/RESEARCH-LOOP-01/funding_archive_v1/manifest.json)**（`56,529` bytes，SHA-256 `a1f2c2f878885159a4bd756ddc4b9333b2ab1d696a49dfa2f3964bf02b2a1a02`；含全部 61 分片 `sha256_gz`／`sha256_csv_uncompressed`／大小／重複鍵／`source_ym` 與間隔分佈）
- **[held_position_funding_roster.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/94348bd549b35c1dd9d6f4e91f337c1764d17749/research/RESEARCH-LOOP-01/funding_archive_v1/held_position_funding_roster.json)**（`5,013` bytes，SHA-256 `0a8df637e2921a2a8e99fb4749ef71c202f8d53da29686036b186fd01e7ae51e`；僅從既有已存輸出彙整 L1 `off` 與 `LONG-LOOP-01` 各臂之 `observed_8h`、`observed_non_8h`、`miss_8h` 與已記錄缺口標的；未序列化欄位標 `null`／`unknown`）
- **抽樣驗證混合頻率分片**：[funding_2026-01.csv.gz](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/94348bd549b35c1dd9d6f4e91f337c1764d17749/research/RESEARCH-LOOP-01/funding_archive_v1/shards/funding_2026-01.csv.gz)（`350,638` bytes，SHA-256 `d5bc36bcc1f3fa40920cb5526fa96be970379cee563626e250ded7acdda91930`，`33,747` 筆含 `15,526` 筆非 8H，實際間隔 `1h: 4,451 / 4h: 23,115 / 8h: 5,957`）。所有分片均保留 `funding_time_ms` 與 `ts_snapped_ms`，並區分「8H 網格空格 `miss_8h`」、「已觀測結算事件（8H／非 8H）」與「非 8H 實際應收分母 `unknown`」。

---

### 2. `LONG-LOOP-01` 零重跑補正與 BTC `1D` 時間可用性稽核
- **更正版輸出（未重跑、保留原檔）**：
  - 原檔 `long_loop_01_result.json`（`17,678` bytes，SHA-256 `c8e551cc4e9b8f28aa6511762e71762d4ecf4434b2032cd86c216e7f1bc655d8`，未動）
  - 更正版 `long_loop_01_result_v1_1_corrected.json`（`21,315` bytes，SHA-256 `2f892a1fd18a0823db25c00c076cc005bebff28ec01f16274d2b8ddadf85ad52`）：復盤已確認無法自原檔恢復的 `exposure`、`monthly_summary`、`by_month` 皆已改為 `null` 並標註 `unknown_not_serialized_in_v1_0`（不再填 `0`）；另獨立列出由 `f_ev_real_8h + f_ev_miss_8h` 派生之 8H 持倉人槽；同步更正解讀（`10pct` 候選拒絕率 `87.34%` vs 實際成交縮減率 `86.90%`／`86.18%`，且 `exposure` 未序列化前不斷言虧損縮小「僅」由少開單造成）。
- **BTC `1D` 時間可用性稽核**：
  - **[btc_1d_availability_audit.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/94348bd549b35c1dd9d6f4e91f337c1764d17749/research/RESEARCH-LOOP-01/funding_archive_v1/btc_1d_availability_audit.json)**（`9,124` bytes，SHA-256 `4c94af71c1f0f9b88f37bf7e8f2a6ae249f9adf472c880fd7cf76378c8623e0a`，實測 HTTP 200 且雜湊一致）。
  - OKX `1D` 定義為 `candle_open = 16:00:00 UTC`、`candle_close / available_after = open + 24h`（次日 `16:00:00 UTC`）。全窗 `8,554` 根 4H 檢查 `available_after > signal_time` 違規數為 **`0`**（最小餘量 `0 ms` 落於 `16:00:00 UTC` 交界；含邊界前後 `candle_open`、`candle_close / available_after`、`signal_time` 與實際選中資料對照）。

---

### 3. 已測多單去重清單與新多單結構構想（僅提案，不啟動掃描）
- **已封存 NO-GO 去重清單（不再重掃）**：
  1. `LONG-SHORT-SCOPE-01-L1`：`FIB_4H_Long_v3`（`ENTRY 0.618`、`EMA60`、`RSI [55,85]`、`SL 4%`）× `TP {2.5%, 4.0%, 6.0%}` × `{cross_1tick, delay1bar}`（6 replays，全負）。
  2. `LONG-LOOP-01`：`FIB_4H_Long_v3`（`TP 2.5%`、`SL 4%`）× `BTC_FILTER {off, 200ma, 10pct}` × `{cross_1tick, delay1bar}`（4 新增 replays，全負）。
- **新多單限價進場結構構想 `LONG-STRUCT-01`（僅供審查，未執行任何掃描）**：原結構在 `RSI 55~85` 順勢高檔掛 `0.618` 限價單易承受「轉弱才成交」的逆選擇，且固定 `TP 2.5% / SL 4%` 賠率倒掛（0.625R）；建議待私人離線包由 ChatGPT 獨立重播通過後，改評「深跌流動性掃尾限價承接 + ATR 正規化盈虧比（`TP >= 1.5 * SL`）+ 時間停損」之新結構。

---

### 4. 安全邊界與下一步
- 空單已凍結規格與 14 天公開前向觀測維持不動；所有工作僅限離線研究，無 `--demo`／`--live`、下撤平單、部署或實盤風控變更授權。
- **下一步**：待 ChatGPT 驗證 `funding_archive_v1`（commit `94348bd549b35c1dd9d6f4e91f337c1764d17749`）與 `btc_1d_availability_audit.json`，並待私人離線包 `RESEARCH-LOOP-01-PACK v1.1` 交到 ChatGPT 端完成獨立重播後，再決定 `LONG-STRUCT-01` 是否預登記。
