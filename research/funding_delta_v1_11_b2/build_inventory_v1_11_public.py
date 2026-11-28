# Publishable copy of build_inventory_v1_11.py.
# Local data locations are relative/config constants — edit the path
# constants before running. This file contains no host absolute paths
# and no secrets. The v1.11 inventory was not re-run from this copy.

#!/usr/bin/env python3
"""BACKTEST-READINESS-01 v1.11 — official funding-month inventory.

Offline research data prep only. Does not trade, run strategies, refetch
candles, add symbols/periods, zero-fill, interpolate, modify frozen files,
download new monthly ZIPs (except HEAD when the history API is inconclusive),
or push/publish anything.

For each EX_USDC_286 symbol, derive the CST (UTC+8) calendar months in which
the NPZ actually has 30m bars inside 2023-01-01 00:00 UTC .. 2026-11-26 12:00 UTC.
Classify each (inst_id, month_cst) against already-fetched official ZIPs,
existing frozen+delta settlement rows, and the OKX monthly-history API.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Paths and window
# ---------------------------------------------------------------------------
RESEARCH_ID = "BACKTEST-READINESS-01"
VERSION = "v1.11-inventory"
DATASET = "EX_USDC_286"

OUT_DIR = "funding_inventory_v1_11"
CSV_NAME = "funding_month_inventory_v1_11.csv"
MANIFEST_NAME = "funding_month_inventory_v1_11_manifest.json"

NPZ_MANIFEST = (
    "ex_usdc_286_npz_manifest_v1.json"
)
CACHE_V3_MANIFEST = (
    "cache_v3_manifest.json"
)
NPZ_DIR = "cache_v3"
FROZEN_DB = "funding_archive_l1_isolated.sqlite"

DELTA_ROOT = "backtest_readiness_01"
DELTA_CSVS = [
    ("v1.7", os.path.join(DELTA_ROOT, "funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz")),
    ("v1.9", os.path.join(DELTA_ROOT, "funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz")),
    ("v1.10", os.path.join(DELTA_ROOT, "funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz")),
    ("v1.11_b1", os.path.join(DELTA_ROOT, "funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz")),
]
VERIFIED_MONTH_LISTS = [
    os.path.join(DELTA_ROOT, "funding_delta_v1_10/funding_source_months_v1_10.json"),
    os.path.join(DELTA_ROOT, "funding_delta_v1_11_b1/funding_source_months_v1_11_b1.json"),
]
VERIFIED_ZIP_DIRS = [
    os.path.join(DELTA_ROOT, "funding_delta_v1_10/official_monthly_zips"),
    os.path.join(DELTA_ROOT, "funding_delta_v1_11_b1/official_monthly_zips"),
]

WINDOW_START_UTC = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END_UTC = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
WIN_LO_MS = int(WINDOW_START_UTC.timestamp() * 1000)
WIN_HI_MS = int(WINDOW_END_UTC.timestamp() * 1000)
CST = timezone(timedelta(hours=8))
CST_OFFSET_MS = 8 * 3600 * 1000
EIGHT_H_MS = 8 * 3600 * 1000

# The current CST month is not closed, so official monthly ZIPs are not published.
# Run date is 2026-11-28 (CST); CST November 2026 closes at 2026-12-01 00:00 CST.
CURRENT_INCOMPLETE_MONTH_CST = "2026-11"

API_BASE = "https://www.okx.com/api/v5/public/market-data-history"
CDN_TMPL = (
    "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/"
    "{yyyymm}/{inst}-fundingrates-{yyyy}-{mm}.zip"
)
USER_AGENT = "BACKTEST-READINESS-01-inventory/1.11 (research; offline-prep)"
API_MAX_FAMILIES = 5
# The history API caps each query at 10 months, and it measures those months
# in CST (UTC+8). A UTC end of 23:59:59 falls into the next CST calendar month
# and returns code 50077. Windows below are CST-month inclusive ranges, with
# begin = CST month-start and end = 1 ms before the following CST month-start.
def _cst_api_window(start_ym: str, end_ym: str) -> tuple[datetime, datetime]:
    y1, m1 = map(int, start_ym.split("-"))
    y2, m2 = map(int, end_ym.split("-"))
    start = datetime(y1, m1, 1, 0, 0, 0, tzinfo=CST).astimezone(timezone.utc)
    if m2 == 12:
        end_excl = datetime(y2 + 1, 1, 1, 0, 0, 0, tzinfo=CST)
    else:
        end_excl = datetime(y2, m2 + 1, 1, 0, 0, 0, tzinfo=CST)
    end = (end_excl - timedelta(milliseconds=1)).astimezone(timezone.utc)
    return start, end


API_WINDOWS = [
    _cst_api_window("2023-01", "2023-10"),
    _cst_api_window("2023-11", "2024-08"),
    _cst_api_window("2024-09", "2025-06"),
    _cst_api_window("2025-07", "2026-04"),
    _cst_api_window("2026-05", "2026-11"),
]
MIN_INTERVAL_S = 0.21  # ~5 req/s
MAX_RETRIES = 6

CSV_FIELDS = [
    "inst_id",
    "month_cst",
    "npz_bar_first_utc",
    "npz_bar_last_utc",
    "existing_rows",
    "existing_sources",
    "official_listed",
    "http",
    "class",
    "sub_reason",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ms_to_utc_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def ts_to_month_cst(ts_ms: int) -> str:
    return datetime.fromtimestamp(
        ts_ms / 1000.0, tz=timezone.utc
    ).astimezone(CST).strftime("%Y-%m")


def month_cst_bounds_utc_ms(month_cst: str) -> tuple[int, int]:
    """Return [start, end) UTC ms for a CST calendar month."""
    y, m = map(int, month_cst.split("-"))
    start = datetime(y, m, 1, 0, 0, 0, tzinfo=CST)
    if m == 12:
        end = datetime(y + 1, 1, 1, 0, 0, 0, tzinfo=CST)
    else:
        end = datetime(y, m + 1, 1, 0, 0, 0, tzinfo=CST)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def eight_h_grid_min(first_ms: int, last_ms: int, month_cst: str) -> int:
    """Count UTC 8H grid points (00/08/16Z) in [first, last] ∩ CST month."""
    m_lo, m_hi = month_cst_bounds_utc_ms(month_cst)
    lo = max(first_ms, m_lo)
    hi = min(last_ms, m_hi - 1)
    if hi < lo:
        return 0
    g = ((lo + EIGHT_H_MS - 1) // EIGHT_H_MS) * EIGHT_H_MS
    if g > hi:
        return 0
    return int((hi - g) // EIGHT_H_MS) + 1


def inst_family(inst_id: str) -> str:
    if inst_id.endswith("-SWAP"):
        return inst_id[: -len("-SWAP")]
    return inst_id


def cdn_url(inst_id: str, month_cst: str) -> str:
    yyyy, mm = month_cst.split("-")
    return CDN_TMPL.format(yyyymm=yyyy + mm, inst=inst_id, yyyy=yyyy, mm=mm)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    print(f"[{utc_now_iso()}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
_last_req_t = 0.0


def _rate_limit() -> None:
    global _last_req_t
    now = time.monotonic()
    wait = MIN_INTERVAL_S - (now - _last_req_t)
    if wait > 0:
        time.sleep(wait)
    _last_req_t = time.monotonic()


def _open(req: urllib.request.Request, timeout: int = 30):
    _rate_limit()
    return urllib.request.urlopen(req, timeout=timeout)


def http_json(url: str) -> tuple[int, Any]:
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with _open(req) as resp:
                status = resp.status
                body = json.loads(resp.read().decode())
            if isinstance(body, dict):
                code = str(body.get("code", ""))
                # OKX rate-limit / busy codes
                if code in {"50011", "50001", "50004", "50013"}:
                    raise RuntimeError(f"okx transient code={code} msg={body.get('msg')}")
            return status, body
        except urllib.error.HTTPError as e:
            payload = e.read().decode(errors="replace")
            if e.code in {429, 500, 502, 503, 504} and attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"HTTP {e.code} on API, retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                last_err = e
                continue
            try:
                return e.code, json.loads(payload)
            except Exception:
                return e.code, {"code": str(e.code), "msg": payload[:300], "data": []}
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"API error {type(e).__name__}: {e}; retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                continue
            raise
    raise RuntimeError(f"API failed after retries: {last_err}")


def http_head(url: str) -> int:
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": USER_AGENT}
        )
        try:
            with _open(req) as resp:
                return int(resp.status)
        except urllib.error.HTTPError as e:
            # Drain and close
            try:
                e.read()
            except Exception:
                pass
            if e.code in {429, 500, 502, 503, 504} and attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"HEAD HTTP {e.code}, retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                last_err = e
                continue
            return int(e.code)
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"HEAD error {type(e).__name__}: {e}; retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                continue
            raise
    raise RuntimeError(f"HEAD failed after retries: {last_err}")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def load_universe() -> list[str]:
    with open(NPZ_MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    syms = sorted(x["filename"].replace(".npz", "") for x in man["files"])
    if len(syms) != 286:
        raise SystemExit(f"expected 286 symbols, got {len(syms)}")
    missing = [s for s in syms if not os.path.isfile(os.path.join(NPZ_DIR, s + ".npz"))]
    if missing:
        raise SystemExit(f"missing {len(missing)} NPZ files, e.g. {missing[:5]}")
    return syms


def load_cache_meta() -> dict[str, dict]:
    if not os.path.isfile(CACHE_V3_MANIFEST):
        return {}
    with open(CACHE_V3_MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    return man.get("symbols", {}) or {}


def load_verified_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for path in VERIFIED_MONTH_LISTS:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        for row in rows:
            pairs.add((row["inst_id"], row["month_cst"]))
    # Cross-check ZIP filenames on disk (do not refetch).
    zip_pairs: set[tuple[str, str]] = set()
    for d in VERIFIED_ZIP_DIRS:
        for fn in os.listdir(d):
            if not fn.endswith(".zip"):
                continue
            # INST-USDT-SWAP-fundingrates-YYYY-MM.zip
            stem = fn[: -len(".zip")]
            marker = "-fundingrates-"
            i = stem.rfind(marker)
            if i < 0:
                continue
            inst = stem[:i]
            month = stem[i + len(marker) :]  # YYYY-MM
            zip_pairs.add((inst, month))
    if zip_pairs != pairs:
        only_json = pairs - zip_pairs
        only_zip = zip_pairs - pairs
        raise SystemExit(
            f"verified ZIP/json mismatch: only_json={len(only_json)} only_zip={len(only_zip)} "
            f"examples json={list(only_json)[:3]} zip={list(only_zip)[:3]}"
        )
    if len(pairs) != 85:
        raise SystemExit(f"expected 85 verified official months, got {len(pairs)}")
    return pairs


def derive_npz_pairs(symbols: list[str]) -> dict[tuple[str, str], dict[str, int]]:
    """Return {(inst, month_cst): {first_ms, last_ms, n_bars}} from ts30 in window."""
    out: dict[tuple[str, str], dict[str, int]] = {}
    t0 = time.monotonic()
    for i, inst in enumerate(symbols, 1):
        path = os.path.join(NPZ_DIR, inst + ".npz")
        with np.load(path) as z:
            ts = np.asarray(z["ts30"], dtype=np.int64)
        m = ts[(ts >= WIN_LO_MS) & (ts <= WIN_HI_MS)]
        if m.size == 0:
            continue
        # Adding 8h then taking UTC year-month == CST year-month.
        cst_sec = (m + CST_OFFSET_MS) // 1000
        months = cst_sec.astype("datetime64[s]").astype("datetime64[M]")
        uniq = np.unique(months)
        for month in uniq:
            mask = months == month
            sl = m[mask]
            month_cst = str(month)  # 'YYYY-MM'
            out[(inst, month_cst)] = {
                "first_ms": int(sl[0]),
                "last_ms": int(sl[-1]),
                "n_bars": int(sl.size),
            }
        if i % 50 == 0 or i == len(symbols):
            log(f"NPZ scan {i}/{len(symbols)} symbols, pairs so far {len(out)}, {time.monotonic()-t0:.1f}s")
    return out


def load_existing_rows(
    symbols: set[str],
) -> tuple[dict[tuple[str, str], set[int]], dict[tuple[str, str], set[str]]]:
    """Unique ts_snapped per (inst, month_cst) and the sources that contributed."""
    keys: dict[tuple[str, str], set[int]] = defaultdict(set)
    sources: dict[tuple[str, str], set[str]] = defaultdict(set)

    log("Loading frozen funding_archive (read-only)…")
    con = sqlite3.connect(f"file:{FROZEN_DB}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        cur = con.execute(
            "SELECT inst_id, ts_snapped FROM funding_archive"
        )
        n = 0
        while True:
            batch = cur.fetchmany(50_000)
            if not batch:
                break
            for inst, ts in batch:
                if inst not in symbols:
                    continue
                month = ts_to_month_cst(int(ts))
                k = (inst, month)
                keys[k].add(int(ts))
                sources[k].add("frozen")
                n += 1
        log(f"Frozen rows kept for universe: {n}")
    finally:
        con.close()

    for label, path in DELTA_CSVS:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if "ts_snapped_ms" not in (reader.fieldnames or []):
                raise SystemExit(f"{path} missing ts_snapped_ms, fields={reader.fieldnames}")
            n = 0
            for row in reader:
                inst = row["inst_id"]
                if inst not in symbols:
                    continue
                ts = int(row["ts_snapped_ms"])
                month = ts_to_month_cst(ts)
                k = (inst, month)
                keys[k].add(ts)
                sources[k].add(label)
                n += 1
            log(f"Delta {label}: {n} universe rows from {os.path.basename(path)}")
    return keys, sources


def fetch_official_listings(symbols: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    """Query market-data-history for every symbol across the whole window.

    Returns {(inst, month_cst): {url, date_ts, http}}.
    """
    listed: dict[tuple[str, str], dict[str, Any]] = {}
    batches = [
        symbols[i : i + API_MAX_FAMILIES]
        for i in range(0, len(symbols), API_MAX_FAMILIES)
    ]
    total = len(batches) * len(API_WINDOWS)
    done = 0
    t0 = time.monotonic()
    for batch in batches:
        fams = ",".join(inst_family(s) for s in batch)
        inst_by_fam = {inst_family(s): s for s in batch}
        for lo, hi in API_WINDOWS:
            begin = int(lo.timestamp() * 1000)
            end = int(hi.timestamp() * 1000)
            url = (
                f"{API_BASE}?module=3&instType=SWAP"
                f"&instFamilyList={fams}&dateAggrType=monthly"
                f"&begin={begin}&end={end}"
            )
            status, body = http_json(url)
            done += 1
            if not isinstance(body, dict) or str(body.get("code")) != "0":
                log(
                    f"API non-OK ({done}/{total}) http={status} "
                    f"code={body.get('code') if isinstance(body, dict) else type(body)} "
                    f"msg={body.get('msg') if isinstance(body, dict) else body}"
                )
                # Leave months unlisted; HEAD will follow.
                continue
            data = body.get("data") or []
            for block in data:
                for det in block.get("details") or []:
                    fam = det.get("instFamily") or ""
                    inst = inst_by_fam.get(fam)
                    if not inst:
                        # Sometimes API may echo a family we asked for with a
                        # slightly different key; try filename instead.
                        inst = None
                    for g in det.get("groupDetails") or []:
                        fn = g.get("filename") or ""
                        marker = "-fundingrates-"
                        j = fn.find(marker)
                        if j < 0:
                            continue
                        file_inst = fn[:j]
                        month = fn[j + len(marker) :].replace(".zip", "")
                        use_inst = inst or file_inst
                        listed[(use_inst, month)] = {
                            "url": (g.get("url") or "").split("?", 1)[0],
                            "date_ts": int(g["dateTs"]) if g.get("dateTs") else None,
                            "http": 200,
                            "via": "api",
                        }
            if done % 20 == 0 or done == total:
                log(
                    f"API listings {done}/{total}, listed months {len(listed)}, "
                    f"{time.monotonic()-t0:.1f}s"
                )
    return listed


def head_unlisted(
    pairs: list[tuple[str, str]],
    listed: dict[tuple[str, str], dict[str, Any]],
    verified: set[tuple[str, str]],
) -> dict[tuple[str, str], int]:
    """HEAD CDN for pairs that the API did not list (and that we have not already fetched)."""
    http_map: dict[tuple[str, str], int] = {}
    todo = [k for k in pairs if k not in listed and k not in verified]
    log(f"CDN HEAD for {len(todo)} unlisted pairs…")
    t0 = time.monotonic()
    for i, (inst, month) in enumerate(todo, 1):
        status = http_head(cdn_url(inst, month))
        http_map[(inst, month)] = status
        if status == 200:
            listed[(inst, month)] = {
                "url": cdn_url(inst, month),
                "date_ts": None,
                "http": 200,
                "via": "head",
            }
        if i % 50 == 0 or i == len(todo):
            n200 = sum(1 for v in http_map.values() if v == 200)
            log(
                f"HEAD {i}/{len(todo)}, 200={n200} other={i-n200}, "
                f"{time.monotonic()-t0:.1f}s"
            )
    return http_map


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def official_end_months(
    symbols: list[str], listed: dict[tuple[str, str], dict[str, Any]]
) -> dict[str, str | None]:
    last: dict[str, str | None] = {s: None for s in symbols}
    for inst, month in listed:
        prev = last.get(inst)
        if prev is None or month > prev:
            last[inst] = month
    return last


def official_start_months(
    symbols: list[str], listed: dict[tuple[str, str], dict[str, Any]]
) -> dict[str, str | None]:
    first: dict[str, str | None] = {s: None for s in symbols}
    for inst, month in listed:
        prev = first.get(inst)
        if prev is None or month < prev:
            first[inst] = month
    return first


def classify_row(
    inst: str,
    month: str,
    existing_n: int,
    eight_min: int,
    verified: set[tuple[str, str]],
    listed: dict[tuple[str, str], dict[str, Any]],
    head_http: dict[tuple[str, str], int],
    first_official: dict[str, str | None],
    last_official: dict[str, str | None],
    cache_meta: dict[str, dict],
) -> tuple[str, str, str, str]:
    """Return (official_listed, http, class, sub_reason)."""
    k = (inst, month)
    is_listed = k in listed
    if k in verified:
        http = "200"
        return ("true", http, "covered_verified", "")

    if is_listed:
        http = str(listed[k].get("http") or 200)
        # Official file exists. Completeness vs 8H-grid minimum of bar coverage.
        if existing_n == 0:
            return ("true", http, "confirmed_missing", "zero_rows")
        if existing_n < eight_min:
            return ("true", http, "confirmed_missing", "below_8h_grid_min")
        return ("true", http, "pending_check", "")

    # Not listed by API (and not in the 85 already-fetched ZIPs).
    http_i = head_http.get(k)
    http = "" if http_i is None else str(http_i)

    # If HEAD found the file after all, treat as official exists.
    if http_i == 200:
        if existing_n == 0:
            return ("true", http, "confirmed_missing", "zero_rows")
        if existing_n < eight_min:
            return ("true", http, "confirmed_missing", "below_8h_grid_min")
        return ("true", http, "pending_check", "")

    # Official unavailable — pick a sub-reason.
    meta = cache_meta.get(inst) or {}
    live = meta.get("live", True)
    list_time = meta.get("listTime")
    list_ms = int(list_time) if list_time not in (None, "") else None
    m_lo, m_hi = month_cst_bounds_utc_ms(month)

    if month >= CURRENT_INCOMPLETE_MONTH_CST:
        reason = "boundary-insufficient"
    elif not live and (last_official.get(inst) is None or month > (last_official.get(inst) or "")):
        reason = "listing-suspension"
    elif (
        last_official.get(inst)
        and month > last_official[inst]  # type: ignore[operator]
        and month < CURRENT_INCOMPLETE_MONTH_CST
    ):
        reason = "listing-suspension"
    elif (
        first_official.get(inst)
        and last_official.get(inst)
        and first_official[inst] < month < last_official[inst]  # type: ignore[operator]
    ):
        # Hole in the official month series while later months resume.
        reason = "listing-suspension"
    elif list_ms is not None and m_hi <= list_ms:
        # Month ends at or before listing time — official history would not exist.
        reason = "listing-suspension"
    elif http_i == 404:
        reason = "404"
    else:
        reason = "not_listed"
    return ("false", http, "official_unavailable", reason)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    start_utc = utc_now_iso()
    start_mono = time.monotonic()
    os.makedirs(OUT_DIR, exist_ok=True)
    log(f"Inventory start {start_utc}")

    symbols = load_universe()
    cache_meta = load_cache_meta()
    verified = load_verified_pairs()
    log(f"Universe {len(symbols)} symbols; already-fetched official months {len(verified)}")

    pairs = derive_npz_pairs(symbols)
    log(f"NPZ-derived (inst, month_cst) pairs: {len(pairs)}")

    existing_keys, existing_sources = load_existing_rows(set(symbols))

    listed = fetch_official_listings(symbols)
    log(f"Official months listed via API: {len(listed)}")

    # Deterministic order for HEAD and CSV.
    pair_list = sorted(pairs.keys(), key=lambda x: (x[0], x[1]))
    head_http = head_unlisted(pair_list, listed, verified)
    first_official = official_start_months(symbols, listed)
    last_official = official_end_months(symbols, listed)

    rows_out: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    unavail_counts: Counter[str] = Counter()
    missing_by_sym: Counter[str] = Counter()
    verified_without_npz = sorted(verified - set(pairs))

    for inst, month in pair_list:
        info = pairs[(inst, month)]
        k = (inst, month)
        ts_set = existing_keys.get(k, set())
        srcs = existing_sources.get(k, set())
        existing_n = len(ts_set)
        eight_min = eight_h_grid_min(info["first_ms"], info["last_ms"], month)
        official_listed, http, klass, sub = classify_row(
            inst,
            month,
            existing_n,
            eight_min,
            verified,
            listed,
            head_http,
            first_official,
            last_official,
            cache_meta,
        )
        class_counts[klass] += 1
        if klass == "official_unavailable":
            unavail_counts[sub] += 1
        if klass == "confirmed_missing":
            missing_by_sym[inst] += 1
        rows_out.append(
            {
                "inst_id": inst,
                "month_cst": month,
                "npz_bar_first_utc": ms_to_utc_iso(info["first_ms"]),
                "npz_bar_last_utc": ms_to_utc_iso(info["last_ms"]),
                "existing_rows": existing_n,
                "existing_sources": ",".join(sorted(srcs)),
                "official_listed": official_listed,
                "http": http,
                "class": klass,
                "sub_reason": sub,
            }
        )

    csv_path = os.path.join(OUT_DIR, CSV_NAME)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows_out)

    csv_size = os.path.getsize(csv_path)
    csv_sha = sha256_file(csv_path)

    # Download-time estimate for pending_check + confirmed_missing official ZIPs.
    to_fetch = class_counts["pending_check"] + class_counts["confirmed_missing"]
    # Existing 85 ZIPs: median ~1.3 KiB, fetched previously at a burst; we will
    # stay at ~5 req/s plus unzip/parse (~0.05–0.15s extra per file).
    est_sec_low = to_fetch * 0.21 + to_fetch * 0.05
    est_sec_high = to_fetch * 0.21 + to_fetch * 0.15 + 30  # + setup margin
    # Typical bytes from the already-fetched 85 ZIPs (mean ~1347 B).
    est_bytes = int(to_fetch * 1347)

    end_utc = utc_now_iso()
    elapsed = time.monotonic() - start_mono

    manifest = {
        "research_id": RESEARCH_ID,
        "version": VERSION,
        "dataset": DATASET,
        "window_start_utc": WINDOW_START_UTC.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_end_utc": WINDOW_END_UTC.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "elapsed_sec": round(elapsed, 2),
        "universe_symbols": len(symbols),
        "bar_series": "ts30",
        "month_timezone": "CST (UTC+8)",
        "total_pairs": len(rows_out),
        "class_counts": {
            "covered_verified": class_counts["covered_verified"],
            "pending_check": class_counts["pending_check"],
            "confirmed_missing": class_counts["confirmed_missing"],
            "official_unavailable": class_counts["official_unavailable"],
        },
        "official_unavailable_breakdown": dict(unavail_counts),
        "already_fetched_official_zips": len(verified),
        "verified_pairs_without_npz_bars_in_window": [
            {"inst_id": a, "month_cst": b} for a, b in verified_without_npz
        ],
        "top_symbols_confirmed_missing": [
            {"inst_id": s, "confirmed_missing_months": n}
            for s, n in missing_by_sym.most_common(20)
        ],
        "classification_rules": {
            "covered_verified": "Pair is one of the 85 already-fetched official monthly ZIPs (v1.10 80 + v1.11-b1 5). Those ZIPs were not refetched.",
            "pending_check": "Official monthly file exists (API listed or CDN HEAD 200); frozen+deltas already have at least the 8H-grid minimum row count for the NPZ bar span in that CST month, but the month has not been verified against the official ZIP.",
            "confirmed_missing": "Official monthly file exists, and frozen+deltas have 0 rows for that CST month, or fewer rows than the UTC 8H-grid (00/08/16Z) point count inside [npz_bar_first, npz_bar_last] ∩ the CST month.",
            "official_unavailable": "Official file not listed and not retrievable. sub_reason is one of: not_listed, 404, listing-suspension, boundary-insufficient.",
            "boundary-insufficient": "CST month is still open (2026-11 closes 2026-12-01 00:00 CST), so the official monthly ZIP is not published yet.",
            "no_zero_fill_no_interpolation": True,
            "frozen_files_unmodified": True,
        },
        "download_estimate_pending_plus_missing": {
            "file_count": to_fetch,
            "est_seconds_at_5rps": {
                "low": round(est_sec_low, 1),
                "high": round(est_sec_high, 1),
            },
            "est_minutes": {
                "low": round(est_sec_low / 60.0, 1),
                "high": round(est_sec_high / 60.0, 1),
            },
            "est_bytes_from_v1_10_v1_11_b1_mean": est_bytes,
            "note": "Estimate only; ZIPs were not downloaded in this inventory run. Mean size taken from the existing 85 official ZIPs (~1347 B).",
        },
        "inputs": {
            "npz_manifest": NPZ_MANIFEST,
            "npz_dir": NPZ_DIR,
            "frozen_db": FROZEN_DB,
            "frozen_access": "sqlite mode=ro, unmodified",
            "deltas": [p for _, p in DELTA_CSVS],
            "verified_month_lists": VERIFIED_MONTH_LISTS,
        },
        "files": {
            CSV_NAME: {"size_bytes": csv_size, "sha256": csv_sha},
        },
        "rule": "Offline inventory only. No zero-fill, no interpolation, no symbol/period expansion, no candle refetch, no strategy run, no ZIP body download, no push.",
    }

    man_path = os.path.join(OUT_DIR, MANIFEST_NAME)
    # Write manifest first without its own hash, then add script + manifest hashes.
    script_src = os.path.abspath(__file__) if "__file__" in dir() else os.path.join(OUT_DIR, "build_inventory_v1_11.py")
    script_name = "build_inventory_v1_11.py"
    script_path = os.path.join(OUT_DIR, script_name)
    if os.path.isfile(script_path):
        manifest["files"][script_name] = {
            "size_bytes": os.path.getsize(script_path),
            "sha256": sha256_file(script_path),
        }

    tmp_man = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    with open(man_path, "w", encoding="utf-8") as f:
        f.write(tmp_man)
    manifest["files"][MANIFEST_NAME] = {
        "size_bytes": os.path.getsize(man_path),
        "sha256": sha256_file(man_path),
    }
    # The self-hash in the manifest file cannot include its own digest stably;
    # record csv + script hashes in the file, and leave manifest sha as a
    # post-write value printed below and stored under files after a second field
    # `sha256_after_write` would shift the bytes. Keep manifest["files"] without
    # its own sha inside the written JSON; report it at runtime.
    manifest_for_write = dict(manifest)
    manifest_for_write["files"] = {
        CSV_NAME: manifest["files"][CSV_NAME],
        **(
            {script_name: manifest["files"][script_name]}
            if script_name in manifest["files"]
            else {}
        ),
    }
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest_for_write, f, indent=2, ensure_ascii=False)
        f.write("\n")
    man_size = os.path.getsize(man_path)
    man_sha = sha256_file(man_path)

    log(f"Wrote {csv_path} ({csv_size} B, sha256={csv_sha})")
    log(f"Wrote {man_path} ({man_size} B, sha256={man_sha})")
    log(f"Total pairs {len(rows_out)} class_counts={dict(class_counts)}")
    log(f"official_unavailable breakdown={dict(unavail_counts)}")
    log(f"top confirmed_missing symbols={missing_by_sym.most_common(10)}")
    log(
        f"Download estimate for {to_fetch} pending+missing ZIPs: "
        f"{est_sec_low/60:.1f}–{est_sec_high/60:.1f} min at ~5 req/s"
    )
    if verified_without_npz:
        log(f"Note: {len(verified_without_npz)} verified official months have no NPZ bars in window")
    log(f"Inventory end {end_utc} elapsed {elapsed:.1f}s")

    # Sidecar print block for the parent report (stdout).
    summary = {
        "start_utc": start_utc,
        "end_utc": end_utc,
        "elapsed_sec": round(elapsed, 2),
        "total_pairs": len(rows_out),
        "class_counts": dict(class_counts),
        "official_unavailable_breakdown": dict(unavail_counts),
        "top_symbols_confirmed_missing": missing_by_sym.most_common(20),
        "csv_size": csv_size,
        "csv_sha256": csv_sha,
        "manifest_size": man_size,
        "manifest_sha256": man_sha,
        "script_size": os.path.getsize(script_path) if os.path.isfile(script_path) else None,
        "script_sha256": sha256_file(script_path) if os.path.isfile(script_path) else None,
        "download_estimate_files": to_fetch,
        "download_estimate_minutes": {
            "low": round(est_sec_low / 60.0, 1),
            "high": round(est_sec_high / 60.0, 1),
        },
        "verified_without_npz": verified_without_npz,
    }
    print("===INVENTORY_SUMMARY===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
