# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:07:19
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229888026

<!-- comment_id: 7229888026 -->

【2026-11-28 07:07 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.9／v1.12｜PR #7 報表更正已推上新固定 head

- 角色：策略組
- 研究編號：BACKTEST-READINESS-01（v1.9 兩項非阻擋報表更正，v1.10～v1.12 交辦「PR #7 報表修正」）
- 版本：PR #7 head `59dea52b31e1360e0349f2139e6b9bb002efd3ce`（parent `4307a6f3963f58707c1c6afca397db0cfe8bc0b3`），Open Draft，未合併
- 推送與線上驗證 UTC：推送完成於 `2026-11-27T23:06Z` 前；raw 逐檔驗證 `2026-11-27T23:07:01Z`
- 資料截止：不涉及新資料；未跑任何歷史回測

**完成事項**
1. `run_l1_bounded_backtest.py`：月報改用真實欄位（`_ord_log` 的 `pts`/`ets`，`_trades` 的 `ets`/`xts`）輸出 `by_year_month`（`by_month` 為別名）；候選訊號依回測窗過濾，輸出 `candidate_bars_in_window`／`candidate_signals_in_window`，另列 `*_including_warmup`；新增 `l1_bounded_local_details.json`（PASS 與 ABORT 都寫並附 SHA）；`missing_by_scenario` 增加不截斷的 `missing_funding_events_all`。
2. 兩支 adapter（RETEST24／LONG_STRUCT）：部分月判定改用 30m bar-open 口徑，月末最後一根 23:30 UTC 開盤即算完整月；新增 `is_partial_month_convention` 欄位。

**證據（線上 raw 檔 @59dea52b，大小／SHA-256）**
- `run_l1_bounded_backtest.py`：46,871 B，`27520cf4a352936019cd1e1b408e61d316e02cb51d8614e223a01702d78d98fb`
- `run_retest24_bounded_backtest.py`：54,101 B，`67094079a995fa6f751d5393127b12895264641ccadc99a105d75511c3742f89`
- `run_long_struct_bounded_backtest.py`：57,609 B，`8db9e3fd0f64f86493f39584b5a5849b6f7f1067026a5e75413a86b6e9010a59`
- 兩支 synthetic 測試未變（`eed3bda2…efd2`、`c4788a7a…a8e`）
- py_compile 三檔 PASS；`ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS`、`ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS`
- 舊版重現失敗、新版通過：舊 adapter 把 2025-10 00:00→31T23:30 判為部分月，新版判為完整（23:00 結尾仍為部分月）；舊 L1 `by_month` 為 `{}`，新版產出 2025-10 fills=1、closed=1、is_partial=False（`ALL_V1_9_OLD_FAIL_NEW_PASS_VERIFIED_OK`）
- CLI 命令同 #7228727329，未改參數

**缺口**：本次只修報表序列化與口徑，不改策略邏輯或撮合；ChatGPT 尚未審核此 head。

**下一步**：請 ChatGPT 靜態審核 `59dea52b…`，毋須重跑團隊歷史。PR 維持 draft；`FIB-4H-LONG-V3` 維持 `NO-GO`，全案 `live_approved: false`。
