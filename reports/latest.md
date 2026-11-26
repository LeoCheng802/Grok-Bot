# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-27 03:38:05
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7201800183

<!-- comment_id: 7201800183 -->

[復盤] RETEST24-RELEASE-AUDIT-01 v1.0（補充納入開單審核獨立覆核）

- **角色**：復盤（補充彙整開單審核獨立離線覆核；接續前則 `[復盤]` 留言 `7201770935`）
- **研究／事件編號**：`RETEST24-RELEASE-AUDIT-01`
- **版本**：`v1.0`（補充更新，不取代 `7201770935` 之策略組／復盤證據）
- **對應 ChatGPT 留言 ID**：`7200864466`
- **狀態**：階段進行中（**維持 NO-GO，不得標示可直接實盤**；開單審核已完成原版 `v1.0` 獨立覆核，待其針對 `v1.1-auditfix` 執行二次獨立複驗，並待執行與風險管理簽核）
- **時間與時區**：開單審核覆核 `2026-11-26 19:34 UTC`（台北 `2026-11-27 03:34 CST`）；復盤彙整 `2026-11-26 19:38 UTC`（台北 `2026-11-27 03:38 CST`，UTC+8）
- **資料截止**：純離線靜態＋模擬端點測試（零實盤連線、零委託／撤單／平倉；不變更任何實盤風控）

### 開單審核獨立覆核結果（標的：`RETEST24_R1_R2_Switchable.py` 原版 `v1.0`）
- **結論**：**不放行**；7 項獨立案例於原版 `v1.0` 全部重現缺陷（`7/7`）：
  1. `AUDIT-01-CORRUPT-STATE`：狀態檔 JSON 損毀時 `load_state()` 靜默吞錯回傳空狀態，未進入 fail-closed 停開新單；另送單成功未先落盤意圖。
  2. `AUDIT-02-CANCEL-SCODE-IGNORED`：撤單回傳頂層 `code="0"` 但 `data[0].sCode="51400"` 時未驗逐筆 `sCode`，誤計撤單成功。
  3. `AUDIT-03-PARTIAL-FILL-SLOT-LEAK`：部分成交持倉仍在且餘單撤銷成功時，以 `active_slots - canceled` 相減誤釋放仍被持倉占用的 1 槽。
  4. `AUDIT-04-POSMODE-UNKNOWN-DEFAULT`：`account/config` 逾時時 `detect_pos_mode()` 靜默預設 `"long_short_mode"`；下單逾時當失敗跳過，未以 `clOrdId` 查回或停開新單。
  5. `AUDIT-05-PROFILE-SWITCH-DROP-TRACKING`：`R1→R2` 切換後舊 profile 掛單雖擋同幣但漏計 `active_slots`／逾期撤單，且遭移出追蹤清單。
  6. `AUDIT-06-NO-PAGINATION`：`orders-pending`、`orders-algo-pending`（未含 `move_order_stop`）與 `positions-history` 滿頁 100 筆皆未翻頁。
  7. `AUDIT-07-STATIC-GUARDS-MISSING`：原版缺進程互斥鎖、缺逾時原單查回（`GET /api/v5/trade/order`）、缺成交後保護單生效與張數覆蓋回查。

### 證據與檔案雜湊（SHA-256，去識別）
- 原版（保留未動）`RETEST24_R1_R2_Switchable.py`：`7f87a1f00eb17725cec13eb472045ba2467d9e65cc3c5fa421a3a651acf31a78`
- 開單審核離線報告 `order_audit_report.json`：`617f5746bec68b6666e89fa4da7a4ebb56dfd7b40603d6947ed54f257f78e153`
- 開單審核測試腳本 `run_audit_checks.py`：`0305a66a28e1038028984afacbbd184b7aa5977e072e3e886bdc1bd2cb479d9e`
- 既有隔離修正候選 `RETEST24_R1_R2_Switchable_v1_1_auditfix.py`：`e6e112cd9c4183f31c62678080aa60a36be25ad5b634efb6ecbfa24a802f6484`

### 缺口與下一步
- **新增確認缺口**：快速靜態核對 `v1.1-auditfix` 已含進程鎖、`sCode` 檢查、`GET /api/v5/trade/order` 查回與保護單覆蓋檢查，但條件單查詢尚未納入 `move_order_stop` 類型。
- **下一步**：已通知開單審核直接針對 `v1.1-auditfix`（`e6e112cd…`）重跑同套 7 項案例做二次獨立複驗，並彙整執行與風險管理覆核意見；全角色簽核前維持 **NO-GO**。
