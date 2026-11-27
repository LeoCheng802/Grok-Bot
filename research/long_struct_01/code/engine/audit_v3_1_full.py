import os
import json, math, time, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np

ROOT = Path(os.environ.get("OKX_RESEARCH_ROOT", Path(__file__).resolve().parent))
CACHE_V3 = ROOT / "cache_v3"
PUB_DIR = ROOT / "public_data"
OUT_ROOT = ROOT / "outputs"
TZ = timezone(timedelta(hours=8))
M30, H1, H4, H8, DAY = 1800000, 3600000, 14400000, 28800000, 86400000
MS_PER_YEAR = 365.25 * DAY

# Full real-funding coverage window: 2026-08-27 00:00 CST ~ 2026-11-26 20:00 CST
FUND_COV_START = 1787760000000  # 2026-08-27 00:00 CST
VIEWED_OOS_START = 1794686400000  # 2026-11-15 04:00 CST
FUND_COV_END = 1795694400000  # 2026-11-26 20:00 CST

def fmt_cst(ts_ms):
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(ts_ms / 1000.0, TZ).strftime("%Y-%m-%d %H:%M CST")

def indicators(c):
    n = len(c); ema = np.full(n, np.nan); rsi = np.full(n, np.nan)
    if n < 55: return ema, rsi
    k = 2.0 / 56.0; ema[54] = float(np.mean(c[:55]))
    for i in range(55, n): ema[i] = c[i] * k + ema[i - 1] * (1.0 - k)
    df = np.diff(c); g = float(np.mean(np.maximum(df[:14], 0.0))); lo = float(np.mean(np.maximum(-df[:14], 0.0)))
    rsi[14] = 100.0 * g / (g + lo) if (g + lo) else 50.0
    for i in range(14, n - 1):
        d = df[i]; g = (g * 13.0 + (d if d > 0 else 0.0)) / 14.0; lo = (lo * 13.0 + (-d if d < 0 else 0.0)) / 14.0
        rsi[i + 1] = 100.0 * g / (g + lo) if (g + lo) else 50.0
    return ema, rsi

def align_tick(px, t): return math.floor(px / t) * t if t > 0 else px

def load_all_data():
    m = json.loads((CACHE_V3 / "manifest.json").read_text(encoding="utf-8"))
    tiers_db = json.loads((PUB_DIR / "position_tiers.json").read_text(encoding="utf-8"))
    real_mmr_map = {k: float(v["tier1_mmr"]) for k, v in tiers_db.items()}
    raw = {}
    for inst, info in m["symbols"].items():
        z = np.load(CACHE_V3 / f"{inst}.npz")
        ts30, o30, ts1, o1, ts4, o4, d1_ts, fts, frt = (
            z["ts30"], z["ohlc30"], z["ts1"], z["ohlc1"],
            z["ts4"], z["ohlc4"], z["d1_ts"], z["fts"], z["frt"]
        )
        c4 = o4[:, 3]; ema, rsi = indicators(c4)
        raw[inst] = {
            "d30": ({int(t): j for j, t in enumerate(ts30.tolist())}, o30),
            "d1h": ({int(t): j for j, t in enumerate(ts1.tolist())}, o1),
            "ts4": ts4, "o4": o4, "ema": ema, "rsi": rsi,
            "d1_set": set(d1_ts.tolist()),
            "fmap": {int(t): float(r) for t, r in zip(fts.tolist(), frt.tolist())},
            "tickSz": float(info["spec"]["tickSz"]),
            "maxLever": float(info["spec"].get("maxLever", 10.0)),
        }
    all_30 = sorted({t for v in raw.values() for t in v["d30"][0]})
    return m, real_mmr_map, raw, all_30

def build_cands(raw, legs, lev_cfg):
    cands_by_bar = {}
    max_lev = {}
    for inst, v in raw.items():
        max_lev[inst] = min(lev_cfg, v["maxLever"])
        ts4, o4, ema, rsi, d1_set, tk = v["ts4"], v["o4"], v["ema"], v["rsi"], v["d1_set"], v["tickSz"]
        c4 = o4[:, 3]
        for li, lg in enumerate(legs):
            mode = lg["mode"]; side = "long" if mode == "fib_long" else "short"
            lb, rlo, rhi, lvl = int(lg["lookback"]), float(lg["rsi_lo"]), float(lg["rsi_hi"]), float(lg.get("entry_level", 0.0))
            for i in range(60, len(ts4)):
                bt = int(ts4[i])
                if int(ts4[i - 1]) != bt - H4: continue
                cp, ep, rp = float(c4[i - 1]), float(ema[i - 1]), float(rsi[i - 1])
                if math.isnan(ep) or math.isnan(rp): continue
                if side == "long" and (cp <= ep or not (rlo <= rp <= rhi)): continue
                if side == "short" and (cp >= ep or not (rlo <= rp <= rhi)): continue
                dk = (bt + H8) // DAY * DAY - H8
                if not all((dk - d * DAY) in d1_set for d in range(1, 61)): continue
                op = float(o4[i, 0]); wl = i - lb
                if wl < 0: continue
                hw, lw = max(op, float(np.max(o4[wl:i, 1]))), min(op, float(np.min(o4[wl:i, 2])))
                sw_lo = float(np.min(o4[wl:i, 2]))
                if mode == "fib_long":
                    raw_px = round(hw - (hw - lw) * lvl, 4); dist = (op - raw_px) / op; sk, trig = -dist, False
                elif mode in ("fib_short", "fib_short_1h_cancel"):
                    raw_px = round(lw + (hw - lw) * lvl, 4); dist = (raw_px - op) / op; sk, trig = -rp, False
                elif mode == "breakout_short":
                    raw_px = sw_lo * 0.9995; dist = (op - raw_px) / op; sk, trig = -rp, True
                elif mode == "breakout_retest_short":
                    if i - 1 - lb < 0: continue
                    pl = float(np.min(o4[i - 1 - lb:i - 1, 2]))
                    if not (cp < pl and op < pl): continue
                    raw_px = pl * 0.9995; dist = (raw_px - op) / op; sk, trig = -rp, False
                else: continue
                if not (0.0 <= dist <= 0.15): continue
                epx = align_tick(raw_px, tk)
                if epx <= 0: continue
                cands_by_bar.setdefault(bt, []).append((sk, li, inst, epx, trig))
    return cands_by_bar, max_lev

def run_sim(raw, all_30, spec, mmr_map=None, start_ts=None, end_ts=None, missing_fund_short_bps=0.0, track_liq_detail=False):
    legs = spec["legs"]
    init_cap = float(spec.get("initial_capital_u", 50000.0))
    lev_cfg = float(spec.get("leverage", 10.0))
    default_mmr = float(spec.get("mmr_approx", 0.01))
    mfee, tfee, slip = float(spec.get("maker_fee", 0.0002)), float(spec.get("taker_fee", 0.0005)), float(spec.get("slip_mkt", 0.0003))
    cands_by_bar, max_lev = build_cands(raw, legs, lev_cfg)

    bars = [t for t in all_30 if (start_ts is None or t >= start_ts) and (end_ts is None or t <= end_ts)]
    pend, pos, blk, dpnl, streak, pause_u = {}, {}, {}, {}, [0]*len(legs), [0]*len(legs)
    trades, last_c = [], {}
    real_eq = init_cap; mpk = init_cap; mdd_u = mdd_p = 0.0; halted = False
    halt_ts = None; liq_events = []
    post_halt_signals = 0; post_halt_orders = 0; post_halt_entries = 0
    min_margin_ratio = 9999.0
    st = {"signals_seen": 0, "orders_placed": 0, "cancelled_ttl": 0, "cancelled_1h": 0, "cancelled_margin": 0,
          "blocked_slots": 0, "blocked_daily": 0, "blocked_margin": 0, "same_bar_sl": 0, "liquidations": 0,
          "funding_events_real": 0, "funding_events_missing": 0, "halted_capital": False}
    real_fund_notional_sum = 0.0; real_fund_u_sum = 0.0

    def cur_px(inst, t30, fb):
        j = raw[inst]["d30"][0].get(t30)
        if j is not None: c = float(raw[inst]["d30"][1][j][3]); last_c[inst] = c; return c
        return last_c.get(inst, fb)
    def calc_flt(t30):
        return sum(p["not"] * ((cur_px(k[1], t30, p["ep"]) - p["ep"]) / p["ep"] if p["side"] == "long"
                               else (p["ep"] - cur_px(k[1], t30, p["ep"])) / p["ep"]) - p["ef"] for k, p in pos.items())

    for t30 in bars:
        # 1. Funding
        for (li, inst), p in pos.items():
            if t30 > p["ets"]:
                rt = raw[inst]["fmap"].get(t30)
                if rt is not None:
                    fp = (-p["not"] * rt) if p["side"] == "long" else (p["not"] * rt)
                    p["fund"] += fp; real_eq += fp; st["funding_events_real"] += 1
                    real_fund_u_sum += fp; real_fund_notional_sum += p["not"]
                elif t30 % H8 == 0:
                    st["funding_events_missing"] += 1; p["fmiss"] += 1
                    if missing_fund_short_bps != 0.0:
                        # missing_fund_short_bps: negative means short pays (e.g. -2.0 bps => -0.0002 * notional for short, +0.0002 for long)
                        rate_s = missing_fund_short_bps / 10000.0
                        fp = (p["not"] * rate_s) if p["side"] == "short" else (-p["not"] * rate_s)
                        p["fund_synth"] += fp; real_eq += fp

        # 2. Cross-margin liquidation check
        if pos:
            w_flt = 0.0; maint_req = 0.0
            for (li, inst), p in pos.items():
                j = raw[inst]["d30"][0].get(t30)
                if j is not None:
                    o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
                    wpx = float(l) if p["side"] == "long" else float(h)
                else:
                    wpx = last_c.get(inst, p["ep"])
                w_flt += p["not"] * ((wpx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - wpx) / p["ep"]) - p["ef"]
                im_mmr = mmr_map.get(inst, default_mmr) if mmr_map is not None else default_mmr
                maint_req += p["not"] * (im_mmr + tfee)
            if maint_req > 0:
                mr = (real_eq + w_flt) / maint_req
                if mr < min_margin_ratio: min_margin_ratio = mr
            if real_eq + w_flt <= maint_req:
                st["liquidations"] += 1
                eq_before = real_eq + w_flt
                pos_cnt = len(pos)
                pend_cnt = len(pend)
                for (li, inst), p in list(pos.items()):
                    j = raw[inst]["d30"][0].get(t30)
                    wpx = (float(raw[inst]["d30"][1][j][2]) if p["side"] == "long" else float(raw[inst]["d30"][1][j][1])) if j is not None else last_c.get(inst, p["ep"])
                    epx = wpx * (1.0 - slip if p["side"] == "long" else 1.0 + slip)
                    gr = p["not"] * ((epx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - epx) / p["ep"])
                    xf = p["not"] * (epx / p["ep"]) * tfee; net = gr - p["ef"] - xf + p["fund"] + p["fund_synth"]
                    real_eq += (gr - p["ef"] - xf)
                    trades.append({"entry_ts": p["ets"], "exit_ts": t30, "not": p["not"], "gross": gr, "fee": p["ef"] + xf,
                                   "fund": p["fund"], "fund_synth": p["fund_synth"], "fmiss": p["fmiss"], "net": net, "liq": 1})
                pos.clear(); pend.clear()
                real_eq = max(0.0, real_eq); halted = True; st["halted_capital"] = True
                if halt_ts is None: halt_ts = t30
                if track_liq_detail:
                    liq_events.append({
                        "event_ts": t30, "event_cst": fmt_cst(t30),
                        "positions_liquidated": pos_cnt, "pending_cleared": pend_cnt,
                        "mtm_equity_at_trigger_u": round(eq_before, 2),
                        "maint_req_u": round(maint_req, 2),
                        "post_liq_real_eq_u": round(real_eq, 2)
                    })

        # 3. Expire TTL
        for k in [k for k, od in pend.items() if t30 >= od["exp"]]: st["cancelled_ttl"] += 1; del pend[k]

        # 4. New 4H signals
        if halted and t30 % H4 == 0 and t30 in cands_by_bar:
            post_halt_signals += len(cands_by_bar[t30])
        if not halted and t30 % H4 == 0 and t30 in cands_by_bar:
            ud = t30 // DAY
            for _, li, inst, px, tr in sorted(cands_by_bar[t30], key=lambda x: x[0]):
                lg = legs[li]; side = "long" if lg["mode"] == "fib_long" else "short"
                st["signals_seen"] += 1
                if (li, inst) in pos or (li, inst) in pend or blk.get((li, inst), 0) > t30 or t30 < pause_u[li]: continue
                eq_now = real_eq + calc_flt(t30)
                dlim = (eq_now * float(lg["daily_loss_eq_pct"])) if lg.get("daily_loss_eq_pct") else float(lg["daily_loss_limit"])
                if dpnl.get((li, ud), 0.0) <= -dlim: st["blocked_daily"] += 1; continue
                used_slots = len({k[1] for k in pos if k[0] == li} | {k[1] for k in pend if k[0] == li})
                if used_slots >= int(lg["max_slots"]): st["blocked_slots"] += 1; continue
                rk = min(float(lg["risk_cap_u"]), max(0.0, eq_now) * float(lg["risk_eq_pct"])) if lg.get("risk_eq_pct") else float(lg["risk_per_trade"])
                nt = rk / float(lg["sl_pct"])
                req_im = nt / max_lev[inst]; est_fee = nt * (tfee if tr else mfee)
                used_im = sum(p["im"] for p in pos.values()) + sum(od["im"] for od in pend.values())
                if eq_now <= 0.0 or nt <= 0.0 or (eq_now - used_im) < (req_im + est_fee): st["blocked_margin"] += 1; continue
                pend[(li, inst)] = {"px": px, "pts": t30, "exp": t30 + int(float(lg["ttl_hours"]) * H1), "tr": tr, "not": nt, "im": req_im, "side": side}
                st["orders_placed"] += 1
                if halt_ts is not None and t30 >= halt_ts: post_halt_orders += 1

        # 5. Exits
        done = []
        for (li, inst), p in pos.items():
            j = raw[inst]["d30"][0].get(t30)
            if j is None: continue
            o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
            hsl = (l <= p["sl"]) if p["side"] == "long" else (h >= p["sl"])
            htp = (h >= p["tp"]) if p["side"] == "long" else (l <= p["tp"])
            if hsl or htp:
                epx = (p["sl"] if hsl else p["tp"]) * (1.0 - slip if p["side"] == "long" else 1.0 + slip)
                gr = p["not"] * ((epx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - epx) / p["ep"])
                xf = p["not"] * (epx / p["ep"]) * tfee; pnl_exf = gr - p["ef"] - xf; net = pnl_exf + p["fund"] + p["fund_synth"]
                ud = t30 // DAY; dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + net; real_eq += pnl_exf
                lg = legs[li]; lsl = int(lg.get("loss_streak_limit", 0))
                if net < 0:
                    streak[li] += 1
                    if lsl > 0 and streak[li] >= lsl: pause_u[li] = t30 + int(float(lg.get("loss_streak_pause_hours", 24)) * H1); streak[li] = 0
                else: streak[li] = 0
                trades.append({"entry_ts": p["ets"], "exit_ts": t30, "not": p["not"], "gross": gr, "fee": p["ef"] + xf,
                               "fund": p["fund"], "fund_synth": p["fund_synth"], "fmiss": p["fmiss"], "net": net, "liq": 0})
                done.append((li, inst))
        for k in done: del pos[k]

        # 6. Pending fills
        dp = []
        for (li, inst), od in pend.items():
            j = raw[inst]["d30"][0].get(t30)
            if j is None: continue
            o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
            fl, fpx = False, od["px"]; side = od["side"]
            if od["tr"]:
                if o <= od["px"]: fl, fpx = True, o * (1.0 - slip)
                elif l <= od["px"]: fl, fpx = True, od["px"] * (1.0 - slip)
            elif (side == "long" and l <= od["px"]) or (side == "short" and h >= od["px"]): fl = True
            if fl:
                eq_now = real_eq + calc_flt(t30); used_pos_im = sum(p["im"] for p in pos.values())
                if halted or eq_now <= 0.0 or (eq_now - used_pos_im) < od["im"]:
                    st["cancelled_margin"] += 1; dp.append((li, inst)); continue
                if halt_ts is not None and t30 >= halt_ts: post_halt_entries += 1
                lg = legs[li]; nt = od["not"]; ef = nt * (tfee if od["tr"] else mfee)
                tp_px = fpx * (1.0 + float(lg["tp_pct"]) if side == "long" else 1.0 - float(lg["tp_pct"]))
                sl_px = fpx * (1.0 - float(lg["sl_pct"]) if side == "long" else 1.0 + float(lg["sl_pct"]))
                if (l <= sl_px) if side == "long" else (h >= sl_px):
                    st["same_bar_sl"] += 1
                    epx = sl_px * (1.0 - slip if side == "long" else 1.0 + slip)
                    gr = nt * ((epx - fpx) / fpx if side == "long" else (fpx - epx) / fpx)
                    xf = nt * (epx / fpx) * tfee; pnl = gr - ef - xf
                    ud = t30 // DAY; dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl; real_eq += pnl
                    trades.append({"entry_ts": t30, "exit_ts": t30, "not": nt, "gross": gr, "fee": ef + xf,
                                   "fund": 0.0, "fund_synth": 0.0, "fmiss": 0, "net": pnl, "liq": 0})
                else:
                    pos[(li, inst)] = {"ep": fpx, "ets": t30, "not": nt, "im": od["im"], "ef": ef, "tp": tp_px, "sl": sl_px, "side": side, "fund": 0.0, "fund_synth": 0.0, "fmiss": 0}
                dp.append((li, inst))
        for k in dp: pend.pop(k, None)

        # 7. MTM equity & DD
        flt = calc_flt(t30); eq = max(0.0, real_eq + flt)
        mpk = max(mpk, eq); dd = mpk - eq
        mdd_u = max(mdd_u, dd); mdd_p = max(mdd_p, dd / mpk * 100.0 if mpk > 0 else 0.0)

        # 8. 1H cancel
        if (t30 + M30) % H1 == 0:
            hb = t30 - M30; d1 = []
            for (li, inst), od in pend.items():
                if not legs[li].get("use_1h_cancel", False) or od["side"] != "short" or od["pts"] > hb: continue
                j1 = raw[inst]["d1h"][0].get(hb)
                if j1 is None: continue
                o, h, l, c = raw[inst]["d1h"][1][j1]
                if c > o and h > l and (h - c) * 5.0 <= (h - l):
                    st["cancelled_1h"] += 1; blk[(li, inst)] = ((hb // H4) + 1) * H4; d1.append((li, inst))
            for k in d1: pend.pop(k, None)

    final_mtm_eq = max(0.0, real_eq + calc_flt(bars[-1])) if bars else init_cap
    first_tr_ts = min((t["entry_ts"] for t in trades), default=None)
    last_tr_ts = max((t["exit_ts"] for t in trades), default=None)
    # Use actual equity path span: from first trade entry (or window start if windowed) to window end
    span_start = start_ts if start_ts is not None else (first_tr_ts if first_tr_ts is not None else bars[0])
    span_end = end_ts if end_ts is not None else bars[-1]
    years_active = max((span_end - span_start) / MS_PER_YEAR, 1e-6)
    years_full_data = max((bars[-1] - bars[0]) / MS_PER_YEAR, 1e-6) if bars else 1.0

    # Compute CAGR on equity path (init_cap -> final_mtm_eq)
    def calc_cagr(end_eq, yrs):
        if end_eq <= 0.0:
            return -100.0
        return ((end_eq / init_cap) ** (1.0 / yrs) - 1.0) * 100.0

    cagr_active = calc_cagr(final_mtm_eq, years_active)
    cagr_data = calc_cagr(final_mtm_eq, years_full_data)

    ns = [x["net"] for x in trades]; ws = [x for x in ns if x > 0]; ls = [x for x in ns if x <= 0]
    tn = sum(ns); ret_trades = tn / init_cap * 100.0
    ret_eq = (final_mtm_eq - init_cap) / init_cap * 100.0
    fe_tot = st["funding_events_real"] + st["funding_events_missing"]
    cov_pct = round(100.0 * st["funding_events_real"] / fe_tot, 2) if fe_tot else 100.0
    emp_bps = (real_fund_u_sum / real_fund_notional_sum * 10000.0) if real_fund_notional_sum > 0 else 0.0

    out = {
        "trades": len(trades),
        "win_rate": round(100.0 * len(ws) / len(trades), 2) if trades else 0.0,
        "gross_u": round(sum(x["gross"] for x in trades), 2),
        "fee_u": round(sum(x["fee"] for x in trades), 2),
        "real_funding_u": round(sum(x["fund"] for x in trades), 2),
        "synth_funding_u": round(sum(x["fund_synth"] for x in trades), 2),
        "net_pnl_trades_u": round(tn, 2),
        "final_real_eq_u": round(real_eq, 2),
        "final_mtm_eq_u": round(final_mtm_eq, 2),
        "ret_trades_pct": round(ret_trades, 2),
        "ret_eq_pct": round(ret_eq, 2),
        "mtm_mdd_u": round(mdd_u, 2),
        "mtm_mdd_pct": round(mdd_p, 2),
        "cum_ret_over_mdd": round(ret_trades / mdd_p, 3) if mdd_p > 0 else 0.0,
        "span_start_cst": fmt_cst(span_start),
        "span_end_cst": fmt_cst(span_end),
        "first_trade_cst": fmt_cst(first_tr_ts),
        "last_trade_cst": fmt_cst(last_tr_ts),
        "years_active": round(years_active, 3),
        "years_full_data": round(years_full_data, 3),
        "cagr_active_pct": round(cagr_active, 2),
        "ann_calmar_active": round(cagr_active / mdd_p, 3) if mdd_p > 0 else 0.0,
        "cagr_full_data_pct": round(cagr_data, 2),
        "ann_calmar_full_data": round(cagr_data / mdd_p, 3) if mdd_p > 0 else 0.0,
        "pf": round((sum(ws) / abs(sum(ls))) if ls and sum(ls) else 0.0, 3),
        "liq_events_count": st["liquidations"],
        "liq_positions_count": int(sum(x["liq"] for x in trades)),
        "halted_capital": st["halted_capital"],
        "funding_coverage_pct": cov_pct,
        "funding_events_real": st["funding_events_real"],
        "funding_events_missing": st["funding_events_missing"],
        "emp_real_funding_bps_per_event": round(emp_bps, 3),
        "min_margin_ratio": round(min_margin_ratio, 2) if min_margin_ratio < 9999 else None,
        "blocked_margin": st["blocked_margin"],
        "cancelled_margin": st["cancelled_margin"],
    }
    if track_liq_detail:
        out["liq_detail"] = {
            "events": liq_events,
            "halt_ts_cst": fmt_cst(halt_ts),
            "post_halt_signals_ignored": post_halt_signals,
            "post_halt_orders_placed": post_halt_orders,
            "post_halt_entries": post_halt_entries,
            "post_halt_trades_after_halt_ts": sum(1 for t in trades if halt_ts is not None and t["entry_ts"] > halt_ts),
        }
    return out

def main():
    t0 = time.time()
    m, real_mmr_map, raw, all_30 = load_all_data()
    print(f"Loaded {len(raw)} symbols, {len(all_30)} 30m bars in {time.time()-t0:.1f}s")

    # 1. Audit Q23~Q33 (exact original specs & mmr_approx=0.01 to match Q23~Q33 + compute true CAGR / ann_calmar)
    q_dirs = sorted([d for d in OUT_ROOT.iterdir() if d.is_dir() and any(f"F4V3-Q{i}-" in d.name for i in range(23, 34))])
    q_audit = {}
    specs_by_q = {}
    for qd in q_dirs:
        qid = qd.name.split("-")[1]  # Q23..Q33
        orig = json.loads((qd / "result.json").read_text(encoding="utf-8"))
        spec = orig["spec"]
        specs_by_q[qid] = spec
        res = run_sim(raw, all_30, spec, mmr_map=None, track_liq_detail=(qid == "Q23"))
        res["orig_reported_calmar_field"] = orig["all"].get("calmar")
        res["orig_ret_pct"] = orig["all"].get("ret_pct")
        res["orig_mtm_mdd_pct"] = orig["all"].get("mtm_mdd_pct")
        res["name"] = qd.name
        q_audit[qid] = res
        print(f"{qid}: ret_tr={res['ret_trades_pct']}% mdd={res['mtm_mdd_pct']}% cum/mdd={res['cum_ret_over_mdd']} cagr_act={res['cagr_active_pct']}% ({res['years_active']}y) ann_calmar={res['ann_calmar_active']} liq_ev={res['liq_events_count']} liq_pos={res['liq_positions_count']}")

    # 2. Full-funding-coverage period same-condition comparison (R1=Q28, R2=Q29, R3=Q30) with REAL tier-1 MMR
    cov_compare = {}
    for label, qid in [("R1_12S_150U", "Q28"), ("R2_12S_100U", "Q29"), ("R3_12S_250U", "Q30")]:
        sp = specs_by_q[qid]
        full_cov = run_sim(raw, all_30, sp, mmr_map=real_mmr_map, start_ts=FUND_COV_START, end_ts=FUND_COV_END)
        pre_oos = run_sim(raw, all_30, sp, mmr_map=real_mmr_map, start_ts=FUND_COV_START, end_ts=VIEWED_OOS_START - M30)
        viewed_oos = run_sim(raw, all_30, sp, mmr_map=real_mmr_map, start_ts=VIEWED_OOS_START, end_ts=FUND_COV_END)
        cov_compare[label] = {
            "full_funding_window_20260827_1126": full_cov,
            "sub_pre_nov15_20260827_1115": pre_oos,
            "sub_viewed_oos_20261115_1126": viewed_oos,
        }
        print(f"COV {label}: tr={full_cov['trades']} cov={full_cov['funding_coverage_pct']}% fund={full_cov['real_funding_u']}U ({full_cov['emp_real_funding_bps_per_event']}bps/ev) net={full_cov['net_pnl_trades_u']}U ret={full_cov['ret_eq_pct']}% mdd={full_cov['mtm_mdd_pct']}% pf={full_cov['pf']} minMR={full_cov['min_margin_ratio']}x")

    # Empirical short funding bps/event from R1 full-funding window
    emp_bps_r1 = cov_compare["R1_12S_150U"]["full_funding_window_20260827_1126"]["emp_real_funding_bps_per_event"]

    # 3. Full-period funding sensitivity (R1, R2, R3) with REAL tier-1 MMR
    sens_levels = [
        ("0bps_partial_real_only", 0.0),
        (f"emp_{emp_bps_r1:+.2f}bps", emp_bps_r1),
        ("-1.0bps_per_8h", -1.0),
        ("-2.0bps_per_8h", -2.0),
        ("-3.0bps_per_8h", -3.0),
        ("-5.0bps_per_8h", -5.0),
    ]
    sensitivity = {}
    for label, qid in [("R1_12S_150U", "Q28"), ("R2_12S_100U", "Q29"), ("R3_12S_250U", "Q30")]:
        sp = specs_by_q[qid]
        sensitivity[label] = {}
        for sname, bps in sens_levels:
            r = run_sim(raw, all_30, sp, mmr_map=real_mmr_map, missing_fund_short_bps=bps)
            sensitivity[label][sname] = {
                "missing_bps_per_8h": bps,
                "trades": r["trades"],
                "real_funding_u": r["real_funding_u"],
                "synth_funding_u": r["synth_funding_u"],
                "net_pnl_u": r["net_pnl_trades_u"],
                "final_mtm_eq_u": r["final_mtm_eq_u"],
                "ret_eq_pct": r["ret_eq_pct"],
                "cagr_active_pct": r["cagr_active_pct"],
                "mtm_mdd_pct": r["mtm_mdd_pct"],
                "cum_ret_over_mdd": r["cum_ret_over_mdd"],
                "ann_calmar_active": r["ann_calmar_active"],
                "pf": r["pf"],
                "liq_events": r["liq_events_count"],
                "min_margin_ratio": r["min_margin_ratio"],
            }
            print(f"SENS {label} [{sname}]: net={r['net_pnl_trades_u']}U cagr={r['cagr_active_pct']}% mdd={r['mtm_mdd_pct']}% annCalmar={r['ann_calmar_active']} pf={r['pf']} liq={r['liq_events_count']}")

    # 4. Save OOS viewed registry
    oos_reg = {
        "registry_version": "v1.0",
        "updated_at_taipei": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S CST"),
        "consumed_viewed_windows": [
            {
                "id": "VIEWED_OOS_20261115_1126",
                "start_ts": VIEWED_OOS_START,
                "end_ts": FUND_COV_END,
                "start_cst": fmt_cst(VIEWED_OOS_START),
                "end_cst": fmt_cst(FUND_COV_END),
                "duration_days": round((FUND_COV_END - VIEWED_OOS_START) / DAY, 2),
                "status": "CONSUMED_VIEWED_DO_NOT_REUSE_AS_INDEPENDENT_OOS",
                "note": "Already inspected in Q22-Q34 and V3.1 audit; must not be claimed as untouched OOS after any further tuning."
            }
        ]
    }
    (ROOT / "oos_registry.json").write_text(json.dumps(oos_reg, ensure_ascii=False, indent=2), encoding="utf-8")

    out_dir = OUT_ROOT / "F4V3-Q22_Q34-AUDIT-V3_1"
    out_dir.mkdir(parents=True, exist_ok=True)
    full_res = {
        "audit_version": "v3.1-report-correction-and-funding-audit",
        "generated_at_taipei": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S CST"),
        "data_hash": m["data_hash"],
        "full_period_funding_incomplete_disclaimer": "OKX public funding-rate-history covers only ~9.0%~10.2% of 6-year 8h events (2021~2025H1 missing); full-period numbers are NOT complete real net PnL.",
        "q23_q33_cagr_calmar_correction": q_audit,
        "full_funding_coverage_comparison": cov_compare,
        "full_period_funding_sensitivity_real_mmr": sensitivity,
        "oos_registry": oos_reg,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    (out_dir / "result.json").write_text(json.dumps(full_res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE in {time.time()-t0:.1f}s -> {out_dir / 'result.json'}")

if __name__ == "__main__":
    main()
