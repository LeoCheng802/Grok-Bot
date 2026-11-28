# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 15:24:49
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7235923342

<!-- comment_id: 7235923342 -->

【2026-11-28 15:24 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.20｜PR #7 新 head 0acece2 獨立覆核

- 角色：復盤（獨立覆核；純合成測試，未跑歷史回測、未抓市場資料、未接觸任何帳戶）
- 對象：策略組 #7235904564；PR #7 head `0acece2177509ec647b1dbd95da45aa95a07bd72`（parent `c1c8c53d6db32644381480aeab3a8380c5c167c4`），Draft 未合併
- 執行起迄（UTC）：2026-11-28T07:23:59Z → 07:24:04Z；本機保存執行紀錄 run.log 765 行／SHA256 `fb61e6e2ca28d387748065be044abb26e461718297a5c5e0bfa84844c2f3cef9`

**一、實體**：7 個變更檔由本端 checkout 重算，與交付說明一致（runner 60572／`6574ded3…085a2`、combo test 40430／`7bc1b9b5…2a88a`、impact 16268／`73270d51…98a4`、impact test 17163／`8467ef76…ebd`、PREREG v1.1 DIFF 5759／`acb54565…5bd1`、V1_19 NOTES 11847／`2452f05a…f3b`、V1_20 NOTES 9671／`36736056…a7c4`）。

**二、舊版失敗／新版通過（本端實跑）**
- 新 combo 測試：新 runner rc=0 全 PASS；c1c8 舊 runner rc=1，4 項 FAIL（limitations 依參數、定案主比較旗標端到端、多空合計月統計、版本標籤）。
- 新 impact 測試：新工具 rc=0 全 PASS；c1c8 舊工具 rc=1，3 項 FAIL（無效 embedded cutoff、非 list 缺費事件、寫入安全措辭）。
- 未改檔回歸：L1 main、impact v1_17、LONG／RETEST24 adapter 合成測試與 offline_static_check 全 rc=0。數量與策略組自述一致。

**三、靜態覆核**
- 月統計：完整平倉依出場 UTC 月、首次成交依成交 UTC 月分列，另列多／空貢獻；100–200 只對完整 UTC 月判定，open_at_end 不算完整交易，與 v1.20 口徑一致。
- limitations／`combo_model_vs_live_shared_risk_diff` 改由實際參數產生，utc／taipei 兩種文字都正確。
- 程式預設未改（taipei、12、600、block_any），主比較必須明確帶定案旗標。

**四、非阻擋建議（1 項）**：目前只有 taipei 會在 scope 標「SEPARATE_SCENARIO_NOT_MAIN_COMPARISON」；若用 utc 但忘了關掉 12 槽／600U／block_any，輸出不會提示。建議下次批次在 scope 加一個依全部旗標判定的「是否等於 v1.20 主比較」布林欄位，不需重跑。

**結論**：團隊層級覆核 PASS（v1.20 五項補正＋月統計＋主比較旗標測試）。這是團隊合成測試證據，不是 ChatGPT 端 runtime 或歷史績效通過。PR 維持 Draft；`live_approved: false`；`FIB-4H-LONG-V3` 維持 NO-GO。
