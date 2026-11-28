#!/usr/bin/env python3
"""BACKTEST-READINESS-01 v1.17 | old-result impact scope (static, no replay).

Answers "does this newly delivered funding data touch what an OLD result actually held?" without
re-running any strategy. Inputs: one or more saved local-details JSON files (L1 / LONG / RETEST24 /
combo adapters) and one or more funding delta CSV(.gz) files (rows that were NOT in that old run's DB).
Rule (same as the B6/Q38 engine): funding at ts_snapped t is booked for a position when ets < t <= xts.
Verdict per scenario:
  AFFECTED_PATH_MAY_CHANGE      new rows fall inside held intervals or cover old miss_8h events
                                (equity, margin, daily-loss and liquidation paths can change -> update that arm)
  NOT_AFFECTED_BY_THESE_DELTAS  zero intersection -> do not rerun for this data
  UNDETERMINABLE                no per-position detail serialized (e.g. open positions not listed) -> listed, not guessed
Delta rows whose rate is empty/None/NaN/Inf are counted as rejected and never used. Output: a NEW JSON file.
Zero network, zero strategy/engine import, zero writes except --out.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

RUNNER_VERSION = "v1.17"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def load_delta(paths):
    keys, rejected, dup_conflicts = {}, 0, 0
    for p in paths:
        opener = gzip.open if str(p).endswith(".gz") else open
        with opener(p, "rt", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                inst = row.get("inst_id")
                ts = row.get("ts_snapped_ms")
                txt = (row.get("funding_rate") or "").strip()
                try:
                    rate = float(txt)
                    ok = math.isfinite(rate)
                except ValueError:
                    ok = False
                if not inst or not ts or not ok:
                    rejected += 1
                    continue
                k = (inst, int(ts))
                if k in keys and keys[k][0] != txt:
                    dup_conflicts += 1
                keys.setdefault(k, (txt, str(row.get("is_8h_grid", "")).lower() == "true"))
    by_inst = {}
    for (inst, ts), (_, is8) in keys.items():
        by_inst.setdefault(inst, []).append((ts, is8))
    for v in by_inst.values():
        v.sort()
    return by_inst, {"valid_keys": len(keys), "rejected_non_finite_or_empty": rejected, "conflicting_duplicates": dup_conflicts}


def _intervals(scen):
    out, undet = [], []
    trades = scen.get("closed_trades")
    if trades is None:
        trades = scen.get("trades_detail")
    for t in trades or []:
        ets = t.get("ets_ms", t.get("entry_ts_ms"))
        xts = t.get("xts_ms", t.get("exit_ts_ms"))
        if t.get("inst_id") is None or ets is None or xts is None:
            undet.append("closed_trade_missing_inst_or_times")
            continue
        out.append((t["inst_id"], int(ets), int(xts), "closed"))
    if "open_at_end" in scen:
        for p in scen.get("open_at_end") or []:
            out.append((p["inst_id"], int(p["ets_ms"]), None, "open_at_end"))
    else:
        undet.append("open_at_end_not_serialized")
    return out, undet


def assess(details_obj, delta):
    res = {}
    for name, scen in (details_obj.get("scenarios") or {}).items():
        ivs, undet = _intervals(scen)
        hit8 = hitn = 0
        touched = 0
        for inst, a, b, _kind in ivs:
            n_here = 0
            for ts, is8 in delta.get(inst, ()):
                if ts > a and (b is None or ts <= b):
                    n_here += 1
                    if is8:
                        hit8 += 1
                    else:
                        hitn += 1
            touched += 1 if n_here else 0
        miss = scen.get("missing_funding_events_all") or []
        covered = sum(1 for m in miss if any(ts == int(m["ts_ms"]) for ts, _ in delta.get(m["inst_id"], ())))
        if hit8 or hitn or covered:
            verdict = "AFFECTED_PATH_MAY_CHANGE"
        elif undet:
            verdict = "UNDETERMINABLE"
        else:
            verdict = "NOT_AFFECTED_BY_THESE_DELTAS"
        res[name] = {"verdict": verdict, "positions_checked": len(ivs), "positions_touched": touched,
                     "delta_keys_in_held_8h": hit8, "delta_keys_in_held_non8h": hitn,
                     "old_miss_8h_events": len(miss), "old_miss_8h_now_covered": covered, "undeterminable_reasons": sorted(set(undet))}
    if not res:
        res["_no_scenarios"] = {"verdict": "UNDETERMINABLE", "undeterminable_reasons": ["no_scenarios_in_details"]}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--details", action="append", required=True)
    ap.add_argument("--delta", action="append", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists() or out.is_symlink():
        raise RuntimeError("--out already exists; write each assessment to a NEW file")
    ins = [Path(p) for p in a.details + a.delta]
    if any(out.resolve() == p.resolve() for p in ins):
        raise RuntimeError("--out collides with an input")
    before = {str(p.name): sha(p) for p in ins}
    delta, dstats = load_delta([Path(p) for p in a.delta])
    report = {"tool": "old_result_impact_scope_v1_17", "version": RUNNER_VERSION,
              "rule": "funding booked when ets < ts_snapped <= xts (open_at_end: ets < ts)",
              "delta_stats": dstats, "inputs_sha256": before, "assessments": {}}
    for p in a.details:
        obj = json.loads(Path(p).read_text(encoding="utf-8"))
        report["assessments"][Path(p).name] = assess(obj, delta)
    if {str(p.name): sha(p) for p in ins} != before:
        raise RuntimeError("input changed during assessment")
    tmp = Path(str(out) + ".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    print("IMPACT_SCOPE_SHA256:", sha(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
