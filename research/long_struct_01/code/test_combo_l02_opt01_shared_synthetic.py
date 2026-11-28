#!/usr/bin/env python3
"""100% synthetic main() tests for run_combo_l02_opt01_shared_backtest.py (BACKTEST-READINESS-01 v1.20).

Zero real market data, zero network, zero live/demo trading, no historical or performance backtest.
The REAL registered engine files (engine/*.py) are copied into a temp dir and registered in a synthetic
manifest; the RETEST24 script / shared_risk are stubs. Candidate builders are replaced by tiny stub
adapters (they import the real adapters and override only the two build_cands_* functions) so that
the shared-account wiring can be exercised deterministically on hand-made OHLC bars.
Covers: shared margin pool, global slot cap, global Taipei-day loss, same-instrument cross-leg conflict
(same bar / held / allow_opposite / priority), missing funding annotation (no zero fill, no abort),
inventory complete==true semantics, uncomputable windows (inventory 51001 + explicit), output
exclusivity (fresh out-dir, failure leaves no result, symlink refused), real-builder smoke, dry-check.
v1.19 (ChatGPT v1.19, Issue #1 #7231413139) adds: REST 51001 = funding annotation only (item 3), explicit
uncomputable windows need price evidence (item 3), same-scale cross-leg rank interleave + research-added
controls listed/switchable (item 4), OPT01_SIG_R2_SIZING_100U rename (item 5), adapter size/SHA verified and
network blocked BEFORE adapter load (item 6), per-leg daily-loss day boundary taipei default / utc option
(item 7), patched engine source written and its SHA-256 recorded (item 8).
v1.20 (ChatGPT v1.20, Issue #1 #7235223075 and #7235255702) adds: limitations / model-vs-live diff text derived from the
actual --leg-daily-loss-day and global-control parameters (no hard-coded "600U UTC-day"), the decided main-comparison
parameter set (utc legs + rank_interleave + global controls off) running end-to-end, and combined long+short monthly
closed-trade statistics by exit UTC month with first fills and per-direction contribution.
COMBO_RUNNER_PATH may point at another runner version (old-fails / new-passes evidence); flags the runner
under test does not know are omitted from shared fixtures so that the item's assertion, not argparse, fails.
"""
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNNER = Path(os.environ.get("COMBO_RUNNER_PATH") or (HERE / "run_combo_l02_opt01_shared_backtest.py"))
REAL_LONG = HERE / "run_long_struct_bounded_backtest.py"
REAL_SHORT = HERE / "run_retest24_bounded_backtest.py"
ENGINE_DIR = HERE / "engine"

_spec = importlib.util.spec_from_file_location("combo_runner_under_test", str(RUNNER))
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

M30, H4, H8, DAY = 1800000, 14400000, 28800000, 86400000
S0 = 1709251200000            # 2024-03-01T00:00:00Z (Taipei 08:00)
BAR0 = S0 - 2 * DAY           # data starts 2024-02-28T00:00Z
BAR_END = S0 + 3 * DAY - M30  # 2024-03-03T23:30Z
START, END = "2024-03-01T00:00:00Z", "2024-03-03T23:30:00Z"
NEW_API = hasattr(mod, "PINNED_ADAPTERS")
R2ARM = getattr(mod, "R2_SIZING_ARM", "R2_100U")
SYMS = ["AAA-USDT-SWAP", "BBB-USDT-SWAP", "CCC-USDT-SWAP", "DDD-USDT-SWAP", "EEE-USDT-SWAP", "FFF-USDT-SWAP"]


def _check(cond, msg):
    if not cond:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + msg)


STUB_ADAPTER = '''%(prefix)simport importlib.util as _u
_s = _u.spec_from_file_location(%(modname)r, %(real)r)
_m = _u.module_from_spec(_s)
_s.loader.exec_module(_m)
for _k, _v in vars(_m).items():
    if not _k.startswith("__"):
        globals()[_k] = _v
_CANDS = %(cands)r
_RAISE = %(raise_)r

def _stub(raw, start_ts, end_ts, li):
    if _RAISE:
        raise RuntimeError("SYNTHETIC_BUILDER_FAILURE")
    out = {}
    for bt, inst, px, sk in _CANDS:
        out.setdefault(int(bt), []).append((sk, 0, inst, float(px), False))
    ml = {inst: min(10.0, float(v["maxLever"])) for inst, v in raw.items()}
    return out, ml, {"stub": True, "signals": len(_CANDS)}

def %(fn)s(raw, *a, **kw):
    if %(is_long)r:
        symbol_order, start_ts, end_ts = a[0], a[1], a[2]
    else:
        start_ts, end_ts = a[0], a[1]
    return _stub(raw, start_ts, end_ts, 0)
'''


def _write_stub(path, real, fn, cands, is_long, raise_=False, prefix=""):
    path.write_text(STUB_ADAPTER % {"modname": "_real_" + path.stem, "real": str(real), "cands": cands,
                                    "raise_": raise_, "fn": fn, "is_long": is_long, "prefix": prefix}, encoding="utf-8")


def make_env(root, long_cands=(), short_cands=(), max_lever=None, crash=None, funding=(), raise_long=False,
             inventory_rows=None, unc_windows=None, pin_stubs=True, short_prefix=""):
    code = root / "code"
    (code / "engine").mkdir(parents=True)
    (code / "scripts").mkdir(parents=True)
    for f in ("b6_sim_portable.py", "sim_50k_v3_2_sl_fix.py", "audit_v3_1_full.py", "run_q38_audit_01.py"):
        shutil.copy2(ENGINE_DIR / f, code / "engine" / f)
    (code / "scripts" / "RETEST24_R1_R2_Switchable_v1_5_auditfix.py").write_text("STUB = 1\n", encoding="utf-8")
    (code / "scripts" / "shared_risk.py").write_text("SHARED_RISK_STUB = True\n", encoding="utf-8")
    entries = {}
    for fp in sorted(list((code / "engine").glob("*.py")) + list((code / "scripts").glob("*.py"))):
        entries[fp.relative_to(code).as_posix()] = {"sha256": mod.sha(fp), "size": fp.stat().st_size}
    (code / "manifest.json").write_text(json.dumps({"files": entries}), encoding="utf-8")

    cache = root / "cache"
    cache.mkdir()
    ts30 = np.arange(BAR0, BAR_END + 1, M30, dtype=np.int64)
    ts4 = np.arange(BAR0, BAR_END + 1, H4, dtype=np.int64)
    ts1 = np.arange(BAR0, BAR_END + 1, 3600000, dtype=np.int64)
    d1 = np.arange(BAR0 - 70 * DAY, BAR_END + 1, DAY, dtype=np.int64)
    symbols = {}
    for inst in SYMS:
        o30 = np.tile(np.array([100.0, 100.5, 99.5, 100.0]), (len(ts30), 1))
        for (cinst, cts, ohlc) in (crash or ()):
            if cinst == inst:
                o30[int((cts - BAR0) // M30)] = ohlc
        np.savez(cache / (inst + ".npz"), ts30=ts30, ohlc30=o30, ts4=ts4, ohlc4=np.tile(np.array([100.0, 100.5, 99.5, 100.0]), (len(ts4), 1)),
                 ts1=ts1, ohlc1=np.tile(np.array([100.0, 100.5, 99.5, 100.0]), (len(ts1), 1)), d1_ts=d1)
        fp = cache / (inst + ".npz")
        lev = (max_lever or {}).get(inst, "20")
        symbols[inst] = {"spec": {"tickSz": "0.1", "maxLever": lev}, "npz_sha256": mod.sha(fp), "npz_size_bytes": fp.stat().st_size}
    (cache / "manifest.json").write_text(json.dumps({"symbols": symbols}), encoding="utf-8")

    db = root / "funding.sqlite"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL)")
    for inst, ts, rate in funding:
        con.execute("INSERT INTO funding_archive VALUES (?,?,?,?)", (inst, ts, ts, rate))
    con.commit()
    con.close()

    la, sa = root / "long_adapter_stub.py", root / "short_adapter_stub.py"
    _write_stub(la, REAL_LONG, "build_cands_long_struct_02_temporal_split", list(long_cands), True, raise_long)
    _write_stub(sa, REAL_SHORT, "build_cands_retest24", list(short_cands), False, prefix=short_prefix)
    argv = ["--manifest", str(code / "manifest.json"),
            "--retest24-script", str(code / "scripts" / "RETEST24_R1_R2_Switchable_v1_5_auditfix.py"),
            "--shared-risk", str(code / "scripts" / "shared_risk.py"),
            "--cache-dir", str(cache), "--funding-db", str(db), "--out-dir", str(root / "out"),
            "--start-utc", START, "--end-utc", END,
            "--long-adapter", str(la), "--short-adapter", str(sa)]
    if NEW_API and pin_stubs:
        argv += ["--long-adapter-size", str(la.stat().st_size), "--long-adapter-sha256", mod.sha(la),
                 "--short-adapter-size", str(sa.stat().st_size), "--short-adapter-sha256", mod.sha(sa)]
    if inventory_rows is not None:
        inv = root / "inventory.csv"
        lines = ["inst_id,month_cst,class,sub_reason,complete"] + [",".join(r) for r in inventory_rows]
        inv.write_text("\n".join(lines) + "\n", encoding="utf-8")
        argv += ["--funding-inventory", str(inv)]
    if unc_windows is not None:
        uw = root / "unc.json"
        uw.write_text(json.dumps(unc_windows), encoding="utf-8")
        argv += ["--uncomputable-windows", str(uw)]
    return {"argv": argv, "out": root / "out", "root": root}


def run(env, extra=(), scen="R1_150U|cross_1tick"):
    rc = mod.main(env["argv"] + ["--scenarios", scen] + list(extra))
    res = json.loads((env["out"] / mod.RESULT_NAME).read_text(encoding="utf-8"))
    det = json.loads((env["out"] / mod.DETAILS_NAME).read_text(encoding="utf-8"))
    return rc, res, det


def placed(det, scen, leg):
    return [o for o in det["scenarios"][scen]["order_log"] if o.get("leg") == leg]


def test_shared_margin_pool():
    sc = "R1_150U|cross_1tick"
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, SYMS[0], 100.0, -0.01)], short_cands=[(S0, SYMS[1], 100.0, -30.0)],
                       max_lever={SYMS[0]: "0.1", SYMS[1]: "0.1"})
        rc, res, det = run(env)
        _check(rc == 0, "rc")
        _check(len(placed(det, sc, 0)) == 1, "long placed (im 37,500U)")
        _check(len(placed(det, sc, 1)) == 0, "short must be rejected: shared pool 50,000 - 37,500 < 30,000 im")
        _check(res["scope"]["capital_model"].startswith("SINGLE_SHARED_ACCOUNT"), "capital model label")
    with tempfile.TemporaryDirectory() as td:  # control: same short alone fits -> proves rejection came from the shared pool
        env = make_env(Path(td), short_cands=[(S0, SYMS[1], 100.0, -30.0)], max_lever={SYMS[0]: "0.1", SYMS[1]: "0.1"})
        rc, res, det = run(env)
        _check(len(placed(det, sc, 1)) == 1, "short alone must be placed")
    print("MARGIN: shared pool rejects 2nd leg; alone it is placed")


def test_global_slot_cap():
    sc = "R1_150U|cross_1tick"
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, s, 100.0, -0.01 * (i + 1)) for i, s in enumerate(SYMS[:2])],
                       short_cands=[(S0, SYMS[2], 100.0, -30.0)])
        # whole-direction order keeps this v1.17 slot-cap case meaningful; rank interleave has its own test
        rc, res, det = run(env, ["--global-max-slots", "2"] + (["--cross-leg-order", "direction_block"] if NEW_API else []))
        gates = res["arms"][sc]["combo_gates"]["blocked_counts"]
        _check(len(placed(det, sc, 0)) == 2 and len(placed(det, sc, 1)) == 0, "2 longs placed, short blocked")
        _check(gates.get("global_slots_full", {}).get("1") == 1, "global_slots_full counted for short leg: %r" % gates)
    print("SLOTS: long+short combined cap enforced")


def test_global_daily_loss_taipei():
    sc = "R1_150U|cross_1tick"
    crash = [(s, S0 + H4, [100.0, 100.0, 90.0, 91.0]) for s in SYMS[:5]]
    longs = [(S0, s, 100.0, -0.01 * (i + 1)) for i, s in enumerate(SYMS[:5])]
    shorts = [(S0 + 2 * H4, SYMS[5], 100.0, -30.0)]  # 08:00Z = Taipei 16:00 same day
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=longs, short_cands=shorts, crash=crash)
        rc, res, det = run(env)
        arm = res["arms"][sc]
        _check(arm["legs"]["0_long"]["closed_trades"] == 5, "5 long SL exits")
        _check(len(placed(det, sc, 1)) == 0, "short blocked by global Taipei-day loss")
        _check(arm["combo_gates"]["blocked_counts"].get("global_daily_loss_taipei_day", {}).get("1") == 1, "gate counted")
        day = arm["combo_gates"]["taipei_day_realised_net_u"]
        _check(list(day.keys()) == ["2024-03-01"] and day["2024-03-01"] < -600.0, "Taipei day net %r" % day)
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=longs, short_cands=shorts, crash=crash)
        rc, res, det = run(env, ["--global-daily-loss-u", "100000"])
        _check(len(placed(det, sc, 1)) == 1, "control: short placed when global limit is not hit (per-leg short limit untouched)")
    print("DAILY: global Taipei-day realised loss blocks the other leg")


def test_same_inst_conflicts():
    sc = "R1_150U|cross_1tick"
    A = SYMS[0]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01)], short_cands=[(S0, A, 100.0, -30.0), (S0 + H4, A, 100.0, -30.0)])
        rc, res, det = run(env)
        g = res["arms"][sc]["combo_gates"]["blocked_counts"]
        _check(len(placed(det, sc, 0)) == 1 and len(placed(det, sc, 1)) == 0, "long_first: long wins")
        _check(g.get("same_bar_cross_leg_same_inst", {}).get("1") == 1, "same-bar conflict counted %r" % g)
        _check(g.get("same_inst_held_by_other_leg", {}).get("1") == 1, "held conflict counted %r" % g)
        _check(res["candidates"]["bars_with_both_legs_signalling"] == 1, "contested bar count")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01)], short_cands=[(S0, A, 100.0, -30.0)])
        rc, res, det = run(env, ["--leg-priority", "short_first"])
        _check(len(placed(det, sc, 1)) == 1 and len(placed(det, sc, 0)) == 0, "short_first: short wins")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01)], short_cands=[(S0, A, 100.0, -30.0)])
        rc, res, det = run(env, ["--same-inst-policy", "allow_opposite"])
        _check(len(placed(det, sc, 1)) == 1 and len(placed(det, sc, 0)) == 1, "allow_opposite: both placed")
    print("CONFLICT: same bar / held / priority / allow_opposite all deterministic")


def test_missing_funding_annotation_and_inventory():
    sc = R2ARM + "|cross_1tick"
    A, B, C = SYMS[0], SYMS[1], SYMS[2]
    funding = [(A, S0 + H8, 0.0001), (A, S0 + 2 * H8, 0.0001)]
    inv = [(A, "2024-03", "covered_verified", "", "true"), (B, "2024-03", "pending_check", "", ""),
           (C, "2024-03", "covered_verified", "", " True")]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01), (S0, C, 100.0, -0.02)],
                       short_cands=[(S0, B, 100.0, -30.0)], funding=funding, inventory_rows=inv)
        rc, res, det = run(env, scen=sc)
        arm = res["arms"][sc]
        _check(rc == 0, "missing funding must NOT abort under v1.15")
        _check(arm["status"] == "PRELIMINARY_INCOMPLETE_DATA" and res["status"] != "PASS", "preliminary label")
        _check(arm["funding"]["miss_8h_events"] > 0, "miss events counted")
        miss = det["scenarios"][sc]["missing_funding_events_all"]
        _check(len(miss) == arm["funding"]["miss_8h_events"], "full untruncated miss list")
        _check(all(m["inst_id"] != A or m["ts_ms"] not in (S0 + H8, S0 + 2 * H8) for m in miss), "known rates not listed as missing")
        _check(abs(arm["funding"]["booked_fund_u"] - (-2 * 3750.0 * 0.0001)) < 1e-6, "only known rates booked (no zero-fill rows invented)")
        op = {o["inst_id"]: o for o in det["scenarios"][sc]["open_at_end"]}
        _check(op[A]["funding_status"] == "complete_by_batch_scope", "A complete=true")
        _check(op[B]["funding_status"] == "incomplete_or_unknown" and op[B]["funding_months_cst"]["2024-03"] == "unknown_blank", "B blank=unknown")
        _check(op[C]["funding_months_cst"]["2024-03"] == "unknown_unrecognised_value", "' True' is not true")
        _check(res["funding_inventory_stats"]["complete_true"] == 1, "inventory stats")
        _check("missing_8h_funding_events_not_booked" in arm["gaps"], "gap listed")
        _check("條件情境" in arm["performance_label"], "conditional-scenario label")
        _check(res["transport_hits"] == [], "no network")
    print("FUNDING: missing rates unknown/not booked, listed in full, complete==true only")


def test_uncomputable_windows():
    """v1.19 item 3: REST 51001 = funding note only (entry allowed, population kept); explicit price-evidence window flags."""
    sc = "R1_150U|cross_1tick"
    D_, E = SYMS[3], SYMS[4]
    inv = [(D_, "2024-03", "pending_check", "rest_51001_instrument_not_listed", "")]
    unc = [{"inst_id": E, "from_utc": "2024-03-02T00:00:00Z", "reason": "synthetic price gap",
            "evidence": "synthetic: required 30m OHLC absent from 2024-03-02T00:00Z"}]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, D_, 100.0, -0.01), (S0, E, 100.0, -0.02)], inventory_rows=inv, unc_windows=unc)
        rc, res, det = run(env)
        arm = res["arms"][sc]
        _check(arm["combo_gates"]["blocked_counts"].get("uncomputable_window", {}).get("0") is None, "51001 month must NOT block entries: %r" % arm["combo_gates"])
        op = {o["inst_id"]: o for o in det["scenarios"][sc]["open_at_end"]}
        _check(D_ in op and op[D_]["computability"] == "computable", "D entered and stays computable (no price evidence)")
        _check(op[D_].get("funding_notes") and "51001" in op[D_]["funding_notes"][0], "D carries the 51001 funding note")
        _check(op[E]["computability"].startswith("不可計算"), "E position overlapping evidence-backed price window flagged")
        _check("uncomputable_positions_present" in arm["gaps"] and "positions_in_rest_51001_funding_months_rates_unknown" in arm["gaps"], "gaps listed")
        _check(res["uncomputable_windows_count"] == 1 and res["funding_query_51001_note_months"] == 1, "1 window + 1 note, symbols not dropped")
    print("UNCOMPUTABLE: 51001 = funding note only (entry allowed); evidence-backed price window flags overlap")


def test_explicit_window_needs_evidence():
    with tempfile.TemporaryDirectory() as td:
        unc = [{"inst_id": SYMS[4], "from_utc": "2024-03-02T00:00:00Z", "reason": "no evidence given"}]
        env = make_env(Path(td), long_cands=[(S0, SYMS[4], 100.0, -0.02)], unc_windows=unc)
        refused = False
        try:
            mod.main(env["argv"] + ["--scenarios", "R1_150U|cross_1tick"])
        except RuntimeError as exc:
            refused = "evidence" in str(exc)
        _check(refused, "explicit window without price evidence must be refused")
        _check(not (env["out"] / mod.RESULT_NAME).exists(), "no result written")
    print("EVIDENCE: explicit uncomputable window without price evidence refused")


def test_cross_leg_rank_interleave():
    """v1.19 item 4: same-scale rank interleave, equal rank -> long first; within-direction order unchanged."""
    sc = "R1_150U|cross_1tick"
    A, B, C, D_ = SYMS[:4]
    longs = [(S0, B, 100.0, -0.01), (S0, A, 100.0, -0.02)]      # long rank: A(0), B(1)
    shorts = [(S0, D_, 100.0, -20.0), (S0, C, 100.0, -30.0)]    # short rank: C(0), D(1)
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=longs, short_cands=shorts)
        rc, res, det = run(env, ["--global-max-slots", "2"])
        got = sorted((o["leg"], o["inst"]) for o in det["scenarios"][sc]["order_log"])
        _check(got == [(0, A), (1, C)], "interleave rank0 long A + rank0 short C, got %r" % got)
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=longs, short_cands=shorts)
        rc, res, det = run(env, ["--global-max-slots", "3"])
        got = sorted((o["leg"], o["inst"]) for o in det["scenarios"][sc]["order_log"])
        _check(got == [(0, A), (0, B), (1, C)], "3rd slot = rank1 long B before rank1 short D, got %r" % got)
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=longs, short_cands=shorts)
        rc, res, det = run(env, ["--global-max-slots", "2", "--cross-leg-order", "direction_block"])
        got = sorted((o["leg"], o["inst"]) for o in det["scenarios"][sc]["order_log"])
        _check(got == [(0, A), (0, B)], "direction_block keeps v1.17 behaviour, got %r" % got)
        _check(res["scope"]["cross_leg_order"] == "direction_block", "order recorded")
    print("ORDER: rank interleave (long first on equal rank); direction_block available as sensitivity")


def test_research_controls_switchable_and_listed():
    sc = "R1_150U|cross_1tick"
    A = SYMS[0]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01)], short_cands=[(S0, A, 100.0, -30.0)])
        rc, res, det = run(env, ["--global-max-slots", "0", "--global-daily-loss-u", "0", "--same-inst-policy", "off"])
        _check(len(placed(det, sc, 0)) == 1 and len(placed(det, sc, 1)) == 1, "all research controls off -> both legs placed")
        rr = res["scope"]["research_added_risk_controls"]
        _check(not rr["global_max_slots"]["enabled"] and not rr["global_daily_loss_u"]["enabled"] and not rr["same_inst_policy"]["enabled"], "listed as off")
        _check("established_combo_basis" in res["scope"], "established basis listed separately")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01)])
        rc, res, det = run(env)
        rr = res["scope"]["research_added_risk_controls"]
        _check(rr["global_max_slots"] == {"enabled": True, "value": 12} and rr["same_inst_policy"]["value"] == "block_any"
               and rr["global_daily_loss_u"]["value"] == 600.0, "defaults kept (12 / 600 / block_any) and labelled research-added")
        _check("0.0005" in res["scope"]["established_combo_basis"]["out_of_scope"], "slippage/mapping alignment documented out of scope")
    print("RESEARCH CONTROLS: 12 slots / 600U / block_any listed separately, each switchable")


def test_r2_arm_renamed():
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, SYMS[0], 100.0, -0.01)])
        rc, res, det = run(env, scen="OPT01_SIG_R2_SIZING_100U|cross_1tick")
        arm = res["arms"]["OPT01_SIG_R2_SIZING_100U|cross_1tick"]
        _check("NOT the R2 comparison" in arm["short_sizing_note"], "arm note says it is not the R2 comparison")
        _check(all(not a.startswith("R2_100U") for a in mod.DEFAULT_SCENARIOS.split(",")), "defaults renamed")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td))
        try:
            mod.main(env["argv"] + ["--scenarios", "R2_100U|cross_1tick"])
            _check(False, "old arm name must be refused")
        except RuntimeError as exc:
            _check("renamed" in str(exc), "rename message: %s" % exc)
    print("R2: combo arm renamed OPT01_SIG_R2_SIZING_100U; old name refused with explanation")


def test_adapter_verified_before_load():
    with tempfile.TemporaryDirectory() as td:
        marker = Path(td) / "adapter_code_ran.txt"
        prefix = "open(%r, 'w').write('RAN')\n" % str(marker)
        env = make_env(Path(td), short_prefix=prefix, pin_stubs=False)   # unpinned override, no expected SHA given
        refused = False
        try:
            mod.main(env["argv"] + ["--scenarios", "R1_150U|cross_1tick"])
        except RuntimeError as exc:
            refused = "before" in str(exc)
        _check(not marker.exists(), "adapter code must NOT run before its size/SHA is verified")
        _check(refused, "unverified adapter override refused")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td))
        argv = [a for a in env["argv"]]
        i = argv.index("--short-adapter-sha256") if "--short-adapter-sha256" in argv else -1
        _check(i >= 0, "runner exposes expected-SHA flags")
        argv[i + 1] = "0" * 64
        try:
            mod.main(argv + ["--scenarios", "R1_150U|cross_1tick"])
            _check(False, "wrong expected SHA must be refused")
        except RuntimeError as exc:
            _check("mismatch" in str(exc), "mismatch message")
    print("ADAPTER: size/SHA verified before any adapter code runs; mismatch refused")


def test_network_blocked_before_adapter_load():
    with tempfile.TemporaryDirectory() as td:
        marker = Path(td) / "net.txt"
        prefix = ("import socket as _sk\n"
                  "try:\n"
                  "    _sk.create_connection(('127.0.0.1', 9), timeout=0.5).close(); _NETR = 'CONNECTED'\n"
                  "except Exception as _e:\n"
                  "    _NETR = type(_e).__name__ + ':' + str(_e)\n"
                  "open(%r, 'w').write(_NETR)\n") % str(marker)
        env = make_env(Path(td), long_cands=[(S0, SYMS[0], 100.0, -0.01)], short_prefix=prefix)
        rc, res, det = run(env)
        got = marker.read_text(encoding="utf-8")
        _check("OFFLINE_TRANSPORT_BLOCKED" in got, "socket at adapter import time must hit the outer guard, got %r" % got)
        _check(res.get("outer_offline_guard_active_entire_run") is True and res.get("outer_guard_hits"), "guard hit recorded")
    print("NETWORK: outer guard active before adapter import (localhost-only probe)")


def test_leg_daily_loss_day_boundary():
    """v1.19 item 7: short losses at 20:00Z (Taipei 04:00 next day); next short signal 00:00Z next UTC day."""
    sc = "R1_150U|cross_1tick"
    crash = [(s, S0 + 5 * H4, [100.0, 110.0, 100.0, 109.0]) for s in SYMS[:5]]
    shorts = [(S0 + 4 * H4, s, 100.0, -30.0 - i) for i, s in enumerate(SYMS[:5])] + [(S0 + 6 * H4, SYMS[5], 100.0, -30.0)]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), short_cands=shorts, crash=crash)
        rc, res, det = run(env, ["--global-daily-loss-u", "100000"])
        late = [o for o in placed(det, sc, 1) if o["inst"] == SYMS[5]]
        _check(res["arms"][sc]["legs"]["1_short"]["closed_trades"] == 5, "5 short SL exits")
        _check(late == [], "default taipei day: same Taipei day loss >= 600U blocks the next short")
        _check(res["scope"].get("leg_daily_loss_day") == "taipei" and res["scope"].get("prereg_deviations"), "taipei recorded + deviation listed")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), short_cands=shorts, crash=crash)
        rc, res, det = run(env, ["--global-daily-loss-u", "100000", "--leg-daily-loss-day", "utc"])
        late = [o for o in placed(det, sc, 1) if o["inst"] == SYMS[5]]
        _check(len(late) == 1, "utc (PREREG v1.0) day: new UTC day -> next short placed")
        _check(res["scope"]["prereg_deviations"] == [], "no deviation in utc mode")
    print("LEG DAY: taipei default blocks across 00:00Z; utc option reproduces PREREG v1.0")


def _texts(res):
    return res["limitations"], res["combo_model_vs_live_shared_risk_diff"]


def test_limitations_text_follows_parameters():
    """v1.20 item 4: no hard-coded '600U UTC-day'; text follows --leg-daily-loss-day and the global control settings."""
    A = SYMS[0]
    def one(extra):
        with tempfile.TemporaryDirectory() as td:
            env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01)])
            rc, res, det = run(env, extra)
            return res
    res = one(["--leg-daily-loss-day", "utc"])
    lim, diff = _texts(res)
    jl, jd = "\n".join(lim), "\n".join(diff)
    _check("各腿日損日界：UTC 日" in jl and "各腿日損日界：台北日" not in jl, "utc leg-day text in limitations: %r" % lim)
    _check("UTC day" in jd and "Taipei day (Asia/Taipei" not in jd, "utc leg-day text in diff: %r" % diff)
    _check("共同日損限制（另加研究風控）：啟用" in jl and "600U" in jl, "global default 600U described as ON")
    _check("600U UTC-day" not in jd and "600U UTC-day" not in jl, "no hard-coded 600U UTC-day")
    res = one(["--leg-daily-loss-day", "taipei"])
    lim, diff = _texts(res)
    jl, jd = "\n".join(lim), "\n".join(diff)
    _check("各腿日損日界：台北日" in jl and "各腿日損日界：UTC 日" not in jl, "taipei leg-day text: %r" % lim)
    _check("per-leg daily loss day: Taipei day" in jd and "per-leg daily loss day: UTC day" not in jd, "taipei leg-day text in diff: %r" % diff)
    res = one(["--leg-daily-loss-day", "utc", "--global-daily-loss-u", "0", "--global-max-slots", "0", "--same-inst-policy", "off"])
    lim, diff = _texts(res)
    jl, jd = "\n".join(lim), "\n".join(diff)
    _check("共同日損限制：關閉" in jl and "沒有共同日損限制" in jl, "global loss off stated: %r" % lim)
    _check("600" not in jl and "600" not in jd, "no 600U claim anywhere in limitations / diff when global limit is 0: %r %r" % (lim, diff))
    _check("OFF in this run" in jd and "共同名額限制：關閉" in jl and "同幣跨腿規則：關閉" in jl, "other controls stated off")
    res = one(["--global-daily-loss-u", "250"])
    _check("250U" in "\n".join(_texts(res)[0]), "custom global limit value echoed")
    print("TEXT: limitations / diff follow --leg-daily-loss-day and global control parameters")


def test_main_comparison_parameter_set():
    """ChatGPT v1.20 decided main comparison: utc legs + rank_interleave + global controls OFF (program defaults unchanged)."""
    A, B, C = SYMS[:3]
    sc1, sc2 = "R1_150U|cross_1tick", "OPT01_SIG_R2_SIZING_100U|cross_1tick"
    crash = [(A, S0 + H4, [100.0, 100.0, 90.0, 91.0]), (B, S0 + H4, [100.0, 100.0, 90.0, 91.0]), (C, S0 + H4, [100.0, 110.0, 100.0, 109.0])]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01), (S0, B, 100.0, -0.02)],
                       short_cands=[(S0, A, 100.0, -30.0), (S0, C, 100.0, -31.0)], crash=crash)
        rc = mod.main(env["argv"] + ["--scenarios", sc1 + "," + sc2, "--leg-daily-loss-day", "utc", "--cross-leg-order", "rank_interleave",
                                      "--global-max-slots", "0", "--global-daily-loss-u", "0", "--same-inst-policy", "off"])
        res = json.loads((env["out"] / mod.RESULT_NAME).read_text(encoding="utf-8"))
        det = json.loads((env["out"] / mod.DETAILS_NAME).read_text(encoding="utf-8"))
        _check(rc == 0 and set(res["arms"]) == {sc1, sc2}, "main-comparison parameter set runs end-to-end, 2 arms")
        sc = res["scope"]
        _check(sc["leg_daily_loss_day"] == "utc" and sc["cross_leg_order"] == "rank_interleave" and sc["prereg_deviations"] == [], "utc legs, no PREREG deviation")
        rr = sc["research_added_risk_controls"]
        _check(not rr["global_max_slots"]["enabled"] and not rr["global_daily_loss_u"]["enabled"] and not rr["same_inst_policy"]["enabled"], "research-added controls all off")
        for name in (sc1, sc2):
            placed_by_leg = {(o.get("leg"), o["inst"]) for o in det["scenarios"][name]["order_log"]}
            _check((0, A) in placed_by_leg and (1, A) in placed_by_leg, "same instrument held by both legs when same-inst control is off (%s)" % name)
            arm = res["arms"][name]
            _check(arm["legs"]["0_long"]["closed_trades"] == 2 and arm["legs"]["1_short"]["closed_trades"] >= 1, "both legs trade (%s)" % name)
            mc = arm["monthly_combined"]
            row = mc["by_year_month"]["2024-03"]
            _check(row["closed_trades_total"] == row["long_closed_trades"] + row["short_closed_trades"] == arm["legs"]["0_long"]["closed_trades"] + arm["legs"]["1_short"]["closed_trades"],
                   "combined monthly closed = long + short: %r" % row)
        jl = "\n".join(res["limitations"])
        _check("共同日損限制：關閉" in jl and "各腿日損日界：UTC 日" in jl and "600" not in jl, "limitations describe this exact basis")
        _check("v1.20" in res["version"], "version")
    print("MAIN COMPARISON: utc legs + rank_interleave + global controls off runs end-to-end (2 arms)")


def test_monthly_combined_statistics():
    """v1.20: long+short closed trades by EXIT UTC month, first fills and direction contribution; 100-200 band on full months."""
    A, B, C = SYMS[:3]
    crash = [(A, S0 + H4, [100.0, 100.0, 90.0, 91.0]), (B, S0 + H4, [100.0, 100.0, 90.0, 91.0]), (C, S0 + H4, [100.0, 110.0, 100.0, 109.0])]
    sc = "R1_150U|cross_1tick"
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, A, 100.0, -0.01), (S0, B, 100.0, -0.02)], short_cands=[(S0, C, 100.0, -30.0)], crash=crash)
        rc, res, det = run(env, ["--global-max-slots", "0", "--global-daily-loss-u", "0"])
        mc = res["arms"][sc]["monthly_combined"]
        row = mc["by_year_month"]["2024-03"]
        _check(row["closed_trades_total"] == 3 and row["long_closed_trades"] == 2 and row["short_closed_trades"] == 1, "3 closed = 2 long + 1 short: %r" % row)
        _check(row["unique_first_fills_total"] == 3 and row["long_unique_first_fills"] == 2 and row["short_unique_first_fills"] == 1, "first fills by direction: %r" % row)
        _check(row["is_partial_month"] is True and row["in_target_band_100_200"] is None, "partial month reported, not judged")
        _check(mc["summary"]["full_months"] == 0 and mc["target_band_closed_per_month"] == [100, 200], "summary")
        _check("EXIT UTC month" in mc["definition"], "definition states exit-month rule")
    # direct unit check of the band logic and the exit-month rule on fabricated month data (no market data)
    spec = importlib.util.spec_from_file_location("short_for_monthly_test", str(REAL_SHORT))
    sm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sm)
    JAN, FEB, MAR = 1704067200000, 1706745600000, 1709251200000  # 2024-01-01 / 02-01 / 03-01 UTC
    def tr(side, x, net=1.0):
        return {"side": side, "ets": x - H4, "xts": x, "net": net, "fee": 0.1, "fund": 0.0}
    trades = [tr("long", JAN + 5 * H4 + i * M30) for i in range(100)] + [tr("short", JAN + 9 * H4 + i * M30) for i in range(50)]
    trades += [tr("long", FEB + 5 * H4 + i * M30) for i in range(10)]
    trades.append({"side": "long", "ets": JAN + 28 * DAY, "xts": FEB + H4, "net": -1.0, "fee": 0.1, "fund": 0.0})  # opened Jan, closed Feb
    ol = [{"outcome": "filled", "ets": t["ets"], "leg": 0 if t["side"] == "long" else 1} for t in trades]
    leg_ym = {li: sm._build_by_year_month([o for o in ol if o["leg"] == li], [t for t in trades if t["side"] == ("long" if li == 0 else "short")],
                                          start_ts_ms=JAN, end_ts_ms=MAR - M30) for li in (0, 1)}
    mc = mod._monthly_combined(sm, ol, trades, leg_ym, JAN, MAR - M30)
    j, f = mc["by_year_month"]["2024-01"], mc["by_year_month"]["2024-02"]
    _check(j["closed_trades_total"] == 150 and j["in_target_band_100_200"] is True, "Jan 150 closed in band: %r" % j)
    _check(f["closed_trades_total"] == 11 and f["in_target_band_100_200"] is False, "Feb counts the Jan-opened trade by EXIT month (11): %r" % f)
    _check(j["long_closed_trades"] == 100 and j["short_closed_trades"] == 50, "direction contribution")
    _check(mc["summary"] == {"full_months": 2, "months_in_band": 1, "months_below_band": 1, "months_above_band": 0}, "band summary %r" % mc["summary"])
    print("MONTHLY: combined closed trades by exit UTC month, first fills, direction split, 100-200 band on full months")


def test_engine_source_sha_recorded():
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, SYMS[0], 100.0, -0.01)])
        rc, res, det = run(env)
        f = env["out"] / getattr(mod, "ENGINE_SRC_NAME", "combo_engine_patched_source.txt")
        _check(f.is_file(), "patched engine source written to out-dir")
        h = mod.sha(f)
        _check(res.get("combo_engine_patched_source_sha256") == h == res["sha256"]["combo_engine_source"]
               == res["sha256"]["combo_engine_source_file"], "recorded SHA == file SHA == executed source SHA")
        src = f.read_text(encoding="utf-8")
        _check("def run_audit_sim_combo(" in src and "_leg_doff" in src and "_combo_gate(" in src, "file is the patched engine")
        compile(src, "<check>", "exec")
    print("ENGINE SRC: patched source file + SHA-256 recorded in combo_result.json")


def _listing(d):
    return sorted(p.name for p in d.iterdir()) if d.exists() else []


def test_output_exclusivity():
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, SYMS[0], 100.0, -0.01)])
        rc, res, det = run(env)
        files = _listing(env["out"])
        _check(not [n for n in files if n.endswith(".tmp")], "no tmp")
        _check(res["sha256"]["details"] == mod.sha(env["out"] / mod.DETAILS_NAME), "details sha recorded")
        before = {n: (env["out"] / n).read_bytes() for n in files}
        try:
            mod.main(env["argv"])
            _check(False, "reused out-dir must be refused")
        except RuntimeError as exc:
            _check("NEW isolated out-dir" in str(exc), "fresh-dir message: %s" % exc)
        _check({n: (env["out"] / n).read_bytes() for n in _listing(env["out"])} == before, "old evidence untouched")
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, SYMS[0], 100.0, -0.01)], raise_long=True)
        try:
            mod.main(env["argv"])
            _check(False, "builder failure must raise")
        except RuntimeError as exc:
            _check("SYNTHETIC_BUILDER_FAILURE" in str(exc), "failure propagated")
        names = _listing(env["out"])
        _check(mod.RESULT_NAME not in names and not [n for n in names if n.endswith(".tmp")], "no result/tmp after failure: %r" % names)
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td))
        real_out = Path(td) / "elsewhere"
        real_out.mkdir()
        env["out"].symlink_to(real_out, target_is_directory=True)
        try:
            mod.main(env["argv"])
            _check(False, "symlink out-dir must be refused")
        except RuntimeError as exc:
            _check("symlink" in str(exc), "symlink refusal")
        _check(_listing(real_out) == [], "nothing written through symlink")
    print("OUTPUTS: fresh dir enforced, failure leaves no result, symlink refused")


def test_real_builders_smoke_and_dry_check():
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td))
        argv = [a for a in env["argv"]]
        for flag in ("--long-adapter", "--short-adapter", "--long-adapter-size", "--long-adapter-sha256",
                     "--short-adapter-size", "--short-adapter-sha256"):
            if flag in argv:  # drop stub adapters (+ their expected values) -> real pinned sibling adapters
                i = argv.index(flag)
                del argv[i:i + 2]
        rc = mod.main(argv + ["--scenarios", mod.DEFAULT_SCENARIOS])
        res = json.loads((env["out"] / mod.RESULT_NAME).read_text(encoding="utf-8"))
        _check(rc == 0 and set(res["arms"]) == set(mod.DEFAULT_SCENARIOS.split(",")), "4 arms")
        _check(res["sha256"]["long_adapter"] == mod.sha(REAL_LONG) and res["sha256"]["short_adapter"] == mod.sha(REAL_SHORT), "real adapters bound")
        _check(res["version"] == "v1.20" and res["scope"]["version"] == "v1.20", "version label")
        _check(res["scope"]["adapter_verification"]["short"]["expected_source"] == "pinned_constant", "pinned adapters verified")
        rc2 = mod.main(env["argv"][:6] + ["--dry-check"])
        _check(rc2 == 0, "dry-check")
    print("SMOKE: real builders run on flat synthetic data (0 signals), 4 arms, dry-check PASS")


def main():
    tests = [test_shared_margin_pool, test_global_slot_cap, test_global_daily_loss_taipei, test_same_inst_conflicts,
             test_missing_funding_annotation_and_inventory, test_uncomputable_windows, test_explicit_window_needs_evidence,
             test_cross_leg_rank_interleave, test_research_controls_switchable_and_listed, test_r2_arm_renamed,
             test_adapter_verified_before_load, test_network_blocked_before_adapter_load, test_leg_daily_loss_day_boundary,
             test_limitations_text_follows_parameters, test_main_comparison_parameter_set, test_monthly_combined_statistics,
             test_engine_source_sha_recorded, test_output_exclusivity, test_real_builders_smoke_and_dry_check]
    failed = 0
    for t in tests:
        try:
            t()
            print("RESULT %s: PASS" % t.__name__)
        except (Exception, SystemExit):  # SystemExit: argparse refusal of an unknown option counts as FAIL
            failed += 1
            print("RESULT %s: FAIL" % t.__name__)
            traceback.print_exc(limit=3, file=sys.stdout)
    if failed:
        print("COMBO_SYNTHETIC_TESTS_FAILED:", failed)
        return 1
    print("ALL_COMBO_L02_OPT01_SHARED_SYNTHETIC_TESTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
