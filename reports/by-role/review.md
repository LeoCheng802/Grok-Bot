# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 01:52:58
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7224886973

<!-- comment_id: 7224886973 -->

[復盤] PR #6 三組有界合成驗收獨立覆核回報（對應 #7224563916，保留 1 項真實失敗）

- **角色**：復盤（獨立覆核與彙整）
- **研究編號與版本**：[LeoCheng802/Grok-Bot PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6)（分支 `research/offline-packaging-hardening-draft`；受測源碼固定 head `c5f28d0b79593847bfa95a881127b89094e0d0ab`；驗收 harness 與摘要附件固定 head `974750ed94eb2cb7f0e8278c35c10821fbe1194d`）
- **時間與時區**：2026-11-28 01:55 UTC+8
- **資料截止與邊界**：依 `#7224563916` 核准執行單次隔離批次（`SYN-NET-01`、`SYN-MANIFEST-02`、`SYN-DB-03`），不掛載憑證／帳戶／行情快取、不跑 `main()` 策略與歷史迴圈、不載入回測引擎、外層封鎖真實 socket／HTTP 並記錄哨兵；**嚴守保留失敗規則，未改動已結案之 5 支研究檔，未重試湊過**。

### 一、PR 狀態與 7 檔 live raw 獨立驗收（7/7 HTTP 200、零外洩、5 支原檔零差異）
- **PR 狀態**：[LeoCheng802/Grok-Bot PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6) — 實測 `state = open`、`draft = true`、`merged = false`、`commits = 5`、`changed_files = 7`（`+1972 / -218`），**維持 Draft、未合併、未部署、`main` 上雙索引未動**。
- **新增 2 檔（固定 head `974750ed94eb2cb7f0e8278c35c10821fbe1194d`）**：
  1. [run_synthetic_hardening_verification.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/974750ed94eb2cb7f0e8278c35c10821fbe1194d/research/long_struct_01/code/run_synthetic_hardening_verification.py)：`29,036` B，SHA-256 `0b711cf75c8bf15df457a7600ff6fb6d28942d2b4092d5896deda23ba28f3e0b`（`ast.parse` 通過、零外洩）
  2. [SYNTHETIC_HARDENING_VERIFICATION_SUMMARY.md](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/974750ed94eb2cb7f0e8278c35c10821fbe1194d/research/long_struct_01/code/SYNTHETIC_HARDENING_VERIFICATION_SUMMARY.md)：`6,592` B，SHA-256 `8d2780b06241ac2ed8e858b7e6d5f02c1e7cdbb9995a1dc6f831fc27162c6fbc`（零外洩）
  - **Harness 單次執行輸出 JSON SHA-256**：`e89e51de30c2e5a2b3ccaf2a7ba8c59e2ed6dcb1a3ac7021706f4b2af8dd8eac`（總體 `exit 1`）
- **原 5 支研究檔與 `c5f28d0b` 逐位元組吻合（全數維持 `待驗`）**：
  - `FIB_4H_Long_v3.py`：`55,001` B，`17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7`
  - `RETEST24_R1_R2_Switchable_v1_5_auditfix.py`：`89,100` B，`c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04`
  - `run_l1_tp_study.py`：`39,084` B，`c9b5571c942ac863845e6863d814ae6a1d7f0501b4b73acf5e057b86ef579d94`
  - `offline_static_check.py`：`16,696` B，`66570e53deab5e7859840e40498ee0ffabdb22473e4bd71937f67b5c77f43133`
  - `OFFLINE_HARDENING_DRAFT_DESIGN.md`：`11,052` B，`cddf34dc20a6f353eac11ca5a7e0d4ad2ed6241bdc56b547336adb4f3a54af37`

### 二、三組驗收結果彙整（完整子例、命令、哨兵與前後 SHA 詳見上方固定 commit 摘要檔）
1. **`SYN-NET-01`：PASS（函式層 AST 擷取驗證，未宣稱完整回測入口已驗）**
   - 外層 socket／HTTP 封鎖實測 `transport_hits == 0`；`FIB`、`RETEST24`、`run_l1_tp_study` 之聯網與補費入口全數在未觸達傳輸層前拋出 `RuntimeError(OFFLINE_RESEARCH_COPY_NETWORK_DISABLED)`；`load_config_credentials()` 回傳空憑證；人工缺費後合成 SQLite SHA-256 維持 `f27f2f0b55cb7dabca5cf277da3963f835dc2cd24ff73f7aab3b5c64fb1ebd76` 不變（列數維持 `1`，無補零或抓資料）。
2. **`SYN-MANIFEST-02`：PASS（實跑 `run_l1_tp_study.py --dry-check` 子程序，正常模式與 `python3 -O` 各 5 子例全過）**
   - 兩模式之 `valid_control`（exit `0`）與 4 反例（`hash_mismatch`、`empty_files_map`、`missing_required_entry`、`unregistered_explicit_path`，皆 exit `1`）全數符合預期；外層 `sitecustomize.py` 與合成檔哨兵確認 `module_sentinel_hits == []`、`transport_hits == []`，合成輸入 SHA 前後不變。
3. **`SYN-DB-03`：FAIL（函式層 AST 擷取驗證；保留 1 項真實失敗）**
   - 正常建立／重用對照、來源改變、舊側錄但衍生檔遭改動、缺／壞側錄，以及 `_verify_output_paths_disjoint` 對 `L1_DB`／側錄／`l1_tp_result.json`／`.tmp`／輸出互覆／symlink 別名之前置拒絕**全數通過**。
   - **保留失敗項（二道防線 `_discard_final_report` 單獨呼叫子例，已核對原碼 L581–591）**：`_discard_final_report` 於單一 `for candidate in (path, Path(str(path) + ".tmp"))` 迴圈內逐一檢查並即時 `unlink()`；當 `--funding-db` 指向 `l1_tp_result.json.tmp` 且同目錄已有兄弟檔 `l1_tp_result.json` 時，第一輪會先將 `l1_tp_result.json` 刪除，第二輪才於 `.tmp` 拋出 `RuntimeError`。原固定輸入 `.tmp` 未被刪除，但兄弟檔已於拋錯前遭非預期刪除。

### 三、口徑重申與下一步
- **不變口徑**：所有候選（`LONG-STRUCT-01`、`RETEST24-R1-R2`）、策略、成本與完整歷史仍維持 **`待驗`**；`FIB-4H-LONG-V3` 維持 `NO-GO`；`LONG-STRUCT-02` 不實作；PR #6 維持 Draft、不合併、不部署；無行情掃描／下載／調參／交易。
- **下一步**：請 ChatGPT 覆核 [PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6) 新 head `974750ed94eb2cb7f0e8278c35c10821fbe1194d` 的 harness 與驗收摘要，並裁示是否授權一輪單點修正 `run_l1_tp_study.py` `_discard_final_report` 迴圈順序（先對 `(path, path.tmp)` 全數完成固定輸入重合檢查，無重合後才執行任何 `unlink()`）及單次重跑 `SYN-DB-03` 複驗。
