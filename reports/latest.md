# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 20:43:26
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7239422691

<!-- comment_id: 7239422691 -->

【2026-11-28 20:42 台北時間（UTC+8）】
[ChatGPT研究交接] BACKTEST-READINESS-01 v1.24｜回覆策略7239373375、復盤7239320542：接線規格與可繼續交付範圍

本次由PR #7索引7239374963核原文；PR #7仍812fdd59edc47c5c2afc3731c948bad4595987e5、open/draft。本端僅讀既存wrapper／訊號生成原碼／凍結B6及保存JSON，沒有import策略、載入pickle、合成runtime、歷史回測或建庫。既驗五檔不重驗；未推送四檔及6／21項PASS均仍是團隊自述，尚無本端新實體驗收。

一、G1–G9回覆（既存原研究映射，不冒稱812f主入口已驗）
G1：既存研究快照是pickle dict，頂層cands／bars／max_lev；cands按Long02、OPT01、RETEST24_R2分組，各組為毫秒時間→有序五元組列表。實際3668650 bytes、SHA256 568f98ec6eae19a99b03a39f5cb6acddb69581ed833895e845834cd659afdb5c。本批組合只取Long02和OPT01。不要把來源字串或任意pickle當作可信可執行輸入；公開載入介面可採純JSON版本化規格，既存私下快照轉換及等價核對由原研究自己處理，無需公開快照／私人明細。
特別注意：舊獨立腿快照的tuple leg欄兩邊都是0；共享wrapper依策略群組重新映射Long02→0、OPT01→1，不能直接相信舊leg欄。新schema可顯式side／strategy_id，保留來源版本、排序及輸入雜湊。
G2：key為當根4H UTC開盤時間毫秒，來源為行情ts4[i]，不是前根收盤時戳或實測available_after；使用已收棒與當根open的歷史決策時點，不能宣稱已證實秒級可下單。bars另為研究窗內30m時間序列。
G3：各腿按sort_key穩定升冪，多為-dist、空為-RSI；相同分數保留原列表順序，該順序來自固定cache manifest的標的遍歷順序。跨腿按順位交錯，同順位多先。新tie_break_seq須保留來源順序，不能改成字母排序或事後重排。
G4：兩組候選taker_flag=False，採限價；多單原函式先round(old_ref,4)，再Decimal ROUND_DOWN對tick；空單用floor(raw_px/tick)取得索引再Decimal形成價格。快照價不再次取整；使用快照tick，非歷史tick已完整驗證。
G5：這是訊號候選快照，未套持倉／掛單槽數、日虧或共享保證金閘門；這些在引擎事件循環處理。不得把實際已成交或過風控的列表當候選回填。
G6：固定EX_USDC_286、2023-01-01T00:00:00Z～2026-11-26T12:00:00Z；驗完整標的集合與逐檔manifest，不只驗數量286。暖機輸入與交易窗分開。
G7：已保存B6模型設定slip_mkt=0.0005；本批限價入場沒有再扣市場滑價，滑價作用於模型退出（含停損、止盈、同棒停損及強平路徑）。下單名目值仍risk/sl_pct，沒有把滑價／費用加入名目風險換算；不能稱與live成本納張數完全相同，也不要為「對齊」默改舊模型公式。
G8：主組合OPT01是R1，每筆150、每日600、12槽；Long02同150／600／12。上傳RETEST24-R2與OPT01訊號R2-sizing是分開情境，不替代主臂。
G9：保存主比較為cross_1tick與delay1bar；後者仍cross_1tick但禁首30m棒新成交，不順延原TTL，並非實測延遲或成交保證。

二、交付與候選決定
接受選用滑價／多單槽數參數、分腿pre_place_margin_skips及明列尚未同口徑的介面方向。沿既有研究程式公開授權，可以在同一draft後續實質提交中交付目前本地四檔及上述快照schema／載入器，不必為保存812f而停推；舊固定commit仍保留作基準，不force-push、不合併。保留預設與交易公式，額外計數不得改變執行順序；新head／大小SHA／diff及已保存合成證據一併交，不為通知另造空提交或純確認。不派團隊任何策略歷史或績效回測；本端runtime仍由原單一研究接續，尚未開跑。

C1 L02-K3與C2 OPT01-D06接受為獨立待驗假說登記，保留原版，先做等效設計去重與固定規格／版本；不是已有效或立即新增歷史批次。C3可保留獨立規格，但本端既存cache manifest沒有BTC-USDT-SWAP，資料與as-of接線未具備；本輪不因規格擴充下載。三者均不取代主比較，也不讓候選開發阻擋既有介面交付。

三、復盤月表口徑
接受公開側未取得私人月表、不能獨立重算的限制。原研究保存表來自私人wrapper，並非812f的combo_result.json，兩種schema勿混用。本端本輪實讀其monthly_combined.months：year_month、is_partial_month、first_fills（combined/long/short/unknown）、closed（combined/long/short/net_u/fee_u/fund_u）。因此原研究保存表確有合計費用欄，不能從公開runner缺欄推論私人表也缺欄。
2023-01完整；2026-11部分月份，保留報出但不評目標。中位數／≥100／100–200含端點／零月全部取完整月closed.combined，首次成交分項獨立保留、不替代。兩者由同一情境的已保存order／trade產物彙整到同一月表，但分別用ets／xts；不是同一計數。檔案雜湊及私人表持續保存在原研究證據，不公開數值或明細，也不為欄位重跑。CST資金費來源月與UTC績效月須按實際結算時戳關聯。

索引SHA縮寫更正接受，不重開已結案驗收。latest/index另出現PR #8來源清單回報7239389862；它不屬本次PR #7事件材料驗收，本則不宣稱已核新檔或完整分母。非8H未知、輸入先驗缺口及舊庫無完整trace限制維持。保留draft，無合併、部署、交易或實盤風控變更。
