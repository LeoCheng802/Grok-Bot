import math
from datetime import datetime, timezone, timedelta

M30, H1, H4, H8, DAY = 1800000, 3600000, 14400000, 28800000, 86400000
MS_PER_YEAR = 365.25 * DAY

def run_v3_2_sl_fix(raw, all_30, spec, mmr_map=None, start_ts=None, end_ts=None, cands_pre=None, max_lev_pre=None):
    """
    Independent fixed copy of sim_50k_v3 (keeps original F4V3 ledger, UTC daily-loss, fees, slippage).
    Fix vs sim_50k_v3:
      1) Evaluate Stop-Loss / Take-Profit exits BEFORE checking bar-extreme liquidation on remaining open positions,
         so positions that already crossed SL are NOT held to the 30m wick low for unrealized loss.
      2) Handle gap past SL at bar open: if long open <= sl (or short open >= sl), fill at open*(1-/+slip)
         instead of idealized sl.
      3) Track `ambiguous_sl_liq_bars`: bars where an SL-triggered position's 30m wick low would have breached
         maintenance margin if SL had not filled, surfacing intra-bar path uncertainty instead of silently
         declaring exact liquidation.
    """
    import audit_v3_1_full as a
    legs = spec["legs"]
    init_cap = float(spec.get("initial_capital_u", 50000.0))
    lev_cfg = float(spec.get("leverage", 10.0))
    default_mmr = float(spec.get("mmr_approx", 0.01))
    mfee = float(spec.get("maker_fee", 0.0002))
    tfee = float(spec.get("taker_fee", 0.0005))
    slip = float(spec.get("slip_mkt", 0.0003))
    if cands_pre is None or max_lev_pre is None:
        cands_by_bar, max_lev = a.build_cands(raw, legs, lev_cfg)
    else:
        cands_by_bar, max_lev = cands_pre, max_lev_pre

    bars = [t for t in all_30 if (start_ts is None or t >= start_ts) and (end_ts is None or t <= end_ts)]
    pend, pos, blk, dpnl, streak, pause_u = {}, {}, {}, {}, [0]*len(legs), [0]*len(legs)
    trades, last_c = [], {}
    real_eq = init_cap; mpk = init_cap; mdd_u = mdd_p = 0.0; halted = False
    liq_events = 0; liq_positions = 0; ambiguous_sl_liq_bars = []
    gap_sl_fills = 0

    def cur_px(inst, t30, fb):
        j = raw[inst]["d30"][0].get(t30)
        if j is not None:
            c = float(raw[inst]["d30"][1][j][3]); last_c[inst] = c; return c
        return last_c.get(inst, fb)

    def calc_flt(t30):
        tot = 0.0
        for (li, inst), p in pos.items():
            px = cur_px(inst, t30, p["ep"])
            tot += p["not"] * ((px - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - px) / p["ep"]) - p["ef"]
        return tot

    for t30 in bars:
        # 1. Funding
        for (li, inst), p in pos.items():
            if t30 > p["ets"]:
                rt = raw[inst]["fmap"].get(t30)
                if rt is not None:
                    fp = (-p["not"] * rt) if p["side"] == "long" else (p["not"] * rt)
                    p["fund"] += fp; real_eq += fp

        # 2. Expire TTL (exact sim_50k_v3 order)
        for k in [k for k, od in pend.items() if t30 >= od["exp"]]: del pend[k]

        # 3. Signals (exact sim_50k_v3 order)
        if not halted and t30 % H4 == 0 and t30 in cands_by_bar:
            ud = t30 // DAY
            for _, li, inst, px, tr in sorted(cands_by_bar[t30], key=lambda x: x[0]):
                lg = legs[li]; side = "long" if lg["mode"] == "fib_long" else "short"
                if (li, inst) in pos or (li, inst) in pend or blk.get((li, inst), 0) > t30 or t30 < pause_u[li]: continue
                eq_now = real_eq + calc_flt(t30)
                dlim = (eq_now * float(lg["daily_loss_eq_pct"])) if lg.get("daily_loss_eq_pct") else float(lg["daily_loss_limit"])
                if dpnl.get((li, ud), 0.0) <= -dlim: continue
                used_slots = len({k[1] for k in pos if k[0] == li} | {k[1] for k in pend if k[0] == li})
                if used_slots >= int(lg["max_slots"]): continue
                rk = min(float(lg["risk_cap_u"]), max(0.0, eq_now) * float(lg["risk_eq_pct"])) if lg.get("risk_eq_pct") else float(lg["risk_per_trade"])
                nt = rk / float(lg["sl_pct"])
                req_im = nt / max_lev[inst]; est_fee = nt * (tfee if tr else mfee)
                used_im = sum(p["im"] for p in pos.values()) + sum(od["im"] for od in pend.values())
                if eq_now <= 0.0 or nt <= 0.0 or (eq_now - used_im) < (req_im + est_fee): continue
                pend[(li, inst)] = {"px": px, "pts": t30, "exp": t30 + int(float(lg["ttl_hours"]) * H1), "tr": tr, "not": nt, "im": req_im, "side": side}

        # 4a. Intra-bar ambiguity diagnostic BEFORE SL exits
        if pos and not halted:
            w_flt_all = 0.0; maint_all = 0.0; any_sl_bar = False
            for (li, inst), p in pos.items():
                j = raw[inst]["d30"][0].get(t30)
                if j is not None:
                    o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
                    wpx = float(l) if p["side"] == "long" else float(h)
                    if (p["side"] == "long" and float(l) <= p["sl"]) or (p["side"] == "short" and float(h) >= p["sl"]):
                        any_sl_bar = True
                else:
                    wpx = last_c.get(inst, p["ep"])
                w_flt_all += p["not"] * ((wpx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - wpx) / p["ep"]) - p["ef"]
                im_mmr = mmr_map.get(inst, default_mmr) if mmr_map is not None else default_mmr
                maint_all += p["not"] * (im_mmr + tfee)
            would_liq_if_no_sl = (real_eq + w_flt_all <= maint_all)
        else:
            any_sl_bar = False; would_liq_if_no_sl = False

        # 4b. Process Stop-Loss & Take-Profit exits BEFORE liquidation (with gap-past-SL check at bar open)
        done = []
        sl_exited_this_bar = 0
        for (li, inst), p in pos.items():
            j = raw[inst]["d30"][0].get(t30)
            if j is None: continue
            o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
            o, h, l, c = float(o), float(h), float(l), float(c)
            hsl = (l <= p["sl"]) if p["side"] == "long" else (h >= p["sl"])
            htp = (h >= p["tp"]) if p["side"] == "long" else (l <= p["tp"])
            if hsl or htp:
                if hsl:
                    sl_exited_this_bar += 1
                    if (p["side"] == "long" and o <= p["sl"]) or (p["side"] == "short" and o >= p["sl"]):
                        base_px = o; gap_sl_fills += 1; reason = "sl_gap"
                    else:
                        base_px = p["sl"]; reason = "sl"
                else:
                    base_px = p["tp"]; reason = "tp"
                epx = base_px * (1.0 - slip if p["side"] == "long" else 1.0 + slip)
                gr = p["not"] * ((epx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - epx) / p["ep"])
                xf = p["not"] * (epx / p["ep"]) * tfee
                pnl_exf = gr - p["ef"] - xf
                net = pnl_exf + p["fund"]
                ud = t30 // DAY
                dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + net
                real_eq += pnl_exf
                lg = legs[li]; lsl = int(lg.get("loss_streak_limit", 0))
                if net < 0:
                    streak[li] += 1
                    if lsl > 0 and streak[li] >= lsl:
                        pause_u[li] = t30 + int(float(lg.get("loss_streak_pause_hours", 24)) * H1)
                        streak[li] = 0
                else:
                    streak[li] = 0
                trades.append({"inst": inst, "entry_ts": p["ets"], "exit_ts": t30, "not": p["not"],
                               "gross": gr, "fee": p["ef"] + xf, "fund": p["fund"], "net": net, "reason": reason})
                done.append((li, inst))
        for k in done: del pos[k]

        # 5. Liquidation check on remaining open positions (or if realized equity after SL/gap already <= 0)
        if not halted and (pos or real_eq <= 0.0):
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
            if real_eq + w_flt <= maint_req:
                liq_events += 1
                liq_positions += len(pos)
                for (li, inst), p in list(pos.items()):
                    j = raw[inst]["d30"][0].get(t30)
                    wpx = (float(raw[inst]["d30"][1][j][2]) if p["side"] == "long" else float(raw[inst]["d30"][1][j][1])) if j is not None else last_c.get(inst, p["ep"])
                    epx = wpx * (1.0 - slip if p["side"] == "long" else 1.0 + slip)
                    gr = p["not"] * ((epx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - epx) / p["ep"])
                    xf = p["not"] * (epx / p["ep"]) * tfee
                    pnl_exf = gr - p["ef"] - xf; net = pnl_exf + p["fund"]
                    real_eq += pnl_exf
                    trades.append({"inst": inst, "entry_ts": p["ets"], "exit_ts": t30, "not": p["not"],
                                   "gross": gr, "fee": p["ef"] + xf, "fund": p["fund"], "net": net, "reason": "liq"})
                pos.clear(); pend.clear(); real_eq = max(0.0, real_eq); halted = True
        if not halted and any_sl_bar and would_liq_if_no_sl and sl_exited_this_bar > 0:
            ambiguous_sl_liq_bars.append({"ts": t30, "sl_exited": sl_exited_this_bar, "post_sl_real_eq": round(real_eq, 2)})

        # 7. Pending fills
        dp = []
        for (li, inst), od in pend.items():
            j = raw[inst]["d30"][0].get(t30)
            if j is None: continue
            o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
            o, h, l, c = float(o), float(h), float(l), float(c)
            fl, fpx = False, od["px"]; side = od["side"]
            if od["tr"]:
                if o <= od["px"]: fl, fpx = True, o * (1.0 - slip)
                elif l <= od["px"]: fl, fpx = True, od["px"] * (1.0 - slip)
            elif (side == "long" and l <= od["px"]) or (side == "short" and h >= od["px"]): fl = True
            if fl:
                eq_now = real_eq + calc_flt(t30); used_pos_im = sum(p["im"] for p in pos.values())
                if halted or eq_now <= 0.0 or (eq_now - used_pos_im) < od["im"]:
                    dp.append((li, inst)); continue
                lg = legs[li]; nt = od["not"]; ef = nt * (tfee if od["tr"] else mfee)
                tp_px = fpx * (1.0 + float(lg["tp_pct"]) if side == "long" else 1.0 - float(lg["tp_pct"]))
                sl_px = fpx * (1.0 - float(lg["sl_pct"]) if side == "long" else 1.0 + float(lg["sl_pct"]))
                if (l <= sl_px) if side == "long" else (h >= sl_px):
                    epx = sl_px * (1.0 - slip if side == "long" else 1.0 + slip)
                    gr = nt * ((epx - fpx) / fpx if side == "long" else (fpx - epx) / fpx)
                    xf = nt * (epx / fpx) * tfee; pnl = gr - ef - xf
                    ud = t30 // DAY; dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl; real_eq += pnl
                    trades.append({"inst": inst, "entry_ts": t30, "exit_ts": t30, "not": nt,
                                   "gross": gr, "fee": ef + xf, "fund": 0.0, "net": pnl, "reason": "same_bar_sl"})
                else:
                    pos[(li, inst)] = {"ep": fpx, "ets": t30, "not": nt, "im": od["im"], "ef": ef, "tp": tp_px, "sl": sl_px, "side": side, "fund": 0.0}
                dp.append((li, inst))
        for k in dp: pend.pop(k, None)

        # 8. MTM Equity & DD
        flt = calc_flt(t30); eq = max(0.0, real_eq + flt)
        mpk = max(mpk, eq); dd = mpk - eq
        mdd_u = max(mdd_u, dd); mdd_p = max(mdd_p, dd / mpk * 100.0 if mpk > 0 else 0.0)

        # 9. 1H cancel
        if (t30 + M30) % H1 == 0:
            hb = t30 - M30; d1 = []
            for (li, inst), od in pend.items():
                if not legs[li].get("use_1h_cancel", False) or od["side"] != "short" or od["pts"] > hb: continue
                j1 = raw[inst]["d1h"][0].get(hb)
                if j1 is None: continue
                o, h, l, c = raw[inst]["d1h"][1][j1]
                if c > o and h > l and (h - c) * 5.0 <= (h - l):
                    blk[(li, inst)] = ((hb // H4) + 1) * H4; d1.append((li, inst))
            for k in d1: pend.pop(k, None)

    end_flt = calc_flt(bars[-1])
    end_eq = max(0.0, real_eq + end_flt)
    first_ts = min((t["entry_ts"] for t in trades), default=bars[0])
    yrs = max((bars[-1] - first_ts) / MS_PER_YEAR, 1e-6)
    ret_eq_pct = (end_eq - init_cap) / init_cap * 100.0
    cagr_eq_pct = (((end_eq / init_cap) ** (1.0 / yrs) - 1.0) * 100.0) if end_eq > 0 else -100.0
    return {
        "trades": len(trades),
        "closed_net_u": round(sum(t["net"] for t in trades), 2),
        "final_cash_u": round(real_eq, 2),
        "final_unr_mtm_u": round(end_flt, 2),
        "final_eq_u": round(end_eq, 2),
        "ret_eq_pct": round(ret_eq_pct, 2),
        "cagr_eq_pct": round(cagr_eq_pct, 2),
        "mtm_mdd_pct": round(mdd_p, 2),
        "cum_ret_eq_over_mdd": round(ret_eq_pct / mdd_p, 3) if mdd_p > 0 else 0.0,
        "ann_calmar_eq": round(cagr_eq_pct / mdd_p, 3) if mdd_p > 0 else 0.0,
        "liq_events": liq_events,
        "liq_positions": liq_positions,
        "halted": halted,
        "gap_sl_fills": gap_sl_fills,
        "ambiguous_sl_liq_bars_count": len(ambiguous_sl_liq_bars),
        "ambiguous_sl_liq_bars": ambiguous_sl_liq_bars[:10],
    }
