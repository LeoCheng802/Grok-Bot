# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 03:29:40
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7226582272

<!-- comment_id: 7226582272 -->

【2026-11-28 03:29 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.3｜空單 `load_funding_db` 修正、可比較回測接線與多單三檔合併備妥（本機自述待落地；工具攔截回報）

- **角色**：策略組
- **研究／事件編號**：`BACKTEST-READINESS-01`
- **版本**：`v1.3`（對應 `#7226371856` 與 `#7226404293`；不取代既已釘選之 PR #7 head `86ba35af90847af2e88e422e020c9a6375c472dd`，待新固定 commit 落地後更新）
- **時間與時區**：回覆 `2026-11-28 03:29 UTC+8`；本輪靜態修改與純合成回歸執行起迄（UTC）`2026-11-27T19:25:05Z` → `2026-11-27T19:29:03Z`
- **資料截止**：本輪零真實行情讀取、零歷史回測執行；所有驗證均採 100% 合成記憶體／暫存 SQLite／暫存 NPZ fixture。

### 一、已完成事項（本機自述，尚未推上遠端，不列為已驗交付）
1. **空單 `run_retest24_bounded_backtest.py` v1.3 修正與接線補齊**（`47,818` B，SHA-256 `70b338436585c9d4093d481c68896abf2cda5e01447dec3c23ac147681e85b8b`，`py_compile` PASS、零 `assert`、零外洩）：
   - **`load_funding_db` 介面修正（對應 `#7226404293`）**：改為 `SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive`，比照已釘選 FIB loader 回傳 `fmaps[inst][ts_snapped] = float(rate)` 與 `ov_raw[inst][ts_snapped] = int(ts_raw)`（`dict` 形狀，支援 Q38 `.get(t30, t30)`，保留原始結算時間不以對齊時間取代）。
   - **歷史模型與交付腳本差異明列（對應 `#7226371856` §3.1）**：內建 `HISTORICAL_MODEL_VS_DELIVERED_SCRIPT_DIFF` 輸出於 `--dry-check`、scope 與報告，明列 `slip_mkt`（`0.0003` vs 交付版 `0.0005`）、EMA55 計算窗口（全快取 vs 最多 600 已收棒）、預設母體排除（僅排 `USDC-USDT-SWAP` vs `EXCLUDED_BASES`）及未覆蓋之實盤狀態機，並附純訊號映射檢核輔助函式 `inspect_signal_mapping_sample`；明確聲明雜湊核對不代表完整 v1.5 腳本／`shared_risk` 等效執行。
   - **逐檔 NPZ 綁定與前後雜湊驗證（對應 `#7226371856` §3.2）**：新增選用 `--input-manifest` 及 `cache_manifest` 逐檔 `sha256`/`size_bytes` 檢核，於載入模組與 `np.load` 前將所有實際 NPZ 路徑納入 `fixed_inputs` 並通過輸出互斥檢查，跑完覆核前後雜湊一致；未列管、缺檔、空陣列或雜湊不符立即中止，不自動補齊換樣本。
   - **離線本機完整明細輸出（對應 `#7226371856` §3.3）**：新增 `by_year_month` 年月分項摘要，並於離線本機另寫 `retest24_bounded_local_details.json`（標註禁止自動推上公開庫），保留**完整不截斷** `missing_funding_events_all`、唯一首次成交識別／時間、完整平倉明細與費用／資金費、平倉權益序列與固定輸入雜湊；明記 158／128 與 50 筆對帳僅為有限範圍線索。
2. **純合成回歸測試 `test_retest24_bounded_synthetic.py`**（`8,104` B，SHA-256 `7188f01ce8f4fbd54c0ed20ae9225c107563843b2b71c373cc09d91bf7e977ad`，`ALL_RETEST24_V1_3_SYNTHETIC_TESTS_PASS`）：
   - 重現舊版 `set` 形狀在 Q38 `.get(t30, t30)` 觸發 `AttributeError`；
   - 以非真實行情暫存 SQLite fixture（`ts_raw = 1700006400123 > ts_snapped = 1700006400000`）驗證 `ov_raw` 保留原始 `ts_raw`、費率以 `ts_snapped` 查詢正確、未命中時回退 `t30`；
   - 驗證 NPZ 逐檔 hash/size 檢核、竄改阻斷、輸出與 NPZ 路徑重疊阻斷、以及 30 筆（>25）`miss_8h` 不截斷輸出與差異中繼資料。
3. **多單限價三檔已併入同一待推批次**（`load_funding_db` 原已採 `inst -> ts_snapped -> ts_raw` 字典形狀，零 `assert`、零外洩）：
   - `research/long_struct_01/code/run_long_struct_bounded_backtest.py`（`41,155` B，SHA-256 `4653b8664102f87d39ded2b2b8edfcbd71a9c558915d0c7a8c916e8902f5ec18`）
   - `research/long_struct_01/code/test_long_struct_bounded_synthetic.py`（`5,960` B，SHA-256 `02d9e71c67c671a0f6257527b172396ba6515dd949eeb1d96630136e9f0145b9`）
   - `research/long_struct_01/V1_2_AUTONOMOUS_DELIVERY_NOTES.md`（`5,019` B，SHA-256 `f70fb02983d7ce6a090bf13cb12ed46c20a89453a3ca07df35a9522da32d3f7d`）

### 二、實際工具攔截與解除條件（澄清：非缺 77 研究授權）
- **攔截動作**：於群組對話（`77｜OKX 交易台`）觸發推送至 PR #7 分支 `research/retest24-bounded-adapter-and-opt01-draft`。
- **實際錯誤**：
  1. GitHub 連接器（`cursor-github`）未提供寫檔／推送工具（僅支援讀取、留言、開／改 PR 與建分支）。
  2. 透過 Cloud Agent 推送時，系統安全審查回傳：`This action needs Auto-review approval, which isn't available in this conversation. Run it from a direct chat with the assistant.`
- **所需解除條件**：不繞過系統限制；須由策略組於與 77 的 **1:1 私訊對話**發起 Cloud Agent 推送，即可一次將上述 5 檔以新固定 commit 推上 Open Draft PR #7（不合併、不部署、`main` 不動）。

### 三、下一步
1. 將於 1:1 私訊通知 77 觸發該次 Cloud Agent 推送，將 5 檔一次落地至 PR #7 分支 `research/retest24-bounded-adapter-and-opt01-draft`（父提交 `86ba35af90847af2e88e422e020c9a6375c472dd`）。
2. 落地後立即以 live raw HTTP 200 與 SHA-256 覆核新固定 commit，再正式上報 `@復盤` 與 ChatGPT 供獨立回測與驗證；本端維持零歷史回測、零實盤／模擬盤下單。
