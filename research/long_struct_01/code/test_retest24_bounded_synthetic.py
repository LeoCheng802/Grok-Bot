#!/usr/bin/env python3
"""100% synthetic regression tests for run_retest24_bounded_backtest.py (exact B6/Q38 schema).

Zero real market data, zero network access, zero live/demo trading.
Covers:
1. Old-vs-new load_funding_db regression (AttributeError on old set shape vs fixed dict shape + ts_raw > ts_snapped SQLite fixture + miss fallback).
2. Per-file NPZ hash/size verification, fixed_inputs disjoint guard, and tamper rejection.
3. Exact B6/Q38 field mapping (pts/ets in _ord_log, ets/xts in _trades, ets in _open):
   - Cross-month trade: first fill (ets) in 2024-01, close (xts) in 2024-02.
   - Zero-trade scored month (2024-03) explicitly enumerated with 0.
   - Open-at-end position (ets in 2024-04, no _trades row) counted in unique_first_fills for 2024-04, NOT closed_trades.
   - Non-filled orders (expired, margin_rej, pend_at_end) NOT counted in unique_first_fills.
   - Missing xts trade goes to MISSING_EXIT_TS and NEVER falls back to ets.
   - Partial month flag (is_partial_month) and explicit realized-only equity_curve_basis.
   - Untruncated (>25) miss_8h events in local details.
"""
import importlib.util
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

MOD_PATH = Path(__file__).resolve().parent / "run_retest24_bounded_backtest.py"
spec = importlib.util.spec_from_file_location("run_retest24_bounded_backtest", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + msg)


def _utc_ms(y: int, m: int, d: int, h: int = 0) -> int:
    return int(datetime(y, m, d, h, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)


def _make_synth_funding_db(db_path: Path) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL)")
        con.execute("INSERT INTO funding_archive VALUES (?, ?, ?, ?)", ("SYNTH-USDT-SWAP", 1700006400000, 1700006400123, 0.000125))
        con.execute("INSERT INTO funding_archive VALUES (?, ?, ?, ?)", ("SYNTH-USDT-SWAP", 1700035200000, 1700035200456, -0.000250))
        con.commit()
    finally:
        con.close()


def test_old_vs_new_funding_db_regression() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "synth_funding.sqlite"
        _make_synth_funding_db(db_path)

        old_ov_raw = {"SYNTH-USDT-SWAP": {1700006400000, 1700035200000}}
        reproduced_attr_err = False
        try:
            _ = old_ov_raw.get("SYNTH-USDT-SWAP", {}).get(1700006400000, 1700006400000)
        except AttributeError:
            reproduced_attr_err = True
        _check(reproduced_attr_err, "Expected AttributeError on old set-based ov_raw shape")

        fmaps, ov_raw = mod.load_funding_db(db_path)
        _check(isinstance(ov_raw["SYNTH-USDT-SWAP"], dict), "ov_raw[inst] must be dict")
        ts_snap_1, ts_raw_1, ts_miss = 1700006400000, 1700006400123, 1700064000000
        _check(abs(fmaps["SYNTH-USDT-SWAP"][ts_snap_1] - 0.000125) < 1e-12, "rate lookup mismatch")
        hit_raw = ov_raw.get("SYNTH-USDT-SWAP", {}).get(ts_snap_1, ts_snap_1)
        _check(hit_raw == ts_raw_1 and hit_raw > ts_snap_1, "ts_raw > ts_snapped not preserved")
        _check(ov_raw.get("SYNTH-USDT-SWAP", {}).get(ts_miss, ts_miss) == ts_miss, "miss fallback failed")


def test_npz_manifest_and_disjoint_guard() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        npz_path = root / "SYNTH-USDT-SWAP.npz"
        np.savez(
            npz_path,
            ts30=np.array([1700006400000, 1700008200000], dtype=np.int64),
            ohlc30=np.ones((2, 4), dtype=np.float64),
            ts4=np.array([1700006400000], dtype=np.int64),
            ohlc4=np.ones((1, 4), dtype=np.float64),
            ts1=np.array([1700006400000], dtype=np.int64),
            ohlc1=np.ones((1, 4), dtype=np.float64),
            d1_ts=np.array([1700006400000], dtype=np.int64),
        )
        good_sha = mod.sha(npz_path)
        good_size = npz_path.stat().st_size

        resolved, recs = mod._verify_and_record_npz_inputs(
            ["SYNTH-USDT-SWAP"], root, {"SYNTH-USDT-SWAP": {}},
            {"SYNTH-USDT-SWAP": {"sha256": good_sha, "size_bytes": good_size}},
        )
        _check(resolved["SYNTH-USDT-SWAP"] == npz_path.resolve(), "resolved NPZ path mismatch")
        _check(recs["SYNTH-USDT-SWAP"]["manifest_verified"] is True, "manifest_verified should be True")

        failed_bad_sha = False
        try:
            mod._verify_and_record_npz_inputs(
                ["SYNTH-USDT-SWAP"], root, {"SYNTH-USDT-SWAP": {}},
                {"SYNTH-USDT-SWAP": {"sha256": "0" * 64, "size_bytes": good_size}},
            )
        except RuntimeError:
            failed_bad_sha = True
        _check(failed_bad_sha, "bad NPZ sha256 must raise RuntimeError")

        failed_overlap = False
        try:
            mod._verify_output_paths_disjoint(
                [("evil_out", npz_path)],
                [("symbol npz SYNTH-USDT-SWAP", resolved["SYNTH-USDT-SWAP"])],
            )
        except RuntimeError:
            failed_overlap = True
        _check(failed_overlap, "output overlapping NPZ must be rejected")


def test_b6_q38_cross_month_and_local_details() -> None:
    # Scored window: 2024-01-15 (partial) through 2024-04-20 (partial); 2024-02 & 2024-03 are full months.
    start_ts = _utc_ms(2024, 1, 15, 0)
    end_ts = _utc_ms(2024, 4, 20, 0)

    # Exact B6 _ord_log schema (pts, exp, px, outcome, ets) and Q38 _trades schema (ets, xts, net, fund, fee, reason)
    t_fill_jan = _utc_ms(2024, 1, 31, 12)
    t_close_feb = _utc_ms(2024, 2, 2, 8)
    t_open_apr = _utc_ms(2024, 4, 10, 4)

    events = {(0, "SYNTH-USDT-SWAP", _utc_ms(2024, 2, 1, 0) + i * 28800000, "miss_8h") for i in range(30)}
    fake_res = {
        "_ord_log": [
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 1, 31, 8), "exp": _utc_ms(2024, 2, 2, 8), "px": 100.0, "outcome": "filled", "ets": t_fill_jan, "filled_on_first_bar": False},
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 2, 5, 0), "exp": _utc_ms(2024, 2, 7, 0), "px": 102.0, "outcome": "expired", "ets": None},
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 3, 10, 0), "exp": _utc_ms(2024, 3, 12, 0), "px": 98.0, "outcome": "margin_rej", "ets": None},
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 4, 9, 20), "exp": _utc_ms(2024, 4, 11, 20), "px": 95.0, "outcome": "filled", "ets": t_open_apr, "filled_on_first_bar": False},
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 4, 19, 20), "exp": _utc_ms(2024, 4, 21, 20), "px": 94.0, "outcome": "pend_at_end", "ets": None},
        ],
        "_trades": [
            # Cross-month: filled in 2024-01, closed in 2024-02
            {"inst": "SYNTH-USDT-SWAP", "side": "short", "ets": t_fill_jan, "xts": t_close_feb, "net": 120.5, "fund": 1.2, "fee": 2.5, "reason": "tp"},
            # Malformed missing xts must NEVER fall back to ets (2024-02)
            {"inst": "SYNTH-USDT-SWAP", "side": "short", "ets": t_close_feb, "xts": None, "net": -10.0, "fund": 0.0, "fee": 1.0, "reason": "malformed"},
        ],
        "_open": [
            {"inst": "SYNTH-USDT-SWAP", "ets": t_open_apr},
        ],
        "_end_eq_raw": 50110.5,
        "mtm_mdd_pct": 0.42,
        "f_ev_real_8h": 4,
        "f_ev_real_non8h": 0,
        "f_ev_miss_8h": 30,
        "_real_fund_raw": 1.2,
        "events_set": events,
    }

    summary = mod.summarize_run(fake_res, start_ts_ms=start_ts, end_ts_ms=end_ts)
    bym = summary["by_year_month"]

    # Partial vs full month flags
    _check(bym["2024-01"]["is_partial_month"] is True, "2024-01 should be partial")
    _check(bym["2024-02"]["is_partial_month"] is False, "2024-02 should be full")
    _check(bym["2024-03"]["is_partial_month"] is False, "2024-03 should be full")
    _check(bym["2024-04"]["is_partial_month"] is True, "2024-04 should be partial")

    # Cross-month attribution: Jan has 1 fill / 0 closes; Feb has 0 fills / 1 close (+120.5)
    _check(bym["2024-01"]["unique_first_fills"] == 1 and bym["2024-01"]["closed_trades"] == 0, "2024-01 fill/close mismatch")
    _check(bym["2024-02"]["unique_first_fills"] == 0 and bym["2024-02"]["closed_trades"] == 1 and abs(bym["2024-02"]["closed_net_u"] - 120.5) < 1e-6, "2024-02 close mismatch")

    # Zero-trade month 2024-03 explicitly present with 0 fills (margin_rej excluded) and 0 closes
    _check(bym["2024-03"]["unique_first_fills"] == 0 and bym["2024-03"]["closed_trades"] == 0, "2024-03 zero-trade month mismatch")

    # Open-at-end in 2024-04: counted in unique_first_fills (pend_at_end excluded), 0 closes
    _check(bym["2024-04"]["unique_first_fills"] == 1 and bym["2024-04"]["closed_trades"] == 0, "2024-04 open-at-end mismatch")

    # Missing xts trade goes to MISSING_EXIT_TS, never backfilled to 2024-02
    _check("MISSING_EXIT_TS" in bym and bym["MISSING_EXIT_TS"]["closed_trades"] == 1, "missing xts must map to MISSING_EXIT_TS")
    _check("UNKNOWN" not in bym, "UNKNOWN bucket should not appear")

    details = mod.build_local_detail_payload("R1_150U|cross_1tick", fake_res, start_ts_ms=start_ts, end_ts_ms=end_ts)
    _check(details["equity_curve_basis"] == "REALIZED_CLOSED_TRADES_ONLY_NOT_MTM_UNREALIZED", "equity_curve_basis mismatch")
    _check(details["missing_funding_events_count"] == 30 and len(details["missing_funding_events_all"]) == 30, "miss_8h truncated")
    _check(details["unique_first_fills_count"] == 2, "expected 2 unique first fills (Jan + Apr open-at-end)")
    _check(details["first_fills"][0]["pts_utc"] is not None and details["first_fills"][0]["ets_utc"] is not None, "pts_utc/ets_utc should not be null")
    _check(details["closed_trades"][0]["ets_utc"] is not None and details["closed_trades"][0]["xts_utc"] is not None, "trade ets_utc/xts_utc should not be null")
    _check(details["closed_trades"][1]["xts_utc"] is None, "missing xts must stay None")

    diff = mod.HISTORICAL_MODEL_VS_DELIVERED_SCRIPT_DIFF
    items = {d["item"] for d in diff["known_parameter_and_data_diffs"]}
    _check({"slip_mkt", "ema55_calculation_window", "default_universe_exclusions"}.issubset(items), "missing diff items")




def _make_e2e_synth_env(root: Path, include_miss_events: bool = False):
    import json
    cache_dir = root / "cache"
    cache_dir.mkdir()
    out_dir = root / "out"
    code_dir = root / "code"
    code_dir.mkdir()

    # Tiny 100% synthetic stub engine & required manifest files
    miss_line = (
        '    events = {(0, "SYNTH-USDT-SWAP", 1706745600000 + i * 28800000, "miss_8h") for i in range(28)}'
        if include_miss_events else
        '    events = set()'
    )
    b6_stub = (
        'def run_audit_sim_b6(raw, bars, spec, **kw):\n'
        + miss_line + '\n'
        '    return {\n'
        '        "_ord_log": [{"inst": "SYNTH-USDT-SWAP", "pts": 1706659200000, "exp": 1706832000000, "px": 100.0, "outcome": "filled", "ets": 1706702400000}],\n'
        '        "_trades": [{"inst": "SYNTH-USDT-SWAP", "side": "short", "ets": 1706702400000, "xts": 1706860800000, "net": 50.0, "fund": 0.5, "fee": 1.0, "reason": "tp"}],\n'
        '        "_open": [], "_end_eq_raw": 50050.0, "mtm_mdd_pct": 0.1,\n'
        '        "f_ev_real_8h": 1, "f_ev_real_non8h": 0, "f_ev_miss_8h": len(events), "_real_fund_raw": 0.5, "events_set": events,\n'
        '    }\n'
    )
    (code_dir / "scripts").mkdir()
    (code_dir / "engine").mkdir()
    b6_path = code_dir / "engine" / "b6_sim_portable.py"
    b6_path.write_text(b6_stub, encoding="utf-8")
    sr_path = code_dir / "scripts" / "shared_risk.py"
    sr_path.write_text("SHARED_RISK_STUB = True\n", encoding="utf-8")
    rt_path = code_dir / "scripts" / "RETEST24_R1_R2_Switchable_v1_5_auditfix.py"
    rt_path.write_text("RETEST24_STUB = True\n", encoding="utf-8")
    s1_path = code_dir / "engine" / "sim_50k_v3_2_sl_fix.py"
    s1_path.write_text("STUB = 1\n", encoding="utf-8")
    s2_path = code_dir / "engine" / "audit_v3_1_full.py"
    s2_path.write_text("STUB = 2\n", encoding="utf-8")
    s3_path = code_dir / "engine" / "run_q38_audit_01.py"
    s3_path.write_text("STUB = 3\n", encoding="utf-8")

    manifest_path = code_dir / "manifest.json"
    manifest_data = {
        "files": {
            "engine/b6_sim_portable.py": {"sha256": mod.sha(b6_path), "size": b6_path.stat().st_size},
            "engine/sim_50k_v3_2_sl_fix.py": {"sha256": mod.sha(s1_path), "size": s1_path.stat().st_size},
            "engine/audit_v3_1_full.py": {"sha256": mod.sha(s2_path), "size": s2_path.stat().st_size},
            "engine/run_q38_audit_01.py": {"sha256": mod.sha(s3_path), "size": s3_path.stat().st_size},
            "scripts/shared_risk.py": {"sha256": mod.sha(sr_path), "size": sr_path.stat().st_size},
            "scripts/RETEST24_R1_R2_Switchable_v1_5_auditfix.py": {"sha256": mod.sha(rt_path), "size": rt_path.stat().st_size},
        }
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    db_path = root / "funding.sqlite"
    _make_synth_funding_db(db_path)

    npz_path = cache_dir / "SYNTH-USDT-SWAP.npz"
    ts_base = 1706745600000
    ts30 = np.array([ts_base + i * 1800000 for i in range(4)], dtype=np.int64)
    ts4 = np.array([ts_base + i * 14400000 for i in range(4)], dtype=np.int64)
    np.savez(
        npz_path,
        ts30=ts30, ohlc30=np.ones((4, 4), dtype=np.float64) * 100.0,
        ts4=ts4, ohlc4=np.ones((4, 4), dtype=np.float64) * 100.0,
        ts1=ts4, ohlc1=np.ones((4, 4), dtype=np.float64) * 100.0,
        d1_ts=np.array([ts_base], dtype=np.int64),
    )
    cache_manifest = {
        "symbols": {
            "SYNTH-USDT-SWAP": {"spec": {"tickSz": "0.1", "maxLever": "20"}}
        }
    }
    (cache_dir / "manifest.json").write_text(json.dumps(cache_manifest), encoding="utf-8")

    input_manifest_path = root / "input_manifest.json"
    input_manifest_path.write_text(
        json.dumps({"files": {"SYNTH-USDT-SWAP": {"sha256": mod.sha(npz_path), "size_bytes": npz_path.stat().st_size}}}),
        encoding="utf-8",
    )
    return {
        "manifest": manifest_path, "retest24": rt_path, "shared_risk": sr_path,
        "cache_dir": cache_dir, "funding_db": db_path, "out_dir": out_dir,
        "input_manifest": input_manifest_path, "npz_path": npz_path,
    }


def test_main_strict_manifest_disjoint_and_e2e_sentinels() -> None:
    import json
    with tempfile.TemporaryDirectory() as td:
        env = _make_e2e_synth_env(Path(td), include_miss_events=False)
        base_argv = [
            "--manifest", str(env["manifest"]),
            "--retest24-script", str(env["retest24"]),
            "--shared-risk", str(env["shared_risk"]),
            "--cache-dir", str(env["cache_dir"]),
            "--funding-db", str(env["funding_db"]),
            "--out-dir", str(env["out_dir"]),
            "--candidate", "RETEST24_V1_5_FROZEN",
            "--symbols", "SYNTH-USDT-SWAP",
            "--start-utc", "2024-01-15T00:00:00Z",
            "--end-utc", "2024-02-15T00:00:00Z",
            "--scenarios", "R1_150U|cross_1tick",
        ]

        # Sentinel wrappers to prove ZERO writes and ZERO np.load / module loads on rejection
        orig_np_load = mod.np.load
        orig_load_mods = mod._load_runtime_modules
        orig_write = mod._atomic_write_text
        calls = {"np_load": 0, "load_mods": 0, "writes": []}

        def _spy_np_load(*a, **kw):
            calls["np_load"] += 1
            return orig_np_load(*a, **kw)

        def _spy_load_mods(*a, **kw):
            calls["load_mods"] += 1
            return orig_load_mods(*a, **kw)

        def _spy_write(path, text):
            calls["writes"].append(str(path))
            return orig_write(path, text)

        mod.np.load = _spy_np_load
        mod._load_runtime_modules = _spy_load_mods
        mod._atomic_write_text = _spy_write
        try:
            # 1) Reject when --input-manifest is omitted and cache manifest has no sha256/size
            rejected_unlisted = False
            try:
                mod.main(base_argv)
            except RuntimeError:
                rejected_unlisted = True
            _check(rejected_unlisted, "main() must reject unlisted NPZ without expected sha256/size")
            _check(calls["np_load"] == 0 and calls["load_mods"] == 0 and not calls["writes"], "unlisted rejection must happen before np.load, module load, and any write")

            # 2) Reject BEFORE any write when an output path collides (via symlink) with a selected NPZ, leaving NPZ intact
            npz_sha_before = mod.sha(env["npz_path"])
            env["out_dir"].mkdir(parents=True, exist_ok=True)
            colliding_scope = env["out_dir"] / "retest24_bounded_scope.json"
            colliding_scope.symlink_to(env["npz_path"])
            rejected_collision = False
            try:
                mod.main(base_argv + ["--input-manifest", str(env["input_manifest"])])
            except RuntimeError:
                rejected_collision = True
            _check(rejected_collision, "main() must reject output colliding with NPZ")
            _check(calls["np_load"] == 0 and calls["load_mods"] == 0 and not calls["writes"], "disjoint rejection must happen before any write or load")
            _check(mod.sha(env["npz_path"]) == npz_sha_before, "colliding input NPZ must remain completely untouched")
            colliding_scope.unlink()

            # 3) Valid PASS run via main() writes local details
            rc_pass = mod.main(base_argv + ["--input-manifest", str(env["input_manifest"])])
            _check(rc_pass == 0, "expected rc=0 for synthetic PASS run")
            detail_file = env["out_dir"] / "retest24_bounded_local_details.json"
            _check(detail_file.is_file(), "local detail file missing on PASS")
            det = json.loads(detail_file.read_text(encoding="utf-8"))
            _check(det["fixed_inputs_verified"]["npz_files_count"] == 1, "expected 1 verified NPZ")
        finally:
            mod.np.load = orig_np_load
            mod._load_runtime_modules = orig_load_mods
            mod._atomic_write_text = orig_write

    # 4) ABORTED_MISSING_FUNDING run still writes full untruncated missing_funding_events_all (28 items)
    with tempfile.TemporaryDirectory() as td2:
        env2 = _make_e2e_synth_env(Path(td2), include_miss_events=True)
        rc_abort = mod.main([
            "--manifest", str(env2["manifest"]),
            "--retest24-script", str(env2["retest24"]),
            "--shared-risk", str(env2["shared_risk"]),
            "--cache-dir", str(env2["cache_dir"]),
            "--funding-db", str(env2["funding_db"]),
            "--out-dir", str(env2["out_dir"]),
            "--input-manifest", str(env2["input_manifest"]),
            "--candidate", "RETEST24_V1_5_FROZEN",
            "--symbols", "SYNTH-USDT-SWAP",
            "--start-utc", "2024-01-15T00:00:00Z",
            "--end-utc", "2024-02-15T00:00:00Z",
            "--scenarios", "R1_150U|cross_1tick",
        ])
        _check(rc_abort == 2, "expected rc=2 for ABORTED_MISSING_FUNDING")
        det2 = json.loads((env2["out_dir"] / "retest24_bounded_local_details.json").read_text(encoding="utf-8"))
        miss_all = det2["scenarios"]["R1_150U|cross_1tick"]["missing_funding_events_all"]
        _check(len(miss_all) == 28, "short ABORT local details must keep all 28 untruncated miss_8h events")


if __name__ == "__main__":
    test_old_vs_new_funding_db_regression()
    test_npz_manifest_and_disjoint_guard()
    test_b6_q38_cross_month_and_local_details()
    test_main_strict_manifest_disjoint_and_e2e_sentinels()
    print("ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS")
