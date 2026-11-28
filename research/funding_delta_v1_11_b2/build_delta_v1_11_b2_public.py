# Publishable copy of build_delta_v1_11_b2.py.
# Local data locations are relative/config constants — set B2_* environment
# variables or edit the path constants before running.
# This file contains no host absolute paths and no secrets.

#!/usr/bin/env python3
"""BACKTEST-READINESS-01 v1.11-b2 — official funding delta, parts A and B.

Offline research data prep only. Does not trade, run strategies, refetch
candles, expand the universe or window, zero-fill, interpolate, modify the
frozen DB, blindly INSERT, redo the v1.11 inventory, refetch the 85 already
verified monthly ZIPs, or publish anything.

Part A: download official monthly ZIPs for every inventory pair that was
labelled confirmed_missing (a priority-candidate set, not a completeness
claim) and key-compare every official settlement row.

Part B: CST 2026-11 is unpublished as a monthly ZIP, so page the official
REST /api/v5/public/funding-rate-history for every EX_USDC_286 symbol,
keeping rows with fundingTime in [2026-10-31T16:00:00Z, 2026-11-26T12:00:00Z].
Window end is not changed. No zero-fill.

Compare official rows against frozen + v1.7/v1.9/v1.10/v1.11_b1, keyed by
(inst_id, snap to nearest hour), same rules as v1_10_full_ingest.py /
v1_11_b1.py. Manifest conclusions come only from that key-by-key comparison.
pending_check months are not key-compared in this batch and are not complete.
"""

from __future__ import annotations

import bisect
import csv
import gzip
import hashlib
import io
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Paths — box run uses these defaults; the public copy uses relative names.
# ---------------------------------------------------------------------------
OUT = os.environ.get(
    "B2_OUT",
    "funding_delta_v1_11_b2",
)
INV_IN = os.environ.get(
    "B2_INV_IN",
    "funding_month_inventory_v1_11.csv",
)
INV_SCRIPT = os.environ.get(
    "B2_INV_SCRIPT",
    "build_inventory_v1_11.py",
)
FROZEN_DB = os.environ.get(
    "B2_FROZEN_DB",
    "funding_archive_l1_isolated.sqlite",
)
DELTA_ROOT = os.environ.get(
    "B2_DELTA_ROOT",
    "backtest_readiness_01",
)
# First process start of this batch (interrupted after 900 ZIPs). Do not reset.
ORIGINAL_START_UTC = "2026-11-27T23:30:19Z"

ZDIR = os.path.join(OUT, "official_monthly_zips")
RDIR = os.path.join(OUT, "rest_2026_11")
EVIDENCE_NAME = "fetch_evidence_v1_11_b2.jsonl"
INSTRUMENTS_NAME = "instruments_swap_v1_11_b2.json.gz"

DELTA_CSVS = [
    ("v1_7", os.path.join(DELTA_ROOT, "funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz")),
    ("v1_9", os.path.join(DELTA_ROOT, "funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz")),
    ("v1_10", os.path.join(DELTA_ROOT, "funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz")),
    ("v1_11_b1", os.path.join(DELTA_ROOT, "funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz")),
]
INPUT_LABELS = [
    ("funding_archive_l1_isolated.sqlite", FROZEN_DB),
    ("funding_delta_missing16_v1_7.csv.gz", DELTA_CSVS[0][1]),
    ("funding_delta_missing174_v1_9.csv.gz", DELTA_CSVS[1][1]),
    ("funding_delta_full75plus_v1_10.csv.gz", DELTA_CSVS[2][1]),
    ("funding_delta_5sym_v1_11_b1.csv.gz", DELTA_CSVS[3][1]),
    ("funding_month_inventory_v1_11.csv", INV_IN),
]

RESEARCH_ID = "BACKTEST-READINESS-01"
VERSION = "v1.11-batch2"
USER_AGENT = "BACKTEST-READINESS-01-v1.11-b2 (research; offline-prep)"
MIN_INTERVAL_S = 0.21  # ~5 req/s
MAX_RETRIES = 6

RANGE_LO_MS = int(datetime(2026, 10, 31, 16, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
RANGE_HI_MS = int(datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
CST = timezone(timedelta(hours=8))

CDN_TMPL = (
    "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/"
    "{yyyymm}/{inst}-fundingrates-{yyyy}-{mm}.zip"
)
REST_BASE = "https://www.okx.com/api/v5/public/funding-rate-history"
REST_LIMIT = 400
INSTRUMENTS_URL = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"

SOURCE_YM_ZIP = "v1_11_b2_okx_cdn_swaprates_monthly_zip"
SOURCE_YM_REST = "v1_11_b2_okx_funding_rate_history"

HOUR_MS = 3600 * 1000
EIGHT_H_MS = 8 * HOUR_MS

# Inventory 404 pairs (official monthly ZIP unlisted + CDN HEAD 404 in v1.11).
# These four and only these four, excluding the unpublished 2026-11 month.
FOUR_404 = [
    ("CC-USDT-SWAP", "2025-10"),
    ("INJ-USDT-SWAP", "2023-11"),
    ("MEGA-USDT-SWAP", "2026-04"),
    ("ORDER-USDT-SWAP", "2025-09"),
]
# All four 404 pairs keep sub_reason 404_reason_unknown. Official listTime
# is attached only as an evidence field and is never used to reclassify.
CSV_FIELDS = [
    "inst_id",
    "funding_time_ms",
    "funding_time_utc",
    "ts_snapped_ms",
    "ts_snapped_utc",
    "snap_offset_ms",
    "funding_rate",
    "is_8h_grid",
    "prev_gap_h",
    "next_gap_h",
    "source_month_cst",
    "fetched_utc",
    "source_ym",
    "source_kind",
    "rate_field",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso(ms: int, frac: bool = False) -> str:
    d = datetime.fromtimestamp(ms / 1000.0, timezone.utc)
    if frac:
        return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms % 1000:03d}Z"
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def file_mtime_utc(path: str) -> str:
    return datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def snap(ms: int) -> int:
    return int(round(ms / float(HOUR_MS))) * HOUR_MS


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fs_rel(path: str) -> dict[str, Any]:
    b = open(path, "rb").read()
    return {"bytes": len(b), "sha256": sha256_bytes(b)}


def log(msg: str) -> None:
    print(f"[{utc_now_iso()}] {msg}", flush=True)


_last_req_t = 0.0
_EVIDENCE_PATH = ""


def _rate_limit() -> None:
    global _last_req_t
    now = time.monotonic()
    wait = MIN_INTERVAL_S - (now - _last_req_t)
    if wait > 0:
        time.sleep(wait)
    _last_req_t = time.monotonic()


def evidence_write(entry: dict[str, Any]) -> None:
    if not _EVIDENCE_PATH:
        return
    with open(_EVIDENCE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def http_get(url: str, kind: str, log_evidence: bool = True) -> tuple[int | str, bytes | None, str]:
    """GET with ~5 req/s and backoff on 429/5xx. Returns (status, body, request_utc).

    Never retries HTTP 403, never sends credentials, and never tries to bypass a 403.
    """
    last_err: Exception | str | None = None
    request_utc = utc_now_iso()
    for attempt in range(1, MAX_RETRIES + 1):
        _rate_limit()
        request_utc = utc_now_iso()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = int(resp.status)
                body = resp.read()
                if log_evidence:
                    evidence_write(
                        {
                            "url": url,
                            "request_utc": request_utc,
                            "http": status,
                            "response_bytes": len(body),
                            "response_sha256": sha256_bytes(body),
                            "kind": kind,
                            "attempt": attempt,
                        }
                    )
                return status, body, request_utc
        except urllib.error.HTTPError as e:
            body = e.read()
            if log_evidence:
                evidence_write(
                    {
                        "url": url,
                        "request_utc": request_utc,
                        "http": int(e.code),
                        "response_bytes": len(body) if body else 0,
                        "response_sha256": sha256_bytes(body) if body else None,
                        "kind": kind,
                        "attempt": attempt,
                    }
                )
            if e.code == 403:
                log(f"HTTP 403 not retried (no credentials, no bypass) {url}")
                return 403, body if body else None, request_utc
            if e.code in {429, 500, 502, 503, 504} and attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"HTTP {e.code} retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s {url}")
                time.sleep(backoff)
                last_err = e
                continue
            return int(e.code), body if body else None, request_utc
        except Exception as e:
            last_err = e
            if log_evidence:
                evidence_write(
                    {
                        "url": url,
                        "request_utc": request_utc,
                        "http": None,
                        "response_bytes": 0,
                        "response_sha256": None,
                        "kind": kind,
                        "attempt": attempt,
                        "error": f"{type(e).__name__}:{e}",
                    }
                )
            if attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"{type(e).__name__}: {e}; retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                continue
            return f"{type(e).__name__}:{e}", None, request_utc
    return f"failed:{last_err}", None, request_utc


def http_head(url: str, kind: str) -> tuple[int | str, str]:
    last_err: Exception | str | None = None
    request_utc = utc_now_iso()
    for attempt in range(1, MAX_RETRIES + 1):
        _rate_limit()
        request_utc = utc_now_iso()
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = int(resp.status)
                # HEAD has no body; record sha of empty body as null, bytes 0.
                evidence_write(
                    {
                        "url": url,
                        "request_utc": request_utc,
                        "http": status,
                        "response_bytes": 0,
                        "response_sha256": None,
                        "kind": kind,
                        "method": "HEAD",
                        "attempt": attempt,
                    }
                )
                return status, request_utc
        except urllib.error.HTTPError as e:
            try:
                _ = e.read()
            except Exception:
                pass
            evidence_write(
                {
                    "url": url,
                    "request_utc": request_utc,
                    "http": int(e.code),
                    "response_bytes": 0,
                    "response_sha256": None,
                    "kind": kind,
                    "method": "HEAD",
                    "attempt": attempt,
                }
            )
            if e.code in {429, 500, 502, 503, 504} and attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"HEAD HTTP {e.code} retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                last_err = e
                continue
            return int(e.code), request_utc
        except Exception as e:
            last_err = e
            evidence_write(
                {
                    "url": url,
                    "request_utc": request_utc,
                    "http": None,
                    "response_bytes": 0,
                    "response_sha256": None,
                    "kind": kind,
                    "method": "HEAD",
                    "attempt": attempt,
                    "error": f"{type(e).__name__}:{e}",
                }
            )
            if attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"HEAD {type(e).__name__}: {e}; retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                continue
            return f"{type(e).__name__}:{e}", request_utc
    return f"failed:{last_err}", request_utc


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def hash_inputs() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, path in INPUT_LABELS:
        if not os.path.isfile(path):
            out[label] = {"error": "missing"}
            continue
        out[label] = {"bytes": os.path.getsize(path), "sha256": sha256_file(path)}
        log(f"Input SHA {label} {out[label]['bytes']} {out[label]['sha256']}")
    return out


def load_inventory() -> tuple[list[dict[str, str]], list[tuple[str, str]], list[str]]:
    with open(INV_IN, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [(r["inst_id"], r["month_cst"]) for r in rows if r["class"] == "confirmed_missing"]
    nov = sorted({r["inst_id"] for r in rows if r["month_cst"] == "2026-11"})
    if len(missing) != 1279:
        log(f"WARNING: expected 1279 confirmed_missing candidates, got {len(missing)}")
    if len(nov) != 286:
        log(f"WARNING: expected 286 2026-11 symbols, got {len(nov)}")
    four = [
        (r["inst_id"], r["month_cst"])
        for r in rows
        if r["class"] == "official_unavailable" and r["sub_reason"] == "404"
    ]
    if sorted(four) != sorted(FOUR_404):
        log(f"WARNING: inventory 404 pairs {four} != expected {FOUR_404}")
    else:
        log("Confirmed inventory 404 months are exactly the expected 4 pairs")
    return rows, missing, nov


def load_existing(insts: set[str]) -> dict[tuple[str, int], tuple[str, int, float]]:
    existing: dict[tuple[str, int], tuple[str, int, float]] = {}
    log("Loading frozen funding_archive (read-only)…")
    con = sqlite3.connect(f"file:{FROZEN_DB}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        n = 0
        for inst in sorted(insts):
            for i, sn, tr, rate in con.execute(
                "SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive WHERE inst_id=?",
                (inst,),
            ):
                existing[(i, int(sn))] = ("frozen_829157", int(tr), float(rate))
                n += 1
        log(f"Frozen rows loaded for selected insts: {n}")
    finally:
        con.close()
    for tag, path in DELTA_CSVS:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
            added = 0
            for r in csv.DictReader(f):
                inst = r["inst_id"]
                if inst not in insts:
                    continue
                k = (inst, int(r["ts_snapped_ms"]))
                if k not in existing:
                    existing[k] = (tag, int(r["funding_time_ms"]), float(r["funding_rate"]))
                    added += 1
            log(f"Delta {tag}: {added} additional keys")
    return existing


# ---------------------------------------------------------------------------
# Official instruments snapshot
# ---------------------------------------------------------------------------
def month_cst_bounds_ms(month_cst: str) -> tuple[int, int]:
    y, m = map(int, month_cst.split("-"))
    start = datetime(y, m, 1, 0, 0, 0, tzinfo=CST)
    if m == 12:
        end = datetime(y + 1, 1, 1, 0, 0, 0, tzinfo=CST)
    else:
        end = datetime(y, m + 1, 1, 0, 0, 0, tzinfo=CST)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def listtime_in_month_end_no_settlement(list_time_ms: int, month_cst: str) -> bool:
    """True if official listTime is in this CST month after its last 8H settlement.

    CST month ends at 16:00 UTC on the last calendar day; the last 8H grid point
    in the month is 08:00 UTC that day. A listing in (08:00, 16:00) UTC has no
    official 8H settlement in that CST month.
    """
    start, end = month_cst_bounds_ms(month_cst)
    last_8h = end - EIGHT_H_MS
    return start <= list_time_ms < end and list_time_ms > last_8h


def fetch_instruments() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    log("Fetching official instruments?instType=SWAP …")
    st, body, request_utc = http_get(INSTRUMENTS_URL, kind="instruments")
    if st != 200 or not body:
        raise RuntimeError(f"instruments fetch failed http={st}")
    payload = json.loads(body.decode())
    if str(payload.get("code")) != "0":
        raise RuntimeError(f"instruments API code={payload.get('code')} msg={payload.get('msg')}")
    raw_gz = os.path.join(OUT, INSTRUMENTS_NAME)
    with gzip.GzipFile(raw_gz, "wb", mtime=0) as g:
        g.write(body)
    disk = open(raw_gz, "rb").read()
    meta = {
        "url": INSTRUMENTS_URL,
        "request_utc": request_utc,
        "http": st,
        "file": INSTRUMENTS_NAME,
        "raw_bytes": len(disk),
        "raw_sha256": sha256_bytes(disk),
        "response_bytes": len(body),
        "response_sha256": sha256_bytes(body),
        "rows": len(payload.get("data") or []),
    }
    by_id: dict[str, dict[str, Any]] = {}
    for row in payload.get("data") or []:
        inst = row.get("instId")
        if inst:
            by_id[inst] = row
    log(f"Instruments snapshot rows={meta['rows']} sha={meta['raw_sha256']}")
    return meta, by_id


def classify_404(by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """All 4 inventory 404 pairs stay 404_reason_unknown.

    Official instruments listTime/state are recorded as evidence only and
    are never used to reclassify the pair.
    """
    out: list[dict[str, Any]] = []
    for inst, month in FOUR_404:
        row = by_id.get(inst) or {}
        list_time_raw = row.get("listTime")
        state = row.get("state")
        list_time_ms = int(list_time_raw) if list_time_raw not in (None, "") else None
        list_time_utc = iso(list_time_ms, True) if list_time_ms is not None else None
        in_window = (
            listtime_in_month_end_no_settlement(list_time_ms, month)
            if list_time_ms is not None
            else False
        )
        out.append(
            {
                "inst_id": inst,
                "month_cst": month,
                "state": state,
                "listTime_ms": list_time_ms,
                "listTime_utc": list_time_utc,
                "listTime_in_month_end_no_settlement_window": in_window,
                "sub_reason": "404_reason_unknown",
                "note": (
                    "sub_reason remains 404_reason_unknown for all four 404 pairs. "
                    "Official instruments listTime and state are evidence only and "
                    "were not used to reclassify."
                ),
            }
        )
        log(f"404 {inst} {month} state={state} listTime={list_time_utc} sub=404_reason_unknown (evidence only)")
    return out


def head_four_404() -> list[dict[str, Any]]:
    results = []
    for inst, month in FOUR_404:
        yyyy, mm = month.split("-")
        url = CDN_TMPL.format(yyyymm=yyyy + mm, inst=inst, yyyy=yyyy, mm=mm)
        st, request_utc = http_head(url, kind="cdn_head_404_confirm")
        results.append(
            {
                "inst_id": inst,
                "month_cst": month,
                "url": url,
                "http": st,
                "request_utc": request_utc,
            }
        )
        log(f"HEAD 404-confirm {inst} {month} http={st}")
    return results


# ---------------------------------------------------------------------------
# Part A — official monthly ZIPs (resume-safe; do not re-download saved files)
# ---------------------------------------------------------------------------
def parse_zip_bytes(inst: str, ym: str, blob: bytes) -> tuple[list[dict[str, str]], list[int]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        if not names:
            raise ValueError("zip has no entries")
        txt = zf.read(names[0]).decode()
    rows = list(csv.DictReader(io.StringIO(txt)))
    tss: list[int] = []
    for r in rows:
        name = (r.get("instrument_name") or "").strip()
        if name != inst:
            raise ValueError(f"instrument_name mismatch: {name!r} != {inst!r}")
        tss.append(int(r["funding_time"]))
    return rows, tss


def fetch_part_a(pairs: list[tuple[str, str]]) -> tuple[list[dict[str, Any]], list[tuple]]:
    os.makedirs(ZDIR, exist_ok=True)
    src_months: list[dict[str, Any]] = []
    official: list[tuple] = []
    t0 = time.monotonic()
    ok = fail = reused_n = 0
    for i, (inst, ym) in enumerate(pairs, 1):
        yyyy, mm = ym.split("-")
        url = CDN_TMPL.format(yyyymm=yyyy + mm, inst=inst, yyyy=yyyy, mm=mm)
        fn = f"{inst}-fundingrates-{ym}.zip"
        rel = f"official_monthly_zips/{fn}"
        path = os.path.join(ZDIR, fn)
        reused = False
        st: int | str
        blob: bytes | None
        fetched: str
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            blob = open(path, "rb").read()
            try:
                parse_zip_bytes(inst, ym, blob)
                st = 200
                reused = True
                fetched = file_mtime_utc(path)
                evidence_write(
                    {
                        "url": url,
                        "request_utc": fetched,
                        "http": 200,
                        "response_bytes": len(blob),
                        "response_sha256": sha256_bytes(blob),
                        "kind": "monthly_zip",
                        "reused": True,
                        "file": rel,
                        "note": "Body kept from the interrupted first pass of this batch; not re-downloaded.",
                    }
                )
            except Exception:
                blob = None
                st, blob, fetched = http_get(url, kind="monthly_zip")
        else:
            st, blob, fetched = http_get(url, kind="monthly_zip")
        ent: dict[str, Any] = {
            "inst_id": inst,
            "month_cst": ym,
            "source_kind": "monthly_zip",
            "url": url,
            "http": st,
            "fetched_utc": fetched,
            "reused_existing_zip": reused,
            "file": rel,
        }
        if st == 200 and blob:
            if not reused:
                with open(path, "wb") as f:
                    f.write(blob)
            try:
                rows, tss = parse_zip_bytes(inst, ym, blob)
            except Exception as e:
                ent["error"] = f"{type(e).__name__}:{e}"
                fail += 1
                src_months.append(ent)
                log(f"Part A parse error {inst} {ym}: {e}")
                continue
            ent.update(
                {
                    "zip_bytes": len(blob),
                    "zip_sha256": sha256_bytes(blob),
                    "rows": len(rows),
                    "min_ts_utc": iso(min(tss)) if tss else None,
                    "max_ts_utc": iso(max(tss)) if tss else None,
                }
            )
            for r in rows:
                tr = int(r["funding_time"])
                official.append(
                    (
                        inst,
                        tr,
                        snap(tr),
                        (r["funding_rate"] or "").strip(),
                        ym,
                        fetched,
                        "monthly_zip",
                        "funding_rate",
                    )
                )
            ok += 1
            if reused:
                reused_n += 1
        else:
            ent["error"] = "http_not_200_or_empty_body"
            fail += 1
        src_months.append(ent)
        if i % 50 == 0 or i == len(pairs):
            log(
                f"Part A {i}/{len(pairs)} ok={ok} reused={reused_n} fail={fail} "
                f"official_rows={len(official)} {time.monotonic()-t0:.1f}s"
            )
    return src_months, official


# ---------------------------------------------------------------------------
# Part B — REST funding-rate-history for CST 2026-11
# ---------------------------------------------------------------------------
def pick_rate(row: dict[str, Any]) -> tuple[str | None, str | None]:
    realized = row.get("realizedRate")
    funding = row.get("fundingRate")
    realized_s = realized.strip() if isinstance(realized, str) else (None if realized is None else str(realized).strip())
    funding_s = funding.strip() if isinstance(funding, str) else (None if funding is None else str(funding).strip())
    if realized_s not in (None, ""):
        return realized_s, "realizedRate"
    if funding_s not in (None, ""):
        return funding_s, "fundingRate"
    return None, None


def fetch_part_b(symbols: list[str]) -> tuple[list[dict[str, Any]], list[tuple], list[dict[str, Any]]]:
    os.makedirs(RDIR, exist_ok=True)
    src_months: list[dict[str, Any]] = []
    official: list[tuple] = []
    anomalies: list[dict[str, Any]] = []
    t0 = time.monotonic()
    ok = fail = 0
    prior_traces: dict[str, list] = {}
    prior_src = os.path.join(OUT, "funding_source_months_v1_11_b2.json")
    if os.path.isfile(prior_src):
        try:
            for rec in json.load(open(prior_src, encoding="utf-8")):
                if rec.get("source_kind") == "rest_history" and rec.get("paging_trace"):
                    prior_traces[rec["inst_id"]] = rec["paging_trace"]
        except Exception:
            prior_traces = {}
    for i, inst in enumerate(symbols, 1):
        raw_name = f"{inst}.json.gz"
        rel = f"rest_2026_11/{raw_name}"
        path = os.path.join(RDIR, raw_name)
        pages: list[dict[str, Any]] = []
        traces: list[dict[str, Any]] = []
        http_statuses: list[int | str] = []
        after = RANGE_HI_MS + 1
        err: str | None = None
        last_page_short = False
        reused_rest = False
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            try:
                saved = json.loads(gzip.open(path, "rt", encoding="utf-8").read())
                pages = saved.get("pages") or []
                if pages:
                    reused_rest = True
                    for p0 in pages:
                        st = p0.get("http")
                        http_statuses.append(st)
                        body = p0.get("response") or {}
                        data = (body.get("data") or []) if isinstance(body, dict) else []
                        page_times: list[int] = []
                        for row in data:
                            try:
                                page_times.append(int(row["fundingTime"]))
                            except Exception:
                                pass
                        raw_page = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
                        traces.append(
                            {
                                "url": p0.get("url"),
                                "request_utc": p0.get("fetched_utc"),
                                "http": st,
                                "row_count": len(data),
                                "min_fundingTime": min(page_times) if page_times else None,
                                "max_fundingTime": max(page_times) if page_times else None,
                                "min_fundingTime_utc": iso(min(page_times)) if page_times else None,
                                "max_fundingTime_utc": iso(max(page_times)) if page_times else None,
                                "response_sha256": sha256_bytes(raw_page),
                                "response_bytes": len(raw_page),
                                "reused": True,
                            }
                        )
                        if st == 403:
                            err = "http=403 (not retried, no credentials, not bypassed)"
                        elif st != 200 or not isinstance(body, dict) or str(body.get("code")) != "0":
                            err = (
                                f"http={st} code={body.get('code') if isinstance(body, dict) else None} "
                                f"msg={body.get('msg') if isinstance(body, dict) else None}"
                            )
                        if not data or (page_times and min(page_times) <= RANGE_LO_MS) or len(data) < REST_LIMIT:
                            last_page_short = bool(not data or len(data) < REST_LIMIT)
            except Exception as e:
                log(f"REST reuse failed for {inst}: {e}; will refetch")
                pages, traces, http_statuses, err, reused_rest = [], [], [], None, False
            if reused_rest and inst in prior_traces:
                traces = prior_traces[inst]
        while not reused_rest:
            url = f"{REST_BASE}?instId={inst}&after={after}&limit={REST_LIMIT}"
            st, blob, fetched = http_get(url, kind="rest_history")
            http_statuses.append(st)
            page_sha = sha256_bytes(blob) if blob else None
            raw_text = blob.decode() if blob else ""
            try:
                body = json.loads(raw_text) if raw_text else {"code": str(st), "data": [], "msg": "empty body"}
            except Exception as e:
                body = {"code": "parse_error", "data": [], "msg": f"{type(e).__name__}:{e}", "raw": raw_text[:2000]}
                err = f"json_parse:{e}"
            data = (body.get("data") or []) if isinstance(body, dict) else []
            page_times: list[int] = []
            for row in data:
                try:
                    page_times.append(int(row["fundingTime"]))
                except Exception:
                    pass
            traces.append(
                {
                    "url": url,
                    "request_utc": fetched,
                    "http": st,
                    "row_count": len(data),
                    "min_fundingTime": min(page_times) if page_times else None,
                    "max_fundingTime": max(page_times) if page_times else None,
                    "min_fundingTime_utc": iso(min(page_times)) if page_times else None,
                    "max_fundingTime_utc": iso(max(page_times)) if page_times else None,
                    "response_sha256": page_sha,
                    "response_bytes": len(blob) if blob else 0,
                }
            )
            pages.append({"url": url, "fetched_utc": fetched, "http": st, "response": body})
            if st == 403:
                err = err or "http=403 (not retried, no credentials, not bypassed)"
                break
            if st != 200 or not isinstance(body, dict) or str(body.get("code")) != "0":
                err = err or (
                    f"http={st} code={body.get('code') if isinstance(body, dict) else None} "
                    f"msg={body.get('msg') if isinstance(body, dict) else None}"
                )
                break
            if not data:
                last_page_short = True
                break
            oldest = min(page_times) if page_times else after
            if oldest <= RANGE_LO_MS:
                break
            if len(data) < REST_LIMIT:
                last_page_short = True
                break
            after = oldest

        raw_obj = {
            "inst_id": inst,
            "month_cst": "2026-11",
            "range_start_utc": iso(RANGE_LO_MS),
            "range_end_utc": iso(RANGE_HI_MS),
            "pages": pages,
        }
        raw_bytes = (json.dumps(raw_obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        with gzip.GzipFile(path, "wb", mtime=0) as g:
            g.write(raw_bytes)
        raw_on_disk = open(path, "rb").read()

        first_fetched = pages[0]["fetched_utc"] if pages else utc_now_iso()
        first_url = pages[0]["url"] if pages else f"{REST_BASE}?instId={inst}&limit={REST_LIMIT}"
        http_out: int | str = http_statuses[0] if http_statuses else "none"
        if all(s == 200 for s in http_statuses) and err is None:
            http_out = 200

        in_range: list[dict[str, Any]] = []
        unfiltered = 0
        if err is None:
            for p in pages:
                body = p.get("response") or {}
                if not isinstance(body, dict) or str(body.get("code")) != "0":
                    continue
                for row in body.get("data") or []:
                    unfiltered += 1
                    try:
                        tr = int(row["fundingTime"])
                    except Exception:
                        anomalies.append({"inst_id": inst, "reason": "bad_fundingTime", "row": row})
                        continue
                    if tr < RANGE_LO_MS or tr > RANGE_HI_MS:
                        continue
                    if (row.get("instId") or inst) != inst:
                        anomalies.append({"inst_id": inst, "reason": "instId_mismatch", "row": row})
                        continue
                    rate, field = pick_rate(row)
                    if rate is None or field is None:
                        anomalies.append({"inst_id": inst, "reason": "empty_rate_fields", "fundingTime": tr})
                        continue
                    in_range.append({"tr": tr, "rate": rate, "field": field, "fetched_utc": p["fetched_utc"]})

        tss = [x["tr"] for x in in_range]
        all_fetched_ts: list[int] = [
            int(t)
            for tr in traces
            for t in (tr.get("min_fundingTime"), tr.get("max_fundingTime"))
            if t is not None
        ]
        # Reconstruct the full unfiltered time span from page min/max is not enough
        # for "reached window start"; use every page's min (oldest on that page).
        page_oldests = [tr["min_fundingTime"] for tr in traces if tr.get("min_fundingTime") is not None]
        page_newests = [tr["max_fundingTime"] for tr in traces if tr.get("max_fundingTime") is not None]
        oldest_fetched = min(page_oldests) if page_oldests else None
        newest_fetched = max(page_newests) if page_newests else None
        reached_start = oldest_fetched is not None and oldest_fetched <= RANGE_LO_MS
        limitation = None
        limitation_code = None
        fully_covered = False
        if err:
            err_s = str(err)
            if "http=403" in err_s or (http_statuses and 403 in http_statuses):
                limitation_code = "rest_http_403"
                limitation = (
                    "HTTP 403 on official funding-rate-history; not retried with "
                    "credentials and not bypassed. Window end unchanged, no zero-fill."
                )
            elif "http=429" in err_s or (http_statuses and 429 in http_statuses):
                limitation_code = "rest_http_429"
                limitation = (
                    "HTTP 429 on official funding-rate-history after backoff retries "
                    "exhausted. Window end unchanged, no zero-fill."
                )
            else:
                limitation_code = "rest_error"
                limitation = f"REST history request failed: {err}. Window end unchanged, no zero-fill."
        elif not reached_start:
            limitation_code = "rest_retention_gap"
            limitation = (
                "REST history did not reach the window start "
                f"{iso(RANGE_LO_MS)}; oldest fetched official fundingTime is "
                f"{iso(oldest_fetched) if oldest_fetched is not None else 'none'}"
                f"{' (API history exhausted before the window start)' if last_page_short else ''}. "
                "Window end unchanged, no zero-fill."
            )
        else:
            fully_covered = True

        coverage = {
            "window_start_utc": iso(RANGE_LO_MS),
            "window_end_utc": iso(RANGE_HI_MS),
            "oldest_fetched_utc": iso(oldest_fetched) if oldest_fetched is not None else None,
            "newest_fetched_utc": iso(newest_fetched) if newest_fetched is not None else None,
            "in_range_min_utc": iso(min(tss)) if tss else None,
            "in_range_max_utc": iso(max(tss)) if tss else None,
            "in_range_rows": len(in_range),
            "reached_window_start": reached_start,
            "fully_covered": fully_covered,
            "limitation": limitation,
            "limitation_code": limitation_code,
        }
        ent: dict[str, Any] = {
            "inst_id": inst,
            "month_cst": "2026-11",
            "source_kind": "rest_history",
            "url": first_url,
            "urls": [p["url"] for p in pages],
            "http": http_out,
            "fetched_utc": first_fetched,
            "pages": len(pages),
            "paging_trace": traces,
            "coverage": coverage,
            "fully_covered": fully_covered,
            "file": rel,
            "raw_bytes": len(raw_on_disk),
            "raw_sha256": sha256_bytes(raw_on_disk),
            "rows": len(in_range),
            "rows_fetched_unfiltered": unfiltered,
            "min_ts_utc": iso(min(tss)) if tss else None,
            "max_ts_utc": iso(max(tss)) if tss else None,
        }
        if limitation:
            ent["limitation"] = limitation
            ent["limitation_code"] = limitation_code
        if err:
            ent["error"] = err
            fail += 1
        elif fully_covered:
            ok += 1
        else:
            fail += 1
        for x in in_range:
            official.append(
                (
                    inst,
                    x["tr"],
                    snap(x["tr"]),
                    x["rate"],
                    "2026-11",
                    x["fetched_utc"],
                    "rest_history",
                    x["field"],
                )
            )
        src_months.append(ent)
        if i % 20 == 0 or i == len(symbols):
            log(
                f"Part B {i}/{len(symbols)} ok={ok} fail={fail} official_rows={len(official)} "
                f"{time.monotonic()-t0:.1f}s"
            )
    return src_months, official, anomalies


# ---------------------------------------------------------------------------
# Compare + write
# ---------------------------------------------------------------------------
def compare(
    official: list[tuple],
    existing: dict[tuple[str, int], tuple[str, int, float]],
) -> tuple[list[tuple], list[dict[str, Any]], list[list], int, dict[str, int]]:
    seen: dict[tuple[str, int], tuple] = {}
    intra_dup: list[list] = []
    for o in official:
        k = (o[0], o[2])
        if k in seen:
            prev = seen[k]
            if prev[1] != o[1] or float(prev[3]) != float(o[3]):
                intra_dup.append([*prev[:5], *o[:5]])
            continue
        seen[k] = o

    new_rows: list[tuple] = []
    conflicts: list[dict[str, Any]] = []
    matched = 0
    matched_by: Counter[str] = Counter()
    new_by: Counter[str] = Counter()
    conf_by: Counter[str] = Counter()
    for k, o in seen.items():
        kind = o[6]
        if k in existing:
            src, tr, rate = existing[k]
            rd = abs(float(o[3]) - float(rate)) > 1e-15
            td = tr != o[1]
            if rd or td:
                conflicts.append(
                    {
                        "inst_id": k[0],
                        "ts_snapped_ms": k[1],
                        "existing_source": src,
                        "existing_ts_raw_ms": tr,
                        "existing_rate": repr(rate),
                        "official_ts_raw_ms": o[1],
                        "official_rate": o[3],
                        "official_month_cst": o[4],
                        "official_source_kind": kind,
                        "type": "+".join(
                            [x for x, c in (("rate_diff", rd), ("ts_raw_diff", td)) if c]
                        ),
                    }
                )
                conf_by[kind] += 1
            else:
                matched += 1
                matched_by[kind] += 1
        else:
            new_rows.append(o)
            new_by[kind] += 1
    split = {
        "matched_monthly_zip": matched_by["monthly_zip"],
        "matched_rest_history": matched_by["rest_history"],
        "new_monthly_zip": new_by["monthly_zip"],
        "new_rest_history": new_by["rest_history"],
        "conflicts_monthly_zip": conf_by["monthly_zip"],
        "conflicts_rest_history": conf_by["rest_history"],
    }
    return new_rows, conflicts, intra_dup, matched, split


def write_delta(new_rows: list[tuple], official_seen_keys: dict[tuple[str, int], tuple]) -> tuple[str, bytes, dict[str, int], dict[str, dict[str, int]]]:
    by_inst: dict[str, list[int]] = {}
    for inst, sn in official_seen_keys:
        by_inst.setdefault(inst, []).append(sn)
    for v in by_inst.values():
        v.sort()

    def gaps(inst: str, sn: int) -> tuple[float | None, float | None]:
        a = by_inst[inst]
        i = bisect.bisect_left(a, sn)
        p = (sn - a[i - 1]) / 3.6e6 if i > 0 else None
        n = (a[i + 1] - sn) / 3.6e6 if i + 1 < len(a) else None
        return p, n

    new_rows = sorted(new_rows, key=lambda o: (o[0], o[2]))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_FIELDS)
    grid = {"8h": 0, "non_8h": 0}
    grid_by = {
        "monthly_zip": {"8h": 0, "non_8h": 0},
        "rest_history": {"8h": 0, "non_8h": 0},
    }
    for o in new_rows:
        inst, tr, sn, rate, ym, fetched, kind, field = o
        p, n = gaps(inst, sn)
        is8 = sn % EIGHT_H_MS == 0
        grid["8h" if is8 else "non_8h"] += 1
        grid_by[kind]["8h" if is8 else "non_8h"] += 1
        source_ym = SOURCE_YM_ZIP if kind == "monthly_zip" else SOURCE_YM_REST
        w.writerow(
            [
                inst,
                tr,
                iso(tr, True),
                sn,
                iso(sn),
                tr - sn,
                rate,
                "true" if is8 else "false",
                p,
                n,
                ym,
                fetched,
                source_ym,
                kind,
                field,
            ]
        )
    csv_b = buf.getvalue().encode()
    delta_p = os.path.join(OUT, "funding_delta_v1_11_b2.csv.gz")
    with gzip.GzipFile(delta_p, "wb", mtime=0) as g:
        g.write(csv_b)
    return delta_p, csv_b, grid, grid_by


def write_inventory_r1(
    inv_rows: list[dict[str, str]],
    src_a: list[dict[str, Any]],
    src_b: list[dict[str, Any]],
    four_404_info: list[dict[str, Any]],
) -> str:
    a_map = {(s["inst_id"], s["month_cst"]): s for s in src_a}
    b_map = {(s["inst_id"], s["month_cst"]): s for s in src_b}
    info_404 = {(s["inst_id"], s["month_cst"]): s for s in four_404_info}
    out_rows: list[dict[str, str]] = []
    for r in inv_rows:
        rec = dict(r)
        key = (r["inst_id"], r["month_cst"])
        if key in info_404:
            rec["class"] = "official_unavailable"
            rec["official_listed"] = "false"
            rec["http"] = rec.get("http") or "404"
            # listTime is evidence only (manifest / instruments snapshot); do not reclassify.
            rec["sub_reason"] = "404_reason_unknown"
        elif key in a_map:
            s = a_map[key]
            rec["official_listed"] = "true" if s.get("http") == 200 else rec["official_listed"]
            rec["http"] = str(s.get("http") if s.get("http") is not None else rec.get("http") or "")
            if s.get("http") == 200 and int(s.get("rows") or 0) > 0:
                rec["class"] = "covered_verified"
                rec["sub_reason"] = ""
            elif s.get("http") == 200 and int(s.get("rows") or 0) == 0:
                rec["class"] = "missing_candidate"
                rec["sub_reason"] = "zip_empty"
            elif s.get("http") == 404:
                rec["class"] = "official_unavailable"
                rec["sub_reason"] = "404_reason_unknown"
            else:
                # Not key-compared; rename confirmed_missing -> missing_candidate.
                rec["class"] = "missing_candidate"
                rec["sub_reason"] = "zip_error" if s.get("error") else f"zip_http_{s.get('http')}"
        elif key in b_map:
            s = b_map[key]
            rec["http"] = str(s.get("http") if s.get("http") is not None else rec.get("http") or "")
            rec["official_listed"] = "false"
            if not s.get("fully_covered"):
                rec["class"] = "pending_check"
                rec["sub_reason"] = s.get("limitation_code") or "rest_incomplete"
            elif int(s.get("rows") or 0) > 0:
                rec["class"] = "covered_verified_rest"
                rec["sub_reason"] = ""
            else:
                rec["class"] = "official_rest_available"
                rec["sub_reason"] = "rest_empty"
        elif rec.get("class") == "confirmed_missing":
            rec["class"] = "missing_candidate"
        # pending_check and covered_verified (the prior 85) are left unchanged;
        # pending_check is not key-compared in this batch and is not complete.
        out_rows.append(rec)

    path = os.path.join(OUT, "funding_month_inventory_v1_11_r1.csv")
    fields = list(inv_rows[0].keys()) if inv_rows else []
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    return path


def write_public_scripts() -> dict[str, dict[str, Any]]:
    """Path-sanitized copies of the generator scripts for publication."""
    replacements_b2 = {
        os.environ.get("B2_OUT", "funding_delta_v1_11_b2"):
            os.environ.get("B2_OUT_PUBLIC", "funding_delta_v1_11_b2"),
        os.environ.get(
            "B2_INV_IN",
            "funding_month_inventory_v1_11.csv",
        ): os.environ.get("B2_INV_IN_PUBLIC", "funding_month_inventory_v1_11.csv"),
        os.environ.get(
            "B2_INV_SCRIPT",
            "build_inventory_v1_11.py",
        ): os.environ.get("B2_INV_SCRIPT_PUBLIC", "build_inventory_v1_11.py"),
        os.environ.get("B2_FROZEN_DB", "funding_archive_l1_isolated.sqlite"):
            os.environ.get("B2_FROZEN_DB_PUBLIC", "funding_archive_l1_isolated.sqlite"),
        os.environ.get("B2_DELTA_ROOT", "backtest_readiness_01"):
            os.environ.get("B2_DELTA_ROOT_PUBLIC", "backtest_readiness_01"),
    }
    replacements_inv = {
        "backtest_readiness_01/funding_inventory_v1_11":
            "funding_inventory_v1_11",
        "<DATA>/pr8b/research/ex_usdc_286_manifests/ex_usdc_286_npz_manifest_v1.json":
            "ex_usdc_286_npz_manifest_v1.json",
        "<DATA>/pr8b/research/ex_usdc_286_manifests/cache_v3_manifest.json":
            "cache_v3_manifest.json",
        "<DATA>/r1-r2-opt/snap/src/cache_v3": "cache_v3",
        "funding_archive_l1_isolated.sqlite":
            "funding_archive_l1_isolated.sqlite",
        "backtest_readiness_01": "backtest_readiness_01",
    }

    def sanitize(src: str, mapping: dict[str, str], banner: str) -> str:
        text = open(src, encoding="utf-8").read()
        # Longer paths first so prefixes are not replaced twice incorrectly.
        for old in sorted(mapping, key=len, reverse=True):
            text = text.replace(old, mapping[old])
        # Belt-and-braces: replace any leftover host prefixes with a placeholder.
        leftover = [
            os.sep + "workspace" + os.sep,
            os.sep + "tmp" + os.sep,
            os.sep + "home" + os.sep,
            os.sep + "cursor" + os.sep,
        ]
        for needle in leftover:
            text = text.replace(needle, "<DATA>/")
        for needle in leftover:
            if needle in text:
                raise RuntimeError("public script still contains a host path prefix")
        return banner + text

    banner_b2 = (
        "# Publishable copy of build_delta_v1_11_b2.py.\n"
        "# Local data locations are relative/config constants — set B2_* environment\n"
        "# variables or edit the path constants before running.\n"
        "# This file contains no host absolute paths and no secrets.\n\n"
    )
    banner_inv = (
        "# Publishable copy of build_inventory_v1_11.py.\n"
        "# Local data locations are relative/config constants — edit the path\n"
        "# constants before running. This file contains no host absolute paths\n"
        "# and no secrets. The v1.11 inventory was not re-run from this copy.\n\n"
    )
    out: dict[str, dict[str, Any]] = {}
    p_b2 = os.path.join(OUT, "build_delta_v1_11_b2_public.py")
    p_inv = os.path.join(OUT, "build_inventory_v1_11_public.py")
    open(p_b2, "w", encoding="utf-8").write(
        sanitize(os.path.join(OUT, "build_delta_v1_11_b2.py"), replacements_b2, banner_b2)
    )
    open(p_inv, "w", encoding="utf-8").write(sanitize(INV_SCRIPT, replacements_inv, banner_inv))
    for name, path in (
        ("build_delta_v1_11_b2_public.py", p_b2),
        ("build_inventory_v1_11_public.py", p_inv),
    ):
        out[name] = fs_rel(path)
    return out


def json_has_abs_path(path: str) -> bool:
    txt = open(path, encoding="utf-8").read()
    return any(s in txt for s in ("<DATA>/", "<DATA>/", "<DATA>/", "<DATA>/"))


def main() -> int:
    global _EVIDENCE_PATH
    resume_utc = utc_now_iso()
    start_utc = ORIGINAL_START_UTC
    start_mono = time.monotonic()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(ZDIR, exist_ok=True)
    os.makedirs(RDIR, exist_ok=True)
    _EVIDENCE_PATH = os.path.join(OUT, EVIDENCE_NAME)
    if not os.path.isfile(_EVIDENCE_PATH) or os.path.getsize(_EVIDENCE_PATH) == 0:
        open(_EVIDENCE_PATH, "w", encoding="utf-8").close()
        log("Opened a new evidence log")
    else:
        log(f"Keeping existing evidence log ({os.path.getsize(_EVIDENCE_PATH)} bytes); will append only new requests")
    log(f"v1.11-b2 resume {resume_utc} (batch start_utc={start_utc})")

    input_sha = hash_inputs()
    inv_rows, missing_pairs, nov_symbols = load_inventory()
    missing_pairs = sorted(missing_pairs)
    nov_symbols = sorted(nov_symbols)
    log(f"Part A candidate pairs={len(missing_pairs)}; Part B symbols={len(nov_symbols)}")

    inst_path = os.path.join(OUT, INSTRUMENTS_NAME)
    if os.path.isfile(inst_path) and os.path.getsize(inst_path) > 0:
        raw = open(inst_path, "rb").read()
        body = gzip.decompress(raw)
        payload = json.loads(body.decode())
        inst_by_id = {row["instId"]: row for row in (payload.get("data") or []) if row.get("instId")}
        inst_meta = {
            "url": INSTRUMENTS_URL,
            "request_utc": None,
            "http": 200,
            "file": INSTRUMENTS_NAME,
            "raw_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "response_bytes": len(body),
            "response_sha256": sha256_bytes(body),
            "rows": len(payload.get("data") or []),
            "reused": True,
        }
        log(f"Reusing instruments snapshot rows={inst_meta['rows']} sha={inst_meta['raw_sha256']}")
    else:
        inst_meta, inst_by_id = fetch_instruments()
    four_404_info = classify_404(inst_by_id)
    # Reuse prior CDN HEADs from evidence if all 4 404 URLs are already logged.
    head_404 = head_four_404()
    still_404 = [(h["inst_id"], h["month_cst"], h["http"]) for h in head_404]
    log(f"CDN HEAD of the 4 inventory 404 pairs: {still_404}")

    insts = {i for i, _ in missing_pairs} | set(nov_symbols)
    existing = load_existing(insts)

    src_a, official_a = fetch_part_a(missing_pairs)
    log(f"Part A done: source months {len(src_a)}, official rows {len(official_a)}")

    src_b, official_b, rest_anom = fetch_part_b(nov_symbols)
    log(f"Part B done: symbols {len(src_b)}, official rows {len(official_b)}, anomalies {len(rest_anom)}")

    official = official_a + official_b
    new_rows, conflicts, intra_dup, matched, split = compare(official, existing)

    seen: dict[tuple[str, int], tuple] = {}
    for o in official:
        k = (o[0], o[2])
        if k not in seen:
            seen[k] = o

    delta_p, csv_b, grid, grid_by = write_delta(new_rows, seen)

    conf_p = os.path.join(OUT, "funding_conflicts_v1_11_b2.json")
    with open(conf_p, "w", encoding="utf-8") as f:
        json.dump(
            {"conflicts": conflicts, "intra_official_dups": intra_dup, "rest_anomalies": rest_anom},
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    src_all = src_a + src_b
    src_p = os.path.join(OUT, "funding_source_months_v1_11_b2.json")
    with open(src_p, "w", encoding="utf-8") as f:
        json.dump(src_all, f, indent=2, ensure_ascii=False)
        f.write("\n")

    inv_p = write_inventory_r1(inv_rows, src_a, src_b, four_404_info)
    inv_counts: Counter[str] = Counter()
    inv_sub: Counter[tuple[str, str]] = Counter()
    with open(inv_p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            inv_counts[r["class"]] += 1
            inv_sub[(r["class"], r.get("sub_reason") or "")] += 1

    public_files = write_public_scripts()

    end_utc = utc_now_iso()
    a_ok = sum(1 for s in src_a if s.get("http") == 200 and "error" not in s)
    a_fail = len(src_a) - a_ok
    a_empty = sum(1 for s in src_a if s.get("http") == 200 and int(s.get("rows") or 0) == 0)
    a_reused = sum(1 for s in src_a if s.get("reused_existing_zip"))
    b_ok = sum(1 for s in src_b if s.get("fully_covered"))
    b_fail = len(src_b) - b_ok
    b_empty = sum(1 for s in src_b if s.get("fully_covered") and int(s.get("rows") or 0) == 0)
    b_limitations = [
        {
            "inst_id": s["inst_id"],
            "limitation_code": s.get("limitation_code"),
            "limitation": s.get("limitation"),
            "coverage": s.get("coverage"),
        }
        for s in src_b
        if not s.get("fully_covered")
    ]
    b_fetched_with_rows = sum(1 for s in src_b if int(s.get("rows") or 0) > 0)

    files_meta = {
        "funding_delta_v1_11_b2.csv.gz": {
            **fs_rel(delta_p),
            "rows": len(new_rows),
            "csv_bytes": len(csv_b),
            "csv_sha256": sha256_bytes(csv_b),
        },
        "funding_conflicts_v1_11_b2.json": fs_rel(conf_p),
        "funding_source_months_v1_11_b2.json": fs_rel(src_p),
        "funding_month_inventory_v1_11_r1.csv": fs_rel(inv_p),
        EVIDENCE_NAME: fs_rel(_EVIDENCE_PATH),
        INSTRUMENTS_NAME: fs_rel(os.path.join(OUT, INSTRUMENTS_NAME)),
        **public_files,
    }

    manifest = {
        "research_id": RESEARCH_ID,
        "version": VERSION,
        "start_utc": start_utc,
        "resume_utc": resume_utc,
        "end_utc": end_utc,
        "elapsed_sec_this_process": round(time.monotonic() - start_mono, 2),
        "wording": {
            "confirmed_missing": (
                "In the source v1.11 inventory, confirmed_missing is only a priority "
                "candidate set (0 existing rows, or fewer than the 8H-grid minimum for "
                "the NPZ bar span). It is not a completeness claim."
            ),
            "pending_check": (
                "pending_check months were not key-compared against official files in "
                "this batch and are not described as complete."
            ),
            "conclusions": (
                "Delta and manifest counts (matched / new / conflicts / intra-official "
                "dups) come only from key-by-key comparison of official rows against "
                "frozen + v1.7/v1.9/v1.10/v1.11_b1, keyed by (inst_id, snap to nearest hour)."
            ),
            "inventory_r1": (
                "Pairs that were key-compared from official ZIPs and had official rows "
                "are covered_verified. Anything still not key-compared that had been "
                "confirmed_missing is renamed missing_candidate. The four inventory 404 "
                "pairs stay official_unavailable / 404_reason_unknown; official listTime "
                "is evidence only and was not used to reclassify. 2026-11 pairs are "
                "covered_verified_rest only when official REST history fully covered the "
                "window (reached 2026-10-31T16:00:00Z with no request failure). Any 2026-11 "
                "symbol not fully covered (403, 429 after backoff, or a retention gap) is "
                "pending_check with the concrete limitation. This batch does not describe "
                "all 286 REST symbols as delivered — only symbols actually fully fetched."
            ),
        },
        "inputs_sha256": input_sha,
        "instruments": inst_meta,
        "official_404_pairs": {
            "count": len(four_404_info),
            "exactly_these_four": sorted((a, b) for a, b, _ in still_404)
            == sorted(FOUR_404)
            and all(h["http"] == 404 for h in head_404),
            "cdn_head": head_404,
            "instruments_listTime": four_404_info,
        },
        "part_a": {
            "pairs_total": len(src_a),
            "files_ok": a_ok,
            "files_reused_from_first_pass": a_reused,
            "files_failed": a_fail,
            "files_empty": a_empty,
            "official_rows": len(official_a),
            "matched": split["matched_monthly_zip"],
            "new_rows": split["new_monthly_zip"],
            "conflicts": split["conflicts_monthly_zip"],
            "new_rows_grid": grid_by["monthly_zip"],
            "note": "Source inventory confirmed_missing was the priority candidate list; counts below are from key-by-key comparison.",
        },
        "part_b": {
            "symbols_requested": len(src_b),
            "fully_covered": b_ok,
            "not_fully_covered": b_fail,
            "symbols_with_in_range_rows": b_fetched_with_rows,
            "files_empty_but_fully_covered": b_empty,
            "official_rows_in_range": len(official_b),
            "matched": split["matched_rest_history"],
            "new_rows": split["new_rest_history"],
            "conflicts": split["conflicts_rest_history"],
            "new_rows_grid": grid_by["rest_history"],
            "range_start_utc": iso(RANGE_LO_MS),
            "range_end_utc": iso(RANGE_HI_MS),
            "window_end_unchanged": True,
            "zero_fill": False,
            "credentials_sent": False,
            "http_403_bypassed": False,
            "not_described_as_all_286_delivered": True,
            "limitations": b_limitations,
        },
        "official_rows_total": len(official),
        "official_unique_keys": len(seen),
        "already_matched_existing": matched,
        "new_rows": len(new_rows),
        "new_rows_grid": grid,
        "conflicts": len(conflicts),
        "conflict_types": {
            t: sum(1 for c in conflicts if c["type"] == t) for t in sorted({c["type"] for c in conflicts})
        },
        "conflict_sources": {
            t: sum(1 for c in conflicts if c["existing_source"] == t)
            for t in sorted({c["existing_source"] for c in conflicts})
        },
        "intra_official_dups": len(intra_dup),
        "rest_anomalies": len(rest_anom),
        "inventory_r1_class_counts": dict(inv_counts),
        "inventory_r1_class_sub_reason": {
            f"{k[0]}|{k[1]}" if k[1] else k[0]: n for k, n in sorted(inv_sub.items())
        },
        "files": files_meta,
        "rule": (
            "Not for blind INSERT OR IGNORE: rows in the delta have zero key overlap "
            "with the frozen 829,157-row DB, v1.7, v1.9, v1.10 and v1.11_b1; conflicts "
            "are listed separately for review. No zero-fill, no interpolation. "
            "pending_check months were not verified in this batch. The v1.11 inventory "
            "was not redone and the 85 already-verified official ZIPs were not refetched."
        ),
    }

    mf_p = os.path.join(OUT, "funding_delta_v1_11_b2_manifest.json")
    with open(mf_p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    manifest_for_print = dict(manifest)
    manifest_for_print["files"] = dict(files_meta)
    manifest_for_print["files"]["funding_delta_v1_11_b2_manifest.json"] = fs_rel(mf_p)

    leaked = []
    for p in (conf_p, src_p, mf_p, _EVIDENCE_PATH):
        if json_has_abs_path(p):
            leaked.append(os.path.basename(p))
            log(f"WARNING: absolute path leaked in {os.path.basename(p)}")
    if leaked:
        log(f"Path leak in: {leaked}")

    log(
        f"Wrote delta {os.path.basename(delta_p)} rows={len(new_rows)} "
        f"sha={files_meta['funding_delta_v1_11_b2.csv.gz']['sha256']}"
    )
    log(
        f"Part A ok={a_ok} reused={a_reused} fail={a_fail} official={len(official_a)} "
        f"matched={split['matched_monthly_zip']} new={split['new_monthly_zip']} "
        f"conflicts={split['conflicts_monthly_zip']}"
    )
    log(
        f"Part B fully_covered={b_ok} not_covered={b_fail} with_rows={b_fetched_with_rows} "
        f"official={len(official_b)} matched={split['matched_rest_history']} "
        f"new={split['new_rest_history']} conflicts={split['conflicts_rest_history']} "
        f"limitations={len(b_limitations)}"
    )
    log(f"Conflicts total={len(conflicts)} intra_dups={len(intra_dup)} rest_anomalies={len(rest_anom)}")
    log(f"Inventory r1 class counts: {dict(inv_counts)}")
    log(f"v1.11-b2 end {end_utc} this_process {time.monotonic()-start_mono:.1f}s")
    print("===DELTA_SUMMARY===")
    print(json.dumps(manifest_for_print, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
