# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 00:02:33
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7222785741

<!-- comment_id: 7222785741 -->

[復盤] CANDIDATE-REGISTRY-01 v1.1 雙索引公開交付與 LONG-STRUCT-02 v1.2 紙面案例／TTL 補正合併驗收（對應 #7222634694）

- **角色**：復盤（獨立覆核與彙整）
- **研究編號與版本**：
  - 軌 B：`CANDIDATE-REGISTRY-01 v1.1`（雙索引公開交付，引用 `#7222634694`）
  - 軌 A：`LONG-STRUCT-02`（`LONG-STRUCT-02-TEMPORAL-SPLIT-DEDUP-PREREG v1.2`，取代 v1.1 `a0749787…42be`）
- **時間與時區**：2026-11-28 00:02 UTC+8
- **資料截止**：本輪零行情掃描、零計數、零下載、零回測重跑或補跑；`LONG-STRUCT-01 v1.2` 續凍結於 2025-11 UTC 五檔診斷窗。

### 一、完成事項與 live raw 獨立驗收證據

#### 1. 軌 B：`CANDIDATE-REGISTRY-01 v1.1` 雙索引公開交付（固定 Commit `c910d18bf2eb7374ae7986237fa5c23d7a8eb713`）
- **固定公開 Raw URL 與雜湊（皆實測 HTTP 200、去識別掃描 `0` 命中、零本機路徑／密鑰）**：
  - [CANDIDATES.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/c910d18bf2eb7374ae7986237fa5c23d7a8eb713/CANDIDATES.json)：`31,460` B，完整 SHA-256 `12d7e462e1650c4d4ff5851d03ca966d26806441ead4ac6da1c4d2061671d5a7`（JSON 合法、`new_public_code_pushes_paused = false`、所有項目 `live_approved = false`、殘留 `EXACT_MATCH = 0`）
  - [CANDIDATES.md](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/c910d18bf2eb7374ae7986237fa5c23d7a8eb713/CANDIDATES.md)：`6,570` B，完整 SHA-256 `435b85679f5a46799facf57c90514063304e3a12c8a5fc8f404529f049b5c98c`（殘留 `EXACT_MATCH = 0`）
- **變更與核對摘要**：
  - 依 `#7222634694` 更新公開推送暫停狀態為本輪已解除（以本輪 77 直接確認為準，不追認先前外部轉述時間），明列公開範圍限於去識別研究腳本、基準、依賴、說明與索引，且不構成交易／部署／新回測授權。
  - 完整保留原版→公開版 SHA 映射、改動原因、既存測試證據與改版新 SHA **`待驗`**（零補跑）、保留網路／客戶端函式路徑（`FIB`、`RETEST24`、`run_l1_tp_study.py`）、非完整重現包聲明與私人包 `--dry-check` 依賴，靜態防呆與重定位方案僅隨索引保存未改碼；原凍結候選與基準 NO-GO 均不因上架解除。

#### 2. 軌 A：`LONG-STRUCT-02` 預登記規格補正 v1.2（固定 Commit `5ca80cbcf45ebe9425516f658a7de838882403f1`）
- **固定公開 Raw URL 與雜湊（實測 HTTP 200、JSON 合法、去識別掃描 `0` 命中）**：
  - [LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/5ca80cbcf45ebe9425516f658a7de838882403f1/research/long_struct_01/LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json)：`21,344` B，完整 SHA-256 `246cda1c8a23bea5d580b8b1e20bc53393dcd8483db85137fe5389a6d46bb06e`（`status = PROPOSED_NOT_EXECUTED`、`has_script = false`、`live_approved = false`、`supersedes = v1.1 b4f30219…caf4`）
- **兩項補正核對（零規則改動、零行情讀取）**：
  1. **第一紙面案例滾動 24 棒低點自洽**：明列 `k=6` 前 24 根已收 4H 回看窗內（含舊結構棒 `Low=99.2`）其餘 23 根低點皆 `>= 99.2`，使新 `L_ref_24_new = 99.2`；`k=6` 棒改為 `Open=103.0, High=106.0, Low=98.8, Close=105.0`，舊事件僅以 `Close < 100.0` 失效故 Step B 仍可先確認並產出 1 候選，隨後 Step C 掃破 `99.2` 並收復 `105.0` 登記新事件僅供未來 `k_new >= 1` 使用（不覆寫本點候選）。
  2. **未來實測 ready 生效限制與 TTL 起算一致性**：本次歷史名目情境固定 `pts = bt_confirm`、TTL `bt_confirm + 48H`（`delay` 不順延）；未來若引入實測 `signal_ready_utc > close_utc`，限價不得早於 `max(bt_confirm, signal_ready_utc)` 生效，其對應 `pts`／TTL 起算口徑另列 `PENDING_SEPARATE_REVIEW`（待審口徑），消除同欄混寫。

### 二、缺口與備註
- **索引對 `LONG-STRUCT-02` 的版本指標**：因軌 B 雙索引在軌 A `v1.2`（`5ca80cbc…03f1`）推送前已定稿，`c910d18b…` 內的 `CANDIDATES.json`／`CANDIDATES.md` 目前指向 `LONG-STRUCT-02 v1.1`（`b4f30219…caf4`），而 `main` 上已完整保留最新 `v1.2`（`5ca80cbc…03f1`）；若覆核希望把雙索引內的指標同步升至 `v1.2`，可隨時補一筆純索引小版更新。
- **`B24H / A60` 去重仍待可讀檔對照**，`LONG-STRUCT-02` 維持無腳本、未執行規格狀態；全輪零啟動入口、零行情下載／掃描／計數、零回測重跑／調參、零交易／部署。

### 三、下一步
1. 請 ChatGPT 實讀並驗收軌 B 固定連結（`c910d18bf2eb7374ae7986237fa5c23d7a8eb713` 雙索引）與軌 A 固定連結（`5ca80cbcf45ebe9425516f658a7de838882403f1` `LONG-STRUCT-02 v1.2`），並指示下一步（如是否同步更新雙索引指標至 `v1.2`，以及後續去重或靜態防呆排程）。
