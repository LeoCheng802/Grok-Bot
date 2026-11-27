#!/usr/bin/env python3
"""
BACKTEST-READINESS-01 v1.2 — Bounded Offline Long-Limit Strategy Adapter.

Supports three strictly-causal long-limit (多單限價) candidates on the exact
same 50,000U common-capital, cost, and b6_sim_portable engine contract as
run_l1_bounded_backtest.py:
  1. LONG_STRUCT_01_V1_2_FROZEN
     Verbatim frozen baseline from long_struct_01_v1_2_isolated.py
     (same-bar 24-bar liquidity sweep + bullish reclaim + EMA60 + RSI14 [55,85],
     limit at L_ref). Preserved unchanged as negative-evidence control.
  2. LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT
     Runnable implementation of LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json:
     strictly causal 3-stage state machine at each closed 4H decision point bt:
       Step A: expire (k > 6) or invalidate (Close < L_ref_old) active pending event
       Step B: confirm active event (1 <= k <= 6) on EMA60 + RSI14 [55,85] + 60x1 gate;
               if confirmed, mark consumed and evaluate limit price L_ref_old vs Open_bt
       Step C: register new structure sweep+reclaim event for future k_new >= 1 only
      Historical baseline comparison note: B24H and A60+量縮 readable artifacts
     are unavailable ("歷史設計對照未完成"); no deduplication or superiority claim.
  3. LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT
     v1.2 multi-factor trend-continuation long-limit alternative:
       - Closed 4H uptrend: EMA20 > EMA60 > EMA200 (200-bar warmup) and EMA60 rising over 6 bars
       - Healthy pullback momentum reset: 38.0 <= RSI14 <= 58.0
       - Bullish stabilization: Close >= EMA60 and (Close > Open or Close_pos >= 0.50)
       - Strict limit buy order anchored at min(EMA20, Open_bt - 0.25 * ATR14)
       - Default improved R:R exit profile: tp_pct=0.055, sl_pct=0.030, ttl_hours=36.0, max_slots=16
       (Attribution belongs to the whole version until ChatGPT runs ablation.)

Offline governance guarantees:
  - Zero top-level strategy / engine / shared_risk imports (manifest verified first).
  - TransportBlocker active for the entire run (zero network calls).
  - Isolated read-only funding DB copy + unified input/output path disjointness check.
  - Hard abort (exit 2) on ANY miss_8h > 0; zero-fill / interpolation forbidden.
  - --dry-check verifies manifest & scope without importing runtime modules.
"""
import argparse
import hashlib
import http.client
import importlib.util
import json
import os
import shutil
import socket
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

H1 = 3_600_000
H4 = 4 * H1
H8 = 8 * H1
DAY = 24 * H1
TZ_UTC = timezone.utc

SUPPORTED_CANDIDATES = (
    "LONG_STRUCT_01_V1_2_FROZEN",
    "LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT",
    "LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT",
)

SUPPORTED_SCENARIOS = {
    "cross_1tick": False,
    "delay1bar": True,
}

DEFAULT_EXIT_BY_CANDIDATE = {
    "LONG_STRUCT_01_V1_2_FROZEN": {
        "tp_pct": 0.025,
        "sl_pct": 0.040,
        "ttl_hours": 48.0,
        "max_slots": 24,
        "risk_per_trade": 150.0,
    },
    "LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT": {
        "tp_pct": 0.025,
        "sl_pct": 0.040,
        "ttl_hours": 48.0,
        "max_slots": 24,
        "risk_per_trade": 150.0,
    },
    "LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT": {
        "tp_pct": 0.055,
        "sl_pct": 0.030,
        "ttl_hours": 36.0,
        "max_slots": 16,
        "risk_per_trade": 150.0,
    },
}


class TransportBlockedError(RuntimeError):
    pass


class TransportBlocker:
    """Blocks all outbound socket / HTTP / urllib connections during offline runs."""

    def __init__(self):
        self.hits: List[str] = []
        self._orig: Dict[str, object] = {}

    def _deny(self, label: str):
        def _fn(*args, **kwargs):
            self.hits.append(label)
            raise TransportBlockedError(f"Offline transport blocked: {label}")
        return _fn

    def __enter__(self):
        self._orig = {
            "create_connection": socket.create_connection,
            "socket_connect": socket.socket.connect,
            "socket_connect_ex": socket.socket.connect_ex,
            "urlopen": urllib.request.urlopen,
            "http_connect": http.client.HTTPConnection.connect,
            "https_connect": http.client.HTTPSConnection.connect,
        }
        socket.create_connection = self._deny("socket.create_connection")
        socket.socket.connect = self._deny("socket.socket.connect")
        socket.socket.connect_ex = self._deny("socket.socket.connect_ex")
        urllib.request.urlopen = self._deny("urllib.request.urlopen")
        http.client.HTTPConnection.connect = self._deny("http.client.HTTPConnection.connect")
        http.client.HTTPSConnection.connect = self._deny("http.client.HTTPSConnection.connect")
        return self

    def __exit__(self, exc_type, exc, tb):
        socket.create_connection = self._orig["create_connection"]
        socket.socket.connect = self._orig["socket_connect"]
        socket.socket.connect_ex = self._orig["socket_connect_ex"]
        urllib.request.urlopen = self._orig["urlopen"]
        http.client.HTTPConnection.connect = self._orig["http_connect"]
        http.client.HTTPSConnection.connect = self._orig["https_connect"]
        return False


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_utc_ms(iso_str: str) -> int:
    s = iso_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("Timestamp must include timezone (e.g. Z or +00:00): " + iso_str)
    return int(round(dt.astimezone(TZ_UTC).timestamp() * 1000))


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _norm_path(p: Path) -> str:
    return str(p.expanduser().resolve(strict=False))


def _verify_output_paths_disjoint(outputs: Sequence[Tuple[str, Path]], fixed_inputs: Sequence[Tuple[str, Path]]) -> None:
    input_map = {_norm_path(p): label for label, p in fixed_inputs}
    seen_out: Dict[str, str] = {}
    for label, p in outputs:
        npth = _norm_path(p)
        if npth in input_map:
            raise RuntimeError(f"Output path '{label}' collides with fixed input '{input_map[npth]}': {npth}")
        if npth in seen_out:
            raise RuntimeError(f"Output path '{label}' duplicates '{seen_out[npth]}': {npth}")
        seen_out[npth] = label


def _discard_final_report(final_report: Path, fixed_inputs: Sequence[Tuple[str, Path]]) -> None:
    targets = [final_report, Path(str(final_report) + ".tmp")]
    input_norms = {_norm_path(p) for _, p in fixed_inputs}
    for t in targets:
        if _norm_path(t) in input_norms:
            raise RuntimeError("Refusing to unlink path colliding with fixed input: " + str(t))
    for t in targets:
        if t.exists():
            t.unlink()


def _verify_manifest_bindings(manifest_path: Path, shared_risk_path: Path) -> dict:
    if not manifest_path.is_file():
        raise RuntimeError("Manifest not found: " + str(manifest_path))
    m_root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files_spec = manifest.get("files") or {}
    if not isinstance(files_spec, dict) or not files_spec:
        raise RuntimeError("Manifest missing non-empty 'files' mapping")

    verified_files: Dict[str, Path] = {}
    verified_shas: Dict[str, str] = {}
    for rel, meta in files_spec.items():
        expected_sha = meta["sha256"] if isinstance(meta, dict) else str(meta)
        fpath = (m_root / rel).resolve()
        if not fpath.is_file():
            raise RuntimeError(f"Manifest file missing: {rel}")
        actual_sha = sha(fpath)
        if actual_sha != expected_sha:
            raise RuntimeError(f"Manifest SHA mismatch for {rel}: expected {expected_sha}, got {actual_sha}")
        verified_files[rel] = fpath
        verified_shas[rel] = actual_sha

    if not shared_risk_path.is_file():
        raise RuntimeError("shared_risk.py not found: " + str(shared_risk_path))
    sr_resolved = shared_risk_path.resolve()
    sr_sha = sha(sr_resolved)
    if sr_sha not in verified_shas.values():
        raise RuntimeError("shared_risk.py SHA not registered in manifest: " + sr_sha)

    b6_candidates = [p for rel, p in verified_files.items() if rel.endswith("b6_sim_portable.py")]
    if not b6_candidates:
        raise RuntimeError("Manifest does not register b6_sim_portable.py")

    return {
        "manifest": manifest_path.resolve(),
        "manifest_root": m_root,
        "files": verified_files,
        "files_verified": len(verified_files),
        "roles": {
            "shared_risk": sr_resolved,
            "b6_sim_portable": b6_candidates[0],
        },
    }


def _load_runtime_modules(bound: dict) -> dict:
    b6_path = bound["roles"]["b6_sim_portable"]
    engine_dir = str(b6_path.parent)
    sr_dir = str(bound["roles"]["shared_risk"].parent)
    for d in (engine_dir, sr_dir):
        if d not in sys.path:
            sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("b6_sim_portable", str(b6_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load b6_sim_portable from " + str(b6_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {"b6_sim_portable": mod}


def _bind_isolated_funding_db(src_db: Path, dst_db: Path, meta_path: Path) -> None:
    if not src_db.is_file():
        raise RuntimeError("Source funding DB missing: " + str(src_db))
    src_sha = sha(src_db)
    shutil.copy2(src_db, dst_db)
    dst_sha = sha(dst_db)
    if dst_sha != src_sha:
        raise RuntimeError("Isolated funding DB copy SHA mismatch")
    _atomic_write_text(meta_path, json.dumps({
        "source_sha256": src_sha,
        "isolated_copy_sha256": dst_sha,
        "copied_utc": datetime.now(TZ_UTC).isoformat(),
    }, ensure_ascii=False, indent=2) + "\n")


def load_funding_db(db_path: Path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    fmaps: Dict[str, Dict[int, float]] = {}
    ov_raw: Dict[str, Dict[int, int]] = {}
    for inst, ts_grid, ts_raw, rate in conn.execute("SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive"):
        fmaps.setdefault(inst, {})[int(ts_grid)] = float(rate)
        ov_raw.setdefault(inst, {})[int(ts_grid)] = int(ts_raw)
    conn.close()
    return fmaps, ov_raw


# -------------------------------------------------------------------------
# Pure causal indicators & price gate (zero lookahead)
# --------------------------------------------------------------------------

def ema_series(closes: Sequence[float], period: int) -> List[float]:
    if len(closes) < period:
        raise ValueError(f"Need at least {period} closes for EMA{period}")
    ema = sum(closes[:period]) / float(period)
    k = 2.0 / (period + 1.0)
    out = [ema]
    for p in closes[period:]:
        ema = p * k + ema * (1.0 - k)
        out.append(ema)
    return out


def indicators_ema60_rsi14(closes: Sequence[float]) -> Tuple[float, float]:
    """Exact match to FIB_4H_Long_v3 / long_struct_01_v1_2_isolated.indicators_180."""
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


def wilder_atr14(o4_window: Sequence[Sequence[float]]) -> float:
    """Wilder ATR(14) over closed 4H OHLC bars (at least 15 bars)."""
    trs: List[float] = []
    for idx in range(1, len(o4_window)):
        h = float(o4_window[idx][1])
        l = float(o4_window[idx][2])
        pc = float(o4_window[idx - 1][3])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < 14:
        return sum(trs) / max(1, len(trs))
    atr = sum(trs[:14]) / 14.0
    for tr in trs[14:]:
        atr = (atr * 13.0 + tr) / 14.0
    return atr


def eval_limit_price_and_gate(op: float, raw_input: float, tk_d: D, min_dist: float = 0.0005, max_dist: float = 0.10):
    """Strict long-limit (多單限價) price alignment & distance gate below Open_bt."""
    raw_px = round(raw_input, 4)
    if op <= 0.0 or raw_px <= 0.0:
        return None
    dist = (op - raw_px) / op
    if not (min_dist <= dist <= max_dist):
        return None
    px_d = (D(str(raw_px)) / tk_d).to_integral_value(rounding=ROUND_DOWN) * tk_d
    if px_d <= 0 or float(px_d) >= op:
        return None
    return dist, float(px_d)


def _contiguous_recent_indices(idx_map: Dict[int, int], bt: int, max_bars: int) -> List[int]:
    recent: List[int] = []
    for n in range(1, max_bars + 1):
        j = idx_map.get(bt - n * H4)
        if j is None:
            break
        recent.append(j)
    return recent


def _has_60d_causal_gate(bt: int, d1_set: set) -> bool:
    day = (bt + H8) // DAY * DAY - H8
    return all((day - d * DAY) in d1_set for d in range(1, 61))


# -------------------------------------------------------------------------
# Candidate 1: LONG_STRUCT_01_V1_2_FROZEN (verbatim control)
# --------------------------------------------------------------------------

def build_cands_long_struct_01_frozen(
    raw: Dict[str, dict],
    symbol_order: Sequence[str],
    start_ts: int,
    end_ts: int,
    lookback: int = 24,
    rsi_lo: float = 55.0,
    rsi_hi: float = 85.0,
    lev_cfg: float = 10.0,
):
    cands_by_bar: Dict[int, list] = {}
    max_lev: Dict[str, float] = {}
    diag = {"candidate": "LONG_STRUCT_01_V1_2_FROZEN", "signals": 0}
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
            recent_idx = _contiguous_recent_indices(idx_map, bt, 180)
            if len(recent_idx) < max(60, lookback + 1):
                continue
            closes = [float(o4[j, 3]) for j in reversed(recent_idx)]
            ema, rsi = indicators_ema60_rsi14(closes)
            if closes[-1] <= ema or not (rsi_lo <= rsi <= rsi_hi):
                continue
            if not _has_60d_causal_gate(bt, d1_set):
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
            res = eval_limit_price_and_gate(op, l_ref, tk_d)
            if res is None:
                continue
            dist, px_f = res
            cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, px_f, False))
            diag["signals"] += 1
    return cands_by_bar, max_lev, diag


# -------------------------------------------------------------------------
# Candidate 2: LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT (prereg v1.2 runnable)
# --------------------------------------------------------------------------

def build_cands_long_struct_02_temporal_split(
    raw: Dict[str, dict],
    symbol_order: Sequence[str],
    start_ts: int,
    end_ts: int,
    lookback: int = 24,
    horizon_bars: int = 6,
    rsi_lo: float = 55.0,
    rsi_hi: float = 85.0,
    lev_cfg: float = 10.0,
):
    """
    Exact runnable implementation of LONG_STRUCT_02_TEMPORAL_SPLIT_DEDUP_PREREG_v1.2.json.
    Three-stage deterministic state machine at each closed 4H decision point bt:
      Step A: expire (k > 6) or invalidate (Close_prev < L_ref_old) pending event.
      Step B: if pending event still active (1 <= k <= 6), evaluate EMA60 + RSI14 [55,85]
              + 60-day causal gate. If confirmed, consume pending event and evaluate
              limit price L_ref_old vs Open_bt ([0.0005, 0.10], ROUND_DOWN to tickSz).
              If k == 6 and not confirmed, naturally expire at end of Step B.
      Step C: evaluate whether just-closed bar [bt - 4H, bt) forms a new structure
              event (Low < L_ref_new, Close > L_ref_new, Close > Open).
              Register for future k_new >= 1 ONLY; never overwrite Step B output.
    """
    cands_by_bar: Dict[int, list] = {}
    max_lev: Dict[str, float] = {}
    diag = {
        "candidate": "LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT",
        "historical_baseline_comparison": "歷史設計對照未完成（B24H 與 A60＋量縮缺可讀原檔，不宣稱已完成去重或優於缺少的對照）",
        "events_registered": 0,
        "expired_over_window": 0,
        "invalidated_close_below_L_ref": 0,
        "confirmed_total": 0,
        "consumed_price_gate_failed": 0,
        "signals": 0,
    }
    warmup_start = start_ts - (48 + horizon_bars * 4) * H1
    for inst in symbol_order:
        if inst not in raw:
            continue
        v = raw[inst]
        max_lev[inst] = min(lev_cfg, float(v["maxLever"]))
        ts4, o4, d1_set = v["ts4"], v["o4"], v["d1_set"]
        tk_d = D(str(v["tickSz_str"]))
        ts4_list = [int(x) for x in ts4.tolist()]
        idx_map = {t: idx for idx, t in enumerate(ts4_list)}

        # pending_event: {"t_struct": int, "l_ref": {float}} or None
        pending: Optional[dict] = None

        for i in range(lookback + 1, len(ts4_list)):
            bt = ts4_list[i]
            if bt < warmup_start or bt > end_ts:
                continue

            # Just-closed bar s = [bt - 4H, bt) must be strictly contiguous
            s_idx = idx_map.get(bt - H4)
            if s_idx is None:
                pending = None
                continue

            open_s = float(o4[s_idx, 0])
            low_s = float(o4[s_idx, 2])
            close_s = float(o4[s_idx, 3])

            # ---- Step A: Invalidate or expire existing pending event ----
            if pending is not None:
                diff_ms = bt - pending["t_struct"]
                if diff_ms <= 0 or (diff_ms % H4)!= 0:
                    pending = None
                else:
                    k = diff_ms // H4
                    if k > horizon_bars:
                        diag["expired_over_window"] += 1
                        pending = None
                    elif close_s < pending["l_ref"]:
                        diag["invalidated_close_below_L_ref"] += 1
                        pending = None

            # ---- Step B: Confirm still-active pending event (1 <= k <= horizon_bars) ----
            if pending is not None:
                k = (bt - pending["t_struct"]) // H4
                if 1 <= k <= horizon_bars:
                    recent_idx = _contiguous_recent_indices(idx_map, bt, 180)
                    confirmed_now = False
                    if len(recent_idx) >= 60 and _has_60d_causal_gate(bt, d1_set):
                        closes = [float(o4[j, 3]) for j in reversed(recent_idx)]
                        ema60, rsi14 = indicators_ema60_rsi14(closes)
                        if closes[-1] > ema60 and (rsi_lo <= rsi14 <= rsi_hi):
                            confirmed_now = True

                    if confirmed_now:
                        diag["confirmed_total"] += 1
                        l_ref_old = pending["l_ref"]
                        pending = None  # consumed immediately
                        if bt >= start_ts - 48 * H1:
                            op = float(o4[i, 0])
                            res = eval_limit_price_and_gate(op, l_ref_old, tk_d)
                            if res is not None:
                                dist, px_f = res
                                cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, px_f, False))
                                diag["signals"] += 1
                            else:
                                diag["consumed_price_gate_failed"] += 1
                    elif k == horizon_bars:
                        # k == 6 did not confirm -> naturally expires at end of Step B
                        diag["expired_over_window"] += 1
                        pending = None

            # ---- Step C: Register new structure event for future k_new >= 1 ----
            recent_for_struct = _contiguous_recent_indices(idx_map, bt, lookback + 1)
            if len(recent_for_struct) >= lookback + 1:
                prior_idx = recent_for_struct[1 : 1 + lookback]
                l_ref_new = min(float(o4[j, 2]) for j in prior_idx)
                if low_s < l_ref_new and close_s > l_ref_new and close_s > open_s:
                    # Strictly for future k_new >= 1; never overwrites Step B's emitted candidate
                    pending = {"t_struct": bt, "l_ref": l_ref_new}
                    diag["events_registered"] += 1

    return cands_by_bar, max_lev, diag


# --------------------------------------------------------------------------
# Candidate 3: LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT (v1.2 multi-factor)
# ---------------------------------------------------------------------------

def build_cands_long_struct_03_ema_pullback_limit(
    raw: Dict[str, dict],
    symbol_order: Sequence[str],
    start_ts: int,
    end_ts: int,
    rsi_lo: float = 38.0,
    rsi_hi: float = 58.0,
    atr_pullback_mult: float = 0.25,
    lev_cfg: float = 10.0,
):
    """
    v1.2 Multi-Factor Trend-Continuation Long-Limit Strategy (多單限價):
      - Designed for steady monthly trade cadence + improved R:R without relying on
        rare same-bar sweep intersections or overextended RSI [55,85] chasing.
      - Strictly causal closed 4H bar conditions:
        1. 200+ contiguous closed 4H bars & 60 contiguous closed UTC+8 1d bars
        2. Uptrend stack: EMA20 > EMA60 > EMA200 and ELA60[-1] > EMA60[-7] (rising)
        3. Healthy pullback momentum reset: 38.0 <= RSI14 <= 58.0
        4. Bullish stabilization: Close >= EMA60 and (Close > Open or close_pos >= 0.50)
        5. Strict limit buy order anchored at min(EMA20, Open_bt - 0.25 * ATr14),
            gated by [0.0005, 0.10] below Open_bt and ROUND_DOWN to tickSz.
    """
    cands_by_bar: Dict[int, list] = {}
    max_lev: Dict[str, float] = {}
    diag = {"candidate": "LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT", "signals": 0}
    for inst in symbol_order:
        if inst not in raw:
            continue
        v = raw[inst]
        max_lev[inst] = min(lev_cfg, float(v["maxLever"]))
        ts4, o4, d1_set = v["ts4"], v["o4"], v["d1_set"]
        tk_d = D(str(v["tickSz_str"]))
        ts4_list = [int(x) for x in ts4.tolist()]
        idx_map = {t: idx for idx, t in enumerate(ts4_list)}

        for i in range(200, len(ts4_list)):
            bt = ts4_list[i]
            if bt < start_ts - 48 * H1 or bt > end_ts:
                continue
            recent_idx = _contiguous_recent_indices(idx_map, bt, 220)
            if len(recent_idx) < 206:
                continue
            if not _has_60d_causal_gate(bt, d1_set):
                continue

            ordered = list(reversed(recent_idx))
            closes = [float(o4[j, 3]) for j in ordered]
            ema20_s = ema_series(closes, 20)
            ema60_s = ema_series(closes, 60)
            ema200_s = ema_series(closes, 200)
            ema20 = ema20_s[-1]
            ema60 = ema60_s[-1]
            ema60_prev6 = ema60_s[-7]
            ema200 = ema200_s[-1]

            if not (ema20 > ema60 > ema200 and ema60 > ema60_prev6):
                continue

            _, rsi14 = indicators_ema60_rsi14(closes[-180:])
            if not (rsi_lo <= rsi14 <= rsi_hi):
                continue

            s_idx = recent_idx[0]
            open_s = float(o4[s_idx, 0])
            high_s = float(o4[s_idx, 1])
            low_s = float(o4[s_idx, 2])
            close_s = float(o4[s_idx, 3])
            rng_s = high_s - low_s
            close_pos = (close_s - low_s) / rng_s if rng_s > 0 else 0.0
            if close_s < ema60 or not (close_s > open_s or close_pos >= 0.50):
                continue

            atr14 = wilder_atr14([o4[j] for j in ordered[-40:]])
            if atr14 <= 0.0:
                continue

            op = float(o4[i, 0])
            raw_anchor = min(ema20, op - atr_pullback_mult * atr14)
            res = eval_limit_price_and_gate(op, raw_anchor, tk_d)
            if res is None:
                continue
            dist, px_f = res
            cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, px_f, False))
            diag["signals"] += 1

    return cands_by_bar, max_lev, diag

def make_sim_spec(candidate: str, tp_pct: float, sl_pct: float, ttl_hours: float, max_slots: int, risk_per_trade: float):
    return {
        "initial_capital_u": 50000.0,
        "leverage": 10.0,
        "mmr_approx": 0.01,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slip_mkt": 0.0003,
        "legs": [{
            "mode": "fib_long",
            "candidate_tag": candidate,
            "tp_pct": float(tp_pct),
            "sl_pct": float(sl_pct),
            "lookback": 24,
            "rsi_lo": 55.0 if candidate != "LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT" else 38.0,
            "rsi_hi": 85.0 if candidate != "LONG_STRUCT_03_V1_0_EMA_PULLBACK_LIMIT" else 58.0,
            "entry_level": 0.618,
            "ttl_hours": float(ttl_hours),
            "max_slots": int(max_slots),
            "risk_per_trade": float(risk_per_trade),
            "daily_loss_limit": 600.0,
            "loss_streak_limit": 3,
            "loss_streak_pause_hours": 24.0,
            "use_1h_cancel": False,
        }],
    }


def summarize_run(res: dict) -> dict:
    ov = res["overall_trade_stats"]
    by_year = {}
    for y_int, d in sorted(res.get("by_year", {}).items()):
        by_year[str(y_int)] = {
            "trades": d.get("trades", 0),
            "win_rate_pct": d.get("win_rate_pct", 0.0),
            "net_pnl_u": d.get("net_pnl_u", 0.0),
            "pf": d.get("profit_factor"),
        }
    ol = res.get("order_log", [])
    filled_ol = [o for o in ol if o.get("outcome") == "filled"]
    return {
        "closed_trades": ov["trades"],
        "win_rate_pct": ov["win_rate_pct"],
        "final_eq_u": res["final_eq_u"],
        "mtm_mdd_pct": res["mtm_mdd_pct"],
        "closed_net_u": ov["net_pnl_u"],
        "closed_fee_u": ov["fee_u"],
        "closed_fund_u": ov["fund_u"],
        "all_real_fund_u": res["real_fund_u"],
        "pf": ov["profit_factor"],
        "expectancy_u": ov["expectancy_u"],
        "same_bar_sl": res.get("_same_bar_sl", 0),
        "skip_first_bar_cross": res.get("_skip_fb_cross", 0),
        "order_placed": len(ol),
        "order_filled": len(filled_ol),
        "order_expired": sum(1 for o in ol if o.get("outcome") == "expired"),
        "order_margin_rej": sum(1 for o in ol if o.get("outcome") == "margin_rej"),
        "f_ev_real_8h": res["f_ev_real_8h"],
        "f_ev_real_non8h": res["f_ev_real_non8h"],
        "f_ev_miss_8h": res["f_ev_miss_8h"],
        "by_year": by_year,
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="BACKTEST-READINESS-01 v1.2 bounded offline Long-Limit adapter")
    p.add_argument("--manifest", required=True, help="Path to manifest JSON")
    p.add_argument("--shared-risk", required=True, help="Path to shared_risk.py")
    p.add_argument("--cache-dir", required=True, help="Path to cache_v3 directory")
    p.add_argument("--funding-db", required=True, help="Path to read-only funding SQLite database")
    p.add_argument("--out-dir", required=True, help="Isolated output directory")
    p.add_argument("--candidate", required=True, choices=SUPPORTED_CANDIDATES, help="Long-limit candidate to run")
    p.add_argument("--symbols", default="", help="Optional comma-separated ordered symbol list; empty = all EX_USDC_286")
    p.add_argument("--start-utc", required=True, help="Inclusive UTC start timestamp (ISO-8601)")
    p.add_argument("--end-utc", required=True, help="Inclusive UTC end timestamp (ISO-8601)")
    p.add_argument("--scenarios", default="cross_1tick,delay1bar", help="Comma-separated subset of: cross_1tick,delay1bar")
    p.add_argument("--tp-pct", type=float, default=None, help="Optional TP override (decimal, e.g. 0.055)")
    p.add_argument("--sl-pct", type=float, default=None, help="Optional SL override (decimal, e.g. 0.030)")
    p.add_argument("--ttl-hours", type=float, default=None, help="Optional TTL hours override")
    p.add_argument("--max-slots", type=int, default=None, help="Optional max_slots override")
    p.add_argument("--risk-per-trade", type=float, default=None, help="Optional risk_per_trade (USDT) override")
    p.add_argument("--dry-check", action="store_true", help="Read-only manifest & scope check; no runtime imports")
    return p.parse_args(argv)

def main(argv=None) -> int:
    args = parse_args(argv)
    started_utc = datetime.now(TZ_UTC).isoformat()
    t0 = time.time()

    manifest_path = Path(args.manifest).expanduser()
    shared_risk_path = Path(args.shared_risk).expanduser()
    cache_dir = Path(args.cache_dir).expanduser()
    src_funding_db = Path(args.funding_db).expanduser()
    out_dir = Path(args.out_dir).expanduser()

    start_ts = parse_utc_ms(args.start_utc)
    end_ts = parse_utc_ms(args.end_utc)
    if end_ts < start_ts:
        raise RuntimeError("end-utc must be >= start-utc")

    requested_scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    if not requested_scenarios:
        raise RuntimeError("At least one scenario must be specified")
    for s in requested_scenarios:
        if s not in SUPPORTED_SCENARIOS:
            raise RuntimeError("Unsupported scenario: " + s)

    defaults = DEFAULT_EXIT_BY_CANDIDATE[args.candidate]
    tp_pct = defaults["tp_pct"] if args.tp_pct is None else args.tp_pct
    sl_pct = defaults["sl_pct"] if args.sl_pct is None else args.sl_pct
    ttl_hours = defaults["ttl_hours"] if args.ttl_hours is None else args.ttl_hours
    max_slots = defaults["max_slots"] if args.max_slots is None else args.max_slots
    risk_per_trade = defaults["risk_per_trade"] if args.risk_per_trade is None else args.risk_per_trade
    requested_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    with TransportBlocker() as tb:
        bound = _verify_manifest_bindings(manifest_path, shared_risk_path)
        scope_preview = {
            "study_id": "BACKTEST-READINESS-01",
            "version": "v1.2",
            "candidate": args.candidate,
            "direction": "LONG_LIMIT_ONLY",
            "started_utc": started_utc,
            "manifest": str(bound["manifest"]),
            "shared_risk": str(bound["roles"]["shared_risk"]),
            "cache_dir": str(cache_dir),
            "funding_db": str(src_funding_db),
            "out_dir": str(out_dir),
            "symbols_arg": requested_symbols if requested_symbols else "ALL_EX_USDC_286",
            "start_utc": args.start_utc,
            "end_utc": args.end_utc,
            "scenarios": requested_scenarios,
            "exit_profile": {
                "tp_pct": tp_pct,
                "sl_pct": sl_pct,
                "ttl_hours": ttl_hours,
                "max_slots": max_slots,
                "risk_per_trade": risk_per_trade,
            },
            "dry_check": bool(args.dry_check),
            "transport_blocker_active": True,
        }
        print("RESOLVED_SCOPE:", json.dumps(scope_preview, ensure_ascii=False), flush=True)

        if args.dry_check:
            print(json.dumps({
                "dry_check": "PASS",
                "files_verified": bound["files_verified"],
                "modules_executed": False,
                "transport_hits": list(tb.hits),
                "scope": scope_preview,
            }, ensure_ascii=False, indent=2), flush=True)
            return 0

        iso_db = out_dir / "funding_archive_long_struct_isolated.sqlite"
        iso_meta = Path(str(iso_db) + ".source_meta.json")
        final_report = out_dir / f"{args.candidate.lower()}_bounded_result.json"
        abort_report = out_dir / f"{args.candidate.lower()}_missing_funding_abort.json"
        scope_file = out_dir / f"{args.candidate.lower()}_bounded_scope.json"

        outputs = (
            ("iso_db", iso_db),
            ("iso_meta", iso_meta),
            ("iso_meta_tmp", Path(str(iso_meta) + ".tmp")),
            ("final_report", final_report),
            ("final_report_tmp", Path(str(final_report) + ".tmp")),
            ("abort_report", abort_report),
            ("abort_report_tmp", Path(str(abort_report) + ".tmp")),
            ("scope_file", scope_file),
            ("scope_file_tmp", Path(str(scope_file) + ".tmp")),
        )
        fixed_inputs = [
            ("funding-db", src_funding_db),
            ("manifest", manifest_path),
            ("shared-risk", shared_risk_path),
            ("cache-manifest", cache_dir / "manifest.json"),
            ("registered shared-risk", bound["roles"]["shared_risk"]),
        ]
        for rel, path in bound["files"].items():
            fixed_inputs.append(("manifest entry " + rel, path))
        _verify_output_paths_disjoint(outputs, fixed_inputs)

        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            _atomic_write_text(scope_file, json.dumps(scope_preview, ensure_ascii=False, indent=2) + "\n")

            funding_db_sha_before = sha(src_funding_db)
            cache_manifest_path = cache_dir / "manifest.json"
            if not cache_manifest_path.is_file():
                raise RuntimeError("cache_v3 manifest.json missing: " + str(cache_manifest_path))
            cache_manifest_sha_before = sha(cache_manifest_path)

            _bind_isolated_funding_db(src_funding_db, iso_db, iso_meta)
            loaded = _load_runtime_modules(bound)
            b6mod = loaded["b6_sim_portable"]
            if not callable(getattr(b6mod, "run_audit_sim_b6", None)):
                raise RuntimeError("registered b6_sim_portable missing callable run_audit_sim_b6")

            cache_manifest = json.loads(cache_manifest_path.read_text(encoding="utf-8"))
            symbols_dict = cache_manifest["symbols"]
            if requested_symbols:
                missing_syms = [s for s in requested_symbols if s not in symbols_dict]
                if missing_syms:
                    raise RuntimeError("requested symbols missing from cache manifest: " + ", ".join(missing_syms))
                ordered_syms = requested_symbols
            else:
                ordered_syms = [inst for inst in symbols_dict.keys() if inst != "USDC-USDT-SWAP"]

            fmaps, ov_raw = load_funding_db(iso_db)
            raw = {}
            all_bars_set = set()
            for inst in ordered_syms:
                info = symbols_dict[inst]
                npz_path = cache_dir / f"{inst}.npz"
                if not npz_path.is_file():
                    raise RuntimeError("symbol npz missing from cache_dir: " + inst)
                z = np.load(npz_path)
                ts30, o30 = z["ts30"], z["ohlc30"]
                ts4, o4 = z["ts4"], z["ohlc4"]
                ts1, o1 = z["ts1"], z["ohlc1"]
                d1_set = set(int(x) for x in z["d1_ts"].tolist())
                d30_map = {int(t): j for j, t in enumerate(ts30.tolist())}
                ts4_map = {int(t): j for j, t in enumerate(ts4.tolist())}
                for t in ts30.tolist():
                    ti = int(t)
                    if start_ts <= ti <= end_ts:
                        all_bars_set.add(ti)
                raw[inst] = {
                    "ts4": ts4, "o4": o4, "ts4_map": ts4_map,
                    "d30": (d30_map, o30),
                    "d1h": ({int(t): j for j, t in enumerate(ts1.tolist())}, o1),
                    "d1_set": d1_set,
                    "tickSz": float(info["spec"]["tickSz"]),
                    "tickSz_str": str(info["spec"]["tickSz"]),
                    "maxLever": float(info["spec"].get("maxLever", 20.0)),
                    "fmap": fmaps.get(inst, {}),
                }

            bars = sorted(all_bars_set)
            if args.candidate == "LONG_STRUCT_01_V1_2_FROZEN":
                cands_by_bar, max_lev, build_diag = build_cands_long_struct_01_frozen(raw, ordered_syms, start_ts, end_ts)
            elif args.candidate == "LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT":
                cands_by_bar, max_lev, build_diag = build_cands_long_struct_02_temporal_split(raw, ordered_syms, start_ts, end_ts)
            else:
                cands_by_bar, max_lev, build_diag = build_cands_long_struct_03_ema_pullback_limit(raw, ordered_syms, start_ts, end_ts)

            spec = make_sim_spec(args.candidate, tp_pct, sl_pct, ttl_hours, max_slots, risk_per_trade)
            arms = {}
            missing_by_scenario = {}
            for scen in requested_scenarios:
                dly = SUPPORTED_SCENARIOS[scen]
                r = b6mod.run_audit_sim_b6(
                    raw, bars, spec, ov_raw_ts=ov_raw,
                    cands_pre=cands_by_bar, max_lev_pre=max_lev,
                    record_events=True, record_trades_detail=True,
                    fill_mode="cross_1tick", delay_first_bar=dly,
                )
                miss_events = sorted(e for e in r["events_set"] if e[3] == "miss_8h")
                if miss_events:
                    by_inst: Dict[str, List[int]] = {}
                    for (_, inst, t30, _kind) in miss_events:
                        by_inst.setdefault(inst, []).append(int(t30))
                    missing_by_scenario[scen] = {
                        "miss_8h_count": len(miss_events),
                        "f_ev_real_8h": r["f_ev_real_8h"],
                        "f_ev_real_non8h": r["f_ev_real_non8h"],
                        "distinct_symbols": len(by_inst),
                        "per_symbol_counts": {k: len(v) for k, v in sorted(by_inst.items())},
                    }
                arms[scen] = summarize_run(r)

            if sha(src_funding_db) != funding_db_sha_before or sha(cache_manifest_path) != cache_manifest_sha_before:
                raise RuntimeError("Fixed input modified during run!")

            finished_utc = datetime.now(TZ_UTC).isoformat()
            if missing_by_scenario:
                _discard_final_report(final_report, fixed_inputs)
                abort_payload = {
                    "status": "ABORTED_MISSING_FUNDING",
                    "study_id": "BACKTEST-READINESS-01",
                    "version": "v1.2",
                    "candidate": args.candidate,
                    "started_utc": started_utc,
                    "finished_utc": finished_utc,
                    "elapsed_sec": round(time.time() - t0, 2),
                    "transport_hits": list(tb.hits),
                    "build_diagnostics": build_diag,
                    "missing_funding_gaps": missing_by_scenario,
                }
                _atomic_write_text(abort_report, json.dumps(abort_payload, ensure_ascii=False, indent=2) + "\n")
                return 2

            result_payload = {
                "status": "PASS",
                "study_id": "BACKTEST-READINESS-01",
                "version": "v1.2",
                "candidate": args.candidate,
                "started_utc": started_utc,
                "finished_utc": finished_utc,
                "elapsed_sec": round(time.time() - t0, 2),
                "transport_hits": list(tb.hits),
                "scope": scope_preview,
                "build_diagnostics": build_diag,
                "arms": arms,
                "sha256": {
                    "funding_db": funding_db_sha_before,
                    "cache_manifest": cache_manifest_sha_before,
                    "manifest": sha(manifest_path),
                    "shared_risk": sha(bound["roles"]["shared_risk"]),
                    "runner": sha(Path(__file__)),
                },
            }
            _atomic_write_text(final_report, json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n")
            return 0
        except Exception:
            _discard_final_report(final_report, fixed_inputs)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
