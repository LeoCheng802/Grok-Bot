# RETEST24-OPT-01 v1.0｜凍結基準離線 Adapter 與單一假說隔離優化提案

- **研究編號**：`BACKTEST-READINESS-01 v1.1`（對應 Issue #1 `#7225850828`）
- **狀態**：`PROPOSED_UNBACKTESTED`｜`live_approved: false`｜**尚未由 ChatGPT 獨立回測**
- **基準 ID**：`RETEST24-R1-R2 v1.5`（凍結不動，SHA-256 `c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04`）
- **候選 ID**：`RETEST24-OPT-01 v1.0`（`RETEST24_OPT_01_BEARISH_CLOSE_POS`）
- **對齊介面**：與 `run_l1_bounded_backtest.py`（`da65fe4dbdd549aa973e4e3f2c69447b53dcb64a`）採同一有界參數、外層 `TransportBlocker`、路徑互斥與缺費 `EXIT=2` 硬拒絕規範。

## 1. 唯一主要假說與變更差異

- **問題根因**：`RETEST24-R1-R2 v1.5` 僅要求前一根 4H 跌破棒收盤 `c_prev < pl` 且本棒開盤 `op < pl`，未區分「實體弱勢收低」與「長下影線／買盤吸收反彈」。既有 `B6` 負證據顯示在保守 1-bar 延遲進場（`delay1bar_cross_1tick`）下原訊號優勢翻負。
- **唯一新增條件（嚴格因果，僅用已收盤 4H 棒 `i-1`）**：
  - `h_prev > l_prev` 且 `(c_prev - l_prev) / (h_prev - l_prev) <= 0.35`（跌破棒須收在自身振幅下 35% 區間內）。
- **完全不變項**：`EMA55`、`RSI14 [20, 40]`、60 日因果 D1 暖機、`lookback=12`、`entry_offset_mult=0.9995`、`dist∈[0, 0.15]`、`TP=5%`、`SL=5%`、`TTL=24h`、`R1 (150U/600U)` 與 `R2 (100U/400U)` 倉位對照、費用／滑價／資金費與 `shared_risk` 公式全數原樣保留。

## 2. 既有研究去重

- 不重複 `B1`（EMA55）、`B2`（TTL）、`B3`（RSI 區間）、`B4`（進場 offset）、`B5`（觸價／穿價）、`B6`（1-bar 延遲）、`B7/B8`（tick／出場順序）與 `R1/R2` 倉位對照；屬嚴格收緊訊號品質，非放寬條件衝交易量。

## 3. ChatGPT 獨立隔離執行命令

### 3.1 Manifest 前置乾跑（不載入策略／引擎）
```bash
python3 research/long_struct_01/code/run_retest24_bounded_backtest.py \
  --manifest <PACK_ROOT>/REPRO_MANIFEST.json \
  --retest24-script <PACK_ROOT>/scripts/RETEST24_R1_R2_Switchable_v1_5_auditfix.py \
  --shared-risk <PACK_ROOT>/scripts/shared_risk.py \
  --candidate RETEST24_V1_5_FROZEN \
  --dry-check
```

### 3.2 凍結基準 `RETEST24-R1-R2 v1.5` 有界回測
```bash
python3 research/long_struct_01/code/run_retest24_bounded_backtest.py \
  --manifest <PACK_ROOT>/REPRO_MANIFEST.json \
  --retest24-script <PACK_ROOT>/scripts/RETEST24_R1_R2_Switchable_v1_5_auditfix.py \
  --shared-risk <PACK_ROOT>/scripts/shared_risk.py \
  --cache-dir <CACHE_V3_DIR> \
  --funding-db <FUNDING_DB_SQLITE> \
  --out-dir <OUT_DIR_BASE> \
  --start-utc 2023-01-01T00:00:00Z \
  --end-utc 2026-11-26T12:00:00Z \
  --scenarios 'R1_150U|cross_1tick,R1_150U|delay1bar,R2_100U|cross_1tick,R2_100U|delay1bar' \
  --candidate RETEST24_V1_5_FROZEN
```

### 3.3 隔離候選 `RETEST24-OPT-01 v1.0` 有界回測
```bash
python3 research/long_struct_01/code/run_retest24_bounded_backtest.py \
  --manifest <PACK_ROOT>/REPRO_MANIFEST.json \
  --retest24-script <PACK_ROOT>/scripts/RETEST24_R1_R2_Switchable_v1_5_auditfix.py \
  --shared-risk <PACK_ROOT>/scripts/shared_risk.py \
  --cache-dir <CACHE_V3_DIR> \
  --funding-db <FUNDING_DB_SQLITE> \
  --out-dir <OUT_DIR_OPT01> \
  --start-utc 2023-01-01T00:00:00Z \
  --end-utc 2026-11-26T12:00:00Z \
  --scenarios 'R1_150U|cross_1tick,R1_150U|delay1bar,R2_100U|cross_1tick,R2_100U|delay1bar' \
  --candidate RETEST24_OPT_01_BEARISH_CLOSE_POS
```

## 4. 靜態檢查紀錄與未驗證聲明

- `run_retest24_bounded_backtest.py`：`33881` B｜SHA-256 `19c2fe0d3ae1f2b7e06950318293175fe5b264420144e9790c075b99b3dac2da`｜`py_compile` PASS｜AST `assert=0`｜頂層零策略／`shared_risk`／引擎 import｜零本機路徑／憑證外洩。
- `RETEST24_OPT_01_PREREG_v1.0.json`：`5471` B｜SHA-256 `81f6882cda59f0f5db6977b5943bcc10a90df8b8284a3d4848cf44398f7b9b83`。
- **未驗證聲明**：Grok／策略組**未執行**任何行情掃描、歷史計數或績效回測；上述基準與候選均待 ChatGPT 於隔離環境獨立回測與裁示。
