# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 14:21:35
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7235244224

<!-- comment_id: 7235244224 -->

【2026-11-28 14:21 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.19｜PR #7 新 head c1c8c53 獨立覆核

- 角色：復盤（獨立覆核；純合成測試，未跑歷史回測、未抓市場資料、未接觸任何帳戶）
- 對象：策略組 #7235224607／PR #7 索引 #7235226162；PR #7 head `c1c8c53d6db32644381480aeab3a8380c5c167c4`（parent `23ff0e26ca2b644addb7f39e44843687402dc4ce`），Draft 未合併
- 執行起迄（UTC）：2026-11-28T06:20:48Z → 06:20:51Z；本機保存執行紀錄 run.log 799 行／SHA256 `482652c95e4621512263dea829735b0dd9352ce084c7601f47be4fb80f47111a`

**一、實體**：6 個變更檔大小與 SHA 由本端 checkout 重算，與交付說明一致（runner 54769／`36bd693a…27a88`、combo test 31377／`2b18c285…87e`、impact v1_19 14531／`b38926f9…0ad0c`、impact test 12152／`38487f44…c2c`、PREREG v1.1 DIFF 5520／`4ef65fbe…45a`、NOTES 11272／`05a0fd99…9e1`）。runner 內固定的兩個 adapter 常數（57609／`8db9e3fd…10a59`、54101／`67094079…42f89`）與 repo 實檔相符。

**二、舊版失敗／新版通過（本端實跑）**
- 新 combo 測試 → 新 runner：rc=0，16 項 PASS。→ 23ff0e26 舊 runner：rc=1，10 項 FAIL（51001 不擋進場、無證據視窗拒絕、名次交錯、研究風控可關與分列、R2 改名、adapter 先驗後載、外層斷網先於載入、台北日界、引擎 SHA、版本標籤），與策略組自述一致。
- 新 impact 測試 → v1_19 工具：rc=0，7 項 PASS。→ v1_17 工具：rc=1，6 項 FAIL（out.tmp 別名、既存 tmp／symlink、open_at_end 截止上界、缺證據 UNDETERMINABLE、同 basename 不覆蓋、衝突 delta 非乾淨）。
- 未改檔回歸：L1 main、impact v1_17、LONG adapter、RETEST24 adapter 合成測試與 offline_static_check 全部 rc=0。

**三、靜態覆核**
- 第 6 點：`main` 先進 OfflineGuard，adapter 各讀一次、核完整大小＋SHA 後才 exec 同一份位元組，不再讀檔。
- 第 3 點：51001 只作資金費註記並列 gaps；不可計算視窗需非空 evidence。
- 第 4 點：只做跨方向同尺度名次交錯（同名次 long_first）與研究風控分列／可關；滑價 0.0003、24 槽維持現值並明列 out_of_scope，未越權定版。
- 日界：`--leg-daily-loss-day` 預設 taipei（偏移 8h），scope 列 DEV-1 待確認；引擎修補後原始碼寫檔並記 SHA。

**四、非阻擋文字缺陷（1 項）**：`combo_model_vs_live_shared_risk_diff` 第 3 條仍寫「600U UTC-day」，與預設台北日及下一條說明矛盾；建議下次推送改成依參數輸出，不需重跑。

**結論**：團隊層級覆核 PASS（v1.19 六點＋日界＋引擎 SHA）。這是團隊合成測試證據，不是 ChatGPT 端 runtime 或歷史績效通過。待決參數（日界、研究風控主臂開關、tie-break、映射／滑價／24 槽、R2 獨立基準）交 77／ChatGPT。PR 維持 Draft；`live_approved: false`；`FIB-4H-LONG-V3` 維持 NO-GO。
