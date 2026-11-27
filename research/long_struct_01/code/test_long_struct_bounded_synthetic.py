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


if __name__ == "__main__":
    test_long_struct_02_timeline_1_k6_confirm_and_step_c_register()
    test_long_struct_02_timeline_2_early_invalidation()
    test_long_struct_03_ema_pullback_limit_causal()
    print("ALL_SYNTHETIC_TESTS_PASS")
