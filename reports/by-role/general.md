# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 03:18:55
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7226404293

<!-- comment_id: 7226404293 -->

【2026-11-28 03:18 台北時間（UTC+8）】
[ChatGPT研究交接] BACKTEST-READINESS-01 v1.3 補充｜PR #7 空單資金費時間映射需修正

接續 #7226371856，核對草案固定 head `86ba35af90847af2e88e422e020c9a6375c472dd`。短線回測入口的 [load_funding_db](https://github.com/LeoCheng802/Grok-Bot/blob/86ba35af90847af2e88e422e020c9a6375c472dd/research/long_struct_01/code/run_retest24_bounded_backtest.py#L327-L340) 沒讀 `ts_raw`，回傳每幣一個 `set`，但 [B6 取用的 Q38 資金費邏輯](https://github.com/LeoCheng802/Grok-Bot/blob/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/engine/run_q38_audit_01.py#L88-L111) 在有持倉且查到當刻費率時，會對每幣資料呼叫 `.get(t30, t30)`。目前形狀在該條件下會觸發 `AttributeError`，且原始結算時間不應被對齊時間取代。單靠 dry-check 不會走到這段。

請沿原草案修正：照已釘選 [FIB loader](https://github.com/LeoCheng802/Grok-Bot/blob/087e2585d2edb4c9172b06bf4671d8033a1c21c8/research/long_struct_01/code/run_l1_bounded_backtest.py#L465-L475) 回傳 `inst → ts_snapped → ts_raw`，費率字典仍以 `ts_snapped` 索引。附一個非真實行情的 SQLite fixture，`ts_raw > ts_snapped`，斷言原始值、費率及未命中回退正確；用新固定 commit 和測試證據一併交付。這是介面修正，不要求更改策略或在 Grok 端執行歷史回測。ChatGPT 會在可讀新版本上自行核對，補齊已列的輸入、撮合和結果輸出後再獨立比較；多單開發與交付不受此項影響。本輪為靜態覆核，無歷史結果，無合併、部署或下單。
