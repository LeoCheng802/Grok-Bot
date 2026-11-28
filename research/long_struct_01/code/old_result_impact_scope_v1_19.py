#!/usr/bin/env python3
"""BACKTEST-READINESS-01 v1.21 | old-result impact scope (static, no replay).

(File name kept as old_result_impact_scope_v1_19.py on purpose: v1.20 and v1.21 update it in place; the tool still supersedes
old_result_impact_scope_v1_17.py.)
Supersedes old_result_impact_scope_v1_17.py (kept unchanged for audit; do not use for new assessments).
Answers "does this newly delivered funding data touch what an OLD result actually held?" without
re-running any strategy. Inputs: saved local-details JSON files (L1 / LONG / RETEST24 / combo adapters),
each bound to the TRUE cutoff of that run (--cutoff-utc, one per --details, same order), and one or more
funding delta CSV(.gz) files (rows that were NOT in that old run's DB).

Rule (same as the B6/Q38 engine): funding at ts_snapped t is booked for a position when ets < t <= xts;
an open_at_end position is held over (ets, cutoff]. Delta keys after the cutoff never count.

Verdict per scenario:
  AFFECTED_PATH_MAY_CHANGE      clean (non-conflicting) delta keys fall inside held intervals or cover old
                                miss_8h events (equity / margin / daily-loss / liquidation paths can change)
  NOT_AFFECTED_BY_THESE_DELTAS  complete, schema-valid, count-verified evidence and zero intersection
  UNDETERMINABLE                evidence insufficient or schema invalid (closed or open_at_end list missing,
                                schema invalid, counts not verifiable or not matching, position outside the
                                cutoff, invalid / mismatched embedded cutoff, non-list missing_funding_events_all,
                                or a CONFLICTING delta key touching a held interval). Verdict priority (v1.21):
                                any undeterminable reason (including schema) wins over AFFECTED_PATH_MAY_CHANGE;
                                hit counts (hit8 / hitn / covered) are still recorded.
v1.19 fixes (ChatGPT v1.19, Issue #1 #7231413139, items 1-2):
  * --out AND --out + ".tmp" must both differ from every input (resolve() and os.path.samefile);
    an existing --out, an existing .tmp or a symlink at either path is refused before any write;
    the .tmp is created with O_CREAT|O_EXCL; inputs are re-hashed after the assessment and the output paths are
    checked a SECOND time immediately before the .tmp is written (a second pre-write check, not a rename-time check).
    This does NOT guarantee that an arbitrary concurrent change by another process can never overwrite a file;
    run it in a NEW isolated single-writer directory.
v1.20 (ChatGPT v1.20, Issue #1 #7235223075): an invalid / non-string / empty embedded cutoff_utc in a details file, or a
  non-list missing_funding_events_all, no longer aborts the whole assessment: the affected scenarios are reported
  UNDETERMINABLE (reasons details_embedded_cutoff_invalid / missing_funding_events_not_a_list). The CLI --cutoff-utc
  stays strict (explicit refusal with a message).
v1.21 (ChatGPT v1.21, Issue #1 #7235906231): final verdict priority: any undeterminable reason (schema-invalid
  embedded cutoff, non-list missing_funding_events_all, and every other undet reason) is applied FIRST; a clean
  delta hit (held interval or covered miss event) must not upgrade the verdict to AFFECTED_PATH_MAY_CHANGE.
  hit8 / hitn / covered are still recorded so the intersection is visible.
  * open_at_end bound to the run cutoff; schema and record-count integrity checked; missing evidence ->
    UNDETERMINABLE; identical basenames never overwrite each other (inputs / assessments are lists keyed
    by argument index); conflicting delta keys are excluded from the clean set and never reported clean.
Delta rows whose rate is empty/None/NaN/Inf are counted as rejected and never used. Output: a NEW JSON file.
Zero network, zero strategy/engine import, zero writes except --out (via its .tmp).
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

RUNNER_VERSION = "v1.21"
TOOL_ID = "old_result_impact_scope_v1_19"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def parse_utc_ms(s):
    s = str(s).strip()
    if not s.endswith("Z"):
        raise RuntimeError("cutoff must be an explicit UTC ISO time ending in Z: " + s)
    dt = datetime.strptime(s[:-1], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


# ------------------------------------------------------------------------------------------------
# output-path safety (item 1)
# ------------------------------------------------------------------------------------------------

def _same(a, b):
    try:
        if a.resolve() == b.resolve():
            return True
    except OSError:
        return True
    try:
        if a.exists() and b.exists() and os.path.samefile(str(a), str(b)):
            return True
    except OSError:
        return True
    return False


def check_output_paths(out, inputs):
    tmp = Path(str(out) + ".tmp")
    for label, p in (("--out", out), ("--out.tmp", tmp)):
        if p.is_symlink():
            raise RuntimeError(label + " is a symlink; refusing before any write")
        if p.exists():
            raise RuntimeError(label + " already exists (stale temp / old assessment); write each assessment to a NEW file")
        for q in inputs:
            if _same(p, q):
                raise RuntimeError(label + " collides with an input (" + q.name + "); refusing before any write")
    parent = out.parent if str(out.parent) else Path(".")
    if parent.is_symlink():
        raise RuntimeError("--out parent directory is a symlink; refusing before any write")
    return tmp


def write_exclusive(tmp, out, text):
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    os.replace(str(tmp), str(out))


# ------------------------------------------------------------------------------------------------
# delta loading (item 2: conflicts never kept as first value)
# ------------------------------------------------------------------------------------------------

def load_delta(paths):
    seen, conflict_keys, rejected, dup_identical = {}, set(), 0, 0
    for p in paths:
        opener = gzip.open if str(p).endswith(".gz") else open
        with opener(p, "rt", encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            cols = rd.fieldnames or []
            miss = [c for c in ("inst_id", "ts_snapped_ms", "funding_rate") if c not in cols]
            if miss:
                raise RuntimeError("delta CSV missing columns: " + ", ".join(miss))
            for row in rd:
                inst = (row.get("inst_id") or "").strip()
                ts = (row.get("ts_snapped_ms") or "").strip()
                txt = (row.get("funding_rate") or "").strip()
                try:
                    rate = float(txt)
                    ok = math.isfinite(rate)
                    tsv = int(ts)
                except ValueError:
                    ok = False
                if not inst or not ok:
                    rejected += 1
                    continue
                k = (inst, tsv)
                is8 = str(row.get("is_8h_grid", "")).strip().lower() == "true"
                if k in seen:
                    if seen[k][0] != rate:
                        conflict_keys.add(k)
                    else:
                        dup_identical += 1
                    continue
                seen[k] = (rate, is8)
    clean, conflicts = {}, {}
    for (inst, ts), (_, is8) in seen.items():
        tgt = conflicts if (inst, ts) in conflict_keys else clean
        tgt.setdefault(inst, []).append((ts, is8))
    for d in (clean, conflicts):
        for v in d.values():
            v.sort()
    stats = {"distinct_keys": len(seen), "clean_keys": len(seen) - len(conflict_keys),
             "conflicting_keys_excluded": len(conflict_keys), "identical_duplicate_rows": dup_identical,
             "rejected_non_finite_or_empty": rejected, "delta_clean": not conflict_keys}
    return clean, conflicts, stats


# ------------------------------------------------------------------------------------------------
# details evidence (item 2: cutoff, schema, counts)
# ------------------------------------------------------------------------------------------------

def _declared_counts(scen):
    c = scen.get("counts")
    if isinstance(c, dict) and _is_int(c.get("closed_trades")) and _is_int(c.get("open_at_end")):
        return c["closed_trades"], c["open_at_end"]
    return None


def _intervals(scen, cutoff):
    out, undet = [], []
    closed = scen.get("closed_trades")
    if closed is None:
        closed = scen.get("trades_detail")
    if not isinstance(closed, list):
        undet.append("closed_trades_not_serialized")
        closed = []
    for t in closed:
        ets = t.get("ets_ms", t.get("entry_ts_ms")) if isinstance(t, dict) else None
        xts = t.get("xts_ms", t.get("exit_ts_ms")) if isinstance(t, dict) else None
        if not isinstance(t, dict) or not t.get("inst_id") or not _is_int(ets) or not _is_int(xts):
            undet.append("closed_trade_schema_invalid")
            continue
        if xts < ets:
            undet.append("closed_trade_exit_before_entry")
            continue
        if xts > cutoff:
            undet.append("closed_trade_after_cutoff")
            continue
        out.append((t["inst_id"], ets, xts, "closed"))
    opens = scen.get("open_at_end")
    if not isinstance(opens, list):
        undet.append("open_at_end_not_serialized")
        opens = []
    for p in opens:
        ets = p.get("ets_ms") if isinstance(p, dict) else None
        if not isinstance(p, dict) or not p.get("inst_id") or not _is_int(ets):
            undet.append("open_at_end_schema_invalid")
            continue
        if ets > cutoff:
            undet.append("open_at_end_entry_after_cutoff")
            continue
        out.append((p["inst_id"], ets, cutoff, "open_at_end"))
    dc = _declared_counts(scen)
    if dc is None:
        undet.append("record_counts_not_declared_count_integrity_unverifiable")
    elif dc != (len(closed), len(opens)):
        undet.append("record_counts_mismatch_declared_%d_%d_found_%d_%d" % (dc[0], dc[1], len(closed), len(opens)))
    return out, undet


def _count_in(series, a, b):
    n8 = nn = 0
    for ts, is8 in series:
        if a < ts <= b:
            if is8:
                n8 += 1
            else:
                nn += 1
    return n8, nn


def _embedded_cutoff_state(embedded, cutoff):
    """None -> no embedded cutoff; 'ok' / 'mismatch' / 'invalid' otherwise (never raises)."""
    if embedded is None:
        return None
    if not isinstance(embedded, str):
        return "invalid"
    try:
        return "ok" if parse_utc_ms(embedded) == cutoff else "mismatch"
    except (RuntimeError, ValueError, OverflowError, OSError):
        return "invalid"


def assess(details_obj, clean, conflicts, cutoff):
    res = {}
    embedded = details_obj.get("cutoff_utc") if isinstance(details_obj, dict) else None
    scen_all = details_obj.get("scenarios") if isinstance(details_obj, dict) else None
    if not isinstance(scen_all, dict) or not scen_all:
        return {"_no_scenarios": {"verdict": "UNDETERMINABLE", "undeterminable_reasons": ["no_scenarios_in_details"]}}
    for name, scen in scen_all.items():
        if not isinstance(scen, dict):
            res[name] = {"verdict": "UNDETERMINABLE", "undeterminable_reasons": ["scenario_schema_invalid"]}
            continue
        ivs, undet = _intervals(scen, cutoff)
        est = _embedded_cutoff_state(embedded, cutoff)
        if est == "mismatch":
            undet.append("cutoff_mismatch_with_details_embedded_cutoff")
        elif est == "invalid":
            undet.append("details_embedded_cutoff_invalid")
        hit8 = hitn = touched = conflict_hits = 0
        for inst, a, b, _kind in ivs:
            n8, nn = _count_in(clean.get(inst, ()), a, b)
            c8, cn = _count_in(conflicts.get(inst, ()), a, b)
            hit8 += n8
            hitn += nn
            conflict_hits += c8 + cn
            touched += 1 if (n8 or nn) else 0
        miss = scen.get("missing_funding_events_all")
        if miss is None:
            miss = []
        elif not isinstance(miss, list):
            undet.append("missing_funding_events_not_a_list")
            miss = []
        covered = conflict_cover = 0
        for m in miss:
            if not isinstance(m, dict) or not m.get("inst_id") or not _is_int(m.get("ts_ms")):
                undet.append("missing_funding_event_schema_invalid")
                continue
            if m["ts_ms"] > cutoff:
                continue
            if any(ts == m["ts_ms"] for ts, _ in clean.get(m["inst_id"], ())):
                covered += 1
            if any(ts == m["ts_ms"] for ts, _ in conflicts.get(m["inst_id"], ())):
                conflict_cover += 1
        if conflict_hits or conflict_cover:
            undet.append("conflicting_delta_values_touch_held_interval_or_miss_event")
        # v1.21: schema / evidence problems (undet) take priority over a clean-delta hit.
        if undet:
            verdict = "UNDETERMINABLE"
        elif hit8 or hitn or covered:
            verdict = "AFFECTED_PATH_MAY_CHANGE"
        else:
            verdict = "NOT_AFFECTED_BY_THESE_DELTAS"
        res[name] = {"verdict": verdict, "positions_checked": len(ivs), "positions_touched": touched,
                     "clean_delta_keys_in_held_8h": hit8, "clean_delta_keys_in_held_non8h": hitn,
                     "conflicting_delta_keys_in_held": conflict_hits,
                     "old_miss_8h_events": len(miss), "old_miss_8h_now_covered_clean": covered,
                     "old_miss_8h_covered_by_conflicting_keys": conflict_cover,
                     "undeterminable_reasons": sorted(set(undet))}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--details", action="append", required=True)
    ap.add_argument("--cutoff-utc", action="append", required=True,
                    help="TRUE data cutoff (end) of the run that produced the matching --details, e.g. 2026-11-26T12:00:00Z; one per --details, same order")
    ap.add_argument("--delta", action="append", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if len(a.cutoff_utc) != len(a.details):
        raise RuntimeError("exactly one --cutoff-utc per --details is required (same order)")
    cutoffs = [parse_utc_ms(c) for c in a.cutoff_utc]
    out = Path(a.out)
    ins = [("details", i, Path(p)) for i, p in enumerate(a.details)] + [("delta", i, Path(p)) for i, p in enumerate(a.delta)]
    for _, _, p in ins:
        if not p.is_file():
            raise RuntimeError("input is not a regular file: " + p.name)
    tmp = check_output_paths(out, [p for _, _, p in ins])
    before = [{"role": r, "index": i, "name": p.name, "sha256": sha(p)} for r, i, p in ins]
    clean, conflicts, dstats = load_delta([Path(p) for p in a.delta])
    names = [Path(p).name for p in a.details]
    report = {"tool": TOOL_ID, "version": RUNNER_VERSION,
              "write_safety": "output and .tmp checked before the hash pass and again immediately before the .tmp is written; no guarantee against arbitrary concurrent changes by other processes; use a new isolated single-writer directory",
              "rule": "funding booked when ets < ts_snapped <= xts; open_at_end held over (ets, cutoff]; keys after cutoff ignored",
              "delta_stats": dstats, "inputs_sha256": before,
              "duplicate_details_basenames": sorted({n for n in names if names.count(n) > 1}),
              "assessments": []}
    for i, p in enumerate(a.details):
        obj = json.loads(Path(p).read_text(encoding="utf-8"))
        report["assessments"].append({"details_index": i, "details_name": Path(p).name, "cutoff_utc": a.cutoff_utc[i],
                                      "scenarios": assess(obj, clean, conflicts, cutoffs[i])})
    if [{"role": r, "index": i, "name": p.name, "sha256": sha(p)} for r, i, p in ins] != before:
        raise RuntimeError("input changed during assessment")
    check_output_paths(out, [p for _, _, p in ins])
    write_exclusive(tmp, out, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("IMPACT_SCOPE_SHA256:", sha(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
