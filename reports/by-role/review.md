# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-27 23:47:51
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7222493032

<!-- comment_id: 7222493032 -->

[復盤] LONG-STRUCT-02 v1.1 規格補正與 CANDIDATE-REGISTRY-01 v1.1-draft 雙軌獨立驗收（對應 #7222274363、#7222311457）

- **角色**：復盤（獨立覆核與彙整）
- **研究編號與版本**：
  - 軌 A：`LONG-STRUCT-02`（`LONG-STRUCT-02-TEMPORAL-SPLIT-DEDUP-PREREG v1.1`，取代 v1.0 `8f9bf553…84d4`）
  - 軌 B：`CANDIDATE-REGISTRY-01 v1.1-draft`（隔離草案，未推送）
- **時間與時區**：2026-11-27 23:48 UTC+8
- **資料截止**：本輪零行情掃描、零計數、零回測重跑或補跑；`LONG-STRUCT-01 v1.2` 維持凍結於 2025-11 UTC 五檔診斷窗。

### 一、完成事項與獨立覆核結果

#### 1. 軌 A：`LONG-STRUCT-02` 預登記規格補正 v1.1（對應 #7222274363）— **已推送並通過 live raw 獨立驗收**
- **公開固定 Commit SHA**：`b4f3021995249b6e6734888ef7af0d871fd7caf4`
- **公開固定 Raw URL**：[LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.1.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/b4f3021995249b6e6734888ef7af0d871fd7caf4/research/long_struct_01/LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.1.json)
- **獨立驗證證據**：HTTP 200、`18,883` B、完整 SHA-256 `a074978776176189cfc581537b318e61c190dda9a3d7e7e12ad549c4a68042be`、JSON 合法、去識別掃描 `0` 命中（零本機路徑／密鑰）、`status = PROPOSED_NOT_EXECUTED`、`has_script = false`、`live_approved = false`。
- **四項補正逐項確認**：
  1. **同決策點三階段固定順序**：Step A 先判舊事件逾期／失效（明確 `k=6` 可確認、`k>6` 才逾期）→ Step B 確認仍有效舊事件 → Step C 登記新結構事件供未來 `k>=1`；明定舊事件本點已產候選時新事件不得追溯覆寫，每標的每決策點最多 1 候選。
  2. **`close_utc` 與 `available_after_utc` 分欄**：明標 `close_utc == available_after_utc` 為「歷史名目可用假設」（非實測收件／訊號 ready），限定 `Open_bt` 須於已觀測後使用且限價不得早於未來實測 ready 生效；保留 `cross` 首棒樂觀／未解與 `delay` 一棒敏感度標籤，不宣稱秒級因果驗證。
  3. **兩條純紙面合成時間線（零行情）**：① 舊事件於 `k=6` 確認且同棒出現新事件（本點產 1 候選、新事件僅登記供未來 `k>=1`）；② 確認棒 `Close < L_ref` 於 Step A 先行失效（跳過 Step B、產 0 候選）。
  4. **去重用詞精準化**：`L1 / LONG-LOOP` 僅述書面規則結構差異、不宣稱已證實訊號集合不重疊；`10 日假跌破`、`B24H` 與 `A60＋量縮` 均明標尚待外部／可讀檔對照，不寫成完整去重通過。

#### 2. 軌 B：`CANDIDATE-REGISTRY-01 v1.1-draft` 隔離雙索引補正草案（對應 #7222311457）— **隔離複驗通過，維持未推送**
- **覆核紀錄**：首輪獨立檢查檢出 `CANDIDATES.json` 的 `offline_engine_dependencies` 仍殘留 v1.0 舊字樣（`EXACT_MATCH`、缺 `provenance`、`run_l1_tp_study.py` 漏列保留網路函式與 `PACK_ROOT` 依賴）且 `proposed_hypotheses[0]` 仍指 v1.0，已退回修補並完成二輪複驗。
- **二輪複驗通過之隔離草案雜湊（未推送、零本機路徑／密鑰）**：
  - `CANDIDATES.json`（隔離草案）：`30,862` B，完整 SHA-256 `cc8ecd58655ce10d06e7e8885e0d597dff4b29cfc2ca16025e9cb3b386a5b939`（JSON 合法、`EXACT_MATCH` 殘留 `0` 次、去識別掃描 `0` 命中）
  - `CANDIDATES.md`（隔離草案）：`6,215` B，完整 SHA-256 `6936481b70cff33719c5785a0ac029b74b0249fba16e645149915c8894875415`（`EXACT_MATCH` 殘留 `0` 次、去識別掃描 `0` 命中）
- **四項補正逐項確認**：
  1. **表述與治理邊界修正**：`LONG-STRUCT-01` 嚴格限縮為「該五檔十一月樣本同棒交集為零」；明註 ChatGPT 接受的是檔案／雜湊／報表核對與停止決策，而非獨立重現改版公開副本；`proposed_hypotheses[0]` 與 Markdown 已同步對齊剛驗收之 `LONG-STRUCT-02 v1.1`（`b4f30219…caf4`、`a0749787…42be`）並明標 `B24H / A60` 去重未完成；`new_public_code_pushes_paused = true`、`public_code_dir_is_complete_repro_pack = false`。
  2. **原版 → 公開副本逐檔映射與誠實標「待驗」**：
     - `FIB_4H_Long_v3.py`（`c52ea221…dbe9` → `75891548…aaba`）與 `RETEST24_R1_R2_Switchable_v1_5_auditfix.py`（`949a86f5…c15c` → `c48e2928…9d19`）均明標原版回歸不可等同新 SHA 通過，新 SHA 標 **`待驗`**。
     - `engine/b6_sim_portable.py`（`b4b81446…3972`）與 `engine/sim_50k_v3_2_sl_fix.py`（`1d2aebf5…da7ca`）標明與私人包原檔逐位元組相同；其餘三份去路徑改版檔（`engine/audit_v3_1_full.py` `8ef7c513…` → `b4b264ef…`、`engine/run_q38_audit_01.py` `0cb653f9…` → `47efa8ac…`、`run_l1_tp_study.py` `f98af4eb…` → `e5a67230…`）因先前未保存新 SHA 執行紀錄與輸出雜湊，不補跑並全數改標 **`待驗`**（舊私人包基準雜湊僅作參照）；`requirements.txt` 亦移除 `EXACT_MATCH` 字樣。
  3. **保留之網路／客戶端函式路徑與靜態防呆方案**：明列 `FIB`（`urllib.request.urlopen` L206/L241、`HOST` L29）、`RETEST24`（`OkxClient` L419、`BASE_URL` L221）、`run_l1_tp_study.py`（`fetch_okx_funding` L217、`urlopen` L223、`backfill_missing_funding` L242），絕不宣稱完全無連線程式碼，並記錄未來核准改碼時之離線硬阻斷與 `--offline-only` 靜態防呆方案。
  4. **`run_l1_tp_study.py --dry-check` 依賴與重定位方案**：明列 `PACK_ROOT/REPRO_MANIFEST.json`（`3dacf887…9874`）、`PACK_ROOT/scripts/shared_risk.py`（`3bbb11a8…2296`）、`PACK_ROOT/scripts/FIB_4H_Long_v3.py`（`c52ea221…dbe9`）均完整存於既有私人包（非缺件），同時聲明目前公開 `research/long_struct_01/code/` 10 檔**非**可直接執行 `--dry-check` 或全期重現之完整包，並於草案詳列 `--manifest`／`--shared-risk` 重定位方案（待核准前不動碼）。

### 二、缺口與紅線狀態
- **公開完整碼推送維持暫停**：依 #7222311457，在 ChatGPT 尚未收到 77 本人直接確認公開完整碼範圍前，暫停任何新增完整碼公開推送，亦**不刪庫、不改可見性、不重寫歷史**。
- **軌 B 雙索引草案暫留隔離區**：未推送至公開 repo，待 ChatGPT 覆核本回報及 77 核准後再決定是否推送 v1.1 雙索引。
- **零未授權動作**：全輪零行情掃描／計數／回測重跑／調參／交易／部署，所有項目均 `live_approved: false`。

### 三、下一步
1. 請 ChatGPT 覆核軌 A（`LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.1.json`，commit `b4f3021995249b6e6734888ef7af0d871fd7caf4`）是否滿足 #7222274363 全部規格要求。
2. 請 ChatGPT 覆核軌 B（`CANDIDATE-REGISTRY-01 v1.1-draft`）四項補正內容；待 77 本人直接確認公開碼範圍與推送指示後，再行決定是否推送雙索引 v1.1 或進行後續靜態防呆／重定位改碼。
