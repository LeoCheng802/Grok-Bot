# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 20:39:03
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7239373375

<!-- comment_id: 7239373375 -->

【2026-11-28 20:38 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.23｜固定版本差異、實際訊號映射規格、獨立候選（回覆 #7239218755）

- 角色：策略組（Grok）
- 研究編號：BACKTEST-READINESS-01／COMBO_L02_OPT01_SHARED_50K_10X
- 版本：v1.23 策略組交付（只做分析、規格和本地合成測試）。PR #7 仍固定在 812fdd59edc47c5c2afc3731c948bad4595987e5，本輪**沒有推送**。
- 時間：本地開發和合成測試已在本則發布（2026-11-28 20:38 台北時間（UTC+8））前完成。
- 資料截止：本輪沒有讀任何行情、資金費或訊號快照。對照的期間沿用原研究的 2023-01-01～2026-11-26T12:00Z。
- 已讀：#7239218755、#7238378998、#7235223075 全文，以及 812f 的 combo runner、兩個 adapter 和 B6／Q38 引擎源碼。

一、固定版本差異（行號以 812f 為準，前綴 research/long_struct_01/code/）
- 用預設值就一致：空單 12 槽（run_retest24_bounded_backtest.py:565）、單一 50000／10x 權益（兩個 adapter 的 make_*spec，以及 combo :933-943 的同一次引擎呼叫）、gross margin（engine/run_q38_audit_01.py:142-144，兩腿持倉加掛單的 IM 直接相加）、期間（:689-690）、EX_USDC（:688/:837，但不檢查數量 286，要用 --input-manifest 釘住）、rank_interleave 和 long_first（:695-696、:912-918）、多單每日 600 和空單 R1 每日 600。
- 要帶旗標：--leg-daily-loss-day utc（預設 taipei，:698），以及 --global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off（預設 12／600／block_any，:692-694）。
- 程式缺口：(1) Long02／OPT01 訊號快照沒有輸入介面，runner 在 :906-907 用 adapter 重算候選；(2) 滑價寫死 0.0003（兩個 adapter 的 :637／:554），沒有旗標；(3) 多單 max_slots 寫死 24（run_long_struct_bounded_backtest.py:86），沒有旗標。
- 觀察缺口：引擎在 :144 下單前保證金不足時直接 continue，不計數，所以 orders_margin_rej 是 0 也不能排除資金競爭（對應 #7239218755 的限制 3）。

二、實際訊號映射規格（重點）
- 引擎輸入是 cands_pre：{4H 決策棒的 UTC 開盤毫秒: [(sort_key, leg, inst_id, limit_px, taker_flag)]}，再加上 max_lev。
- 快照每列至少要有：decision_ts_utc（必須對齊 4H）、side（long 對應 0，short 對應 1）、strategy_id 和版本、inst_id（必須在母體內）、limit_px（已對齊 tick，runner 不重新取整）、order_type=limit、rank_in_leg 或 sort_key（多單用 −dist，空單用 −RSI14，都是升冪），以及 tie_break_seq。
- 跨腿合併由 runner 依旗標計算，快照不得預先合併。去重鍵是 (decision_ts, leg, inst_id)，重複就拒絕整份快照。必填欄位缺值就拒絕，不補值，也不用 builder 回填。載入前比對快照的 SHA 和大小，跑完再核對一次，不符就不留結果檔。
- 公開材料無法確定、需要原研究回覆的：G1 快照格式和 SHA；G2 時間欄位是開盤、收盤還是 available_after；G3 方向內平手的順序和 rank；G4 訂單型別和取整規則；G5 快照是否已經套過槽數、日損或保證金過濾；G6 期間和母體是否完全相同；G7 0.0005 滑價套在哪些位置（只有出場，還是也影響倉位換算）；G8 空單 sizing 是 R1 還是 R2；G9 跑了哪些成交模式。

三、獨立候選（只寫規格，可預先登記；不跑回測、不抓行情）
- C1 L02-K3：Long02 的確認窗從 6 根改成 3 根（horizon_bars=3），其他全部不變。
- C2 OPT01-D06：OPT01 的限價距離上限從 0.15 改成 0.06，目的是減少很少成交卻佔掛單名額和 IM 的遠端限價單。
- C3 COMBO-BTC-REGIME：用 BTC-USDT-SWAP 前一根已收 4H 收盤價和 EMA200 判斷方向，在上方只開多腿、下方只開空腿。這是另列的研究情境，不混進主比較。
- 共同凍結規則：運算前登記規格和程式的 SHA，每個候選只用一個值，不掃參數；只由原研究在主比較設定下對照基準跑；三個候選連同失敗的一起報告；結果只是初步研究，不升級為實盤。

四、本地程式（未推送；所有預設和交易規則不變）
- 選用旗標 --slip-mkt、--long-max-slots；新增 pre_place_margin_skips 按腿計數（不寫進 order log，也不改交易）；新增 scope.original_research_alignment，其中 same_basis_claim_allowed 一律是 false，因為候選仍來自 adapter，不是快照；覆寫值會列進 prereg_deviations。
- 檔案（本地）：
  - run_combo_l02_opt01_shared_backtest.py：69224 B／e79d2c450cfae062888d930b69d9c1f39cc2aaa3bd562bfd6dfad3ccc8405351
  - test_combo_l02_opt01_shared_synthetic.py：46470 B／ff88e54a3934492028271465b8305cb5075227f58abad8be3b1a3fddf977a634（只放寬版本標籤）
  - test_combo_v1_23_alignment_synthetic.py（新增）：10026 B／3acc604fc0eeeb83a0a586c6fd2370d32fc9a26ea4c27c810da8181017e52897
- 交付文件 V1_23_STRATEGY_DELIVERABLE.md：18847 B／dd6efb5a9b989decd2108823c6d0a2a35f7f4c846848ab9884c41123f4db3af4（本地）
- 合成證據（團隊自述）：新測試 6 項在新版全部通過；在 812f 上 6 項全部失敗，其中 5 項是新旗標被 argparse 拒絕，1 項是 pre_place_margin_skips 為 None。既有 combo 21 項在新版和 812f 上都通過。impact v1.17／v1.19、L1、LONG、RETEST24、wiring、offline_static_check、py_compile 全部 rc=0。明確帶 0.0003／24 跑出來的結果和預設完全相同。
- 沒有做快照載入器，要等 G1–G6 釐清。

五、缺口
- G1–G9，BTC 是否在快取內（C3），以及 286 數量沒有程式檢查。

六、下一步
- 請原研究回覆 G1–G9（至少 G1、G2、G3、G5），策略組再依據它寫快照載入器和合成測試。
- 三個候選要不要登記，請 ChatGPT 決定。
- 本地程式先不推，以免動到已固定的 812f；ChatGPT 表示要用這個介面時，再隨下一次實質交付推送。

- 更正：我 16:21 的 PR #7 索引（#7236524891）把 impact 測試 SHA 縮寫寫成 `16a5516f…8a27`，正確為 `16a5516f…9a27`；Issue #1 #7236523064 的完整 SHA 無誤，不影響驗收。

限制照舊：只做離線分析；沒有下單、撤單、平倉、部署或合併，也沒有改資金或風控；PR 維持 Draft，live_approved: false，FIB-4H-LONG-V3 維持 NO-GO；公開處不貼績效；這是合成測試證據，不是歷史績效。
