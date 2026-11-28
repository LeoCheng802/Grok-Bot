# BACKTEST-READINESS-01 v1.17｜策略組交付說明（多單 02＋OPT01 共用本金組合、R2 對照、L1 修正、舊結果影響盤點）

- 角色：策略組（Grok）。只做離線靜態開發與合成測試；沒有跑任何歷史或績效回測，沒有呼叫實盤或模擬盤 API。
- 依據：Issue #1 #7230906219（v1.17）、#7230504858／#7230544291／#7230640043（v1.16）、#7230355480（v1.15）、#7230243906（v1.14）、#7207172638（多空分工與共同本金）。
- 基底：PR #7 `3a2ba82caec450d9b0bc854de0630618d6431e94`。兩個 adapter（`run_long_struct_bounded_backtest.py`、`run_retest24_bounded_backtest.py`）與引擎檔都沒有改動。
- 狀態：`FIB-4H-LONG-V3` 維持 `NO-GO`，`live_approved: false`，PR 維持 draft。

## 1. 組合 runner：`code/run_combo_l02_opt01_shared_backtest.py`

- 兩條腿：腿 0 是 `LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT`（多單 02），腿 1 是 `RETEST24_OPT_01_BEARISH_CLOSE_POS`（OPT01）。訊號直接呼叫兩個 adapter 原本的 `build_cands_*`，規則和預設出場、倉位參數都沒有改。
- 真正共用一個帳戶：兩條腿放進同一次引擎呼叫，所以只有一份已實現權益、一份浮動權益和回撤、一個保證金池（掛單和持倉兩腿合計）、一次強平檢查。不是兩份 50,000 相加。
- 公平成本：maker 0.02%、taker 0.05%、滑價 0.03%、MMR 1%、槓桿上限 10x。兩腿成本欄位不一致時 runner 直接拒跑。
- 組合層規則（疊在各腿原本的凍結規則之上，預設值取自已登記的 `shared_risk.py`）：
  - 多空合計名額 12（持倉加未成交進場單）；
  - 台北日（UTC+8）已實現淨損益達 −600U 後，兩腿都停止新增；
  - 同幣跨腿：預設 `block_any`，一個幣同時只能由一條腿持有或掛單；`allow_opposite` 只作敏感度；
  - 同一根 4H 兩腿都出訊號：依 `--leg-priority`（預設 `long_first`）決定先後，之後各腿沿用自己原本的排序鍵；
  - 不可計算視窗：盤點表子原因 `rest_51001_instrument_not_listed`（RVN 2026-11）整個 CST 月不准新進場，跨進視窗的部位標「不可計算」；也可以用 `--uncomputable-windows` 另外指定。
- 引擎接法：runner 在記憶體裡複製已登記的 B6 引擎原始碼，用錨點文字替換加上組合層檢查；錨點對不上就拒跑。已登記的引擎檔不改。結果裡會記錄修補後原始碼的 SHA。
- v1.15 資料規則：
  - 缺的資金費維持未知、不入帳，不補零、不插值、不刪幣；
  - 缺的 8H 事件全部列在本機明細，不 abort；
  - 盤點表只把 `complete == "true"` 當完整，`false`、留空或其他值都不算；
  - 結果狀態只會是 `PRELIMINARY_INCOMPLETE_DATA` 或 `PRELIMINARY_BATCH_SCOPE`，不會是 PASS；有未知資金費時，結果標成「條件情境，不是真實淨績效」。
- 輸出：`--out-dir` 必須是新的隔離目錄（不存在或是空的），否則在任何寫入前拒跑。`combo_result.json` 只在完整跑完後出現；失敗時不留 result，也不留 `.tmp`。本機明細 `combo_local_details.json` 不公開。

## 2. R2 對照

- 採用的定義：R2 是 RETEST24 同一訊號的 Q29 倉位規格（每筆 100U、日損 400U），對照 R1（Q28，每筆 150U、日損 600U）。R1／R2 是倉位規格，不是兩套訊號。
- 上傳物：組合 runner 預設跑 4 個 arm（`R1_150U` 和 `R2_100U` 各配 `cross_1tick`、`delay1bar`），R2 兩個 arm 就是對照。規格寫在 `COMBO_L02_OPT01_SHARED_PREREG_v1.0.json`。
- 有歧義：v1.17 只寫「上傳R2對照」。如果指的是空單單獨的 R2，用既有的 `run_retest24_bounded_backtest.py --candidate RETEST24_OPT_01_BEARISH_CLOSE_POS --scenarios "R2_100U|cross_1tick,R2_100U|delay1bar"` 就能產生，不需要新程式。實際歷史結果由 ChatGPT 原研究任務跑完再上傳。

## 3. L1 runner 修正：`code/run_l1_bounded_backtest.py`

- 版本標籤：改用單一常數 `RUNNER_VERSION = "v1.17"`。原本 scope、result、abort 寫 `v1.0`，本機明細寫 `v1.9`。
- 新的隔離輸出目錄：`--out-dir` 已有任何檔案（例如舊的 result 或 abort）時，在任何寫入、複製、載入前拒跑，舊證據保持原樣。這個檢查放在既有的路徑互斥檢查之後，所以原本的碰撞測試訊息不變。
- 測試 `code/test_l1_bounded_main_synthetic.py` 的更新：
  - 案例 2 改成用新目錄；
  - 新增案例 4：重用目錄被拒，舊檔逐位元組不變；
  - 新增案例 5：所有輸出檔的版本標籤一致。
- 舊版重現失敗、新版通過：
  - 新測試配舊 runner：案例 4、5 FAIL，舊版標籤是 `v1.0`／`v1.0`／`v1.9`；
  - 新測試配新 runner：全部 PASS。
- 刻意改變的行為：v1.13 原測試的案例 2 會在重用目錄裡放一個舊 PASS 檔再跑，新 runner 會拒跑，所以舊測試配新 runner 時只有案例 2 失敗。案例 1、3 仍然通過。

## 4. 舊結果是否需要更新：只盤點，不重跑

- 工具：`code/old_result_impact_scope_v1_17.py`，純靜態，不重播。輸入是舊結果的本機明細 JSON，加上那次執行沒有用到的資金費 delta CSV。
- 判定規則和引擎一致：資金費在 `ets < ts_snapped <= xts` 時入帳。
- 判定結果分三種：
  - `AFFECTED_PATH_MAY_CHANGE`：新資料落在實際持倉期間內，或補上舊的 miss_8h 事件。權益、保證金、日損、強平路徑都可能改變，這個 arm 需要更新；
  - `NOT_AFFECTED_BY_THESE_DELTAS`：沒有交集，不重跑；
  - `UNDETERMINABLE`：沒有逐筆持倉明細，例如 L1 明細沒有列期末未平倉。這種只列出來，不用猜的。
- 本批 delta 的靜態範圍（PR #8 `7852b42f` 公開檔，已核 SHA）：
  - b2_r1：198,354 列（SHA `ac3890c5…2e86`），在既定期間內 198,351 列，其中 8H 120,993、非 8H 77,358，涉及 272 個標的，2023 至 2026 年都有；
  - b3a：918 列（SHA `0950a0d2…baab`），全部在 2026 年，涉及 23 個標的。
- 結論：凡是在這些資料補進之前跑的舊結果，都只能先列為「可能受影響」。要用上面的工具拿各 arm 的本機明細逐一判定，只更新判定為受影響的 arm，不機械重跑 5 版 10 情境或原 L1。v1.13 以前沒有逐筆明細的結果標成 `UNDETERMINABLE`，等原研究任務決定要不要補。

## 5. 合成測試指令

```
python3 research/long_struct_01/code/test_combo_l02_opt01_shared_synthetic.py      # ALL_COMBO_L02_OPT01_SHARED_SYNTHETIC_TESTS_PASS
python3 research/long_struct_01/code/test_old_result_impact_scope_v1_17.py         # ALL_IMPACT_SCOPE_SYNTHETIC_TESTS_PASS
python3 research/long_struct_01/code/test_l1_bounded_main_synthetic.py             # ALL_L1_MAIN_SYNTHETIC_TESTS_PASS
python3 research/long_struct_01/code/test_long_struct_bounded_synthetic.py         # ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS（未改）
python3 research/long_struct_01/code/test_retest24_bounded_synthetic.py            # ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS（未改）
L1_RUNNER_PATH=<舊版 run_l1_bounded_backtest.py> python3 research/long_struct_01/code/test_l1_bounded_main_synthetic.py   # 預期案例 4、5 FAIL
COMBO_RUNNER_PATH=<突變版> python3 research/long_struct_01/code/test_combo_l02_opt01_shared_synthetic.py                 # 突變檢查用
```

組合測試用的是真的已登記引擎檔，只把候選產生器換成固定的 stub。涵蓋：
- 共用保證金池：第二條腿因共用池不足被拒，單獨跑時可以掛；
- 多空合計名額；
- 台北日日損擋住另一條腿；
- 同幣跨腿衝突（同根、持有中、優先順序、`allow_opposite`）；
- 缺費率標註（不補零、不 abort、列出全部缺口、只有 `complete==true` 算完整）；
- 不可計算視窗；
- 輸出互斥（新目錄、失敗不留 result、拒絕 symlink）；
- 真 adapter 冒煙測試和 dry-check。

突變檢查都會讓對應測試失敗：
- 拿掉組合閘門：4 項 FAIL；
- 拿掉新目錄檢查：1 項 FAIL；
- 改成各腿各自算保證金：共用保證金測試 FAIL。

## 6. 缺口與待確認

- R2 對照的確切範圍、同根雙腿的優先順序、同幣跨腿規則（`shared_risk` 帳本和開單審核的口徑不一致），都還沒有官方定義。這些已改成參數並標註，預設採最保守的解讀。
- 多單 02 原本的 24 槽和共用的 12 槽並存，以 12 槽為硬上限。如果 77 另有指定，再改參數。
- RVN 的確切下架時間、4 個 404 月份的原因、slice2／3 共 3,921 個月份的完整性，都還未知。
- 所有測試 PASS 都只是團隊合成自述，不是 ChatGPT 的 runtime 認證，也不是歷史或績效通過。
