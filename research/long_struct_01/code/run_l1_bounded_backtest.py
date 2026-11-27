#!/usr/bin/env python3
"""Bounded offline L1 baseline backtest entry point (BACKTEST-READINESS-01 v1.0).

Adds explicit scope controls (symbols, UTC window, frozen scenarios, output dir)
and outer-layer socket/HTTP transport blocking on top of the frozen L1 baseline
rules from run_l1_tp_study.py (PR #6 head 3f67bd87fe5db2ec64d97b543fe780fa2f505f6f).

Strictly preserves:
  - Zero strategy, signal, cost, funding, or risk formula modifications.
  - Zero credentials, zero network calls (outer socket/HTTP blocker active for
    the entire run + hard refusal on missing funding).
  - Zero assert statements; zero top-level strategy/shared_risk/engine imports.
  - Read-only fixed inputs; unified output/temp vs input path-disjointness guard
    before any copy/write/cleanup; two-pass _discard_final_report guard.
  - Hard abort (exit 2, NO success report written) on any miss_8h funding gap.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import importlib.util
import json
import math
import os
import shutil
import socket
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path, PurePosixPath

import numpy as np

M30, H1, H4, H8, DAY = 1800000, 3600000, 14400000, 28800000, 86400000
TZ_UTC = timezone.utc

REQUIRED_EXPLICIT_KEYS = {
    "orig_long": "scripts/FIB_4H_Long_v3.py",
    "shared_risk": "scripts/shared_risk.py",
}
REQUIRED_ENGINE_FILES = (
    "b6_sim_portable.py",
    "sim_50k_v3_2_sl_fix.py",
    "audit_v3_1_full.py",
    "run_q38_audit_01.py",
)
ENGINE_IMPORT_ORDER = (
    ("sim_50k_v3_2_sl_fix", "sim_50k_v3_2_sl_fix.py"),
    ("audit_v3_1_full", "audit_v3_1_full.py"),
    ("run_q38_audit_01", "run_q38_audit_01.py"),
    ("b6_sim_portable", "b6_sim_portable.py"),
)
FROZEN_SCENARIOS = {
    "TP_2.5pct|cross_1tick": (0.025, False),
    "TP_2.5pct|delay1bar": (0.025, True),
}


class TransportBlocker:
    """Outer-layer socket/HTTP blocker active for the entire offline run."""

    def __init__(self) -> None:
        self.hits = []
        self._orig = {}

    def _deny(self, label: str):
        def _blocked(*args, **kwargs):
            self.hits.append(label)
            raise RuntimeError("OFFLINE_TRANSPORT_BLOCKED: " + label)
        return _blocked

    def __enter__(self) -> "TransportBlocker":
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

    def __exit__(self, exc_type, exc, tb) -> None:
        socket.create_connection = self._orig["create_connection"]
        socket.socket.connect = self._orig["socket_connect"]
        socket.socket.connect_ex = self._orig["socket_connect_ex"]
        urllib.request.urlopen = self._orig["urlopen"]
        http.client.HTTPConnection.connect = self._orig["http_connect"]
        http.client.HTTPSConnection.connect = self._orig["https_connect"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def parse_utc_ms(iso_str: str) -> int:
    s = iso_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise RuntimeError("UTC timestamp must include timezone offset or trailing Z: " + iso_str)
    return int(dt.astimezone(TZ_UTC).timestamp() * 1000)


def _manifest_file_path(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or rel == "":
        raise RuntimeError("manifest path is empty")
    parts = PurePosixPath(rel).parts
    if rel.startswith(("/", "\\")) or ".." in parts or PurePosixPath(rel).is_absolute():
        raise RuntimeError("manifest path is not a relative pack path: " + rel)
    root_res = root.resolve()
    candidate = (root / Path(*parts)).resolve()
    try:
        candidate.relative_to(root_res)
    except ValueError:
        raise RuntimeError("manifest path escapes the manifest directory: " + rel) from None
    return candidate


def _engine_manifest_key(files, filename: str) -> str:
    matches = []
    for rel in files:
        if not isinstance(rel, str):
            continue
        parts = PurePosixPath(rel).parts
        if len(parts) >= 2 and parts[-1] == filename and parts[-2] == "engine":
            matches.append(rel)
    if len(matches) != 1:
        raise RuntimeError(
            "manifest must contain exactly one registered engine/" + filename
            + " entry; found " + str(len(matches))
        )
    return matches[0]


def _verify_manifest_bindings(manifest_path: Path, orig_long: Path, shared_risk: Path):
    if not manifest_path.is_file():
        raise RuntimeError("manifest file is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("manifest is not readable JSON") from exc
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or len(files) == 0:
        raise RuntimeError('manifest["files"] must be a non-empty object')
    missing_explicit = [key for key in REQUIRED_EXPLICIT_KEYS.values() if key not in files]
    if missing_explicit:
        raise RuntimeError("manifest missing required entries: " + ", ".join(missing_explicit))
    engine_keys = {name: _engine_manifest_key(files, name) for name in REQUIRED_ENGINE_FILES}
    target_root = manifest_path.parent
    resolved = {}
    for rel, info in files.items():
        if not isinstance(info, dict) or not isinstance(info.get("sha256"), str) or info.get("sha256") == "":
            raise RuntimeError("manifest entry is missing sha256: " + str(rel))
        fp = _manifest_file_path(target_root, rel)
        if not fp.is_file():
            raise RuntimeError("manifest file is missing: " + rel)
        digest = sha(fp)
        if digest != info["sha256"]:
            raise RuntimeError("manifest SHA-256 mismatch: " + rel)
        resolved[rel] = fp
    cli_paths = {"orig_long": orig_long, "shared_risk": shared_risk}
    bound_roles = {}
    for role, key in REQUIRED_EXPLICIT_KEYS.items():
        registered = resolved[key]
        try:
            given = cli_paths[role].resolve(strict=True)
        except OSError as exc:
            raise RuntimeError(role + " path is missing") from exc
        if given != registered:
            raise RuntimeError(
                role + " is not the manifest-registered file " + key
                + "; refusing to verify one file and load another"
            )
        bound_roles[role] = registered
    return {
        "manifest": manifest_path,
        "target_root": target_root.resolve(),
        "files": resolved,
        "roles": bound_roles,
        "engine_keys": engine_keys,
        "files_verified": len(resolved),
    }


def _load_registered_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("registered module cannot be loaded: " + module_name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return mod


def _load_runtime_modules(bound):
    loaded = {}
    for module_name, filename in ENGINE_IMPORT_ORDER:
        rel = bound["engine_keys"][filename]
        loaded[module_name] = _load_registered_module(module_name, bound["files"][rel])
    return loaded


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        if left.resolve() == right.resolve():
            return True
    except OSError as exc:
        raise RuntimeError("path cannot be resolved for disjointness check") from exc
    if left.exists() and right.exists():
        try:
            if os.path.samefile(left, right):
                return True
        except OSError:
            return False
    return False


def _verify_output_paths_disjoint(outputs, fixed_inputs) -> None:
    for index, (out_label, out_path) in enumerate(outputs):
        for in_label, in_path in fixed_inputs:
            if _paths_overlap(out_path, in_path):
                raise RuntimeError(
                    "output path " + out_label + " overlaps fixed input " + in_label
                    + "; refusing before any copy, write, or cleanup"
                )
        for other_label, other_path in outputs[index + 1:]:
            if _paths_overlap(out_path, other_path):
                raise RuntimeError(
                    "output path " + out_label + " overlaps output path " + other_label
                    + "; refusing before any copy, write, or cleanup"
                )


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = Path(str(path) + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def _discard_final_report(path: Path, fixed_inputs) -> None:
    candidates = (path, Path(str(path) + ".tmp"))
    fixed_list = tuple(fixed_inputs)
    for candidate in candidates:
        for label, fixed in fixed_list:
            if _paths_overlap(candidate, fixed):
                raise RuntimeError(
                    "refusing to delete " + candidate.name
                    + " because it overlaps fixed input " + label
                )
    for candidate in candidates:
        if candidate.exists():
            candidate.unlink()


def _bind_isolated_funding_db(src_db: Path, l1_db: Path, meta_path: Path) -> str:
    if _paths_overlap(src_db, l1_db) or _paths_overlap(src_db, meta_path):
        raise RuntimeError("source funding DB overlaps derived L1_DB or sidecar")
    if not src_db.is_file():
        raise RuntimeError("source funding DB is missing")
    source_sha = sha(src_db)
    if l1_db.exists():
        if not meta_path.is_file():
            raise RuntimeError("L1_DB exists without source metadata; refusing to reuse or overwrite")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("L1_DB source metadata is unreadable; refusing to overwrite") from exc
        if not isinstance(meta, dict):
            raise RuntimeError("L1_DB source metadata is malformed; refusing to overwrite")
        if meta.get("b6_source_sha256") != source_sha or meta.get("derived_l1_db_sha256") != sha(l1_db):
            raise RuntimeError("L1_DB source or content hash does not match sidecar; refusing to reuse or overwrite")
        return source_sha
    l1_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_db, l1_db)
    derived_sha = sha(l1_db)
    try:
        _atomic_write_text(meta_path, json.dumps({
            "b6_source_sha256": source_sha,
            "b6_source_name": src_db.name,
            "derived_l1_db_sha256": derived_sha,
        }, ensure_ascii=False, indent=2))
    except Exception:
        if l1_db.exists() and not _paths_overlap(l1_db, src_db):
            l1_db.unlink()
        raise
    return source_sha


# --- Frozen L1 baseline formulas (exact verbatim from run_l1_tp_study.py) ---

def align_dec(val_float: float, tick_str: str) -> float:
    t = D(tick_str)
    if t <= 0:
        return val_float
    return float((D(str(val_float)) / t).to_integral_value(rounding=ROUND_DOWN) * t)


def indicators_180(prices):
    # Exact match to FIB_4H_Long_v3.indicators
    ema = sum(prices[:60]) / 60.0
    k = 2.0 / 61.0
    for price in prices[60:]:
        ema += (price - ema) * k
    moves = [b - a_ for a_, b in zip(prices, prices[1:])]
    gain = sum(max(0.0, v) for v in moves[:14]) / 14.0
    loss = sum(max(0.0, -v) for v in moves[:14]) / 14.0
    for v in moves[14:]:
        gain = (gain * 13.0 + max(0.0, v)) / 14.0
        loss = (loss * 13.0 + max(0.0, -v)) / 14.0
    rsi = 100.0 * gain / (gain + loss) if (gain + loss) else 50.0
    return ema, rsi


def build_cands_fib_long_exact(raw, start_ts: int, end_ts: int, lookback=24, rsi_lo=55.0, rsi_hi=85.0, entry_level=0.618, lev_cfg=10.0):
    """Exact signal mapping of FIB_4H_Long_v3.py (180-bar contiguous closed 4H window,
    EMA60, RSI14 [55,85], 60 contiguous 1D bars on UTC+8 day boundary, Fib 0.618,
    0.0005 <= (op - raw)/op <= 0.10, Decimal ROUND_DOWN tick alignment, sort by -depth)."""
    cands_by_bar = {}
    max_lev = {}
    for inst, v in raw.items():
        max_lev[inst] = min(lev_cfg, v["maxLever"])
        ts4, o4, d1_set = v["ts4"], v["o4"], v["d1_set"]
        tk_str = str(v["tickSz_str"])
        tk_d = D(tk_str)
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
            raw_px = round(hi - (hi - lo) * entry_level, 4)
            dist = (op - raw_px) / op
            if not (0.0005 <= dist <= 0.10):
                continue
            px_d = (D(str(raw_px)) / tk_d).to_integral_value(rounding=ROUND_DOWN) * tk_d
            if px_d <= 0:
                continue
            cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, float(px_d), False))
    return cands_by_bar, max_lev


def load_orig_module(orig_long_path: Path):
    spec = importlib.util.spec_from_file_location("fib_long_v3_orig", str(orig_long_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("orig_long module cannot be loaded")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_mapping(orig_mod, raw, cands_by_bar, start_ts: int, end_ts: int):
    """Compare orig FIB_4H_Long_v3.signal() & price_targets() against our exact builder."""
    class MockAPI:
        def __init__(self, r):
            self.r = r
            self.cur_bar = 0
        def call(self, path, params, private=False):
            inst = params["instId"]
            v = self.r[inst]
            if params["bar"] == "4H":
                ts4, o4 = v["ts4"], v["o4"]
                res = []
                j = v["ts4_map"].get(self.cur_bar)
                if j is None:
                    return []
                lo_i = max(0, j - 180)
                for k in range(j, lo_i - 1, -1):
                    confirm = "0" if k == j else "1"
                    res.append([str(int(ts4[k])), str(o4[k, 0]), str(o4[k, 1]), str(o4[k, 2]), str(o4[k, 3]), "0", "0", "0", confirm])
                return res
            elif params["bar"] == "1D":
                return [[str(int(t)), "1", "1", "1", "1", "0", "0", "0", "1"] for t in sorted(v["d1_set"], reverse=True)]
            return []

    api = MockAPI(raw)
    test_insts = sorted(raw.keys())[:30]
    checked = 0
    matched_sig = 0
    mismatches = 0
    for inst in test_insts:
        v = raw[inst]
        ts4 = [int(x) for x in v["ts4"].tolist() if start_ts <= int(x) <= end_ts]
        step = max(1, len(ts4) // 100)
        sp = {"instId": inst, "tickSz": v["tickSz_str"]}
        for bt in ts4[::step][:100]:
            api.cur_bar = bt
            orig_out = orig_mod.signal(api, sp, bt)
            ours = [c for c in cands_by_bar.get(bt, []) if c[2] == inst]
            checked += 1
            if orig_out is None and not ours:
                continue
            if orig_out is not None and len(ours) == 1:
                orig_px = float(orig_out[0])
                our_px = ours[0][3]
                if abs(orig_px - our_px) <= 1e-12:
                    matched_sig += 1
                else:
                    mismatches += 1
            else:
                mismatches += 1

    exit_checks = 0
    exit_mismatches = 0
    orig_mod.TP_PCT = D("0.025")
    orig_mod.SL_PCT = D("0.04")
    for avg_s, tk_s in [("1.2345", "0.0001"), ("0.00456", "0.00001"), ("142.35", "0.01"), ("23.81", "0.001")]:
        otp, osl = orig_mod.price_targets(D(avg_s), D(tk_s))
        etp = align_dec(float(D(avg_s) * (D(1) + D("0.025"))), tk_s)
        esl = align_dec(float(D(avg_s) * (D(1) - D("0.04"))), tk_s)
        exit_checks += 1
        if abs(float(otp) - etp) > 1e-12 or abs(float(osl) - esl) > 1e-12:
            exit_mismatches += 1
    return {
        "bars_checked": checked,
        "signals_matched": matched_sig,
        "signal_mismatches": mismatches,
        "exit_target_checks": exit_checks,
        "exit_target_mismatches": exit_mismatches,
    }


def load_funding_db(db_path: Path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    fmaps = {}
    ov_raw = {}
    for inst, ts_grid, ts_raw, rate in conn.execute("SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive"):
        fmaps.setdefault(inst, {})[int(ts_grid)] = float(rate)
        ov_raw.setdefault(inst, {})[int(ts_grid)] = int(ts_raw)
    conn.close()
    return fmaps, ov_raw


def make_spec_tp25():
    return {
        "initial_capital_u": 50000.0,
        "leverage": 10.0,
        "mmr_approx": 0.01,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slip_mkt": 0.0003,
        "legs": [{
            "mode": "fib_long",
            "tp_pct": 0.025,
            "sl_pct": 0.04,
            "lookback": 24,
            "rsi_lo": 55.0,
            "rsi_hi": 85.0,
            "entry_level": 0.618,
            "ttl_hours": 48.0,
            "max_slots": 24,
            "risk_per_trade": 150.0,
            "daily_loss_limit": 600.0,
            "loss_streak_limit": 3,
            "loss_streak_pause_hours": 24.0,
            "use_1h_cancel": False,
        }],
    }


def summarize_run(res):
    ov = res["overall_trade_stats"]
    by_year = {}
    for y_int, d in sorted(res.get("by_year", {}).items()):
        by_year[str(y_int)] = {
            "trades": d["trades"],
            "win_rate_pct": d["win_rate_pct"],
            "net_pnl_u": d["net_pnl_u"],
            "fee_u": d["fee_u"],
            "fund_u": d["fund_u"],
            "pf": d["profit_factor"],
            "expectancy_u": d["expectancy_u"],
            "mtm_mdd_pct": d["mtm_mdd_pct"],
            "end_eq_u": d["end_eq_u"],
        }
    by_month = {}
    for tr in res.get("trades_detail", []) or []:
        ts_exit = tr.get("exit_ts") or tr.get("close_ts") or tr.get("entry_ts")
        if ts_exit is None:
            continue
        ym = datetime.fromtimestamp(int(ts_exit) / 1000.0, tz=TZ_UTC).strftime("%Y-%m")
        m = by_month.setdefault(ym, {"trades": 0, "wins": 0, "net_pnl_u": 0.0})
        m["trades"] += 1
        net = float(tr.get("net_pnl_u", tr.get("net_u", tr.get("pnl_u", 0.0))))
        if net > 0:
            m["wins"] += 1
        m["net_pnl_u"] += net
    by_month_out = {
        ym: {
            "trades": d["trades"],
            "win_rate_pct": round(100.0 * d["wins"] / d["trades"], 2) if d["trades"] else 0.0,
            "net_pnl_u": round(d["net_pnl_u"], 2),
        }
        for ym, d in sorted(by_month.items())
    }
    ol = res.get("_ord_log", [])
    filled_ol = [o for o in ol if o["outcome"] == "filled"]
    return {
        "final_eq_u": res["final_eq_u"],
        "ret_eq_pct": res["ret_eq_pct"],
        "cagr_eq_pct": res["cagr_eq_pct"],
        "mtm_mdd_pct": res["mtm_mdd_pct"],
        "ann_calmar_eq": res["ann_calmar_eq"],
        "closed_trades": ov["trades"],
        "win_rate_pct": ov["win_rate_pct"],
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
        "order_expired": sum(1 for o in ol if o["outcome"] == "expired"),
        "order_margin_rej": sum(1 for o in ol if o["outcome"] == "margin_rej"),
        "f_ev_real_8h": res["f_ev_real_8h"],
        "f_ev_real_non8h": res["f_ev_real_non8h"],
        "f_ev_miss_8h": res["f_ev_miss_8h"],
        "by_year": by_year,
        "by_month": by_month_out,
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="BACKTEST-READINESS-01 v1.0 bounded offline L1 baseline runner")
    p.add_argument("--manifest", required=True, help="Explicit path to manifest JSON")
    p.add_argument("--orig-long", required=True, help="Explicit path to FIB_4H_Long_v3.py")
    p.add_argument("--shared-risk", required=True, help="Explicit path to shared_risk.py")
    p.add_argument("--cache-dir", required=True, help="Path to cache_v3 directory")
    p.add_argument("--funding-db", required=True, help="Path to read-only funding SQLite database")
    p.add_argument("--out-dir", required=True, help="Isolated output directory")
    p.add_argument("--symbols", default="", help="Optional comma-separated ordered symbol list; empty = all EX_USDC_286")
    p.add_argument("--start-utc", required=True, help="Inclusive UTC start timestamp (ISO-8601, e.g. 2025-10-01T00:00:00Z)")
    p.add_argument("--end-utc", required=True, help="Inclusive UTC end timestamp (ISO-8601, e.g. 2025-10-31T23:30:00Z)")
    p.add_argument("--scenarios", required=True, help="Comma-separated subset of frozen scenarios: TP_2.5pct|cross_1tick,TP_2.5pct|delay1bar")
    p.add_argument("--dry-check", action="store_true", help="Read-only manifest & scope check; no module imports")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    started_utc = datetime.now(TZ_UTC).isoformat()
    t0 = time.time()

    manifest_path = Path(args.manifest).expanduser()
    orig_long_path = Path(args.orig_long).expanduser()
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
        raise RuntimeError("at least one frozen scenario must be specified")
    for s in requested_scenarios:
        if s not in FROZEN_SCENARIOS:
            raise RuntimeError("unsupported or unfrozen scenario: " + s + "; allowed: " + ", ".join(FROZEN_SCENARIOS))

    requested_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    with TransportBlocker() as tb:
        bound = _verify_manifest_bindings(manifest_path, orig_long_path, shared_risk_path)

        scope_preview = {
            "study_id": "BACKTEST-READINESS-01",
            "version": "v1.0",
            "started_utc": started_utc,
            "manifest": str(bound["manifest"]),
            "orig_long": str(bound["roles"]["orig_long"]),
            "shared_risk": str(bound["roles"]["shared_risk"]),
            "cache_dir": str(cache_dir),
            "funding_db": str(src_funding_db),
            "out_dir": str(out_dir),
            "symbols_arg": requested_symbols if requested_symbols else "ALL_EX_USDC_286",
            "start_utc": args.start_utc,
            "end_utc": args.end_utc,
            "scenarios": requested_scenarios,
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

        l1_db = out_dir / "funding_archive_l1_isolated.sqlite"
        l1_meta = Path(str(l1_db) + ".source_meta.json")
        final_report = out_dir / "l1_bounded_result.json"
        abort_report = out_dir / "l1_bounded_missing_funding_abort.json"
        scope_file = out_dir / "l1_bounded_scope.json"

        outputs = (
            ("L1_DB", l1_db),
            ("L1_DB sidecar", l1_meta),
            ("L1_DB sidecar temp", Path(str(l1_meta) + ".tmp")),
            ("final report", final_report),
            ("final report temp", Path(str(final_report) + ".tmp")),
            ("abort report", abort_report),
            ("abort report temp", Path(str(abort_report) + ".tmp")),
            ("scope file", scope_file),
            ("scope file temp", Path(str(scope_file) + ".tmp")),
        )
        fixed_inputs = [
            ("funding-db", src_funding_db),
            ("manifest", manifest_path),
            ("orig-long", orig_long_path),
            ("shared-risk", shared_risk_path),
            ("cache-manifest", cache_dir / "manifest.json"),
            ("registered orig-long", bound["roles"]["orig_long"]),
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

            _bind_isolated_funding_db(src_funding_db, l1_db, l1_meta)
            loaded = _load_runtime_modules(bound)
            b6mod = loaded["b6_sim_portable"]
            if not callable(getattr(b6mod, "run_audit_sim_b6", None)):
                raise RuntimeError("registered b6_sim_portable missing callable run_audit_sim_b6")

            orig_mod = load_orig_module(bound["roles"]["orig_long"])
            cache_manifest = json.loads(cache_manifest_path.read_text(encoding="utf-8"))
            symbols_dict = cache_manifest["symbols"]

            if requested_symbols:
                missing_syms = [s for s in requested_symbols if s not in symbols_dict]
                if missing_syms:
                    raise RuntimeError("requested symbols missing from cache manifest: " + ", ".join(missing_syms))
                ordered_syms = requested_symbols
            else:
                ordered_syms = [inst for inst in symbols_dict.keys() if inst != "USDC-USDT-SWAP"]

            fmaps, ov_raw = load_funding_db(l1_db)
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
            cands_by_bar, max_lev = build_cands_fib_long_exact(raw, start_ts, end_ts)
            total_cands = sum(len(v) for v in cands_by_bar.values())
            mapping_check = verify_mapping(orig_mod, raw, cands_by_bar, start_ts, end_ts)
            if mapping_check["signal_mismatches"] != 0 or mapping_check["exit_target_mismatches"] != 0:
                raise RuntimeError("Mapping verification failed: " + json.dumps(mapping_check))

            arms = {}
            missing_by_scenario = {}
            for name in requested_scenarios:
                tp_pct, dly = FROZEN_SCENARIOS[name]
                r = b6mod.run_audit_sim_b6(
                    raw, bars, make_spec_tp25(), ov_raw_ts=ov_raw,
                    cands_pre=cands_by_bar, max_lev_pre=max_lev,
                    record_events=True, record_trades_detail=True,
                    fill_mode="cross_1tick", delay_first_bar=dly,
                )
                miss_events = sorted(e for e in r["events_set"] if e[3] == "miss_8h")
                if miss_events:
                    by_inst = {}
                    for (_, inst, t30, kind) in miss_events:
                        by_inst.setdefault(inst, []).append(int(t30))
                    missing_by_scenario[name] = {
                        "miss_8h_count": len(miss_events),
                        "f_ev_real_8h": r["f_ev_real_8h"],
                        "f_ev_real_non8h": r["f_ev_real_non8h"],
                        "distinct_symbols": len(by_inst),
                        "min_ts_utc": datetime.fromtimestamp(min(e[2] for e in miss_events) / 1000.0, tz=TZ_UTC).isoformat(),
                        "max_ts_utc": datetime.fromtimestamp(max(e[2] for e in miss_events) / 1000.0, tz=TZ_UTC).isoformat(),
                        "per_symbol_counts": {k: len(v) for k, v in sorted(by_inst.items())},
                        "sample_events_utc": [
                            {
                                "inst_id": inst,
                                "ts_utc": datetime.fromtimestamp(t30 / 1000.0, tz=TZ_UTC).isoformat(),
                                "kind": kind,
                            }
                            for (_, inst, t30, kind) in miss_events[:25]
                        ],
                    }
                arms[name] = summarize_run(r)

            funding_db_sha_after = sha(src_funding_db)
            cache_manifest_sha_after = sha(cache_manifest_path)
            if funding_db_sha_before != funding_db_sha_after or cache_manifest_sha_before != cache_manifest_sha_after:
                raise RuntimeError("Fixed input modified during run!")

            finished_utc = datetime.now(TZ_UTC).isoformat()

            if missing_by_scenario:
                _discard_final_report(final_report, fixed_inputs)
                abort_payload = {
                    "status": "ABORTED_MISSING_FUNDING",
                    "study_id": "BACKTEST-READINESS-01",
                    "version": "v1.0",
                    "started_utc": started_utc,
                    "finished_utc": finished_utc,
                    "elapsed_sec": round(time.time() - t0, 2),
                    "transport_blocker_active_entire_run": True,
                    "transport_hits": list(tb.hits),
                    "scope": scope_preview,
                    "symbols_loaded": len(raw),
                    "bars_30m_in_window": len(bars),
                    "candidate_bars_in_window": len(cands_by_bar),
                    "candidate_signals_in_window": total_cands,
                    "mapping_verification": mapping_check,
                    "inputs_unchanged": True,
                    "sha256": {
                        "funding_db": funding_db_sha_after,
                        "cache_manifest": cache_manifest_sha_after,
                        "manifest": sha(manifest_path),
                        "orig_long": sha(bound["roles"]["orig_long"]),
                        "shared_risk": sha(bound["roles"]["shared_risk"]),
                        "runner": sha(Path(__file__)),
                    },
                    "missing_funding_gaps": missing_by_scenario,
                    "policy_note": "Offline hard refusal: miss_8h > 0 aborts with exit 2 and writes NO success report (zero-fill/interpolation/network fetch forbidden).",
                }
                _atomic_write_text(abort_report, json.dumps(abort_payload, ensure_ascii=False, indent=2) + "\n")
                print("ABORT_REPORT_SHA256:", sha(abort_report), flush=True)
                print("MISSING_FUNDING_SUMMARY:", json.dumps({
                    k: {kk: vv for kk, vv in v.items() if kk != "sample_events_utc"}
                    for k, v in missing_by_scenario.items()
                }, ensure_ascii=False), flush=True)
                return 2

            result_payload = {
                "status": "PASS",
                "study_id": "BACKTEST-READINESS-01",
                "version": "v1.0",
                "started_utc": started_utc,
                "finished_utc": finished_utc,
                "elapsed_sec": round(time.time() - t0, 2),
                "transport_blocker_active_entire_run": True,
                "transport_hits": list(tb.hits),
                "scope": scope_preview,
                "symbols_loaded": len(raw),
                "symbol_order": ordered_syms if len(ordered_syms) <= 10 else ordered_syms[:10] + ["..."],
                "bars_30m_in_window": len(bars),
                "candidate_bars_in_window": len(cands_by_bar),
                "candidate_signals_in_window": total_cands,
                "mapping_verification": mapping_check,
                "inputs_unchanged": True,
                "sha256": {
                    "funding_db": funding_db_sha_after,
                    "l1_isolated_funding_db": sha(l1_db),
                    "cache_manifest": cache_manifest_sha_after,
                    "manifest": sha(manifest_path),
                    "orig_long": sha(bound["roles"]["orig_long"]),
                    "shared_risk": sha(bound["roles"]["shared_risk"]),
                    "runner": sha(Path(__file__)),
                },
                "limitations": [
                    "缺歷史 BBO，post_only 實際可否掛入與排隊順位未知",
                    "cross_1tick 僅為穿價下界檢驗，不證明實盤全量成交",
                    "歷史 MMR 採 1% 近似、歷史 tick 採現有快照、非 8H 資金費分母完整性待驗",
                    "delay1bar 為敏感度測試而非真實延遲",
                ],
                "arms": arms,
            }
            _atomic_write_text(final_report, json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n")
            print("FINAL_REPORT_SHA256:", sha(final_report), flush=True)
            for name, s in arms.items():
                print(
                    f"[PASS] {name}: trades={s['closed_trades']} win={s['win_rate_pct']}% net={s['closed_net_u']} "
                    f"eq={s['final_eq_u']} mdd={s['mtm_mdd_pct']}% pf={s['pf']} ev={s['expectancy_u']} "
                    f"f8h={s['f_ev_real_8h']} fnon8h={s['f_ev_real_non8h']} miss8h={s['f_ev_miss_8h']}",
                    flush=True,
                )
            return 0
        except Exception:
            _discard_final_report(final_report, fixed_inputs)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
