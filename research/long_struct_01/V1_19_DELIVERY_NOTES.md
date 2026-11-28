# BACKTEST-READINESS-01 v1.19 交付說明（策略組）

> v1.20 更正（就地）：(1) impact「rename 前再檢」措辭改為「寫 .tmp 前第二次檢查」，不聲稱可保證並行變更不覆寫；(2) 日損日界待決事項已由 ChatGPT #7235223075 定案。完整 v1.20 變更見 V1_20_DELIVERY_NOTES.md。

- 角色：策略組（Grok 開發交付；群組不跑任何歷史／績效回測）
- 研究編號：BACKTEST-READINESS-01／COMBO_L02_OPT01_SHARED_50K_10X
- 版本：v1.19（對應 ChatGPT v1.19 交接，Issue #1 留言 #7231413139；另含 復盤 #7231409226 與 風險管理 群組意見）
- 基底：PR #7 head `23ff0e26ca2b644addb7f39e44843687402dc4ce`（本輪先由 raw 重抓，8 個 v1.17 交付檔大小／SHA 全部吻合後才修改）
- 資料截止：本輪沒有新資料、沒有抓任何市場資料；組合 runner 預設窗口仍為 2023-01-01T00:00:00Z ～ 2026-11-26T12:00:00Z；資金費資料參考 PR #8 head `f1280dc41d8409ed856fd41c339ff095a67ebe74`（只作參考，未讀取）
- 狀態：PRELIMINARY 工具交付；`live_approved: false`；`FIB-4H-LONG-V3` 維持 `NO-GO`；PR 維持 Draft，不合併、不部署、不交易

## 交付檔案（research/long_struct_01/）

| 檔案 | 狀態 | 大小 (B) | SHA-256 |
|---|---|---|---|
| code/run_combo_l02_opt01_shared_backtest.py | 修改（v1.17 → v1.19） | 54769 | 36bd693a777b4284875b1d2313ec849f98e98287d524f3f2be18a683e8627a88 |
| code/test_combo_l02_opt01_shared_synthetic.py | 修改 | 31377 | 2b18c2850095175057fac1c9348fa3609eee2887c3b50e3f548f941b5ab4187e |
| code/old_result_impact_scope_v1_19.py | 新增（取代 v1_17，舊檔保留不動供稽核） | 14531 | b38926f9fb6c50313c00f6e5cb78b6ebf89d6aa7e84c760733c5edf437a0ad0c |
| code/test_old_result_impact_scope_v1_19.py | 新增 | 12152 | 38487f448b6e7767647c071904f2ad170828bfed47ab57bfc496733022922c2c |
| COMBO_L02_OPT01_SHARED_PREREG_v1.1_DIFF.json | 新增（差異檔；凍結的 v1.0 不改） | 5520 | 4ef65fbea1b0f335c88422eb4676cd1ef9b9c14a49c5fde3045016c75755b45a |
| V1_19_DELIVERY_NOTES.md | 新增（本檔） | 見推送回報 | 見推送回報 |

未變動（沿用 23ff0e26）：`COMBO_L02_OPT01_SHARED_PREREG_v1.0.json`（7228 B，98c6b5e3…b543f）、`run_long_struct_bounded_backtest.py`（57609 B，8db9e3fd…10a59）、`run_retest24_bounded_backtest.py`（54101 B，67094079…42f89）、`run_l1_bounded_backtest.py`（48621 B，0d7e316e…db15）、`old_result_impact_scope_v1_17.py`（6275 B，b824758f…abcd1，已被 v1_19 取代，請勿再用於新評估）、engine/*。

L1 runner 不改：ChatGPT v1.19 已靜態接受 L1 單一版本標籤與新 outdir 防護，且明言不為標籤重跑 L1，所以 L1 的版本字串維持 v1.17。

## 逐點對應（ChatGPT v1.19 六點＋群組兩點）

| # | 要求 | 本次做法 | 回歸測試（新版 PASS／舊版 23ff0e26 FAIL） |
|---|---|---|---|
| 1 | impact 只查 --out、沒查 out.tmp | `--out` 與 `--out.tmp` 都要和每個輸入 resolve 不同、且 `os.path.samefile` 不同；既存 `.tmp`、symlink（含懸空 symlink）一律拒絕；`.tmp` 以 O_CREAT\|O_EXCL 建立；寫 .tmp 前再檢一次（v1.20 更正措辭：這是寫入暫存檔之前的第二次檢查，不是 rename 時的檢查，也不保證任何並行變更都不會覆寫；請用新的隔離單一寫入目錄） | `test_out_tmp_aliases_input`（舊版把輸入 `assessment.json.tmp` 截斷）、`test_existing_tmp_and_symlink_refused`（舊版覆寫既存 .tmp） |
| 2 | open_at_end 沒有截止上界等 | 每個 `--details` 必配一個 `--cutoff-utc`（該次回測真實截止）；open_at_end 區間 (ets, cutoff]，截止後的 delta 不算；closed 清單或 open_at_end 清單缺、schema 錯、筆數未宣告或不符、持倉超出截止 → UNDETERMINABLE；inputs/assessments 改成依參數序號的清單，同 basename 不覆蓋；衝突 delta 鍵不進乾淨集合，碰到持倉區間就 UNDETERMINABLE，`delta_clean=false` | `test_open_at_end_bound_to_cutoff`、`test_missing_evidence_is_undeterminable`、`test_same_basename_not_overwritten`、`test_conflicting_delta_not_clean`（舊版各自 FAIL） |
| 3 | 51001 變成整月禁進場 | inventory 的 `rest_51001_instrument_not_listed` 改為「資金費註記」：母體保留、不擋進場、缺費率維持未知（不補零、不內插），每筆碰到該月的持倉帶 `funding_notes`，arm gaps 列 `positions_in_rest_51001_funding_months_rates_unknown`。只有 `--uncomputable-windows` 且每筆有非空 `evidence`（必要價格確實缺）才列不可計算 | `test_uncomputable_windows`（舊版擋 D 進場）、`test_explicit_window_needs_evidence`（舊版接受無證據視窗） |
| 4 | 跨方向排序與另加研究風控 | `--cross-leg-order rank_interleave`（預設）：各方向內仍用原本凍結排序鍵（穩定排序），跨方向以同尺度名次 0,1,2… 交錯，同名次依 `--leg-priority`（預設 long_first＝同順位多單先）；`direction_block` 保留 v1.17 行為只作敏感度。共同 12 槽、共同 600U 台北日限、block_any 在 scope 另列 `research_added_risk_controls`，與 `established_combo_basis` 分開，可各自關閉（`--global-max-slots 0`、`--global-daily-loss-u 0`、`--same-inst-policy off`），預設值不變 | `test_cross_leg_rank_interleave`（舊版給出整個多方向先）、`test_research_controls_switchable_and_listed`（舊版不接受 0／off） |
| 4（不在範圍） | 候選映射、滑價、24 槽 | 依指示**不自行定版**：滑價維持 adapter 現值 0.0003、多單每腿 24 槽維持現值、不設 0.0005／24 槽為預設。**候選映射、滑價對齊與隔離修正由 ChatGPT 原研究完成，不在本次範圍**；scope `established_combo_basis.out_of_scope` 與結果 limitations 都寫明 | — |
| 5 | R2 命名 | 組合臂 `R2_100U` 改名 `OPT01_SIG_R2_SIZING_100U`（OPT01 訊號套 R2 倉位 100U／400U）；arm 帶 `short_sizing_note` 寫明它**不是** R2 對照，「R2」指原 RETEST24 R2 獨立基準（已上傳腳本），此臂不得代替；舊名 `R2_100U` 會被拒絕並說明 | `test_r2_arm_renamed`（舊版不認得新名） |
| 6 | adapter 先載入後驗證 | 進入 `main` 先開外層 `OfflineGuard`（socket.create_connection／connect／connect_ex／getaddrinfo、urllib、http.client 全擋），再各讀一次兩個 adapter，比對完整大小與 SHA-256（預設比對程式內固定常數；換路徑時必須同時給 `--*-adapter-size` 與 `--*-adapter-sha256`），通過後只執行已驗的那份位元組，不再讀檔；不符就在任何 adapter 程式碼執行前拒絕 | `test_adapter_verified_before_load`（舊版會執行未驗 adapter 的程式碼）、`test_network_blocked_before_adapter_load`（只連 127.0.0.1:9；舊版得到 ConnectionRefusedError，代表未擋） |
| 7 | 日損日界（風險管理／復盤） | 各腿日損改為參數 `--leg-daily-loss-day`，預設 `taipei`（Asia/Taipei 00:00 重置），可選 `utc`（凍結 PREREG v1.0 口徑）；scope 寫 `leg_daily_loss_day` 與 `prereg_deviations`。凍結的 PREREG v1.0 不改，另出 `COMBO_L02_OPT01_SHARED_PREREG_v1.1_DIFF.json`（DEV-1，待 77／ChatGPT 確認） | `test_leg_daily_loss_day_boundary`（20:00Z 虧損＝台北隔日 04:00；舊版在 00:00Z 換 UTC 日後照樣下單） |
| 8 | 修補後引擎原始碼 SHA（復盤） | 實跑時把實際執行的修補後引擎原始碼寫到 out-dir `combo_engine_patched_source.txt`，SHA-256 記在 `combo_result.json` 的 `combo_engine_patched_source_sha256`、`sha256.combo_engine_source`、`sha256.combo_engine_source_file`，並在結束前重核 | `test_engine_source_sha_recorded`（舊版沒有這個檔） |

其他：`combo_local_details.json` 每個情境新增 `counts` 與檔頭 `cutoff_utc`／`last_bar_30m_utc`，讓 v1_19 impact 工具能核筆數與截止。

## 測試清單與結果（全部純合成，臨時目錄、樁資料；未跑任何歷史回測、未抓市場資料）

| 測試 | 對象 | 結果 |
|---|---|---|
| test_combo_l02_opt01_shared_synthetic.py（v1.19，16 項） | 新 runner | rc=0，`ALL_COMBO_L02_OPT01_SHARED_SYNTHETIC_TESTS_PASS` |
| 同上，`COMBO_RUNNER_PATH`=23ff0e26 舊 runner | 舊 runner | rc=1，10 項 FAIL（正好是 3／3／4／4／5／6／6／7／8 各新測試與版本標籤），6 項舊有測試 PASS |
| test_old_result_impact_scope_v1_19.py（7 項） | v1_19 工具 | rc=0，`ALL_IMPACT_SCOPE_V1_19_SYNTHETIC_TESTS_PASS` |
| 同上，`IMPACT_TOOL_PATH`=v1_17 工具 | 舊工具 | rc=1，6 項 FAIL（第 1、2 點），legacy 語意 1 項 PASS |
| v1.17 原 test_combo（23ff0e26）對新 runner | 新 runner | rc=1，8 項 FAIL：舊樁 adapter 沒有預期 SHA，被第 6 點拒絕（預期中的介面變更）；新版測試已改為傳入樁的大小與 SHA |
| test_old_result_impact_scope_v1_17.py | v1_17 工具（未改） | rc=0 PASS |
| test_l1_bounded_main_synthetic.py | L1（未改） | rc=0 PASS |
| test_long_struct_bounded_synthetic.py | LONG adapter（未改） | rc=0 PASS |
| test_retest24_bounded_synthetic.py | RETEST24 adapter（未改） | rc=0 PASS |
| offline_static_check.py | 全目錄 | rc=0 |
| py_compile（4 支 .py） | — | OK |

v1.13 L1 舊測試的 case 2 在 v1.17 之後的 L1 runner 會失敗（重用輸出目錄被拒）屬預期，沿用 v1.17 紀錄；L1 本輪未改。

## 偏離預註冊清單（PREREG v1.0 → v1.1 差異檔）

1. DEV-1 各腿日損日界：v1.0 為 UTC 日 → 預設台北日（可選 utc），（v1.20 更新：ChatGPT #7235223075 已定案主比較明確帶 `--leg-daily-loss-day utc`；台北日只作另列情境，程式預設不變。）
2. DEV-2 REST 51001：v1.0 為整個 CST 月不可計算並擋進場 → 只註記資金費未知，不擋進場；只有有證據的缺價視窗才不可計算（ChatGPT 要求的更正）。
3. DEV-3 跨方向排序：v1.0 為整個方向先後 → 同尺度名次交錯、同順位多單先（ChatGPT 要求的更正）。
4. DEV-4 R2 命名：v1.0 的 `R2_100U`「R2 對照」→ 改名 `OPT01_SIG_R2_SIZING_100U`，不是 R2 對照（ChatGPT 要求的更正）。

## 未決參數（需 77 或 ChatGPT 決定）

- 各腿日損日界：taipei（預設）或 utc。
- 另加研究風控（共同 12 槽／共同 600U 台北日限／block_any）在主臂維持開啟，或改為只作敏感度。
- 同順位 tie-break：預設 long_first（依 ChatGPT「同順位多先」），short_first 只作敏感度。
- 候選映射、滑價對齊（原研究 0.0005 vs 目前 0.0003）、原 24 槽與隔離修正：由 ChatGPT 原研究完成，不在本次範圍。
- R2 對照：原 RETEST24 R2 獨立基準由 ChatGPT 原研究產出；組合內的 `OPT01_SIG_R2_SIZING_100U` 不能代替。

## 指令範本（只給 ChatGPT 原研究使用；群組不執行）

```
python3 research/long_struct_01/code/run_combo_l02_opt01_shared_backtest.py --manifest <REPRO_MANIFEST_JSON> --retest24-script <RETEST24_PY> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --funding-inventory <FUNDING_MONTH_INVENTORY_CSV> --out-dir <NEW_EMPTY_OUT_DIR>
# 敏感度：--leg-daily-loss-day utc ｜ --cross-leg-order direction_block ｜ --leg-priority short_first ｜ --global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off（每次都要新的 out-dir）
python3 research/long_struct_01/code/old_result_impact_scope_v1_19.py --details <OLD_DETAILS_JSON> --cutoff-utc <THAT_RUN_END_UTC> --delta <DELTA_CSV_GZ> --out <NEW_ASSESSMENT_JSON>
```

紅線：不公開私人明細（combo_local_details.json 只留本機）、不含帳密／config.json／本機路徑；兩個 PR 維持 Draft，不合併、不部署、不下單；`live_approved: false`。
