# 執行

此檔是「執行」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:25:45
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230133680

<!-- comment_id: 7230133680 -->

[執行] BACKTEST-READINESS-01 v1.11／v1.12 全窗資金費來源月份盤點清單

- 角色：執行｜研究：BACKTEST-READINESS-01｜版本：v1.11-inventory
- 執行起迄（UTC）：2026-11-27T23:18:01Z ～ 2026-11-27T23:23:02Z（300.86 s）
- 固定 commit：PR #8 head `eaf46daabfd8fdb80f19ced56640363ebfd64e50`，目錄 `research/funding_inventory_v1_11/`（`313829d6…` 加入清單，`eaf46daa…` 只把 manifest 內的本機路徑改成檔名）
- 範圍：固定 `EX_USDC_286` 286 個 USDT-SWAP，窗 `2023-01-01T00:00Z`～`2026-11-26T12:00Z`；月份按 UTC+8 切，取自各 NPZ `ts30` 實際有行情的月份
- 既有列：凍結庫 829,157 列＋v1.7／v1.9／v1.10／v1.11-b1 增量（以 `ts_snapped` 去重）
- 官方存在性：`market-data-history`（module=3、monthly）列出 7,323 個月；290 個未列出的月份再對 CDN 做 HEAD。85 份已驗 ZIP 不重抓，本輪沒有下載任何新 ZIP。

**分項（共 7,536 個標的×月份）**

| 類別 | 數量 | 說明 |
|---|---|---|
| 已存可用（covered_verified） | 85 | 已用官方 ZIP 逐列比過（v1.10 80 份＋v1.11-b1 5 份） |
| 待核（pending_check） | 5,882 | 官方有月檔；既有列數達到 8H 網格下限，但還沒逐列比過。仍可能缺 1H／4H 結算 |
| 確缺（confirmed_missing） | 1,279 | 官方有月檔；既有 0 列 1,157，低於 8H 下限 122；涉及 272 個標的 |
| 官方不可得（official_unavailable） | 290 | 邊界不足 286；404 共 4 |

- 邊界不足 286：每個標的的 CST 2026-11 都有行情，但這個月的官方月檔要到 2026-12-01 00:00 CST 月結後才會發布（API 未列出、CDN 404）。
- 404 共 4：CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09。都是在 CST 月底最後幾小時才上市，行情區間內沒有 8H 結算，第一筆結算落在下個月。
- 確缺最多的標的（月數）：PEPE 13、SHIB 13、SATS 12、FLOKI 11、GAS 11；ARB、ETC、ETHW、FLOW、GMT、SAND、SUI 各 10。

**交付檔（SHA-256）**
- `funding_month_inventory_v1_11.csv`：771,000 B，`038d59cd74b28859c482aeda1bf7f378ac44728054fdfd134d8647dab2b08e21`。欄位：inst_id, month_cst, npz_bar_first_utc, npz_bar_last_utc, existing_rows, existing_sources, official_listed, http, class, sub_reason
- `funding_month_inventory_v1_11_manifest.json`（PR 版，已去本機路徑）：6,709 B，`d84d67cb2e0d2dfe3a9deb1a7bb4c4059e58c9b0b299d1aebf0526bc1fba0d8a`

**缺口**
- 這份是 NPZ 全量清單，不是 ChatGPT 的 2,757 條路徑優先清單（我沒拿到那份清單）。提供後可以直接拿 CSV 篩出來。
- 5,882 個待核月份只做到列數檢查，還不能說可用。
- 2026-11 要等官方月結；本輪不處理。

**下一步（估時）**：確缺加待核共 7,161 份月檔，約 9.6 MB，以約 5 req/s 計約 31～44 分鐘。打算先抓確缺 1,279 份交第 2 批增量，再分批抓待核。每批照 v1.10 格式附原 ZIP、SHA、既有匹配／新增／衝突。

紅線維持：不補零、不插值、不刪幣換母體、不盲目 INSERT OR IGNORE；不擴標的或期間、不抓行情、不跑策略；PR #7／#8 為 draft、不合併；`FIB-4H-LONG-V3` NO-GO，`live_approved: false`。
