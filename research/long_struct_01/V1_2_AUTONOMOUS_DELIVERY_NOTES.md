# BACKTEST-READINESS-01 v1.2 — Autonomous Strategy & Offline Adapter Delivery

- **Governance Authority**: Issue #1 `#7226128609` (`BACKTEST-READINESS-01 v1.2`) & `#7225850828` (Grok develops & delivers isolated runnable scripts/adapters; ChatGPT runs all independent backtests in its own isolated environment).
- **Status**: Draft only (`live_approved: false` for all items; unmerged; undeployed; zero local market scans or historical backtests performed).

## 1. Short Track (`run_retest24_bounded_backtest.py`, commit `86ba35af90847af2e88e422e020c9a6375c472dd`)
- **`RETEST24_V1_5_FROZEN`**: Exact frozen baseline (`RETEST24_R1_R2_Switchable_v1_5_auditfix.py` + `R1_150U` / `R2_100U` × `cross_1tick` / `delay1bar`) retained unchanged as control.
- **`RETEST24_OPT_01_BEARISH_CLOSE_POS`**: Adds one strictly causal filter on closed 4H breakdown bar `i-1`: `h_prev > l_prev and ((c_prev - l_prev) / (h_prev - l_prev)) <= 0.35`, filtering out lower-wick absorption/hammer breakdowns that drove conservative `delay1bar_cross_1tick` negative expectancy.

## 2. Long-Limit Track (`run_long_struct_bounded_backtest.py`, strict `多單限價`)
All three candidates share the exact same `50,000 USDT` capital, `b6_sim_portable.run_audit_sim_b6` engine, `TransportBlocker`, manifest SHA binding, `--dry-check`, and `EXIT=2` hard refusal on any `miss_8h > 0` as `run_l1_bounded_backtest.py`:

1. **`LONG_STRUCT_01_V1_2_FROZEN`**: Verbatim frozen baseline (`long_struct_01_v1_2_isolated.py`), preserved unchanged as negative-evidence control (`tp=0.025, sl=0.040, ttl=48h`).
2. **`LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT`**: Full runnable implementation of `LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json` (three-stage causal state machine: Step A expire `k > 6` / invalidate `Close < L_ref_old` -> Step B confirm active event `1 <= k <= 6` on `EMA60` + `RSI14 [55, 85]` + 60-day causal gate -> Step C register new structure event for future `k_new >= 1` only; strictly `多單限價` at `L_ref_old`, zero backfill before confirmation).
   - **Historical Baseline Disclosure**: `B24H` and `A60＋量縮` readable source/rule files are unavailable — explicitly marked **「歷史設計對照未完成」**; no deduplication completion or superiority claim is made.
3. **`LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT`**: v1.2 multi-factor trend-continuation **limit-buy (`多單限價`)** alternative designed for stable monthly trade cadence and improved R:R without relying on rare same-bar sweep intersections or overextended `RSI [55, 85]` entries:
   - Uptrend stack: `EMA20 > EMA60 > EMA200` (200-bar warmup) and `EMA60` strictly rising over 6 bars.
   - Momentum reset: `38.0 <= RSI14 <= 58.0` with bullish stabilization (`Close >= EMA60` and `Close > Open or close_pos >= 0.50`).
   - Strict limit buy order anchored at `min(EMA20, Open_bt - 0.25 * ATR14)` within `[0.0005, 0.10]` below `Open_bt`, `ROUND_DOWN` to `tickSz`.
   - Improved default R:R profile: `tp_pct=0.055`, `sl_pct=0.030`, `ttl_hours=36.0`, `max_slots=16`, `risk_per_trade=150.0` (multi-factor attribution belongs to the whole version until ChatGPT runs ablation).

## 3. Verification Performed Locally (Zero Real Market Data)
- `python3 -m py_compile` PASS on `run_long_struct_bounded_backtest.py` and `test_long_struct_bounded_synthetic.py`.
- AST check: zero `assert` statements in runner, zero top-level strategy/engine imports, zero local path or credential leaks.
- `python3 test_long_struct_bounded_synthetic.py`: `ALL_SYNTHETIC_TESTS_PASS` (verifying `LONG_STRUCT_02` Timeline 1 `k=6` + Step C registration, Timeline 2 Step A early invalidation, and `LONG_STRUCT_03` strict below-open limit-order causality).

## 4. Exact Offline CLI Commands for ChatGPT Independent Backtesting
```bash
# 1) Read-only manifest & scope dry-check
python3 research/long_struct_01/code/run_long_struct_bounded_backtest.py \
  --manifest <MANIFEST_JSON> \
  --shared-risk <SHARED_RISK_PY> \
  --cache-dir <CACHE_V3_DIR> \
  --funding-db <FUNDING_SQLITE> \
  --out-dir <ISOLATED_OUT_DIR> \
  --candidate LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT \
  --start-utc 2025-10-01T00:00:00Z \
  --end-utc 2026-10-31T23:30:00Z \
  --dry-check

# 2) Run any of the three long-limit candidates (repeat for LONG_STRUCT_01_V1_2_FROZEN / LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT / LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT)
python3 research/long_struct_01/code/run_long_struct_bounded_backtest.py \
  --manifest <MANIFEST_JSON> \
  --shared-risk <SHARED_RISK_PY> \
  --cache-dir <CACHE_V3_DIR> \
  --funding-db <FUNDING_SQLITE> \
  --out-dir <ISOLATED_OUT_DIR> \
  --candidate LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT \
  --start-utc 2025-10-01T00:00:00Z \
  --end-utc 2026-10-31T23:30:00Z \
  --scenarios cross_1tick,delay1bar
```

## 5. Unverified Items
- Not yet backtested on real historical market data or funding archives (reserved exclusively for ChatGPT's isolated execution).
- Performance, monthly trade cadence, drawdown, and funding sensitivity remain **待 ChatGPT 獨立回測驗證**.
