#!/usr/bin/env python3
"""Synthetic test: a month that only shows a constant 2H interval.

Usage (from the repository root):
    python3 research/funding_sources_nonh8_v1_25/test_2h_classification_v1_25.py <path-to-generator-script>

Old logic (v1.23, commit 3280b7a6): analyze_month only recognised 1H/4H/8H, so a
constant 2H month fell into a fallback that picked a 1H base. It was labelled
not_determinable_internal_gaps with inferred_interval=1H. That is wrong: a 2H grid
being consistent with a 1H grid does not mean 1H slots should exist and are missing.

New logic (v1.25) keeps the observed 2H interval, marks the official schedule
unknown, and only writes inferred_interval for a single constant observed gap.

All data here is synthetic. No network access, no real rates.
"""
import importlib.util
import os
import sys
from datetime import datetime, timedelta, timezone

HOUR_MS = 3600 * 1000


def load(path):
    spec = importlib.util.spec_from_file_location("gen_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ms(dt):
    return int(dt.timestamp() * 1000)


def grid(start_utc, step_h, count):
    s = ms(start_utc)
    return [s + i * step_h * HOUR_MS for i in range(count)]


def main(path):
    mod = load(path)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))

    # CST 2025-04 = 2025-03-31T16:00Z .. 2025-04-30T16:00Z (exclusive); fully inside the window.
    open_utc = datetime(2025, 3, 31, 16, 0, tzinfo=timezone.utc)

    # Case A: constant 2H for the full CST month (360 slots).
    a_times = grid(open_utc, 2, 360)
    a = mod.analyze_month("SYNTH-USDT-SWAP", "2025-04", a_times, [])
    print(f"A: observed={a['observed_intervals']!r} status={a['denominator_status']!r} "
          f"inferred_interval={a['inferred_interval']!r} expected={a['inferred_expected_count']!r}")
    check("A1 observed interval stays 2H", a["observed_intervals"] == "2H", a["observed_intervals"])
    check("A2 not labelled internal_gaps", a["denominator_status"] != "not_determinable_internal_gaps", a["denominator_status"])
    check("A3 inferred_interval is not 1H", a["inferred_interval"] != "1H", a["inferred_interval"])
    check("A4 inferred_interval is 2H (observed constant)", a["inferred_interval"] == "2H", a["inferred_interval"])
    check("A5 status is inferred constant full month, nonstandard interval",
          a["denominator_status"] == "inferred_constant_full_month_nonstandard_interval", a["denominator_status"])
    check("A6 inferred expected count is 360", a["inferred_expected_count"] == "360", a["inferred_expected_count"])
    check("A7 denominator is not official", a["denominator_is_official"] == "false", a["denominator_is_official"])
    check("A8 official schedule marked unknown",
          a.get("official_schedule_status") == "unknown_no_official_schedule_source_used", str(a.get("official_schedule_status")))

    # Case B: control, constant 4H for the full month (180 slots). Must be unchanged.
    b = mod.analyze_month("SYNTH-USDT-SWAP", "2025-04", grid(open_utc, 4, 180), [])
    print(f"B: observed={b['observed_intervals']!r} status={b['denominator_status']!r} "
          f"inferred_interval={b['inferred_interval']!r} expected={b['inferred_expected_count']!r}")
    check("B1 4H control observed 4H", b["observed_intervals"] == "4H")
    check("B2 4H control status inferred_constant_full_month", b["denominator_status"] == "inferred_constant_full_month")
    check("B3 4H control expected 180", b["inferred_expected_count"] == "180")

    # Case C: 2H with one slot missing -> two gap sizes, not constant. No 1H may be inferred.
    c_times = grid(open_utc, 2, 360)
    del c_times[100]
    c = mod.analyze_month("SYNTH-USDT-SWAP", "2025-04", c_times, [])
    print(f"C: observed={c['observed_intervals']!r} status={c['denominator_status']!r} "
          f"inferred_interval={c['inferred_interval']!r}")
    check("C1 not constant: inferred_interval is not 1H", c["inferred_interval"] != "1H", c["inferred_interval"])
    check("C2 not constant: no inferred expected count", c["inferred_expected_count"] == "", c["inferred_expected_count"])

    # Case D: constant 2H but listed mid-month (shorter span). Observed 2H, not internal_gaps.
    d_start = datetime(2025, 4, 18, 16, 0, tzinfo=timezone.utc)
    d = mod.analyze_month("SYNTH-USDT-SWAP", "2025-04", grid(d_start, 2, 144), [])
    print(f"D: observed={d['observed_intervals']!r} status={d['denominator_status']!r} "
          f"inferred_interval={d['inferred_interval']!r}")
    check("D1 mid-month listing: observed interval stays 2H", d["observed_intervals"] == "2H", d["observed_intervals"])
    check("D2 mid-month listing: not internal_gaps", d["denominator_status"] != "not_determinable_internal_gaps", d["denominator_status"])
    check("D3 mid-month listing: span shorter than month",
          d["denominator_status"] == "not_determinable_span_shorter_than_month", d["denominator_status"])
    check("D4 mid-month listing: inferred_interval is not 1H", d["inferred_interval"] != "1H", d["inferred_interval"])

    # Case E (v1.25 only): raw-vs-snap evidence on synthetic rows. Skipped if absent.
    if hasattr(mod, "time_evidence"):
        raw1 = ms(open_utc) + 5000                      # +5 s offset
        raw2 = ms(open_utc) + 20000                     # +20 s, same snapped hour: collision
        rows = [(raw1, "0.0001"), (raw2, "0.0002"), (ms(open_utc) + 2 * HOUR_MS, "0.0001")]
        ev = mod.time_evidence(rows, "2025-04")
        check("E1 snap collision detected", ev["snap_collision_keys"] == 1, str(ev["snap_collision_keys"]))
        check("E2 snap collision with different rates detected", ev["snap_collision_diff_rate_keys"] == 1, str(ev["snap_collision_diff_rate_keys"]))
        check("E3 non-zero offsets counted", ev["rows_nonzero_offset"] == 2, str(ev["rows_nonzero_offset"]))
        check("E4 raw basis keeps both raw times", len(ev["raw_times"]) == 3, str(len(ev["raw_times"])))
        check("E5 snap basis collapses them", len(ev["snap_times"]) == 2, str(len(ev["snap_times"])))
    else:
        print("SKIP  E raw-vs-snap evidence (function not present in this version)")

    failed = [n for n, ok in results if not ok]
    print(f"SUMMARY checks={len(results)} passed={len(results) - len(failed)} failed={len(failed)}")
    if failed:
        print("FAILED: " + ", ".join(failed))
    print("RESULT " + ("PASS" if not failed else "FAIL"))
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: test_2h_classification_v1_25.py <generator-script-path>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
