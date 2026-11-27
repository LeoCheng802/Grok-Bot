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


if __name__ == "__main__":
    test_old_vs_new_funding_db_regression()
    test_npz_manifest_and_disjoint_guard()
    test_b6_q38_cross_month_and_local_details()
    print("ALL_RETEST24_V1_3_SYNTHETIC_TESTS_PASS")
