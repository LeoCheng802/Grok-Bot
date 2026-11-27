#!/usr/bin/env python3
"""Bounded offline RETEST24-R1-R2 backtest adapter (BACKTEST-READINESS-01 v1.1).

Aligned with run_l1_bounded_backtest.py (PR #6 head da65fe4dbdd549aa973e4e3f2c69447b53dcb64a).
Supports:
  1. Frozen baseline: RETEST24_V1_5_FROZEN (exact breakout_retest_short rules from
     audit_v3_1_full.py + Q28 R1 150U / Q29 R2 100U specs, entry_offset_mult=0.9995).
  2. Isolated single-hypothesis candidate: RETEST24_OPT_01_BEARISH_CLOSE_POS
     (adds ONLY one causal filter on closed breakdown bar i-1:
      high > low and (close - low) / (high - low) <= 0.35; all other signal,
      cost, funding, sizing, and risk formulas remain bit-for-bit identical).

Strictly preserves:
  - Zero credentials, zero network calls (outer socket/HTTP TransportBlocker
    active for the entire run + hard refusal on missing funding).
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
from pathlib import Path, PurePosixPath

import numpy as np

M30, H1, H4, H8, DAY = 1800000, 3600000, 14400000, 28800000, 86400000
TZ_UTC = timezone.utc

REQUIRED_EXPLICIT_KEYS = {
    "retest24_script": "scripts/RETEST24_R1_R2_Switchable_v1_5_auditfix.py",
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

CANDIDATE_MODES = (
    "RETEST24_V1_5_FROZEN",
    "RETEST24_OPT_01_BEARISH_CLOSE_POS",
)
OPT_01_MAX_CLOSE_POS = 0.35

# Frozen R1/R2 same-signal sizing controls under both fill-timing modes
FROZEN_SCENARIOS = {
    "R1_150U|cross_1tick": ("R1", 150.0, 600.0, False),
    "R1_150U|delay1bar": ("R1", 150.0, 600.0, True),
    "R2_100U|cross_1tick": ("R2", 100.0, 400.0, False),
    "R2_100U|delay1bar": ("R2", 100.0, 400.0, True),
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


def _verify_manifest_bindings(manifest_path: Path, retest24_script: Path, shared_risk: Path):
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
    cli_paths = {"retest24_script": retest24_script, "shared_risk": shared_risk}
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


def _bind_isolated_funding_db(src_db: Path, derived_db: Path, meta_path: Path) -> str:
    if _paths_overlap(src_db, derived_db) or _paths_overlap(src_db, meta_path):
        raise RuntimeError("source funding DB overlaps derived funding DB or sidecar")
    if not src_db.is_file():
        raise RuntimeError("source funding DB is missing")
    source_sha = sha(src_db)
    if derived_db.exists():
        if not meta_path.is_file():
            raise RuntimeError("derived funding DB exists without source metadata; refusing to reuse or overwrite")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("derived funding DB source metadata is unreadable; refusing to overwrite") from exc
        if not isinstance(meta, dict):
            raise RuntimeError("derived funding DB source metadata is malformed; refusing to overwrite")
        if meta.get("source_sha256") != source_sha or meta.get("derived_db_sha256") != sha(derived_db):
            raise RuntimeError("derived funding DB source or content hash does not match sidecar; refusing to reuse or overwrite")
        return source_sha
    derived_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_db, derived_db)
    derived_sha = sha(derived_db)
    try:
        _atomic_write_text(meta_path, json.dumps({
            "source_sha256": source_sha,
            "source_name": src_db.name,
            "derived_db_sha256": derived_sha,
        }, ensure_ascii=False, indent=2))
    except Exception:
        if derived_db.exists() and not _paths_overlap(derived_db, src_db):
            derived_db.unlink()
        raise
    return source_sha


def load_funding_db(db_path: Path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT inst_id, ts_snapped, rate FROM funding_archive").fetchall()
    finally:
        con.close()
    fmaps = {}
    ov_raw = {}
    for inst, ts_s, rt in rows:
        ts_i = int(ts_s)
        fmaps.setdefault(inst, {})[ts_i] = float(rt)
        ov_raw.setdefault(inst, set()).add(ts_i)
    return fmaps, ov_raw


# --- Frozen RETEST24-R1-R2 v1.5 formulas (verbatim from audit_v3_1_full.py) ---

def indicators_ema55_rsi14(c: np.ndarray):
    n = len(c)
    ema = np.full(n, np.nan)
    rsi = np.full(n, np.nan)
    if n < 55:
        return ema, rsi
    k = 2.0 / 56.0
    ema[54] = float(np.mean(c[:55]))
    for i in range(55, n):
        ema[i] = c[i] * k + ema[i - 1] * (1.0 - k)
    df = np.diff(c)
    g = float(np.mean(np.maximum(df[:14], 0.0)))
    lo = float(np.mean(np.maximum(-df[:14], 0.0)))
    rsi[14] = 100.0 * g / (g + lo) if (g + lo) else 50.0
    for i in range(14, n - 1):
        d = df[i]
        g = (g * 13.0 + (d if d > 0 else 0.0)) / 14.0
        lo = (lo * 13.0 + (-d if d < 0 else 0.0)) / 14.0
        rsi[i + 1] = 100.0 * g / (g + lo) if (g + lo) else 50.0
    return ema, rsi


def align_tick(px: float, t: float) -> float:
    return math.floor(px / t) * t if t > 0 else px


def make_retest24_spec(risk_id: str, risk_per_trade: float, daily_loss_limit: float) -> dict:
    return {
        "batch": "V3-B1",
        "risk_id": risk_id,
        "initial_capital_u": 50000.0,
        "leverage": 10.0,
        "mmr_approx": 0.01,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slip_mkt": 0.0003,
        "legs": [{
            "mode": "breakout_retest_short",
            "lookback": 12,
            "rsi_lo": 20,
            "rsi_hi": 40,
            "entry_offset_mult": 0.9995,
            "tp_pct": 0.05,
            "sl_pct": 0.05,
            "ttl_hours": 24,
            "use_1h_cancel": False,
            "max_slots": 12,
            "risk_per_trade": risk_per_trade,
            "daily_loss_limit": daily_loss_limit,
            "loss_streak_limit": 0,
        }],
    }


def build_cands_retest24(raw: dict, start_ts: int, end_ts: int, candidate_mode: str):
    if candidate_mode not in CANDIDATE_MODES:
        raise RuntimeError("unsupported candidate_mode: " + str(candidate_mode))
    lb = 12
    rlo, rhi = 20.0, 40.0
    offset_mult = 0.9995
    lev_cfg = 10.0

    cands_by_bar = {}
    max_lev = {}
    stats = {
        "baseline_candidates_in_window": 0,
        "filtered_by_opt01_close_pos": 0,
        "final_candidates_in_window": 0,
    }
    for inst, v in raw.items():
        max_lev[inst] = min(lev_cfg, v["maxLever"])
        ts4, o4, ema, rsi, d1_set, tk = v["ts4"], v["o4"], v["ema"], v["rsi"], v["d1_set"], v["tickSz"]
        c4 = o4[:, 3]
        for i in range(60, len(ts4)):
            bt = int(ts4[i])
            if bt < start_ts or bt > end_ts:
                continue
            if int(ts4[i - 1]) != bt - H4:
                continue
            cp, ep, rp = float(c4[i - 1]), float(ema[i - 1]), float(rsi[i - 1])
            if math.isnan(ep) or math.isnan(rp):
                continue
            if cp >= ep or not (rlo <= rp <= rhi):
                continue
            dk = (bt + H8) // DAY * DAY - H8
            if not all((dk - d * DAY) in d1_set for d in range(1, 61)):
                continue
            op = float(o4[i, 0])
            if i - 1 - lb < 0:
                continue
            pl = float(np.min(o4[i - 1 - lb:i - 1, 2]))
            if not (cp < pl and op < pl):
                continue
            raw_px = pl * offset_mult
            dist = (raw_px - op) / op
            if not (0.0 <= dist <= 0.15):
                continue
            epx = align_tick(raw_px, tk)
            if epx <= 0:
                continue

            stats["baseline_candidates_in_window"] += 1

            # Single-hypothesis isolated candidate filter (RETEST24-OPT-01)
            if candidate_mode == "RETEST24_OPT_01_BEARISH_CLOSE_POS":
                h_prev = float(o4[i - 1, 1])
                l_prev = float(o4[i - 1, 2])
                bar_range = h_prev - l_prev
                if bar_range <= 0.0 or ((cp - l_prev) / bar_range) > OPT_01_MAX_CLOSE_POS:
                    stats["filtered_by_opt01_close_pos"] += 1
                    continue

            sk = -rp
            cands_by_bar.setdefault(bt, []).append((sk, 0, inst, epx, False))
            stats["final_candidates_in_window"] += 1

    return cands_by_bar, max_lev, stats


def summarize_run(r: dict) -> dict:
    trades = r.get("_trades", [])
    n = len(trades)
    wins = sum(1 for t in trades if t["net"] > 0)
    gross_win = sum(t["net"] for t in trades if t["net"] > 0)
    gross_loss = abs(sum(t["net"] for t in trades if t["net"] < 0))
    net_sum = sum(t["net"] for t in trades)
    pf = round(gross_win / gross_loss, 4) if gross_loss > 0 else None
    ol = r.get("_ord_log", [])
    filled_ol = [o for o in ol if o["outcome"] == "filled"]
    return {
        "closed_trades": n,
        "open_at_end": len(r.get("_open", [])),
        "win_rate_pct": round(100.0 * wins / n, 2) if n else 0.0,
        "closed_net_u": round(net_sum, 2),
        "final_eq_u": round(float(r.get("_end_eq_raw", r.get("final_eq", 50000.0))), 2),
        "mtm_mdd_pct": round(float(r.get("mtm_mdd_pct", 0.0)), 2),
        "pf": pf,
        "expectancy_u": round(net_sum / n, 3) if n else 0.0,
        "f_ev_real_8h": int(r.get("f_ev_real_8h", 0)),
        "f_ev_real_non8h": int(r.get("f_ev_real_non8h", 0)),
        "f_ev_miss_8h": int(r.get("f_ev_miss_8h", 0)),
        "real_fund_u": round(float(r.get("_real_fund_raw", 0.0)), 2),
        "orders_placed": len(ol),
        "orders_filled": len(filled_ol),
        "orders_expired": sum(1 for o in ol if o["outcome"] == "expired"),
        "orders_margin_rej": sum(1 for o in ol if o["outcome"] == "margin_rej"),
        "same_bar_sl": int(r.get("_same_bar_sl", 0)),
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Bounded offline RETEST24-R1-R2 backtest adapter (frozen v1.5 baseline + isolated OPT-01 candidate)."
    )
    p.add_argument("--manifest", required=True, help="Path to REPRO_MANIFEST.json")
    p.add_argument("--retest24-script", required=True, help="Path to manifest-registered RETEST24_R1_R2_Switchable_v1_5_auditfix.py")
    p.add_argument("--shared-risk", required=True, help="Path to manifest-registered shared_risk.py")
    p.add_argument("--cache-dir", help="Path to cache_v3 directory containing manifest.json and *.npz")
    p.add_argument("--funding-db", help="Path to read-only source funding SQLite DB")
    p.add_argument("--out-dir", help="Directory for bounded run outputs")
    p.add_argument("--symbols", default="", help="Comma-separated symbol list (empty = all cache symbols excl. USDC-USDT-SWAP)")
    p.add_argument("--start-utc", default="2023-01-01T00:00:00Z", help="Inclusive window start ISO-8601 UTC")
    p.add_argument("--end-utc", default="2026-11-26T12:00:00Z", help="Inclusive window end ISO-8601 UTC")
    p.add_argument(
        "--scenarios",
        default="R1_150U|cross_1tick,R1_150U|delay1bar",
        help="Comma-separated frozen scenarios from: " + ", ".join(FROZEN_SCENARIOS.keys()),
    )
    p.add_argument(
        "--candidate",
        default="RETEST24_V1_5_FROZEN",
        choices=CANDIDATE_MODES,
        help="Strategy mode: frozen v1.5 baseline or isolated single-hypothesis RETEST24_OPT_01_BEARISH_CLOSE_POS",
    )
    p.add_argument("--dry-check", action="store_true", help="Verify manifest bindings only without loading strategy/engine or running backtest")
    return p.parse_args(argv)


def main(argv=None) -> int:
    t0 = time.time()
    started_utc = datetime.now(TZ_UTC).isoformat()
    args = parse_args(argv)

    with TransportBlocker() as tb:
        manifest_path = Path(args.manifest)
        retest24_path = Path(args.retest24_script)
        shared_risk_path = Path(args.shared_risk)

        bound = _verify_manifest_bindings(manifest_path, retest24_path, shared_risk_path)

        requested_scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
        if not requested_scenarios:
            raise RuntimeError("at least one scenario must be specified")
        invalid_scenarios = [s for s in requested_scenarios if s not in FROZEN_SCENARIOS]
        if invalid_scenarios:
            raise RuntimeError("unsupported scenarios: " + ", ".join(invalid_scenarios))

        start_ts = parse_utc_ms(args.start_utc)
        end_ts = parse_utc_ms(args.end_utc)
        if end_ts < start_ts:
            raise RuntimeError("end-utc must be >= start-utc")

        requested_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

        if args.dry_check:
            payload = {
                "dry_check": "PASS",
                "study_id": "BACKTEST-READINESS-01",
                "adapter": "run_retest24_bounded_backtest.py",
                "candidate": args.candidate,
                "scenarios": requested_scenarios,
                "files_verified": bound["files_verified"],
                "transport_blocker_active_entire_run": True,
                "transport_hits": list(tb.hits),
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
            return 0

        if not args.cache_dir or not args.funding_db or not args.out_dir:
            raise RuntimeError("--cache-dir, --funding-db, and --out-dir are required unless --dry-check is set")

        cache_dir = Path(args.cache_dir)
        src_funding_db = Path(args.funding_db)
        out_dir = Path(args.out_dir)

        derived_db = out_dir / "funding_archive_retest24_isolated.sqlite"
        derived_meta = out_dir / "funding_archive_retest24_isolated.meta.json"
        scope_file = out_dir / "retest24_bounded_scope.json"
        final_report = out_dir / "retest24_bounded_result.json"
        abort_report = out_dir / "retest24_bounded_missing_funding_abort.json"

        outputs = [
            ("derived_funding_db", derived_db),
            ("derived_funding_meta", derived_meta),
            ("derived_funding_meta.tmp", Path(str(derived_meta) + ".tmp")),
            ("scope_file", scope_file),
            ("scope_file.tmp", Path(str(scope_file) + ".tmp")),
            ("final_report", final_report),
            ("final_report.tmp", Path(str(final_report) + ".tmp")),
            ("abort_report", abort_report),
            ("abort_report.tmp", Path(str(abort_report) + ".tmp")),
        ]
        fixed_inputs = [
            ("source funding_db", src_funding_db),
            ("manifest", manifest_path),
            ("retest24_script", retest24_path),
            ("shared_risk", shared_risk_path),
            ("cache_manifest", cache_dir / "manifest.json"),
        ]
        for rel, path in bound["files"].items():
            fixed_inputs.append(("manifest entry " + rel, path))

        _verify_output_paths_disjoint(outputs, fixed_inputs)

        scope_preview = {
            "study_id": "BACKTEST-READINESS-01",
            "version": "v1.1",
            "adapter": "run_retest24_bounded_backtest.py",
            "candidate": args.candidate,
            "opt_01_max_close_pos": OPT_01_MAX_CLOSE_POS if args.candidate == "RETEST24_OPT_01_BEARISH_CLOSE_POS" else None,
            "start_utc": args.start_utc,
            "end_utc": args.end_utc,
            "scenarios": requested_scenarios,
            "requested_symbols": requested_symbols if requested_symbols else "ALL_EX_USDC",
            "started_utc": started_utc,
        }
        print("BOUNDED_SCOPE:", json.dumps(scope_preview, ensure_ascii=False), flush=True)

        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            _atomic_write_text(scope_file, json.dumps(scope_preview, ensure_ascii=False, indent=2) + "\n")

            funding_db_sha_before = sha(src_funding_db)
            cache_manifest_path = cache_dir / "manifest.json"
            if not cache_manifest_path.is_file():
                raise RuntimeError("cache_v3 manifest.json missing")
            cache_manifest_sha_before = sha(cache_manifest_path)

            _bind_isolated_funding_db(src_funding_db, derived_db, derived_meta)
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

            fmaps, ov_raw = load_funding_db(derived_db)
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
                c4 = o4[:, 3]
                ema, rsi = indicators_ema55_rsi14(c4)
                d30_map = {int(t): j for j, t in enumerate(ts30.tolist())}
                for t in ts30.tolist():
                    ti = int(t)
                    if start_ts <= ti <= end_ts:
                        all_bars_set.add(ti)
                raw[inst] = {
                    "ts4": ts4,
                    "o4": o4,
                    "ema": ema,
                    "rsi": rsi,
                    "d30": (d30_map, o30),
                    "d1h": ({int(t): j for j, t in enumerate(ts1.tolist())}, o1),
                    "d1_set": d1_set,
                    "tickSz": float(info["spec"]["tickSz"]),
                    "maxLever": float(info["spec"].get("maxLever", 10.0)),
                    "fmap": fmaps.get(inst, {}),
                }

            bars = sorted(all_bars_set)
            cands_by_bar, max_lev, cand_stats = build_cands_retest24(raw, start_ts, end_ts, args.candidate)

            arms = {}
            missing_by_scenario = {}
            for name in requested_scenarios:
                risk_id, risk_u, dloss_u, dly = FROZEN_SCENARIOS[name]
                sp = make_retest24_spec(risk_id, risk_u, dloss_u)
                r = b6mod.run_audit_sim_b6(
                    raw,
                    bars,
                    sp,
                    ov_raw_ts=ov_raw,
                    cands_pre=cands_by_bar,
                    max_lev_pre=max_lev,
                    record_events=True,
                    record_trades_detail=True,
                    fill_mode="cross_1tick",
                    delay_first_bar=dly,
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
                    "version": "v1.1",
                    "adapter": "run_retest24_bounded_backtest.py",
                    "candidate": args.candidate,
                    "started_utc": started_utc,
                    "finished_utc": finished_utc,
                    "elapsed_sec": round(time.time() - t0, 2),
                    "transport_blocker_active_entire_run": True,
                    "transport_hits": list(tb.hits),
                    "scope": scope_preview,
                    "symbols_loaded": len(raw),
                    "bars_30m_in_window": len(bars),
                    "candidate_stats": cand_stats,
                    "inputs_unchanged": True,
                    "sha256": {
                        "funding_db": funding_db_sha_after,
                        "cache_manifest": cache_manifest_sha_after,
                        "manifest": sha(manifest_path),
                        "retest24_script": sha(bound["roles"]["retest24_script"]),
                        "shared_risk": sha(bound["roles"]["shared_risk"]),
                        "runner": sha(Path(__file__)),
                    },
                    "missing_funding_gaps": missing_by_scenario,
                    "policy_note": "Offline hard refusal: miss_8h > 0 aborts with exit 2 and writes NO success report.",
                }
                _atomic_write_text(abort_report, json.dumps(abort_payload, ensure_ascii=False, indent=2) + "\n")
                print("ABORT_REPORT_SHA256:", sha(abort_report), flush=True)
                return 2

            result_payload = {
                "status": "PASS",
                "study_id": "BACKTEST-READINESS-01",
                "version": "v1.1",
                "adapter": "run_retest24_bounded_backtest.py",
                "candidate": args.candidate,
                "started_utc": started_utc,
                "finished_utc": finished_utc,
                "elapsed_sec": round(time.time() - t0, 2),
                "transport_blocker_active_entire_run": True,
                "transport_hits": list(tb.hits),
                "scope": scope_preview,
                "symbols_loaded": len(raw),
                "bars_30m_in_window": len(bars),
                "candidate_stats": cand_stats,
                "inputs_unchanged": True,
                "sha256": {
                    "funding_db": funding_db_sha_after,
                    "derived_funding_db": sha(derived_db),
                    "cache_manifest": cache_manifest_sha_after,
                    "manifest": sha(manifest_path),
                    "retest24_script": sha(bound["roles"]["retest24_script"]),
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
            return 0
        except Exception:
            _discard_final_report(final_report, fixed_inputs)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
