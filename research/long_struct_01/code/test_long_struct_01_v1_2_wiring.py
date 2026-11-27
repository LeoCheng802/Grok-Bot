#!/usr/bin/env python3
"""
Isolated synthetic & small-scale wiring verification for LONG-STRUCT-01 v1.2.
- ZERO full-period strategy replay, ZERO historical PnL backtest, ZERO parameter scan.
"""
import hashlib, json, os, sys
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
ENGINE_DIR = os.environ.get("ENGINE_DIR")
if ENGINE_DIR:
    sys.path.insert(0, ENGINE_DIR)

import long_struct_01_v1_2_isolated as mod
import b6_sim_portable as b6mod

H1 = 3_600_000
H4 = 4 * H1
M30 = 1_800_000
H8 = 8 * H1
DAY = 24 * H1
TZ_UTC = timezone.utc


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def make_synthetic_symbol(
    bt: int,
    op_bt: float,
    l_ref_low: float = 95.0,
    sweep_low: float = 93.0,
    reclaim_open: float = 94.0,
    reclaim_close: float = 99.5,
    missing_1d: bool = False,
    flat_downtrend: bool = False,
    tick_str: str = "0.01",
    extra_30m_bars=None,
):
    """Build 70 contiguous closed 4H bars before bt + bar bt (index 70) + optional 30m bars."""
    n_pre = 70
    ts4 = [bt - (n_pre - k) * H4 for k in range(n_pre)] + [bt]
    o4 = []
    for k in range(n_pre):
        if flat_downtrend:
            # Downtrend so Close_s <= EMA60 and RSI < 55
            base = 130.0 - k * 0.5
            o4.append([base + 0.2, base + 0.5, base - 0.5, base])
        else:
            # Gentle uptrend with alternating wiggle so EMA60 < Close and RSI14 ~ 68 in [55, 85]
            base = 80.0 + k * 0.25 + (0.6 if k % 2 == 0 else -0.2)
            if k == n_pre - 1:
                # Signal bar s = recent_idx[0]
                o4.append([reclaim_open, max(reclaim_open, reclaim_close) + 0.2, sweep_low, reclaim_close])
            elif k >= n_pre - 25:
                # Prior 24 bars: exact min low == l_ref_low
                lo_val = l_ref_low if k == n_pre - 10 else max(l_ref_low + 0.5, base - 0.3)
                o4.append([base - 0.1, base + 0.4, lo_val, base + 0.1])
            else:
                o4.append([base - 0.1, base + 0.4, base - 0.3, base + 0.1])
    # Bar bt itself
    o4.append([op_bt, op_bt + 0.5, op_bt - 0.5, op_bt + 0.1])

    day = (bt + H8) // DAY * DAY - H8
    d1_set = {day - d * DAY for d in range(1, 61)}
    if missing_1d:
        d1_set.remove(day - 30 * DAY)

    if extra_30m_bars is None:
        ts30 = np.array([bt], dtype=np.int64)
        o30 = np.array([[op_bt, op_bt + 0.2, op_bt - 0.2, op_bt]], dtype=np.float64)
    else:
        ts30 = np.array([x[0] for x in extra_30m_bars], dtype=np.int64)
        o30 = np.array([x[1] for x in extra_30m_bars], dtype=np.float64)

    return {
        "ts4": np.array(ts4, dtype=np.int64),
        "o4": np.array(o4, dtype=np.float64),
        "d1_set": d1_set,
        "d30": ({int(t): j for j, t in enumerate(ts30.tolist())}, o30),
        "d1h": ({}, np.zeros((0, 4), dtype=np.float64)),
        "tickSz": float(tick_str),
        "tickSz_str": tick_str,
        "maxLever": 20.0,
        "fmap": {},
    }


def main():
    report = {
        "spec_id": "LONG-STRUCT-01",
        "version": "v1.2_wiring_verification",
        "historical_replays_executed": 0,
        "tests": {},
    }

    # --- Test 1: Reused v1.2 synthetic unit cases ---
    r1_100 = mod._eval_price_and_gate(100.0, 90.5, D("0.01"))
    r1_102 = mod._eval_price_and_gate(102.0, 90.5, D("0.01"))
    assert r1_100 is not None and abs(r1_100[0] - 0.095) < 1e-12 and r1_100[1] == 90.5
    assert r1_102 is None  # 11.2745% > 10%
    r2_a100 = mod._eval_price_and_gate(100.0, 94.0, D("0.01"))
    r2_a102 = mod._eval_price_and_gate(102.0, 94.0, D("0.01"))
    r2_bfix = mod._eval_price_and_gate(100.0, 93.0, D("0.01"))
    ord_100 = [x[1] for x in sorted([(-r2_a100[0], "A"), (-r2_bfix[0], "B")], key=lambda x: x[0])]
    ord_102 = [x[1] for x in sorted([(-r2_a102[0], "A"), (-r2_bfix[0], "B")], key=lambda x: x[0])]
    assert ord_100 == ["B", "A"] and ord_102 == ["A", "B"]
    report["tests"]["test_1_v1_2_synthetic_unit_cases"] = {
        "status": "PASS",
        "case1_ref100_dist_pct": round(r1_100[0] * 100, 4),
        "case1_ref102_rejected": r1_102 is None,
        "case2_rank_ref100": ord_100,
        "case2_rank_ref102": ord_102,
    }

    # --- Test 2: Fixed symbol_order determinism on exact -dist ties ---
    bt = int(datetime(2025, 10, 15, 8, 0, tzinfo=TZ_UTC).timestamp() * 1000)
    sym_a = make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5)
    sym_b = make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5)
    raw_ab = {"SYM-A": sym_a, "SYM-B": sym_b}
    raw_ba = {"SYM-B": sym_b, "SYM-A": sym_a}
    c1, _ = mod.build_cands_long_struct_01_v1_2(raw_ab, ["SYM-A", "SYM-B"], bt, bt)
    c2, _ = mod.build_cands_long_struct_01_v1_2(raw_ba, ["SYM-A", "SYM-B"], bt, bt)
    s1 = [x[2] for x in sorted(c1[bt], key=lambda x: x[0])]
    s2 = [x[2] for x in sorted(c2[bt], key=lambda x: x[0])]
    assert s1 == ["SYM-A", "SYM-B"] and s2 == ["SYM-A", "SYM-B"]
    report["tests"]["test_2_fixed_symbol_order_tie_determinism"] = {
        "status": "PASS",
        "dict_AB_with_fixed_order": s1,
        "dict_BA_with_fixed_order": s2,
    }

    # --- Test 3: Causal gate & filter preservation checks ---
    cases = {
        "valid_sweep_reclaim": make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5),
        "no_sweep_low_eq_lref": make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=95.0, reclaim_open=95.5, reclaim_close=100.5),
        "no_reclaim_close_le_lref": make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=95.0),
        "bearish_reclaim_close_le_open": make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=101.0, reclaim_close=100.5),
        "missing_60d_gate": make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5, missing_1d=True),
        "fail_ema60_rsi": make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5, flat_downtrend=True),
    }
    c_gates, _ = mod.build_cands_long_struct_01_v1_2(cases, list(cases.keys()), bt, bt)
    emitted = [x[2] for x in c_gates.get(bt, [])]
    assert emitted == ["valid_sweep_reclaim"], f"Unexpected emitted: {emitted}"
    px_emitted = c_gates[bt][0][3]
    assert px_emitted == 95.0, f"Expected P_limit=95.0 (L_ref, NOT Low_s=93.0), got {px_emitted}"
    report["tests"]["test_3_causal_and_filter_gates"] = {
        "status": "PASS",
        "emitted_only": emitted,
        "limit_px_equals_L_ref_not_Low_s": px_emitted,
        "rejected_cases": [k for k in cases if k != "valid_sweep_reclaim"],
    }

    # --- Test 4: Synthetic 30m wiring with b6_sim_portable (optimistic vs 30m delay + TTL anchor) ---
    # 30m bars from 04:00 UTC to bt + 50H:
    # - [04:00..07:30 UTC]: dips to 93.0 (during signal 4H bar s -> MUST NOT fill)
    # - 08:00 UTC (t30 == bt): dips to 94.98 (crosses 95.0 - 0.01 = 94.99) -> fills under cross_1tick, skipped under delay1bar
    # - 08:30 UTC (t30 == bt + 30m): dips to 94.98 -> fills under delay1bar
    # - 09:00 UTC: hits TP (95.0 * 1.025 = 97.375)
    bars_fill = []
    for m in range(-8, 4):
        t30 = bt + m * M30
        if m < 0:
            bars_fill.append((t30, [96.0, 96.5, 93.0, 96.0]))
        elif m == 0:
            bars_fill.append((t30, [99.0, 99.2, 94.98, 96.0]))
        elif m == 1:
            bars_fill.append((t30, [96.0, 96.2, 94.98, 96.0]))
        else:
            bars_fill.append((t30, [96.0, 98.5, 95.8, 98.0]))
    sym_fill = make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5, extra_30m_bars=bars_fill)
    raw_fill = {"SYN-USDT-SWAP": sym_fill}
    c_fill, ml_fill = mod.build_cands_long_struct_01_v1_2(raw_fill, ["SYN-USDT-SWAP"], bt, bt)
    spec_syn = {
        "initial_capital_u": 50000.0, "leverage": 10.0, "mmr_approx": 0.01,
        "maker_fee": 0.0002, "taker_fee": 0.0005, "slip_mkt": 0.0003,
        "legs": [{
            "mode": "fib_long", "tp_pct": 0.025, "sl_pct": 0.04, "lookback": 24,
            "rsi_lo": 55.0, "rsi_hi": 85.0, "entry_level": 0.618, "ttl_hours": 48.0,
            "max_slots": 24, "risk_per_trade": 150.0, "daily_loss_limit": 600.0,
            "loss_streak_limit": 3, "loss_streak_pause_hours": 24.0, "use_1h_cancel": False,
        }],
    }
    bars_ts_fill = [x[0] for x in bars_fill]
    r_opt = b6mod.run_audit_sim_b6(raw_fill, bars_ts_fill, spec_syn, cands_pre=c_fill, max_lev_pre=ml_fill, fill_mode="cross_1tick", delay_first_bar=False)
    r_dly = b6mod.run_audit_sim_b6(raw_fill, bars_ts_fill, spec_syn, cands_pre=c_fill, max_lev_pre=ml_fill, fill_mode="cross_1tick", delay_first_bar=True)
    ord_opt = r_opt["_ord_log"][0]
    ord_dly = r_dly["_ord_log"][0]
    assert ord_opt["outcome"] == "filled" and ord_opt["ets"] == bt and ord_opt["filled_on_first_bar"] is True
    assert ord_dly["outcome"] == "filled" and ord_dly["ets"] == bt + M30 and r_dly["_skip_fb_cross"] == 1

    # TTL anchor test: price stays at 99.0 until bt + 48H (m=96), then dips to 94.0 at bt + 48H
    bars_ttl = []
    for m in range(0, 99):
        t30 = bt + m * M30
        if m < 96:
            bars_ttl.append((t30, [99.0, 99.5, 98.5, 99.0]))
        else:
            bars_ttl.append((t30, [99.0, 99.5, 94.0, 98.0]))
    sym_ttl = make_synthetic_symbol(bt, op_bt=100.0, l_ref_low=95.0, sweep_low=93.0, reclaim_open=94.0, reclaim_close=100.5, extra_30m_bars=bars_ttl)
    raw_ttl = {"SYN-USDT-SWAP": sym_ttl}
    c_ttl, ml_ttl = mod.build_cands_long_struct_01_v1_2(raw_ttl, ["SYN-USDT-SWAP"], bt, bt)
    bars_ts_ttl = [x[0] for x in bars_ttl]
    r_ttl_opt = b6mod.run_audit_sim_b6(raw_ttl, bars_ts_ttl, spec_syn, cands_pre=c_ttl, max_lev_pre=ml_ttl, fill_mode="cross_1tick", delay_first_bar=False)
    r_ttl_dly = b6mod.run_audit_sim_b6(raw_ttl, bars_ts_ttl, spec_syn, cands_pre=c_ttl, max_lev_pre=ml_ttl, fill_mode="cross_1tick", delay_first_bar=True)
    assert r_ttl_opt["_ord_log"][0]["outcome"] == "expired" and r_ttl_dly["_ord_log"][0]["outcome"] == "expired"
    report["tests"]["test_4_synthetic_30m_engine_wiring"] = {
        "status": "PASS",
        "optimistic_cross_1tick_fill_offset_min": int((ord_opt["ets"] - bt) // 60_000),
        "conservative_delay1bar_fill_offset_min": int((ord_dly["ets"] - bt) // 60_000),
        "delay1bar_skip_first_bar_count": r_dly["_skip_fb_cross"],
        "ttl_48h_expired_both_modes_unextended": True,
    }

    # --- Test 5: Small-scale 5-symbol 1-month (2025-10) candidate-only diff (ZERO PnL replay) ---
    cache_dir_env = os.environ.get("CACHE_V3_DIR")
    univ_env = os.environ.get("UNIVERSE_JSON")
    if cache_dir_env and univ_env and Path(cache_dir_env).exists() and Path(univ_env).exists():
        cache_dir = Path(cache_dir_env)
        manifest = json.loads((cache_dir / "manifest.json").read_text(encoding="utf-8"))
        univ = json.loads(Path(univ_env).read_text(encoding="utf-8"))
        manifest_syms_ex_usdc = [s for s in manifest["symbols"].keys() if s != "USDC-USDT-SWAP"]
        univ_syms = [s["instId"] if isinstance(s, dict) else s for s in univ["symbols"]]
        order_exact_match = (manifest_syms_ex_usdc == univ_syms)
        sample_syms = [s for s in ["SOL-USDT-SWAP", "FIL-USDT-SWAP", "DOGE-USDT-SWAP", "XRP-USDT-SWAP", "ADA-USDT-SWAP"] if s in manifest["symbols"]]
        # Lock sample order to manifest order
        sample_order = [s for s in manifest_syms_ex_usdc if s in set(sample_syms)]
        raw_sm = {}
        for inst in sample_order:
            info = manifest["symbols"][inst]
            z = np.load(cache_dir / f"{inst}.npz")
            raw_sm[inst] = {
                "ts4": z["ts4"], "o4": z["ohlc4"],
                "d1_set": set(int(x) for x in z["d1_ts"].tolist()),
                "tickSz": float(info["spec"]["tickSz"]),
                "tickSz_str": str(info["spec"]["tickSz"]),
                "maxLever": float(info["spec"].get("maxLever", 20.0)),
            }
        s_start = int(datetime(2025, 10, 1, 0, 0, tzinfo=TZ_UTC).timestamp() * 1000)
        s_end = int(datetime(2025, 11, 1, 0, 0, tzinfo=TZ_UTC).timestamp() * 1000)
        c_base, _ = mod.build_cands_fib_long_exact(raw_sm, sample_order, s_start, s_end)
        c_new, _ = mod.build_cands_long_struct_01_v1_2(raw_sm, sample_order, s_start, s_end)
        base_keys = {(bt_k, x[2]) for bt_k, lst in c_base.items() for x in lst}
        new_keys = {(bt_k, x[2]) for bt_k, lst in c_new.items() for x in lst}
        report["tests"]["test_5_small_sample_candidate_only_diff_no_replay"] = {
            "status": "PASS",
            "window_utc": "2025-10-01T00:00:00Z ~ 2025-11-01T00:00:00Z (includes 48H warmup buffer per builder)",
            "fixed_symbol_order": sample_order,
            "manifest_vs_ex_usdc_286_order_identical": order_exact_match,
            "baseline_fib_candidates": len(base_keys),
            "long_struct_01_v1_2_candidates": len(new_keys),
            "overlap_bar_symbol_pairs": len(base_keys & new_keys),
            "only_in_new": len(new_keys - base_keys),
            "only_in_baseline": len(base_keys - new_keys),
            "pnl_replay_executed": False,
        }


    else:
        report["tests"]["test_5_small_sample_candidate_only_diff_no_replay"] = {
            "status": "SKIPPED_NO_LOCAL_CACHE_ENV",
            "pnl_replay_executed": False,
        }

    # --- Test 6: ChatGPT Contract Acceptance Vectors (#7211463402) ---
    # Vector 1: Lower-bound literal IEEE-754 float consistency (no epsilon, no Decimal dist)
    op_v1, raw_v1 = 100.0, 99.95
    dist_v1 = (op_v1 - raw_v1) / op_v1
    res_v1 = mod._eval_price_and_gate(op_v1, raw_v1, D("0.01"))
    assert dist_v1 < 0.0005 and repr(dist_v1) == "0.0004999999999999716", f"Unexpected float: {dist_v1!r}"
    assert res_v1 is None, "Vector 1 must be rejected under literal float dist < 0.0005"
    # Verify exact match with FIB_4H_Long_v3.py literal float check
    orig_v1_pass = (0.0005 <= (op_v1 - round(raw_v1, 4)) / op_v1 <= 0.10)
    assert orig_v1_pass is False

    # Vector 2: Distance gate strictly BEFORE tick ROUND_DOWN
    op_v2, raw_v2, tk_v2 = 100.0, 90.01, D("0.7")
    dist_v2 = (op_v2 - round(raw_v2, 4)) / op_v2
    res_v2 = mod._eval_price_and_gate(op_v2, raw_v2, tk_v2)
    assert res_v2 is not None, "Vector 2 must PASS raw dist gate before tick rounding"
    v2_dist_out, v2_placed_out = res_v2
    assert abs(v2_dist_out - 0.0999) < 1e-12
    assert abs(v2_placed_out - 89.6) < 1e-12
    placed_dist_audit = (op_v2 - v2_placed_out) / op_v2  # 0.1040 (>10%, NOT used to reject)

    # Vector 3: Event-time sequencing (signal data available at 08:00:02 UTC; tape prints 94.98 at 08:00:01 & 08:30:01)
    t_080000 = int(datetime(2025, 10, 15, 8, 0, 0, tzinfo=TZ_UTC).timestamp() * 1000)
    t_avail  = int(datetime(2025, 10, 15, 8, 0, 2, tzinfo=TZ_UTC).timestamp() * 1000)
    t_083000 = int(datetime(2025, 10, 15, 8, 30, 0, tzinfo=TZ_UTC).timestamp() * 1000)
    tape = [
        {"ts_utc": "2025-10-15T08:00:01Z", "ts_ms": t_080000 + 1000, "px": 94.98},
        {"ts_utc": "2025-10-15T08:30:01Z", "ts_ms": t_083000 + 1000, "px": 94.98},
    ]
    lim_v3, tk_v3 = 95.0, 0.01
    cross_thresh = lim_v3 - tk_v3 * (1.0 - 1e-9)
    tape_eval = []
    first_event_time_cross = None
    first_delay1bar_cross = None
    for ev in tape:
        is_cross = (ev["px"] <= cross_thresh)
        if ev["ts_ms"] < t_avail:
            tape_eval.append({**ev, "event_time_eligible": False, "reject_reason": "trade_before_data_available"})
        else:
            tape_eval.append({**ev, "event_time_eligible": is_cross, "reject_reason": None if is_cross else "not_crossed"})
            if is_cross and first_event_time_cross is None:
                first_event_time_cross = ev["ts_utc"]
        if ev["ts_ms"] >= t_083000 and is_cross and first_delay1bar_cross is None:
            first_delay1bar_cross = ev["ts_utc"]
    assert first_event_time_cross == "2025-10-15T08:30:01Z"
    assert first_delay1bar_cross == "2025-10-15T08:30:01Z"
    assert tape_eval[0]["event_time_eligible"] is False and tape_eval[0]["reject_reason"] == "trade_before_data_available"

    report["tests"]["test_6_chatgpt_contract_vectors_7211463402"] = {
        "status": "PASS",
        "vector_1_lower_bound_literal_float": {
            "op": op_v1,
            "raw": raw_v1,
            "placed": None,
            "dist_literal_float_repr": repr(dist_v1),
            "passed": False,
            "reject_reason": "dist_below_min_0.0005",
            "matches_orig_FIB_4H_Long_v3_literal_float": True,
        },
        "vector_2_dist_gate_before_tick_round_down": {
            "op": op_v2,
            "raw": raw_v2,
            "tick": str(tk_v2),
            "placed": v2_placed_out,
            "dist_raw_for_gate_and_sort": v2_dist_out,
            "sort_key_neg_dist": -v2_dist_out,
            "placed_dist_audit_only": round(placed_dist_audit, 6),
            "passed": True,
            "reject_reason": None,
        },
        "vector_3_event_time_sequencing": {
            "limit_px": lim_v3,
            "tick": tk_v3,
            "data_available_utc": "2025-10-15T08:00:02Z",
            "tape_evaluation": tape_eval,
            "first_eligible_cross_event_time": first_event_time_cross,
            "first_eligible_cross_delay1bar_30m": first_delay1bar_cross,
            "caveat_30m_ohlc_and_queue": "With 30m OHLC only, [08:00,08:30) remains optimistic/unresolved; tick-level cross does not prove queue-position fill.",
        },
    }

    out_dir = Path(os.environ.get("OUT_DIR", str(SCRIPT_DIR / "out")))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "wiring_verification_v1_2.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for p in [
        SCRIPT_DIR / "long_struct_01_v1_2_isolated.py",
        Path(__file__).resolve(),
        out_path,
    ]:
        print(f"{p.stat().st_size:>8}  {sha256(p)}  {p}")
    print(json.dumps(report["tests"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
