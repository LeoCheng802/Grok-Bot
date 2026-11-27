"""Portable builder for run_audit_sim_b6 (identical patch logic to run_b6_timing.py L46-139, zero hardcoded paths)."""
import inspect, sys, textwrap
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import audit_v3_1_full as a
import run_q38_audit_01 as q38a

# Build patched run_audit_sim_b6 directly from frozen q38a.run_audit_sim source
_sim_src = textwrap.dedent(inspect.getsource(q38a.run_audit_sim))
_sig_old = 'def run_audit_sim(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False):'
_sig_new = 'def run_audit_sim_b6(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False, fill_mode="cross_1tick", delay_first_bar=False):'
assert _sim_src.count(_sig_old) == 1
_sim_src = _sim_src.replace(_sig_old, _sig_new, 1)

_init_old = '    trades, last_c = [], {}'
_init_new = '    trades, last_c = [], {}; _ord_log = []; _skip_fb_cross = 0; _same_bar_sl = 0'
assert _sim_src.count(_init_old) == 1
_sim_src = _sim_src.replace(_init_old, _init_new, 1)

_exp_old = '        for k in [k for k, od in pend.items() if t30 >= od["exp"]]: del pend[k]'
_exp_new = (
    '        for k in [k for k, od in pend.items() if t30 >= od["exp"]]:\n'
    '            od_x = pend[k]\n'
    '            _ord_log.append({"inst": k[1], "pts": od_x["pts"], "exp": od_x["exp"], "px": od_x["px"], '
    '"outcome": "expired", "ets": None, "first_bar_crossed": od_x.get("fb_cross", False), "ever_touched": False, "ever_crossed": False, "ever_subtick": False})\n'
    '            del pend[k]'
)
assert _sim_src.count(_exp_old) == 1
_sim_src = _sim_src.replace(_exp_old, _exp_new, 1)

_fill_old = '            elif (side == "long" and l <= od["px"]) or (side == "short" and h >= od["px"]): fl = True'
_fill_new = (
    '            else:\n'
    '                tk = raw[inst]["tickSz"]\n'
    '                if side == "long":\n'
    '                    crossed = (l <= od["px"] - tk * (1.0 - 1e-9))\n'
    '                    touched = (l <= od["px"])\n'
    '                else:\n'
    '                    crossed = (h >= od["px"] + tk * (1.0 - 1e-9))\n'
    '                    touched = (h >= od["px"])\n'
    '                if t30 == od["pts"] and crossed:\n'
    '                    od["fb_cross"] = True\n'
    '                    if delay_first_bar:\n'
    '                        _skip_fb_cross += 1\n'
    '                elig_bar = (t30 > od["pts"]) if delay_first_bar else True\n'
    '                if elig_bar:\n'
    '                    if fill_mode == "cross_1tick":\n'
    '                        if crossed: fl = True\n'
    '                    else:\n'
    '                        if touched: fl = True'
)
assert _sim_src.count(_fill_old) == 1
_sim_src = _sim_src.replace(_fill_old, _fill_new, 1)

_mrej_old = '                    dp.append((li, inst)); continue'
_mrej_new = (
    '                    _ord_log.append({"inst": inst, "pts": od["pts"], "exp": od["exp"], "px": od["px"], '
    '"outcome": "margin_rej", "ets": None, "first_bar_crossed": od.get("fb_cross", False), "ever_touched": False, "ever_crossed": False, "ever_subtick": False})\n'
    '                    dp.append((li, inst)); continue'
)
assert _sim_src.count(_mrej_old) == 1
_sim_src = _sim_src.replace(_mrej_old, _mrej_new, 1)

_sbsl_old = '                    trades.append({"inst": inst, "side": side, "ets": t30, "xts": t30, "net": pnl, "fund": 0.0, "fee": ef + xf, "reason": "same_bar_sl"})'
_sbsl_new = (
    '                    _same_bar_sl += 1\n'
    '                    trades.append({"inst": inst, "side": side, "ets": t30, "xts": t30, "net": pnl, "fund": 0.0, "fee": ef + xf, "reason": "same_bar_sl"})'
)
assert _sim_src.count(_sbsl_old) == 1
_sim_src = _sim_src.replace(_sbsl_old, _sbsl_new, 1)

_filled_old = '                dp.append((li, inst))\n        for k in dp:'
_filled_new = (
    '                _ord_log.append({"inst": inst, "pts": od["pts"], "exp": od["exp"], "px": od["px"], '
    '"outcome": "filled", "ets": t30, "filled_on_first_bar": (t30 == od["pts"]), "ever_touched": False, "ever_crossed": False, "ever_subtick": False, '
    '"first_bar_crossed": od.get("fb_cross", False)})\n'
    '                dp.append((li, inst))\n'
    '        for k in dp:'
)
assert _sim_src.count(_filled_old) == 1
_sim_src = _sim_src.replace(_filled_old, _filled_new, 1)

_ret_old = '    return out'
_ret_new = (
    '    for (li, inst), od_x in pend.items():\n'
    '        _ord_log.append({"inst": inst, "pts": od_x["pts"], "exp": od_x["exp"], "px": od_x["px"], '
    '"outcome": "pend_at_end", "ets": None, "first_bar_crossed": od_x.get("fb_cross", False), "ever_touched": False, "ever_crossed": False, "ever_subtick": False})\n'
    '    out["_ord_log"] = _ord_log\n'
    '    out["_skip_fb_cross"] = _skip_fb_cross\n'
    '    out["_same_bar_sl"] = _same_bar_sl\n'
    '    out["_last_bar"] = bars[-1] if bars else 0\n'
    '    out["_trades"] = trades\n'
    '    out["_open"] = [{"inst": k[1], "ets": p["ets"]} for k, p in pos.items()]\n    out["_end_eq_raw"] = end_eq\n    out["_real_fund_raw"] = real_fund_u\n'
    '    return out'
)
assert _sim_src.count(_ret_old) == 1
_sim_src = _sim_src.replace(_ret_old, _ret_new, 1)

_ns = dict(q38a.__dict__)
exec(compile(_sim_src, "<run_audit_sim_b6>", "exec"), _ns)
run_audit_sim_b6 = _ns["run_audit_sim_b6"]
