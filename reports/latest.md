# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 04:09:37
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7227232528

<!-- comment_id: 7227232528 -->

【2026-11-28 04:10 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.3｜PR #7 新固定 commit `e7ec397b0f17a830c97e27bdcc574101578f4a42` 已落地並通過 5/5 live raw 驗收（取代 `#7226582272` 待推狀態）

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`
- **版本**：`v1.3`（取代 `#7226582272` 中「尚未推上遠端」狀態；接續 PR #7 父提交 `86ba35af90847af2e88e422e020c9a6375c472dd`）
- **時間與時區**：回覆 `2026-11-28 04:10 UTC+8`；本輪 live raw 下載、雜湊核對與純合成測試覆核起迄（UTC）`2026-11-27T20:08:42Z` → `2026-11-27T20:09:04Z`
- **資料截止**：本輪零真實行情讀取、零歷史回測執行；所有測試均於下載之 live raw 檔案上以 100% 合成記憶體／暫存 SQLite／暫存 NPZ 執行。

### 一、PR #7 狀態與 5/5 Live Raw 實測證據
- **PR 狀態**：[PR #7](https://github.com/LeoCheng802/Grok-Bot/pull/7) 實測 `state = open`、`draft = true`、`merged = false`、`commits = 2`、`base = research/offline-packaging-hardening-draft`（`087e2585d2edb4c9172b06bf4671d8033a1c21c8`）、`head = e7ec397b0f17a830c97e27bdcc574101578f4a42`；`main` 未更動，不合併、不部署、`live_approved: false`。
- **5 檔 live raw HTTP 200、大小、SHA-256 與靜態檢查（零 `assert`、零私有路徑／憑證外洩）**：
  1. [run_retest24_bounded_backtest.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/e7ec397b0f17a830c97e27bdcc574101578f4a42/research/long_struct_01/code/run_retest24_bounded_backtest.py)：`47,821` B，SHA-256 `d04744b10e0e10d44da95ff93c0f3d48958d20f2ce242431d512aa0dd5a1d048`（較本機草稿僅變數命名與註解字元微異，已逐行 diff 確認邏輯完全一致且通過全部回歸）
  2. [test_retest24_bounded_synthetic.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/e7ec397b0f17a830c97e27bdcc574101578f4a42/research/long_struct_01/code/test_retest24_bounded_synthetic.py)：`8,104` B，SHA-256 `7188f01ce8f4fbd54c0ed20ae9225c107563843b2b71c373cc09d91bf7e977ad`（於 live 複本執行通過：`ALL_RETEST24_V1_3_SYNTHETIC_TESTS_PASS`；含舊 `set` 形狀 `AttributeError` 重現、`ts_raw > ts_snapped` SQLite fixture、未命中回退、NPZ 竄改／路徑重疊阻斷、30 筆不截斷 `miss_8h`）
  3. [run_long_struct_bounded_backtest.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/e7ec397b0f17a830c97e27bdcc574101578f4a42/research/long_struct_01/code/run_long_struct_bounded_backtest.py)：`41,144` B，SHA-256 `52ac6e85d7ff4a915d2f7dc8a5d8a2e409116802d17b65208de4d813c4038331`（三模式多單限價：`LONG_STRUCT_01_V1_2_FROZEN`、`LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT`、`LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT`；`load_funding_db` 採 `inst → ts_snapped → ts_raw` 字典；`B24H`／`A60＋量縮` 標註「歷史設計對照未完成」）
  4. [test_long_struct_bounded_synthetic.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/e7ec397b0f17a830c97e27bdcc574101578f4a42/research/long_struct_01/code/test_long_struct_bounded_synthetic.py)：`5,960` B，SHA-256 `02d9e71c67c671a0f6257527b172396ba6515dd949eeb1d96630136e9f0145b9`（於 live 複本執行通過：`ALL_SYNTHETIC_TESTS_PASS`）
  5. [V1_2_AUTONOMOUS_DELIVERY_NOTES.md](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/e7ec397b0f17a830c97e27bdcc574101578f4a42/research/long_struct_01/V1_2_AUTONOMOUS_DELIVERY_NOTES.md)：`5,019` B，SHA-256 `f70fb02983d7ce6a090bf13cb12ed46c20a89453a3ca07df35a9522da32d3f7d`

### 二、ChatGPT 隔離環境獨立驗證／回測命令（僅供 ChatGPT 執行，本端不跑歷史回測）
- **純合成測試（不需行情資料）**：
  - `python3 research/long_struct_01/code/test_retest24_bounded_synthetic.py`
  - `python3 research/long_struct_01/code/test_long_struct_bounded_synthetic.py`
- **空單歷史模型 adapter（含 `--input-manifest` 選用逐檔 NPZ 綁定與離線本機明細輸出）**：
  - `python3 research/long_struct_01/code/run_retest24_bounded_backtest.py --manifest <REPRO_MANIFEST.json> --retest24-script <RETEST24_v1_5.py> --shared-risk <shared_risk.py> --cache-dir <cache_v3> --funding-db <funding.sqlite> --out-dir <out_dir> --candidate RETEST24_V1_5_FROZEN`
  - （同命令切換 `--candidate RETEST24_OPT_01_BEARISH_CLOSE_POS` 跑單因子對照；可加 `--dry-check` 先核對 `HISTORICAL_MODEL_VS_DELIVERED_SCRIPT_DIFF`）
- **多單限價三模式 adapter**：
  - `python3 research/long_struct_01/code/run_long_struct_bounded_backtest.py --manifest <REPRO_MANIFEST.json> --shared-risk <shared_risk.py> --cache-dir <cache_v3> --funding-db <funding.sqlite> --out-dir <out_dir> --start-utc 2023-01-01T00:00:00Z --end-utc 2026-11-26T12:00:00Z --candidate <LONG_STRUCT_01_V1_2_FROZEN|LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT|LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT>`

### 三、缺口與下一步
- **缺口**：歷史模型與交付腳本之差異（`slip_mkt` 0.0003 vs 0.0005、EMA55 窗口、預設母體 vs `EXCLUDED_BASES`）仍須由 ChatGPT 分列情境比較；`B24H`／`A60＋量縮` 維持「歷史設計對照未完成」；158／128 與 50 筆資金費對帳僅作有限範圍線索。
- **下一步**：交由 `@復盤` 獨立覆核新固定 head `e7ec397b0f17a830c97e27bdcc574101578f4a42`，並靜待 ChatGPT 獨立歷史回測與合成映射檢核結果。
