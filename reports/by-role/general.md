# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:08:45
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229907329

<!-- comment_id: 7229907329 -->

【2026-11-28 07:08 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.9 報表更正｜PR #7 head `59dea52b31e1360e0349f2139e6b9bb002efd3ce` 獨立靜態驗收：PASS

角色：復盤（獨立驗證，非歷史回測）｜實測 UTC `2026-11-27T23:07:53Z` → `23:08:22Z`｜對應 [#7229888026](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229888026)。PR #7 仍 open/draft 未合併。

1. head `59dea52b…` parent 為 `4307a6f3…`；diff 僅 3 檔（+296/−57）：`run_l1_bounded_backtest.py`、`run_retest24_bounded_backtest.py`、`run_long_struct_bounded_backtest.py`。engine、策略檔、測試檔均未變。
2. 大小／SHA 與報告一致：L1 46,871 B `27520cf4…98fb`、RETEST24 54,101 B `67094079…f89`、LONG 57,609 B `8db9e3fd…a59`；測試 `eed3bda2…efd2`、`c4788a7a…a8e` 未變。
3. 變更範圍：L1 移除的行只在 `summarize_run` 與 `main` 的報表輸出（舊 `by_month` 讀 `exit_ts`/`net_pnl_u` 等不存在的欄位）；新增行不含網路／子行程／交易所 API 呼叫，只新增 `import calendar`；成本／杠桿／TP/SL／撮合參數未動。
4. 自行重跑兩套 synthetic：`ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS`、`ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS`。
5. 隔離回歸（舊版 vs 新版 `_enumerate_scored_utc_months`）：
   - 2025-10-01T00:00 → 10-31T23:30：舊 `partial=True`（錯）→ 新 `False` ✅
   - 2025-10-01T00:00 → 10-31T23:00：舊新皆 `True` ✅（少一根仍是部分月）
   - 2025-12-01 → 2026-01-31T23:30 跨年：舊 2026-01 `True` → 新 `False` ✅
   RETEST24 與 LONG 兩支結果相同。
6. 未驗：L1 新月報與 `l1_bounded_local_details.json` 未以真實資料執行（依規不跑團隊歷史），僅做靜態審閱。

FIB-4H-LONG-V3 維持 NO-GO，live_approved: false；無交易、部署或風控變更。
