# CANDIDATES Registry (`CANDIDATE-REGISTRY-01 v1.1.1` + `BACKTEST-READINESS-01 v1.1`)

> **分支範圍**：本檔在 PR #6 **Open Draft** 分支 `research/offline-packaging-hardening-draft` 上更新（`BACKTEST-READINESS-01 v1.1`，引用 `#7225486769`、`#7225850828`、`#7226049299`）。**尚未合併 `main`，不覆寫 `main` 上的舊 SHA。** 回測由 ChatGPT 在隔離環境獨立執行；v1.1 前本地 Job 1／Job 2 只保留為修正前稽核紀錄。
>
> **發布狀態**：`PUBLISHED`（依 [Issue #1 #7222634694](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7222634694) 2026-11-27 23:54 UTC+8，77 已於 ChatGPT 對話直接確認公開範圍，**`#7222311457` 之公開推送暫停本輪已解除**，不追認先前外部轉述時間；公開範圍僅限本研究去識別候選腳本、基準、依賴、說明與索引，帳密／金鑰／憑證／私人交易紀錄與未授權私人結果仍嚴禁公開，且公開入庫非交易／部署／新回測授權；本輪維持零行情掃描／計數／回測／調參／交易／部署）。
> **對照交接**：`#7222026368`、`#7222274363`、`#7222311457`、`#7222634694`、`#7222785741`、`#7223029578`｜**儲存庫**：`LeoCheng802/Grok-Bot`（`public`）｜**實盤核准**：全部項目 **`live_approved: false`**。
> **審核口徑界線**：ChatGPT 於 `#7223029578` 實讀並接受 `#7222785741` 所交固定三檔（`CANDIDATES.json` 與 `CANDIDATES.md` 於 `c910d18b…`，以及 `LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json` 於 `5ca80cbc…`）之檔案／雜湊／報表核對與停止決策，**不等於**對公開改版新 SHA 完成獨立重現。

---

## 1. 基準（Baselines）

| 研究 ID | 方向 | 檔名／版本 | 狀態 | `has_script` | `live_approved` | 原版 SHA → 公開副本 SHA | 保留連線路徑與限制 |
|---|---|---|---|---|---|---|---|
| `FIB-4H-LONG-V3` | LONG | `FIB_4H_Long_v3.py` (`v3 sanitized`) | **淘汰（NO-GO）**；新 SHA 回歸：**待驗** | `true` | `false` | `c52ea221…dbe9` (`54,085` B) → `17b46a4e…26d7` (`55,001` B) at PR #6 `3f67bd87…` | **保留連線碼**：`urllib.request.urlopen` 與 `HOST='https://www.okx.com'`。2025-11 基準候選 101 係由隔離構建器產出，非以新 SHA 直接重跑。 |

## 2. 候選策略（Candidates）

| 研究 ID | 方向 | 檔名 | 版本 | 狀態 | `has_script` | `live_approved` | 原版 SHA → 公開副本 SHA | 測試證據與限制 |
|---|---|---|---|---|---|---|---|---|
| `LONG-STRUCT-01` | LONG | `long_struct_01_v1_2_isolated.py` | `v1.2` | **凍結** | `true` | `false` | 原檔未改：`4ea731a4…073b` (`6,881` B)；配套測試檔由 `9b532cc4…fe0d` 改為 `d7e063a1…3473`（僅去本機路徑） | 無連線碼。2025-11 五檔診斷窗（分母 900）最終候選為 0，結論嚴格限於**「該五檔十一月樣本同棒交集為零」**（不升級為普遍邏輯互斥）；ChatGPT 接受的是檔案／報表核對與停止決策，非獨立重現。 |
| `RETEST24-R1-R2` | SHORT | `RETEST24_R1_R2_Switchable_v1_5_auditfix.py` | `v1.5_auditfix (sanitized offline reference)` | **凍結**；新 SHA 回歸：**待驗** | `true` | `false` | `949a86f5…c15c` (`90,142` B) → `c2b00a98…4b04` (`89,100` B) at PR #6 `3f67bd87…` | **保留連線碼**：`BASE_URL='https://www.okx.com'` 與 `class OkxClient`。先前三角色審核係針對原版，不等同新 SHA 通過。 |

## 3. 未完成新假說（Pending Hypotheses）

| 研究 ID | 方向 | 狀態 | `has_script` | `live_approved` | 說明與未完成項 |
|---|---|---|---|---|---|
| `LONG-STRUCT-02` | LONG | **規格中／尚無腳本** | `false` | `false` | 單一時間結構假說（掃破收復與動能確認分時點）；**`B24H` 與 `A60＋量縮` 去重尚未完成**（待可讀檔對照），`L1 / LONG-LOOP` 不宣稱已證實訊號集合不重疊；已發布並經 `#7223029578` 結案接受純規格預登記 **v1.2**（[LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/5ca80cbcf45ebe9425516f658a7de838882403f1/research/long_struct_01/LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json)，commit `5ca80cbcf45ebe9425516f658a7de838882403f1`，`21,344` B，SHA-256 `246cda1c…b06e`；取代歷史 [v1.1](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/b4f3021995249b6e6734888ef7af0d871fd7caf4/research/long_struct_01/LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.1.json) `a0749787…42be` 與 v1.0 `8f9bf553…84d4`），仍維持 `PROPOSED_NOT_EXECUTED`。 |

## 4. 離線回測引擎依賴（`research/long_struct_01/code/`，非完整可獨立重現包）

| 檔案 | 原版 SHA（私人包 `v1.1`） | 公開副本 SHA（commit `fbe47540…9a6b`） | 變更範圍 | 新 SHA 狀態 | 保留連線路徑 |
|---|---|---|---|---|---|
| `engine/b6_sim_portable.py` | `b4b81446…3972` (`5,538` B) | 同左（原檔未改） | 無 | 與私人包原檔相同 | 無 |
| `engine/sim_50k_v3_2_sl_fix.py` | `1d2aebf5…da7ca` (`13,996` B) | 同左（原檔未改） | 無 | 與私人包原檔相同 | 無 |
| `engine/audit_v3_1_full.py` | `8ef7c513…4173` (`26,896` B) | `b4b264ef…4c02` (`26,951` B) at PR #6 `3f67bd87…` | 替換硬編碼 Windows `ROOT` 為 `OKX_RESEARCH_ROOT` 預設模組目錄 | **待驗** | 無 |
| `engine/run_q38_audit_01.py` | `0cb653f9…efdf` (`27,953` B) | `47efa8ac…b142` (`27,984` B) at PR #6 `3f67bd87…` | 替換兩處硬編碼 Windows 路徑字串 | **待驗** | 無 |
| `run_l1_tp_study.py` | `f98af4eb…6ee9` (`23,290` B) | `e920b953…75eb` (`39,180` B) at PR #6 `3f67bd87…` | 離線封裝：顯式路徑、網路拒絕、衍生庫雜湊與清理前路徑檢查 | **待驗** | 缺費入口硬拒絕；不在本索引重跑 |
| `requirements.txt` | `6d0f0462…bff1` (`117` B) | 同左 | 無 | 依賴清單 | 無 |

## 1A. 就緒四維（PR #6 Draft；不覆寫 `main`）

恰好 **2** 個凍結腳本候選。`FIB-4H-LONG-V3` 是基準 **NO-GO**，不是候選。`LONG-STRUCT-02` v1.2 是規格（`has_script: false`），不算腳本候選。全部 `live_approved: false`。

| 研究 ID | `script_delivered` | `packaging_verified` | `real_engine_integration` | `full_backtest` |
|---|---|---|---|---|
| `FIB-4H-LONG-V3`（基準，NO-GO） | true（PR #6 `3f67bd87fe5db2ec64d97b543fe780fa2f505f6f`，SHA `17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7`） | true（`#7225486769`） | 已備有界離線入口 `run_l1_bounded_backtest.py`（`da65fe4d`）；v1.1 前本地 fixture 小測曾留存 0-diff 紀錄，仍待 ChatGPT 獨立驗證 | 尚未由 ChatGPT 獨立完成（v1.1 前本地全期試跑因既有資金費庫缺 8H 費率 158/128 筆已硬拒絕中止 EXIT=2，未產出成功報表） |
| `LONG-STRUCT-01`（v1.2，凍結候選 #1） | true（main `fbe475402ff568eac2684bf4d97f49de579e9a6b`，SHA `4ea731a4f5b62dfa0b435e5a03a028c5c2bb0b190a6076e03442f5856fca073b`） | false（與 `main` 相同，未改） | 未接線（缺專屬離線 adapter） | 尚未由 ChatGPT 獨立完成 |
| `RETEST24-R1-R2`（v1.5，凍結候選 #2） | true（PR #6 `3f67bd87fe5db2ec64d97b543fe780fa2f505f6f`，SHA `c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04`） | true（`#7225486769`） | 未接線（缺空單專屬離線有界 adapter，待策略組對齊） | 尚未由 ChatGPT 獨立完成 |
| `LONG-STRUCT-02`（v1.2，待驗假說，`has_script: false`） | false | false | 不適用（缺 B24H 與 A60+量縮 規則去重，禁止實作） | 不適用 |

有界入口 `run_l1_bounded_backtest.py` 在 `da65fe4dbdd549aa973e4e3f2c69447b53dcb64a`（`37,538` B，SHA-256 `26757d866146622176803c05948ed27007b87f9503aad3f4ef89934a74ddccbf`）。本報告 `BACKTEST_READINESS_01_REPORT.md` 隨本草案分支更新，不併入 `main`。

## 5. `run_l1_tp_study.py --dry-check` 依賴與重定位方案（純文件方案，未推新碼）

- **依賴項目與現有可用位置（私人包內皆齊備，非缺件）**：
  1. `PACK_ROOT/REPRO_MANIFEST.json`（L316）：存於私人包 `RESEARCH-LOOP-01-PACK-v1.1.tar.gz`（SHA-256 `87dc925b8025c3bcaba87debb4d1bf8a86b794a8e47921f6ac2208b04e17da0d`）內（`3dacf887…9874`），公開 `code/` 目錄未含。
  2. `PACK_ROOT/scripts/shared_risk.py`（L324）：存於同私人包內（`3bbb11a8…2296`），公開 `code/` 目錄未含。
  3. `PACK_ROOT/scripts/FIB_4H_Long_v3.py`（L24 `--orig-long` 預設）：私人包內為原版 `c52ea221…dbe9`；公開 `code/` 目錄下則為去識別副本且位於 `code/FIB_4H_Long_v3.py`（非 `../scripts/`）。
- **明確界線**：目前公開庫 `research/long_struct_01/code/` 10 檔**不可**宣稱為可直接執行 `--dry-check` 或全期重現之完整包。
- **重定位與靜態安全修正方案（公開範圍已依 `#7222634694` 確認，程式改動按 `#7223029578` 有界範圍審核後於獨立分支草案 PR 提交，不合併、不部署）**：
  1. **重定位**：於 `run_l1_tp_study.py` 補齊顯式 `--manifest`、`--shared-risk` 參數（與 `--orig-long` 一致），或將公開目錄檢核拆為獨立離線 import 檢查，解除對私人包 `PACK_ROOT/scripts/` 結構的硬耦合。
  2. **靜態防呆**：維持 `FIB` 與 `RETEST24` 禁止執行 `main()`；若後續核准改碼，於 `FIB` HTTP helper、`RETEST24` `OkxClient` 請求方法及 `run_l1_tp_study.py` `backfill_missing_funding` 加上離線硬阻斷（預設 `--offline-only`，遇缺費報錯退出不聯網）。
