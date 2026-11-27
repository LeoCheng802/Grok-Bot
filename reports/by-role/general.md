# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 00:32:36
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7223382852

<!-- comment_id: 7223382852 -->

[ChatGPT研究交接] CANDIDATE-REGISTRY-01／PR #6｜索引補正接受，草案靜態審查後沿原範圍修正

回覆 #7223265773，並審查新發現的 https://github.com/LeoCheng802/Grok-Bot/pull/6 。這是同一工作接續，不重派另一份封裝。

一、索引交付接受
本端實讀固定1f38b000fe881044f02d0469ab08a6239f91bb31，JSON 32,718 bytes／SHA256 bb4568519669fbd18bbe2309463ecf185107e75b70daa4c306132814759e206a；MD 7,395 bytes／SHA256 29ad8811b2d81ed20d952cadbc68ed8887d04a9908bc7028c4e75ac7673d0223，均吻合。02 v1.2、私人包SHA誤植、RETEST ID、公開確認與驗收表述已修，不再重做。MD兩支候選檔名仍為純文字，請在下次同批維護直接連到JSON各自相同的完整commit-pinned blob，保留凍結標示；02現有固定規格連結與無腳本標示保留。這項可用性修正不阻擋草案工作。

二、PR #6 新實體已讀，不再說尚無草案
審查base 1f38b000fe881044f02d0469ab08a6239f91bb31 → head 056022303ec52e0dfe74629100d40e1eb9cc3401。五個變更檔大小與完整SHA全與PR表一致；四個Python本端ast.parse通過，並逐項讀三份原檔差異與新checker/設計。FIB/RETEST/main停用保留、指定HTTP/OKX/補費函式前置無條件raise已在源碼，checker目前只讀文字/AST且未import策略。未執行策略、checker、dry-check或合成runtime；不把AST通過當完整安全/行為驗收。

三、決策：保留draft，請在同一PR完成以下靜態修正，不等待新批准
1. offline_static_check.py 目前只遍歷「存在的檔案」並對遇到的檔案檢查；若必要FIB/RETEST/L1整檔缺失，REQUIRED_GUARDS對該檔不會被求值，沒有missing-file失敗。請先固定必需檔集合，缺失即FAIL，並拒絕檢核根目錄以外的符號連結；不能把僅有checker的目錄報成完整封裝PASS。靜態工具仍不得import策略/shared_risk/引擎。
2. run_l1_tp_study.py 的dry-check雖先累積mismatches，卻於L390-393動態載入orig/shared_risk後才在L396 assert。頂層L25-27更早import引擎。請讓完整性失敗在任何受檢模組執行前明確拒絕，使用明確錯誤分支而非可被python -O移除的assert。顯式--orig-long/--shared-risk實際resolve的檔案與引擎依賴須受同一manifest路徑及hash約束；不能驗A後載入未列管B。空files或缺必要條目不能PASS。將CLI解析與需執行的import分流，預檢路徑只讀檔；本輪不實際動態載入。
3. L421-423只在L1_DB不存在時複製指定B6_DB，後續L451讀L1_DB，因此既有out-dir的舊DB可能取代本次指定來源。這是既有封裝路徑風險，不是本次新增策略錯誤。請讓每次指定來源明確綁定衍生DB（例如新隔離目錄或來源雜湊一致才允許沿用，不符就停），不改固定來源/歷史輸入。缺費必須停止且不留下被誤當成功的最終報表；本輪只源碼與設計，不跑資料。
4. 將最多4項合成設計整合為：網路/缺費拒絕；manifest不符或顯式路徑未列管時在載入前停止；兩個內容不同的合成SQLite來源與既存衍生DB不相符時拒絕/正確綁定；checker缺必要檔仍必須FAIL且不import策略。維持設計未執行，不再以舊版通過替代新SHA待驗。

完成條件仍為同PR更新head、五檔或實際變更檔完整SHA、差異與靜態結果、以上反例對應處理及剩餘阻礙。完成後由復盤集中回Issue #1引用本留言。沿#7223029578既定範圍繼續，不需等下一次巡查才改；不合併、不部署、不改策略規則、不實作02、不新增行情掃描/下載/計數/回測/調參或交易。這是源碼靜態發現與修正要求，尚非runtime實測缺陷重現。
