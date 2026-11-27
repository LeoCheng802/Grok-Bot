# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 01:25:03
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7224381445

<!-- comment_id: 7224381445 -->

[復盤] SYN-STATIC-04 隔離臨時副本獨立實測回報（對應 #7224263057）

- **角色**：復盤（獨立覆核與重現）
- **研究編號與版本**：[LeoCheng802/Grok-Bot PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6) 固定 head `defae193e40cf7347be4ae0362be449062ff501c`（分支 `research/offline-packaging-hardening-draft`，維持 Open Draft、未合併、未部署）
- **時間與時區**：2026-11-28 01:26 UTC+8
- **資料截止與邊界**：僅依 `#7224263057` 核准執行 `SYN-STATIC-04` 純標準庫檢核器；全程於隔離臨時目錄（執行組標示 `syn_static_04_uz64eysn`、復盤獨立重現標示 `rev_syn_static_04_whjez6rp`，跑畢即自動清除）執行，零異動 repo、零 `import` 策略／`shared_risk`／引擎、零跑 `run_l1_tp_study.py` `main()`／`--dry-check`、零行情／零網路。**本回報僅驗證純靜態檢核器，不放行其他 3 組 runtime（`SYN-NET-01`、`SYN-MANIFEST-02`、`SYN-DB-03` 維持 UNEXECUTED），亦不解除任何候選／腳本之 `待驗` 狀態。**

### 一、受測對象與檔案 SHA-256（固定 head `defae193e40cf7347be4ae0362be449062ff501c`）
- **受測檢核器**：[offline_static_check.py](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/defae193e40cf7347be4ae0362be449062ff501c/research/long_struct_01/code/offline_static_check.py)（`16,696` B，SHA-256 `66570e53deab5e7859840e40498ee0ffabdb22473e4bd71937f67b5c77f43133`）
- **隔離副本 9 檔齊備對照（均自該固定 head 拉取）**：
  - `FIB_4H_Long_v3.py`：`55,001` B，`17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7`
  - `RETEST24_R1_R2_Switchable_v1_5_auditfix.py`：`89,100` B，`c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04`
  - `run_l1_tp_study.py`：`35,985` B，`a16fe5baa7ce2249201cfefbcda53df2dd4e0fd2294c711a39ea502ecdf9968e`
  - `offline_static_check.py`：`16,696` B，`66570e53deab5e7859840e40498ee0ffabdb22473e4bd71937f67b5c77f43133`
  - `engine/b6_sim_portable.py`：`5,538` B，`b4b81446d50173bdd1d503fd3efc049cda3d35de53b7121b31996d3635723972`
  - `engine/sim_50k_v3_2_sl_fix.py`：`13,996` B，`1d2aebf56eafa87820748c688ed778e625c483737fdda3dc714f79f4f67da7ca`
  - `engine/audit_v3_1_full.py`：`26,951` B，`b4b264ef65654d5599221b0f58a399e704cee9e46535d2bd7e3c86e4844d4c02`
  - `engine/run_q38_audit_01.py`：`27,984` B，`47efa8acf6933172b60e53237277b1adc9ddebf0bab664d22a90b28d5316b142`
  - `requirements.txt`：`117` B，`6d0f046253b2fc1b673f4b0e922cd14677dbbcbcefc17977e9caccfefa12bff1`

### 二、逐例實測結果（復盤獨立重現 `rev_syn_static_04_whjez6rp`，與執行組結果一致）
5 組皆顯示 `process.imported_trading_modules = []`、`executed_strategy_main = false`、`ran_private_pack_dry_check = false`：
1. **完整副本對照（`control_full_copy`）**：`exit 0`｜`stdout`：`STATIC_CHECK PASS`｜`checked_required_py = 8`｜`escaping_symlinks = []`｜`failures = []`。
2. **子例 1 — 缺必要檔（`subcase1_missing_required_file`，移除 `FIB_4H_Long_v3.py`）**：`exit 1`｜`stdout`：`STATIC_CHECK FAIL`｜`checked_required_py = 7`｜`failures = ["FIB_4H_Long_v3.py: required file missing", "FIB_4H_Long_v3.py: required python file did not complete AST, leak, and network-guard checks"]`。
3. **子例 2 — 根外 symlink（`subcase2_outside_root_symlink`，新增指往根外目標之 `escape_link.py`）**：`exit 1`｜`stdout`：`STATIC_CHECK FAIL`｜`escaping_symlinks = ["escape_link.py"]`｜`failures = ["escape_link.py: symlink escapes check root"]`。
4. **子例 3 — 根內必要檔別名（`subcase3_inroot_required_alias_symlink`，將 `run_l1_tp_study.py` 改為指向同根內 `FIB_4H_Long_v3.py` 之 symlink）**：`exit 1`｜`stdout`：`STATIC_CHECK FAIL`｜`checked_required_py = 7`｜`escaping_symlinks = []`｜`failures = ["run_l1_tp_study.py: required path component is a symlink: run_l1_tp_study.py", "run_l1_tp_study.py: required python file did not complete AST, leak, and network-guard checks"]`。
5. **子例 4 — `engine/` 目錄 symlink（`subcase4_engine_dir_symlink_inroot`，將 `engine/` 替換為指向同根內 `engine_real/` 之 symlink）**：`exit 1`｜`stdout`：`STATIC_CHECK FAIL`｜`checked_required_py = 4`｜`escaping_symlinks = []`｜`failures` 明確列出全部 4 支 `engine/*.py` 的 `required path component is a symlink: engine` 與 `required python file did not complete AST, leak, and network-guard checks`（亦與執行組以兄弟目錄測試之拒絕結果一致）。

### 三、剩餘阻礙與下一步
- **進行中**：`run_l1_tp_study.py` 結果／`.tmp` 與固定輸入統一重合保護及 `SYN-DB-03` 子例補強正由執行組於同 [PR #6](https://github.com/LeoCheng802/Grok-Bot/pull/6) 進行中，待新 head 落地並完成獨立覆核後另行回報。
- **不變紅線**：`SYN-NET-01`、`SYN-MANIFEST-02`、`SYN-DB-03` 維持 **UNEXECUTED**；PR #6 維持 Draft、不合併、不部署；兩候選凍結、基準 NO-GO、`LONG-STRUCT-02` 不實作。
