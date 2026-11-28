#!/usr/bin/env python3
# Publishable compiler for BACKTEST-READINESS-01 v1.25
# (correction of v1.23 non-8H completeness unknowns).
# Local data locations are relative/config constants - set V125_* environment
# variables or edit the path constants before running.
# This file contains no host absolute paths and no secrets.
# OFFLINE ONLY: reads already-saved files; never makes a network request.

"""BACKTEST-READINESS-01 v1.25 - correction of the v1.23 non-8H unknowns.

Offline only. No refetch of any verified ZIP/REST, no backtest, no zero-fill,
no interpolation, no change to any rate, no universe or window change. The v1.23
files are kept unchanged; this writes new v1.25 files.

Fixes (ChatGPT v1.25):
1. analyze_month recognised only 1H/4H/8H. A single constant observed 2H
   interval fell into a fallback that chose a 1H base, labelling the month
   internal_gaps with inferred_interval=1H. v1.25 keeps the observed interval
   (2H or any whole-hour gap), marks the official schedule unknown and writes
   inferred_interval only for a single constant observed gap. interval_change_visible
   is an observed gap-size change only, not proof of an official interval change.
2. v1.23 snapped raw funding times to the hour (no tolerance) before de-duplication.
   v1.25 reports raw-basis and snap-basis crossing counts separately and records
   raw-vs-snapped offsets, cross-month differences and snap collisions (including
   same key with different rates) from the saved raw timestamps. Where no raw
   timestamps are saved the fields are "unknown".

No official settlement-schedule source has been used; every interval and
denominator is inferred, not verified. Inventory complete=true means passed per
that batch's source and comparison scope only. Self-run checks are team execution
evidence, not ChatGPT runtime certification.

FIB-4H-LONG-V3 remains NO-GO; live_approved is false.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

OUT = os.environ.get("V125_OUT", "funding_sources_nonh8_v1_25")
REPO = os.environ.get("V125_REPO", ".")
RESEARCH = os.environ.get("V125_RESEARCH", os.path.join(REPO, "research"))
INV_R5 = os.environ.get(
    "V125_INV",
    os.path.join(RESEARCH, "funding_delta_v1_11_b3c", "funding_month_inventory_v1_11_r5.csv"),
)
START_UTC = os.environ.get("V125_START_UTC", "")
OLD_CSV = os.environ.get(
    "V125_V123_CSV",
    os.path.join(RESEARCH, "funding_sources_nonh8_v1_23", "nonh8_completeness_unknowns_v1_23.csv"),
)
OLD_SCRIPT = os.environ.get(
    "V125_V123_SCRIPT",
    os.path.join(RESEARCH, "funding_sources_nonh8_v1_23", "build_sources_nonh8_v1_23_public.py"),
)

WIN_LO = 1672531200000  # 2023-01-01T00:00:00Z
WIN_HI = 1795694400000  # 2026-11-26T12:00:00Z inclusive
HOUR_MS = 3600 * 1000
EIGHT_H_MS = 8 * HOUR_MS
CST = timezone(timedelta(hours=8))

CDN_TMPL = (
    "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/"
    "{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip"
)
REST_TMPL = (
    "https://www.okx.com/api/v5/public/funding-rate-history"
    "?instId={INST}&after={AFTER}&limit={LIMIT}"
)

SPECIAL_NULL = {
    ("OL-USDT-SWAP", "2025-10"): "official_rate_null 1/85 literal None in official monthly ZIP",
    ("ZK-USDT-SWAP", "2024-06"): "official_rate_null 1/54 literal None in official monthly ZIP",
}
SPECIAL_PENDING = {
    ("RVN-USDT-SWAP", "2026-11"): "pending_check / rest_51001_instrument_not_listed",
}
SPECIAL_404 = {
    ("CC-USDT-SWAP", "2025-10"): "official_unavailable / 404_reason_unknown",
    ("INJ-USDT-SWAP", "2023-11"): "official_unavailable / 404_reason_unknown",
    ("MEGA-USDT-SWAP", "2026-04"): "official_unavailable / 404_reason_unknown",
    ("ORDER-USDT-SWAP", "2025-09"): "official_unavailable / 404_reason_unknown",
}

ZIP_DIRS = [
    ("v1.10", "funding_delta_v1_10/official_monthly_zips"),
    ("v1.11_b1", "funding_delta_v1_11_b1/official_monthly_zips"),
    ("v1.11_b2", "funding_delta_v1_11_b2/official_monthly_zips"),
    ("v1.11_b3a", "funding_delta_v1_11_b3a/official_monthly_zips"),
    ("v1.11_b3b", "funding_delta_v1_11_b3b/official_monthly_zips"),
    ("v1.11_b3c", "funding_delta_v1_11_b3c/official_monthly_zips"),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(f"[{utc_now_iso()}] {msg}", flush=True)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def iso(ms: int, millis: bool = False) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    if millis:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(ms % 1000):03d}Z"
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_cst_date(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=CST)
    return dt.strftime("%Y-%m-%d")


def snap(ms: int) -> int:
    return int(round(ms / float(HOUR_MS))) * HOUR_MS


def rate_status(value: Any) -> str:
    if value is None:
        return "python_none"
    text = str(value).strip()
    if text == "":
        return "empty"
    low = text.lower()
    if low == "none":
        return "literal_none"
    if low in {"null", "na", "n/a"}:
        return f"literal_{low.replace('/', '_')}"
    if low in {"nan"}:
        return "nan"
    if low in {"inf", "+inf", "infinity", "+infinity"}:
        return "inf"
    if low in {"-inf", "-infinity"}:
        return "neg_inf"
    try:
        number = float(text)
    except ValueError:
        return "non_numeric"
    if math.isnan(number):
        return "nan"
    if not math.isfinite(number):
        return "inf" if number > 0 else "neg_inf"
    return "numeric"


def is_numeric_rate(value: Any) -> bool:
    return rate_status(value) == "numeric"


def month_cst_from_ms(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=CST)
    return f"{dt.year:04d}-{dt.month:02d}"


def cst_month_bounds(ym: str) -> tuple[int, int]:
    year, month = map(int, ym.split("-"))
    start = datetime(year, month, 1, tzinfo=CST)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=CST)
    else:
        end = datetime(year, month + 1, 1, tzinfo=CST)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def month_fully_in_window(month_lo: int, month_hi: int) -> bool:
    return month_lo >= WIN_LO and (month_hi - 1) <= WIN_HI


def grid_points(lo: int, hi_exclusive: int, interval_ms: int) -> list[int]:
    """Hour-aligned grid points t with t % interval_ms == 0, lo <= t < hi_exclusive, clipped to window."""
    a = max(lo, WIN_LO)
    b = min(hi_exclusive - 1, WIN_HI)
    if a > b:
        return []
    rem = a % interval_ms
    first = a if rem == 0 else a + (interval_ms - rem)
    out = []
    t = first
    while t <= b:
        out.append(t)
        t += interval_ms
    return out


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def rel_research(path: str) -> str:
    path = os.path.abspath(path)
    root = os.path.abspath(RESEARCH)
    if path.startswith(root + os.sep):
        return "research/" + path[len(root) + 1 :].replace("\\", "/")
    base = os.path.basename(path)
    return base




def interval_label(hours: float) -> str:
    if hours == 1:
        return "1H"
    if hours == 4:
        return "4H"
    if hours == 8:
        return "8H"
    if hours == int(hours) and hours > 0:
        return f"{int(hours)}H"
    return f"{hours}H"



def is_utc_month_end_crossing(ms: int) -> bool:
    """True iff the UTC instant is on or after 16:00Z on the last UTC day of a month.

    Those instants fall in the *next* CST month (UTC+8) and in the *current* UTC
    month. An 8H contract has at most one such official slot per month (16:00Z).
    A 4H contract may have 16:00Z and 20:00Z; a 1H contract may have 16:00Z
    through 23:00Z (the last eight hours). Count observed settlements one by
    one; do not assume the typological count.
    """
    return month_cst_from_ms(ms) != datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m")


def annotate_cst_utc_boundary(rec: dict[str, Any], ym: str, times: list[int], notes: list[str]) -> None:
    crossings = [ts for ts in times if is_utc_month_end_crossing(ts)]
    rec["boundary_crossing_settlement_count"] = len(crossings)
    rec["boundary_crossing_times_utc"] = ";".join(iso(ts) for ts in crossings)
    month_lo, month_hi = cst_month_bounds(ym)
    # month_hi is next CST month start = last UTC day of this calendar month at 16:00Z.
    # Those outgoing slots belong to the *next* CST month, not this row.
    outgoing_possible = month_hi <= WIN_HI
    window_start_truncates_cst_open = month_lo < WIN_LO
    window_end_truncates = (month_hi - 1) > WIN_HI
    fully = rec.get("month_fully_inside_research_window") == "true"
    rec["partial_month"] = "false" if fully else "true"
    rec["month_end_crossing_in_window"] = "true" if outgoing_possible else "false"

    if window_end_truncates or ym == "2026-11":
        effect = "partial_month_no_month_end_crossing"
        rec["month_end_crossing_in_window"] = "false"
        rec["partial_month"] = "true"
        notes.append(
            "This CST month is a partial month: the research window ends "
            "2026-11-26T12:00:00Z, so there is no month-end UTC-day 16:00Z+ "
            "crossing in the saved data."
        )
        if crossings:
            notes.append(
                "Incoming opening crossings (previous UTC month last day 16:00Z+) "
                "are still counted one by one; only the month-end outgoing crossing "
                "is absent because the window ends mid-month."
            )
    elif window_start_truncates_cst_open:
        effect = "window_start_truncates_cst_month_open"
        rec["partial_month"] = "true"
        notes.append(
            "The CST month opens at the previous UTC day 16:00Z, which is before "
            "WIN_LO 2023-01-01T00:00:00Z, so the usual opening boundary-crossing "
            "slots are outside the research window. A UTC January bucket starts "
            "at the window origin; CST vs UTC completeness of this month can differ."
        )
    elif crossings:
        effect = "has_opening_boundary_crossings"
        notes.append(
            "Counted one by one from saved official timestamps (snap-to-hour basis in this function; raw basis is reported in separate columns). Typologically, "
            "an 8H contract has exactly one such slot (16:00Z); a 4H contract may "
            "have several in the last 8 hours (16:00Z, 20:00Z); a 1H contract may "
            "have 16:00Z through 23:00Z. These instants are in this CST month and "
            "in the previous UTC month, so a UTC-month completeness bucket can "
            "disagree with a CST-month bucket."
        )
    elif outgoing_possible:
        effect = "utc_month_end_slots_belong_to_next_cst_month"
        notes.append(
            "No opening boundary-crossing settlement was observed in this CST month, "
            "but last-UTC-day 16:00Z+ slots of this calendar month belong to the "
            "next CST month. CST vs UTC month-end completeness can still differ."
        )
    else:
        effect = "none"

    may_differ = (
        len(crossings) > 0
        or outgoing_possible
        or window_start_truncates_cst_open
        or window_end_truncates
    )
    rec["cst_vs_utc_boundary_effect"] = effect
    rec["cst_vs_utc_completeness_may_differ"] = "true" if may_differ else "false"
    if may_differ:
        notes.append(
            "Funding completeness is bucketed by CST (UTC+8) month; performance "
            "month buckets are UTC months, so month boundaries can misalign "
            "(復盤 Issue #1 comment 7239320542)."
        )



def parse_zip_rows(inst: str, blob: bytes) -> list[tuple[int, str]]:
    """All rows as (raw funding_time ms, funding_rate text). No snapping here."""
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        if not names:
            raise ValueError("zip has no entries")
        txt = zf.read(names[0]).decode()
    out: list[tuple[int, str]] = []
    for r in csv.DictReader(io.StringIO(txt)):
        name = (r.get("instrument_name") or "").strip()
        if name and name != inst:
            raise ValueError(f"instrument_name mismatch: {name!r} != {inst!r}")
        raw_rate = r.get("funding_rate")
        out.append((int(r["funding_time"]), "" if raw_rate is None else str(raw_rate)))
    return out


def parse_rest_rows(obj: dict[str, Any]) -> tuple[list[tuple[int, str]], str]:
    """All parsed-JSON REST rows as (raw fundingTime ms, rate text) and a status."""
    out: list[tuple[int, str]] = []
    status = "ok"
    pages = obj.get("pages") or []
    if not pages:
        code = str(obj.get("code") or obj.get("response", {}).get("code") or "")
        if code and code != "0":
            return [], f"rest_code_{code}"
    for page in pages:
        http = page.get("http")
        resp = page.get("response") or {}
        code = str(resp.get("code") or "")
        if http not in (None, 200) or (code and code != "0"):
            status = f"http_{http}_code_{code or 'unknown'}"
            continue
        for rec in resp.get("data") or []:
            rate = rec.get("realizedRate")
            if rate is None or str(rate).strip() == "":
                rate = rec.get("fundingRate")
            out.append((int(rec["fundingTime"]), "" if rate is None else str(rate)))
    return out, status


def month_utc_from_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m")


def is_crossing(ms: int) -> bool:
    return month_cst_from_ms(ms) != month_utc_from_ms(ms)


def time_evidence(rows: list[tuple[int, str]], ym: str) -> dict[str, Any]:
    """Raw-basis vs snap-basis evidence for one source file / inventory month.

    snap basis (as in v1.23): snap() to the nearest hour, no tolerance, keep
    snapped ts inside the research window and inside CST month ym, de-duplicate.
    raw basis: keep raw ts inside the window and inside CST month ym, de-duplicate.
    """
    finite = [(raw, rate) for raw, rate in rows if is_numeric_rate(rate)]
    snap_times: set[int] = set()
    raw_times: set[int] = set()
    off_hist: Counter[int] = Counter()
    nonzero = 0
    max_abs = 0
    xm_cst = 0
    xm_utc = 0
    excl_snap = 0
    excl_raw = 0
    groups: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for raw, rate in finite:
        s = snap(raw)
        off = raw - s
        off_hist[off] += 1
        if off != 0:
            nonzero += 1
            max_abs = max(max_abs, abs(off))
        if month_cst_from_ms(raw) != month_cst_from_ms(s):
            xm_cst += 1
        if month_utc_from_ms(raw) != month_utc_from_ms(s):
            xm_utc += 1
        if WIN_LO <= s <= WIN_HI and month_cst_from_ms(s) == ym:
            snap_times.add(s)
        else:
            excl_snap += 1
        if WIN_LO <= raw <= WIN_HI and month_cst_from_ms(raw) == ym:
            raw_times.add(raw)
        else:
            excl_raw += 1
        groups[s].append((raw, rate))
    coll_keys = 0
    coll_same_raw = 0
    coll_distinct_raw = 0
    coll_diff_rate = 0
    for s, lst in groups.items():
        if len(lst) < 2:
            continue
        coll_keys += 1
        if len({r for r, _ in lst}) > 1:
            coll_distinct_raw += 1
        else:
            coll_same_raw += 1
        vals = [float(x) for _, x in lst]
        if max(vals) - min(vals) > 1e-15:
            coll_diff_rate += 1
    snap_cross = sorted(t for t in snap_times if is_crossing(t))
    raw_cross = sorted(t for t in raw_times if is_crossing(t))
    return {
        "rows_total": len(rows),
        "rows_finite": len(finite),
        "rows_flagged": len(rows) - len(finite),
        "snap_times": sorted(snap_times),
        "raw_times": sorted(raw_times),
        "snap_cross": snap_cross,
        "raw_cross": raw_cross,
        "off_hist": off_hist,
        "rows_nonzero_offset": nonzero,
        "max_abs_offset_ms": max_abs,
        "rows_cross_month_cst": xm_cst,
        "rows_cross_month_utc": xm_utc,
        "rows_excluded_snap_basis": excl_snap,
        "rows_excluded_raw_basis": excl_raw,
        "snap_collision_keys": coll_keys,
        "snap_collision_same_raw_dup_keys": coll_same_raw,
        "snap_collision_distinct_raw_keys": coll_distinct_raw,
        "snap_collision_diff_rate_keys": coll_diff_rate,
        "raw_to_snap_set_equal": "true"
        if {snap(t) for t in raw_times} == snap_times
        else "false",
    }


def analyze_month(inst: str, ym: str, times: list[int], extra_notes: list[str]) -> dict[str, Any]:
    """v1.25 classification (observed intervals only; official schedule unknown).

    Fix vs v1.23: any single constant observed gap (including 2H or any other
    whole-hour interval) is kept as the observed interval and is NOT folded into
    a smaller base interval. inferred_interval is assigned only for a single
    constant observed gap. interval_change_visible means an observed gap-size
    change in the saved data only; it is not proof of an official interval change.
    """
    month_lo, month_hi = cst_month_bounds(ym)
    full_month = month_fully_in_window(month_lo, month_hi)
    n = len(times)
    n_8h = sum(1 for t in times if t % EIGHT_H_MS == 0)
    first = times[0] if times else None
    last = times[-1] if times else None
    rec: dict[str, Any] = {
        "inst_id": inst,
        "month_cst": ym,
        "observed_settlement_count": n,
        "observed_8h_grid_count": n_8h,
        "observed_non_8h_count": n - n_8h,
        "observed_intervals": "",
        "unique_gap_hours": "",
        "nonstandard_gap_hours": "",
        "interval_change_visible": "false",
        "interval_change_at_utc": "",
        "interval_change_at_cst_date": "",
        "first_settlement_utc": iso(first) if first is not None else "",
        "last_settlement_utc": iso(last) if last is not None else "",
        "month_start_utc": iso(month_lo),
        "month_end_exclusive_utc": iso(month_hi),
        "month_fully_inside_research_window": "true" if full_month else "false",
        "denominator_status": "",
        "inferred_interval": "",
        "inferred_expected_count": "",
        "denominator_is_official": "false",
        "official_schedule_status": "unknown_no_official_schedule_source_used",
        "boundary_crossing_settlement_count": 0,
        "boundary_crossing_times_utc": "",
        "month_end_crossing_in_window": "",
        "partial_month": "",
        "cst_vs_utc_boundary_effect": "",
        "cst_vs_utc_completeness_may_differ": "false",
        "notes": "",
    }
    notes = list(extra_notes)

    if n == 0:
        rec["denominator_status"] = "not_determinable_no_numeric_settlements"
        annotate_cst_utc_boundary(rec, ym, times, notes)
        rec["notes"] = "; ".join(notes)
        return rec
    if n == 1:
        rec["observed_intervals"] = "unknown_single_point"
        rec["denominator_status"] = "not_determinable_insufficient_points"
        annotate_cst_utc_boundary(rec, ym, times, notes)
        rec["notes"] = "; ".join(notes)
        return rec

    gaps_h = [(times[i] - times[i - 1]) / HOUR_MS for i in range(1, n)]
    uniq = sorted(set(gaps_h))

    def fmt(g: float) -> str:
        return str(int(g)) if float(g).is_integer() else str(g)

    rec["unique_gap_hours"] = ",".join(fmt(g) for g in uniq)
    known = {1.0, 4.0, 8.0}
    nonstd = [g for g in uniq if g not in known]
    rec["nonstandard_gap_hours"] = ",".join(fmt(g) for g in nonstd)

    change_utc: list[str] = []
    change_date: list[str] = []
    for i in range(1, len(gaps_h)):
        if gaps_h[i] != gaps_h[i - 1]:
            rec["interval_change_visible"] = "true"
            change_utc.append(iso(times[i + 1]))
            change_date.append(iso_cst_date(times[i + 1]))
    rec["interval_change_at_utc"] = ";".join(change_utc)
    rec["interval_change_at_cst_date"] = ";".join(dict.fromkeys(change_date))

    runs: list[tuple[float, int]] = []
    run_v, run_n = gaps_h[0], 1
    for g in gaps_h[1:]:
        if g == run_v:
            run_n += 1
        else:
            runs.append((run_v, run_n))
            run_v, run_n = g, 1
    runs.append((run_v, run_n))

    def check_full(interval_h: float) -> tuple[str, str]:
        interval_ms = int(interval_h * HOUR_MS)
        expected_pts = grid_points(month_lo, month_hi, interval_ms)
        if not full_month:
            return "not_determinable_window_truncated", ""
        if not expected_pts:
            return "not_determinable_window_truncated", ""
        if first == expected_pts[0] and last == expected_pts[-1] and n == len(expected_pts):
            return "inferred_constant_full_month", str(len(expected_pts))
        span_n = int(round((last - first) / interval_ms)) + 1
        if n == span_n:
            return "not_determinable_span_shorter_than_month", ""
        return "not_determinable_internal_gaps", ""

    status = ""
    inferred_i = ""
    expected = ""
    if len(uniq) == 1:
        g = uniq[0]
        rec["observed_intervals"] = interval_label(g)
        inferred_i = interval_label(g)
        status, expected = check_full(g)
        if g not in known:
            # Observed constant whole-hour interval that is not 1H/4H/8H (e.g. 2H).
            if status == "inferred_constant_full_month":
                status = "inferred_constant_full_month_nonstandard_interval"
            notes.append(
                f"Observed a single constant {interval_label(g)} interval in the saved data. "
                f"{interval_label(g)} is not one of the 1H/4H/8H intervals the v1.23 logic "
                "recognised; v1.23 folded it into a 1H base and labelled it internal_gaps "
                "with inferred_interval=1H. That was a classification error. The observed "
                f"{interval_label(g)} interval is kept; the official settlement schedule is "
                "unknown (no official schedule source was used). Any expected count here is "
                "an inferred observed-assumption only."
            )
    elif len(runs) == 2 and all(v in known for v, _ in runs):
        rec["observed_intervals"] = "+".join(interval_label(v) for v, _ in runs)
        status = "not_determinable_interval_change"
    else:
        bases = [b for b in (1.0, 4.0, 8.0) if all(abs(g / b - round(g / b)) < 1e-9 for g in uniq)]
        labels = [interval_label(b) for b in (1.0, 4.0, 8.0) if any(abs(g - b) < 1e-9 for g in uniq)]
        rec["observed_intervals"] = "+".join(labels + [interval_label(g) for g in nonstd]) or "irregular"
        if bases:
            status = (
                "not_determinable_interval_change_or_gaps"
                if rec["interval_change_visible"] == "true"
                else "not_determinable_internal_gaps"
            )
        else:
            status = "not_determinable_irregular_gaps"
        # v1.25: no inferred interval for non-constant months (v1.23 wrote the
        # smallest divisible base, usually 1H, which was not an observation).
        inferred_i = ""
        if nonstd:
            notes.append(
                "Observed gap hours include non-1H/4H/8H values "
                f"({rec['nonstandard_gap_hours']}); no inferred interval is assigned and the "
                "status is unchanged from v1.23."
            )

    rec["denominator_status"] = status
    rec["inferred_interval"] = inferred_i
    rec["inferred_expected_count"] = expected
    rec["denominator_is_official"] = "false"
    if rec["interval_change_visible"] == "true":
        notes.append(
            "interval_change_visible=true means a gap-size change is observed in the "
            "saved data only; it is not proof of an official interval change."
        )
    if status in ("inferred_constant_full_month", "inferred_constant_full_month_nonstandard_interval"):
        notes.append(
            "Expected count is inferred from the observed constant interval across the "
            "full CST month (inferred_constant_full_month). No official "
            "settlement-schedule source was used; this denominator is not officially verified."
        )
    else:
        notes.append(
            "No official settlement-schedule source was used; an expected-count "
            "denominator is not determinable (or not a full-month constant interval) "
            "from the saved data alone."
        )
    annotate_cst_utc_boundary(rec, ym, times, notes)
    rec["notes"] = "; ".join(notes)
    return rec


UNKNOWN_FIELDS = [
    "record_kind", "inst_id", "month_cst", "inventory_class", "inventory_sub_reason",
    "inventory_complete", "official_source", "official_file",
    "observed_settlement_count", "observed_8h_grid_count", "observed_non_8h_count",
    "observed_intervals", "unique_gap_hours", "nonstandard_gap_hours",
    "interval_change_visible", "interval_change_at_utc", "interval_change_at_cst_date",
    "first_settlement_utc", "last_settlement_utc", "month_start_utc", "month_end_exclusive_utc",
    "month_fully_inside_research_window", "denominator_status", "inferred_interval",
    "inferred_expected_count", "denominator_is_official", "official_schedule_status",
    "boundary_crossing_snap_count", "boundary_crossing_snap_times_utc",
    "boundary_crossing_raw_count", "boundary_crossing_raw_times_utc",
    "boundary_crossing_raw_minus_snap", "time_basis_status",
    "raw_rows_finite", "raw_rows_nonzero_offset", "raw_max_abs_offset_ms",
    "raw_rows_cross_month_cst", "raw_rows_cross_month_utc",
    "raw_rows_excluded_snap_basis", "raw_rows_excluded_raw_basis", "raw_to_snap_set_equal",
    "snap_collision_keys", "snap_collision_same_raw_dup_keys",
    "snap_collision_distinct_raw_keys", "snap_collision_diff_rate_keys",
    "month_end_crossing_in_window", "partial_month", "cst_vs_utc_boundary_effect",
    "cst_vs_utc_completeness_may_differ", "notes",
]

EIGHT_MONTHS = [
    ("API3-USDT-SWAP", "2025-04"), ("AUCTION-USDT-SWAP", "2025-04"),
    ("KAITO-USDT-SWAP", "2025-04"), ("LAYER-USDT-SWAP", "2025-04"),
    ("LAYER-USDT-SWAP", "2025-03"), ("BARD-USDT-SWAP", "2025-09"),
    ("SOPH-USDT-SWAP", "2025-08"), ("SYRUP-USDT-SWAP", "2025-08"),
]


def write_csv(path: str, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def md_escape(s: Any) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(md_escape(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def count_rows(counter: Counter) -> list[dict[str, Any]]:
    return [{"key": k, "count": v} for k, v in counter.most_common()]


def load_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    start_utc = START_UTC or utc_now_iso()
    log(f"v1.25 start_utc={start_utc}")
    log("OFFLINE correction; no network fetches.")

    inv_rows = load_csv(INV_R5)
    inv_sha, inv_bytes = sha256_file(INV_R5)
    if len(inv_rows) != 7536:
        raise SystemExit(f"expected 7536 inventory rows, got {len(inv_rows)}")
    old_csv_sha, old_csv_bytes = sha256_file(OLD_CSV)
    old_script_sha, old_script_bytes = sha256_file(OLD_SCRIPT)
    old_rows = load_csv(OLD_CSV)
    log(f"inventory r5 sha={inv_sha}; v1.23 unknowns csv rows={len(old_rows)} sha={old_csv_sha}")

    zip_index: dict[tuple[str, str], tuple[str, str]] = {}
    for batch, rel in ZIP_DIRS:
        d = os.path.join(RESEARCH, rel)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".zip") or "-fundingrates-" not in name:
                continue
            inst, ym = name[:-4].split("-fundingrates-")
            if (inst, ym) in zip_index:
                raise SystemExit(f"duplicate ZIP for {(inst, ym)}")
            zip_index[(inst, ym)] = (rel + "/" + name, os.path.join(d, name))
    rest_dir = os.path.join(RESEARCH, "funding_delta_v1_11_b2", "rest_2026_11")
    log(f"unique official ZIPs indexed: {len(zip_index)}")

    evid: dict[tuple[str, str], dict[str, Any]] = {}
    meta_by: dict[tuple[str, str], dict[str, Any]] = {}
    glob_first: dict[tuple[str, int], tuple[int, float]] = {}
    file_ids: dict[tuple[str, str], int] = {}
    cross_file_keys = 0
    cross_file_diff_rate = 0
    cross_pair_kinds: Counter[str] = Counter()
    cross_pair_diff_by_kind: Counter[str] = Counter()
    file_kind: dict[int, str] = {}
    excl_by_reason: Counter[str] = Counter()
    off_hist_all: Counter[int] = Counter()
    totals = Counter()
    for r in inv_rows:
        inst, ym = r["inst_id"], r["month_cst"]
        key = (inst, ym)
        rows: list[tuple[int, str]] | None = None
        if key in zip_index:
            rel, path = zip_index[key]
            rows = parse_zip_rows(inst, open(path, "rb").read())
            meta_by[key] = {"official_source": "official_monthly_zip", "official_file": "research/" + rel}
            totals["rows_zip"] += len(rows)
        elif ym == "2026-11":
            fp = os.path.join(rest_dir, f"{inst}.json.gz")
            if os.path.isfile(fp):
                obj = json.loads(gzip.open(fp, "rt", encoding="utf-8").read())
                rows, _status = parse_rest_rows(obj)
                meta_by[key] = {
                    "official_source": "rest_parsed_json",
                    "official_file": rel_research(fp),
                }
                totals["rows_rest"] += len(rows)
        if rows is None:
            meta_by[key] = {"official_source": "none", "official_file": ""}
            evid[key] = {}
            continue
        ev = time_evidence(rows, ym)
        evid[key] = ev
        fid = file_ids.setdefault(key, len(file_ids))
        kind_src = meta_by[key]["official_source"]
        file_kind[fid] = "zip" if kind_src == "official_monthly_zip" else "rest"
        for raw, rate in rows:
            if not is_numeric_rate(rate):
                continue
            s0 = snap(raw)
            if WIN_LO <= s0 <= WIN_HI and month_cst_from_ms(s0) == ym:
                continue
            why = "before_window" if s0 < WIN_LO else "after_window" if s0 > WIN_HI else ("earlier_cst_month" if month_cst_from_ms(s0) < ym else "later_cst_month")
            excl_by_reason[file_kind[fid] + ":" + why] += 1
        off_hist_all.update(ev["off_hist"])
        for raw, rate in rows:
            if not is_numeric_rate(rate):
                continue
            gk = (inst, snap(raw))
            val = float(rate)
            if gk in glob_first:
                f0, v0 = glob_first[gk]
                if f0 != fid:
                    cross_file_keys += 1
                    pair = "-".join(sorted((file_kind[f0], file_kind[fid])))
                    cross_pair_kinds[pair] += 1
                    if abs(v0 - val) > 1e-15:
                        cross_file_diff_rate += 1
                        cross_pair_diff_by_kind[pair] += 1
            else:
                glob_first[gk] = (fid, val)
    log(f"parsed rows zip={totals['rows_zip']} rest={totals['rows_rest']}")

    inv_by = {(r["inst_id"], r["month_cst"]): r for r in inv_rows}
    special_keys = set(SPECIAL_NULL) | set(SPECIAL_PENDING) | set(SPECIAL_404)

    def build_row(key: tuple[str, str], kind: str, extra: list[str]) -> dict[str, Any]:
        inst, ym = key
        inv = inv_by[key]
        ev = evid.get(key) or {}
        times = ev.get("snap_times") or []
        rec = analyze_month(inst, ym, times, extra)
        rec["boundary_crossing_snap_count"] = rec.pop("boundary_crossing_settlement_count")
        rec["boundary_crossing_snap_times_utc"] = rec.pop("boundary_crossing_times_utc")
        meta = meta_by.get(key) or {}
        rec.update({
            "record_kind": kind,
            "inventory_class": inv.get("class") or "",
            "inventory_sub_reason": inv.get("sub_reason") or "",
            "inventory_complete": (inv.get("complete") or "").strip(),
            "official_source": meta.get("official_source") or "none",
            "official_file": meta.get("official_file") or "",
        })
        if ev:
            rc = ev["raw_cross"]
            rec.update({
                "boundary_crossing_raw_count": len(rc),
                "boundary_crossing_raw_times_utc": ";".join(iso(t) for t in rc),
                "boundary_crossing_raw_minus_snap": len(rc) - int(rec["boundary_crossing_snap_count"]),
                "time_basis_status": "evidence_from_saved_raw_timestamps",
                "raw_rows_finite": ev["rows_finite"],
                "raw_rows_nonzero_offset": ev["rows_nonzero_offset"],
                "raw_max_abs_offset_ms": ev["max_abs_offset_ms"],
                "raw_rows_cross_month_cst": ev["rows_cross_month_cst"],
                "raw_rows_cross_month_utc": ev["rows_cross_month_utc"],
                "raw_rows_excluded_snap_basis": ev["rows_excluded_snap_basis"],
                "raw_rows_excluded_raw_basis": ev["rows_excluded_raw_basis"],
                "raw_to_snap_set_equal": ev["raw_to_snap_set_equal"],
                "snap_collision_keys": ev["snap_collision_keys"],
                "snap_collision_same_raw_dup_keys": ev["snap_collision_same_raw_dup_keys"],
                "snap_collision_distinct_raw_keys": ev["snap_collision_distinct_raw_keys"],
                "snap_collision_diff_rate_keys": ev["snap_collision_diff_rate_keys"],
            })
        else:
            rec.update({
                "boundary_crossing_raw_count": "unknown",
                "boundary_crossing_raw_times_utc": "",
                "boundary_crossing_raw_minus_snap": "unknown",
                "time_basis_status": "unknown_no_saved_raw_timestamps",
                "raw_rows_finite": "unknown",
                "raw_rows_nonzero_offset": "unknown",
                "raw_max_abs_offset_ms": "unknown",
                "raw_rows_cross_month_cst": "unknown",
                "raw_rows_cross_month_utc": "unknown",
                "raw_rows_excluded_snap_basis": "unknown",
                "raw_rows_excluded_raw_basis": "unknown",
                "raw_to_snap_set_equal": "unknown",
                "snap_collision_keys": "unknown",
                "snap_collision_same_raw_dup_keys": "unknown",
                "snap_collision_distinct_raw_keys": "unknown",
                "snap_collision_diff_rate_keys": "unknown",
            })
        return rec

    unknown_rows: list[dict[str, Any]] = []
    for r in inv_rows:
        key = (r["inst_id"], r["month_cst"])
        times = (evid.get(key) or {}).get("snap_times") or []
        n_non = sum(1 for t in times if t % EIGHT_H_MS != 0)
        if n_non:
            extras = [SPECIAL_NULL[key]] if key in SPECIAL_NULL else []
            unknown_rows.append(build_row(key, "non8h_month", extras))
        elif key in special_keys:
            if key in SPECIAL_NULL:
                extras, kind = [SPECIAL_NULL[key]], "known_gap_official_rate_null"
            elif key in SPECIAL_PENDING:
                extras, kind = [SPECIAL_PENDING[key]], "known_gap_pending"
            else:
                extras, kind = [SPECIAL_404[key]], "known_gap_404"
            unknown_rows.append(build_row(key, kind, extras))
    unknown_rows.sort(key=lambda x: (x["inst_id"], x["month_cst"], x["record_kind"]))
    non8h = [x for x in unknown_rows if x["record_kind"] == "non8h_month"]
    specials = [x for x in unknown_rows if x["record_kind"] != "non8h_month"]
    log(f"unknown rows={len(unknown_rows)} non8h={len(non8h)} specials={len(specials)}")

    # ---- diff vs v1.23 (before/after) ----
    old_by = {(o["inst_id"], o["month_cst"], o["record_kind"]): o for o in old_rows}
    new_by = {(x["inst_id"], x["month_cst"], x["record_kind"]): x for x in unknown_rows}
    if set(old_by) != set(new_by):
        raise SystemExit("row key set differs from v1.23 unknowns file")
    cmp_fields = [
        "observed_settlement_count", "observed_intervals", "unique_gap_hours",
        "interval_change_visible", "interval_change_at_utc", "first_settlement_utc",
        "last_settlement_utc", "denominator_status", "inferred_interval", "inferred_expected_count",
    ]
    changed_rows: list[dict[str, Any]] = []
    field_change_counts: Counter[str] = Counter()
    unexpected_changes = 0
    snap_count_mismatch = 0
    for k in sorted(new_by):
        o, x = old_by[k], new_by[k]
        diffs = []
        for f in cmp_fields:
            if str(o.get(f, "")) != str(x.get(f, "")):
                diffs.append(f)
                field_change_counts[f] += 1
        if str(o.get("boundary_crossing_settlement_count", "")) != str(x["boundary_crossing_snap_count"]):
            snap_count_mismatch += 1
        if diffs:
            changed_rows.append({
                "inst_id": k[0], "month_cst": k[1], "record_kind": k[2],
                "changed_fields": ";".join(diffs),
                "old_observed_intervals": o["observed_intervals"],
                "new_observed_intervals": x["observed_intervals"],
                "old_denominator_status": o["denominator_status"],
                "new_denominator_status": x["denominator_status"],
                "old_inferred_interval": o["inferred_interval"],
                "new_inferred_interval": x["inferred_interval"],
                "old_inferred_expected_count": o["inferred_expected_count"],
                "new_inferred_expected_count": x["inferred_expected_count"],
            })
            allowed = {"denominator_status", "inferred_interval", "inferred_expected_count"}
            if set(diffs) - allowed:
                unexpected_changes += 1
    old_status = Counter(o["denominator_status"] for o in old_rows if o["record_kind"] == "non8h_month")
    new_status = Counter(x["denominator_status"] for x in non8h)
    old_inferred = Counter(o["inferred_interval"] for o in old_rows if o["record_kind"] == "non8h_month")
    new_inferred = Counter(x["inferred_interval"] for x in non8h)
    interval_counts = Counter(x["observed_intervals"] for x in non8h)
    nonstd_months = [x for x in non8h if x["nonstandard_gap_hours"]]
    nonstd_by_gap = Counter(x["nonstandard_gap_hours"] for x in nonstd_months)
    nonstd_by_status = Counter(x["denominator_status"] for x in nonstd_months)

    changed_csv = os.path.join(OUT, "nonh8_v1_25_vs_v1_23_changed_rows.csv")
    write_csv(changed_csv, [
        "inst_id", "month_cst", "record_kind", "changed_fields",
        "old_observed_intervals", "new_observed_intervals",
        "old_denominator_status", "new_denominator_status",
        "old_inferred_interval", "new_inferred_interval",
        "old_inferred_expected_count", "new_inferred_expected_count",
    ], changed_rows)

    # ---- eight months before/after ----
    eight_rows: list[dict[str, Any]] = []
    for inst, ym in EIGHT_MONTHS:
        o = old_by[(inst, ym, "non8h_month")]
        x = new_by[(inst, ym, "non8h_month")]
        eight_rows.append({
            "inst_id": inst, "month_cst": ym,
            "observed_settlements": x["observed_settlement_count"],
            "first_settlement_utc": x["first_settlement_utc"],
            "last_settlement_utc": x["last_settlement_utc"],
            "before_observed_intervals": o["observed_intervals"],
            "before_denominator_status": o["denominator_status"],
            "before_inferred_interval": o["inferred_interval"],
            "before_inferred_expected_count": o["inferred_expected_count"],
            "after_observed_intervals": x["observed_intervals"],
            "after_denominator_status": x["denominator_status"],
            "after_inferred_interval": x["inferred_interval"],
            "after_inferred_expected_count": x["inferred_expected_count"],
            "after_denominator_is_official": x["denominator_is_official"],
            "after_official_schedule_status": x["official_schedule_status"],
            "boundary_crossing_snap_count": x["boundary_crossing_snap_count"],
            "boundary_crossing_raw_count": x["boundary_crossing_raw_count"],
        })
    eight_csv = os.path.join(OUT, "eight_2h_months_before_after_v1_25.csv")
    write_csv(eight_csv, list(eight_rows[0].keys()), eight_rows)

    # ---- global time-basis evidence ----
    def bucket(off: int) -> str:
        a = abs(off)
        if a == 0:
            return "0"
        if a < 1000:
            return "1-999ms"
        if a < 10000:
            return "1-9s"
        if a < 60000:
            return "10-59s"
        return ">=60s"
    off_buckets: Counter[str] = Counter()
    for off, c in off_hist_all.items():
        off_buckets[bucket(off)] += c
    all_ev = [e for e in evid.values() if e]
    snap_all = sum(len(e["snap_cross"]) for e in all_ev)
    raw_all = sum(len(e["raw_cross"]) for e in all_ev)
    snap_non8 = sum(int(x["boundary_crossing_snap_count"]) for x in non8h)
    raw_non8 = sum(int(x["boundary_crossing_raw_count"]) for x in non8h if x["boundary_crossing_raw_count"] != "unknown")
    months_raw_ne_snap = sum(1 for x in non8h if x["boundary_crossing_raw_minus_snap"] not in ("unknown", 0))
    tb = {
        "raw_timestamps_saved": True,
        "note": (
            "ZIP funding_time and REST fundingTime raw millisecond values are present in the "
            "saved official files; this is raw-basis evidence from those saved values, not a "
            "claim that the original HTTP bytes for REST were retained (REST stored bodies are "
            "parsed JSON)."
        ),
        "rows_parsed_total": totals["rows_zip"] + totals["rows_rest"],
        "rows_zip": totals["rows_zip"],
        "rows_rest": totals["rows_rest"],
        "rows_finite": sum(e["rows_finite"] for e in all_ev),
        "rows_flagged_nonfinite_or_null": sum(e["rows_flagged"] for e in all_ev),
        "rows_nonzero_offset": sum(e["rows_nonzero_offset"] for e in all_ev),
        "rows_zero_offset": sum(e["rows_finite"] - e["rows_nonzero_offset"] for e in all_ev),
        "max_abs_offset_ms": max((e["max_abs_offset_ms"] for e in all_ev), default=0),
        "offset_abs_buckets": dict(off_buckets),
        "rows_cross_month_cst_raw_vs_snap": sum(e["rows_cross_month_cst"] for e in all_ev),
        "rows_cross_month_utc_raw_vs_snap": sum(e["rows_cross_month_utc"] for e in all_ev),
        "rows_excluded_snap_basis": sum(e["rows_excluded_snap_basis"] for e in all_ev),
        "rows_excluded_raw_basis": sum(e["rows_excluded_raw_basis"] for e in all_ev),
        "months_with_raw_to_snap_set_unequal": sum(1 for e in all_ev if e["raw_to_snap_set_equal"] == "false"),
        "in_file_snap_collision_keys": sum(e["snap_collision_keys"] for e in all_ev),
        "in_file_snap_collision_same_raw_dup_keys": sum(e["snap_collision_same_raw_dup_keys"] for e in all_ev),
        "in_file_snap_collision_distinct_raw_keys": sum(e["snap_collision_distinct_raw_keys"] for e in all_ev),
        "in_file_snap_collision_diff_rate_keys": sum(e["snap_collision_diff_rate_keys"] for e in all_ev),
        "cross_file_same_snapped_key_collisions": cross_file_keys,
        "cross_file_same_snapped_key_diff_rate": cross_file_diff_rate,
        "cross_file_same_snapped_key_by_source_pair": dict(cross_pair_kinds),
        "cross_file_same_snapped_key_diff_rate_by_source_pair": dict(cross_pair_diff_by_kind),
        "rows_excluded_by_reason": dict(excl_by_reason),
        "boundary_crossings_snap_basis_all_months_with_files": snap_all,
        "boundary_crossings_raw_basis_all_months_with_files": raw_all,
        "boundary_crossings_snap_basis_non8h_months": snap_non8,
        "boundary_crossings_raw_basis_non8h_months": raw_non8,
        "non8h_months_raw_crossing_count_differs_from_snap": months_raw_ne_snap,
        "months_without_saved_raw_timestamps": [
            {"inst_id": k[0], "month_cst": k[1], "status": "unknown_no_saved_raw_timestamps"}
            for k, e in sorted(evid.items()) if not e
        ],
        "scope_unknown": [
            "Rows excluded as non-finite/None rates (2 official ZIP rows) have raw timestamps in the ZIPs but are not part of the finite-rate time sets.",
            "Frozen DB rows and the v1.7/v1.9 deltas were not used as the official time source here; v1.7/v1.9 raw official bodies are not retained on this branch.",
            "Same-key-different-rate across the frozen DB, v1.7, v1.9, v1.10, b1..b3c deltas is per-batch compare evidence (conflicts 0 in those manifests); it was not re-run here.",
        ],
    }
    tb_json = os.path.join(OUT, "time_basis_evidence_v1_25.json")
    open(tb_json, "w", encoding="utf-8").write(json.dumps(tb, indent=2, ensure_ascii=False) + "\n")

    write_csv(os.path.join(OUT, "nonh8_completeness_unknowns_v1_25.csv"), UNKNOWN_FIELDS, unknown_rows)

    # ---- markdown ----
    compact = [
        "record_kind", "inst_id", "month_cst", "observed_intervals", "nonstandard_gap_hours",
        "observed_settlement_count", "denominator_status", "inferred_interval",
        "inferred_expected_count", "official_schedule_status",
        "boundary_crossing_snap_count", "boundary_crossing_raw_count",
        "snap_collision_keys", "partial_month", "cst_vs_utc_completeness_may_differ",
    ]
    md_path = os.path.join(OUT, "nonh8_completeness_unknowns_v1_25.md")
    status_changes = []
    for st in sorted(set(old_status) | set(new_status)):
        status_changes.append({"denominator_status": st, "v1.23": old_status.get(st, 0), "v1.25": new_status.get(st, 0)})
    inferred_changes = []
    for iv in sorted(set(old_inferred) | set(new_inferred), key=lambda s: (s == "", s)):
        inferred_changes.append({"inferred_interval": iv or "(blank)", "v1.23": old_inferred.get(iv, 0), "v1.25": new_inferred.get(iv, 0)})
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"""# Non-8H completeness unknowns (v1.25 correction of v1.23)

This is a new versioned file. The v1.23 files are kept unchanged. Offline only,
from already-saved official monthly ZIPs and 2026-11 REST parsed-JSON files; no
refetch, no backtest, no zero-fill, no interpolation, no change to any rate.

**No official settlement-schedule source has been used.** Every interval and every
expected-count denominator here is inferred from observed timestamps and is not
officially verified. `official_schedule_status` is
`unknown_no_official_schedule_source_used` on every row.

## Correction 1: 2H and other non-1H/4H/8H intervals

v1.23 `analyze_month` recognised only 1H/4H/8H. A month with a single constant
observed 2H interval fell into the fallback branch, which chose the smallest
divisible base (1H), labelled the month `not_determinable_internal_gaps` and wrote
`inferred_interval=1H`. A 2H grid is *consistent with* a 1H grid with missing slots,
but that does not mean 1H slots should exist and are missing. v1.25 keeps the observed
interval and leaves the official schedule unknown.

- v1.25 rule: a single constant observed gap of any whole-hour size is kept as the
  observed interval. If it is not 1H/4H/8H and spans the full CST month, the status is
  `inferred_constant_full_month_nonstandard_interval` (inferred only, not official).
- `inferred_interval` is assigned only when a single constant observed gap exists; v1.23
  wrote `1H` for non-constant months, which was not an observation. v1.25 leaves it blank.
- `interval_change_visible` means a gap-size change observed in the saved data only. It is
  not proof of an official interval change.
- Statuses of all other months are unchanged from v1.23.

### Non-8H months by denominator status (before / after)

{md_table(status_changes, ["denominator_status", "v1.23", "v1.25"])}

### Non-8H months by inferred_interval (before / after)

{md_table(inferred_changes, ["inferred_interval", "v1.23", "v1.25"])}

Changed rows vs v1.23: {len(changed_rows)} (field changes: {dict(field_change_counts)}).
Rows with changes outside denominator_status / inferred_interval / inferred_expected_count:
{unexpected_changes}. Boundary snap-count mismatches vs v1.23 `boundary_crossing_settlement_count`:
{snap_count_mismatch}. See `nonh8_v1_25_vs_v1_23_changed_rows.csv`.

### Months whose observed gaps include a non-1H/4H/8H value

Count: {len(nonstd_months)} of {len(non8h)} non-8H months (observed gap hours outside 1,4,8).

{md_table(count_rows(nonstd_by_gap), ["key", "count"])}

By v1.25 status:

{md_table(count_rows(nonstd_by_status), ["key", "count"])}

Only the 8 constant-2H months changed status; the other nonstandard-gap months keep their
v1.23 status (they have more than one gap size, so they remain not determinable).
The 2H gaps in mixed months and the single 132H gap (OL 2025-10) are observed gaps only;
whether they reflect an official interval, an interval change, or missing rows is unknown.

### The eight months (before / after)

{md_table(eight_rows, ["inst_id", "month_cst", "observed_settlements", "before_denominator_status", "before_inferred_interval", "after_observed_intervals", "after_denominator_status", "after_inferred_interval", "after_inferred_expected_count", "after_official_schedule_status"])}

## Correction 2: time basis (raw vs snap)

v1.23 `snap()` rounded each raw funding time to the nearest hour with no tolerance, then
de-duplicated, then assigned CST months and counted crossings. The v1.23 count of 6,109
is therefore a count over the post-snap, de-duplicated time set (snap basis). It is not a
raw-timestamp-by-raw-timestamp certification.

v1.25 records both bases from the saved raw values (ZIP `funding_time`, REST `fundingTime`):

- snap basis (v1.23 definition): {snap_non8:,} crossings over the {len(non8h):,} non-8H months
  (all months with a saved file: {snap_all:,}).
- raw basis (raw ts kept inside the window and inside the CST month, de-duplicated on raw ts):
  {raw_non8:,} crossings over the same non-8H months (all months with a saved file: {raw_all:,}).
- Non-8H months where raw and snap crossing counts differ: {months_raw_ne_snap}.
- Rows parsed: {tb['rows_parsed_total']:,} (ZIP {tb['rows_zip']:,} + REST {tb['rows_rest']:,}); finite-rate
  rows {tb['rows_finite']:,}; 2 ZIP rows have a null/None rate and are excluded. Rows with a non-zero raw-vs-snapped offset:
  {tb['rows_nonzero_offset']:,}; maximum absolute offset: {tb['max_abs_offset_ms']:,} ms.
  Offset buckets: {tb['offset_abs_buckets']}.
- Raw vs snapped timestamp in a different CST month: {tb['rows_cross_month_cst_raw_vs_snap']}; in a
  different UTC month: {tb['rows_cross_month_utc_raw_vs_snap']}.
- Snap collisions (several raw rows mapping to the same snapped key within one file): keys
  {tb['in_file_snap_collision_keys']} (same raw time duplicated {tb['in_file_snap_collision_same_raw_dup_keys']},
  distinct raw times {tb['in_file_snap_collision_distinct_raw_keys']}); same snapped key with different
  rates: {tb['in_file_snap_collision_diff_rate_keys']}.
- Cross-file same snapped key: {tb['cross_file_same_snapped_key_collisions']} by source pair
  {tb['cross_file_same_snapped_key_by_source_pair']}; with different rates: {tb['cross_file_same_snapped_key_diff_rate']}
  (by pair {tb['cross_file_same_snapped_key_diff_rate_by_source_pair']}). The saved 2026-11 REST files also
  carry earlier history outside CST 2026-11 (rows excluded from the month sets: {tb['rows_excluded_by_reason']}),
  which repeats keys present in the official monthly ZIPs; those overlaps are listed here as evidence and are not
  used to add or change any value.
- Months with no saved raw timestamps (listed as unknown, not estimated): {len(tb['months_without_saved_raw_timestamps'])}
  (the four 404 months). RVN-USDT-SWAP 2026-11 has a saved REST 51001 response with zero data rows.

This evidence covers the finite-rate rows of the saved ZIP/REST files only. See
`time_basis_evidence_v1_25.json`.

## What was NOT verified

- Same-key-different-rate across sources and snap collisions were checked only inside the saved
  ZIP/REST files as reported above (including cross-file within the saved ZIPs). They were not
  re-checked against the frozen DB, v1.7, v1.9 or the other deltas here; those comparisons remain
  the per-batch evidence (conflicts 0 in the b3b/b3c manifests and earlier batch manifests) and
  are not re-verified in this compilation.
- The ZIP/REST SHA-256 listings are navigation aids. They are not per-file acceptance against the
  expected manifests, and nothing here claims full-rate completeness.
- Frozen DB SHA `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc` only matches the
  references in the b3b/b3c manifests. Equal row counts (829,157) do not mean the file is
  identical to any other version.
- No official settlement-schedule source was used, so no interval and no denominator is official.
- Inventory `complete=true` is passed per that batch's source and comparison scope only, not a
  full-period or cross-frequency verification.

Self-run checks are team execution evidence, not ChatGPT runtime certification.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

## Known gaps (unchanged)

- OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06: official_rate_null (1/85 and 1/54 literal `None`).
- RVN-USDT-SWAP 2026-11: pending_check / rest_51001_instrument_not_listed.
- CC-USDT-SWAP 2025-10, INJ-USDT-SWAP 2023-11, MEGA-USDT-SWAP 2026-04, ORDER-USDT-SWAP 2025-09:
  official_unavailable / 404_reason_unknown.

{md_table(specials, compact)}

## All non-8H inst/month rows

{md_table(non8h, compact)}
""")

    end_utc = utc_now_iso()
    summary = {
        "unknown_file_rows": len(unknown_rows),
        "non8h_months": len(non8h),
        "special_known_gap_rows": len(specials),
        "denominator_status_v1_23": dict(old_status),
        "denominator_status_v1_25": dict(new_status),
        "inferred_interval_v1_23": {k or "(blank)": v for k, v in old_inferred.items()},
        "inferred_interval_v1_25": {k or "(blank)": v for k, v in new_inferred.items()},
        "observed_intervals_v1_25": dict(interval_counts),
        "changed_rows_vs_v1_23": len(changed_rows),
        "field_change_counts": dict(field_change_counts),
        "unexpected_field_changes": unexpected_changes,
        "boundary_snap_count_mismatch_vs_v1_23": snap_count_mismatch,
        "nonstandard_gap_months": len(nonstd_months),
        "nonstandard_gap_by_hours": dict(nonstd_by_gap),
        "nonstandard_gap_by_status": dict(nonstd_by_status),
        "time_basis": {k: v for k, v in tb.items() if k not in ("months_without_saved_raw_timestamps", "scope_unknown", "note")},
    }

    def meta(path: str, **extra: Any) -> dict[str, Any]:
        sh, sz = sha256_file(path)
        d = {"bytes": sz, "sha256": sh}
        d.update(extra)
        return d

    files_meta = {
        "nonh8_completeness_unknowns_v1_25.csv": meta(os.path.join(OUT, "nonh8_completeness_unknowns_v1_25.csv"), rows=len(unknown_rows)),
        "nonh8_completeness_unknowns_v1_25.md": meta(md_path),
        "nonh8_v1_25_vs_v1_23_changed_rows.csv": meta(changed_csv, rows=len(changed_rows)),
        "eight_2h_months_before_after_v1_25.csv": meta(eight_csv, rows=len(eight_rows)),
        "time_basis_evidence_v1_25.json": meta(tb_json),
    }
    script_path = os.path.abspath(__file__) if os.path.isfile(__file__) else ""
    if script_path:
        files_meta["build_sources_nonh8_v1_25_public.py"] = meta(script_path)
    manifest = {
        "research_id": "BACKTEST-READINESS-01",
        "version": "v1.25",
        "batch": "funding_sources_nonh8_v1_25",
        "corrects": "funding_sources_nonh8_v1_23 (kept unchanged)",
        "start_utc": start_utc,
        "end_utc": end_utc,
        "mode": "offline_only_from_already_saved_files",
        "no_official_settlement_schedule_source_used": True,
        "inputs_sha256": {
            "funding_month_inventory_v1_11_r5.csv": {"bytes": inv_bytes, "sha256": inv_sha},
            "nonh8_completeness_unknowns_v1_23.csv": {"bytes": old_csv_bytes, "sha256": old_csv_sha},
            "build_sources_nonh8_v1_23_public.py": {"bytes": old_script_bytes, "sha256": old_script_sha},
        },
        "summary": summary,
        "files": files_meta,
        "not_verified": [
            "same-key-different-rate across sources and snap collisions only checked inside the saved ZIP/REST files",
            "ZIP/REST hash listing is not per-file manifest acceptance and is not a full-rate completeness claim",
            "frozen DB 23ebdab5 only matches the references in b3b/b3c manifests; equal row counts do not mean equal to other versions",
            "no official settlement-schedule source used; all intervals and denominators are inferred, not verified",
        ],
        "rule": (
            "v1.25 offline correction: 2H and other nonstandard observed intervals kept as observed; "
            "inferred_interval only for a single constant observed gap; raw-basis and snap-basis crossing "
            "counts reported separately with offset, cross-month and collision evidence from saved raw "
            "timestamps. v1.23 files are unchanged. No refetch, no backtest, no zero-fill. "
            "FIB-4H-LONG-V3 remains NO-GO; live_approved is false."
        ),
    }
    mf = os.path.join(OUT, "funding_sources_nonh8_v1_25_manifest.json")
    open(mf, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    open(os.path.join(OUT, "funding_sources_nonh8_v1_25_counts.json"), "w", encoding="utf-8").write(
        json.dumps({"start_utc": start_utc, "end_utc": end_utc, "summary": summary}, indent=2, ensure_ascii=False) + "\n"
    )
    log(
        f"DONE changed_rows={len(changed_rows)} status_after={dict(new_status)} "
        f"snap={snap_non8} raw={raw_non8} coll_keys={tb['in_file_snap_collision_keys']} end_utc={end_utc}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
