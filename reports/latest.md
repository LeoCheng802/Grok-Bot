# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 06:46:51
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229611844

<!-- comment_id: 7229611844 -->

[執行] BACKTEST-READINESS-01 v1.10｜80 份官方逐幣月檔全量入庫比對：新增 10,633 列未入庫官方結算（含 1H／4H），新 7 鍵 7/7 取得，衝突 0；推上 PR #8 新 head `b0dcf61e…`

- **角色**：執行
- **研究／事件編號**：`BACKTEST-READINESS-01 v1.10`（對應 Issue #1 `#7229543627`）
- **回報時間**：`2026-11-28 06:47 台北時間（UTC+8）`
- **執行起迄（UTC）**：
  - 月檔取得、保存與全量比對：`2026-11-27T22:45:55Z` → `2026-11-27T22:46:06Z`
  - PR #8 推送與 live raw 驗證：`2026-11-27T22:46:22Z` → `2026-11-27T22:46:25Z`

### 0. 誠實更正
- v1.9 當時 75 份月檔只在記憶體解析、**未落地保存**，因此本輪無法「重用已存月檔」，已依原 75 組 `(inst_id, 月份)` 重新取得同一官方路徑並**這次全數保存原始 ZIP**；另加新 7 鍵所需 5 份月檔，共 `80` 份，`80/80` HTTP 200。
- 重新取得的 `0G-USDT-SWAP-fundingrates-2025-11.zip` SHA-256 `78748b1ab7fc6487cbb28522f897312411471cf82a8a0bc478c994cc41fc9407`，與 ChatGPT 獨立解析的同檔 SHA 完全一致。

### 1. A｜80 份月檔全量入庫比對（不只 174 個 8H 目標）
- 官方列合計 `11,031`（月檔內重複鍵 `0`）；與原凍結 `829,157` 庫＋v1.7＋v1.9 逐鍵比對：已入庫且 `ts_raw`／費率一致 `398`，**衝突 `0`**，**尚未入庫 `10,633` 列**（`69` 標的）。
- 未入庫列的結算網格：落在 8H 整點 `7,036`、非 8H 整點 `3,597`；以同標的官方相鄰結算間隔看，前一筆間隔 `4h` 計 `5,903`、`8h` 計 `3,972`、`1h` 計 `681`，其餘為月初首列或上市／停牌長間隔。
- `0G-USDT-SWAP` 2025-11-24：`15:00`（`-0.0010031826789156`）與 `17:00`（`-0.0006074667787935`）確實未入庫並已列入本增量，`16:00` 原已入庫且一致，另 `14:00` 亦未入庫。

### 2. B｜新路徑 7 鍵：`7/7` 已自官方月檔取得
- `AEVO 2026-05-01T00:00Z`、`USELESS 2026-04-05T00:00Z`、`YB 2026-04-05T08:00Z`／`16:00Z`、`O 2026-08-18T00:00Z`：當期為 **4H 結算**（前後間隔均 `4h`）。
- `THETA 2026-04-06T00:00Z`、`IOTA 2026-07-12T08:00Z`：當期為 8H 結算。
- 7 鍵均在上述 `10,633` 列內，逐列費率與 `ts_raw` 見增量檔。

### 3. C｜分類口徑（不宣稱資金費已完整）
- 指定 174 鍵：已恢復（v1.9）。
- 新路徑 7 鍵：本批已取得官方值，待 ChatGPT 疊加重測。
- 非 8H 漏列：至少 `3,597` 列已證實（遠多於原 2 筆），**全數僅限這 80 個月份**。
- **其他持倉時段跨頻率完整性：仍待驗**。本批只覆蓋 80 個 `(inst_id, 月份)`；原凍結庫其他月份是否同樣漏收 1H／4H 結算尚未全量檢查，屬下一批範圍。

### 4. 已交可讀連結（PR #8 Open Draft 新 head `b0dcf61e26db0e99b178ad0fe59d3944edbe6492`，Parent `8458510c0eb4bc365c121b9c835c2895103aea40`，未合併、`main`／其他 PR／Releases 未動；live raw HTTP 200、大小與 SHA-256 吻合、零私有路徑與憑證）
- PR：https://github.com/LeoCheng802/Grok-Bot/pull/8
1. `research/funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz`（`158,227` B，`10,633` 列，`4fe33c0efe78f1398b02cb231760d3817b13f985de013e51df9c273dec7c999b`；逐列 `raw`／`snap`、費率、前後間隔、來源月份、取得時間）：https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/b0dcf61e26db0e99b178ad0fe59d3944edbe6492/research/funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz
2. `research/funding_delta_v1_10/funding_source_months_v1_10.json`（`38,910` B，`04a86793fa08624bf0e60c20cc01f54a716e45019dd265f1b870351ad118ff2e`；80 月檔各自 URL、ZIP SHA、列數、時戳範圍）：https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/b0dcf61e26db0e99b178ad0fe59d3944edbe6492/research/funding_delta_v1_10/funding_source_months_v1_10.json
3. `research/funding_delta_v1_10/funding_conflicts_v1_10.json`（`50` B，`b9900cb4aae6670829d75b3bb989bbc4227172b656dc28e6da0b6a606f95775d`；衝突表，0 筆）：https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/b0dcf61e26db0e99b178ad0fe59d3944edbe6492/research/funding_delta_v1_10/funding_conflicts_v1_10.json
4. `research/funding_delta_v1_10/funding_delta_full75plus_v1_10_manifest.json`（`3,783` B，`ab64f5b4a4c579f05d9bee0f068c7de17a791b3c4f370f17958d0363fdfca14d`）：https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/b0dcf61e26db0e99b178ad0fe59d3944edbe6492/research/funding_delta_v1_10/funding_delta_full75plus_v1_10_manifest.json
5. 80 份原始官方月檔 ZIP：`research/funding_delta_v1_10/official_monthly_zips/`（共約 328 KB）

### 5. 剩餘缺口與下一步
- 原凍結庫其他月份的 1H／4H 漏收尚未全量檢查；若要收口，下一批需對全部標的、全期月份取官方月檔逐鍵比對，預估約數千份小檔，數十分鐘可完成，待指示再做。
- 請 `@復盤` 獨立驗收。`FIB-4H-LONG-V3` 維持 `NO-GO`，全案維持 `live_approved: false`；零歷史回測、零合併、零部署、零下單。
