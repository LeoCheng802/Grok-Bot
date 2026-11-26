# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-27 04:46:16
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7203055265

<!-- comment_id: 7203055265 -->

[復盤] RETEST24-RELEASE-AUDIT-01 v1.2｜v1.5-auditfix 單一候選完整離線覆核回報（維持 NO-GO）

- **角色**：復盤（彙整策略組、執行、開單審核、風險管理獨立離線覆核結果）
- **研究編號／版本**：`RETEST24-RELEASE-AUDIT-01 v1.2`（對應交接留言 `#7202073891`，並同步確認已接收 `#7202590257`）
- **時間與時區**：`2026-11-27 04:46 CST (Asia/Taipei, UTC+8)` / `2026-11-26T20:46Z`
- **資料截止**：全案為離線 mock 隔離驗證（無連線交易所、未觸及實盤／模擬盤帳戶與既有原檔）
- **放行判定**：**離線審核全數 PASS；整體維持全面 NO-GO（不授權 `--demo` 或 `--live`，非經 77 直接核准絕不啟動任何實盤或模擬盤執行）**

---

### 1. 單一候選雜湊 → 案例 → 覆核角色 → 輸出雜湊對照表

- **單一候選檔**：`RETEST24_R1_R2_Switchable_v1_5_auditfix.py`
- **單一候選 SHA-256**：`949a86f5a532dacfcf7f15b4a4b9ecbc0d8234662795c541a23469a94783c15c`
- **附隨交付雜湊**：`test_retest24_release_audit.py`（`2d5a79a312aa3fc310a022d65202eb63b5e643778a24d5b03b93b97108b1029c`）、`RELEASE_CHECKLIST.md`（`0b38b15f5230b95ac0d69f896c7f686e87029f01d72d029802794fe3cb6ed0db`）
- **原檔未變核驗**：`v1.0`（`7f87a1f0…1a78`）～`v1.4`（`95835e02…613a`）、`test_g4_ownership_01.py`（`738b91c8…1770`）、`test_unknown_recovery_01.py`（`58574636…8aa79`）均未改動。

| 候選雜湊（前 8 碼） | 驗證案例 | 覆核角色 | 執行時間（UTC） | 結果 | 輸出證據與完整 SHA-256 |
|---|---|---|---|---|---|
| `949a86f5`（v1.5） | 24 項離線回歸套件（含 `G-4-OWNERSHIP-01`、`UNKNOWN-RECOVERY-01`、8 訊號函數 1,500 組 K 線零差異） | 策略組 | `2026-11-26T20:20:59.564Z` ～ `2026-11-26T20:20:59.682Z` | **24/24 PASS** | `audit_v1_5_evidence.json`：`a79deb99f6ef35ea9a1cf3efc2c50ff1eb83f03238f059bff0b9e1c24889d6ea` |
| `949a86f5`（v1.5） | `test_retest24_release_audit.py`（24/24）＋獨立 `UNKNOWN-RECOVERY-01` 沙盒實測＋逐行 diff | 執行 | `2026-11-26T20:23:38.667054Z` ～ `2026-11-26T20:23:38.772191Z` | **PASS**（24/24；槽位 `12/12`、送單 `1`） | `unknown_recovery_01_v15_evidence.json`：`b76b66ed7ac2fe20c035ed161448389765ae30aa0ce694dac33798e4a2c862da`；`unknown_recovery_01_v15_output.txt`：`aeb76a0d1dd720e2fed99454fd1ee62b4a8bf64ec27863b98af7046675b3fef7` |
| `949a86f5`（v1.5） | `test_retest24_release_audit.py`（24/24）＋獨立 `UNKNOWN-RECOVERY-01` 隔離 mock＋解除界線 diff | 開單審核 | `2026-11-26T20:24:34.809785Z` ～ `2026-11-26T20:24:34.815132Z` | **PASS**（24/24；槽位 `12/12`、歸屬 `True`） | `unknown_recovery_01_v1_5_audit.json`：`a82ff5e0be5510b684d1b64bb14d143030294749edb4ac94ef61caeddbc38eea` |
| `949a86f5`（v1.5） | 獨立 `UNKNOWN-RECOVERY-01` 與解除界線 9 項斷言＋人工解除留痕驗證 | 風險管理 | `2026-11-26T20:25:49.923714Z` ～ `2026-11-26T20:25:50.042011Z` | **PASS**（9/9 斷言全過） | `risk_v1_5_evidence.json`：`529296953dfe092fd05153d6ac2ea50b1a40aeb775d6db061a67f4df5e78fca6` |

*(註：上表僅計單一候選 `v1.5-auditfix` 結果，不跨檔加總歷史版本測試數。)*

---

### 2. `UNKNOWN-RECOVERY-01` 舊版失敗 → 新版通過證據摘要

- **舊版 `v1.4-auditfix`（`95835e02…613a`）FAIL（BLOCKER）**：
  - **觸發機制**：原 `NOT_FOUND_GRACE_MS = 60_000` 導致 `UNKNOWN_SUBMIT` 在 `+65s` 查單暫遇 `51603` 時被自動改寫為 `RESOLVED_NOT_PLACED` 並釋放槽位（`active_slots` 誤由 `12 → 11`），競爭程序送出新單占走第 12 槽；隨後原單與部分成交於 T4 恢復可見，總槽位突破 `13/12`（且原單部分成交倉位未升格入帳、`family_positions = False`）。
  - **舊版失敗證據雜湊**：執行 `unknown_recovery_01_evidence.json`（`e8b84f6f937bf2907de3e679f5748e1ac32a2b7ebc8b95b585a969447d109d20`）；開單審核 `unknown_recovery_01_v1_4_audit.json`（`ed917be61db34aac8012ed1d2980215c6247180907448342c6ea001fc8a6676f`）。
- **新版 `v1.5-auditfix`（`949a86f5…c15c`）PASS**：
  - **事件順序驗證（T0 → T1 +30s → T2/T3 +65s → T4 +75s/+80s）**：+65s（甚至 10 分鐘後）遇 `51603` 均維持 `UNKNOWN_SUBMIT` 與 `HALT_UNKNOWN_INTENT`（`halt = True`、`active_slots = 12`、競爭程序下單數 `0`）；T4 原單與部分成交恢復可見時，`reconcile_intents()` 正確升格為 `CONFIRMED` 入帳、`family_positions = True`，原單與部分成交合併計 1 槽、總槽位維持 `12/12`、總送單數 `1`。
  - **兩類解除條件界線已落實**：
    1. **已證明未受理（僅此兩類可自動釋放）**：(a) 送單同步明確拒單（`code in 0/1/2` 且單筆 `sCode` 非空非 `"0"` 且無 `ordId` → `RESOLVED_REJECTED`）；(b) 同 `clOrdId` 查得終態 `canceled`/`mmp_canceled` 且 `accFillSz == 0`（→ `RESOLVED_CANCELED`）。
    2. **可能已受理但暫不可見（嚴禁逾時自動釋放）**：送單逾時／斷線／5xx、頂層錯誤無單筆 `sCode`、`sCode != "0"` 但帶回 `ordId`、任何時間之 `51603`／5xx／限流、或查單回傳 `clOrdId` 不符，一律鎖槽停開（不重送、不撤單、不平倉），僅能等查詢確認終態，或經人工核對後透過 `--resolve-unknown-intent <clOrdId> --resolve-reason "<audit note>"`（持單例鎖、必填原因、先查單確認無在途／成交否則拒絕並轉 `CONFIRMED`）寫入 `state.intent_audit` 留痕解除。

---

### 3. 已知限制與未閉合政策差異（維持 NO-GO，待 77 核定）

1. **三項離線／回測差異（已明列於 `RELEASE_CHECKLIST.md`）**：
   - 未平倉當日資金費尚未計入日內損益；
   - 原回測 `loss_streak_pause` 機制未納入現行腳本；
   - 日虧達標撤回自家未成交進場單 vs 原回測僅停新增屬不同執行政策（另換日口徑採台北 `00:00` vs 回測 `UTC 00:00`）。
2. **其他未授權項目**：`B4` 疊加曝險政策與任何 `--demo`／`--live` 啟動權限，須待 77 直接書面核定後方可推進；外部同幣混倉或失去帳本且無法交叉還原時，一律標記未知並停開新倉，不認領整倉亦不操作外部單。

---

### 4. 下一步
- **`RETEST24-RELEASE-AUDIT-01`**：已完成 `v1.5-auditfix` 全組離線覆核與單一候選對照表交付，維持 **NO-GO** 等待 GPT 檢視與 77 指示。
- **`R1R2-VS-FIB-OPT-01 v1.2`（`#7202590257`）**：已於群組轉達並請策略組立即啟動第一批離線研究（凍結 `Q28/Q29` `EMA55` 基準 vs 同一結構破低訊號移除 `EMA55`，同步核實 `Q28/Q29` 淨損益與權益增量差額 `84.11／56.07 USDT`），首份實質結果產出後隨即附工作 ID、UTC 時間與輸出雜湊回報本串。
