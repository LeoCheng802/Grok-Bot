# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 07:48:35
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230424846

<!-- comment_id: 7230424846 -->

[執行] BACKTEST-READINESS-01 v1.11 第 2 批：1,279 份官方月檔＋2026-11 官方 REST 歷史

- 角色：執行｜研究：BACKTEST-READINESS-01｜版本：v1.11-b2
- 執行起迄（UTC）：2026-11-27T23:30:19Z 開始；Part A 至 23:41:56Z（第一輪在 900/1,279 中斷，從已存檔續跑）；Part B 至 23:43:00Z；輸出寫入 23:46:11Z～23:46:18Z
- 固定 commit：PR #8 head `74764f32f6bcdfab8bcc25211eaeed9755fdeffe`，目錄 `research/funding_delta_v1_11_b2/`
- 窗尾維持 `2026-11-26T12:00:00Z`。沒有補零、插值、繞過 403，也沒有傳送憑證。凍結庫未變（SHA `23ebdab5…0783cc`），85 份已驗 ZIP 不重抓，盤點不重做。
- 口徑：結論一律來自官方列和既有資料（凍結庫＋v1.7／v1.9／v1.10／v1.11-b1）的逐鍵比對，鍵為 `(inst_id, snap 到整點)`。「確缺」只是優先候選。此批除 2026-11 外，待核月份都還沒逐鍵比對，不算完整。

**Part A：候選月份的官方月檔**
- 1,279/1,279 HTTP 200；0 失敗、0 空檔。官方 174,957 列，鍵皆唯一。
- 已匹配 5,601；新增 **169,356**（8H 104,157、非 8H 65,199）；衝突 0；官方內重複 0。

**Part B：CST 2026-11 官方 REST `funding-rate-history`**
- 請求 286 個，完整覆蓋 `[2026-10-31T16:00Z, 2026-11-26T12:00Z]` 的有 285 個。範圍內官方 39,037 列，已匹配 10,037，新增 **29,000**（8H 16,841、非 8H 12,159），衝突 0。新列費率全部取 `realizedRate`，原始回應資料均保留。
- 285 個標的的分頁軌跡都有記錄（URL、請求 UTC、HTTP 狀態、列數、最小／最大 fundingTime、回應 SHA），也記了實際覆蓋範圍。
- 未完整：`RVN-USDT-SWAP`。REST 回 HTTP 200、code 51001（Instrument ID doesn't exist），範圍內 0 列，列為待核（`rest_error`）。

**合計**：官方唯一鍵 213,994；已匹配 15,638；新增 **198,356**（8H 120,998、非 8H 77,358）；衝突 0。

**4 個 404**：仍是 CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09，都維持 `404_reason_unknown`。官方 instruments 的 `listTime`／`state` 只當證據附上，沒有拿來改分類。

**盤點 r1（7,536 格）**：`covered_verified` 1,364；`covered_verified_rest` 285；`pending_check` 5,883（原 5,882＋RVN 2026-11）；`official_unavailable` 4。

**交付檔（SHA-256）**
- `funding_delta_v1_11_b2.csv.gz`：3,035,615 B，198,356 列，`2ef8517fc3d70ff098a0ea65c5ad07ffbc0142befa375cf8996ebb8db962d54b`
- `funding_source_months_v1_11_b2.json`：1,295,577 B，`1d9d93f8637f87ac9b75d0bba06a5550c88edf4886824bfd06d5ca21316193ae`
- `funding_conflicts_v1_11_b2.json`：75 B，`154af0034d85c4ceaec4e39560211fe2a91b37af47a46ce15eb5dc3c492bc8c8`
- `funding_month_inventory_v1_11_r1.csv`：751,576 B，`3a9ef2b8b8adeb163a4ae6fb197006cc99ffca491141b109a51586e6874b2f3e`
- `funding_delta_v1_11_b2_manifest.json`：10,586 B，`4d907caeac03ec4c7a822941586d14226c6691ad076c96d8e6e98c8fea9a9468`。內含實際輸入的 SHA：凍結庫、先前 4 份增量、原盤點 CSV。
- `fetch_evidence_v1_11_b2.jsonl`：2,413,395 B，`b54fa9f82cb399b5bb52aa9d7ce8a79a194ed95f54a3372b68e324f96d1baf66`。記錄每個請求的 URL、UTC、狀態、回應 SHA；續跑時只追加不覆寫。
- `instruments_swap_v1_11_b2.json.gz`：26,245 B，`87020ee68af8e3dd39c7e6482359ff6eb2dcd83276c34c74327d3f8edb97f6f1`
- 生成程式（可公開版）：`build_delta_v1_11_b2_public.py`，`2ef8e02c…d97c`；`build_inventory_v1_11_public.py`，`47dcd0d0…9d30`
- 原始資料：`official_monthly_zips/` 1,279 份、`rest_2026_11/` 286 份。

**缺口**：5,882 個待核月份還沒逐鍵比對，可能仍缺 1H／4H 結算；RVN 2026-11 的 REST 查不到此標的；4 個 404 原因未知。因此不能說資金費資料已完整。
**下一步**：待核 5,882 份月檔分批抓取並逐鍵比對，估計約 30～40 分鐘，分 2～3 批交。

紅線維持：不補零、不插值、不刪幣換母體、不盲目 INSERT OR IGNORE；PR #7／#8 為 draft、不合併；`FIB-4H-LONG-V3` NO-GO，`live_approved: false`。
