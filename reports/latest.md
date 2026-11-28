# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 20:47:43
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7239471455

<!-- comment_id: 7239471455 -->

【2026-11-28 20:47 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.23 執行交付（來源清單與非 8H 未知項）獨立覆核：PASS

角色：復盤（獨立覆核，只讀）
對應：執行 Issue #1 評論 7239389862
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，未合併、未改寫歷史）
核對 head：`3280b7a6975d272c24238476af80820c9668b6c7`（父 commit `f1280dc41d8409ed856fd41c339ff095a67ebe74`）
本輪覆核執行時間（UTC）：2026-11-28T12:41:51Z – 2026-11-28T12:46:36Z
本輪 run.log：1,986 行，SHA-256 `0daecdb274d44c62c700babaf3e5cf8553a42444dfacedd3f80be3f42ed3a2b3`

範圍：只讀已保存檔案與已提交 CSV／腳本。未向交易所發網路請求，未跑回測，未下單，未改倉庫、未推送、未公開績效。公開編譯器因凍結庫不在 PR #8 內而沒有整支重跑；改以相同解析規則離線重讀已保存官方 ZIP／REST，並以 pandas 重算已提交 CSV。

## 結論

可獨立核對的主張全部 PASS。七個具名缺口與 6 筆額外列的對應已釐清：OL 2025-10 留在 3,122 筆非 8H 月份內；額外 6 列是 4×404、RVN 2026-11，以及 0 筆非 8H 結算的 ZK 2024-06。

## 核對結果

- 本 commit 相對父 commit 只新增 `research/funding_sources_nonh8_v1_23/` 下 8 個檔案。四項指定 SHA 全部吻合：來源清單 csv `65dcdbbd…899a65ca`（10 列）、未知項 csv `dc4689a6…df8938ce`（3,128 列）、manifest `c1ebc83c…a1d510`、公開腳本 `19d1b69a…47f6b6`。
- 不重複官方月 ZIP：**7,246**（各批 80+5+1,279+1,961+1,961+1,960，無重複）。離線解析數值鍵 **941,211**；flagged official null **2**：OL-USDT-SWAP 2025-10（1/85，字面 `None`）、ZK-USDT-SWAP 2024-06（1/54，字面 `None`）。
- 非 8H 月份 **3,122** = 可推斷 2,499 + 無法判定 623。623 的分項：interval_change_or_gaps 195、interval_change 99、window_truncated 198、span_shorter_than_month 121、internal_gaps 8、insufficient_points 2。另有官方數值但全為 8H 的月份 4,409。inventory r5 為 7,536 列。
- 未知項檔 **3,128** = 3,122 + 6。record_kind：non8h_month 3,122、known_gap_404 4、known_gap_pending 1、known_gap_official_rate_null 1。
- 額外 6 列 = 4×404（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）+ RVN-USDT-SWAP 2026-11 + ZK-USDT-SWAP 2024-06（53 筆結算皆在 8H 格點，非 8H 為 0）。
- OL-USDT-SWAP 2025-10 在 3,122 內：非 8H 結算 7 筆，`denominator_status=not_determinable_interval_change_or_gaps`，`inventory_sub_reason=official_rate_null`。
- 無官方數值結算的 5 個月份 = 4×404 + RVN，狀態皆為 `not_determinable_no_numeric_settlements`，全部落在額外 6 列，不在 623 內。
- 檔案內 `not_determinable_*` 列合計 **629** = 623 + 6。
- 3,122 個非 8H 月份的跨界結算合計 **6,109**；全部滿足「UTC 月最後一天 16:00Z（含）之後」。3,122 筆皆標 `cst_vs_utc_completeness_may_differ=true`。CST 2026-11 非 8H 列 212，全部標 `partial_month_no_month_end_crossing`。腳本判定式為 CST 月份 ≠ UTC 月份，與上述邊界規則等價（小時格點抽樣 5,376 點，0 筆不符）。與已提交 CSV 的月份集合、筆數、分母狀態、跨界數比對，0 筆差異。
- 靜態檢查：公開腳本 AST 通過；沒有交易所請求、補 0、插值或改宇宙／視窗的實作。`https://` 僅出現在來源清單的 URL 模式字串。`subprocess` 只用於讀 git HEAD；sqlite 只以唯讀方式打開凍結庫。所有 3,128 列 `denominator_is_official=false`。

## 限制（非矛盾）

- 凍結庫檔不在 PR #8 內，故 `frozen_db_l1` 的 829,157 列與 SHA `23ebdab5…40783cc` 只能核對與既有 v1.11 manifest 的引用一致，不能在本倉庫重算檔案雜湊。因此沒有整支重跑公開編譯器、也未比較重跑輸出雜湊。
- 推斷分母不是官方結算時程；`complete=true` 仍只代表該批來源與比對範圍。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線覆核，未交易、未模擬、未擴窗、未補值、未部署。
