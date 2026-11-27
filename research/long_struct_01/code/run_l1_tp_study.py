#!/usr/bin/env python3
"""
Portable entrypoint for LONG-SHORT-SCOPE-01-L1 v1.1 (Single-Factor TP Study).
Uses relative pack paths, environment variables, or CLI flags — zero hardcoded host paths.

Private-pack pre-check is separate from the public-directory static verifier
(offline_static_check.py). Both --dry-check and the study path require explicit
--manifest, --shared-risk, and --orig-long. Integrity checks read files and
compare SHA-256 only. They do not import strategy, shared_risk, or engine modules.
Engine and orig-long modules load only after those checks pass, and only from the
manifest-registered paths. There is no PACK_ROOT/REPRO_MANIFEST.json or
PACK_ROOT/scripts/shared_risk.py default.
Missing funding is a hard error: fetch/backfill raise OFFLINE_RESEARCH_COPY_NETWORK_DISABLED
and never zero-fill or download. No flag re-enables network access.
"""
import argparse, copy, hashlib, importlib.util, json, math, os, shutil, sqlite3, sys, time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path, PurePosixPath
import numpy as np

PACK_ROOT = Path(__file__).resolve().parent.parent

# Manifest keys are relative to the manifest file's parent. Explicit CLI paths
# must resolve to these registered files; engine modules load only from the
# unique manifest entry whose path ends in engine/<filename>.
REQUIRED_EXPLICIT_KEYS = {
    "orig_long": "scripts/FIB_4H_Long_v3.py",
    "shared_risk": "scripts/shared_risk.py",
}
REQUIRED_ENGINE_FILES = (
    "audit_v3_1_full.py",
    "sim_50k_v3_2_sl_fix.py",
    "run_q38_audit_01.py",
    "b6_sim_portable.py",
)
ENGINE_IMPORT_ORDER = (
    ("audit_v3_1_full", "audit_v3_1_full.py"),
    ("sim_50k_v3_2_sl_fix", "sim_50k_v3_2_sl_fix.py"),
    ("run_q38_audit_01", "run_q38_audit_01.py"),
    ("b6_sim_portable", "b6_sim_portable.py"),
)

def _explicit_cli_path(raw):
    """Return a user-supplied path unchanged except for user-home expansion.

    Does not prefix PACK_ROOT and does not append scripts/ or REPRO_MANIFEST.json.
    """
    return Path(raw).expanduser()


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="LONG-SHORT-SCOPE-01-L1 v1.1 portable offline TP study runner",
        epilog=(
            "Pre-check and the study both require explicit --manifest, --shared-risk, and "
            "--orig-long. Those paths must be the manifest-registered files and match that "
            "copy's SHA-256. Relative manifest paths resolve from the manifest file's parent. "
            "This runner does not default those three inputs to PACK_ROOT/REPRO_MANIFEST.json "
            "or PACK_ROOT/scripts/. Integrity failure happens before any strategy or engine "
            "import. Public code/ AST checks are offline_static_check.py."
        ),
    )
    p.add_argument("--orig-long", default=None,
                   help="Explicit path to the FIB_4H_Long_v3.py copy under test. Required. "
                        "No PACK_ROOT/scripts default and no REPRO_ORIG_LONG fallback.")
    p.add_argument("--manifest", default=None,
                   help="Explicit path to REPRO_MANIFEST.json. Required before any module load. "
                        "No PACK_ROOT default. files must be a non-empty object containing every "
                        "required entry, and hashes must match the target copy.")
    p.add_argument("--shared-risk", default=None,
                   help="Explicit path to shared_risk.py. Required. Must be the manifest-registered "
                        "scripts/shared_risk.py file. No PACK_ROOT/scripts default.")
    p.add_argument("--cache-dir", default=os.getenv("REPRO_CACHE_DIR", str(PACK_ROOT / "data" / "cache_v3")),
                   help="Path to EX_USDC_286 cache_v3 directory containing manifest.json & symbol CSV/NPY files")
    p.add_argument("--funding-db", default=os.getenv("REPRO_FUNDING_DB", str(PACK_ROOT / "data" / "funding_archive_l1_isolated.sqlite")),
                   help="Path to funding_archive SQLite database (read/copied to isolated workspace)")
    p.add_argument("--out-dir", default=os.getenv("REPRO_OUT_DIR", str(PACK_ROOT / "out")),
                   help="Output directory for l1_tp_result.json")
    p.add_argument("--dry-check", action="store_true",
                   help="Read-only manifest/SHA-256 pre-check. Does not import strategy, "
                        "shared_risk, or engine modules and does not run offline_static_check.py.")
    args = p.parse_args(argv)
    if args.orig_long:
        args.orig_long_path = _explicit_cli_path(args.orig_long)
        args.orig_long = str(args.orig_long_path)
    if args.manifest:
        args.manifest_path = _explicit_cli_path(args.manifest)
        args.manifest = str(args.manifest_path)
    if args.shared_risk:
        args.shared_risk_path = _explicit_cli_path(args.shared_risk)
        args.shared_risk = str(args.shared_risk_path)
    missing = []
    if not args.orig_long:
        missing.append("--orig-long")
    if not args.manifest:
        missing.append("--manifest")
    if not args.shared_risk:
        missing.append("--shared-risk")
    if missing:
        p.error(
            "explicit path(s) required and missing: "
            + ", ".join(missing)
            + ". Pre-check and the study require --manifest, --shared-risk, and --orig-long "
            "pointing at the manifest-registered target copy (hashes must match that copy). "
            "This public runner does not assume a private PACK_ROOT/scripts layout."
        )
    return args

ARGS = _parse_args()
ORIG_LONG = Path(ARGS.orig_long)
CACHE_DIR = Path(ARGS.cache_dir)
B6_DB = Path(ARGS.funding_db)
OUT_DIR = Path(ARGS.out_dir)
L1_DB = OUT_DIR / "funding_archive_l1_isolated.sqlite"
L1_DB_SOURCE_META = Path(str(L1_DB) + ".source_meta.json")
FINAL_REPORT = OUT_DIR / "l1_tp_result.json"

M30, H1, H4, H8, DAY = 1800000, 3600000, 14400000, 28800000, 86400000
TZ_UTC = timezone.utc
START_TS = int(datetime(2023, 1, 1, 0, 0, tzinfo=TZ_UTC).timestamp() * 1000)
END_TS = int(datetime(2026, 11, 26, 12, 0, tzinfo=TZ_UTC).timestamp() * 1000)

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()

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

def build_cands_fib_long_exact(raw, lookback=24, rsi_lo=55.0, rsi_hi=85.0, entry_level=0.618, lev_cfg=10.0):
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
            if bt < START_TS - 48 * H1 or bt > END_TS:
                continue
            # Contiguous closed bars up to 180 before bt
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
            # Sort key: -dist (deeper pullback first), matching pending_signals.sort(key=lambda x: -x[0])
            cands_by_bar.setdefault(bt, []).append((-dist, 0, inst, float(px_d), False))
    return cands_by_bar, max_lev

def load_orig_module(path: Path):
    spec = importlib.util.spec_from_file_location("fib_long_orig", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("registered orig-long cannot be loaded: " + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def verify_mapping(orig_mod, raw, cands_by_bar):
    """Compare orig FIB_4H_Long_v3.signal() & price_targets() against our exact builder on 30 symbols x 120 bars."""
    class MockAPI:
        def __init__(self, r):
            self.r = r
        def call(self, path, params, private=False):
            inst = params["instId"]
            v = self.r[inst]
            if params["bar"] == "4H":
                # Return candles up to current bar (stored on self.cur_bar)
                ts4, o4 = v["ts4"], v["o4"]
                res = []
                # find index of cur_bar
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
        ts4 = [int(x) for x in v["ts4"].tolist() if START_TS <= int(x) <= END_TS]
        # sample up to 100 bars evenly
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

    # Verify exit price_targets across TP = 2.5%, 4.0%, 6.0% and SL = 4.0%
    exit_checks = 0
    exit_mismatches = 0
    for tp_s in ("0.025", "0.04", "0.06"):
        orig_mod.TP_PCT = D(tp_s)
        orig_mod.SL_PCT = D("0.04")
        for avg_s, tk_s in [("1.2345", "0.0001"), ("0.00456", "0.00001"), ("142.35", "0.01"), ("23.81", "0.001")]:
            otp, osl = orig_mod.price_targets(D(avg_s), D(tk_s))
            etp = align_dec(float(D(avg_s) * (D(1) + D(tp_s))), tk_s)
            esl = align_dec(float(D(avg_s) * (D(1) - D("0.04"))), tk_s)
            exit_checks += 1
            if abs(float(otp) - etp) > 1e-12 or abs(float(osl) - esl) > 1e-12:
                exit_mismatches += 1
    # Restore default
    orig_mod.TP_PCT = D("0.025")
    orig_mod.SL_PCT = D("0.04")
    return {
        "bars_checked": checked,
        "signals_matched": matched_sig,
        "signal_mismatches": mismatches,
        "exit_target_checks": exit_checks,
        "exit_target_mismatches": exit_mismatches,
    }

def load_funding_db(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    fmaps = {}
    ov_raw = {}
    for inst, ts_grid, ts_raw, rate in conn.execute("SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive"):
        fmaps.setdefault(inst, {})[int(ts_grid)] = float(rate)
        ov_raw.setdefault(inst, {})[int(ts_grid)] = int(ts_raw)
    conn.close()
    return fmaps, ov_raw

def fetch_okx_funding(inst: str, min_ts: int, max_ts: int):
    # Permanent offline refusal. No flag or environment variable re-enables network access.
    raise RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: funding fetch/backfill is disabled; missing funding must fail explicitly without zero-fill or network download.")
    rows = []
    after = max_ts + H8
    for _ in range(40):
        url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst}&limit=100&after={after}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = body.get("data", [])
        if not data:
            break
        min_got = None
        for d in data:
            ts_r = int(d["fundingTime"])
            rt = float(d["fundingRate"])
            ts_g = ((ts_r + 900_000) // M30) * M30
            rows.append((inst, ts_g, ts_r, rt))
            if min_got is None or ts_r < min_got:
                min_got = ts_r
        if min_got is None or min_got <= min_ts:
            break
        after = min_got
        time.sleep(0.06)
    return rows

def backfill_missing_funding(db_path: Path, miss_events):
    # Permanent offline refusal. No flag or environment variable re-enables network access.
    # Missing funding fails here, before any zero-fill or download.
    raise RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: funding fetch/backfill is disabled; missing funding must fail explicitly without zero-fill or network download.")
    by_inst = {}
    for (_, inst, t30, kind) in miss_events:
        if kind == "miss_8h":
            by_inst.setdefault(inst, []).append(t30)
    if not by_inst:
        return {"insts_queried": 0, "rows_inserted": 0}
    all_rows = []
    def _job(item):
        inst, ts_list = item
        try:
            return fetch_okx_funding(inst, min(ts_list) - DAY, max(ts_list) + DAY)
        except Exception:
            return []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(_job, by_inst.items()):
            all_rows.extend(res)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    before = cur.execute("SELECT COUNT(*) FROM funding_archive").fetchone()[0]
    cur.executemany(
        "INSERT OR IGNORE INTO funding_archive (inst_id, ts_snapped, ts_raw, rate, source_ym) VALUES (?, ?, ?, ?, 'l1_backfill')",
        all_rows,
    )
    conn.commit()
    after = cur.execute("SELECT COUNT(*) FROM funding_archive").fetchone()[0]
    conn.close()
    return {"insts_queried": len(by_inst), "rows_fetched": len(all_rows), "rows_inserted": after - before}

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
    }

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
    """Read the manifest and hash files. Does not import or execute modules."""
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
    """Import engine modules only from manifest-registered paths."""
    loaded = {}
    for module_name, filename in ENGINE_IMPORT_ORDER:
        rel = bound["engine_keys"][filename]
        loaded[module_name] = _load_registered_module(module_name, bound["files"][rel])
    return loaded


def _paths_overlap(left: Path, right: Path) -> bool:
    """True when two paths are the same file by resolve() or samefile().

    samefile covers existing hardlinks, symlinks, and case-insensitive aliases.
    A missing path still matches when both resolve to the same location.
    """
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


def _output_temp_paths():
    """Derived outputs and the temp siblings this runner writes or deletes."""
    return (
        ("L1_DB", L1_DB),
        ("L1_DB sidecar", L1_DB_SOURCE_META),
        ("L1_DB sidecar temp", Path(str(L1_DB_SOURCE_META) + ".tmp")),
        ("final report", FINAL_REPORT),
        ("final report temp", Path(str(FINAL_REPORT) + ".tmp")),
    )


def _fixed_input_paths(bound):
    """Fixed inputs that must never be deleted, renamed, or used as outputs."""
    items = [
        ("funding-db", B6_DB),
        ("manifest", Path(ARGS.manifest)),
        ("orig-long", Path(ARGS.orig_long)),
        ("shared-risk", Path(ARGS.shared_risk)),
        ("registered orig-long", bound["roles"]["orig_long"]),
        ("registered shared-risk", bound["roles"]["shared_risk"]),
    ]
    for rel, path in bound["files"].items():
        items.append(("manifest entry " + rel, path))
    return items


def _verify_output_paths_disjoint(outputs, fixed_inputs) -> None:
    """Raise before any copy, write, or cleanup when an output aliases an input.

    Output and temp paths must also be pairwise disjoint so one output cannot
    overwrite another. This function does not delete or rename anything.
    """
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
    """Remove only a derived report. Never unlink a path that is a fixed input."""
    for candidate in (path, Path(str(path) + ".tmp")):
        for label, fixed in fixed_inputs:
            if _paths_overlap(candidate, fixed):
                raise RuntimeError(
                    "refusing to delete " + candidate.name
                    + " because it overlaps fixed input " + label
                )
        if candidate.exists():
            candidate.unlink()


def _bind_isolated_funding_db(b6_db: Path, l1_db: Path, meta_path: Path) -> str:
    """Bind a derived L1_DB to the source hash and the derived file's own hash.

    Overlap between the fixed source and the derived path or sidecar aborts
    before copy, reuse, or cleanup. An existing derived file is reused only
    when both recorded hashes match the bytes on disk. A mismatch is not
    overwritten or repaired. A fresh copy prefers an empty derived path.
    """
    try:
        b6_real = b6_db.resolve()
        l1_real = l1_db.resolve()
        meta_real = meta_path.resolve()
    except OSError as exc:
        raise RuntimeError("funding DB path cannot be resolved") from exc
    if b6_real == l1_real or b6_real == meta_real:
        raise RuntimeError(
            "B6_DB overlaps the derived L1_DB or its sidecar; refusing to copy, reuse, or clean up the fixed source"
        )
    if not b6_db.is_file():
        raise RuntimeError("B6_DB source is missing")
    source_sha = sha(b6_db)
    source_name = b6_db.name
    if l1_db.exists():
        if not meta_path.is_file():
            raise RuntimeError(
                "L1_DB exists without source metadata; refusing to reuse or overwrite a derived DB"
            )
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("L1_DB source metadata is unreadable; refusing to overwrite") from exc
        if not isinstance(meta, dict):
            raise RuntimeError("L1_DB source metadata is malformed; refusing to overwrite")
        recorded_source = meta.get("b6_source_sha256")
        recorded_derived = meta.get("derived_l1_db_sha256")
        if not isinstance(recorded_source, str) or recorded_source == "" or not isinstance(recorded_derived, str) or recorded_derived == "":
            raise RuntimeError(
                "L1_DB metadata must contain b6_source_sha256 and derived_l1_db_sha256; refusing to overwrite"
            )
        derived_sha = sha(l1_db)
        if recorded_source != source_sha or recorded_derived != derived_sha:
            raise RuntimeError(
                "L1_DB source or content hash does not match the sidecar; refusing to reuse or overwrite"
            )
        return source_sha
    l1_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(b6_db, l1_db)
    derived_sha = sha(l1_db)
    try:
        _atomic_write_text(meta_path, json.dumps({
            "b6_source_sha256": source_sha,
            "b6_source_name": source_name,
            "derived_l1_db_sha256": derived_sha,
        }, ensure_ascii=False, indent=2))
    except Exception:
        if l1_db.exists() and not _paths_overlap(l1_db, b6_db):
            l1_db.unlink()
        raise
    return source_sha


def main():
    bound = _verify_manifest_bindings(Path(ARGS.manifest), Path(ARGS.orig_long), Path(ARGS.shared_risk))
    if ARGS.dry_check:
        print(json.dumps({
            "dry_check": "PASS",
            "pack_root": str(bound["target_root"]),
            "manifest": str(bound["manifest"]),
            "shared_risk": str(bound["roles"]["shared_risk"]),
            "orig_long": str(bound["roles"]["orig_long"]),
            "files_verified": bound["files_verified"],
            "required_explicit_entries": list(REQUIRED_EXPLICIT_KEYS.values()),
            "engine_entries": bound["engine_keys"],
            "mismatches": 0,
            "modules_executed": False,
            "shared_risk_loaded": False,
            "engine_loaded": False,
            "path_note": "explicit paths are the manifest-registered files; hashes match; no module import",
        }, ensure_ascii=False, indent=2))
        return
    fixed_inputs = _fixed_input_paths(bound)
    _verify_output_paths_disjoint(_output_temp_paths(), fixed_inputs)
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        _bind_isolated_funding_db(B6_DB, L1_DB, L1_DB_SOURCE_META)
        loaded = _load_runtime_modules(bound)
        b6mod = loaded["b6_sim_portable"]
        if not callable(getattr(b6mod, "run_audit_sim_b6", None)):
            raise RuntimeError("registered b6_sim_portable is missing callable run_audit_sim_b6")
        t0 = time.time()
        utc_start = datetime.now(TZ_UTC).isoformat()
        orig_sha = sha(bound["roles"]["orig_long"])
        b6_db_sha_before = sha(B6_DB)
        manifest_sha = sha(CACHE_DIR / "manifest.json")
        orig_mod = load_orig_module(bound["roles"]["orig_long"])
        baseline_defaults = {
            "ENTRY_LEVEL": str(orig_mod.ENTRY_LEVEL),
            "TP_PCT": str(orig_mod.TP_PCT),
            "SL_PCT": str(orig_mod.SL_PCT),
            "STOP_DIST": str(orig_mod.STOP_DIST),
            "LOOKBACK_BARS": int(orig_mod.LOOKBACK_BARS),
            "RSI_LO": str(orig_mod.RSI_LO),
            "RSI_HI": str(orig_mod.RSI_HI),
            "ORDER_TTL_HOURS": float(orig_mod.ORDER_TTL_HOURS),
            "MAX_OPEN_TRADES": int(orig_mod.MAX_OPEN_TRADES),
            "RISK_PER_TRADE_USDT": str(orig_mod.RISK_PER_TRADE),
            "MAX_TOTAL_RISK_USDT": str(orig_mod.MAX_TOTAL_RISK),
            "DAILY_LOSS_LIMIT_USDT": str(orig_mod.DAILY_LOSS_LIMIT),
            "DAILY_RESET": "UTC 00:00 (ts // 86400000)",
            "LOSS_STREAK_LIMIT": int(orig_mod.LOSS_STREAK_LIMIT),
            "LOSS_STREAK_PAUSE_HOURS": float(orig_mod.LOSS_STREAK_PAUSE_HOURS),
            "MAX_NEW_ENTRIES_PER_DAY": int(orig_mod.MAX_NEW_ENTRIES_PER_DAY),
            "BTC_FILTER": str(orig_mod.BTC_FILTER),
            "EMA_PERIOD": 60,
            "EXCLUDED_BASES": sorted(list(orig_mod.EXCLUDED_BASES)),
            "comment_vs_code_note": "Code default ENTRY_LEVEL=0.618 (comments mention 0.94); TP=2.5%, SL=4.0%, 24 slots, 150U/trade, 600U UTC daily loss, loss streak 3/24H.",
        }

        # Load EX_USDC_286 raw data
        manifest = json.loads((CACHE_DIR / "manifest.json").read_text(encoding="utf-8"))
        fmaps, ov_raw = load_funding_db(L1_DB)
        raw = {}
        all_bars_set = set()
        for inst, info in manifest["symbols"].items():
            if inst == "USDC-USDT-SWAP":
                continue
            z = np.load(CACHE_DIR / f"{inst}.npz")
            ts30, o30 = z["ts30"], z["ohlc30"]
            ts4, o4 = z["ts4"], z["ohlc4"]
            ts1, o1 = z["ts1"], z["ohlc1"]
            d1_set = set(int(x) for x in z["d1_ts"].tolist())
            d30_map = {int(t): j for j, t in enumerate(ts30.tolist())}
            ts4_map = {int(t): j for j, t in enumerate(ts4.tolist())}
            for t in ts30.tolist():
                ti = int(t)
                if START_TS <= ti <= END_TS:
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
        print(f"Loaded {len(raw)} symbols (EX_USDC_286), {len(bars)} 30m bars in {time.time()-t0:.1f}s", flush=True)

        # Build exact FIB_4H_Long_v3 candidates
        cands_by_bar, max_lev = build_cands_fib_long_exact(raw)
        total_cands = sum(len(v) for v in cands_by_bar.values())
        print(f"Built {total_cands} exact fib_long candidates across {len(cands_by_bar)} 4H bars in {time.time()-t0:.1f}s", flush=True)

        # Step 1: Mapping verification
        mapping_check = verify_mapping(orig_mod, raw, cands_by_bar)
        print("Mapping verification:", json.dumps(mapping_check), flush=True)
        if mapping_check["signal_mismatches"] != 0:
            raise RuntimeError("Signal mismatch! " + str(mapping_check))
        if mapping_check["exit_target_mismatches"] != 0:
            raise RuntimeError("Exit target mismatch! " + str(mapping_check))

        def make_spec(tp_pct: float):
            return {
                "initial_capital_u": 50000.0,
                "leverage": 10.0,
                "mmr_approx": 0.01,
                "maker_fee": 0.0002,
                "taker_fee": 0.0005,
                "slip_mkt": 0.0003,
                "legs": [{
                    "mode": "fib_long",
                    "tp_pct": tp_pct,
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

        # Pass 1: detect missing 8H funding events across all 6 scenarios
        scenarios = [
            ("TP_2.5pct|cross_1tick", 0.025, False),
            ("TP_2.5pct|delay1bar", 0.025, True),
            ("TP_4.0pct|cross_1tick", 0.040, False),
            ("TP_4.0pct|delay1bar", 0.040, True),
            ("TP_6.0pct|cross_1tick", 0.060, False),
            ("TP_6.0pct|delay1bar", 0.060, True),
        ]

        all_miss = set()
        for name, tp, dly in scenarios:
            r = b6mod.run_audit_sim_b6(
                raw, bars, make_spec(tp), ov_raw_ts=ov_raw,
                cands_pre=cands_by_bar, max_lev_pre=max_lev,
                record_events=True, fill_mode="cross_1tick", delay_first_bar=dly
            )
            miss_n = sum(1 for e in r["events_set"] if e[3] == "miss_8h")
            all_miss.update(e for e in r["events_set"] if e[3] == "miss_8h")
            print(f"[Pass1] {name}: trades={r['trades']} eq={r['final_eq_u']:.2f} miss_8h={miss_n}", flush=True)

        backfill_info = {"insts_queried": 0, "rows_inserted": 0}
        if all_miss:
            print(f"Backfilling {len(all_miss)} missing 8H funding events into isolated L1 DB...", flush=True)
            backfill_info = backfill_missing_funding(L1_DB, all_miss)
            print("Backfill info:", json.dumps(backfill_info), flush=True)
            fmaps, ov_raw = load_funding_db(L1_DB)
            for inst in raw:
                raw[inst]["fmap"] = fmaps.get(inst, {})

        # Pass 2: final 6 replays with updated isolated L1 funding DB
        arms = {}
        for name, tp, dly in scenarios:
            r = b6mod.run_audit_sim_b6(
                raw, bars, make_spec(tp), ov_raw_ts=ov_raw,
                cands_pre=cands_by_bar, max_lev_pre=max_lev,
                record_events=False, record_trades_detail=True, fill_mode="cross_1tick", delay_first_bar=dly
            )
            arms[name] = summarize_run(r)
            s = arms[name]
            print(f"[Final] {name}: trades={s['closed_trades']} win={s['win_rate_pct']}% net={s['closed_net_u']} eq={s['final_eq_u']} ({s['ret_eq_pct']}%) cagr={s['cagr_eq_pct']}% mdd={s['mtm_mdd_pct']}% pf={s['pf']} ev={s['expectancy_u']} f_8h={s['f_ev_real_8h']} f_non8h={s['f_ev_real_non8h']} miss_8h={s['f_ev_miss_8h']}", flush=True)

        b6_db_sha_after = sha(B6_DB)
        if b6_db_sha_before != b6_db_sha_after:
            raise RuntimeError("B6 DB modified!")

        utc_end = datetime.now(TZ_UTC).isoformat()
        out = {
            "work_id": "LONG-SHORT-SCOPE-01-L1",
            "version": "v1.1",
            "worker": "策略組",
            "utc_start": utc_start,
            "utc_end": utc_end,
            "elapsed_sec": round(time.time() - t0, 2),
            "window_utc": "2023-01-01 00:00 UTC ~ 2026-11-26 12:00 UTC",
            "oos_note": "Historical diagnostic only (includes viewed 2026-11-15~11-26 window); NOT new out-of-sample.",
            "universe": "EX_USDC_286 (historical delisted preserved, USDC-USDT-SWAP excluded)",
            "capital_and_risk": "50,000 USDT, 10x cross, no top-up, exact FIB_4H_Long_v3.py defaults (24 slots, 150U/trade, 600U UTC daily loss, loss streak 3/24H, SL 4%, TTL 48H)",
            "funding_note": "已取得官方檔案內事件全數匹配，跨頻率（非8H）分母完整性待驗；未補零、未承諾100%。",
            "limitations": [
                "缺歷史 BBO，post_only 實際可否掛入與排隊順位未知",
                "cross_1tick 僅為穿價下界檢驗，不證明實盤全量成交",
                "歷史 MMR 採 1% 近似、歷史 tick 採現有快照、非 8H 資金費分母完整性待驗",
                "delay1bar 為敏感度測試而非真實延遲",
            ],
            "sha256": {
                "orig_FIB_4H_Long_v3.py": orig_sha,
                "cache_v3_manifest.json": manifest_sha,
                "b6_db_unchanged": b6_db_sha_after,
                "l1_isolated_funding_db": sha(L1_DB),
                "script_run_l1_tp_study.py": sha(Path(__file__)),
            },
            "baseline_defaults_verified": baseline_defaults,
            "mapping_verification": mapping_check,
            "total_fib_long_candidates": total_cands,
            "funding_backfill": backfill_info,
            "arms": arms,
        }
        _atomic_write_text(FINAL_REPORT, json.dumps(out, ensure_ascii=False, indent=2))
        print("OUTPUT_SHA256:", sha(FINAL_REPORT), flush=True)
    except Exception:
        _discard_final_report(FINAL_REPORT, fixed_inputs)
        raise

if __name__ == "__main__":
    main()
