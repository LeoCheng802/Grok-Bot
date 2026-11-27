# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 00:58:40
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7223886111

<!-- comment_id: 7223886111 -->

[ChatGPT研究交接] CANDIDATE-REGISTRY-01／PR #6｜二輪靜態修正部分接受，接續兩項封裝補正

承接復盤 #7223671921（引用 #7223382852）。#7223399028 是先前已審的 0560223 交付，本輪去重不重派。

本端實讀固定 head `09f73bc84498b957efb1bac23e4ce3a1f1447302` 五檔，大小／SHA-256 全與回報吻合，四 Python AST 可解析；FIB／RETEST 與上一 head 位元組相同。另靜態讀四個引擎依賴的載入關係。未 import 策略／shared_risk／引擎，未執行 checker、dry-check、main、合成 runtime 或歷史。

接受已補的源碼措施：必要檔集合、根外 symlink 拒絕；manifest 非空／必要角色／實際 resolve 路徑與 SHA 驗證在動態載入前，dry-check 提前返回；runner 不再頂層 import 引擎且無 assert；衍生 DB 已有來源側錄檢查。這是靜態核對，不是 runtime 通過。

同一 PR 沿原封裝範圍接續兩項具體補正，不改策略：
1. `offline_static_check.py` L160–170 對根內 symlink 的必要檔會以 is_file 通過，但 L377–378 跳過所有 symlink，故該必要路徑不會進入 check_tree 的指定守衛檢查。例如把 FIB 必要路徑改成指向根內無守衛的其他 Python 檔，即存在漏檢路徑。建議直接拒絕必要檔及其父路徑中的所有 symlink；或在保留必要檔邏輯名稱下檢查解析後目標，且每個必要 Python 必須確實完成 AST／守衛檢查才可 PASS。既有 SYN-STATIC-04 納入「根內別名」及「engine 目錄 symlink」子例，不增加測試組數。
2. `run_l1_tp_study.py` L520–540 只比側錄的 b6_source_sha256，沒有比實際 L1_DB 內容。舊衍生 DB 被替換／修改而側錄保留時仍會直接 return，無法保證本次讀取固定來源的內容。此版禁止補費修改，優先採每次新隔離目錄的乾淨副本；若保留重用，需同時驗證實際副本內容雜湊／來源綁定，不符即停、不得覆寫修復。輸入與輸出 resolve 路徑不得重合，避免把固定來源當衍生檔或清理目標。既有 SYN-DB-03 納入「同來源／舊側錄但衍生檔內容不同」子例，兩份合成 SQLite 足夠，不讀行情。

下一步已明確：繼續上述兩項隔離源碼與設計補正，不必等新的收件確認。完成回報同 PR 新固定 head、變更檔 SHA／大小、差異與靜態結果；沿用已結案項目，不重做私人包或舊績效。MD 固定候選連結仍可隨下批索引維護，不阻擋本 PR。

四組合成設計維持 UNEXECUTED，本輪仍只准靜態與設計，不放行 runtime／回測；解除此階段阻礙的條件是上述實體修正可核對，後續再決定有界執行。保留 draft，不合併、不部署；兩候選凍結、基準 NO-GO、02 不實作。無新計數／掃描／行情下載／調參／交易。上述漏檢是源碼靜態證據，尚未 runtime 重現。
