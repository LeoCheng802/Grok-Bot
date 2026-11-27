# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 05:25:22
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7228429699

<!-- comment_id: 7228429699 -->

【2026-11-28 05:25 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.6/v1.7（三項主入口接線、強制 NPZ manifest／雜湊預檢、先互斥後寫入與 `main()` 哨兵回歸測試已本機通過；待 77 1:1 啟動雲端推送）

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`
- **版本**：`v1.7`（對應 `#7228269328` 三項主入口接線與 `#7228325917` 優先交付要求；線上可讀 head 仍為 `d88551999f0ad95d4518be5e66d5ea30dd26023c`，本批 4 檔尚在本機暫存、尚未推送）
- **回覆時間與時區**：`2026-11-28 05:25 台北時間（UTC+8）`
- **本機實作、舊版重現與合成哨兵測試執行時間（UTC）**：`2026-11-27T21:19:42Z` ~ `2026-11-27T21:24:44Z`
- **資料截止**：僅使用公開 [PR #7](https://github.com/LeoCheng802/Grok-Bot/pull/7) `d88551999f0ad95d4518be5e66d5ea30dd26023c` 原件與 100% 合成夾具，零真實行情、零歷史回測。

### 已完成事項（含舊版重現失敗 → 新版通過證據）
1. **多單 CLI 與 `main()` 實際接線（`run_long_struct_bounded_backtest.py`）**：
   - *舊版重現失敗（`d8855199…`）*：`parse_args` 不接受 `--input-manifest`（`SystemExit: 2`）；`main()` 未呼叫 `_verify_and_record_npz_inputs` 與 `build_local_detail_payload`，直接 `np.load`。
   - *新版修正通過*：`parse_args` 已補 `--input-manifest`；`main()` 實際呼叫 `_verify_and_record_npz_inputs`（含 `ex_usdc_286_npz_manifest_v1.json` 列表或字典格式相容）與 `build_local_detail_payload`，將所有選定 NPZ 納入 `fixed_inputs`、輸出互斥與跑後 SHA-256 複驗，並於 `PASS` 與 `ABORTED_MISSING_FUNDING` 皆輸出完整本機明細與未截斷 `missing_funding_events_all`。
2. **雙邊強制預期 SHA-256 與大小（拒絕未列管）**：
   - *舊版重現失敗（`d8855199…`）*：`_verify_and_record_npz_inputs` 在 `input_manifest=None` 且 `symbols` 無預期雜湊時放行並回傳 `manifest_verified: False`。
   - *新版修正通過*：空單／多單皆強制要求每檔選定 NPZ 具備合法 64 碼預期 `sha256` 與正整數 `size_bytes`（並預檢檔案存在、非 0 bytes、合法 zip 封裝），任一缺漏、格式錯或未列管皆在 `np.load`、引擎模組載入與任何輸出寫入前直接拒絕。
3. **雙邊完整 `fixed_inputs` 與互斥檢查提前至任何寫入與清理 `try` 前**：
   - *舊版重現失敗（`d8855199…`）*：空單 `main()` 於 L969 先寫 `scope_file`，L988–993 才將 NPZ 加入互斥；多單更未將 NPZ 納入互斥。
   - *新版修正通過*：雙邊皆在進入 `try`、建立 `out_dir` 與寫入 `scope_file` 前，完成全量 `fixed_inputs`（含全部選定 NPZ 與 `--input-manifest`）之 `resolve/samefile` 互斥檢查與 NPZ 預檢；經 `main()` 讀寫哨兵（攔截 `np.load`、`_load_runtime_modules`、`_atomic_write_text`）與符號連結碰撞測例證實，拒絕時寫入次數為 `0`、載入次數為 `0`、原輸入 NPZ SHA-256 完全不變；且雙邊皆通過 `PASS`（rc=0）與 `ABORTED_MISSING_FUNDING`（rc=2，28 筆 `miss_8h` 不截斷）端對端合成測試。

### 本機暫存交付物與驗證雜湊（待推送至 PR #7，推完前仍非線上最終版）
- `run_retest24_bounded_backtest.py`：`53,416` B｜SHA-256 `aa94621ab56d57e9b370bfc972caf2710098a80c182a60a2ed796677420a9774`（`py_compile` PASS、AST `asserts=[]`、零外洩）
- `test_retest24_bounded_synthetic.py`：`19,836` B｜SHA-256 `eed3bda2267e420c6b7c05e78350e6b84f6f26f2fe9b8506fc841aacd5e0efd2`（`ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS`）
- `run_long_struct_bounded_backtest.py`：`56,924` B｜SHA-256 `f80c6dfe9bf272155771a92c2fc43481964baf75055d953da350453fd2ea016b`（`py_compile` PASS、AST `asserts=[]`、零外洩）
- `test_long_struct_bounded_synthetic.py`：`19,252` B｜SHA-256 `c4788a7ae34050f5e51802ecde440dbf8df129f6037a7d190a6f665256218a8e`（`ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS`）

### 供 ChatGPT 獨立執行之精確命令（推送後生效）
- 空單（`RETEST24`）：
  `python3 research/long_struct_01/code/run_retest24_bounded_backtest.py --manifest <MANIFEST_JSON> --retest24-script <RETEST24_PY> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --out-dir <ISOLATED_OUT_DIR> --candidate RETEST24_V1_5_FROZEN --start-utc <START_UTC> --end-utc <END_UTC> --scenarios "R1_150U|cross_1tick,R1_150U|delay1bar,R2_100U|cross_1tick,R2_100U|delay1bar"`
- 多單（`LONG-STRUCT-01`）：
  `python3 research/long_struct_01/code/run_long_struct_bounded_backtest.py --manifest <MANIFEST_JSON> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --out-dir <ISOLATED_OUT_DIR> --candidate LONG_STRUCT_01_V1_2_FROZEN --start-utc <START_UTC> --end-utc <END_UTC> --scenarios "cross_1tick,delay1bar"`

### 推送阻礙如實回報、剩餘缺項與預估時程
- **已交可讀連結**：[PR #7](https://github.com/LeoCheng802/Grok-Bot/pull/7) 目前線上可讀 head 仍為 `d88551999f0ad95d4518be5e66d5ea30dd26023c`（Open Draft、未合併）。
- **剩餘確切缺項與阻礙**：於群組回合啟動雲端代理推送 PR #7 時，遭平台攔截——被拒動作為啟動雲端代理推送分支、平台原因為群組對話不支援 Auto-review 審批卡（`This action needs Auto-review approval, which isn't available in this conversation. Run it from a direct chat with the assistant.`）、所需人工步驟為請 77 在與策略組的 1:1 私聊回覆觸發啟動。
- **負責角色與預估時間**：策略組負責於 77 私聊回覆後即刻啟動推送，預估推送與線上原件複驗約 `3–5` 分鐘內完成。`FIB-4H-LONG-V3` 維持 `NO-GO`，全部維持 `live_approved: false`。
