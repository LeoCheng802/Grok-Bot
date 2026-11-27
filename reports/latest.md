# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 04:34:46
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7227640538

<!-- comment_id: 7227640538 -->

【2026-11-28 04:34 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.4（空單／多單 B6/Q38 月報欄位對齊、多單同契約補齊、PR #7 說明去歧義與 EX_USDC_286 資料交付現況）

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`
- **版本**：`v1.4`（接續已驗收可讀 head `e7ec397b0f17a830c97e27bdcc574101578f4a42` 與 ChatGPT 審核 `#7227474241`）
- **回覆時間與時區**：`2026-11-28 04:34 台北時間（UTC+8）`
- **本機實作與合成自測執行時間（UTC）**：`2026-11-27T20:30:49Z` ~ `2026-11-27T20:34:11Z`
- **資料截止**：僅對照已釘選之 B6/Q38 引擎欄位與 100% 合成夾具，未執行任何歷史回測、未動用實盤或真實行情快取。

### 已完成事項
1. **修正空單月報與明細靜態欄位錯配（`run_retest24_bounded_backtest.py`）**：
   - 依 B6 `_ord_log` 實際欄位 `pts`（掛單）／`ets`（首次成交）與 Q38 `_trades` 實際欄位 `ets`（進場）／`xts`（出場）改寫 `summarize_run`、`_build_by_year_month`、`build_local_detail_payload`。
   - `unique_first_fills` 嚴格由 `_ord_log[outcome == "filled"]` 依 `ets` UTC 月份計數（包含期末仍開倉部位；排除 `expired`／`margin_rej`／`pend_at_end`）。
   - `closed_trades`／`closed_net_u`／`closed_fee_u`／`closed_fund_u` 嚴格依 `_trades["xts"]` UTC 月份計數；缺 `xts` 歸類為 `MISSING_EXIT_TS`，嚴禁回填成進場月。
   - 評分期間 `[start_ts, end_ts]` 內所有 UTC 月份皆明確列舉（零成交月份填 `0` 並標註 `is_partial_month`）；本機已平倉權益曲線明確標記 `equity_curve_basis: "REALIZED_CLOSED_TRADES_ONLY_NOT_MTM_UNREALIZED"`。
2. **多單依同一契約對齊補齊（`run_long_struct_bounded_backtest.py`）**：
   - 補齊 `--input-manifest`、選定 NPZ 逐檔路徑／大小／SHA-256 於載入前驗證並納入 `fixed_inputs` 輸出互斥與跑後複驗。
   - 補齊同口徑 `summarize_run`／`_build_by_year_month`／`build_local_detail_payload` 與本機未截斷缺費事件鍵（`missing_funding_events_all`）明細檔輸出。
3. **兩套合成測試全面換成真實 B6/Q38 欄位並補齊新測例（`test_retest24_bounded_synthetic.py`、`test_long_struct_bounded_synthetic.py`）**：
   - 移除所有引擎不會產生的 `order_ts`／`fill_ts`／`exit_ts` 鍵名，全面改用 `pts`／`ets`／`xts`。
   - 新增並通過：跨 UTC 月首成與平倉（`2024-01` 首成、`2024-02` 平倉）、零成交評分月份（`2024-03`）、期末仍開倉部位（`2024-04` 計入首成、不計入平倉）、非成交單排除、缺 `xts` 歸 `MISSING_EXIT_TS` 不回填進場月、SQLite `ts_raw > ts_snapped` 與未命中回退、NPZ 雜湊／竄改／輸出互斥與超過 25 筆缺費事件不截斷。
4. **PR #7 說明去歧義**：已更新 [PR #7](https://github.com/LeoCheng802/Grok-Bot/pull/7) 內文，移除舊版預期雜湊造成的歧義，維持 Open Draft、未合併。

### 本機暫存交付物與驗證雜湊（待推送至 PR #7）
- `run_retest24_bounded_backtest.py`：`51,608` B｜SHA-256 `48bb518875a2c80ace2fd4031464f25d64203d26ed218825079fb751a4acd029`（`py_compile` PASS、AST `asserts=[]`、零外洩、合成測試 PASS）
- `test_retest24_bounded_synthetic.py`：`10,577` B｜SHA-256 `4cb27366518ccb60b0e478775019c4eaf4d8e0d7248c7b3c6f3a199361d2f742`（`py_compile` PASS、AST `asserts=[]`、零外洩、合成測試 PASS）
- `run_long_struct_bounded_backtest.py`：`55,025` B｜SHA-256 `9394d47b289a3c9fe1d3fbbab3ffcebc74a0be99ac99370354bfaf80687158d8`（`py_compile` PASS、AST `asserts=[]`、零外洩、合成測試 PASS）
- `test_long_struct_bounded_synthetic.py`：`10,674` B｜SHA-256 `9d69dc24b45771beb75ec0c64460fa92baf29852eeb49ea016439a446d1c2e94`（`py_compile` PASS、AST `asserts=[]`、零外洩、合成測試 PASS）

### 既有 `EX_USDC_286` 行情快取與資金費交付途徑盤點（不公開私人路徑／不重抓／不補零／不換母體）
- **現況與確切缺項**：策略組本機與公開儲存庫內均**未存放**既有 `EX_USDC_286` 行情快取 NPZ 檔與資金費 SQLite 資料庫，目前亦尚未取得逐檔 NPZ manifest（含各檔大小與 SHA-256）及可供 ChatGPT 隔離環境直接讀取之授權離線／私有交付途徑。
- **需確認／交接項目**：需由持有既有凍結資料集之 `@執行` 與 77 確認授權交付途徑（例如私有離線壓縮包／受控讀取連結或私有庫），並產出完整 `input_manifest.json`（記錄 `cache_manifest`、資金費 SQLite 與全部選定 NPZ 之逐檔大小與 SHA-256），供 ChatGPT 直接驗證載入；在未補齊前，團隊側不重抓、不補零、不更換母體，亦不代跑歷史回測。

### 缺口與治理狀態
- 上述 4 檔目前位於本機暫存，因群組回合平台 Auto-review 限制無法直接於群組內觸發 CloudAgent 推送（非缺少 77 研究授權），已同步於 1:1 私聊請 77 觸發推送至 PR #7；推送前仍僅屬本機自報結果，以推送後固定 commit SHA 與 `@復盤`／ChatGPT 複核為準。
- `FIB-4H-LONG-V3` 維持 `NO-GO`，全部策略維持 `live_approved: false`。

### 下一步
1. 待 77 於 1:1 私聊觸發 CloudAgent 將上述 4 檔推至 [PR #7](https://github.com/LeoCheng802/Grok-Bot/pull/7)（Open Draft、父提交 `e7ec397b0f17a830c97e27bdcc574101578f4a42`），取得新固定 commit SHA 後回報 `@復盤` 複核。
2. 請 `@執行` 協助盤點既有 `EX_USDC_286` 行情快取與資金費資料庫之逐檔 manifest／SHA-256 與授權離線交付途徑（不洩漏私人路徑與憑證）。
