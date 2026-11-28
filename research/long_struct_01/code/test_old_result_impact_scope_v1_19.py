#!/usr/bin/env python3
"""Synthetic tests for old_result_impact_scope_v1_19.py (v1.20 in-place update; no market data, no replay, temp dirs only).

Minimal pure-synthetic boundary / collision cases for ChatGPT v1.19 items 1-2 (Issue #1 #7231413139).
IMPACT_TOOL_PATH may point at another tool version (used to record old-fails / new-passes evidence);
when the tool under test has no --cutoff-utc (v1.17) the flag is omitted so the assertion, not argparse, fails.
"""
import gzip
import importlib.util
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = Path(os.environ.get("IMPACT_TOOL_PATH") or (HERE / "old_result_impact_scope_v1_19.py"))
_s = importlib.util.spec_from_file_location("impact_under_test", str(TOOL))
mod = importlib.util.module_from_spec(_s)
_s.loader.exec_module(mod)
H8 = 28800000
T0 = 1709251200000                     # 2024-03-01T00:00:00Z
CUT = "2024-03-01T16:00:00Z"           # T0 + 2*H8
HAS_CUTOFF = hasattr(mod, "parse_utc_ms")


def _check(c, m):
    if not c:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + m)


def _delta(td, rows, name="delta.csv.gz"):
    p = td / name
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write("\n".join(["inst_id,ts_snapped_ms,funding_rate,is_8h_grid"] + rows) + "\n")
    return p


def _det(td, obj, name="old_details.json"):
    p = td / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def _run(details, delta, out, cut=CUT):
    argv = []
    for d in details:
        argv += ["--details", str(d)]
        if HAS_CUTOFF:
            argv += ["--cutoff-utc", cut]
    argv += ["--delta", str(delta), "--out", str(out)]
    return mod.main(argv)


def _scen(report, idx=0, name="old_details.json"):
    a = report["assessments"]
    if isinstance(a, list):
        return a[idx]["scenarios"]
    return a[name]


def _counts(closed, opens):
    return {"closed_trades": len(closed), "open_at_end": len(opens)}


def _sc(closed, opens, **kw):
    d = {"closed_trades": closed, "open_at_end": opens, "counts": _counts(closed, opens)}
    d.update(kw)
    return d


def test_legacy_semantics():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8), "AAA-USDT-SWAP,%d,0.0001,false" % (T0 + 10 * H8),
                         "BBB-USDT-SWAP,%d,None,true" % (T0 + H8), "CCC-USDT-SWAP,%d,inf,true" % (T0 + H8),
                         "DDD-USDT-SWAP,%d,0.0002,true" % (T0 + 2 * H8)])
        hit = [{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0, "xts_ms": T0 + H8}]
        edge = [{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0 + H8, "xts_ms": T0 + 2 * H8}]
        det = {"scenarios": {"hit": _sc(hit, []), "edge": _sc(edge, []),
                             "miss": _sc([], [], missing_funding_events_all=[{"inst_id": "DDD-USDT-SWAP", "ts_ms": T0 + 2 * H8}]),
                             "l1_style": {"trades_detail": [{"inst_id": "ZZZ-USDT-SWAP", "entry_ts_ms": T0, "exit_ts_ms": T0 + H8}]}}}
        detp = _det(td, det)
        out = td / "impact.json"
        _check(_run([detp], dp, out) == 0, "rc")
        a = _scen(json.loads(out.read_text(encoding="utf-8")))
        _check(a["hit"]["verdict"] == "AFFECTED_PATH_MAY_CHANGE", "(ets, xts] includes exit bar")
        _check(a["edge"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "ets bar itself excluded")
        _check(a["miss"]["verdict"] == "AFFECTED_PATH_MAY_CHANGE", "miss covered")
        _check(a["l1_style"]["verdict"] == "UNDETERMINABLE", "L1 open positions not serialized")
        try:
            _run([detp], dp, out)
            _check(False, "existing --out must be refused")
        except RuntimeError:
            pass
    print("LEGACY: (ets,xts] rule, rejected rows, miss coverage, L1 undeterminable, existing --out refused")


def test_out_tmp_aliases_input():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        src = _det(td, {"scenarios": {"s": _sc([], [])}}, name="assessment.json.tmp")
        raw = src.read_bytes()
        out = td / "assessment.json"
        refused = False
        try:
            _run([src], dp, out)
        except RuntimeError:
            refused = True
        _check(src.exists() and src.read_bytes() == raw, "input equal to out.tmp must stay byte-identical")
        _check(refused and not out.exists(), "out.tmp == input must be refused before any write")
    print("TMP-ALIAS: --out.tmp equal to an input is refused; input untouched")


def test_existing_tmp_and_symlink_refused():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        detp = _det(td, {"scenarios": {"s": _sc([], [])}})
        out = td / "impact.json"
        stale = Path(str(out) + ".tmp")
        stale.write_text("STALE_TMP_EVIDENCE\n", encoding="utf-8")
        refused = False
        try:
            _run([detp], dp, out)
        except RuntimeError:
            refused = True
        _check(refused and stale.read_text(encoding="utf-8") == "STALE_TMP_EVIDENCE\n" and not out.exists(), "existing .tmp refused and kept")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        detp = _det(td, {"scenarios": {"s": _sc([], [])}})
        victim = td / "victim.txt"
        victim.write_text("VICTIM\n", encoding="utf-8")
        out = td / "impact.json"
        Path(str(out) + ".tmp").symlink_to(victim)
        refused = False
        try:
            _run([detp], dp, out)
        except RuntimeError:
            refused = True
        _check(refused and victim.read_text(encoding="utf-8") == "VICTIM\n", "symlinked .tmp refused; target untouched")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        detp = _det(td, {"scenarios": {"s": _sc([], [])}})
        out = td / "impact.json"
        out.symlink_to(td / "nowhere.json")
        refused = False
        try:
            _run([detp], dp, out)
        except RuntimeError:
            refused = True
        _check(refused and not (td / "nowhere.json").exists(), "dangling symlink --out refused")
    print("TMP/SYMLINK: existing .tmp, symlinked .tmp and symlinked --out all refused before write")


def test_open_at_end_bound_to_cutoff():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # delta key after the run's cutoff (T0+2*H8): must not count for an open_at_end position
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + 5 * H8)])
        detp = _det(td, {"scenarios": {"open": _sc([], [{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0}])}})
        out = td / "impact.json"
        _check(_run([detp], dp, out) == 0, "rc")
        a = _scen(json.loads(out.read_text(encoding="utf-8")))
        _check(a["open"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "post-cutoff delta must not affect open_at_end: %r" % a["open"])
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + 2 * H8)])  # exactly at cutoff -> inside (ets, cutoff]
        detp = _det(td, {"scenarios": {"open": _sc([], [{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0}])}})
        out = td / "impact.json"
        _run([detp], dp, out)
        a = _scen(json.loads(out.read_text(encoding="utf-8")))
        _check(a["open"]["verdict"] == "AFFECTED_PATH_MAY_CHANGE", "key at cutoff counts")
    print("CUTOFF: open_at_end held over (ets, cutoff]; post-cutoff keys ignored; key at cutoff counted")


def test_missing_evidence_is_undeterminable():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        det = {"scenarios": {
            "no_closed_list": {"open_at_end": [], "counts": {"closed_trades": 0, "open_at_end": 0}},
            "count_mismatch": {"closed_trades": [{"inst_id": "BBB-USDT-SWAP", "ets_ms": T0, "xts_ms": T0 + H8}], "open_at_end": [],
                               "counts": {"closed_trades": 2, "open_at_end": 0}},
            "bad_schema": {"closed_trades": [{"inst_id": "BBB-USDT-SWAP", "ets_ms": "x", "xts_ms": T0}], "open_at_end": [],
                           "counts": {"closed_trades": 1, "open_at_end": 0}},
            "no_counts": {"closed_trades": [], "open_at_end": []},
        }}
        detp = _det(td, det)
        out = td / "impact.json"
        rc = 1
        try:
            rc = _run([detp], dp, out)
        except Exception:
            rc = 1
        _check(rc == 0 and out.exists(), "tool must report, not crash, on weak evidence")
        a = _scen(json.loads(out.read_text(encoding="utf-8")))
        for k in ("no_closed_list", "count_mismatch", "bad_schema", "no_counts"):
            _check(a[k]["verdict"] == "UNDETERMINABLE", "%s must be UNDETERMINABLE: %r" % (k, a[k]))
    print("EVIDENCE: missing closed list / count mismatch / bad schema / undeclared counts -> UNDETERMINABLE")


def test_same_basename_not_overwritten():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        d1 = _det(td, {"scenarios": {"s": _sc([{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0, "xts_ms": T0 + H8}], [])}}, name="a/old_details.json")
        d2 = _det(td, {"scenarios": {"s": _sc([], [])}}, name="b/old_details.json")
        out = td / "impact.json"
        _check(_run([d1, d2], dp, out) == 0, "rc")
        r = json.loads(out.read_text(encoding="utf-8"))
        a = r["assessments"]
        _check(isinstance(a, list) and len(a) == 2, "two same-basename details must give two assessments: %r" % type(a))
        _check(a[0]["scenarios"]["s"]["verdict"] == "AFFECTED_PATH_MAY_CHANGE" and a[1]["scenarios"]["s"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "no overwrite")
        hs = r["inputs_sha256"]
        _check(isinstance(hs, list) and len([h for h in hs if h.get("role") == "details"]) == 2, "both input hashes kept")
    print("BASENAME: identical basenames keep separate hashes and assessments")


def test_conflicting_delta_not_clean():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8), "AAA-USDT-SWAP,%d,0.0009,true" % (T0 + H8)])
        detp = _det(td, {"scenarios": {"s": _sc([{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0, "xts_ms": T0 + H8}], []),
                                       "far": _sc([{"inst_id": "ZZZ-USDT-SWAP", "ets_ms": T0, "xts_ms": T0 + H8}], [])}})
        out = td / "impact.json"
        _check(_run([detp], dp, out) == 0, "rc")
        r = json.loads(out.read_text(encoding="utf-8"))
        a = _scen(r)
        _check(a["s"]["verdict"] == "UNDETERMINABLE", "conflicting key in held interval must not be a clean verdict: %r" % a["s"])
        _check(r["delta_stats"].get("delta_clean") is False, "delta_clean flag false")
        _check(a["far"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "untouched scenario unaffected")
    print("CONFLICT: conflicting delta key excluded from clean set; touched scenario UNDETERMINABLE")


def test_invalid_embedded_cutoff_is_undeterminable():
    """v1.20 item 1: a bad embedded cutoff_utc must not abort the whole assessment."""
    bad_values = ["not-a-date", "2024-03-01T16:00:00", 12345, "", ["x"]]
    for i, bad in enumerate(bad_values):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
            det = {"cutoff_utc": bad, "scenarios": {"s": _sc([], []), "t": _sc([], [])}}
            detp = _det(td, det)
            out = td / "impact.json"
            try:
                rc = _run([detp], dp, out)
            except Exception as exc:
                raise AssertionError("SYNTHETIC_TEST_FAIL: invalid embedded cutoff %r aborted the assessment: %s: %s" % (bad, type(exc).__name__, exc))
            _check(rc == 0 and out.exists(), "report written for %r" % (bad,))
            a = _scen(json.loads(out.read_text(encoding="utf-8")))
            for k in ("s", "t"):
                _check(a[k]["verdict"] == "UNDETERMINABLE" and "details_embedded_cutoff_invalid" in a[k]["undeterminable_reasons"],
                       "scenario %s with embedded %r must be UNDETERMINABLE/details_embedded_cutoff_invalid: %r" % (k, bad, a[k]))
    # control: valid and equal embedded cutoff stays clean; valid but different -> mismatch reason (existing semantics)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        detp = _det(td, {"cutoff_utc": CUT, "scenarios": {"s": _sc([], [])}})
        out = td / "impact.json"
        _run([detp], dp, out)
        _check(_scen(json.loads(out.read_text(encoding="utf-8")))["s"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "valid embedded cutoff stays clean")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        detp = _det(td, {"cutoff_utc": "2024-03-02T00:00:00Z", "scenarios": {"s": _sc([], [])}})
        out = td / "impact.json"
        _run([detp], dp, out)
        r = _scen(json.loads(out.read_text(encoding="utf-8")))["s"]
        _check(r["verdict"] == "UNDETERMINABLE" and "cutoff_mismatch_with_details_embedded_cutoff" in r["undeterminable_reasons"], "mismatch reason kept")
    print("EMBEDDED CUTOFF: invalid / non-string / empty -> UNDETERMINABLE, no abort; valid and mismatch semantics kept")


def test_missing_funding_events_not_list_is_undeterminable():
    """v1.20 item 2."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        scen = {}
        for k, v in (("int", 5), ("dict", {"inst_id": "AAA-USDT-SWAP", "ts_ms": T0}), ("str", "oops"), ("true", True)):
            scen[k] = _sc([], [], missing_funding_events_all=v)
        scen["ok_list"] = _sc([], [], missing_funding_events_all=[])
        detp = _det(td, {"scenarios": scen})
        out = td / "impact.json"
        try:
            rc = _run([detp], dp, out)
        except Exception as exc:
            raise AssertionError("SYNTHETIC_TEST_FAIL: non-list missing_funding_events_all aborted the assessment: %s: %s" % (type(exc).__name__, exc))
        a = _scen(json.loads(out.read_text(encoding="utf-8")))
        for k in ("int", "dict", "str", "true"):
            _check(a[k]["verdict"] == "UNDETERMINABLE" and "missing_funding_events_not_a_list" in a[k]["undeterminable_reasons"], "%s must be UNDETERMINABLE: %r" % (k, a[k]))
        _check(a["ok_list"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "valid empty list stays clean")
    print("MISSING EVENTS: non-list missing_funding_events_all -> UNDETERMINABLE per scenario, no abort")


def test_write_safety_wording():
    """v1.20 item 3: no 'checked before the rename' claim; no absolute concurrency guarantee."""
    doc = mod.__doc__ or ""
    _check("before the rename" not in doc, "docstring must not claim a re-check before the rename")
    _check("second" in doc and "before the .tmp is written" in doc, "docstring states the real second pre-write check")
    _check("does NOT guarantee" in doc and "concurrent" in doc, "docstring disclaims concurrent-change guarantee")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dp = _delta(td, ["AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8)])
        detp = _det(td, {"scenarios": {"s": _sc([], [])}})
        out = td / "impact.json"
        _run([detp], dp, out)
        r = json.loads(out.read_text(encoding="utf-8"))
        ws = r.get("write_safety", "")
        _check("no guarantee" in ws and "single-writer" in ws, "report carries the write-safety statement: %r" % ws)
    print("WORDING: second pre-write check described accurately; no concurrency guarantee claimed")


def main():
    tests = [test_legacy_semantics, test_out_tmp_aliases_input, test_existing_tmp_and_symlink_refused,
             test_open_at_end_bound_to_cutoff, test_missing_evidence_is_undeterminable,
             test_same_basename_not_overwritten, test_conflicting_delta_not_clean,
             test_invalid_embedded_cutoff_is_undeterminable, test_missing_funding_events_not_list_is_undeterminable,
             test_write_safety_wording]
    failed = 0
    for t in tests:
        try:
            t()
            print("RESULT %s: PASS" % t.__name__)
        except Exception:
            failed += 1
            print("RESULT %s: FAIL" % t.__name__)
            traceback.print_exc(limit=2, file=sys.stdout)
    if failed:
        print("IMPACT_SCOPE_SYNTHETIC_TESTS_FAILED:", failed)
        return 1
    print("ALL_IMPACT_SCOPE_V1_19_SYNTHETIC_TESTS_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
