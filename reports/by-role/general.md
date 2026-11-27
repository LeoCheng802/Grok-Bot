# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:58:21
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230545281

<!-- comment_id: 7230545281 -->

【2026-11-28 07:59 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.11-b2 r1：D1 修正複驗

- 角色：復盤（獨立覆核）。對象：PR #8 head `08ff3d5bdb02c8b28ed0170d234bf1f02e8cc0ca`（執行回報 #7230527499）
- 執行 UTC：`2026-11-27T23:57Z`～`23:58Z`

**結果**
- 新 delta `funding_delta_v1_11_b2_r1.csv.gz` 的 SHA 是 `ac3890c5…2e86`，與回報一致。共 198,354 列，沒有重複鍵，每列費率都是有限數值（不是 `None`、`NaN` 或 `Inf`）。8H 有 120,996 列，非 8H 有 77,358 列。
- 和 `74764f32` 的 delta 相比，只移除了 OL `2025-10-24T08:00Z` 和 ZK `2024-06-06T08:00Z` 這 2 個鍵。沒有新增任何鍵，其餘費率也沒有改動。
- 旗標檔裡只有這 2 列，旗標是 `official_rate_null`，原值保留為 `None`。它記錄的 2 個來源月檔 SHA，我在 repo 原檔上重算後吻合。
- 盤點表從 r1 到 r2 只改了這 2 列：子原因改成 `official_rate_null`，但分類仍是 `covered_verified`。執行已說明會在下一個 commit 改成未完整，屆時我再複驗。
- 補充：這 2 筆空值都落在 NPZ 第一根行情棒之前（OL 的第一根是 `2025-10-29`，ZK 的是 `2024-06-18`），看起來不在回測期間內。不過這只是旁證，2 個月份還是照規定標成未完整。

**D1 結論**：delta 部分 PASS。分類標記、`NaN`／`Inf`／空值的拒絕邏輯，以及 REST 原始 bytes 的說明，等下一個 head 再一起驗。
`FIB-4H-LONG-V3` 維持 NO-GO；全案 `live_approved: false`；PR 維持 draft。
