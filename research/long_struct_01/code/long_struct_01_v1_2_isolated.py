#!/usr/bin/env python3
"""
Isolated candidate builders for LONG-STRUCT-01 v1.2 vs FIB_4H_Long_v3 baseline.
- Strictly offline / pure candidate generation (no execution, no orders, no full replay).
- Enforces explicit deterministic `symbol_order` so Python Timsort stable tie-breaking
  on `-dist` is reproducible across environments.
- Spec reference: LONG_STRUCT_01_PREREG_v1.2.json (SHA b97fd47a...27b9).
"""
from decimal import Decimal as D, ROUND_DOWN
from typing import Dict, List, Sequence, Tuple

H1 = 3_600_000
H4 = 4 * H1
H8 = 8 * H1
DAY = 24 * H1


def indicators_180(closes: Sequence[float]) -> Tuple[float, float]:
    """Exact match to FIB_4H_Long_v3.indicators (EMA60 + Wilder RSI14 on 60..180 closed 4H bars)."""
    ema = sum(closes[:60]) / 60.0
    k = 2.0 / 61.0
    for p in closes[60:]:
        ema = p * k + ema * (1.0 - k)
    diffs = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gain = sum(max(0.0, v) for v in diffs[:14]) / 14.0
    loss = sum(max(0.0, -v) for v in diffs[:14]) / 14.0
    for v in diffs[14:]:
        gain = (gain * 13.0 + max(0.0, v)) / 14.0
        loss = (loss * 13.0 + max(0.0, -v)) / 14.0
    rsi = 100.0 * gain / (gain + loss) if (gain + loss) else 50.0
    return ema, rsi


def _eval_price_and_gate(op: float, raw_input: float, tk_d: D):
    """Exact FIB_4H_Long_v3.py lines 323-327 / run_l1_tp_study.py lines 106-112 order:
    1) round(raw_input, 4)
    2) dist = (op - raw_px) / op  [BEFORE tick alignment]
    3) 0.0005 <= dist <= 0.10
    4) Decimal ROUND_DOWN to tickSz, require px_d > 0
    """
    raw_px = round(raw_input, 4)
    if op <= 0.0:
        return None
    dist = (op - raw_px) / op
    if not (0.0005 <= dist <= 0.10):
        return None
    px_d = (D(str(raw_px)) / tk_d).to_integral_value(rounding=ROUND_DOWN) * tk_d
    if px_d <= 0:
        return None
    return dist, float(px_d)


def build_cands_fib_long_exact(
    raw: Dict[str, dict],
    symbol_order: Sequence[str],
    start_ts: int,
    end_ts: int,
    lookback: int = 24,
    rsi_lo: float = 55.0,
    rsi_hi: float = 85.0,
    entry_level: float = 0.618,
    lev_cfg: float = 10.0,
):
    """Exact FIB_4H_Long_v3 baseline candidate builder with explicit deterministic symbol_order."""
    cands_by_bar: Dict[int, list] = {}
    max_lev: Dict[str, float] = {}
    for inst in symbol_order:
        if inst not in raw:
            continue
        v = raw[inst]
        max_lev[inst] = min(lev_cfg, float(v["maxLever"]))
        ts4, o4, d1_set = v["ts4"], v["o4"], v["d1_set"]
        tk_d = D(str(v["tickSz_str"]))
        ts4_list = [int(x) for x in ts4.tolist()]
        idx_map = {t: idx for idx, t in enumerate(ts4_list)}
        for i in range(60, len(ts4_list)):
            bt = ts4_list[i]
            if bt < start_ts - 48 * H1 or bt > end_ts:
                continue
            recent_idx = []
            for n in range(1, 181):
                j = idx_map.get(bt - n * H4)
                if j is None:
                    break
                recent_idx.append(j)
            if len(recent_idx) < 60:
                continue
            closes = [float(o4[j, 3]) for j in reversed(recent_idx)]
            ema, rsi = indicators_180(closes)
            if closes[-1] <= ema or not (rsi_lo <= rsi <= rsi_hi):
                continue
            day = (bt + H8) // DAY * DAY - H8
            if not all((day - d * DAY) in d1_set for d in range(1, 61)):
                continue
            op = float(o4[i, 0])
            lb_idx = recent_idx[:lookback]
            hi = max([op] + [float(o4[j, 1]) for j in lb_idx])
            lo = min([op] + [float(o4[j, 2]) for j in lb_idx])
            raw_input = hi - (hi - lo) * entry_level
            res = _eval_price_and_gate(op, raw_input, tk_d)
            if res is None:
                continue
            dist, px_f = res
            cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, px_f, False))
    return cands_by_bar, max_lev


def build_cands_long_struct_01_v1_2(
    raw: Dict[str, dict],
    symbol_order: Sequence[str],
    start_ts: int,
    end_ts: int,
    lookback: int = 24,
    rsi_lo: float = 55.0,
    rsi_hi: float = 85.0,
    lev_cfg: float = 10.0,
):
    """Isolated LONG-STRUCT-01 v1.2 candidate builder.
    Identical to build_cands_fib_long_exact on:
      - explicit symbol_order (deterministic Timsort tie-break)
      - 60..180 contiguous closed 4H bars, EMA60, RSI14 [55,85]
      - 60 contiguous closed UTC+8 1D bars validity gate
      - Open_bt reference price, round(..., 4), dist=(op-raw_px)/op, [0.0005, 0.10], Decimal ROUND_DOWN
      - (-dist, 0, inst, px_f, False) tuple format
    Sole entry difference:
      - Signal bar s = recent_idx[0] (just-closed 4H bar [bt-4H, bt))
      - Reference low L_ref = min(Low of recent_idx[1 : 1+lookback]) (strictly prior 24 closed 4H bars)
      - Sweep + bullish reclaim: Low_s < L_ref and Close_s > L_ref and Close_s > Open_s
      - Limit anchor: raw_input = L_ref (NEVER Low_s)
    """
    cands_by_bar: Dict[int, list] = {}
    max_lev: Dict[str, float] = {}
    for inst in symbol_order:
        if inst not in raw:
            continue
        v = raw[inst]
        max_lev[inst] = min(lev_cfg, float(v["maxLever"]))
        ts4, o4, d1_set = v["ts4"], v["o4"], v["d1_set"]
        tk_d = D(str(v["tickSz_str"]))
        ts4_list = [int(x) for x in ts4.tolist()]
        idx_map = {t: idx for idx, t in enumerate(ts4_list)}
        for i in range(60, len(ts4_list)):
            bt = ts4_list[i]
            if bt < start_ts - 48 * H1 or bt > end_ts:
                continue
            recent_idx = []
            for n in range(1, 181):
                j = idx_map.get(bt - n * H4)
                if j is None:
                    break
                recent_idx.append(j)
            if len(recent_idx) < max(60, lookback + 1):
                continue
            closes = [float(o4[j, 3]) for j in reversed(recent_idx)]
            ema, rsi = indicators_180(closes)
            if closes[-1] <= ema or not (rsi_lo <= rsi <= rsi_hi):
                continue
            day = (bt + H8) // DAY * DAY - H8
            if not all((day - d * DAY) in d1_set for d in range(1, 61)):
                continue
            s_idx = recent_idx[0]
            prior_idx = recent_idx[1 : 1 + lookback]
            l_ref = min(float(o4[j, 2]) for j in prior_idx)
            open_s = float(o4[s_idx, 0])
            low_s = float(o4[s_idx, 2])
            close_s = float(o4[s_idx, 3])
            if not (low_s < l_ref and close_s > l_ref and close_s > open_s):
                continue
            op = float(o4[i, 0])
            res = _eval_price_and_gate(op, l_ref, tk_d)
            if res is None:
                continue
            dist, px_f = res
            cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, px_f, False))
    return cands_by_bar, max_lev
