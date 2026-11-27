# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 06:59:38
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229783504

<!-- comment_id: 7229783504 -->

[執行] BACKTEST-READINESS-01 v1.11 第 1 批：5 標的官方月檔資金費增量

- 角色：執行｜研究：BACKTEST-READINESS-01｜版本：v1.11-batch1
- 回報時間：2026-11-28 07:03 台北時間（UTC+8）
- 執行起迄（UTC）：2026-11-27T22:58:55Z ～ 2026-11-27T22:58:56Z（抓檔＋比對）
- 固定 commit：PR #8 head `6499a579aacdf922c67f432915245adef0c11dc7`（parent `b0dcf61e…`），目錄 `research/funding_delta_v1_11_b1/`
- 來源：OKX 官方 CDN `swaprates/monthly` 逐幣月檔（月份以 UTC+8 切），5/5 HTTP 200

**先查既有**：12 鍵在凍結庫 829,157 列、v1.7、v1.9、v1.10 增量中都不存在，鍵映射無誤，確缺。

| 標的 | 月份(CST) | 官方列 | ZIP SHA | 範圍 UTC | 新增 |
|---|---|---|---|---|---|
| ARKM | 2026-01 | 93 | `f4d86d0c…4e0e` | 12-31T16 ～ 01-31T08 | 93 |
| AT | 2026-10 | 186 | `75b3681a…0712` | 09-30T16 ～ 10-31T12 | 60 |
| BERA | 2026-05 | 186 | `347c7e96…c5bc` | 04-30T16 ～ 05-31T12 | 186 |
| GALA | 2026-04 | 90 | `45926149…f30b` | 03-31T16 ～ 04-30T08 | 90 |
| POPCAT | 2026-04 | 180 | `f64393be…1c4b` | 03-31T16 ～ 04-30T12 | 180 |

**結果**：官方 735 列，已匹配既有 126 列，衝突 0，未入庫 **609** 列（8H 整點 396、非 8H 213）。新 12 鍵 12/12 在增量內：ARKM 5 鍵與 GALA 2 鍵為 8H 結算；AT 3 鍵、BERA、POPCAT 為 4H 結算。ARKM 2026-01、BERA 2026-05、GALA／POPCAT 2026-04 在凍結庫是整月零列。

**交付檔（SHA-256）**
- `funding_delta_5sym_v1_11_b1.csv.gz`：8,286 B，609 列，`2ab89d43188e38c0b34ea04513d9c199eee2fa7fc5bfac891993db2006d48bbb`
- `funding_source_months_v1_11_b1.json`：2,453 B，`7c62f35d465a5e0a0125870f9c6d3e9123a7fb0ae33a12018f8a54f4f9b19b6f`
- `funding_conflicts_v1_11_b1.json`：50 B，`b9900cb4…775d`（0 衝突）
- `funding_delta_5sym_v1_11_b1_manifest.json`：4,681 B，`39747fe4ba7f11c6f0b4a06490902bb0749f00de2e60c11094cb9cf6863af3a7`
- `official_monthly_zips/`：5 份原 ZIP

**文件小修**：PR #8 說明已改寫，對齊實際內容（含 v1.10 與 v1.11-b1 的 ZIP payload）。

**缺口**：只能說這 5 個月份已收齊，不能說資金費資料已完整。全窗盤點清單尚未交。
**下一步**：做 `EX_USDC_286` 全窗的標的×月份盤點清單（已存可用／待核／確缺／官方不可得），先交清單再分批交增量。

紅線維持：不補零、不插值、不刪幣換母體、不盲目 INSERT OR IGNORE；PR #7／#8 不合併；`FIB-4H-LONG-V3` NO-GO，`live_approved: false`。
