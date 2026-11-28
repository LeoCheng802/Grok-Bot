#!/usr/bin/env python3
"""100% synthetic main() tests for run_l1_bounded_backtest.py (BACKTEST-READINESS-01 v1.13, updated v1.17).

Zero real market data, zero network access, zero live/demo trading, no historical run.
A tiny stub engine (engine/b6_sim_portable.py) and stub FIB_4H_Long_v3 are written into a
temp dir and registered in a synthetic manifest, then the real L1 main(argv) is executed
through serialization and writing. Covers:
1. Success exit: rc=0, l1_bounded_local_details.json exists (status PASS, by_year_month),
   its sha256 is recorded in l1_bounded_result.json, no *.tmp left behind.
2. Missing-funding exit: rc=2, abort report written, NO success report (stale one removed),
   local details keep arms, by_year_month, untruncated missing_funding_events_all, status.
3. Details-path collision with a fixed input is rejected before ANY write/copy/load
   (sentinel: zero writes, zero copies, zero np.load, zero module loads, out-dir unchanged).
v1.17 changes:
- case 2 now runs in a NEW isolated out-dir (reusing a dir is refused by design since v1.17);
4. Reused out-dir (stale success report AND stale abort report from earlier runs) is refused before any
   write/copy/load; both stale files stay byte-identical (old evidence preserved, never mixed).
5. One version label: scope, result, abort report and local details all carry runner RUNNER_VERSION
   (v1.13 mixed "v1.0" and "v1.9").

Runner path defaults to the sibling run_l1_bounded_backtest.py; override with env
L1_RUNNER_PATH to run the same tests against another revision (old-fail / new-pass evidence).
"""
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np

MOD_PATH = Path(os.environ.get("L1_RUNNER_PATH") or (Path(__file__).resolve().parent / "run_l1_bounded_backtest.py"))
spec = importlib.util.spec_from_file_location("run_l1_bounded_backtest_under_test", str(MOD_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SYM = "SYNTH-USDT-SWAP"
TS_BASE = 1705708800000  # 2024-01-20T00:00:00Z
N_MISS = 30  # > 25 sample cap, proves untruncated detail
SCENARIOS = "TP_2.5pct|cross_1tick,TP_2.5pct|delay1bar"
DETAILS_NAME = "l1_bounded_local_details.json"


def _check(cond, msg):
    if not cond:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + msg)


def _b6_stub(include_miss):
    miss = (
        '    events = {(0, "%s", 1706745600000 + i * 28800000, "miss_8h") for i in range(%d)}\n' % (SYM, N_MISS)
        if include_miss else '    events = set()\n'
    )
    return (
        "def run_audit_sim_b6(raw, bars, spec, **kw):\n"
        + miss +
        "    return {\n"
        '        "_ord_log": [\n'
        '            {"inst": "%s", "pts": 1705795200000, "outcome": "filled", "ets": 1705798800000},\n'
        '            {"inst": "%s", "pts": 1705881600000, "outcome": "expired", "ets": None},\n'
        "        ],\n"
        '        "_trades": [{"inst": "%s", "ets": 1705798800000, "xts": 1706860800000, "net": 50.0, "fee": 1.0, "fund": 0.5, "reason": "tp"}],\n'
        '        "final_eq_u": 50050.0, "ret_eq_pct": 0.1, "cagr_eq_pct": 1.0, "mtm_mdd_pct": 0.1, "ann_calmar_eq": 10.0,\n'
        '        "overall_trade_stats": {"trades": 1, "win_rate_pct": 100.0, "net_pnl_u": 50.0, "fee_u": 1.0, "fund_u": 0.5, "profit_factor": "INF", "expectancy_u": 50.0},\n'
        '        "real_fund_u": 0.5, "by_year": {},\n'
        '        "f_ev_real_8h": 1, "f_ev_real_non8h": 0, "f_ev_miss_8h": len(events), "events_set": events,\n'
        "    }\n"
    ) % (SYM, SYM, SYM)


ORIG_LONG_STUB = (
    "from decimal import Decimal as D, ROUND_DOWN\n"
    "TP_PCT = D('0.025')\n"
    "SL_PCT = D('0.04')\n"
    "def signal(api, sp, bt):\n"
    "    return None\n"
    "def _al(v, tk):\n"
    "    return (D(str(float(v))) / tk).to_integral_value(rounding=ROUND_DOWN) * tk\n"
    "def price_targets(avg, tk):\n"
    "    return _al(avg * (D(1) + TP_PCT), tk), _al(avg * (D(1) - SL_PCT), tk)\n"
)


def _make_funding_db(db_path):
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL)")
        con.execute("INSERT INTO funding_archive VALUES (?, ?, ?, ?)", (SYM, TS_BASE, TS_BASE + 123, 0.0001))
        con.commit()
    finally:
        con.close()


def _make_env(root, include_miss, funding_db_path=None):
    code = root / "code"
    (code / "engine").mkdir(parents=True)
    (code / "scripts").mkdir(parents=True)
    files = {
        "engine/b6_sim_portable.py": _b6_stub(include_miss),
        "engine/sim_50k_v3_2_sl_fix.py": "STUB = 1\n",
        "engine/audit_v3_1_full.py": "STUB = 2\n",
        "engine/run_q38_audit_01.py": "STUB = 3\n",
        "scripts/FIB_4H_Long_v3.py": ORIG_LONG_STUB,
        "scripts/shared_risk.py": "SHARED_RISK_STUB = True\n",
    }
    entries = {}
    for rel, text in files.items():
        fp = code / rel
        fp.write_text(text, encoding="utf-8")
        entries[rel] = {"sha256": mod.sha(fp), "size": fp.stat().st_size}
    manifest = code / "manifest.json"
    manifest.write_text(json.dumps({"files": entries}), encoding="utf-8")

    cache = root / "cache"
    cache.mkdir()
    ts30 = np.array([TS_BASE + i * 1800000 for i in range(8)], dtype=np.int64)
    ts4 = np.array([TS_BASE + i * 14400000 for i in range(4)], dtype=np.int64)
    np.savez(
        cache / (SYM + ".npz"),
        ts30=ts30, ohlc30=np.ones((8, 4)) * 100.0,
        ts4=ts4, ohlc4=np.ones((4, 4)) * 100.0,
        ts1=ts4, ohlc1=np.ones((4, 4)) * 100.0,
        d1_ts=np.array([TS_BASE], dtype=np.int64),
    )
    (cache / "manifest.json").write_text(
        json.dumps({"symbols": {SYM: {"spec": {"tickSz": "0.1", "maxLever": "20"}}}}), encoding="utf-8"
    )
    db = funding_db_path or (root / "funding.sqlite")
    db.parent.mkdir(parents=True, exist_ok=True)
    _make_funding_db(db)
    out = root / "out"
    argv = [
        "--manifest", str(manifest),
        "--orig-long", str(code / "scripts/FIB_4H_Long_v3.py"),
        "--shared-risk", str(code / "scripts/shared_risk.py"),
        "--cache-dir", str(cache),
        "--funding-db", str(db),
        "--out-dir", str(out),
        "--symbols", SYM,
        "--start-utc", "2024-01-15T00:00:00Z",
        "--end-utc", "2024-02-29T23:30:00Z",
        "--scenarios", SCENARIOS,
    ]
    return {"argv": argv, "out": out, "db": db}


def _listing(d):
    return sorted(p.name for p in d.iterdir()) if d.exists() else []


def test_success_exit():
    with tempfile.TemporaryDirectory() as td:
        env = _make_env(Path(td), include_miss=False)
        rc = mod.main(env["argv"])
        out = env["out"]
        det_p, rep_p = out / DETAILS_NAME, out / "l1_bounded_result.json"
        tmps = [n for n in _listing(out) if n.endswith(".tmp")]
        print("SUCCESS_RC:", rc)
        print("SUCCESS_OUT_FILES:", _listing(out))
        _check(rc == 0, "success rc must be 0, got %r" % (rc,))
        _check(det_p.is_file(), "local details file missing on success")
        _check(rep_p.is_file(), "final report missing on success")
        _check(not (out / "l1_bounded_missing_funding_abort.json").exists(), "abort report must not exist on success")
        _check(not tmps, "no .tmp may remain: %r" % (tmps,))
        det = json.loads(det_p.read_text(encoding="utf-8"))
        rep = json.loads(rep_p.read_text(encoding="utf-8"))
        _check(det["status"] == "PASS", "details status must be PASS")
        _check(set(det["by_year_month"]) == set(SCENARIOS.split(",")), "details by_year_month per scenario")
        bym = det["by_year_month"]["TP_2.5pct|cross_1tick"]
        _check(list(bym) == ["2024-01", "2024-02"], "scored months enumerated: %r" % (list(bym),))
        _check(bym["2024-01"]["unique_first_fills"] == 1 and bym["2024-01"]["closed_trades"] == 0, "fill month (ets)")
        _check(bym["2024-02"]["closed_trades"] == 1 and bym["2024-02"]["is_partial_month"] is False, "close month (xts), full Feb to 23:30")
        _check(bym["2024-01"]["is_partial_month"] is True, "Jan starts 01-15 -> partial")
        _check(rep["local_details_file"] == DETAILS_NAME, "report must name details file")
        _check(rep["local_details_sha256"] == mod.sha(det_p), "report must record details sha256")
        _check(rep["arms"]["TP_2.5pct|cross_1tick"]["by_year_month"] == bym, "same-convention monthly in report and details")
        print("SUCCESS_DETAILS_SHA256_RECORDED:", rep["local_details_sha256"] == mod.sha(det_p))
        print("SUCCESS_DETAILS_BY_YEAR_MONTH_KEYS:", list(bym))


def test_missing_funding_exit():
    with tempfile.TemporaryDirectory() as td:
        env = _make_env(Path(td), include_miss=True)
        out = env["out"]
        stale = out / "l1_bounded_result.json"  # v1.17: fresh out-dir; no success report may appear on abort
        rc = mod.main(env["argv"])
        det_p = out / DETAILS_NAME
        abort_p = out / "l1_bounded_missing_funding_abort.json"
        tmps = [n for n in _listing(out) if n.endswith(".tmp")]
        print("ABORT_RC:", rc)
        print("ABORT_OUT_FILES:", _listing(out))
        _check(rc == 2, "missing-funding rc must be 2, got %r" % (rc,))
        _check(not stale.exists(), "success report must not exist on abort")
        _check(abort_p.is_file(), "abort report missing")
        _check(det_p.is_file(), "local details file missing on abort")
        _check(not tmps, "no .tmp may remain: %r" % (tmps,))
        det = json.loads(det_p.read_text(encoding="utf-8"))
        ab = json.loads(abort_p.read_text(encoding="utf-8"))
        _check(det["status"] == "ABORTED_MISSING_FUNDING" and ab["status"] == "ABORTED_MISSING_FUNDING", "status")
        _check(det.get("performance_valid") is False, "abort details must flag performance_valid False")
        _check("arms" in det and set(det["arms"]) == set(SCENARIOS.split(",")), "abort details must keep arms")
        _check(det["by_year_month"]["TP_2.5pct|cross_1tick"] == det["arms"]["TP_2.5pct|cross_1tick"]["by_year_month"], "by_year_month same convention")
        _check(list(det["by_year_month"]["TP_2.5pct|cross_1tick"]) == ["2024-01", "2024-02"], "abort monthly enumerated")
        for name in SCENARIOS.split(","):
            n_all = len(det["scenarios"][name]["missing_funding_events_all"])
            n_gap = len(det["missing_funding_gaps"][name]["missing_funding_events_all"])
            _check(n_all == N_MISS and n_gap == N_MISS, "untruncated miss events %s: %d/%d" % (name, n_all, n_gap))
        _check("arms" not in ab, "abort report must not carry a performance summary")
        _check(ab["local_details_sha256"] == mod.sha(det_p), "abort report must record details sha256")
        print("ABORT_SUCCESS_REPORT_EXISTS:", stale.exists())
        print("ABORT_DETAILS_KEYS:", sorted(det))
        print("ABORT_MISSING_EVENTS_ALL_PER_SCENARIO:", {n: len(det["scenarios"][n]["missing_funding_events_all"]) for n in SCENARIOS.split(",")})


def _run_collision(case, setup):
    """setup(root) -> env; must make the details path collide with a fixed input."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        env, victim = setup(root)
        victim_sha = mod.sha(victim)
        before = _listing(env["out"])
        calls = {"writes": 0, "copy2": 0, "np_load": 0, "load_mods": 0}
        o_write, o_copy, o_np, o_mods = mod._atomic_write_text, mod.shutil.copy2, mod.np.load, mod._load_runtime_modules

        def spy(key, fn):
            def w(*a, **k):
                calls[key] += 1
                return fn(*a, **k)
            return w

        mod._atomic_write_text = spy("writes", o_write)
        mod.shutil.copy2 = spy("copy2", o_copy)
        mod.np.load = spy("np_load", o_np)
        mod._load_runtime_modules = spy("load_mods", o_mods)
        err = None
        try:
            try:
                mod.main(env["argv"])
            except Exception as exc:  # expected RuntimeError
                err = exc
        finally:
            mod._atomic_write_text, mod.shutil.copy2, mod.np.load, mod._load_runtime_modules = o_write, o_copy, o_np, o_mods
        after = _listing(env["out"])
        print("COLLISION[%s]_ERROR:" % case, type(err).__name__ if err else None, "-", str(err) if err else "")
        print("COLLISION[%s]_SENTINEL:" % case, json.dumps(calls), "out_before=", before, "out_after=", after,
              "victim_unchanged=", mod.sha(victim) == victim_sha)
        _check(isinstance(err, RuntimeError) and "local details file" in str(err), "%s: must be rejected by disjointness guard naming the details file" % case)
        _check(all(v == 0 for v in calls.values()), "%s: no write/copy/np.load/module load before rejection" % case)
        _check(before == after, "%s: out-dir must be unchanged" % case)
        _check(mod.sha(victim) == victim_sha, "%s: colliding input untouched" % case)


def test_details_path_collision_rejected():
    # (a) --funding-db literally IS <out-dir>/l1_bounded_local_details.json (resolve() equality)
    def setup_equal(root):
        db = root / "out" / DETAILS_NAME
        env = _make_env(root, include_miss=False, funding_db_path=db)
        return env, db

    # (b) <out-dir>/l1_bounded_local_details.json is a symlink to a registered manifest entry (samefile)
    def setup_symlink(root):
        env = _make_env(root, include_miss=False)
        env["out"].mkdir(parents=True)
        victim = root / "code" / "scripts" / "shared_risk.py"
        (env["out"] / DETAILS_NAME).symlink_to(victim)
        return env, victim

    # (c) <out-dir>/l1_bounded_local_details.json.tmp is a symlink to the funding DB
    def setup_tmp(root):
        env = _make_env(root, include_miss=False)
        env["out"].mkdir(parents=True)
        (env["out"] / (DETAILS_NAME + ".tmp")).symlink_to(env["db"])
        return env, env["db"]

    _run_collision("details==funding-db", setup_equal)
    _run_collision("details->manifest-entry symlink", setup_symlink)
    _run_collision("details.tmp->funding-db symlink", setup_tmp)


def test_reused_out_dir_refused_old_evidence_kept():
    """v1.17: a reused out-dir holding stale result + abort evidence is refused before any write."""
    with tempfile.TemporaryDirectory() as td:
        env = _make_env(Path(td), include_miss=False)
        out = env["out"]
        out.mkdir(parents=True)
        stale_ok = out / "l1_bounded_result.json"
        stale_abort = out / "l1_bounded_missing_funding_abort.json"
        stale_ok.write_text('{"status": "PASS", "stale": true}\n', encoding="utf-8")
        stale_abort.write_text('{"status": "ABORTED_MISSING_FUNDING", "stale": true}\n', encoding="utf-8")
        snap = {p.name: p.read_bytes() for p in out.iterdir()}
        calls = {"writes": 0, "copy2": 0, "np_load": 0, "load_mods": 0}
        o_write, o_copy, o_np, o_mods = mod._atomic_write_text, mod.shutil.copy2, mod.np.load, mod._load_runtime_modules

        def spy(key, fn):
            def w(*a, **k):
                calls[key] += 1
                return fn(*a, **k)
            return w

        mod._atomic_write_text = spy("writes", o_write)
        mod.shutil.copy2 = spy("copy2", o_copy)
        mod.np.load = spy("np_load", o_np)
        mod._load_runtime_modules = spy("load_mods", o_mods)
        err, rc = None, None
        try:
            try:
                rc = mod.main(env["argv"])
            except Exception as exc:
                err = exc
        finally:
            mod._atomic_write_text, mod.shutil.copy2, mod.np.load, mod._load_runtime_modules = o_write, o_copy, o_np, o_mods
        after = {p.name: p.read_bytes() for p in out.iterdir()}
        print("REUSED_OUT_DIR:", "rc=", rc, "err=", type(err).__name__ if err else None, "-", str(err) if err else "",
              "calls=", json.dumps(calls), "files_after=", sorted(after))
        _check(isinstance(err, RuntimeError) and "NEW isolated out-dir" in str(err), "reused out-dir must be refused")
        _check(all(v == 0 for v in calls.values()), "no write/copy/np.load/module load before refusal")
        _check(after == snap, "stale evidence must stay byte-identical (no mixing, no deletion)")


def test_single_version_label():
    """v1.17: scope/result/details (success) and abort/details (abort) all carry RUNNER_VERSION."""
    want = "v1.17"
    for include_miss, files in ((False, ("l1_bounded_scope.json", "l1_bounded_result.json", DETAILS_NAME)),
                                (True, ("l1_bounded_scope.json", "l1_bounded_missing_funding_abort.json", DETAILS_NAME))):
        with tempfile.TemporaryDirectory() as td:
            env = _make_env(Path(td), include_miss=include_miss)
            mod.main(env["argv"])
            got = {f: json.loads((env["out"] / f).read_text(encoding="utf-8")).get("version") for f in files}
            print("VERSION_LABELS[%s]:" % ("abort" if include_miss else "success"), got)
            _check(set(got.values()) == {want}, "all version labels must equal %s: %r" % (want, got))
    _check(getattr(mod, "RUNNER_VERSION", None) == want, "runner must expose RUNNER_VERSION = %s" % want)


if __name__ == "__main__":
    print("RUNNER_UNDER_TEST_SHA256:", mod.sha(MOD_PATH))
    failed = []
    for fn in (test_success_exit, test_missing_funding_exit, test_details_path_collision_rejected,
               test_reused_out_dir_refused_old_evidence_kept, test_single_version_label):
        print("=== " + fn.__name__)
        try:
            fn()
            print("RESULT " + fn.__name__ + ": PASS")
        except Exception as exc:
            failed.append(fn.__name__)
            print("RESULT " + fn.__name__ + ": FAIL " + type(exc).__name__ + ": " + str(exc))
            traceback.print_exc(limit=2, file=sys.stdout)
    if failed:
        print("L1_MAIN_SYNTHETIC_TESTS_FAILED:", failed)
        sys.exit(1)
    print("ALL_L1_MAIN_SYNTHETIC_TESTS_PASS")
