import os
import json, hashlib, math, sqlite3, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(os.environ.get("OKX_RESEARCH_ROOT", Path(__file__).resolve().parent))
OUT_ROOT = ROOT / "outputs"
DB_PATH = ROOT / "queue.sqlite"
ARCHIVE_DB = ROOT / "public_data" / "funding_archive_q38.sqlite"
TZ_CST = timezone(timedelta(hours=8))
TZ_UTC = timezone.utc
M30, H1, H4, H8, DAY = 1800000, 3600000, 14400000, 28800000, 86400000
MS_PER_YEAR = 365.25 * DAY

sys.path.insert(0, str(ROOT))
import audit_v3_1_full as a
import sim_50k_v3_2_sl_fix as sim_fix

def fmt_cst(ts): return datetime.fromtimestamp(ts / 1000.0, TZ_CST).strftime("%Y-%m-%d %H:%M CST")
def fmt_utc(ts): return datetime.fromtimestamp(ts / 1000.0, TZ_UTC).strftime("%Y-%m-%d %H:%M UTC")
def ym_utc(ts): return datetime.fromtimestamp(ts / 1000.0, TZ_UTC).strftime("%Y-%m")
def yr_utc(ts): return datetime.fromtimestamp(ts / 1000.0, TZ_UTC).strftime("%Y")

def load_overlay_maps():
    acon = sqlite3.connect(ARCHIVE_DB)
    ov_rate = {}
    ov_raw_ts = {}
    dup_check = acon.execute("SELECT COUNT(*), COUNT(DISTINCT inst_id || '|' || ts_snapped) FROM funding_archive").fetchone()
    non_m30 = acon.execute("SELECT COUNT(*) FROM funding_archive WHERE (ts_snapped % ?) != 0", (M30,)).fetchone()[0]
    non_h8_arch = acon.execute("SELECT COUNT(*) FROM funding_archive WHERE (ts_snapped % ?) != 0", (H8,)).fetchone()[0]
    tot_arch = acon.execute("SELECT COUNT(*) FROM funding_archive").fetchone()[0]
    for inst, ts_s, ts_r, rt in acon.execute("SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive").fetchall():
        ov_rate.setdefault(inst, {})[int(ts_s)] = float(rt)
        ov_raw_ts.setdefault(inst, {})[int(ts_s)] = int(ts_r)
    acon.close()
    return ov_rate, ov_raw_ts, {
        "total_rows": tot_arch,
        "distinct_inst_ts_snapped": dup_check[1],
        "duplicate_rows": dup_check[0] - dup_check[1],
        "non_30m_aligned_rows": non_m30,
        "non_8h_grid_rows_in_archive": non_h8_arch,
    }

def run_audit_sim(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False):
    """Exact sim_50k_v3_2_sl_fix logic with:
    - event-level funding telemetry (8h vs non-8h, real vs miss)
    - boundary_mode:
        'default'              : standard engine (t30 > p['ets'], funding before exit at t30)
        'exclude_jitter_exit'  : exclude funding at exit bar if ts_raw > t30 (narrow window: exit happened before +jitter s)
        'include_jitter_entry' : include funding at entry bar t30 == p['ets'] if ts_raw > t30 (narrow window: entry at bar open before +jitter s)
    """
    legs = spec["legs"]
    init_cap = float(spec.get("initial_capital_u", 50000.0))
    lev_cfg = float(spec.get("leverage", 10.0))
    default_mmr = float(spec.get("mmr_approx", 0.01))
    mfee = float(spec.get("maker_fee", 0.0002))
    tfee = float(spec.get("taker_fee", 0.0005))
    slip = float(spec.get("slip_mkt", 0.0003))
    cands_by_bar, max_lev = (cands_pre, max_lev_pre) if cands_pre is not None else a.build_cands(raw, legs, lev_cfg)

    pend, pos, blk, dpnl, streak, pause_u = {}, {}, {}, {}, [0]*len(legs), [0]*len(legs)
    trades, last_c = [], {}
    real_eq = init_cap; mpk = init_cap; mdd_u = mdd_p = 0.0; halted = False

    f_ev_real_8h = 0; f_ev_real_non8h = 0; f_ev_miss_8h = 0
    real_fund_u = 0.0
    events_set = set() if record_events else None
    jitter_exit_hits = 0; jitter_exit_pnl_u = 0.0
    jitter_entry_hits = 0; jitter_entry_pnl_u = 0.0
    jitter_mid_hits = 0

    # For yearly/monthly MTM MDD tracking
    yr_eq_series = {}
    ym_eq_series = {}

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
                    ts_r = ov_raw_ts.get(inst, {}).get(t30, t30) if ov_raw_ts else t30
                    has_pos_jitter = (ts_r > t30)
                    # Check if this bar will also exit this position (SL or TP)
                    will_exit = False
                    if has_pos_jitter:
                        j = raw[inst]["d30"][0].get(t30)
                        if j is not None:
                            o, h, l, c = raw[inst]["d30"][1][j]
                            if p["side"] == "long":
                                will_exit = (l <= p["sl"]) or (h >= p["tp"])
                            else:
                                will_exit = (h >= p["sl"]) or (l <= p["tp"])
                    fp = (-p["not"] * rt) if p["side"] == "long" else (p["not"] * rt)
                    if has_pos_jitter and will_exit:
                        jitter_exit_hits += 1
                        jitter_exit_pnl_u += fp
                        if boundary_mode == "exclude_jitter_exit":
                            continue
                    elif has_pos_jitter:
                        jitter_mid_hits += 1

                    p["fund"] += fp; real_eq += fp; real_fund_u += fp
                    if t30 % H8 == 0: f_ev_real_8h += 1
                    else: f_ev_real_non8h += 1
                    if record_events:
                        events_set.add((li, inst, t30, "real_8h" if (t30 % H8 == 0) else "real_non8h"))
                elif t30 % H8 == 0:
                    f_ev_miss_8h += 1
                    if record_events:
                        events_set.add((li, inst, t30, "miss_8h"))

        # 2. Expire TTL
        for k in [k for k, od in pend.items() if t30 >= od["exp"]]: del pend[k]

        # 3. Signals
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
                used_im = sum(p["im"] for p in pos.values()) + sum(o["im"] for o in pend.values())
                if eq_now <= 0.0 or nt <= 0.0 or (eq_now - used_im) < (req_im + est_fee): continue
                pend[(li, inst)] = {"px": px, "tr": tr, "side": side, "not": nt, "im": req_im, "exp": t30 + int(float(lg["ttl_hours"]) * H1), "pts": t30}

        # 4. Exits before liq
        if not halted and pos:
            cl = []
            for (li, inst), p in list(pos.items()):
                j = raw[inst]["d30"][0].get(t30)
                if j is None: continue
                o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c
                slh = (l <= p["sl"]) if p["side"] == "long" else (h >= p["sl"])
                tph = (h >= p["tp"]) if p["side"] == "long" else (l <= p["tp"])
                if not slh and not tph: continue
                if slh:
                    if p["side"] == "long":
                        epx = (o if o <= p["sl"] else p["sl"]) * (1.0 - slip)
                        rs = "sl_gap_open" if o <= p["sl"] else "sl"
                    else:
                        epx = (o if o >= p["sl"] else p["sl"]) * (1.0 + slip)
                        rs = "sl_gap_open" if o >= p["sl"] else "sl"
                else:
                    epx = p["tp"] * (1.0 - slip if p["side"] == "long" else 1.0 + slip); rs = "tp"
                xf = p["not"] * (epx / p["ep"]) * tfee
                gr = p["not"] * ((epx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - epx) / p["ep"])
                pnl_exf = gr - p["ef"] - xf; pnl = pnl_exf + p["fund"]
                ud = t30 // DAY; dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl; real_eq += pnl_exf
                trades.append({"inst": inst, "side": p["side"], "ets": p["ets"], "xts": t30, "net": pnl, "fund": p["fund"], "fee": p["ef"] + xf, "reason": rs})
                lg = legs[li]; lsl = int(lg.get("loss_streak_limit", 0))
                if pnl < 0:
                    streak[li] += 1
                    if lsl > 0 and streak[li] >= lsl:
                        pause_u[li] = t30 + int(float(lg.get("loss_streak_pause_hours", 24)) * H1); streak[li] = 0
                else:
                    streak[li] = 0
                cl.append((li, inst))
            for k in cl: pos.pop(k, None)

        # 5. Liquidation
        if not halted and (pos or real_eq <= 0.0):
            w_flt = 0.0; maint_req = 0.0
            for (li, inst), p in pos.items():
                j = raw[inst]["d30"][0].get(t30)
                wpx = (float(raw[inst]["d30"][1][j][2]) if p["side"] == "long" else float(raw[inst]["d30"][1][j][1])) if j is not None else last_c.get(inst, p["ep"])
                w_flt += p["not"] * ((wpx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - wpx) / p["ep"]) - p["ef"]
                maint_req += p["not"] * (default_mmr + tfee)
            if real_eq + w_flt <= maint_req:
                for (li, inst), p in list(pos.items()):
                    j = raw[inst]["d30"][0].get(t30)
                    wpx = (float(raw[inst]["d30"][1][j][2]) if p["side"] == "long" else float(raw[inst]["d30"][1][j][1])) if j is not None else last_c.get(inst, p["ep"])
                    epx = wpx * (1.0 - slip if p["side"] == "long" else 1.0 + slip)
                    gr = p["not"] * ((epx - p["ep"]) / p["ep"] if p["side"] == "long" else (p["ep"] - epx) / p["ep"])
                    xf = p["not"] * (epx / p["ep"]) * tfee
                    pnl_exf = gr - p["ef"] - xf; pnl = pnl_exf + p["fund"]; real_eq += pnl_exf
                    trades.append({"inst": inst, "side": p["side"], "ets": p["ets"], "xts": t30, "net": pnl, "fund": p["fund"], "fee": p["ef"] + xf, "reason": "liq"})
                pos.clear(); pend.clear(); real_eq = max(0.0, real_eq); halted = True

        # 6. Pending fills
        dp = []
        for (li, inst), od in list(pend.items()):
            j = raw[inst]["d30"][0].get(t30)
            if j is None: continue
            o, h, l, c = raw[inst]["d30"][1][j]; last_c[inst] = c; side = od["side"]
            fl, fpx = False, od["px"]
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
                    trades.append({"inst": inst, "side": side, "ets": t30, "xts": t30, "net": pnl, "fund": 0.0, "fee": ef + xf, "reason": "same_bar_sl"})
                else:
                    # Check entry boundary with +jitter funding at t30
                    init_fund = 0.0
                    if ov_raw_ts:
                        rt_e = raw[inst]["fmap"].get(t30)
                        if rt_e is not None and ov_raw_ts.get(inst, {}).get(t30, t30) > t30:
                            fp_e = (-nt * rt_e) if side == "long" else (nt * rt_e)
                            jitter_entry_hits += 1
                            jitter_entry_pnl_u += fp_e
                            if boundary_mode == "include_jitter_entry":
                                init_fund = fp_e; real_eq += fp_e; real_fund_u += fp_e
                    pos[(li, inst)] = {"ep": fpx, "ets": t30, "not": nt, "im": od["im"], "ef": ef, "tp": tp_px, "sl": sl_px, "side": side, "fund": init_fund}
                dp.append((li, inst))
        for k in dp: pend.pop(k, None)

        # 7. MTM DD (overall + per year/month if requested)
        flt = calc_flt(t30); eq = max(0.0, real_eq + flt)
        mpk = max(mpk, eq); dd = mpk - eq
        mdd_u = max(mdd_u, dd); mdd_p = max(mdd_p, dd / mpk * 100.0 if mpk > 0 else 0.0)
        if record_trades_detail:
            y = yr_utc(t30); ym = ym_utc(t30)
            st_y = yr_eq_series.setdefault(y, [eq, eq, 0.0, eq]) # start, peak, mdd_pct, end
            st_y[1] = max(st_y[1], eq); st_y[2] = max(st_y[2], (st_y[1] - eq) / st_y[1] * 100.0 if st_y[1] > 0 else 0.0); st_y[3] = eq
            st_m = ym_eq_series.setdefault(ym, [eq, eq, 0.0, eq])
            st_m[1] = max(st_m[1], eq); st_m[2] = max(st_m[2], (st_m[1] - eq) / st_m[1] * 100.0 if st_m[1] > 0 else 0.0); st_m[3] = eq

        # 8. 1H cancel
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

    end_flt = calc_flt(bars[-1]); end_eq = max(0.0, real_eq + end_flt)
    yrs = max((bars[-1] - bars[0]) / MS_PER_YEAR, 1e-6)
    cagr = (((end_eq / init_cap) ** (1.0 / yrs) - 1.0) * 100.0) if end_eq > 0 else -100.0
    tot_real = f_ev_real_8h + f_ev_real_non8h
    tot_all = tot_real + f_ev_miss_8h

    def trade_stats(tlist):
        n = len(tlist)
        if n == 0:
            return {"trades": 0, "win_rate_pct": 0.0, "net_pnl_u": 0.0, "profit_factor": 0.0, "expectancy_u": 0.0, "fund_u": 0.0, "fee_u": 0.0}
        wins = [t["net"] for t in tlist if t["net"] > 0]
        losses = [-t["net"] for t in tlist if t["net"] < 0]
        gw = sum(wins); gl = sum(losses)
        net = sum(t["net"] for t in tlist)
        return {
            "trades": n,
            "win_rate_pct": round(100.0 * len(wins) / n, 2),
            "net_pnl_u": round(net, 2),
            "profit_factor": round(gw / gl, 3) if gl > 0 else (999.0 if gw > 0 else 0.0),
            "expectancy_u": round(net / n, 3),
            "fund_u": round(sum(t["fund"] for t in tlist), 2),
            "fee_u": round(sum(t["fee"] for t in tlist), 2),
        }

    out = {
        "trades": len(trades),
        "final_eq_u": round(end_eq, 2),
        "ret_eq_pct": round((end_eq - init_cap) / init_cap * 100.0, 2),
        "cagr_eq_pct": round(cagr, 2),
        "mtm_mdd_pct": round(mdd_p, 2),
        "ann_calmar_eq": round(cagr / mdd_p, 3) if mdd_p > 0 else 0.0,
        "f_ev_real_8h": f_ev_real_8h,
        "f_ev_real_non8h": f_ev_real_non8h,
        "f_ev_real_total": tot_real,
        "f_ev_miss_8h": f_ev_miss_8h,
        "f_ev_denom_total": tot_all,
        "funding_coverage_pct": round(100.0 * tot_real / tot_all, 2) if tot_all else 100.0,
        "real_fund_u": round(real_fund_u, 2),
        "jitter_boundary": {
            "mid_hold_jitter_events": jitter_mid_hits,
            "exit_bar_jitter_events": jitter_exit_hits,
            "exit_bar_jitter_pnl_u": round(jitter_exit_pnl_u, 2),
            "entry_bar_jitter_events": jitter_entry_hits,
            "entry_bar_jitter_pnl_u": round(jitter_entry_pnl_u, 2),
        },
        "overall_trade_stats": trade_stats(trades),
        "long_stats": trade_stats([t for t in trades if t["side"] == "long"]),
        "short_stats": trade_stats([t for t in trades if t["side"] == "short"]),
    }
    if record_events:
        out["events_set"] = events_set
    if record_trades_detail:
        by_yr = {}
        for y, st in sorted(yr_eq_series.items()):
            tl = [t for t in trades if yr_utc(t["xts"]) == y]
            d = trade_stats(tl)
            d["mtm_mdd_pct"] = round(st[2], 2)
            d["end_eq_u"] = round(st[3], 2)
            by_yr[y] = d
        by_ym = {}
        for ym, st in sorted(ym_eq_series.items()):
            tl = [t for t in trades if ym_utc(t["xts"]) == ym]
            d = trade_stats(tl)
            d["mtm_mdd_pct"] = round(st[2], 2)
            d["end_eq_u"] = round(st[3], 2)
            by_ym[ym] = d
        out["by_year"] = by_yr
        out["by_month"] = by_ym
    return out

def main():
    job_id = "F4V3-Q38-AUDIT-01"
    t0_utc = datetime.now(TZ_UTC); t0_cst = t0_utc.astimezone(TZ_CST)
    engine_sha = hashlib.sha256((ROOT / "sim_50k_v3_2_sl_fix.py").read_bytes()).hexdigest()

    con = sqlite3.connect(DB_PATH, timeout=30.0)
    con.execute("PRAGMA journal_mode=WAL;")
    spec_s = json.dumps({"version": "v1.0", "chatgpt_comment_id": 7200400749, "engine_sha256": engine_sha}, sort_keys=True)
    dk = hashlib.sha256(f"q38audit01:{spec_s}".encode()).hexdigest()[:16]
    con.execute("DELETE FROM jobs WHERE job_id=?", (job_id,))
    con.execute("INSERT INTO jobs (job_id, dedup_key, kind, spec_json, status, started_at) VALUES (?,?,?,?,?,?)",
                (job_id, dk, "q38_audit_01", spec_s, "running", t0_cst.strftime("%Y-%m-%d %H:%M:%S CST")))
    con.commit(); con.close()

    m, _, raw_base, all_30 = a.load_all_data()
    raw_ex = {k: v for k, v in raw_base.items() if k != "USDC-USDT-SWAP"}
    ov_rate, ov_raw_ts, db_audit = load_overlay_maps()

    raw_q38 = {}
    for inst, d in raw_ex.items():
        fm = dict(ov_rate.get(inst, {}))
        fm.update(d["fmap"])
        d2 = dict(d); d2["fmap"] = fm
        raw_q38[inst] = d2

    cands = [
        ("Q23", "F4V3-Q23-V3-FIB-LONG-BASE", "single_long"),
        ("Q24", "F4V3-Q24-V3-FIB-SHORT-BASE", "single_short"),
        ("Q25", "F4V3-Q25-V3-SHORT-1H-CANCEL", "single_short"),
        ("Q28", "F4V3-Q28-V3-RETEST24-R1-12S-150U", "single_short_r1_150u"),
        ("Q29", "F4V3-Q29-V3-RETEST24-R2-12S-100U", "single_short_r2_100u_size_ctrl"),
    ]
    specs = {qid: json.loads((OUT_ROOT / qname / "result.json").read_text(encoding="utf-8"))["spec"] for qid, qname, _ in cands}
    cands_cache = {qid: a.build_cands(raw_ex, specs[qid]["legs"], float(specs[qid].get("leverage", 10.0))) for qid, _, _ in cands}

    # === PART 1: DENOMINATOR DECOMPOSITION (31,044 -> 37,940) & <=60s JITTER BOUNDARY AUDIT ===
    comm_start = int(datetime(2021, 9, 1, 0, 0, tzinfo=TZ_UTC).timestamp() * 1000)
    comm_bars = [t for t in all_30 if t >= comm_start]
    cb28, ml28 = cands_cache["Q28"]

    r37_28 = run_audit_sim(raw_ex, comm_bars, specs["Q28"], None, cb28, ml28, "default", record_events=True)
    r38_28 = run_audit_sim(raw_q38, comm_bars, specs["Q28"], ov_raw_ts, cb28, ml28, "default", record_events=True)
    r38_ex_jit = run_audit_sim(raw_q38, comm_bars, specs["Q28"], ov_raw_ts, cb28, ml28, "exclude_jitter_exit")
    r38_in_jit = run_audit_sim(raw_q38, comm_bars, specs["Q28"], ov_raw_ts, cb28, ml28, "include_jitter_entry")

    # Decompose 31,044 -> 37,940 exactly
    ev37 = {(li, inst, t30) for (li, inst, t30, _) in r37_28["events_set"]}
    ev38 = {(li, inst, t30) for (li, inst, t30, _) in r38_28["events_set"]}
    added = ev38 - ev37
    removed = ev37 - ev38
    added_non8h = sum(1 for (_, _, t) in added if t % H8 != 0)
    added_8h_pos_change = sum(1 for (_, _, t) in added if t % H8 == 0)
    removed_non8h = sum(1 for (_, _, t) in removed if t % H8 != 0)
    removed_8h_pos_change = sum(1 for (_, _, t) in removed if t % H8 == 0)

    # Check if Q37 and Q38 had identical trade sequences on comm_bars
    # Wait: check pure 8H grid count in both!
    denom_decomp = {
        "q37_denom": r37_28["f_ev_denom_total"],
        "q38_denom": r38_28["f_ev_denom_total"],
        "net_diff": r38_28["f_ev_denom_total"] - r37_28["f_ev_denom_total"],
        "q37_breakdown": {"real_8h": r37_28["f_ev_real_8h"], "real_non8h": r37_28["f_ev_real_non8h"], "miss_8h": r37_28["f_ev_miss_8h"]},
        "q38_breakdown": {"real_8h": r38_28["f_ev_real_8h"], "real_non8h": r38_28["f_ev_real_non8h"], "miss_8h": r38_28["f_ev_miss_8h"]},
        "delta_by_cause": {
            "settlement_frequency_non8h_newly_observed": added_non8h - removed_non8h,
            "timestamp_dedup_or_alignment_duplicates": db_audit["duplicate_rows"],
            "position_holding_changes_8h_events": added_8h_pos_change - removed_8h_pos_change,
            "other_unexplained": (r38_28["f_ev_denom_total"] - r37_28["f_ev_denom_total"]) - ((added_non8h - removed_non8h) + (added_8h_pos_change - removed_8h_pos_change)),
        },
        "archive_db_integrity": db_audit,
        "explanation": "Q37 only counted missing events on the default 8H grid (t30%8H==0) because unknown non-8H (4H/2H/1H) settlement schedules cannot be inferred when data is absent. After Q38 backfilled real OKX archive data, actual 4H/2H/1H settlements on non-8H hours appeared in fmap and entered both numerator and denominator, accounting for the vast majority of the +6,896 delta.",
    }

    jitter_audit = {
        "default_final_eq_u": r38_28["final_eq_u"],
        "jitter_events_encountered": r38_28["jitter_boundary"],
        "narrow_window_exclude_jitter_exit": {
            "final_eq_u": r38_ex_jit["final_eq_u"],
            "pnl_diff_vs_default_u": round(r38_ex_jit["final_eq_u"] - r38_28["final_eq_u"], 2),
        },
        "narrow_window_include_jitter_entry": {
            "final_eq_u": r38_in_jit["final_eq_u"],
            "pnl_diff_vs_default_u": round(r38_in_jit["final_eq_u"] - r38_28["final_eq_u"], 2),
        },
    }
    part1_passed = (denom_decomp["delta_by_cause"]["other_unexplained"] == 0 and db_audit["duplicate_rows"] == 0 and db_audit["non_30m_aligned_rows"] == 0)
    print("PART 1 DENOM DECOMP:", json.dumps(denom_decomp["delta_by_cause"], ensure_ascii=False))
    print("PART 1 JITTER AUDIT:", json.dumps(jitter_audit, ensure_ascii=False))
    print("PART 1 PASSED:", part1_passed)

    # === PART 2: 2023-01-01 UTC ~ 2026-11-26 12:00 UTC FULL-FUNDING HISTORICAL DIAGNOSTIC ===
    diag_start = int(datetime(2023, 1, 1, 0, 0, tzinfo=TZ_UTC).timestamp() * 1000)
    diag_bars = [t for t in all_30 if t >= diag_start]
    diag_2023 = {}
    if part1_passed:
        for qid, qname, role_tag in cands:
            cb, ml = cands_cache[qid]
            r = run_audit_sim(raw_q38, diag_bars, specs[qid], ov_raw_ts, cb, ml, "default", record_events=False, record_trades_detail=True)
            # Parity verify against sim_50k_v3_2_sl_fix on diag_bars
            psim = sim_fix.run_v3_2_sl_fix(raw_q38, diag_bars, specs[qid], cands_pre=cb, max_lev_pre=ml)
            r["engine_parity_diff_u"] = round(abs(psim["final_eq_u"] - r["final_eq_u"]), 4)
            r["candidate_name"] = qname
            r["direction_group"] = role_tag
            diag_2023[qid] = r
            print(f"  2023+ {qid} ({role_tag}): cov={r['funding_coverage_pct']}%({r['f_ev_real_total']}/{r['f_ev_denom_total']}, non8h={r['f_ev_real_non8h']}) | eq={r['final_eq_u']} | cagr={r['cagr_eq_pct']}% | mdd={r['mtm_mdd_pct']}% | pf={r['overall_trade_stats']['profit_factor']} | exp={r['overall_trade_stats']['expectancy_u']} | parity_diff={r['engine_parity_diff_u']}")

    t1_utc = datetime.now(TZ_UTC); t1_cst = t1_utc.astimezone(TZ_CST)
    od = OUT_ROOT / job_id
    od.mkdir(parents=True, exist_ok=True)
    out_path = od / "result.json"
    res = {
        "job_id": job_id,
        "version": "v1.0",
        "chatgpt_handoff_comment_id": 7200400749,
        "started_utc": t0_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "finished_utc": t1_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "started_cst": t0_cst.strftime("%Y-%m-%d %H:%M:%S CST"),
        "finished_cst": t1_cst.strftime("%Y-%m-%d %H:%M:%S CST"),
        "elapsed_sec": round((t1_utc - t0_utc).total_seconds(), 1),
        "data_cutoff_cst": m.get("source_cutoff_taipei"),
        "engine_file": "sim_50k_v3_2_sl_fix.py",
        "engine_sha256": engine_sha,
        "base_data_hash_untouched": m["data_hash"],
        "q38_reference_result_sha256": "0a598fd630c44f1dd27ef17db3140294331aa628eabdb3ce19a01de205698b28",
        "matching_and_cost_assumptions": {
            "universe": "EX_USDC_286 (excl. USDC-USDT-SWAP, preserves historical delisted)",
            "initial_capital_u": 50000.0,
            "maker_fee": 0.0002,
            "taker_fee": 0.0005,
            "slip_mkt": 0.0003,
            "sl_before_liq": True,
            "gap_sl_open_fill": True,
            "funding_updates_equity_and_margin": True,
            "mmr_limitation": "Historical tiered MMR unknown; fixed default_mmr=1% + taker_fee approximation retained as known limitation.",
            "oos_limitation": "2026-11-15 04:00 CST ~ 2026-11-26 20:00 CST already consumed/viewed; NOT reusable as independent OOS.",
        },
        "part1_denominator_and_jitter_audit": {
            "passed": part1_passed,
            "denominator_decomposition_q28_comm": denom_decomp,
            "jitter_60s_boundary_audit_q28_comm": jitter_audit,
        },
        "part2_2023_full_funding_diagnostic": {
            "window_utc": f"{fmt_utc(diag_bars[0])} ~ {fmt_utc(diag_bars[-1])}",
            "window_cst": f"{fmt_cst(diag_bars[0])} ~ {fmt_cst(diag_bars[-1])}",
            "days": round((diag_bars[-1] - diag_bars[0]) / DAY, 2),
            "note": "Frozen parameters; single-direction candidates only (no shared-capital multi-leg combo); R1/R2 are position-size controls only. Kept alongside 2021-09 long-term Q38 comparison; shorter window is NOT claimed as performance improvement.",
            "candidates": diag_2023,
        },
    }
    out_bytes = json.dumps(res, ensure_ascii=False, indent=2).encode("utf-8")
    out_path.write_bytes(out_bytes)
    out_sha = hashlib.sha256(out_bytes).hexdigest()

    con = sqlite3.connect(DB_PATH, timeout=30.0)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("UPDATE jobs SET status='done', finished_at=?, result_path=?, summary_json=? WHERE job_id=?",
                (t1_cst.strftime("%Y-%m-%d %H:%M:%S CST"), str(out_path),
                 json.dumps({"part1_passed": part1_passed, "out_sha256": out_sha[:16]}, ensure_ascii=False), job_id))
    con.commit()
    q_counts = con.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()
    con.close()
    print(f"\nDONE {job_id} | {res['started_utc']} ~ {res['finished_utc']} | sha256={out_sha} | queue={q_counts}")

if __name__ == "__main__":
    main()
