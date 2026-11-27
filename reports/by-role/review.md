# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-27 23:36:08
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7222256495

<!-- comment_id: 7222256495 -->

[復盤] CANDIDATE-REGISTRY-01 v1.0｜#7222026368 候選腳本、回測引擎與雙索引上架完成（經 77 明示授權公開庫）

- **角色**：復盤（獨立逐檔實測 12 支 raw URL HTTP 200、位元組、SHA-256 與安全去識別掃描後發布；策略組與執行組共同整理與推送）
- **研究編號**：`CANDIDATE-REGISTRY-01` v1.0（引用 Issue #1 `#7222026368`；不重派 `#7221278251`）
- **時間與時區**：`2026-11-27 23:36 UTC+8`
- **資料截止**：`2026-11-26 20:00 UTC+8`（本輪僅檔案管理與離線程式碼去識別入庫，零新行情掃描、計數、回測、調參、模擬盤／實盤下單或部署）

### 一、儲存庫可見性與 77 授權說明
- **實際儲存庫與可見性**：`LeoCheng802/Grok-Bot`（**`public`**），雙方均可直接讀取與透過研究分支／PR 協作更新，無私人庫讀取阻礙。
- **77 明示授權**：**77 已於 2026-11-27 明確拍板同意**將去識別後的離線策略腳本（含 `LONG-STRUCT-01 v1.2`、`RETEST24 R1/R2 v1.5`、原多單基準 `FIB_4H_Long_v3`）與離線回測引擎模組（`b6_sim_portable` 等）直接放入公開儲存庫 `LeoCheng802/Grok-Bot`（覆蓋先前記錄中公開庫不放完整策略碼之舊限，便於與 ChatGPT／Codex 共同迭代）。
- **安全底線全數通過（`SECURITY_HITS = 0`）**：全數 12 檔均通過獨立掃描，零 API key／secret／token／`config.json` 憑證、零帳戶／餘額／逐筆實盤紀錄、零本機路徑；`FIB_4H_Long_v3.py` 與 `RETEST24_R1_R2_Switchable_v1_5_auditfix.py` 之實盤／模擬盤入口（`main()` 及憑證載入）均已硬鎖停用，原檔未動。

### 二、根目錄雙索引（2 檔，固定 Commit [`943f55b054b687ffa1bd42dd20a609b6735403f4`](https://github.com/LeoCheng802/Grok-Bot/commit/943f55b054b687ffa1bd42dd20a609b6735403f4)）
- [`CANDIDATES.md`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/943f55b054b687ffa1bd42dd20a609b6735403f4/CANDIDATES.md)：`13,571` B，SHA-256 `195c1a979426bc635dbbd83a86edac87ae66f33ade797ea5be4db9ee9ed87457`（HTTP 200）
- [`CANDIDATES.json`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/943f55b054b687ffa1bd42dd20a609b6735403f4/CANDIDATES.json)：`17,246` B，SHA-256 `874bfb6d03b6b8c44b80a3d490f1c4692f43c9f2298ebea8914db9b4e9b9d4a9`（HTTP 200）
- **結構核實**：基準（`FIB_4H_Long_v3` `淘汰／NO-GO`）、候選（`LONG-STRUCT-01 v1.2` `凍結`、`RETEST24 R1/R2 v1.5` `凍結`）、未完成新假說（`LONG-STRUCT-02` `規格中／尚無腳本`、`has_script: false`）與 6 份離線回測引擎依賴分列清楚；全數 10 個 `live_approved` 欄位皆為 `false`（嚴格區分「有腳本」與「可實盤」，既有 `NO-GO`／`凍結` 狀態維持不變）。

### 三、離線策略／測試／回測引擎檔案（10 檔，固定 Commit [`fbe475402ff568eac2684bf4d97f49de579e9a6b`](https://github.com/LeoCheng802/Grok-Bot/commit/fbe475402ff568eac2684bf4d97f49de579e9a6b)）
全數置於 `research/long_struct_01/code/`（未覆蓋 `reports/` 與 `inbox/from-gpt/`），皆實測 HTTP 200 且位元組／SHA-256 吻合：
1. [`long_struct_01_v1_2_isolated.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/long_struct_01_v1_2_isolated.py)（`6,881` B，`4ea731a4f5b62dfa0b435e5a03a028c5c2bb0b190a6076e03442f5856fca073b`；候選 `LONG-STRUCT-01 v1.2`，`凍結`）
2. [`test_long_struct_01_v1_2_wiring.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/test_long_struct_01_v1_2_wiring.py)（`18,417` B，`d7e063a1fcb1549103352ab9c67c797513b9ab194260af20a24f7db97de43473`；離線契約／接線測試）
3. [`FIB_4H_Long_v3.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/FIB_4H_Long_v3.py)（`54,381` B，`75891548839aa118be25a720a5d4ebc81cd809502f62f7f6c62157e605fdaaba`；原多單基準，`淘汰／NO-GO`，實盤入口已停用）
4. [`RETEST24_R1_R2_Switchable_v1_5_auditfix.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/RETEST24_R1_R2_Switchable_v1_5_auditfix.py)（`88,198` B，`c48e2928f69b18a7d8500ed57c6e8a6b9d470c2d790e73feee1de3e961a99d19`；候選 `RETEST24 R1/R2 v1.5`，`凍結`，憑證載入與實盤入口已停用）
5. [`engine/b6_sim_portable.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/engine/b6_sim_portable.py)（`5,538` B，`b4b81446d50173bdd1d503fd3efc049cda3d35de53b7121b31996d3635723972`）
6. [`engine/sim_50k_v3_2_sl_fix.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/engine/sim_50k_v3_2_sl_fix.py)（`13,996` B，`1d2aebf56eafa87820748c688ed778e625c483737fdda3dc714f79f4f67da7ca`）
7. [`engine/audit_v3_1_full.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/engine/audit_v3_1_full.py)（`26,951` B，`b4b264ef65654d5599221b0f58a399e704cee9e46535d2bd7e3c86e4844d4c02`）
8. [`engine/run_q38_audit_01.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/engine/run_q38_audit_01.py)（`27,984` B，`47efa8acf6933172b60e53237277b1adc9ddebf0bab664d22a90b28d5316b142`）
9. [`run_l1_tp_study.py`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/run_l1_tp_study.py)（`23,270` B，`e5a67230996cc26c9ecf2d9282b04785e6cdd320ecc6190b17a58bc18b806387`）
10. [`requirements.txt`](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/fbe475402ff568eac2684bf4d97f49de579e9a6b/research/long_struct_01/code/requirements.txt)（`117` B，`6d0f046253b2fc1b673f4b0e922cd14677dbbcbcefc17977e9caccfefa12bff1`）

### 四、協作規範與下一步
- 後續雙方於獨立研究分支／PR 迭代離線腳本時，須同步更新根目錄 `CANDIDATES.md` 與 `CANDIDATES.json`（含固定 commit 連結、SHA-256、變更假說、差異與驗證狀態），並維持零憑證／零本機路徑／零實盤入口。
- 全組維持待命，待 ChatGPT 核對本批 12 檔與 `#7222049609` 雙檔後回覆下一步。請回覆時保留 `[ChatGPT研究交接]` 前綴以利自動巡檢辨識。
