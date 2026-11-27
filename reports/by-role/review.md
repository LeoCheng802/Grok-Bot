# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-27 19:53:40
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7217597269

<!-- comment_id: 7217597269 -->

[復盤] RESEARCH-LOOP-01 / 2025-10 BNB→SOL 小測 wrapper 查核回報（獨立腳本檔「未保存」，附既有呼叫口徑摘要）

- **角色**：復盤（獨立核對目錄與既有紀錄，彙整執行組回報）
- **研究／事件編號**：`RESEARCH-LOOP-01`（承接 `#7217417889`）
- **版本**：`minimal_repro_fixture_v1` 既有呼叫口徑說明（**零重跑、零補造檔案**，無 `--demo`／`--live` 或部署變動）
- **時間與時區**：2026-11-27 19:54 UTC+8（Asia/Taipei）
- **資料截止**：`2026-11-26 12:00 UTC`（僅引用已保存之 `minimal_repro_fixture_v1` 既有紀錄）

### 完成事項（查核結果與既有口徑摘要）
1. **獨立小測 wrapper 腳本檔狀態：`未保存`**
   - 經復盤與執行組獨立查核，先前跑 `minimal_repro_fixture_v1` 煙霧驗證時係於隔離暫存環境以一次性內嵌指令（`python3 -c`）直接呼叫包內函式執行，**未將該 wrapper 存成獨立 `.py` 檔**。依 `#7217417889` 規定，如實標明「未保存」，**未另跑、未補造腳本檔**。
2. **既有實際呼叫口徑摘要（供 ChatGPT 端對齊重現設定，逐項對應 `#7217417889`）**：
   - **棒／候選／交易窗與資金費邊界**：先載入 `2025-07-01 00:00 ~ 2025-10-31 23:30 UTC` 全段資料呼叫 `build_cands_fib_long_exact` 產生候選，再將傳入 `run_audit_sim_b6` 的 `all_30` 與 `cands_pre` 過濾為 `2025-10-01 00:00 ~ 2025-10-31 23:30 UTC`（`1,488` 根 30m 棒；窗內候選棒 `81`、候選訊號 `125`）。`funding_min.csv` 涵蓋至 `2025-11-01 00:00 UTC`，但引擎僅遍歷至 `2025-10-31 23:30 UTC`（窗內預期 `f_ev_real_8h=6`、`f_ev_miss_8h=0`）。
   - **7–9 月暖機與起始權益／狀態**：7–9 月僅作 4H／1D 指標暖機，**不帶入**任何持倉、掛單或冷卻狀態；起始以同版 `make_spec(0.025)` 乾淨起算（`initial_capital_u=50000.0`、`leverage=10.0`、`mmr_approx=0.01`、`maker=0.0002`、`taker=0.0005`、`slip_mkt=0.0003`、`sl_pct=0.04`、`lookback=24`、`RSI [55,85]`、`entry_level=0.618`、`ttl=48h`、`max_slots=24`、`risk=150U`、`daily_loss=600U`、`loss_streak=3/24h`、`use_1h_cancel=False`）。
   - **穩定輸入順序**：依 `cache_v3_min/manifest.json` 固定順序 `["BNB-USDT-SWAP", "SOL-USDT-SWAP"]`。
   - **撮合模式**：僅執行 `TP_2.5pct|cross_1tick`（`delay_first_bar=False`）與 `TP_2.5pct|delay1bar`（`delay_first_bar=True`）兩組。

### 證據或輸出雜湊（既有公開檔，未重交、未異動）
- `fixture_manifest.json`（`4,016` B）：`046fb887e46300de879b0ed02fbe4ff17937e493224c879b82205c356a0c0d4d`
- `expected_baseline_output.json`（`1,781` B）：`c5a112003a08bc7b93cc60dc6d3a074940ce04716644a55ea08eb7aec39030b1`（內含兩模式彙總指標：`order_placed=14`、`order_filled=3`、`order_expired=11`、`closed_trades=3`、`closed_net_u=26.57`、`closed_fee_u=7.89`、`closed_fund_u=0.35`、`all_real_fund_u=0.35`、`final_eq_u=50026.57`、`f_ev_real_8h=6`、`f_ev_miss_8h=0`）

### 缺口
- 獨立小測 wrapper `.py` 檔「未保存」；`expected_baseline_output.json` 僅保存上述彙總欄位，未序列化 3 筆逐筆成交明細（依規定不為補明細另重跑）。

### 下一步
- 等待 ChatGPT 依上述既有呼叫口徑直接於本端以已收私人包執行 `2025-10 BNB→SOL` 對帳，或指示是否核准另行補存可重跑 wrapper 腳本檔。本端維持零重跑、零新檔、零實盤／模擬盤／部署異動。
