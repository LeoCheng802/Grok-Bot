# BACKTEST-READINESS-01 v1.20 交付說明（策略組）

- 角色：策略組（Grok 開發交付；群組不跑任何歷史／績效回測）
- 研究編號：BACKTEST-READINESS-01／COMBO_L02_OPT01_SHARED_50K_10X
- 版本：v1.20（對應 ChatGPT v1.20，Issue #1 #7235223075 與補充 #7235255702；另含 復盤 的 5 項非阻擋補正）
- 基底：PR #7 head `c1c8c53d6db32644381480aeab3a8380c5c167c4`（parent `23ff0e26ca2b644addb7f39e44843687402dc4ce`；v1.19 交付 6 檔大小／SHA 由 raw 重抓核對一致後才修改）
- 資料截止：本輪沒有新資料、沒有抓任何市場資料；runner 預設窗口仍為 2023-01-01T00:00:00Z ～ 2026-11-26T12:00:00Z
- 狀態：PRELIMINARY 工具交付；`live_approved: false`；`FIB-4H-LONG-V3` 維持 `NO-GO`；PR 維持 Draft，不合併、不部署、不交易

## 交付檔案（research/long_struct_01/）

| 檔案 | 狀態 | 大小 (B) | SHA-256 |
|---|---|---|---|
| code/run_combo_l02_opt01_shared_backtest.py | 修改（v1.19 → v1.20） | 60572 | 6574ded3971811adc80c8ff28e95c769c332da6ab206bba960a5e83d988085a2 |
| code/test_combo_l02_opt01_shared_synthetic.py | 修改（16 → 19 項） | 40430 | 7bc1b9b597b6a4b5297785e5c8659a399e75d90e49f45b28b14561bce642a88a |
| code/old_result_impact_scope_v1_19.py | 就地更新（檔名不變） | 16268 | 73270d51162242c303120002e96a115355d5df2cf1d0cc1ee947e453459298a4 |
| code/test_old_result_impact_scope_v1_19.py | 就地更新（7 → 10 項） | 17163 | 8467ef76839642658ebbd26700050242048d911156fdc76a68bd7fce1495eebd |
| COMBO_L02_OPT01_SHARED_PREREG_v1.1_DIFF.json | 更新（DEV-1 與待決項改為已定案） | 5759 | acb54565832fa63bb2ea4c45b87fc8a125e32d02b1032bccfe577f0d9f395bd1 |
| V1_19_DELIVERY_NOTES.md | 更正措辭（rename 前再檢 → 寫 .tmp 前第二次檢查；待決項已定案） | 11847 | 2452f05a4bb857a04488f621c842025ab578369cdcb2551107d9d34023698f3b |
| V1_20_DELIVERY_NOTES.md | 新增（本檔） | 見推送回報 | 見推送回報 |

impact 工具選擇**原檔就地更新**（檔名維持 `old_result_impact_scope_v1_19.py`，內部版本標 v1.20），以減少檔案數；它仍然取代 `old_result_impact_scope_v1_17.py`（該檔保留供稽核，不再用於新評估）。其餘檔案（L1、LONG／RETEST24 adapter、PREREG v1.0、engine、其餘測試）沿用 c1c8c53d，未動。程式預設值全部不變。

## 逐項對應（5 項非阻擋補正＋定案口徑）

| # | 要求 | 做法 | 回歸測試（新版 PASS／舊版 c1c8c53d FAIL） |
|---|---|---|---|
| 1 | embedded cutoff 無效時 parse 拋錯 | 選「標 UNDETERMINABLE」（與既有「證據不足標 UNDETERMINABLE」語意一致）：details 內嵌 `cutoff_utc` 若不是合法 UTC 字串（亂字串、缺 Z、非字串、空字串、list）→ 該檔每個情境 `UNDETERMINABLE`，原因 `details_embedded_cutoff_invalid`，整份評估不中止；合法且相等維持乾淨判定，合法但不同維持 `cutoff_mismatch...`。CLI 的 `--cutoff-utc` 仍嚴格：不合法直接拒絕並給訊息 | `test_invalid_embedded_cutoff_is_undeterminable`（舊版 RuntimeError 中止整份評估） |
| 2 | `missing_funding_events_all` 非 list | 該情境 `UNDETERMINABLE`，原因 `missing_funding_events_not_a_list`，不中止；缺欄位（None）維持原語意視為空；其他持倉證據照常評估 | `test_missing_funding_events_not_list_is_undeterminable`（舊版 TypeError 中止） |
| 3 | 「rename 前再檢」措辭 | impact docstring、報告新增的 `write_safety` 欄位、V1_19 交付說明都改為：輸出與 `.tmp` 在雜湊前檢查一次，並在**寫入 .tmp 之前**再檢查一次；這不是 rename 時的檢查，**不保證**任意並行變更都不會覆寫，研究請用新的隔離單一寫入目錄。程式行為不變 | `test_write_safety_wording`（舊 docstring 仍寫 before the rename） |
| 4 | limitations／diff 寫死「600U UTC-day」 | 新增 `describe_controls(args)`：`limitations` 與 `combo_model_vs_live_shared_risk_diff` 依實際 `--leg-daily-loss-day`（UTC／台北）與 `--global-daily-loss-u`、`--global-max-slots`、`--same-inst-policy`、`--cross-leg-order` 動態輸出；共同日損關閉（`0`）時明寫「本次沒有共同日損限制」，文字與 diff 都不含 600；各腿限制在 diff 只寫「沿用凍結各腿限制」不帶數字；scope 內「pending 77/ChatGPT」字樣改為「不是 ChatGPT v1.20 主比較口徑」 | `test_limitations_text_follows_parameters`（utc／taipei／全局 0／自訂 250U 四種；舊版沒有 UTC 日界文字、仍含 `600U UTC-day`） |
| 5 | PR #7 說明 Current Live Head | 見 `pr7_description_current_live_head_v1_20.md`（隨推送指令檔，由 cloud agent 推送後把 `<NEW_COMMIT_SHA_40>` 換成實際 commit 並更新） | — |

## ChatGPT 已定案的主比較口徑（#7235223075、#7235255702；程式預設不改）

1. 各腿日損日界：主比較明確帶 `--leg-daily-loss-day utc`（沿用已完成獨立歷史模型）。程式預設仍是 `taipei`，台北日只作另列情境；**不得**忘記帶旗標。
2. 主組合：`--cross-leg-order rank_interleave`（同順位多單先，預設即是）＋ `--global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off`。這不是取消全部風控：各腿原限制與共享保證金拒單仍在。共同 12 槽／600U／`block_any` 只作另列研究情境，不混入主比較，也沒有授權重跑全部組合。
3. 0.0005 滑價、實際候選映射、多單 12 槽由 ChatGPT 原研究單一流程處理並隔離驗證；本版 adapter 現值（0.0003／多單原 24 槽）**不改**，不能冒稱已對齊。
4. 月 100–200 筆目標：按多空合計「完整最終平倉」、以**出場 UTC 月**統計；另列首次成交與方向貢獻；不能用開倉數代替。

新增合成測試 `test_main_comparison_parameter_set` 以上述旗標組合（兩個 arm：`R1_150U|cross_1tick`、`OPT01_SIG_R2_SIZING_100U|cross_1tick`）端到端跑通，檢查：rc=0、scope 為 utc／rank_interleave 且無 PREREG 偏離、三項另加控制皆關閉、同一幣可兩腿同時持有、兩腿皆有平倉、combined 月統計＝多＋空、limitations 描述這組口徑且不含 600。偏離預設值的只有「呼叫時帶的旗標」，沒有改程式預設，所以本版沒有新增偏離。

## 月統計輸出（新增純輸出欄位，不影響交易邏輯）

每個 arm 新增 `monthly_combined`：
- `by_year_month[月]`：`closed_trades_total`（多＋空完整最終平倉，依出場 UTC 月）、`unique_first_fills_total`（首次成交，依成交 UTC 月，含仍持有）、`closed_net_u_total`、多／空各自的 `closed_trades`／`unique_first_fills`／`closed_net_u`、`is_partial_month`、`in_target_band_100_200`（只判完整月，部分月為 null）。
- `summary`：完整月數、落在 100–200 的月數、低於、高於。
- `definition`：明寫開倉不算完整交易、`open_at_end` 不算完整平倉。
測試：`test_monthly_combined_statistics`（合成 3 筆：2 多 1 空；另以捏造月資料驗證 1 月 150 筆在帶內、2 月 11 筆含「1 月開倉、2 月出場」的一筆依出場月歸 2 月、低於帶）。舊版沒有此欄位（KeyError）。僅合成資料，未讀任何歷史資料。

## 測試清單與結果（全部純合成；未跑歷史回測、未抓市場資料）

| 測試 | 結果 |
|---|---|
| test_combo_l02_opt01_shared_synthetic.py（19 項）對新 runner | rc=0，`ALL_COMBO_L02_OPT01_SHARED_SYNTHETIC_TESTS_PASS` |
| 同上套在 c1c8c53d 舊 runner | rc=1，4 項 FAIL（limitations 文字、主比較參數組合、月統計、版本標籤），15 項舊測試 PASS |
| test_old_result_impact_scope_v1_19.py（10 項）對新工具 | rc=0，`ALL_IMPACT_SCOPE_V1_19_SYNTHETIC_TESTS_PASS` |
| 同上套在 c1c8c53d 舊工具 | rc=1，3 項 FAIL（第 1、2、3 點），舊 7 項 PASS |
| test_old_result_impact_scope_v1_17／L1／LONG／RETEST24 測試（未改） | 全部 rc=0 PASS |
| offline_static_check.py、py_compile | rc=0 |

## 未決事項

- 日損日界、同順位排序、另加控制的主比較口徑已由 ChatGPT 定案，無待決。
- 仍由 ChatGPT 原研究處理：0.0005 滑價、候選映射、多單 12 槽、隔離修正、真正共用 50000/10x 的完整執行與 R2 獨立基準。
- 程式預設仍為 taipei 日界與 12 槽／600U／block_any；若 ChatGPT 之後希望改預設以免漏帶旗標，需另行決定並列為偏離。

## 指令範本（只給 ChatGPT 原研究使用；群組不執行）

```
# 主比較（ChatGPT v1.20 定案口徑）
python3 research/long_struct_01/code/run_combo_l02_opt01_shared_backtest.py --manifest <REPRO_MANIFEST_JSON> --retest24-script <RETEST24_PY> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --funding-inventory <FUNDING_MONTH_INVENTORY_CSV> --leg-daily-loss-day utc --cross-leg-order rank_interleave --global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off --out-dir <NEW_EMPTY_OUT_DIR>
# 另列情境（各用新的 out-dir）：加回 --global-max-slots 12 --global-daily-loss-u 600 --same-inst-policy block_any；或 --leg-daily-loss-day taipei
python3 research/long_struct_01/code/old_result_impact_scope_v1_19.py --details <OLD_DETAILS_JSON> --cutoff-utc <THAT_RUN_END_UTC> --delta <DELTA_CSV_GZ> --out <NEW_ASSESSMENT_JSON>
```

紅線：不公開私人明細（combo_local_details.json 只留本機）、不含帳密／config.json／本機路徑；兩個 PR 維持 Draft，不合併、不部署、不下單；`live_approved: false`。
