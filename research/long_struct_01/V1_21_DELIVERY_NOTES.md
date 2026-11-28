# BACKTEST-READINESS-01 v1.21 交付說明（策略組）

- 角色：策略組（Grok 開發交付；群組不跑任何歷史／績效回測）
- 研究編號：BACKTEST-READINESS-01／COMBO_L02_OPT01_SHARED_50K_10X
- 版本：v1.21（對應 ChatGPT v1.21 Issue #1 #7235906231、復盤 #7235923342、補充 #7235944722）
- 基底：PR #7 head `0acece2177509ec647b1dbd95da45aa95a07bd72`（parent `c1c8c53d6db32644381480aeab3a8380c5c167c4`；v1.20 交付 7 檔大小／SHA 由 raw 重抓核對一致後才修改）
- 資料截止：本輪沒有新資料、沒有抓任何市場資料；runner 預設窗口仍為 2023-01-01T00:00:00Z ～ 2026-11-26T12:00:00Z
- 狀態：PRELIMINARY 工具交付；`live_approved: false`；`FIB-4H-LONG-V3` 維持 `NO-GO`；PR 維持 Draft，不合併、不部署、不交易
- 開發與合成測試完成：2026-11-28 15:33 台北時間（UTC+8）

## 交付檔案（research/long_struct_01/）

| 檔案 | 狀態 | 大小 (B) | SHA-256 |
|---|---|---|---|
| code/run_combo_l02_opt01_shared_backtest.py | 修改（v1.20 → v1.21） | 63276 | 4d41f66ff95d0697f61ed31ce53e5288228733d09b9e8fecf8a38366ba600d8d |
| code/test_combo_l02_opt01_shared_synthetic.py | 修改（19 → 21 項） | 46327 | 3a499ea6f9eecfba7de3c3fed77df7d1df1fd5710ffa3887585453a7adb44a5d |
| code/old_result_impact_scope_v1_19.py | 就地更新（檔名不變） | 17008 | ffb2cd40c5ba891a9961fe114b322ea19590eabf2ffa6842fa22a1c6f17b6d7d |
| code/test_old_result_impact_scope_v1_19.py | 就地更新（10 項；既有 2 案各加分支） | 20690 | 16a5516f785df39d4cbe5d4388f4caa93f334625859c0a84be9df264c4a89a27 |
| V1_21_DELIVERY_NOTES.md | 新增（本檔） | 見推送回報 | 見推送回報 |

impact 工具選擇**原檔就地更新**（檔名維持 `old_result_impact_scope_v1_19.py`，內部版本標 v1.21），以減少檔案數；它仍然取代 `old_result_impact_scope_v1_17.py`（該檔保留供稽核，不再用於新評估）。其餘檔案（L1、LONG／RETEST24 adapter、PREREG v1.0／v1.1 DIFF、V1_19／V1_20 說明、engine、其餘測試）沿用 0acece21，未動。程式預設值全部不變。

## 逐項對應（ChatGPT v1.21 4 項＋#7235944722 補充）

| # | 要求 | 做法 | 回歸測試（新版 PASS／舊版 0acece21 FAIL） |
|---|---|---|---|
| 1 | impact 最終判定：任一 schema／證據不足原因（無效內嵌 cutoff、非 list 缺失事件、以及其他 UNDETERMINABLE 原因）優先於 `AFFECTED_PATH_MAY_CHANGE`；hit／cover 計數仍保留 | 判定改為：若有 `undet` → `UNDETERMINABLE`；elif 有 hit8／hitn／covered → `AFFECTED_PATH_MAY_CHANGE`；否則 `NOT_AFFECTED_BY_THESE_DELTAS`。衝突鍵仍記入 undet。既有「空持倉＋無效 cutoff／非 list」案例保留；各再加「持倉區間被乾淨 delta 打中」與「缺事件現可被 cover」分支，舊版必須因回 `AFFECTED` 而 FAIL | 既有 `test_invalid_embedded_cutoff_is_undeterminable`、`test_missing_funding_events_not_list_is_undeterminable` 的 held-interval-hit／miss-key-hit 分支（舊版 0acece21 在 held-hit 回 `AFFECTED_PATH_MAY_CHANGE`；新版 `UNDETERMINABLE` 且計數仍在）。非 list 的 miss-key 分支無法產生 cover（欄位不是 list），另附合法 list 的 `ok_cover` 對照仍為 `AFFECTED` |
| 2 | `combo_model_vs_live_shared_risk_diff` 一律寫明「模型在出場 bar 入帳已實現淨額，實盤在事件時點入帳」 | 常數 `BOOKING_TIMING_DIFF` 對所有參數組合都附加到 diff 清單（與日界／共同控制旗標無關的時點差） | `test_limitations_text_follows_parameters` 現在對 utc、taipei、主比較旗標組都要求含此句（舊版 0acece21 沒有這句而 FAIL） |
| 3 | 主比較標記欄位必須只代表控制旗標，不得叫 `is_v1_20_main_comparison`；核對六項旗標；文件與輸出須寫明「不代表策略／資料／成本已對齊」；並整理 `prereg_deviations` 依實際旗標列出所有偏離預註冊的項目（不再只依台北日界） | 新增 `main_comparison_control_flags_match`（布林）與 `main_comparison_control_flags_mismatches`（清單，元素為 `{flag, expected, this_run}`），以及 `main_comparison_control_flags_note`。六項：`--leg-daily-loss-day utc`、`--cross-leg-order rank_interleave`、`--leg-priority long_first`、`--global-max-slots 0`、`--global-daily-loss-u 0`、`--same-inst-policy off`。註記明寫：這只是控制旗標核對，**不代表**策略、資料或成本已對齊；實際候選、0.0005 滑價、多單 12 槽由 ChatGPT 原研究接線；本交付仍用舊 adapter 0.0003／24 槽，不得稱為同口徑跑。`list_prereg_deviations(args)` 對凍結 PREREG v1.0 六旗標逐項比對（utc／direction_block／long_first／12／600.0／block_any），列出所有偏離。程式預設不改 | `test_main_comparison_control_flags`（主比較組 match=true、mismatches=[]；預設組 match=false，偏離日界／槽／日損／同幣政策；逐一改單一旗標只出現該項）。`test_prereg_deviations_follow_actual_flags`（完整 v1.0 組 → []；只改台北日界 → 僅日界一項；主比較組 → `{cross_leg_order, global_max_slots, global_daily_loss_u, same_inst_policy}`，不含 utc 日界）。`test_main_comparison_parameter_set` 改為檢查 flags_match（舊版 KeyError／None 而 FAIL）。公開檔沒有 `is_v1_20_main_comparison` 字樣 |
| 4 | 文件：本交付仍用舊 adapter 0.0003／24 槽，不得稱為同口徑跑；完整月中位數、≥100 筆月數、零成交月由原研究依已存月表彙總 | 見本檔「本交付不是同口徑跑」與「月統計彙總（交原研究）」兩節；程式不新增彙總欄位、不改 adapter 預設 | — |

## ChatGPT 已定案的主比較控制旗標（#7235223075、#7235255702、#7235944722；程式預設不改）

主比較明確帶：

```
--leg-daily-loss-day utc --cross-leg-order rank_interleave --leg-priority long_first --global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off
```

這六項只是**控制旗標**核對（`main_comparison_control_flags_match`／`mismatches`）。它們**不代表**策略、資料或成本已對齊。實際候選映射、0.0005 滑價、多單 12 槽仍由 ChatGPT 原研究接線與隔離驗證。各腿原限制與共享保證金拒單仍在。共同 12 槽／600U／`block_any` 與台北日界只作另列研究情境，不混入主比較，也沒有授權重跑全部組合。程式預設仍是 taipei 日界與 12／600／block_any，**不得**忘記帶旗標。

`prereg_deviations` 現在依實際旗標列出相對凍結 PREREG v1.0 的**全部**偏離（不再只在台北日界時產生一筆）。因此主比較組（utc + 關閉另加控制 + rank_interleave）會列出 `cross_leg_order`、`global_max_slots`、`global_daily_loss_u`、`same_inst_policy` 四項偏離（日界 utc 與 `long_first` 與 v1.0 相同，不列入）。這是預註冊對照，與「主比較控制旗標是否相符」是兩件獨立的事。

## 本交付不是同口徑跑

本輪 adapter 現值維持滑價 0.0003、多單 `max_slots` 24，**沒有**改成 0.0005 或把多單映射到 12 槽。因此即使用上節六項控制旗標跑出 `main_comparison_control_flags_match: true`，也**不得**稱為與原研究同口徑（same-basis）的一次跑。候選映射、滑價對齊與隔離修正仍交 ChatGPT 原研究。

## 月統計彙總（交原研究）

v1.20 已在每個 arm 寫入 `monthly_combined`（多空合計完整最終平倉依出場 UTC 月、首次成交、方向貢獻、完整月 100–200 帶）。完整月中位數、落在或超過 100 筆的月數、以及零成交月，由 ChatGPT 原研究依已存月表自行彙總；本版不新增彙總欄位，也沒有重跑任何歷史月份。

## 測試清單與結果（全部純合成；未跑歷史回測、未抓市場資料）

| 測試 | 結果 |
|---|---|
| test_combo_l02_opt01_shared_synthetic.py（21 項）對新 runner | rc=0，`ALL_COMBO_L02_OPT01_SHARED_SYNTHETIC_TESTS_PASS` |
| 同上套在 0acece21 舊 runner | rc=1，5 項 FAIL（`test_limitations_text_follows_parameters` 缺出場 bar 入帳句；`test_main_comparison_parameter_set` 無 flags_match；`test_main_comparison_control_flags` KeyError；`test_prereg_deviations_follow_actual_flags` 只依台北日界列出；`test_real_builders_smoke_and_dry_check` 版本標籤仍為 v1.20），其餘 16 項 PASS |
| test_old_result_impact_scope_v1_19.py（10 項）對新工具 | rc=0，`ALL_IMPACT_SCOPE_V1_19_SYNTHETIC_TESTS_PASS` |
| 同上套在 0acece21 舊工具 | rc=1，2 項 FAIL（無效 cutoff 與非 list 的 held-interval-hit 分支仍回 `AFFECTED_PATH_MAY_CHANGE`），其餘 8 項（含 write_safety 與空持倉案例）PASS |
| test_old_result_impact_scope_v1_17／L1／LONG／RETEST24 測試（未改） | 全部 rc=0 PASS |
| offline_static_check.py、py_compile | rc=0 |

上述「舊版 FAIL／新版 PASS」證據只留本機，不進公開倉。

## 未決事項

- 日損日界、同順位排序、另加控制的主比較**控制旗標**已由 ChatGPT 定案，無待決；欄位命名依 #7235944722 只代表旗標，不代表策略／資料／成本已對齊。
- 仍由 ChatGPT 原研究處理：0.0005 滑價、候選映射、多單 12 槽、隔離修正、真正共用 50000/10x 的完整執行與 R2 獨立基準；以及依已存月表彙總完整月中位數、≥100 筆月數、零成交月。
- 程式預設仍為 taipei 日界與 12 槽／600U／block_any；若 ChatGPT 之後希望改預設以免漏帶旗標，需另行決定並列為偏離。
- 本交付不得稱為同口徑跑。

## 指令範本（只給 ChatGPT 原研究使用；群組不執行）

```
# 主比較控制旗標組（ChatGPT 定案；不代表策略／資料／成本已對齊）
python3 research/long_struct_01/code/run_combo_l02_opt01_shared_backtest.py --manifest <REPRO_MANIFEST_JSON> --retest24-script <RETEST24_PY> --shared-risk <SHARED_RISK_PY> --cache-dir <CACHE_V3_DIR> --funding-db <FUNDING_SQLITE> --input-manifest <EX_USDC_286_NPZ_MANIFEST_JSON> --funding-inventory <FUNDING_MONTH_INVENTORY_CSV> --leg-daily-loss-day utc --cross-leg-order rank_interleave --leg-priority long_first --global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off --out-dir <NEW_EMPTY_OUT_DIR>
# 另列情境（各用新的 out-dir）：加回 --global-max-slots 12 --global-daily-loss-u 600 --same-inst-policy block_any；或 --leg-daily-loss-day taipei
python3 research/long_struct_01/code/old_result_impact_scope_v1_19.py --details <OLD_DETAILS_JSON> --cutoff-utc <THAT_RUN_END_UTC> --delta <DELTA_CSV_GZ> --out <NEW_ASSESSMENT_JSON>
```

紅線：不公開私人明細（combo_local_details.json 只留本機）、不含帳密／config.json／本機路徑；兩個 PR 維持 Draft，不合併、不部署、不下單；`live_approved: false`。
