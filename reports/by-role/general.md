# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 02:57:49
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7226049299

<!-- comment_id: 7226049299 -->

【2026-11-28 02:58 台北時間（UTC+8）】
[復盤] `BACKTEST-READINESS-01 v1.1`｜PR #6 A 段有界離線入口獨立驗收、v1.0 更正前作業留存稽核與阻礙彙整（對應 #7225850828，併參 #7225973610）

- **角色**：復盤（獨立覆核與彙整）
- **研究編號與版本**：`BACKTEST-READINESS-01 v1.1`｜[LeoCheng802/Grok-Bot PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6)（分支 `research/offline-packaging-hardening-draft`，新固定 head `da65fe4dbdd549aa973e4e3f2c69447b53dcb64a`）
- **時間與時區**：2026-11-28 02:58 UTC+8
- **獨立覆核起迄（UTC）**：`2026-11-27T18:56:40Z` → `2026-11-27T18:57:30Z`
- **治理邊界**：PR #6 實測 `state = open`、`draft = true`、`merged = false`、`commits = 7`、`changed_files = 12`（`+3822 / -218`），維持 Draft、不合併、不部署、`main` 未動。本端與執行／策略組已依 v1.1 全面停止新增回測／行情掃描／歷史計數作業；**所有基準與候選皆維持「尚未由 ChatGPT 獨立回測」，`FIB-4H-LONG-V3` 維持 `NO-GO`，`LONG-STRUCT-01 v1.2` 與 `RETEST24-R1-R2 v1.5` 維持凍結，`LONG-STRUCT-02` 不實作**。

### 一、PR #6 新增 2 檔 live raw 獨立驗收（HTTP 200、SHA 吻合、零外洩）
接續 `3f67bd87fe5db2ec64d97b543fe780fa2f505f6f` 僅新增 2 檔，原 `run_l1_tp_study.py` 與先前 10 檔零異動：
1. [run_l1_bounded_backtest.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/da65fe4dbdd549aa973e4e3f2c69447b53dcb64a/research/long_struct_01/code/run_l1_bounded_backtest.py)：`37,538` B，SHA-256 `26757d866146622176803c05948ed27007b87f9503aad3f4ef89934a74ddccbf`（AST 通過、`0` `assert`、頂層 18 項全為標準庫與 `numpy`，零策略／`shared_risk`／引擎 import，零路徑或憑證外洩）。提供有界參數（`--symbols` / `--start-utc` / `--end-utc` / `--scenarios` 限已凍結 TP2.5% 兩情境 / `--dry-check`），全程外層禁網、唯讀輸入、遇缺費硬拒絕（`EXIT=2`）。
2. [BACKTEST_READINESS_01_REPORT.md](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/da65fe4dbdd549aa973e4e3f2c69447b53dcb64a/research/long_struct_01/BACKTEST_READINESS_01_REPORT.md)（註：正確 URL 對應 head `da65fe4dbdd549aa973e4e3f2c69447b53dcb64a`）：`8,961` B，SHA-256 `7bc66df46e127c0f168ff86a1eca97e046638024511543b5a362a4ac4ea9da5a`（零路徑或憑證外洩）。**口徑註記**：該報告於接獲 v1.1 更正前即送出提交，標題與授權欄仍標 `v1.0`／`#7225707059`；實際以本則與 `#7225850828`（v1.1）為準，報告中已執行之 B/C 紀錄僅作更正前留存稽核，**絕不替代 ChatGPT 獨立回測**。

### 二、v1.1 更正到達前已結束之既有作業留存摘要（不刪、不續跑、不稱本端驗證完成）
- **Job 1（v1.0 B 段接線小測，UTC `2026-11-27T18:50:05.462Z` → `18:50:05.912Z`）**：既有最小 fixture 正常跑 `EXIT=0`（`0` diffs、`transport_hits=[]`、`inputs_unchanged=True`，輸出 SHA `8c298135…`）；缺費負向測試 `EXIT=2`（無成功報表，診斷 SHA `a4775396…`）。
- **Job 2（v1.0 C 段全期基準跑，UTC `2026-11-27T18:50:19.041Z` → `18:51:52.493Z`）**：`EX_USDC_286` 全窗 `2023-01-01T00:00Z..2026-11-26T12:00Z` 僅 TP2.5% 兩組，於既有 `funding_archive_l1_isolated.sqlite`（`23ebdab5…`）觸發缺費硬拒絕 **`ABORTED_MISSING_FUNDING`（`EXIT=2`）**，未寫成功報表、未補零／插值／縮窗／連線（`transport_hits=[]`、`inputs_unchanged=True`）：
  - `TP_2.5pct|cross_1tick`：缺 `158` 筆 8H 費率（55 標的，`2023-09-29T16:00Z..2026-10-18T08:00Z`；已匹配 `6,415` 筆 8H + `1,228` 筆非 8H）。
  - `TP_2.5pct|delay1bar`：缺 `128` 筆 8H 費率（54 標的，`2023-01-30T16:00Z..2026-08-14T16:00Z`；已匹配 `6,171` 筆 8H + `961` 筆非 8H）。
  - 完整缺口事件明細留存於私有範圍（SHA `54037c6f1c44a2db9b5a4e032aafbfd006366eeaba461dfd81ed6725385c6b1e`），未公開。

### 三、具體阻礙與下一步待辦
1. **既有資金費庫全窗缺口（待 ChatGPT 裁示）**：在不新抓 OKX 且維持缺費硬拒絕前提下，請裁示 ChatGPT 獨立回測基準入口時對上述 158／128 筆 8H 缺口的處置方向。
2. **PR #6 分支待補齊項目（不依賴阻礙、可獨立進行）**：
   - `@執行` 併案對齊 `BACKTEST_READINESS_01_REPORT.md` 標頭至 `v1.1`（標明 Job 1/2 為更正前留存），並更新 PR #6 分支上的 `CANDIDATES.md` / `CANDIDATES.json`（分列「腳本已交付、封裝驗收、真實引擎整合、完整回測」狀態與固定分支檔案連結，不把 `main` 舊 SHA 寫成新版）。
   - `@策略組` 對齊 `run_l1_bounded_backtest.py` 介面準備 `RETEST24-R1-R2 v1.5` 凍結基準離線 adapter 與單一假說優化提案（見 `#7225973610`）。
3. **`LONG-STRUCT-02` 去重硬阻礙**：公開庫與工作區皆無 `B24H` 與 `A60＋量縮` 可讀規則或腳本檔，未補齊同版去重前維持不實作。
