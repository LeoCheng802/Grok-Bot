#!/usr/bin/env python3
"""
Pure synthetic in-memory unit tests for run_long_struct_bounded_backtest.py.
- Uses ZERO real market data, ZERO disk caches, ZERO network calls.
- Verifies:
  1) LONG_STRUCT_02 Timeline 1: k=6 confirmation + simultaneous Step C new event registration.
  2) LONG_STRUCT_02 Timeline 2: Close < L_ref early invalidation in Step A prevents Step B confirmation.
  3) LONG_STRUCT_03 strict long-limit (多單限價) causal anchor below Open_bt in uptrend pullback,
     and rejection in downtrend.
"""
import importlib.util
from pathlib import Path
import numpy as np

MOD_PATH = Path(__file__).resolve().parent / "run_long_struct_bounded_backtest.py"
spec = importlib.util.spec_from_file_location("run_long_struct_bounded_backtest", str(MOD_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

H1 = mod.H1
H4 = mod.H4
H8 = mod.H8
DAY = mod.DAY


def _make_d1_set(start_bt: int, num_days: int = 120):
    base_day = (start_bt + H8) // DAY * DAY - H8
    return {base_day - d * DAY for d in range(-30, num_days)}


def test_long_struct_02_timeline_1_k6_confirm_and_step_c_register():
    n_bars = 90
    t0 = 1_735_689_600_000
    ts4 = np.array([t0 + i * H4 for i in range(n_bars)], dtype=np.int64)
    o4 = np.zeros((n_bars, 4), dtype=np.float64)

    for i in range(70):
        px = 104.0 - 0.05 * i
        o4[i] = [px, px + 0.5, max(100.0, px - 0.5), px - 0.02]
    o4[60] = [101.0, 101.5, 100.0, 100.8]
    o4[70] = [100.2, 101.2, 99.2, 101.0]
    for j in range(71, 76):
        o4[j] = [100.5, 101.0, 100.1, 100.4]
    o4[76] = [103.0, 106.0, 98.8, 104.5]
    for j in range(77, n_bars):
        o4[j] = [105.0, 105.5, 104.5, 105.2]

    raw = {
        "SYN-USDT-SWAP": {
            "ts4": ts4, "o4": o4, "d1_set": _make_d1_set(int(ts4[77])),
            "tickSz_str": "0.1", "maxLever": 10.0,
        }
    }
    cands, _, diag = mod.build_cands_long_struct_02_temporal_split(
        raw, ["SYN-USDT-SWAP"], int(ts4[70]), int(ts4[-1])
    )
    bt_k6 = int(ts4[77])
    if bt_k6 not in cands or len(cands[bt_k6]) != 1:
        raise AssertionError(f"Expected exactly 1 candidate at k=6 ({bt_k6}), got {cands}, diag={diag}")
    _neg_dist, _pri, inst, px_f, _flag = cands[bt_k6][0]
    if inst != "SYN-USDT-SWAP" or abs(px_f - 100.0) > 1e-9:
        raise AssertionError(f"Expected limit price 100.0 at k=6, got {px_f}")
    if diag["events_registered"] < 2:
        raise AssertionError(f"Expected Step C to register new event at k=6, diag={diag}")


def test_long_struct_02_timeline_2_early_invalidation():
    n_bars = 90
    t0 = 1_735_689_600_000
    ts4 = np.array([t0 + i * H4 for i in range(n_bars)], dtype=np.int64)
    o4 = np.zeros((n_bars, 4), dtype=np.float64)
    for i in range(70):
        px = 104.0 - 0.05 * i
        o4[i] = [px, px + 0.5, max(100.0, px - 0.5), px - 0.02]
    o4[60] = [101.0, 101.5, 100.0, 100.8]
    o4[70] = [100.2, 101.2, 99.2, 101.0]
    o4[71] = [100.5, 101.0, 100.1, 100.4]
    o4[72] = [100.4, 100.5, 99.3, 99.5]
    for j in range(73, n_bars):
        o4[j] = [104.0, 106.0, 103.5, 105.5]

    raw = {
        "SYN-USDT-SWAP": {
            "ts4": ts4, "o4": o4, "d1_set": _make_d1_set(int(ts4[75])),
            "tickSz_str": "0.1", "maxLever": 10.0,
        }
    }
    cands, _, diag = mod.build_cands_long_struct_02_temporal_split(
        raw, ["SYN-USDT-SWAP"], int(ts4[70]), int(ts4[-1])
    )
    if diag["invalidated_close_below_L_ref"] < 1:
        raise AssertionError(f"Expected early invalidation, diag={diag}")
    if diag["signals"] != 0 or len(cands) != 0:
        raise AssertionError(f"Invalidated event must emit 0 signals, got {cands}, diag={diag}")


def test_long_struct_03_ema_pullback_limit_causal():
    n_bars = 230
    t0 = 1_735_689_600_000
    ts4 = np.array([t0 + i * H4 for i in range(n_bars)], dtype=np.int64)
    o4_up = np.zeros((n_bars, 4), dtype=np.float64)
    for i in range(215):
        px = 100.0 + 0.25 * i
        o4_up[i] = [px - 0.1, px + 0.6, px - 0.4, px]
    base = 100.0 + 0.25 * 214
    for k in range(8):
        px = base - 0.55 * (k + 1)
        o4_up[215 + k] = [px + 0.3, px + 0.5, px - 0.3, px]
    px_s = base - 0.55 * 8 + 0.4
    o4_up[223] = [px_s - 0.3, px_s + 0.4, px_s - 0.5, px_s + 0.2]
    for j in range(224, n_bars):
        o4_up[j] = [px_s + 0.2, px_s + 0.8, px_s - 0.2, px_s + 0.5]

    o4_dn = np.zeros((n_bars, 4), dtype=np.float64)
    for i in range(n_bars):
        px = 200.0 - 0.3 * i
        o4_dn[i] = [px + 0.1, px + 0.5, px - 0.5, px]

    raw = {
        "UP-USDT-SWAP": {
            "ts4": ts4, "o4": o4_up, "d1_set": _make_d1_set(int(ts4[224])),
            "tickSz_str": "0.01", "maxLever": 10.0,
        },
        "DN-USDT-SWAP": {
            "ts4": ts4, "o4": o4_dn, "d1_set": _make_d1_set(int(ts4[224])),
            "tickSz_str": "0.01", "maxLever": 10.0,
        },
    }
    cands, _, diag = mod.build_cands_long_struct_03_ema_pullback_limit(
        raw, ["UP-USDT-SWAP", "DN-USDT-SWAP"], int(ts4[220]), int(ts4[-1])
    )
    up_sigs = [c for lst in cands.values() for c in lst if c[2] == "UP-USDT-SWAP"]
    dn_sigs = [c for lst in cands.values() for c in lst if c[2] == "DN-USDT-SWAP"]
    if not up_sigs:
        raise AssertionError(f"Expected >=1 uptrend pullback limit signal, diag={diag}")
    if dn_sigs:
        raise AssertionError(f"Expected 0 downtrend signals, got {dn_sigs}")
    ts_to_i = {int(t): idx for idx, t in enumerate(ts4.tolist())}
    for bt, lst in cands.items():
        op_bt = float(o4_up[ts_to_i[bt], 0])
        for _neg_d, _pri, _inst, px_f, _flg in lst:
            if not (px_f < op_bt):
                raise AssertionError(f"Limit price {px_f} must be strictly < Open_bt {op_bt}")




def test_long_v1_3_funding_npz_and_b6_monthly_contract():
    import sqlite3, tempfile
    from datetime import datetime, timezone

    def _utc_ms(y, m, d, h=0):
        return int(datetime(y, m, d, h, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db_path = root / "synth_funding.sqlite"
        con = sqlite3.connect(str(db_path))
        try:
            con.execute("CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL)")
            con.execute("INSERT INTO funding_archive VALUES (?, ?, ?, ?)", ("SYNTH-USDT-SWAP", 1700006400000, 1700006400222, 0.00015))
            con.commit()
        finally:
            con.close()
        fmaps, ov_raw = mod.load_funding_db(db_path)
        if not isinstance(ov_raw["SYNTH-USDT-SWAP"], dict):
            raise RuntimeError("long load_funding_db ov_raw[inst] must be dict")
        if ov_raw["SYNTH-USDT-SWAP"].get(1700006400000, 1700006400000) != 1700006400222:
            raise RuntimeError("long load_funding_db ts_raw not preserved")
        if ov_raw["SYNTH-USDT-SWAP"].get(1700035200000, 1700035200000) != 1700035200000:
            raise RuntimeError("long load_funding_db miss fallback failed")

        npz_path = root / "SYNTH-USDT-SWAP.npz"
        np.savez(npz_path, ts30=np.array([1700006400000], dtype=np.int64), ohlc30=np.ones((1, 4)),
                 ts4=np.array([1700006400000], dtype=np.int64), ohlc4=np.ones((1, 4)),
                 ts1=np.array([1700006400000], dtype=np.int64), ohlc1=np.ones((1, 4)),
                 d1_ts=np.array([1700006400000], dtype=np.int64))
        good_sha = mod.sha(npz_path)
        resolved, recs = mod._verify_and_record_npz_inputs(
            ["SYNTH-USDT-SWAP"], root, {"SYNTH-USDT-SWAP": {}},
            {"SYNTH-USDT-SWAP": {"sha256": good_sha, "size_bytes": npz_path.stat().st_size}},
        )
        if not recs["SYNTH-USDT-SWAP"]["manifest_verified"]:
            raise RuntimeError("long NPZ manifest_verified expected True")
        overlap_blocked = False
        try:
            mod._verify_output_paths_disjoint([("bad", npz_path)], [("npz", resolved["SYNTH-USDT-SWAP"])])
        except RuntimeError:
            overlap_blocked = True
        if not overlap_blocked:
            raise RuntimeError("long NPZ disjoint guard failed")

    start_ts, end_ts = _utc_ms(2024, 1, 10), _utc_ms(2024, 4, 15)
    t_fill_jan, t_close_feb, t_open_apr = _utc_ms(2024, 1, 31, 16), _utc_ms(2024, 2, 3, 4), _utc_ms(2024, 4, 12, 8)
    events = {(0, "SYNTH-USDT-SWAP", _utc_ms(2024, 2, 1) + i * 28800000, "miss_8h") for i in range(28)}
    fake_res = {
        "_ord_log": [
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 1, 31, 12), "exp": _utc_ms(2024, 2, 2, 12), "px": 100.0, "outcome": "filled", "ets": t_fill_jan},
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 3, 5), "exp": _utc_ms(2024, 3, 7), "px": 99.0, "outcome": "expired", "ets": None},
            {"inst": "SYNTH-USDT-SWAP", "pts": _utc_ms(2024, 4, 12, 4), "exp": _utc_ms(2024, 4, 14, 4), "px": 95.0, "outcome": "filled", "ets": t_open_apr},
        ],
        "_trades": [
            {"inst": "SYNTH-USDT-SWAP", "side": "long", "ets": t_fill_jan, "xts": t_close_feb, "net": 85.0, "fund": -1.5, "fee": 2.0, "reason": "tp"},
        ],
        "_open": [{"inst": "SYNTH-USDT-SWAP", "ets": t_open_apr}],
        "_end_eq_raw": 50085.0,
        "mtm_mdd_pct": 0.35,
        "f_ev_real_8h": 2,
        "f_ev_real_non8h": 0,
        "f_ev_miss_8h": 28,
        "_real_fund_raw": -1.5,
        "events_set": events,
    }
    s = mod.summarize_run(fake_res, start_ts_ms=start_ts, end_ts_ms=end_ts)
    bym = s["by_year_month"]
    if not (bym["2024-01"]["unique_first_fills"] == 1 and bym["2024-01"]["closed_trades"] == 0):
        raise RuntimeError("long 2024-01 cross-month fill mismatch")
    if not (bym["2024-02"]["unique_first_fills"] == 0 and bym["2024-02"]["closed_trades"] == 1):
        raise RuntimeError("long 2024-02 cross-month close mismatch")
    if not (bym["2024-03"]["unique_first_fills"] == 0 and bym["2024-03"]["closed_trades"] == 0):
        raise RuntimeError("long 2024-03 zero-trade month mismatch")
    if not (bym["2024-04"]["unique_first_fills"] == 1 and bym["2024-04"]["closed_trades"] == 0):
        raise RuntimeError("long 2024-04 open-at-end mismatch")
    det = mod.build_local_detail_payload("cross_1tick", fake_res, start_ts_ms=start_ts, end_ts_ms=end_ts)
    if det["missing_funding_events_count"] != 28 or len(det["missing_funding_events_all"]) != 28:
        raise RuntimeError("long miss_8h truncated")



def _make_long_e2e_synth_env(root: Path, include_miss_events: bool = False):
    import json, sqlite3
    cache_dir = root / "cache"
    cache_dir.mkdir()
    out_dir = root / "out"
    code_dir = root / "code"
    code_dir.mkdir()

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
        '        "_trades": [{"inst": "SYNTH-USDT-SWAP", "side": "long", "ets": 1706702400000, "xts": 1706860800000, "net": 60.0, "fund": -0.5, "fee": 1.0, "reason": "tp"}],\n'
        '        "_open": [], "_end_eq_raw": 50060.0, "mtm_mdd_pct": 0.12,\n'
        '        "f_ev_real_8h": 1, "f_ev_real_non8h": 0, "f_ev_miss_8h": len(events), "_real_fund_raw": -0.5, "events_set": events,\n'
        '    }\n'
    )
    b6_path = code_dir / "b6_sim_portable.py"
    b6_path.write_text(b6_stub, encoding="utf-8")
    sr_path = code_dir / "shared_risk.py"
    sr_path.write_text("SHARED_RISK_STUB = True\n", encoding="utf-8")

    manifest_path = code_dir / "manifest.json"
    manifest_data = {
        "files": {
            "b6_sim_portable.py": {"sha256": mod.sha(b6_path), "size": b6_path.stat().st_size},
            "shared_risk.py": {"sha256": mod.sha(sr_path), "size": sr_path.stat().st_size},
        }
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    db_path = root / "funding.sqlite"
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL)")
        con.execute("INSERT INTO funding_archive VALUES (?, ?, ?, ?)", ("SYNTH-USDT-SWAP", 1706745600000, 1706745600111, 0.0001))
        con.commit()
    finally:
        con.close()

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
    (cache_dir / "manifest.json").write_text(
        json.dumps({"symbols": {"SYNTH-USDT-SWAP": {"spec": {"tickSz": "0.1", "maxLever": "20"}}}}),
        encoding="utf-8",
    )
    input_manifest_path = root / "input_manifest.json"
    input_manifest_path.write_text(
        json.dumps({"files": {"SYNTH-USDT-SWAP": {"sha256": mod.sha(npz_path), "size_bytes": npz_path.stat().st_size}}}),
        encoding="utf-8",
    )
    return {
        "manifest": manifest_path, "shared_risk": sr_path, "cache_dir": cache_dir,
        "funding_db": db_path, "out_dir": out_dir, "input_manifest": input_manifest_path, "npz_path": npz_path,
    }


def test_long_main_strict_manifest_disjoint_and_e2e_sentinels():
    import json, tempfile
    with tempfile.TemporaryDirectory() as td:
        env = _make_long_e2e_synth_env(Path(td), include_miss_events=False)
        base_argv = [
            "--manifest", str(env["manifest"]),
            "--shared-risk", str(env["shared_risk"]),
            "--cache-dir", str(env["cache_dir"]),
            "--funding-db", str(env["funding_db"]),
            "--out-dir", str(env["out_dir"]),
            "--candidate", "LONG_STRUCT_01_V1_2_FROZEN",
            "--symbols", "SYNTH-USDT-SWAP",
            "--start-utc", "2024-01-15T00:00:00Z",
            "--end-utc", "2024-02-15T00:00:00Z",
            "--scenarios", "cross_1tick",
        ]

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
            # 1) Reject unlisted NPZ (no --input-manifest, no sha256/size in cache manifest) BEFORE any load/write
            rejected_unlisted = False
            try:
                mod.main(base_argv)
            except RuntimeError:
                rejected_unlisted = True
            if not rejected_unlisted:
                raise RuntimeError("long main() must reject unlisted NPZ")
            if calls["np_load"] != 0 or calls["load_mods"] != 0 or calls["writes"]:
                raise RuntimeError("long unlisted rejection must happen before np.load, module load, and any write")

            # 2) Reject output colliding with NPZ (via symlink) BEFORE any write, leaving NPZ intact
            npz_sha_before = mod.sha(env["npz_path"])
            env["out_dir"].mkdir(parents=True, exist_ok=True)
            colliding_scope = env["out_dir"] / "long_struct_01_v1_2_frozen_bounded_scope.json"
            colliding_scope.symlink_to(env["npz_path"])
            rejected_collision = False
            try:
                mod.main(base_argv + ["--input-manifest", str(env["input_manifest"])])
            except RuntimeError:
                rejected_collision = True
            if not rejected_collision:
                raise RuntimeError("long main() must reject output colliding with NPZ")
            if calls["np_load"] != 0 or calls["load_mods"] != 0 or calls["writes"]:
                raise RuntimeError("long disjoint rejection must happen before any write or load")
            if mod.sha(env["npz_path"]) != npz_sha_before:
                raise RuntimeError("long colliding NPZ was modified")
            colliding_scope.unlink()

            # 3) Valid PASS run via main() wires --input-manifest and writes local details
            rc_pass = mod.main(base_argv + ["--input-manifest", str(env["input_manifest"])])
            if rc_pass != 0:
                raise RuntimeError("long main() PASS run expected rc=0")
            det_path = env["out_dir"] / "long_struct_01_v1_2_frozen_bounded_local_details.json"
            if not det_path.is_file():
                raise RuntimeError("long local detail file missing on PASS")
            det = json.loads(det_path.read_text(encoding="utf-8"))
            if det["fixed_inputs_verified"]["npz_files_count"] != 1:
                raise RuntimeError("long local details missing verified NPZ count")
        finally:
            mod.np.load = orig_np_load
            mod._load_runtime_modules = orig_load_mods
            mod._atomic_write_text = orig_write

    # 4) ABORTED_MISSING_FUNDING run still writes full untruncated missing_funding_events_all (28 items)
    with tempfile.TemporaryDirectory() as td2:
        env2 = _make_long_e2e_synth_env(Path(td2), include_miss_events=True)
        rc_abort = mod.main([
            "--manifest", str(env2["manifest"]),
            "--shared-risk", str(env2["shared_risk"]),
            "--cache-dir", str(env2["cache_dir"]),
            "--funding-db", str(env2["funding_db"]),
            "--out-dir", str(env2["out_dir"]),
            "--input-manifest", str(env2["input_manifest"]),
            "--candidate", "LONG_STRUCT_01_V1_2_FROZEN",
            "--symbols", "SYNTH-USDT-SWAP",
            "--start-utc", "2024-01-15T00:00:00Z",
            "--end-utc", "2024-02-15T00:00:00Z",
            "--scenarios", "cross_1tick",
        ])
        if rc_abort != 2:
            raise RuntimeError("long main() ABORT run expected rc=2")
        det2 = json.loads((env2["out_dir"] / "long_struct_01_v1_2_frozen_bounded_local_details.json").read_text(encoding="utf-8"))
        miss_all = det2["scenarios"]["cross_1tick"]["missing_funding_events_all"]
        if len(miss_all) != 28:
            raise RuntimeError("long ABORT local details must keep all 28 untruncated miss_8h events")


if __name__ == "__main__":
    test_long_struct_02_timeline_1_k6_confirm_and_step_c_register()
    test_long_struct_02_timeline_2_early_invalidation()
    test_long_struct_03_ema_pullback_limit_causal()
    test_long_v1_3_funding_npz_and_b6_monthly_contract()
    test_long_main_strict_manifest_disjoint_and_e2e_sentinels()
    print("ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS")
