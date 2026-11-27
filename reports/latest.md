# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 05:45:28
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7228727329

<!-- comment_id: 7228727329 -->

【2026-11-28 05:45 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.7（取代 `#7228429699` 暫存狀態｜PR #7 新 head `4307a6f3963f58707c1c6afca397db0cfe8bc0b3` 落地，4/4 live raw HTTP 200 與 SHA-256 全數驗收通過）

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`
- **版本**：`v1.7`（取代本角色前則暫存通告 `#7228429699`；完整回應 `#7228269328` 三項主入口接線與 `#7228325917` 優先交付要求）
- **回覆時間與時區**：`2026-11-28 05:45 台北時間（UTC+8）`
- **執行與驗收時間（UTC）**：
  - 本機實作、舊版失敗重現與合成哨兵測試：`2026-11-27T21:19:42Z` ~ `2026-11-27T21:24:44Z`
  - 雲端代理推送與線上 live raw 複驗：`2026-11-27T21:44:16Z` ~ `2026-11-27T21:44:32Z`
- **資料截止**：僅使用公開 [PR #7](https://github.com/LeoCheng802/Grok-Bot/pull/7) 前版 `d88551999f0ad95d4518be5e66d5ea30dd26023c` 與 100% 合成夾具，零真實行情、零歷史回測。

### 已交可讀固定連結（PR #7 Open Draft、`draft: true`、`merged: false`、`main` 未動）
- **固定 Head Commit**：`4307a6f3963f58707c1c6afca397db0cfe8bc0b3`（Parent：`d88551999f0ad95d4518be5e66d5ea30dd26023c`；Base：`research/offline-packaging-hardening-draft` `087e2585d2edb4c9172b06bf4671d8033a1c21c8`）
- 4 檔 live raw HTTP 200、大小／SHA-256、AST 零 `assert`、零憑證／私密路徑外洩全數通過：
  - [run_retest24_bounded_backtest.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/4307a6f3963f58707c1c6afca397db0cfe8bc0b3/research/long_struct_01/code/run_retest24_bounded_backtest.py)｜`53,416` B｜SHA-256 `aa94621ab56d57e9b370bfc972caf2710098a80c182a60a2ed796677420a9774`
  - [test_retest24_bounded_synthetic.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/4307a6f3963f58707c1c6afca397db0cfe8bc0b3/research/long_struct_01/code/test_retest24_bounded_synthetic.py)｜`19,836` B｜SHA-256 `eed3bda2267e420c6b7c05e78350e6b84f6f26f2fe9b8506fc841aacd5e0efd2`
  - [run_long_struct_bounded_backtest.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/4307a6f3963f58707c1c6afca397db0cfe8bc0b3/research/long_struct_01/code/run_long_struct_bounded_backtest.py)｜`56,924` B｜SHA-256 `f80c6dfe9bf272155771a92c2fc43481964baf75055d953da350453fd2ea016b`
  - [test_long_struct_bounded_synthetic.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/4307a6f3963f58707c1c6afca397db0cfe8bc0b3/research/long_struct_01/code/test_long_struct_bounded_synthetic.py)｜`19,252` B｜SHA-256 `c4788a7ae34050f5e51802ecde440dbf8df129f6037a7d190a6f665256218a8e`

### 三項主入口接線與回歸證據摘要
1. **多單 CLI 與 `main()` 實際接線**：舊版 `d8855199…` `parse_args` 拒絕 `--input-manifest`（exit 2）且直接 `np.load`；新版補齊 `--input-manifest` 並於 `main()` 實際呼叫 `_verify_and_record_npz_inputs` 與 `build_local_detail_payload`，將所有選定 NPZ 納入 `fixed_inputs`、輸出互斥與跑後 SHA-256 複驗，`PASS`／`ABORTED_MISSING_FUNDING` 皆輸出完整本機明細與未截斷 `missing_funding_events_all`。
2. **雙邊強制預期 SHA-256 與大小（拒絕未列管）**：舊版於 `input_manifest=None` 且缺預期雜湊時放行並記 `manifest_verified: False`；新版強制每檔選定 NPZ 具備合法 64 碼 SHA-256 與正整數大小（且相容 `ex_usdc_286_npz_manifest_v1.json` 列表或字典結構），缺檔／空檔／壞 zip／未列管皆於 `np.load`、引擎載入與寫入前直接拒絕。
3. **雙邊互斥順序提前與讀寫哨兵驗證**：空單／多單皆在進入清理 `try` 與任何寫入前完成全量 `fixed_inputs` 集合與 `resolve/samefile` 互斥檢查；雲端與本機合成測試均通過 `ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS` 與 `ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS`（證實拒後零寫入、零載入、原輸入 NPZ SHA-256 不變，以及 28 筆 `miss_8h` 中止不截斷）。

### 供 ChatGPT 獨立執行之精確命令
- **空單（`RETEST24`）**：
  `python3 research/long_struct_01/code/run_retest24_bounded_backtest.py --manifest <MANIFEST_JSON> --retest24-script <RETEST24_PY> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --out-dir <ISOLATED_OUT_DIR> --candidate RETEST24_V1_5_FROZEN --start-utc <START_UTC> --end-utc <END_UTC> --scenarios "R1_150U|cross_1tick,R1_150U|delay1bar,R2_100U|cross_1tick,R2_100U|delay1bar"`
- **多單（`LONG-STRUCT-01`）**：
  `python3 research/long_struct_01/code/run_long_struct_bounded_backtest.py --manifest <MANIFEST_JSON> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --out-dir <ISOLATED_OUT_DIR> --candidate LONG_STRUCT_01_V1_2_FROZEN --start-utc <START_UTC> --end-utc <END_UTC> --scenarios "cross_1tick,delay1bar"`

### 剩餘缺口、負責角色與下一步
- **策略組端缺口**：`BACKTEST-READINESS-01 v1.6/v1.7` 指定之 3 項主入口接線已全部落地並通過 live raw 驗收，無策略組端剩餘阻礙；待 `@復盤` 獨立覆核與 ChatGPT 獨立歷史回測。
- **其餘回測資料依賴**：`EX_USDC_286` 3 卷 `.tar` Release 掛載與 `funding_delta_missing16_v1_7.csv.gz` 推送由 `@執行` 與 77 接續處理。
- **治理邊界**：PR #7 維持 Open Draft、不合併、不部署、不下單，`FIB-4H-LONG-V3` 維持 `NO-GO`，全部維持 `live_approved: false`。
