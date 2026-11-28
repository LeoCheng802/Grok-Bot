#!/usr/bin/env python3
"""BACKTEST-READINESS-01 v1.17 | COMBO_L02_OPT01_SHARED_50K_10X offline runner.

One shared account, NOT two independent 50,000 USDT books added together:
  * leg 0 (long)  = LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT  (run_long_struct_bounded_backtest.py, unchanged rules/defaults)
  * leg 1 (short) = RETEST24_OPT_01_BEARISH_CLOSE_POS   (run_retest24_bounded_backtest.py, unchanged rules)
                    sized by the frozen R1_150U (150U / 600U) or R2_100U (100U / 400U) spec; R2 is the comparison arm.
Both legs run inside ONE call of the registered B6/Q38 engine (patched copy, see _build_combo_sim):
  * one realised equity, one MTM equity / drawdown, one initial-margin pool (pending + open, both legs),
    one liquidation check, identical fair cost (maker 0.02%, taker 0.05%, slip 0.03%, MMR 1%, 10x cap);
  * combo-level gates on top of each leg's own frozen rules (defaults taken from the registered
    shared_risk.RiskLedger defaults: 12 slots long+short combined, 600U realised daily loss per Taipei day):
      - global active slots (open positions + resting entry orders, both legs),
      - global realised daily loss (UTC+8 day, net incl. fee and booked funding),
      - same-instrument cross-leg policy (default block_any: one instrument, one leg at a time),
      - deterministic cross-leg priority when both legs signal on the same 4H bar (default long_first),
      - uncomputable windows (e.g. delisted instruments) block new entries and flag overlapping positions.

v1.15 preliminary-data policy (data mostly complete -> run, annotate gaps):
  * missing funding rates stay UNKNOWN: never zero-filled, never interpolated, no symbol dropped;
    the engine books only rates present in the funding DB, so any result with unknown funding is a
    CONDITIONAL scenario (unknown funding not booked) and must not be called true net performance;
  * missing 8H grid events are listed in full (local details), no abort;
  * funding-month inventory: ONLY complete == "true" counts as complete; "false" / blank / anything else = not complete;
  * inventory sub_reason rest_51001_instrument_not_listed (e.g. RVN 2026-11) -> whole CST month treated as an
    uncomputable window (exact delisting time unknown); extra windows can be passed with --uncomputable-windows.

Output contract: --out-dir must be a NEW isolated directory (absent or empty); combo_result.json exists only
after a complete run; any failure leaves no result file and no *.tmp. Zero network (outer TransportBlocker),
zero credentials, no order/exchange API. Results are always labelled PRELIMINARY (never PASS).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

RUNNER_VERSION = "v1.17"
STUDY_ID = "BACKTEST-READINESS-01"
COMBO_ID = "COMBO_L02_OPT01_SHARED_50K_10X"
LONG_CANDIDATE = "LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT"
SHORT_CANDIDATE = "RETEST24_OPT_01_BEARISH_CLOSE_POS"
SHORT_SIZINGS = {"R1_150U": ("R1", 150.0, 600.0), "R2_100U": ("R2", 100.0, 400.0)}
FILL_MODES = {"cross_1tick": False, "delay1bar": True}
DEFAULT_SCENARIOS = "R1_150U|cross_1tick,R1_150U|delay1bar,R2_100U|cross_1tick,R2_100U|delay1bar"
UNCOMPUTABLE_SUB_REASONS = ("rest_51001_instrument_not_listed",)
INVENTORY_REQUIRED_COLS = ("inst_id", "month_cst", "complete")

H1, H4, H8, DAY = 3600000, 14400000, 28800000, 86400000
TZ_UTC = timezone.utc
TZ_CST = timezone(timedelta(hours=8))
COST_KEYS = ("initial_capital_u", "leverage", "mmr_approx", "maker_fee", "taker_fee", "slip_mkt")

RESULT_NAME = "combo_result.json"
DETAILS_NAME = "combo_local_details.json"
SCOPE_NAME = "combo_scope.json"
DERIVED_DB_NAME = "funding_archive_combo_isolated.sqlite"
DERIVED_META_NAME = "funding_archive_combo_isolated.meta.json"


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def _iso(ts_ms):
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=TZ_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cst_month(ts_ms: int) -> str:
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=TZ_CST).strftime("%Y-%m")


def _cst_month_start_ms(month: str) -> int:
    y, m = month.split("-")
    return int(datetime(int(y), int(m), 1, tzinfo=TZ_CST).timestamp() * 1000)


def _next_month(month: str) -> str:
    y, m = (int(x) for x in month.split("-"))
    return "%04d-%02d" % (y + (m // 12), (m % 12) + 1)


def _months_spanned(a_ms: int, b_ms: int):
    """CST months touched by the funding interval (a, b]; empty when b <= a."""
    if b_ms <= a_ms:
        return []
    first, last = _cst_month(a_ms + 1), _cst_month(b_ms)
    out, cur = [], first
    while True:
        out.append(cur)
        if cur == last or len(out) > 1200:
            break
        cur = _next_month(cur)
    return out


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("adapter module cannot be loaded: " + path.name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def _require_fresh_out_dir(out_dir: Path) -> None:
    """Every run needs a NEW isolated output directory (old evidence is never mixed or overwritten)."""
    if out_dir.is_symlink():
        raise RuntimeError("out-dir must be a new isolated directory, not a symlink; refusing before any write")
    if out_dir.exists():
        if not out_dir.is_dir():
            raise RuntimeError("out-dir exists and is not a directory; refusing before any write")
        if any(out_dir.iterdir()):
            raise RuntimeError(
                "out-dir already contains files (possible stale result/abort evidence); "
                "every run needs a NEW isolated out-dir; refusing before any write"
            )


def load_funding_inventory(path: Path):
    """Parse the funding-month inventory. Only complete == 'true' (exact) counts as complete."""
    inv = {}
    uncomputable = {}
    stats = {"rows": 0, "complete_true": 0, "complete_false": 0, "complete_blank": 0, "complete_other": 0}
    with open(path, "r", encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames or []
        miss = [c for c in INVENTORY_REQUIRED_COLS if c not in cols]
        if miss:
            raise RuntimeError("funding inventory missing columns: " + ", ".join(miss))
        for row in rd:
            stats["rows"] += 1
            inst = (row.get("inst_id") or "").strip()
            month = (row.get("month_cst") or "").strip()
            if not inst or len(month) != 7 or month[4] != "-":
                raise RuntimeError("funding inventory row has invalid inst_id/month_cst")
            raw_c = row.get("complete")
            raw_c = "" if raw_c is None else raw_c
            if raw_c == "true":
                stats["complete_true"] += 1
                status = "complete_true"
            elif raw_c == "false":
                stats["complete_false"] += 1
                status = "complete_false"
            elif raw_c == "":
                stats["complete_blank"] += 1
                status = "unknown_blank"
            else:
                stats["complete_other"] += 1
                status = "unknown_unrecognised_value"
            rec = {
                "status": status,
                "class": (row.get("class") or "").strip(),
                "sub_reason": (row.get("sub_reason") or "").strip(),
            }
            key = (inst, month)
            if key in inv and inv[key] != rec:
                raise RuntimeError("funding inventory has conflicting duplicate rows for " + inst + " " + month)
            inv[key] = rec
            if rec["sub_reason"] in UNCOMPUTABLE_SUB_REASONS:
                uncomputable.setdefault(inst, []).append({
                    "from_ms": _cst_month_start_ms(month),
                    "to_ms": None,
                    "reason": "inventory:" + rec["sub_reason"] + ":" + month + " (exact delisting time unknown; whole CST month onward)",
                })
    return inv, uncomputable, stats


def load_uncomputable_windows(path: Path, parse_utc_ms):
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("windows") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise RuntimeError("uncomputable windows JSON must be a list or {\"windows\": [...]}")
    out = {}
    for it in items:
        if not isinstance(it, dict) or not it.get("inst_id") or not it.get("from_utc"):
            raise RuntimeError("uncomputable window entry needs inst_id and from_utc")
        a = parse_utc_ms(str(it["from_utc"]))
        b = parse_utc_ms(str(it["to_utc"])) if it.get("to_utc") else None
        if b is not None and b <= a:
            raise RuntimeError("uncomputable window to_utc must be > from_utc")
        out.setdefault(str(it["inst_id"]), []).append({"from_ms": a, "to_ms": b, "reason": str(it.get("reason") or "explicit")})
    return out


# ---------------------------------------------------------------------------------------------
# combo engine: patched copy of the registered b6 engine (the registered files are not modified)
# ---------------------------------------------------------------------------------------------

def _combo_init(ctrl):
    if ctrl is None:
        return None
    return {
        "global_max_slots": int(ctrl["global_max_slots"]),
        "global_daily_loss_u": float(ctrl["global_daily_loss_u"]),
        "same_inst_policy": ctrl["same_inst_policy"],
        "leg_sides": list(ctrl["leg_sides"]),
        "uncomputable": ctrl.get("uncomputable") or {},
        "gday": {},
        "blocked": {},
        "events": [],
    }


def _combo_block(cb, reason, li, inst, t30, extra=None):
    d = cb["blocked"].setdefault(reason, {})
    d[str(li)] = d.get(str(li), 0) + 1
    ev = {"reason": reason, "leg": li, "inst_id": inst, "ts_ms": int(t30)}
    if extra:
        ev.update(extra)
    cb["events"].append(ev)
    return True


def _combo_gate(cb, li, inst, t30, pos, pend, legs):
    for w in cb["uncomputable"].get(inst, ()):
        if w["from_ms"] <= t30 and (w["to_ms"] is None or t30 < w["to_ms"]):
            return _combo_block(cb, "uncomputable_window", li, inst, t30, {"window_reason": w["reason"]})
    holders = [(k, "open") for k in pos if k[1] == inst and k[0] != li]
    holders += [(k, "pending", od) for k, od in pend.items() if k[1] == inst and k[0] != li]
    for h in holders:
        k, state = h[0], h[1]
        same_side = cb["leg_sides"][k[0]] == cb["leg_sides"][li]
        if cb["same_inst_policy"] == "block_any" or same_side:
            same_bar = state == "pending" and int(h[2]["pts"]) == int(t30)
            return _combo_block(cb, "same_bar_cross_leg_same_inst" if same_bar else "same_inst_held_by_other_leg",
                                li, inst, t30, {"holder_leg": k[0], "holder_state": state})
    if len(pos) + len(pend) >= cb["global_max_slots"]:
        return _combo_block(cb, "global_slots_full", li, inst, t30, {"active": len(pos) + len(pend)})
    day = (int(t30) + 8 * H1) // DAY
    if cb["gday"].get(day, 0.0) <= -cb["global_daily_loss_u"]:
        return _combo_block(cb, "global_daily_loss_taipei_day", li, inst, t30, {"day_net_u": round(cb["gday"][day], 6)})
    return False


def _combo_book(cb, t30, pnl):
    if cb is None:
        return
    day = (int(t30) + 8 * H1) // DAY
    cb["gday"][day] = cb["gday"].get(day, 0.0) + float(pnl)


def _combo_export(cb):
    if cb is None:
        return None
    return {
        "blocked_counts": cb["blocked"],
        "blocked_events": cb["events"],
        "taipei_day_realised_net_u": {
            datetime.fromtimestamp(d * DAY / 1000.0, tz=TZ_UTC).strftime("%Y-%m-%d"): round(v, 6)
            for d, v in sorted(cb["gday"].items())
        },
    }


_PATCHES = (
    ("signature",
     'def run_audit_sim_b6(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False, fill_mode="cross_1tick", delay_first_bar=False):',
     'def run_audit_sim_combo(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False, fill_mode="cross_1tick", delay_first_bar=False, combo=None):',
     1),
    ("init",
     '    trades, last_c = [], {}; _ord_log = []; _skip_fb_cross = 0; _same_bar_sl = 0',
     '    trades, last_c = [], {}; _ord_log = []; _skip_fb_cross = 0; _same_bar_sl = 0; _cb = _combo_init(combo)',
     1),
    ("gate",
     '                if (li, inst) in pos or (li, inst) in pend or blk.get((li, inst), 0) > t30 or t30 < pause_u[li]: continue\n',
     '                if (li, inst) in pos or (li, inst) in pend or blk.get((li, inst), 0) > t30 or t30 < pause_u[li]: continue\n'
     '                if _cb is not None and _combo_gate(_cb, li, inst, t30, pos, pend, legs): continue\n',
     1),
    ("book",
     'dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl;',
     'dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl; _combo_book(_cb, t30, pnl);',
     2),
    ("leg_expired", '"outcome": "expired"', '"outcome": "expired", "leg": k[0]', 1),
    ("leg_margin_rej", '"outcome": "margin_rej"', '"outcome": "margin_rej", "leg": li', 1),
    ("leg_filled", '"outcome": "filled"', '"outcome": "filled", "leg": li', 1),
    ("leg_pend_at_end", '"outcome": "pend_at_end"', '"outcome": "pend_at_end", "leg": li', 1),
    ("export",
     '    out["_ord_log"] = _ord_log\n',
     '    out["_ord_log"] = _ord_log\n'
     '    out["_combo"] = _combo_export(_cb)\n'
     '    out["_combo_open"] = [{"leg": k[0], "inst": k[1], "side": p["side"], "ets": p["ets"]} for k, p in pos.items()]\n',
     1),
)


def _build_combo_sim(b6mod):
    src = getattr(b6mod, "_sim_src", None)
    q38a = getattr(b6mod, "q38a", None)
    if not isinstance(src, str) or q38a is None:
        raise RuntimeError("registered b6_sim_portable does not expose _sim_src/q38a; cannot build the shared-account combo engine")
    for name, old, new, cnt in _PATCHES:
        if src.count(old) != cnt:
            raise RuntimeError("combo engine patch anchor mismatch: " + name)
        src = src.replace(old, new)
    ns = dict(q38a.__dict__)
    ns.update({"_combo_init": _combo_init, "_combo_gate": _combo_gate, "_combo_book": _combo_book, "_combo_export": _combo_export})
    exec(compile(src, "<run_audit_sim_combo>", "exec"), ns)
    return ns["run_audit_sim_combo"], hashlib.sha256(src.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------
# annotations (v1.15)
# ---------------------------------------------------------------------------------------------

def _funding_status_for_months(inv, inst, months):
    if inv is None:
        return "inventory_not_supplied", {m: "inventory_not_supplied" for m in months}
    per = {m: (inv.get((inst, m)) or {"status": "unknown_not_in_inventory"})["status"] for m in months}
    if not months:
        return "no_funding_interval", per
    return ("complete_by_batch_scope" if all(v == "complete_true" for v in per.values()) else "incomplete_or_unknown"), per


def _overlaps(windows, a_ms, b_ms):
    hits = []
    for w in windows or ():
        lo, hi = w["from_ms"], w["to_ms"]
        if b_ms >= lo and (hi is None or a_ms < hi):
            hits.append(w["reason"])
    return hits


def annotate_arm(r, leg_names, inv, unc, last_bar):
    trades_out = []
    flags = {"funding_incomplete_or_unknown_trades": 0, "uncomputable_trades": 0, "no_funding_interval_trades": 0}
    side_to_leg = {"long": 0, "short": 1}
    for i, t in enumerate(r.get("_trades", [])):
        inst, ets, xts = t["inst"], int(t["ets"]), int(t["xts"])
        months = _months_spanned(ets, xts)
        fst, per = _funding_status_for_months(inv, inst, months)
        unc_hits = _overlaps(unc.get(inst), ets, xts)
        if fst == "incomplete_or_unknown" or fst == "inventory_not_supplied":
            flags["funding_incomplete_or_unknown_trades"] += 1
        if fst == "no_funding_interval":
            flags["no_funding_interval_trades"] += 1
        if unc_hits:
            flags["uncomputable_trades"] += 1
        leg = side_to_leg[t["side"]]
        trades_out.append({
            "seq": i + 1, "leg": leg, "leg_name": leg_names[leg], "inst_id": inst, "side": t["side"],
            "ets_ms": ets, "ets_utc": _iso(ets), "xts_ms": xts, "xts_utc": _iso(xts),
            "net_pnl_u": round(float(t["net"]), 6), "fee_u": round(float(t["fee"]), 6), "fund_booked_u": round(float(t["fund"]), 6),
            "reason": t.get("reason"), "funding_status": fst, "funding_months_cst": per,
            "computability": "不可計算(UNCOMPUTABLE)" if unc_hits else "computable", "uncomputable_reasons": unc_hits,
        })
    open_out = []
    for p in r.get("_combo_open", []):
        ets = int(p["ets"])
        months = _months_spanned(ets, int(last_bar))
        fst, per = _funding_status_for_months(inv, p["inst"], months)
        unc_hits = _overlaps(unc.get(p["inst"]), ets, int(last_bar))
        if unc_hits:
            flags["uncomputable_trades"] += 1
        open_out.append({"leg": p["leg"], "leg_name": leg_names[p["leg"]], "inst_id": p["inst"], "side": p["side"],
                         "ets_ms": ets, "ets_utc": _iso(ets), "funding_status": fst, "funding_months_cst": per,
                         "computability": "不可計算(UNCOMPUTABLE)" if unc_hits else "computable", "uncomputable_reasons": unc_hits})
    miss = sorted(e for e in r.get("events_set", set()) if len(e) >= 4 and e[3] == "miss_8h")
    miss_out = [{"leg": int(e[0]), "inst_id": e[1], "ts_ms": int(e[2]), "ts_utc": _iso(e[2]), "kind": e[3]} for e in miss]
    return trades_out, open_out, miss_out, flags


def _leg_stats(trades):
    n = len(trades)
    net = sum(t["net_pnl_u"] for t in trades)
    wins = [t["net_pnl_u"] for t in trades if t["net_pnl_u"] > 0]
    losses = [-t["net_pnl_u"] for t in trades if t["net_pnl_u"] < 0]
    return {
        "closed_trades": n,
        "win_rate_pct": round(100.0 * len(wins) / n, 2) if n else 0.0,
        "net_pnl_u_booked": round(net, 2),
        "profit_factor": (round(sum(wins) / sum(losses), 3) if losses else ("INF" if wins else 0.0)),
        "fee_u": round(sum(t["fee_u"] for t in trades), 2),
        "fund_booked_u": round(sum(t["fund_booked_u"] for t in trades), 2),
    }


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def parse_args(argv=None):
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="BACKTEST-READINESS-01 v1.17 shared 50,000 USDT / 10x combo (LONG_STRUCT_02 + RETEST24 OPT-01) offline runner")
    p.add_argument("--manifest", required=True, help="REPRO_MANIFEST.json (registers RETEST24 script, shared_risk.py, engine files)")
    p.add_argument("--retest24-script", required=True)
    p.add_argument("--shared-risk", required=True)
    p.add_argument("--cache-dir")
    p.add_argument("--funding-db")
    p.add_argument("--out-dir", help="NEW isolated output directory (must be absent or empty)")
    p.add_argument("--input-manifest", default="", help="per-symbol NPZ sha256/size_bytes manifest")
    p.add_argument("--symbols", default="", help="comma list; empty = all cache symbols excl. USDC-USDT-SWAP (EX_USDC_286)")
    p.add_argument("--start-utc", default="2023-01-01T00:00:00Z")
    p.add_argument("--end-utc", default="2026-11-26T12:00:00Z")
    p.add_argument("--scenarios", default=DEFAULT_SCENARIOS, help="comma list of <R1_150U|R2_100U>|<cross_1tick|delay1bar>")
    p.add_argument("--global-max-slots", type=int, default=12, help="open positions + resting entries, both legs (shared_risk default 12)")
    p.add_argument("--global-daily-loss-u", type=float, default=600.0, help="realised net loss per Taipei day, both legs (shared_risk default 600)")
    p.add_argument("--same-inst-policy", choices=("block_any", "allow_opposite"), default="block_any")
    p.add_argument("--leg-priority", choices=("long_first", "short_first"), default="long_first")
    p.add_argument("--funding-inventory", default="", help="funding month inventory CSV (only complete==true counts as complete)")
    p.add_argument("--uncomputable-windows", default="", help="optional JSON list of {inst_id, from_utc, to_utc?, reason}")
    p.add_argument("--long-adapter", default=str(here / "run_long_struct_bounded_backtest.py"))
    p.add_argument("--short-adapter", default=str(here / "run_retest24_bounded_backtest.py"))
    p.add_argument("--dry-check", action="store_true", help="verify manifest bindings and parse scope only")
    return p.parse_args(argv)


def main(argv=None) -> int:
    t0 = time.time()
    started_utc = datetime.now(TZ_UTC).isoformat()
    args = parse_args(argv)
    long_path = Path(args.long_adapter).expanduser().resolve()
    short_path = Path(args.short_adapter).expanduser().resolve()
    long_sha_before, short_sha_before = sha(long_path), sha(short_path)
    short_mod = _load_module("combo_short_adapter_retest24", short_path)

    with short_mod.TransportBlocker() as tb:
        long_mod = _load_module("combo_long_adapter_long_struct", long_path)
        manifest_path = Path(args.manifest).expanduser()
        retest_path = Path(args.retest24_script).expanduser()
        shared_risk_path = Path(args.shared_risk).expanduser()
        bound = short_mod._verify_manifest_bindings(manifest_path, retest_path, shared_risk_path)

        scen = [s.strip() for s in args.scenarios.split(",") if s.strip()]
        if not scen:
            raise RuntimeError("at least one scenario is required")
        for s in scen:
            parts = s.split("|")
            if len(parts) != 2 or parts[0] not in SHORT_SIZINGS or parts[1] not in FILL_MODES:
                raise RuntimeError("unsupported scenario: " + s)
        if len(set(scen)) != len(scen):
            raise RuntimeError("duplicate scenario")
        if args.global_max_slots < 1:
            raise RuntimeError("global-max-slots must be >= 1")
        if not (args.global_daily_loss_u > 0):
            raise RuntimeError("global-daily-loss-u must be > 0")
        start_ts = short_mod.parse_utc_ms(args.start_utc)
        end_ts = short_mod.parse_utc_ms(args.end_utc)
        if end_ts < start_ts:
            raise RuntimeError("end-utc must be >= start-utc")
        requested_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

        scope = {
            "study_id": STUDY_ID, "version": RUNNER_VERSION, "combo_id": COMBO_ID,
            "capital_model": "SINGLE_SHARED_ACCOUNT_50000U_10X_ONE_EQUITY_ONE_MARGIN_POOL (not two books added)",
            "legs": {"0": {"name": LONG_CANDIDATE, "side": "long"}, "1": {"name": SHORT_CANDIDATE, "side": "short"}},
            "scenarios": scen, "start_utc": args.start_utc, "end_utc": args.end_utc,
            "universe": requested_symbols if requested_symbols else "ALL_CACHE_EX_USDC (EX_USDC_286)",
            "global_max_slots": args.global_max_slots, "global_daily_loss_u": args.global_daily_loss_u,
            "global_daily_loss_day": "Asia/Taipei (UTC+8) calendar day, realised net incl. fee and booked funding",
            "same_inst_policy": args.same_inst_policy, "leg_priority": args.leg_priority,
            "funding_inventory_supplied": bool(args.funding_inventory),
            "started_utc": started_utc,
        }
        print("COMBO_SCOPE:", json.dumps(scope, ensure_ascii=False), flush=True)
        if args.dry_check:
            print(json.dumps({"dry_check": "PASS", "files_verified": bound["files_verified"], "scope": scope,
                              "transport_hits": list(tb.hits)}, ensure_ascii=False, indent=2), flush=True)
            return 0
        if not args.cache_dir or not args.funding_db or not args.out_dir:
            raise RuntimeError("--cache-dir, --funding-db and --out-dir are required unless --dry-check")

        cache_dir = Path(args.cache_dir).expanduser()
        src_db = Path(args.funding_db).expanduser()
        out_dir = Path(args.out_dir).expanduser()
        _require_fresh_out_dir(out_dir)

        derived_db = out_dir / DERIVED_DB_NAME
        derived_meta = out_dir / DERIVED_META_NAME
        scope_file = out_dir / SCOPE_NAME
        result_file = out_dir / RESULT_NAME
        details_file = out_dir / DETAILS_NAME
        outputs = [("derived_db", derived_db), ("derived_meta", derived_meta), ("derived_meta.tmp", Path(str(derived_meta) + ".tmp")),
                   ("scope", scope_file), ("scope.tmp", Path(str(scope_file) + ".tmp")),
                   ("result", result_file), ("result.tmp", Path(str(result_file) + ".tmp")),
                   ("details", details_file), ("details.tmp", Path(str(details_file) + ".tmp"))]

        cache_manifest_path = cache_dir / "manifest.json"
        if not cache_manifest_path.is_file():
            raise RuntimeError("cache manifest.json missing")
        inv_path = Path(args.funding_inventory).expanduser() if args.funding_inventory else None
        unc_path = Path(args.uncomputable_windows).expanduser() if args.uncomputable_windows else None
        input_manifest_path, input_manifest_entries = short_mod._load_optional_input_manifest(args.input_manifest)
        cache_manifest = json.loads(cache_manifest_path.read_text(encoding="utf-8"))
        symbols_dict = cache_manifest["symbols"]
        if requested_symbols:
            missing = [s for s in requested_symbols if s not in symbols_dict]
            if missing:
                raise RuntimeError("requested symbols missing from cache manifest: " + ", ".join(missing))
            ordered_syms = requested_symbols
        else:
            ordered_syms = [s for s in symbols_dict.keys() if s != "USDC-USDT-SWAP"]

        fixed_inputs = [("funding_db", src_db), ("manifest", manifest_path), ("retest24_script", retest_path),
                        ("shared_risk", shared_risk_path), ("cache_manifest", cache_manifest_path),
                        ("long_adapter", long_path), ("short_adapter", short_path), ("runner", Path(__file__).resolve())]
        if inv_path is not None:
            fixed_inputs.append(("funding_inventory", inv_path))
        if unc_path is not None:
            fixed_inputs.append(("uncomputable_windows", unc_path))
        if input_manifest_path is not None:
            fixed_inputs.append(("input_manifest", input_manifest_path))
        for rel, pth in bound["files"].items():
            fixed_inputs.append(("manifest entry " + rel, pth))
        for inst in ordered_syms:
            fixed_inputs.append(("symbol npz " + inst, (cache_dir / (inst + ".npz")).resolve()))
        short_mod._verify_output_paths_disjoint(outputs, fixed_inputs)
        npz_paths, npz_records = short_mod._verify_and_record_npz_inputs(ordered_syms, cache_dir, symbols_dict, input_manifest_entries)

        inv, inv_unc, inv_stats = (None, {}, None)
        if inv_path is not None:
            inv, inv_unc, inv_stats = load_funding_inventory(inv_path)
        unc = {k: list(v) for k, v in inv_unc.items()}
        if unc_path is not None:
            for k, v in load_uncomputable_windows(unc_path, short_mod.parse_utc_ms).items():
                unc.setdefault(k, []).extend(v)
        sha_before = {lbl: sha(p) for lbl, p in (("funding_db", src_db), ("cache_manifest", cache_manifest_path))}
        if inv_path is not None:
            sha_before["funding_inventory"] = sha(inv_path)
        if unc_path is not None:
            sha_before["uncomputable_windows"] = sha(unc_path)

        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            short_mod._atomic_write_text(scope_file, json.dumps(scope, ensure_ascii=False, indent=2) + "\n")
            short_mod._bind_isolated_funding_db(src_db, derived_db, derived_meta)
            loaded = short_mod._load_runtime_modules(bound)
            combo_sim, combo_src_sha = _build_combo_sim(loaded["b6_sim_portable"])
            fmaps, ov_raw = short_mod.load_funding_db(derived_db)

            raw, bars_set = {}, set()
            for inst in ordered_syms:
                info = symbols_dict[inst]
                z = np.load(npz_paths[inst])
                if len(z["ts30"]) == 0 or len(z["ts4"]) == 0:
                    raise RuntimeError("empty timestamp array in symbol npz: " + inst)
                ts30, o30, ts4, o4, ts1, o1 = z["ts30"], z["ohlc30"], z["ts4"], z["ohlc4"], z["ts1"], z["ohlc1"]
                ema, rsi = short_mod.indicators_ema55_rsi14(o4[:, 3])
                for t in ts30.tolist():
                    if start_ts <= int(t) <= end_ts:
                        bars_set.add(int(t))
                raw[inst] = {
                    "ts4": ts4, "o4": o4, "ts4_map": {int(t): j for j, t in enumerate(ts4.tolist())},
                    "ema": ema, "rsi": rsi,
                    "d30": ({int(t): j for j, t in enumerate(ts30.tolist())}, o30),
                    "d1h": ({int(t): j for j, t in enumerate(ts1.tolist())}, o1),
                    "d1_set": set(int(x) for x in z["d1_ts"].tolist()),
                    "tickSz": float(info["spec"]["tickSz"]), "tickSz_str": str(info["spec"]["tickSz"]),
                    "maxLever": float(info["spec"].get("maxLever", 10.0)),
                    "fmap": fmaps.get(inst, {}),
                }
            bars = sorted(bars_set)
            if not bars:
                raise RuntimeError("no 30m bars inside the window")

            l_cands, l_lev, l_diag = long_mod.build_cands_long_struct_02_temporal_split(raw, ordered_syms, start_ts, end_ts)
            s_cands, s_lev, s_diag = short_mod.build_cands_retest24(raw, start_ts, end_ts, SHORT_CANDIDATE)
            max_lev = {}
            for inst in set(l_lev) | set(s_lev):
                vals = [v[inst] for v in (l_lev, s_lev) if inst in v]
                max_lev[inst] = min(vals)
            rank = {"long_first": (0, 1), "short_first": (1, 0)}[args.leg_priority]
            merged, contested_bars = {}, 0
            for li, cands in ((0, l_cands), (1, s_cands)):
                for bt, lst in cands.items():
                    for (sk, _li, inst, px, tr) in lst:
                        merged.setdefault(int(bt), []).append(((rank[li], sk), li, inst, px, tr))
            for bt, lst in merged.items():
                if len({x[1] for x in lst}) > 1:
                    contested_bars += 1

            ldef = long_mod.DEFAULT_EXIT_BY_CANDIDATE[LONG_CANDIDATE]
            lspec = long_mod.make_sim_spec(LONG_CANDIDATE, ldef["tp_pct"], ldef["sl_pct"], ldef["ttl_hours"], ldef["max_slots"], ldef["risk_per_trade"])
            arms, details = {}, {}
            leg_names = {0: LONG_CANDIDATE, 1: SHORT_CANDIDATE}
            for name in scen:
                sizing, fill = name.split("|")
                rid, risk_u, dloss_u = SHORT_SIZINGS[sizing]
                sspec = short_mod.make_retest24_spec(rid, risk_u, dloss_u)
                for k in COST_KEYS:
                    if float(lspec[k]) != float(sspec[k]):
                        raise RuntimeError("fair-cost mismatch between legs on " + k)
                spec = {k: lspec[k] for k in COST_KEYS}
                spec["legs"] = [dict(lspec["legs"][0]), dict(sspec["legs"][0])]
                sides = ["long" if lg["mode"] == "fib_long" else "short" for lg in spec["legs"]]
                if sides != ["long", "short"]:
                    raise RuntimeError("combo legs must be exactly [long, short]")
                ctrl = {"global_max_slots": args.global_max_slots, "global_daily_loss_u": args.global_daily_loss_u,
                        "same_inst_policy": args.same_inst_policy, "leg_sides": sides, "uncomputable": unc}
                r = combo_sim(raw, bars, spec, ov_raw_ts=ov_raw, cands_pre=merged, max_lev_pre=max_lev,
                              record_events=True, record_trades_detail=True, fill_mode="cross_1tick",
                              delay_first_bar=FILL_MODES[fill], combo=ctrl)
                trades_out, open_out, miss_out, flags = annotate_arm(r, leg_names, inv, unc, bars[-1])
                ol = r.get("_ord_log", [])
                gaps = []
                if miss_out:
                    gaps.append("missing_8h_funding_events_not_booked")
                if inv is None:
                    gaps.append("funding_inventory_not_supplied_completeness_unknown")
                if flags["funding_incomplete_or_unknown_trades"] or any(o["funding_status"] != "complete_by_batch_scope" for o in open_out if o["funding_status"] != "no_funding_interval"):
                    gaps.append("positions_held_in_months_not_complete_true")
                if flags["uncomputable_trades"]:
                    gaps.append("uncomputable_positions_present")
                gaps.append("non_8h_funding_denominator_unknown")
                arms[name] = {
                    "status": "PRELIMINARY_INCOMPLETE_DATA" if len(gaps) > 1 else "PRELIMINARY_BATCH_SCOPE",
                    "performance_label": "初步／資料不完整；未入帳的未知資金費為條件情境，不是真實淨績效",
                    "short_sizing": sizing, "fill_mode": fill,
                    "account": {"final_eq_u": r.get("final_eq_u"), "ret_eq_pct": r.get("ret_eq_pct"),
                                "mtm_mdd_pct": r.get("mtm_mdd_pct"), "cagr_eq_pct": r.get("cagr_eq_pct")},
                    "legs": {
                        "0_long": dict(_leg_stats([t for t in trades_out if t["leg"] == 0]),
                                       orders_placed=sum(1 for o in ol if o.get("leg") == 0),
                                       by_year_month=short_mod._build_by_year_month([o for o in ol if o.get("leg") == 0], [t for t in r.get("_trades", []) if t["side"] == "long"], start_ts_ms=start_ts, end_ts_ms=end_ts)),
                        "1_short": dict(_leg_stats([t for t in trades_out if t["leg"] == 1]),
                                        orders_placed=sum(1 for o in ol if o.get("leg") == 1),
                                        by_year_month=short_mod._build_by_year_month([o for o in ol if o.get("leg") == 1], [t for t in r.get("_trades", []) if t["side"] == "short"], start_ts_ms=start_ts, end_ts_ms=end_ts)),
                    },
                    "combo_gates": {k: v for k, v in (r.get("_combo") or {}).items() if k != "blocked_events"},
                    "open_at_end": len(open_out),
                    "funding": {"f_ev_real_8h": r.get("f_ev_real_8h"), "f_ev_real_non8h": r.get("f_ev_real_non8h"),
                                "miss_8h_events": len(miss_out), "booked_fund_u": r.get("real_fund_u"),
                                "missing_rates_policy": "UNKNOWN_NOT_BOOKED (no zero-fill, no interpolation, no symbol dropped)"},
                    "annotation_flags": flags,
                    "gaps": gaps,
                }
                details[name] = {"closed_trades": trades_out, "open_at_end": open_out, "missing_funding_events_all": miss_out,
                                 "combo_blocked_events": (r.get("_combo") or {}).get("blocked_events", []),
                                 "order_log": ol}

            after = {lbl: sha(p) for lbl, p in (("funding_db", src_db), ("cache_manifest", cache_manifest_path))}
            if inv_path is not None:
                after["funding_inventory"] = sha(inv_path)
            if unc_path is not None:
                after["uncomputable_windows"] = sha(unc_path)
            if after != sha_before or sha(long_path) != long_sha_before or sha(short_path) != short_sha_before:
                raise RuntimeError("fixed input modified during run")
            for inst, pth in npz_paths.items():
                if sha(pth) != npz_records[inst]["sha256"]:
                    raise RuntimeError("symbol npz modified during run: " + inst)

            finished_utc = datetime.now(TZ_UTC).isoformat()
            short_mod._atomic_write_text(details_file, json.dumps({
                "public_repo_policy": "LOCAL_OFFLINE_DETAIL_ONLY_DO_NOT_AUTO_PUSH_TO_PUBLIC_REPO",
                "study_id": STUDY_ID, "version": RUNNER_VERSION, "combo_id": COMBO_ID,
                "uncomputable_windows": {k: v for k, v in sorted(unc.items())},
                "npz_files": npz_records, "scenarios": details,
            }, ensure_ascii=False, indent=2) + "\n")
            payload = {
                "status": "PRELIMINARY_INCOMPLETE_DATA" if any(a["status"] == "PRELIMINARY_INCOMPLETE_DATA" for a in arms.values()) else "PRELIMINARY_BATCH_SCOPE",
                "never_pass_note": "初步情境結果；不是完整驗收 PASS，不是實盤核准（live_approved: false）",
                "study_id": STUDY_ID, "version": RUNNER_VERSION, "combo_id": COMBO_ID,
                "started_utc": started_utc, "finished_utc": finished_utc, "elapsed_sec": round(time.time() - t0, 2),
                "transport_blocker_active_entire_run": True, "transport_hits": list(tb.hits),
                "scope": scope, "symbols_loaded": len(raw), "bars_30m_in_window": len(bars),
                "candidates": {"long": l_diag, "short": s_diag, "bars_with_both_legs_signalling": contested_bars},
                "funding_inventory_stats": inv_stats,
                "uncomputable_windows_count": sum(len(v) for v in unc.values()),
                "historical_model_vs_delivered_script_diff": short_mod.HISTORICAL_MODEL_VS_DELIVERED_SCRIPT_DIFF,
                "combo_model_vs_live_shared_risk_diff": [
                    "live shared_risk.RiskLedger keys slots by (strategy, inst, pos_side); model default block_any is stricter (one instrument, one leg)",
                    "live daily loss uses realised PnL events by Taipei day; model books realised net (fee + booked funding) at exit bar, Taipei day",
                    "each leg keeps its own frozen per-leg limits (long 24 slots / 600U UTC-day / 3-loss pause; short 12 slots / R1 600U or R2 400U UTC-day)",
                    "same-bar cross-leg order follows --leg-priority, then each leg's own frozen sort key",
                ],
                "sha256": dict(after, manifest=sha(manifest_path), retest24_script=sha(bound["roles"]["retest24_script"]),
                               shared_risk=sha(bound["roles"]["shared_risk"]), long_adapter=long_sha_before, short_adapter=short_sha_before,
                               runner=sha(Path(__file__).resolve()), combo_engine_source=combo_src_sha,
                               derived_funding_db=sha(derived_db), details=sha(details_file)),
                "local_details_file": DETAILS_NAME,
                "limitations": [
                    "缺歷史 BBO，post_only 可否掛入與排隊順位未知；cross_1tick 只是穿價下界",
                    "delay1bar 為敏感度，不是真實延遲；歷史 MMR 以 1% 近似",
                    "缺資金費維持未知、未入帳；非 8H 結算應有分母未知；complete=true 只代表該批來源核對口徑",
                    "RVN 等下架合約的確切下架時間未知，整個 CST 月視為不可計算視窗",
                ],
                "arms": arms,
            }
            short_mod._atomic_write_text(result_file, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            print("COMBO_RESULT_SHA256:", sha(result_file), flush=True)
            return 0
        except Exception:
            short_mod._discard_final_report(result_file, fixed_inputs)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
