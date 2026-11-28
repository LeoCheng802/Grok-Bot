#!/usr/bin/env python3
"""100% synthetic main() tests for run_combo_l02_opt01_shared_backtest.py (BACKTEST-READINESS-01 v1.17).

Zero real market data, zero network, zero live/demo trading, no historical or performance backtest.
The REAL registered engine files (engine/*.py) are copied into a temp dir and registered in a synthetic
manifest; the RETEST24 script / shared_risk are stubs. Candidate builders are replaced by tiny stub
adapters (they import the real adapters and override only the two build_cands_* functions) so that
the shared-account wiring can be exercised deterministically on hand-made OHLC bars.
Covers: shared margin pool, global slot cap, global Taipei-day loss, same-instrument cross-leg conflict
(same bar / held / allow_opposite / priority), missing funding annotation (no zero fill, no abort),
inventory complete==true semantics, uncomputable windows (inventory 51001 + explicit), output
exclusivity (fresh out-dir, failure leaves no result, symlink refused), real-builder smoke, dry-check.
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
SYMS = ["AAA-USDT-SWAP", "BBB-USDT-SWAP", "CCC-USDT-SWAP", "DDD-USDT-SWAP", "EEE-USDT-SWAP", "FFF-USDT-SWAP"]


def _check(cond, msg):
    if not cond:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + msg)


STUB_ADAPTER = '''import importlib.util as _u
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


def _write_stub(path, real, fn, cands, is_long, raise_=False):
    path.write_text(STUB_ADAPTER % {"modname": "_real_" + path.stem, "real": str(real), "cands": cands,
                                    "raise_": raise_, "fn": fn, "is_long": is_long}, encoding="utf-8")


def make_env(root, long_cands=(), short_cands=(), max_lever=None, crash=None, funding=(), raise_long=False,
             inventory_rows=None, unc_windows=None):
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
    _write_stub(sa, REAL_SHORT, "build_cands_retest24", list(short_cands), False)
    argv = ["--manifest", str(code / "manifest.json"),
            "--retest24-script", str(code / "scripts" / "RETEST24_R1_R2_Switchable_v1_5_auditfix.py"),
            "--shared-risk", str(code / "scripts" / "shared_risk.py"),
            "--cache-dir", str(cache), "--funding-db", str(db), "--out-dir", str(root / "out"),
            "--start-utc", START, "--end-utc", END,
            "--long-adapter", str(la), "--short-adapter", str(sa)]
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
        rc, res, det = run(env, ["--global-max-slots", "2"])
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
    sc = "R2_100U|cross_1tick"
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
    sc = "R1_150U|cross_1tick"
    D_, E = SYMS[3], SYMS[4]
    inv = [(D_, "2024-03", "pending_check", "rest_51001_instrument_not_listed", "")]
    unc = [{"inst_id": E, "from_utc": "2024-03-02T00:00:00Z", "reason": "synthetic delisting"}]
    with tempfile.TemporaryDirectory() as td:
        env = make_env(Path(td), long_cands=[(S0, D_, 100.0, -0.01), (S0, E, 100.0, -0.02)], inventory_rows=inv, unc_windows=unc)
        rc, res, det = run(env)
        arm = res["arms"][sc]
        _check(arm["combo_gates"]["blocked_counts"].get("uncomputable_window", {}).get("0") == 1, "D blocked (51001 month)")
        op = {o["inst_id"]: o for o in det["scenarios"][sc]["open_at_end"]}
        _check(D_ not in op, "D never entered")
        _check(op[E]["computability"].startswith("不可計算"), "E position overlapping window flagged")
        _check("uncomputable_positions_present" in arm["gaps"], "gap listed")
        _check(res["uncomputable_windows_count"] == 2, "both windows registered, symbols not dropped")
    print("UNCOMPUTABLE: 51001 month blocks entries; overlapping position flagged; no symbol dropped")


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
        i = argv.index("--long-adapter")
        del argv[i:i + 4]  # drop stub adapters -> real sibling adapters
        rc = mod.main(argv + ["--scenarios", mod.DEFAULT_SCENARIOS])
        res = json.loads((env["out"] / mod.RESULT_NAME).read_text(encoding="utf-8"))
        _check(rc == 0 and set(res["arms"]) == set(mod.DEFAULT_SCENARIOS.split(",")), "4 arms")
        _check(res["sha256"]["long_adapter"] == mod.sha(REAL_LONG) and res["sha256"]["short_adapter"] == mod.sha(REAL_SHORT), "real adapters bound")
        _check(res["version"] == "v1.17" and res["scope"]["version"] == "v1.17", "version label")
        rc2 = mod.main(env["argv"][:6] + ["--dry-check"])
        _check(rc2 == 0, "dry-check")
    print("SMOKE: real builders run on flat synthetic data (0 signals), 4 arms, dry-check PASS")


def main():
    tests = [test_shared_margin_pool, test_global_slot_cap, test_global_daily_loss_taipei, test_same_inst_conflicts,
             test_missing_funding_annotation_and_inventory, test_uncomputable_windows, test_output_exclusivity,
             test_real_builders_smoke_and_dry_check]
    failed = 0
    for t in tests:
        try:
            t()
            print("RESULT %s: PASS" % t.__name__)
        except Exception:
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
