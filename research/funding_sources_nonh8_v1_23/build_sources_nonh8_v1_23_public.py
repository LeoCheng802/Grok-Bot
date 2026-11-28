#!/usr/bin/env python3
# Publishable compiler for BACKTEST-READINESS-01 v1.23
# (source register + non-8H completeness unknowns).
# Local data locations are relative/config constants — set V123_* environment
# variables or edit the path constants before running.
# This file contains no host absolute paths and no secrets.
# OFFLINE ONLY: reads already-saved files; never makes a network request.

"""BACKTEST-READINESS-01 v1.23 — funding source register and non-8H unknowns.

Offline compilation only. Does not trade, run strategies, backtest, refetch
candles or official ZIPs/REST, expand the universe or window, zero-fill,
interpolate, or modify the frozen DB.

If an equivalent source-register or non-8H completeness-unknowns list already
exists on this branch, this compiler is supposed to cite it and stop. None was
found (search: funding_source_register, nonh8, non-8h completeness, settlement
denominator). Per-batch manifests and inventory r5 are cited as inputs; this
folder is a new compilation, not a duplicate of those files.

No official settlement-schedule source has been used. Any expected-count
denominator derived from a constant observed interval is an observed-assumption
only, inferred and not officially verified.

Inventory complete=true (in r5) means passed per that batch's source and
comparison scope only, not a full-period or cross-frequency verification.
Self-run scans in this compilation are team execution evidence, not ChatGPT
runtime certification.

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
import sqlite3
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

OUT = os.environ.get("V123_OUT", "funding_sources_nonh8_v1_23")
REPO = os.environ.get("V123_REPO", ".")
RESEARCH = os.environ.get("V123_RESEARCH", os.path.join(REPO, "research"))
FROZEN_DB = os.environ.get("V123_FROZEN_DB", "funding_archive_l1_isolated.sqlite")
INV_R5 = os.environ.get(
    "V123_INV",
    os.path.join(RESEARCH, "funding_delta_v1_11_b3c", "funding_month_inventory_v1_11_r5.csv"),
)
START_UTC = os.environ.get("V123_START_UTC", "")

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

# Known PR #8 introducing (or superseding) commits on this branch. Used when
# git is unavailable; verified against git log when git is available.
KNOWN_COMMITS = {
    "v1.7": "57c30e539ffe73cb2378bc94a8a5c3432707944e",
    "v1.9": "8458510c0eb4bc365c121b9c835c2895103aea40",
    "v1.10": "b0dcf61e26db0e99b178ad0fe59d3944edbe6492",
    "v1.11_b1": "6499a579aacdf922c67f432915245adef0c11dc7",
    "v1.11_b2": "74764f32f6bcdfab8bcc25211eaeed9755fdeffe",
    "v1.11_b2_r1": "928beeb6cfeaa9fc686f0bdfe44154abba6e14ec",
    "v1.11_b3a": "7852b42fe581ce15f1b5c84c8ca4f360c768e8fa",
    "v1.11_b3b": "363dc665e1b3d45c3c85bbdd808a3fc834c36c47",
    "v1.11_b3c": "f1280dc41d8409ed856fd41c339ff095a67ebe74",
}

# Review comment IDs known at compilation time from prior Issue #1 / PR #8
# discussion already recorded in this research thread. IDs not known to this
# compilation are left blank rather than fetched from the network.
REVIEW = {
    "frozen_l1": (
        "Pinned SHA is the read-only baseline in all v1.11 manifests on PR #8. "
        "No dedicated 復盤 comment for the DB file alone is cited here."
    ),
    "v1.7": (
        "Delta SHA is pinned as an input in later v1.11 manifests. "
        "A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.7 "
        "is not cited here."
    ),
    "v1.9": (
        "Delta SHA is pinned as an input in later v1.11 manifests. "
        "A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.9 "
        "is not cited here."
    ),
    "v1.10": (
        "Delta SHA is pinned as an input in later v1.11 manifests. "
        "A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.10 "
        "is not cited here."
    ),
    "v1.11_b1": (
        "Delta SHA is pinned as an input in later v1.11 manifests. "
        "A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.11-b1 "
        "is not cited here."
    ),
    "v1.11_b2_r1": (
        "復盤 PASS of head 928beeb6: Issue #1 comment 7230640210. "
        "D1 found: 7230456720. "
        "ChatGPT v1.16: 7230504858; supplement 7230544291. "
        "Execution reports: 7230527499 (r1 D1), 7230617170 (v1.16 follow-up)."
    ),
    "v1.11_b3a": (
        "Execution report Issue #1 comment 7230844369 (PR #8 index 7230846110). "
        "A 復盤 PASS or ChatGPT acceptance comment ID specifically for b3a "
        "is not cited here."
    ),
    "v1.11_b3b": (
        "Execution report Issue #1 comment 7231162465 (PR #8 index 7231164350). "
        "ChatGPT v1.18 acceptance: 7231209641."
    ),
    "v1.11_b3c": (
        "Execution report Issue #1 comment 7231372486 (PR #8 index 7231374137). "
        "ChatGPT v1.23 (7239218755) is the assignment for this compilation, "
        "not an acceptance of b3c."
    ),
    "REST_2026_11": (
        "Same review trail as v1.11-b2 r1 (REST evidence form and RVN 51001 "
        "documented in that follow-up): Issue #1 7230640210 (復盤 PASS of "
        "928beeb6); ChatGPT v1.16 7230504858 / 7230544291. "
        "Stored REST bodies are parsed JSON, not raw HTTP bytes."
    ),
}

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




def parse_zip_numeric(inst: str, ym: str, blob: bytes) -> tuple[list[int], int, int]:
    """Return (sorted unique ts_snapped in this CST month, n_raw_rows, n_flagged)."""
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        if not names:
            raise ValueError("zip has no entries")
        txt = zf.read(names[0]).decode()
    rows = list(csv.DictReader(io.StringIO(txt)))
    times: set[int] = set()
    flagged = 0
    for r in rows:
        name = (r.get("instrument_name") or "").strip()
        if name and name != inst:
            raise ValueError(f"instrument_name mismatch: {name!r} != {inst!r}")
        tr = int(r["funding_time"])
        raw_rate = r.get("funding_rate")
        if not is_numeric_rate(raw_rate):
            flagged += 1
            continue
        ts = snap(tr)
        if not (WIN_LO <= ts <= WIN_HI):
            continue
        if month_cst_from_ms(ts) != ym:
            continue
        times.add(ts)
    return sorted(times), len(rows), flagged


def parse_rest_numeric(inst: str, ym: str, obj: dict[str, Any]) -> tuple[list[int], int, int, str]:
    """Return (times, n_data_rows, n_flagged, http_or_code)."""
    times: set[int] = set()
    n_data = 0
    flagged = 0
    status = "ok"
    pages = obj.get("pages") or []
    if not pages:
        # maybe a 51001 or error document
        code = str(obj.get("code") or obj.get("response", {}).get("code") or "")
        if code and code != "0":
            return [], 0, 0, f"rest_code_{code}"
    for page in pages:
        http = page.get("http")
        resp = page.get("response") or {}
        code = str(resp.get("code") or "")
        if http not in (None, 200) or (code and code != "0"):
            status = f"http_{http}_code_{code or 'unknown'}"
            continue
        for rec in resp.get("data") or []:
            n_data += 1
            tr = int(rec["fundingTime"])
            rate = rec.get("realizedRate")
            rate_field = "realizedRate"
            if rate is None or str(rate).strip() == "":
                rate = rec.get("fundingRate")
                rate_field = "fundingRate"
            if not is_numeric_rate(rate):
                flagged += 1
                continue
            ts = snap(tr)
            if not (WIN_LO <= ts <= WIN_HI):
                continue
            if month_cst_from_ms(ts) != ym:
                continue
            times.add(ts)
    return sorted(times), n_data, flagged, status


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
            "Counted one by one from saved official timestamps. Typologically, "
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


def analyze_month(inst: str, ym: str, times: list[int], extra_notes: list[str]) -> dict[str, Any]:
    month_lo, month_hi = cst_month_bounds(ym)
    full_month = month_fully_in_window(month_lo, month_hi)
    n = len(times)
    n_8h = sum(1 for t in times if t % EIGHT_H_MS == 0)
    n_non = n - n_8h
    first = times[0] if times else None
    last = times[-1] if times else None
    rec: dict[str, Any] = {
        "inst_id": inst,
        "month_cst": ym,
        "observed_settlement_count": n,
        "observed_8h_grid_count": n_8h,
        "observed_non_8h_count": n_non,
        "observed_intervals": "",
        "unique_gap_hours": "",
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
    rec["unique_gap_hours"] = ",".join(
        str(int(g)) if float(g).is_integer() else str(g) for g in uniq
    )

    change_utc: list[str] = []
    change_date: list[str] = []
    for i in range(1, len(gaps_h)):
        if gaps_h[i] != gaps_h[i - 1]:
            rec["interval_change_visible"] = "true"
            # The settlement that ends the new-sized gap.
            change_utc.append(iso(times[i + 1]))
            change_date.append(iso_cst_date(times[i + 1]))
    rec["interval_change_at_utc"] = ";".join(change_utc)
    rec["interval_change_at_cst_date"] = ";".join(dict.fromkeys(change_date))

    # Runs of constant gap size.
    runs: list[tuple[float, int]] = []
    run_v, run_n = gaps_h[0], 1
    for g in gaps_h[1:]:
        if g == run_v:
            run_n += 1
        else:
            runs.append((run_v, run_n))
            run_v, run_n = g, 1
    runs.append((run_v, run_n))

    known = {1.0, 4.0, 8.0}
    status = ""
    inferred_i = ""
    expected = ""

    def check_full(interval_h: float) -> tuple[str, str]:
        interval_ms = int(interval_h * HOUR_MS)
        expected_pts = grid_points(month_lo, month_hi, interval_ms)
        # observed-assumption expected count if first/last match the full-month grid
        if not full_month:
            return "not_determinable_window_truncated", ""
        if not expected_pts:
            return "not_determinable_window_truncated", ""
        if first == expected_pts[0] and last == expected_pts[-1] and n == len(expected_pts):
            return "inferred_constant_full_month", str(len(expected_pts))
        # constant from first to last, no internal missing, but not full month
        span_n = int(round((last - first) / interval_ms)) + 1
        if n == span_n:
            return "not_determinable_span_shorter_than_month", ""
        return "not_determinable_internal_gaps", ""

    if len(uniq) == 1 and uniq[0] in known:
        rec["observed_intervals"] = interval_label(uniq[0])
        inferred_i = interval_label(uniq[0])
        status, expected = check_full(uniq[0])
    elif len(runs) == 2 and all(v in known for v, _ in runs):
        rec["observed_intervals"] = "+".join(interval_label(v) for v, _ in runs)
        # two contiguous constant runs: visible mid-month interval change
        status = "not_determinable_interval_change"
    else:
        # Multiples of a single known interval? (possible gaps on that grid)
        bases = [b for b in (1.0, 4.0, 8.0) if all(abs(g / b - round(g / b)) < 1e-9 for g in uniq)]
        labels = []
        for b in (1.0, 4.0, 8.0):
            if any(abs(g - b) < 1e-9 for g in uniq):
                labels.append(interval_label(b))
        extras = [g for g in uniq if g not in known]
        rec["observed_intervals"] = "+".join(labels + [interval_label(g) for g in extras]) or "irregular"
        if bases:
            # Could be gaps on the finest matching base, or an interval change, or both.
            if rec["interval_change_visible"] == "true":
                status = "not_determinable_interval_change_or_gaps"
            else:
                status = "not_determinable_internal_gaps"
            inferred_i = interval_label(min(bases))
        else:
            status = "not_determinable_irregular_gaps"

    rec["denominator_status"] = status
    rec["inferred_interval"] = inferred_i
    rec["inferred_expected_count"] = expected
    rec["denominator_is_official"] = "false"
    if status == "inferred_constant_full_month":
        notes.append(
            "Expected count is inferred from the observed constant interval "
            "spanning the full CST month. No official settlement-schedule source "
            "was used; this denominator is not officially verified."
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


REGISTER_FIELDS = [
    "batch",
    "source_type",
    "url_pattern",
    "file_count",
    "row_count",
    "pinned_sha256",
    "bytes",
    "pr8_path",
    "commit_sha",
    "evidence_form",
    "raw_bytes_saved",
    "review_status",
    "notes",
]

UNKNOWN_FIELDS = [
    "record_kind",
    "inst_id",
    "month_cst",
    "inventory_class",
    "inventory_sub_reason",
    "inventory_complete",
    "official_source",
    "official_file",
    "observed_settlement_count",
    "observed_8h_grid_count",
    "observed_non_8h_count",
    "observed_intervals",
    "unique_gap_hours",
    "interval_change_visible",
    "interval_change_at_utc",
    "interval_change_at_cst_date",
    "first_settlement_utc",
    "last_settlement_utc",
    "month_start_utc",
    "month_end_exclusive_utc",
    "month_fully_inside_research_window",
    "denominator_status",
    "inferred_interval",
    "inferred_expected_count",
    "denominator_is_official",
    "boundary_crossing_settlement_count",
    "boundary_crossing_times_utc",
    "month_end_crossing_in_window",
    "partial_month",
    "cst_vs_utc_boundary_effect",
    "cst_vs_utc_completeness_may_differ",
    "notes",
]


def write_csv(path: str, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def md_escape(s: Any) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def md_table(fields: list[str], rows: list[dict[str, Any]], only: list[str] | None = None) -> str:
    cols = only or fields
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(md_escape(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    start_utc = START_UTC or utc_now_iso()
    log(f"v1.23 start_utc={start_utc}")
    log("OFFLINE compilation; no network fetches.")

    # --- inventory ---
    with open(INV_R5, newline="", encoding="utf-8") as f:
        inv_rows = list(csv.DictReader(f))
    inv_sha, inv_bytes = sha256_file(INV_R5)
    log(f"inventory r5 rows={len(inv_rows)} sha={inv_sha} bytes={inv_bytes}")
    if len(inv_rows) != 7536:
        raise SystemExit(f"expected 7536 inventory rows, got {len(inv_rows)}")

    # --- zip index (on-disk only, never download) ---
    zip_index: dict[tuple[str, str], tuple[str, str]] = {}
    zip_counts: dict[str, int] = {}
    dups = []
    for batch, rel in ZIP_DIRS:
        d = os.path.join(RESEARCH, rel)
        n = 0
        if not os.path.isdir(d):
            zip_counts[batch] = 0
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".zip"):
                continue
            # INST-USDT-SWAP-fundingrates-YYYY-MM.zip
            if "-fundingrates-" not in name:
                continue
            inst, rest = name[:-4].split("-fundingrates-")
            ym = rest
            key = (inst, ym)
            path = os.path.join(d, name)
            n += 1
            if key in zip_index:
                dups.append((key, zip_index[key][0], rel))
            else:
                zip_index[key] = (rel + "/" + name, path)
        zip_counts[batch] = n
        log(f"zip dir {batch}: {n}")
    if dups:
        raise SystemExit(f"duplicate official ZIPs for the same month: {dups[:5]}")
    log(f"unique official ZIPs indexed: {len(zip_index)}")

    rest_dir = os.path.join(RESEARCH, "funding_delta_v1_11_b2", "rest_2026_11")
    rest_files = sorted(
        p for p in os.listdir(rest_dir) if p.endswith(".json.gz")
    ) if os.path.isdir(rest_dir) else []
    log(f"REST 2026-11 files: {len(rest_files)}")

    # --- parse official sources per inventory month ---
    official_times: dict[tuple[str, str], list[int]] = {}
    official_meta: dict[tuple[str, str], dict[str, Any]] = {}
    zip_numeric_total = 0
    zip_flagged_total = 0
    rest_numeric_total = 0
    rest_flagged_total = 0
    rest_ok = 0
    rest_err = 0

    for r in inv_rows:
        inst, ym = r["inst_id"], r["month_cst"]
        key = (inst, ym)
        if key in zip_index:
            rel, path = zip_index[key]
            blob = open(path, "rb").read()
            times, nraw, nflag = parse_zip_numeric(inst, ym, blob)
            official_times[key] = times
            official_meta[key] = {
                "official_source": "official_monthly_zip",
                "official_file": "research/" + rel,
                "zip_raw_rows": nraw,
                "zip_flagged": nflag,
                "zip_sha256": sha256_bytes(blob),
            }
            zip_numeric_total += len(times)
            zip_flagged_total += nflag
        elif ym == "2026-11":
            fp = os.path.join(rest_dir, f"{inst}.json.gz")
            if os.path.isfile(fp):
                obj = json.loads(gzip.open(fp, "rt", encoding="utf-8").read())
                times, ndata, nflag, status = parse_rest_numeric(inst, ym, obj)
                official_times[key] = times
                official_meta[key] = {
                    "official_source": "rest_parsed_json",
                    "official_file": rel_research(fp),
                    "rest_data_rows": ndata,
                    "rest_flagged": nflag,
                    "rest_status": status,
                    "file_sha256": sha256_file(fp)[0],
                }
                rest_numeric_total += len(times)
                rest_flagged_total += nflag
                if status == "ok" and times:
                    rest_ok += 1
                elif status != "ok":
                    rest_err += 1
                else:
                    rest_ok += 1  # HTTP 200 with zero rows still a successful fetch
            else:
                official_times[key] = []
                official_meta[key] = {
                    "official_source": "none",
                    "official_file": "",
                }
        else:
            official_times[key] = []
            official_meta[key] = {
                "official_source": "none",
                "official_file": "",
            }
    log(
        f"official parse done: zip months={sum(1 for k,m in official_meta.items() if m['official_source']=='official_monthly_zip')} "
        f"numeric_keys={zip_numeric_total} flagged={zip_flagged_total}; "
        f"REST ok/err={rest_ok}/{rest_err} numeric_keys={rest_numeric_total} flagged={rest_flagged_total}"
    )

    # Frozen row count + SHA (read-only)
    frozen_sha, frozen_bytes = sha256_file(FROZEN_DB)
    con = sqlite3.connect(f"file:{FROZEN_DB}?mode=ro", uri=True)
    try:
        frozen_rows = int(con.execute("SELECT COUNT(*) FROM funding_archive").fetchone()[0])
    finally:
        con.close()
    log(f"frozen rows={frozen_rows} sha={frozen_sha} bytes={frozen_bytes}")

    # --- source register ---
    def delta_info(rel: str, expected_sha: str, expected_rows: int) -> tuple[str, int, int]:
        path = os.path.join(RESEARCH, rel)
        sha, size = sha256_file(path)
        if sha != expected_sha:
            raise SystemExit(f"SHA mismatch {rel}: got {sha}, expected {expected_sha}")
        with gzip.open(path, "rt", encoding="utf-8") as f:
            n = sum(1 for _ in csv.DictReader(f))
        if n != expected_rows:
            raise SystemExit(f"row mismatch {rel}: got {n}, expected {expected_rows}")
        return sha, size, n

    # Pin SHAs from already-published manifests (re-verified above / here).
    reg_rows: list[dict[str, Any]] = []

    reg_rows.append({
        "batch": "frozen_db_l1",
        "source_type": "frozen DB",
        "url_pattern": "",
        "file_count": 1,
        "row_count": frozen_rows,
        "pinned_sha256": frozen_sha,
        "bytes": frozen_bytes,
        "pr8_path": "",
        "commit_sha": "",
        "evidence_form": "sqlite_table_rows",
        "raw_bytes_saved": "false",
        "review_status": REVIEW["frozen_l1"],
        "notes": (
            "Pinned local read-only input funding_archive_l1_isolated.sqlite "
            f"({frozen_rows} rows). Not committed on PR #8; SHA is recorded in "
            "every later v1.11 batch manifest. Opened mode=ro only. "
            "This is an archive table, not raw official ZIP or HTTP bytes."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz",
        "34743db093b5673233693b0bfd4fa020abeb3928f7d4c0c29603c4d4c01311be",
        6748,
    )
    reg_rows.append({
        "batch": "v1.7",
        "source_type": "REST parsed JSON (funding-rate-history)",
        "url_pattern": REST_TMPL.replace("{LIMIT}", "100"),
        "file_count": 1,
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.7"],
        "evidence_form": "delta_csv_only",
        "raw_bytes_saved": "false",
        "review_status": REVIEW["v1.7"],
        "notes": (
            "Official endpoint was REST funding-rate-history. Raw HTTP bodies "
            "and parsed page files are not retained on this branch; the pinned "
            "artifact is the 6,748-row delta CSV. SHA re-verified against the "
            "file and against later batch input manifests."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz",
        "01ed8da28efa7038d03369b0b02b78f5777d3f21d95e5a95ca1e26221bb3340e",
        174,
    )
    reg_rows.append({
        "batch": "v1.9",
        "source_type": "official monthly ZIP and/or REST (mixed; see v1.9 manifest)",
        "url_pattern": CDN_TMPL + " | " + REST_TMPL.replace("{LIMIT}", ""),
        "file_count": 1,
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.9"],
        "evidence_form": "delta_csv_only",
        "raw_bytes_saved": "false",
        "review_status": REVIEW["v1.9"],
        "notes": (
            "v1.9 manifest lists both the official monthly ZIP CDN and REST "
            "funding-rate-history. No raw monthly ZIPs and no raw HTTP bodies "
            "for v1.9 are present on this branch; the pinned artifact is the "
            "174-row delta CSV plus funding_missing174_classification_v1_9.json."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz",
        "4fe33c0efe78f1398b02cb231760d3817b13f985de013e51df9c273dec7c999b",
        10633,
    )
    reg_rows.append({
        "batch": "v1.10",
        "source_type": "official monthly ZIP",
        "url_pattern": CDN_TMPL,
        "file_count": zip_counts.get("v1.10", 0),
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.10"],
        "evidence_form": "raw_zip",
        "raw_bytes_saved": "true",
        "review_status": REVIEW["v1.10"],
        "notes": (
            f"{zip_counts.get('v1.10', 0)} raw official monthly ZIPs are saved "
            "under research/funding_delta_v1_10/official_monthly_zips/. "
            "row_count is the pinned delta (new keys only: 10,633), not the "
            "official ZIP row total (11,031 numeric in the v1.10 manifest)."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz",
        "2ab89d43188e38c0b34ea04513d9c199eee2fa7fc5bfac891993db2006d48bbb",
        609,
    )
    reg_rows.append({
        "batch": "v1.11_b1",
        "source_type": "official monthly ZIP",
        "url_pattern": CDN_TMPL,
        "file_count": zip_counts.get("v1.11_b1", 0),
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.11_b1"],
        "evidence_form": "raw_zip",
        "raw_bytes_saved": "true",
        "review_status": REVIEW["v1.11_b1"],
        "notes": (
            f"{zip_counts.get('v1.11_b1', 0)} raw official monthly ZIPs are saved "
            "under research/funding_delta_v1_11_b1/official_monthly_zips/. "
            "row_count is the pinned delta (609 new keys)."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_11_b2_r1/funding_delta_v1_11_b2_r1.csv.gz",
        "ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86",
        198354,
    )
    reg_rows.append({
        "batch": "v1.11_b2_r1",
        "source_type": "official monthly ZIP (plus REST 2026-11 listed as its own row)",
        "url_pattern": CDN_TMPL,
        "file_count": zip_counts.get("v1.11_b2", 0),
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_11_b2_r1/funding_delta_v1_11_b2_r1.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.11_b2_r1"],
        "evidence_form": "raw_zip",
        "raw_bytes_saved": "true",
        "review_status": REVIEW["v1.11_b2_r1"],
        "notes": (
            f"{zip_counts.get('v1.11_b2', 0)} raw official monthly ZIPs remain "
            "under research/funding_delta_v1_11_b2/official_monthly_zips/ "
            f"(introduced in {KNOWN_COMMITS['v1.11_b2']}). "
            "The r1 delta (198,354) supersedes the b2 delta after dropping 2 "
            "official literal-None rates (D1). Raw ZIP evidence form is "
            "raw_zip / raw_bytes_saved=true. REST 2026-11 is a separate register row."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_11_b3a/funding_delta_v1_11_b3a.csv.gz",
        "0950a0d28966560a84b49a896e418f86ea2af8e866f61f6a15a9d321568cbaab",
        918,
    )
    reg_rows.append({
        "batch": "v1.11_b3a",
        "source_type": "official monthly ZIP",
        "url_pattern": CDN_TMPL,
        "file_count": zip_counts.get("v1.11_b3a", 0),
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_11_b3a/funding_delta_v1_11_b3a.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.11_b3a"],
        "evidence_form": "raw_zip",
        "raw_bytes_saved": "true",
        "review_status": REVIEW["v1.11_b3a"],
        "notes": (
            f"{zip_counts.get('v1.11_b3a', 0)} raw official monthly ZIPs are saved "
            "under research/funding_delta_v1_11_b3a/official_monthly_zips/. "
            "row_count is the pinned delta (918 new keys). Fetch evidence: "
            "fetch_evidence_v1_11_b3a.jsonl."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_11_b3b/funding_delta_v1_11_b3b.csv.gz",
        "f7b139a597e0257283a1c32dd632d6ef39a5822c15a03c929d1d433b53b66b9e",
        1084,
    )
    reg_rows.append({
        "batch": "v1.11_b3b",
        "source_type": "official monthly ZIP",
        "url_pattern": CDN_TMPL,
        "file_count": zip_counts.get("v1.11_b3b", 0),
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_11_b3b/funding_delta_v1_11_b3b.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.11_b3b"],
        "evidence_form": "raw_zip",
        "raw_bytes_saved": "true",
        "review_status": REVIEW["v1.11_b3b"],
        "notes": (
            f"{zip_counts.get('v1.11_b3b', 0)} raw official monthly ZIPs are saved "
            "under research/funding_delta_v1_11_b3b/official_monthly_zips/. "
            "row_count is the pinned delta (1,084 new keys). Fetch evidence: "
            "fetch_evidence_v1_11_b3b.jsonl."
        ),
    })

    sha, size, n = delta_info(
        "funding_delta_v1_11_b3c/funding_delta_v1_11_b3c.csv.gz",
        "8f49f40fa0d47297ab7f4d3b5d21a7b60177f1936079519eccba05ab7137cfda",
        1862,
    )
    reg_rows.append({
        "batch": "v1.11_b3c",
        "source_type": "official monthly ZIP",
        "url_pattern": CDN_TMPL,
        "file_count": zip_counts.get("v1.11_b3c", 0),
        "row_count": n,
        "pinned_sha256": sha,
        "bytes": size,
        "pr8_path": "research/funding_delta_v1_11_b3c/funding_delta_v1_11_b3c.csv.gz",
        "commit_sha": KNOWN_COMMITS["v1.11_b3c"],
        "evidence_form": "raw_zip",
        "raw_bytes_saved": "true",
        "review_status": REVIEW["v1.11_b3c"],
        "notes": (
            f"{zip_counts.get('v1.11_b3c', 0)} raw official monthly ZIPs are saved "
            "under research/funding_delta_v1_11_b3c/official_monthly_zips/. "
            "row_count is the pinned delta (1,862 new keys). Fetch evidence: "
            "fetch_evidence_v1_11_b3c.jsonl. Inventory r5 lives in this folder."
        ),
    })

    # REST file-set pin: sha256 of a stable listing (name, size, file sha256).
    rest_listing_lines = []
    rest_bytes_total = 0
    for name in rest_files:
        p = os.path.join(rest_dir, name)
        sh, sz = sha256_file(p)
        rest_listing_lines.append(f"{name} {sz} {sh}")
        rest_bytes_total += sz
    rest_listing = "\n".join(rest_listing_lines) + "\n"
    rest_set_sha = sha256_bytes(rest_listing.encode())
    rest_listing_path = os.path.join(OUT, "rest_2026_11_file_sha256s_v1_23.txt")
    open(rest_listing_path, "w", encoding="utf-8").write(rest_listing)

    rvn_name = "RVN-USDT-SWAP.json.gz"
    rvn_in_rest = rvn_name in rest_files
    reg_rows.append({
        "batch": "REST_2026_11",
        "source_type": "REST parsed JSON (funding-rate-history)",
        "url_pattern": REST_TMPL.replace("{LIMIT}", "400"),
        "file_count": len(rest_files),
        "row_count": rest_numeric_total,
        "pinned_sha256": rest_set_sha,
        "bytes": rest_bytes_total,
        "pr8_path": "research/funding_delta_v1_11_b2/rest_2026_11/",
        "commit_sha": KNOWN_COMMITS["v1.11_b2_r1"],
        "evidence_form": "parsed_json",
        "raw_bytes_saved": "false",
        "review_status": REVIEW["REST_2026_11"],
        "notes": (
            f"{len(rest_files)} saved files (285 instrument histories + "
            f"{'RVN 51001 present' if rvn_in_rest else 'RVN file missing'}). "
            "Bodies are parsed JSON (raw_bytes_saved=false), documented in "
            "research/funding_delta_v1_11_b2_r1/rest_evidence_form.json "
            "(SHA 5ea53c523001070de522c5db4f360f46a85e67944f67d84e4cdaffa0e75bfdf5). "
            "RVN-USDT-SWAP 2026-11 evidence: "
            "research/funding_delta_v1_11_b2_r1/rvn_usdt_swap_2026_11_rest_51001_evidence.json "
            "(SHA c74b71d80169355980f2c5f45f46a96996d1b77e1e7e8ea25ad1ed8fbedd92bd). "
            f"row_count is official finite-numeric unique keys inside the "
            f"research window and CST 2026-11: {rest_numeric_total}. "
            "Pinned SHA is SHA-256 of the sorted listing "
            "rest_2026_11_file_sha256s_v1_23.txt (name, bytes, file SHA), not a "
            "single archive. Files introduced in commit "
            f"{KNOWN_COMMITS['v1.11_b2']}; form labels in "
            f"{KNOWN_COMMITS['v1.11_b2_r1']}."
        ),
    })

    # --- non-8H completeness unknowns ---
    inv_by = {(r["inst_id"], r["month_cst"]): r for r in inv_rows}
    unknown_rows: list[dict[str, Any]] = []
    n_with_non8h = 0
    n_8h_only = 0
    n_empty_official = 0

    def build_row(key: tuple[str, str], record_kind: str, extra: list[str]) -> dict[str, Any]:
        inst, ym = key
        inv = inv_by[key]
        times = official_times.get(key) or []
        meta = official_meta.get(key) or {}
        analyzed = analyze_month(inst, ym, times, extra)
        analyzed.update({
            "record_kind": record_kind,
            "inventory_class": inv.get("class") or "",
            "inventory_sub_reason": inv.get("sub_reason") or "",
            "inventory_complete": (inv.get("complete") or "").strip(),
            "official_source": meta.get("official_source") or "none",
            "official_file": meta.get("official_file") or "",
        })
        return analyzed

    special_keys = set(SPECIAL_NULL) | set(SPECIAL_PENDING) | set(SPECIAL_404)

    for r in inv_rows:
        key = (r["inst_id"], r["month_cst"])
        times = official_times.get(key) or []
        n_non = sum(1 for t in times if t % EIGHT_H_MS != 0)
        if n_non:
            n_with_non8h += 1
            extras = []
            if key in SPECIAL_NULL:
                extras.append(SPECIAL_NULL[key])
            unknown_rows.append(build_row(key, "non8h_month", extras))
        else:
            if times:
                n_8h_only += 1
            else:
                n_empty_official += 1
            if key in special_keys:
                extras = []
                if key in SPECIAL_NULL:
                    extras.append(SPECIAL_NULL[key])
                elif key in SPECIAL_PENDING:
                    extras.append(SPECIAL_PENDING[key])
                elif key in SPECIAL_404:
                    extras.append(SPECIAL_404[key])
                kind = (
                    "known_gap_official_rate_null" if key in SPECIAL_NULL
                    else "known_gap_pending" if key in SPECIAL_PENDING
                    else "known_gap_404"
                )
                unknown_rows.append(build_row(key, kind, extras))

    # If a special key has non-8H it is already in the list as non8h_month.
    # If it also needs to appear as a known gap with the same analysis, that's
    # enough — notes carry the special reason. Ensure all special keys present.
    have = {(u["inst_id"], u["month_cst"]) for u in unknown_rows}
    for key, msg in {**SPECIAL_NULL, **SPECIAL_PENDING, **SPECIAL_404}.items():
        if key not in have:
            kind = (
                "known_gap_official_rate_null" if key in SPECIAL_NULL
                else "known_gap_pending" if key in SPECIAL_PENDING
                else "known_gap_404"
            )
            unknown_rows.append(build_row(key, kind, [msg]))

    unknown_rows.sort(key=lambda r: (r["inst_id"], r["month_cst"], r["record_kind"]))

    status_counts = Counter(r["denominator_status"] for r in unknown_rows if r["record_kind"] == "non8h_month")
    interval_counts = Counter(r["observed_intervals"] for r in unknown_rows if r["record_kind"] == "non8h_month")
    derivable = sum(1 for r in unknown_rows if r["record_kind"] == "non8h_month" and r["denominator_status"] == "inferred_constant_full_month")
    non8h_rows = [r for r in unknown_rows if r["record_kind"] == "non8h_month"]
    special_rows = [r for r in unknown_rows if r["record_kind"] != "non8h_month"]
    crossing_count_hist = Counter(int(r["boundary_crossing_settlement_count"]) for r in non8h_rows)
    boundary_effect_counts = Counter(r["cst_vs_utc_boundary_effect"] for r in non8h_rows)
    n_non8h_with_crossings = sum(1 for r in non8h_rows if int(r["boundary_crossing_settlement_count"]) > 0)
    n_non8h_may_differ = sum(1 for r in non8h_rows if r["cst_vs_utc_completeness_may_differ"] == "true")
    n_non8h_2026_11 = sum(1 for r in non8h_rows if r["month_cst"] == "2026-11")
    n_non8h_crossing_settlements = sum(int(r["boundary_crossing_settlement_count"]) for r in non8h_rows)

    log(
        f"non8h months={len(non8h_rows)} derivable_inferred={derivable} "
        f"8h_only={n_8h_only} empty_official={n_empty_official} special_extra={len(special_rows)}"
    )

    # --- write outputs ---
    reg_csv = os.path.join(OUT, "funding_source_register_v1_23.csv")
    unk_csv = os.path.join(OUT, "nonh8_completeness_unknowns_v1_23.csv")
    write_csv(reg_csv, REGISTER_FIELDS, reg_rows)
    write_csv(unk_csv, UNKNOWN_FIELDS, unknown_rows)

    # Markdown register
    reg_md_path = os.path.join(OUT, "funding_source_register_v1_23.md")
    register_intro = """# Funding source register (v1.23)

Offline compilation from already-saved PR #8 artifacts and the pinned frozen
DB (read-only). No official file was refetched. No equivalent source-register
file was found on this branch; per-batch manifests are cited rather than
copied in full. SHA and row counts below were re-read from the pinned files
and match those manifests.

`row_count` for official-ZIP batches is the **delta** (new keys added in that
batch), except `frozen_db_l1` (archive rows) and `REST_2026_11` (official
finite-numeric unique keys in CST 2026-11 inside the research window, parsed
from the saved REST files). `file_count` for official-ZIP batches is the
number of raw monthly ZIPs retained in that batch folder.

Review status lists 復盤 PASS and ChatGPT acceptance comment IDs only where
they were already known to this compilation; IDs were not fetched from the
network. Self-run checks here are team execution evidence, not ChatGPT
runtime certification.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.
"""
    # compact table columns
    compact_reg = [
        "batch", "source_type", "file_count", "row_count", "pinned_sha256",
        "pr8_path", "commit_sha", "evidence_form", "raw_bytes_saved",
    ]
    with open(reg_md_path, "w", encoding="utf-8") as f:
        f.write(register_intro)
        f.write("\n## Summary table\n\n")
        f.write(md_table(REGISTER_FIELDS, reg_rows, only=compact_reg))
        f.write("\n\n## Per-batch notes and review status\n\n")
        for r in reg_rows:
            f.write(f"### {r['batch']}\n\n")
            f.write(f"- source type: {r['source_type']}\n")
            f.write(f"- URL pattern: `{r['url_pattern'] or '(none)'}`\n")
            f.write(f"- file count: {r['file_count']}\n")
            f.write(f"- row count: {r['row_count']}\n")
            f.write(f"- pinned SHA-256: `{r['pinned_sha256']}` ({r['bytes']} bytes)\n")
            f.write(f"- PR #8 path: `{r['pr8_path'] or '(not in PR #8)'}`\n")
            f.write(f"- commit: `{r['commit_sha'] or '(n/a)'}`\n")
            f.write(f"- evidence form: {r['evidence_form']}; raw_bytes_saved={r['raw_bytes_saved']}\n")
            f.write(f"- review status: {r['review_status']}\n")
            f.write(f"- notes: {r['notes']}\n\n")

    # Markdown unknowns — summary + specials + compact table of all non8h rows
    unk_md_path = os.path.join(OUT, "nonh8_completeness_unknowns_v1_23.md")
    # interval / status breakdown
    def count_table(counter: Counter) -> str:
        rows = [{"key": k, "count": v} for k, v in counter.most_common()]
        return md_table(["key", "count"], rows, only=["key", "count"])

    compact_unk = [
        "record_kind", "inst_id", "month_cst", "observed_intervals",
        "observed_settlement_count", "observed_non_8h_count",
        "interval_change_visible", "interval_change_at_cst_date",
        "first_settlement_utc", "last_settlement_utc",
        "denominator_status", "inferred_interval", "inferred_expected_count",
        "boundary_crossing_settlement_count", "boundary_crossing_times_utc",
        "cst_vs_utc_completeness_may_differ", "cst_vs_utc_boundary_effect",
        "partial_month", "month_end_crossing_in_window",
    ]
    with open(unk_md_path, "w", encoding="utf-8") as f:
        f.write("""# Non-8H completeness unknowns (v1.23)

Observed official settlements are taken from already-saved official monthly
ZIPs (raw bytes) where a ZIP exists for the inventory month, and from the
already-saved 2026-11 REST parsed-JSON files otherwise. The frozen DB and
delta CSVs were not used as the official month source (they remain in the
source register as library inputs). No official file was refetched. No
zero-fill and no interpolation were applied.

**No official settlement-schedule source has been used.** Every expected-count
denominator that can be written down from these data is an *observed-assumption*
only: a constant interval that happens to span a full CST month. It is
inferred, not officially verified. Months that are not a full-month constant
interval (interval change, internal gaps, mid-month listing/delisting or a
shorter observed span, research-window truncation, irregular gaps, or too few
points) are **not determinable** from the saved data alone.

The research window is 2023-01-01T00:00:00Z to 2026-11-26T12:00:00Z inclusive.
CST months are UTC+8. `complete=true` in inventory r5 means passed per that
batch's source and comparison scope only, not a full-period or cross-frequency
verification. CST vs UTC month-boundary effects are flagged in dedicated
columns (see below; 復盤 Issue #1 comment 7239320542). 2026-11 is a partial
month with no month-end crossing in this window.

The full per-row listing is in `nonh8_completeness_unknowns_v1_23.csv`.
Self-run scans are team execution evidence, not ChatGPT runtime certification.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

""")
        f.write("## Summary counts\n\n")
        f.write(f"- Inventory months (r5): {len(inv_rows)}\n")
        f.write(f"- Official monthly ZIPs indexed (unique inst/month): {len(zip_index)}\n")
        f.write(f"- Months with at least one non-8H official settlement: {len(non8h_rows)}\n")
        f.write(f"- Months with official numeric settlements that are 8H-only (not listed as non-8H unknowns): {n_8h_only}\n")
        f.write(f"- Inventory months with no official numeric settlements in a saved ZIP/REST file: {n_empty_official}\n")
        f.write(f"- Non-8H months whose expected count is *inferred* from a constant full-month interval (not official): {derivable}\n")
        f.write(f"- Non-8H months whose expected count is not determinable from the saved data alone: {len(non8h_rows) - derivable}\n")
        f.write(f"- Additional known-gap rows listed even if they have no non-8H settlements: {len(special_rows)}\n\n")
        f.write("### Non-8H months by observed interval\n\n")
        f.write(count_table(interval_counts))
        f.write("\n\n### Non-8H months by denominator status\n\n")
        f.write(count_table(status_counts))
        f.write("\n\n## CST vs UTC month-boundary effects\n\n")
        f.write(
            "Funding completeness in this research is bucketed by CST (UTC+8) month; "
            "performance month buckets are UTC months, so boundaries can misalign "
            "(復盤 Issue #1 comment 7239320542). A settlement whose UTC timestamp is "
            "on or after 16:00Z on the last UTC day of a month falls in the **next CST "
            "month** and in the **current UTC month**. These crossings are counted "
            "*one by one* from saved official timestamps (not by formula). "
            "Typologically an 8H contract has exactly one such slot per month "
            "(16:00Z); 4H and 1H contracts may have several in the last 8 hours "
            "(4H: 16:00Z and 20:00Z; 1H: 16:00Z through 23:00Z).\n\n"
            "The research window ends 2026-11-26T12:00:00Z, so CST 2026-11 has "
            "**no month-end crossing** in the saved data and is labelled a "
            "partial month. Incoming opening crossings from 31 Oct 16:00Z+ are "
            "still counted when present.\n\n"
        )
        f.write(f"- Non-8H months with at least one observed opening boundary-crossing settlement: {n_non8h_with_crossings}\n")
        f.write(f"- Non-8H months flagged cst_vs_utc_completeness_may_differ=true: {n_non8h_may_differ}\n")
        f.write(f"- Non-8H CST 2026-11 rows (partial month, no month-end crossing in window): {n_non8h_2026_11}\n")
        f.write(f"- Opening boundary-crossing settlements counted one by one across non-8H months: {n_non8h_crossing_settlements}\n")
        f.write("\n### Non-8H months by opening crossing count\n\n")
        f.write(count_table(crossing_count_hist))
        f.write("\n\n### Non-8H months by CST-vs-UTC boundary effect\n\n")
        f.write(count_table(boundary_effect_counts))
        f.write("\n\n## Also listed: already-known gaps\n\n")
        f.write(
            "These are listed regardless of 8H/non-8H content.\n\n"
            "- OL-USDT-SWAP 2025-10: official_rate_null (1/85 literal `None` in the official monthly ZIP); inventory complete=false.\n"
            "- ZK-USDT-SWAP 2024-06: official_rate_null (1/54 literal `None` in the official monthly ZIP); inventory complete=false.\n"
            "- RVN-USDT-SWAP 2026-11: pending_check / rest_51001_instrument_not_listed. Stays in the universe; no zero-fill. Recheck when the CST 2026-11 official monthly ZIP is published.\n"
            "- 4 official ZIP 404s, reason unknown: CC-USDT-SWAP 2025-10, INJ-USDT-SWAP 2023-11, MEGA-USDT-SWAP 2026-04, ORDER-USDT-SWAP 2025-09 (`official_unavailable` / `404_reason_unknown`).\n\n"
        )
        f.write(md_table(UNKNOWN_FIELDS, special_rows + [r for r in non8h_rows if (r["inst_id"], r["month_cst"]) in special_keys], only=compact_unk))
        f.write("\n\n## All non-8H inst/month rows\n\n")
        f.write(md_table(UNKNOWN_FIELDS, non8h_rows, only=compact_unk))
        f.write("\n")

    end_utc = utc_now_iso()
    # manifest after CHANGELOG is added by the follow-up writer; write core now
    # and include produced files except CHANGELOG (added after).
    inputs = {
        "funding_month_inventory_v1_11_r5.csv": {"bytes": inv_bytes, "sha256": inv_sha, "rows": len(inv_rows)},
        "funding_archive_l1_isolated.sqlite": {"bytes": frozen_bytes, "sha256": frozen_sha, "rows": frozen_rows, "pr8_path": None},
    }
    summary = {
        "inventory_months": len(inv_rows),
        "official_zips_indexed": len(zip_index),
        "non8h_months": len(non8h_rows),
        "eight_h_only_months": n_8h_only,
        "empty_official_months": n_empty_official,
        "inferred_constant_full_month": derivable,
        "non8h_not_determinable": len(non8h_rows) - derivable,
        "special_known_gap_rows": len(special_rows),
        "unknown_file_rows": len(unknown_rows),
        "observed_intervals": dict(interval_counts),
        "denominator_status": dict(status_counts),
        "rest_2026_11_files": len(rest_files),
        "rest_2026_11_numeric_keys": rest_numeric_total,
        "zip_numeric_keys": zip_numeric_total,
        "zip_flagged_rows": zip_flagged_total,
        "non8h_with_opening_boundary_crossings": n_non8h_with_crossings,
        "non8h_opening_boundary_crossing_settlements": n_non8h_crossing_settlements,
        "non8h_cst_vs_utc_completeness_may_differ": n_non8h_may_differ,
        "non8h_2026_11_partial_no_month_end_crossing": n_non8h_2026_11,
        "non8h_crossing_count_histogram": {str(k): v for k, v in sorted(crossing_count_hist.items())},
        "non8h_boundary_effect": dict(boundary_effect_counts),
    }
    # files hashes filled after we finish writing? register/unknown already written.
    def meta(path: str, **extra: Any) -> dict[str, Any]:
        sha, size = sha256_file(path)
        d = {"bytes": size, "sha256": sha}
        d.update(extra)
        return d

    script_path = os.path.abspath(__file__) if os.path.isfile(__file__) else ""
    files_meta = {
        "funding_source_register_v1_23.csv": meta(reg_csv, rows=len(reg_rows)),
        "funding_source_register_v1_23.md": meta(reg_md_path),
        "nonh8_completeness_unknowns_v1_23.csv": meta(unk_csv, rows=len(unknown_rows)),
        "nonh8_completeness_unknowns_v1_23.md": meta(unk_md_path),
        "rest_2026_11_file_sha256s_v1_23.txt": meta(rest_listing_path, files=len(rest_files)),
    }
    if script_path:
        files_meta["build_sources_nonh8_v1_23_public.py"] = meta(script_path)

    manifest = {
        "research_id": "BACKTEST-READINESS-01",
        "version": "v1.23",
        "batch": "funding_sources_nonh8_v1_23",
        "start_utc": start_utc,
        "end_utc": end_utc,
        "mode": "offline_only_from_already_saved_files",
        "equivalent_list_in_repo": False,
        "equivalent_list_note": (
            "No existing funding_source_register or non-8H completeness-unknowns "
            "list was found on this branch. Per-batch manifests, inventory r5, "
            "evidence jsonl, and saved official files are inputs, not duplicates "
            "of this compilation."
        ),
        "window": {"win_lo_ms": WIN_LO, "win_hi_ms": WIN_HI, "win_hi_inclusive": True, "months_cst": "UTC+8"},
        "no_official_settlement_schedule_source_used": True,
        "denominator_policy": (
            "complete=true in inventory r5 is not used as a full-period denominator. "
            "inferred_constant_full_month means a single observed interval in {1H,4H,8H} "
            "spans the full CST month (which itself lies inside the research window) "
            "with no internal missing slots. That expected count is an observed-assumption, "
            "inferred and not officially verified. All other cases are not determinable "
            "from the saved data alone."
        ),
        "summary": summary,
        "inputs_sha256": inputs,
        "files": files_meta,
        "rule": (
            "v1.23 offline compilation of the funding source register and non-8H "
            "completeness unknowns from already-saved files only. No refetch, no "
            "backtest, no zero-fill, no universe or window change. No official "
            "settlement-schedule source was used; inferred denominators are not "
            "verified. Team execution evidence, not ChatGPT runtime certification. "
            "FIB-4H-LONG-V3 remains NO-GO; live_approved is false."
        ),
    }
    mf_p = os.path.join(OUT, "funding_sources_nonh8_v1_23_manifest.json")
    open(mf_p, "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    log(f"DONE non8h={len(non8h_rows)} inferred={derivable} not_determinable={len(non8h_rows)-derivable} end_utc={end_utc}")
    # sidecar counts (not for commit)
    open(os.path.join(OUT, "funding_sources_nonh8_v1_23_counts.json"), "w", encoding="utf-8").write(
        json.dumps({"start_utc": start_utc, "end_utc": end_utc, "summary": summary}, indent=2, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
