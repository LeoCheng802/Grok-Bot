#!/usr/bin/env python3
"""100% synthetic in-memory / temp-fixture regression tests for run_retest24_bounded_backtest.py (v1.3).

Zero real market data, zero network access, zero live/demo trading.
Covers:
1. Old-vs-new regression proof for load_funding_db (Q38 .get(t30, t30) AttributeError on old set shape vs fixed dict shape).
2. Non-real-market SQLite fixture with ts_raw > ts_snapped proving raw timestamp preservation, rate lookup, and miss fallback.
3. Per-file NPZ hash/size verification, fixed_inputs disjoint guard, and tamper rejection.
4. Untruncated local detail export (>25 missing funding events), by_year_month summary, first-fill IDs, and diff metadata.
"""
import importlib.util
import sqlite3
import sys
import tempfile
from pathlib import Path
import numpy as np

MOD_PATH = Path(__file__).resolve().parent / "run_retest24_bounded_backtest.py"
spec = importlib.util.spec_from_file_location("run_retest24_bounded_backtest", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + msg)


def _make_synth_funding_db(db_path: Path) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL)"
        )
        # Strictly synthetic timestamps where ts_raw > ts_snapped
        con.execute(
            "INSERT INTO funding_archive VALUES (?, ?, ?, ?)",
            ("SYNTH-USDT-SWAP", 1700006400000, 1700006400123, 0.000125),
        )
        con.execute(
            "INSERT INTO funding_archive VALUES (?, ?, ?, ?)",
            ("SYNTH-USDT-SWAP", 1700035200000, 1700035200456, -0.000250),
        )
        con.commit()
    finally:
        con.close()


def test_old_vs_new_funding_db_regression() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "synth_funding.sqlite"
        _make_synth_funding_db(db_path)

        # 1. Reproduce old bug (returning a set per inst causes AttributeError on Q38 .get(t30, t30))
        old_ov_raw = {"SYNTH-USDT-SWAP": {1700006400000, 1700035200000}}
        reproduced_attr_err = False
        try:
            _ = old_ov_raw.get("SYNTH-USDT-SWAP", {}).get(1700006400000, 1700006400000)
        except AttributeError:
            reproduced_attr_err = True
        _check(reproduced_attr_err, "Expected AttributeError on old set-based ov_raw shape")

        # 2. Verify fixed v1.3 load_funding_db (inst -> ts_snapped -> ts_raw)
        fmaps, ov_raw = mod.load_funding_db(db_path)
        _check("SYNTH-USDT-SWAP" in fmaps and "SYNTH-USDT-SWAP" in ov_raw, "SYNTH-USDT-SWAP missing")
        _check(isinstance(ov_raw["SYNTH-USDT-SWAP"], dict), "ov_raw[inst] must be dict, not set")

        ts_snap_1 = 1700006400000
        ts_raw_1 = 1700006400123
        ts_miss = 1700064000000

        # Rate lookup by ts_snapped
        _check(abs(fmaps["SYNTH-USDT-SWAP"][ts_snap_1] - 0.000125) < 1e-12, "rate lookup mismatch for ts_snap_1")
        _check(abs(fmaps["SYNTH-USDT-SWAP"][1700035200000] - (-0.000250)) < 1e-12, "rate lookup mismatch for ts_snap_2")

        # Q38 lookup path: preserves ts_raw > ts_snapped on hit, falls back to t30 on miss
        hit_raw = ov_raw.get("SYNTH-USDT-SWAP", {}).get(ts_snap_1, ts_snap_1)
        _check(hit_raw == ts_raw_1 and hit_raw > ts_snap_1, f"expected ts_raw {ts_raw_1} > {ts_snap_1}, got {hit_raw}")

        miss_fallback = ov_raw.get("SYNTH-USDT-SWAP", {}).get(ts_miss, ts_miss)
        _check(miss_fallback == ts_miss, f"expected miss fallback {ts_miss}, got {miss_fallback}")

        unseen_inst_fallback = ov_raw.get("OTHER-USDT-SWAP", {}).get(ts_snap_1, ts_snap_1)
        _check(unseen_inst_fallback == ts_snap_1, "unseen inst fallback failed")


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

        # Valid manifest passes
        resolved, recs = mod._verify_and_record_npz_inputs(
            ["SYNTH-USDT-SWAP"],
            root,
            {"SYNTH-USDT-SWAP": {}},
            {"SYNTH-USDT-SWAP": {"sha256": good_sha, "size_bytes": good_size}},
        )
        _check(resolved["SYNTH-USDT-SWAP"] == npz_path.resolve(), "resolved NPZ path mismatch")
        _check(recs["SYNTH-USDT-SWAP"]["manifest_verified"] is True, "manifest_verified should be True")

        # Tampered hash fails before np.load
        failed_bad_sha = False
        try:
            mod._verify_and_record_npz_inputs(
                ["SYNTH-USDT-SWAP"],
                root,
                {"SYNTH-USDT-SWAP": {}},
                {"SYNTH-USDT-SWAP": {"sha256": "0" * 64, "size_bytes": good_size}},
            )
        except RuntimeError:
            failed_bad_sha = True
        _check(failed_bad_sha, "bad NPZ sha256 must raise RuntimeError")

        # Disjoint guard rejects output overlapping NPZ
        failed_overlap = False
        try:
            mod._verify_output_paths_disjoint(
                [("evil_out", npz_path)],
                [("symbol npz SYNTH-USDT-SWAP", resolved["SYNTH-USDT-SWAP"])],
            )
        except RuntimeError:
            failed_overlap = True
        _check(failed_overlap, "output overlapping NPZ must be rejected")


def test_local_details_untruncated_and_diff_metadata() -> None:
    # 30 synthetic miss_8h events (>25) to prove local details are never truncated
    events = {(0, "SYNTH-USDT-SWAP", 1700006400000 + i * 28800000, "miss_8h") for i in range(30)}
    fake_res = {
        "_trades": [
            {"inst": "SYNTH-USDT-SWAP", "entry_ts": 1700006400000, "exit_ts": 1700035200000, "net": 120.5, "fee": -2.5, "fund": 1.2},
            {"inst": "SYNTH-USDT-SWAP", "entry_ts": 1702600000000, "exit_ts": 1702628800000, "net": -40.0, "fee": -2.0, "fund": -0.5},
        ],
        "_ord_log": [
            {"inst": "SYNTH-USDT-SWAP", "outcome": "filled", "order_ts": 1700004600000, "fill_ts": 1700006400000, "entry_px": 100.0},
            {"inst": "SYNTH-USDT-SWAP", "outcome": "expired", "order_ts": 1700040000000},
        ],
        "_open": [],
        "_end_eq_raw": 50080.5,
        "mtm_mdd_pct": 0.42,
        "f_ev_real_8h": 4,
        "f_ev_real_non8h": 0,
        "f_ev_miss_8h": 30,
        "_real_fund_raw": 0.7,
        "events_set": events,
    }
    summary = mod.summarize_run(fake_res)
    _check("2023-11" in summary["by_year_month"] and "2023-12" in summary["by_year_month"], "by_year_month missing expected months")

    details = mod.build_local_detail_payload("R1_150U|cross_1tick", fake_res)
    _check(details["missing_funding_events_count"] == 30, "expected 30 untruncated miss_8h events")
    _check(len(details["missing_funding_events_all"]) == 30, "missing_funding_events_all must not truncate at 25")
    _check(details["first_fills_count"] == 1, "expected 1 first fill")
    _check(len(details["closed_equity_curve"]) == 2, "expected 2 closed equity points")

    diff = mod.HISTORICAL_MODEL_VS_DELIVERED_SCRIPT_DIFF
    items = {d["item"] for d in diff["known_parameter_and_data_diffs"]}
    _check({"slip_mkt", "ema55_calculation_window", "default_universe_exclusions"}.issubset(items), "missing required diff items")


if __name__ == "__main__":
    test_old_vs_new_funding_db_regression()
    test_npz_manifest_and_disjoint_guard()
    test_local_details_untruncated_and_diff_metadata()
    print("ALL_RETEST24_V1_3_SYNTHETIC_TESTS_PASS")
