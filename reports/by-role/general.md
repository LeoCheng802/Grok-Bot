# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 16:22:34
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7236541829

<!-- comment_id: 7236541829 -->

【2026-11-28 16:22 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.21｜PR #7 新 head 812fdd5 獨立覆核

- 角色：復盤（獨立覆核；純合成測試，未跑歷史回測、未抓市場資料、未接觸任何帳戶）
- 對象：策略組 #7236523064；PR #7 head `812fdd59edc47c5c2afc3731c948bad4595987e5`（parent `0acece2177509ec647b1dbd95da45aa95a07bd72`），Draft 未合併
- 執行起迄（UTC）：2026-11-28T08:21:52Z → 08:21:56Z；本機保存執行紀錄 run.log 847 行／SHA256 `3ae825acb100f58d53b8288d76bd6013fdd0a08af4b97895fbe11ee57fc66bf9`

**一、實體**：本次 diff 只有 5 檔，本端 checkout 重算的大小與 SHA256 和交付表完全一致（runner 63276／`4d41f66f…0d8d`、combo test 46327／`3a499ea6…a5d`、impact 17008／`ffb2cd40…6d7d`、impact test 20690／`16a5516f…9a27`、V1_21 NOTES 10882／`cfc1c4e9…7ed7`）。

**二、舊版失敗／新版通過（本端實跑）**
- 新 combo 測試：新 runner rc=0 全 PASS；0acece21 舊 runner rc=1，5 項 FAIL（limitations 出場 bar 入帳句、主比較參數組、控制旗標欄位、prereg_deviations 依實際旗標、版本標籤）。
- 新 impact 測試：新工具 rc=0 全 PASS；0acece21 舊工具 rc=1，2 項 FAIL（無效 cutoff、非 list 缺費事件在有持倉命中時仍回 AFFECTED）。
- 未改檔回歸：L1 main、impact v1_17、LONG／RETEST24 adapter 合成測試與 offline_static_check 全 rc=0。數量與策略組自述一致。

**三、靜態覆核**
- impact 最終判定改為「有任何 undeterminable 原因就先判 UNDETERMINABLE」，hit8／hitn／covered 仍記錄，符合 v1.21 要求。
- 新增 `main_comparison_control_flags_match`／`_mismatches` 核對六項旗標，附註明只代表控制旗標、不代表策略／資料／成本對齊；未使用易誤解的 `is_v1_20_main_comparison` 命名。程式預設未改。

**結論**：團隊層級覆核 PASS，v1.21 待辦（判定優先序、出場 bar 入帳說明、控制旗標欄位、prereg_deviations）均已有舊版失敗／新版通過證據。本交付仍是舊 adapter 0.0003／24 槽，不得稱與原研究同口徑。這是團隊合成測試證據，不是歷史績效。PR 維持 Draft；`live_approved: false`；`FIB-4H-LONG-V3` 維持 NO-GO。
