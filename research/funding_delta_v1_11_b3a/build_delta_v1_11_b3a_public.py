#!/usr/bin/env python3
# Publishable generator for BACKTEST-READINESS-01 v1.11-b3a (pending_check slice 1 of 3).
# Local data locations are relative/config constants — set B3A_* environment
# variables or edit the path constants before running.
# This file contains no host absolute paths and no secrets.

"""BACKTEST-READINESS-01 v1.11-b3a — official funding delta, pending_check slice 1/3.

Offline research data prep only. Does not trade, run strategies, refetch
candles, expand the universe or window, zero-fill, interpolate, modify the
frozen DB, blindly INSERT, rebuild the v1.11-b2 r1 198,354-row delta, or
refetch already-verified official monthly ZIPs (1,364 covered_verified).

Universe: inventory r2 class=pending_check excluding RVN-USDT-SWAP 2026-11
(5,882 months), sorted by (inst_id, month_cst), split into 3 deterministic
slices of 1,961 / 1,961 / 1,960. This run processes slice 1 only.

Official rates must be finite numeric (float + math.isfinite, case-insensitive).
Empty/None/null -> official_rate_null; NaN/Inf/-Inf -> official_rate_nonfinite.
Rejected rows are listed with source ZIP name+SHA. No zero-fill, no interpolation.
Conflicts are listed and never overwrite existing keys.

Inventory complete=true means the month passed per this batch's source and
comparison scope only; it is not a full-period or cross-frequency verification.
complete=false means this batch's official ZIP contained at least one flagged
non-numeric or non-finite rate (known incomplete). blank=unknown.
Self-run scans in this batch are team execution evidence, not ChatGPT runtime
certification.
"""

from __future__ import annotations

import bisect
import csv
import gzip
import hashlib
import io
import json
import math
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

OUT = os.environ.get("B3A_OUT", "funding_delta_v1_11_b3a")
INV_IN = os.environ.get("B3A_INV_IN", "funding_month_inventory_v1_11_r2.csv")
FROZEN_DB = os.environ.get("B3A_FROZEN_DB", "funding_archive_l1_isolated.sqlite")
DELTA_ROOT = os.environ.get("B3A_DELTA_ROOT", ".")
ORIGINAL_START_UTC = os.environ.get("B3A_START_UTC", "")

ZDIR = os.path.join(OUT, "official_monthly_zips")
EVIDENCE_NAME = "fetch_evidence_v1_11_b3a.jsonl"

DELTA_CSVS = [
    ("v1_7", os.path.join(DELTA_ROOT, "funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz")),
    ("v1_9", os.path.join(DELTA_ROOT, "funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz")),
    ("v1_10", os.path.join(DELTA_ROOT, "funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz")),
    ("v1_11_b1", os.path.join(DELTA_ROOT, "funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz")),
    ("v1_11_b2_r1", os.path.join(DELTA_ROOT, "funding_delta_v1_11_b2_r1/funding_delta_v1_11_b2_r1.csv.gz")),
]
INPUT_LABELS = [
    ("funding_archive_l1_isolated.sqlite", FROZEN_DB),
    ("funding_delta_missing16_v1_7.csv.gz", DELTA_CSVS[0][1]),
    ("funding_delta_missing174_v1_9.csv.gz", DELTA_CSVS[1][1]),
    ("funding_delta_full75plus_v1_10.csv.gz", DELTA_CSVS[2][1]),
    ("funding_delta_5sym_v1_11_b1.csv.gz", DELTA_CSVS[3][1]),
    ("funding_delta_v1_11_b2_r1.csv.gz", DELTA_CSVS[4][1]),
    ("funding_month_inventory_v1_11_r2.csv", INV_IN),
]

RESEARCH_ID = "BACKTEST-READINESS-01"
VERSION = "v1.11-batch3a"
USER_AGENT = "BACKTEST-READINESS-01-v1.11-b3a (research; offline-prep)"
MIN_INTERVAL_S = 0.21
MAX_RETRIES = 6
THIS_SLICE = 1
N_SLICES = 3
RVN_EXCL = ("RVN-USDT-SWAP", "2026-11")

CDN_TMPL = (
    "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/"
    "{yyyymm}/{inst}-fundingrates-{yyyy}-{mm}.zip"
)
SOURCE_YM_ZIP = "v1_11_b3a_okx_cdn_swaprates_monthly_zip"
FLAGGED_CSV_NAME = "funding_null_rate_rows_v1_11_b3a.csv"
FLAGGED_ROWS: list[dict[str, Any]] = []

HOUR_MS = 3600 * 1000
EIGHT_H_MS = 8 * HOUR_MS
CST = timezone(timedelta(hours=8))

CSV_FIELDS = [
    "inst_id", "funding_time_ms", "funding_time_utc", "ts_snapped_ms", "ts_snapped_utc",
    "snap_offset_ms", "funding_rate", "is_8h_grid", "prev_gap_h", "next_gap_h",
    "source_month_cst", "fetched_utc", "source_ym", "source_kind", "rate_field",
]
FLAG_FIELDS = [
    "inst_id", "funding_time_ms", "funding_time_utc", "ts_snapped_ms", "ts_snapped_utc",
    "snap_offset_ms", "funding_rate_raw", "reject_type", "rate_field", "source_kind",
    "source_month_cst", "source_file", "zip_sha256", "fetched_utc", "flag",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso(ms: int, frac: bool = False) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    if frac:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond/1000):03d}Z"
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def file_mtime_utc(path: str) -> str:
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snap(ms: int) -> int:
    return int(round(ms / float(HOUR_MS))) * HOUR_MS


def rate_status(value) -> str:
    """Classify an official rate. Only finite numeric values are accepted."""
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


def is_numeric_rate(value) -> bool:
    return rate_status(value) == "numeric"


_NULL_REJECT = {
    "python_none", "empty", "literal_none", "literal_null",
    "literal_na", "literal_n_a", "non_numeric",
}
_NONFINITE_REJECT = {"nan", "inf", "neg_inf"}


def reject_flag(status: str) -> str:
    if status in _NONFINITE_REJECT:
        return "official_rate_nonfinite"
    if status in _NULL_REJECT or status != "numeric":
        return "official_rate_null"
    raise ValueError(f"rate_status {status!r} is accepted, not flagged")


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
    """GET with ~5 req/s and backoff on 429/5xx. Never retries 403, never sends credentials."""
    last_err: Exception | str | None = None
    request_utc = utc_now_iso()
    for attempt in range(1, MAX_RETRIES + 1):
        _rate_limit()
        request_utc = utc_now_iso()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = int(resp.status)
                body = resp.read()
                if log_evidence:
                    ev = {
                        "url": url,
                        "request_utc": request_utc,
                        "http": status,
                        "response_bytes": len(body),
                        "response_sha256": sha256_bytes(body),
                        "kind": kind,
                        "attempt": attempt,
                    }
                    if kind == "monthly_zip":
                        ev["evidence_form"] = "raw_zip"
                        ev["raw_bytes_saved"] = status == 200
                    evidence_write(ev)
                return status, body, request_utc
        except urllib.error.HTTPError as e:
            body = e.read()
            if log_evidence:
                ev = {
                    "url": url,
                    "request_utc": request_utc,
                    "http": int(e.code),
                    "response_bytes": len(body) if body else 0,
                    "response_sha256": sha256_bytes(body) if body else None,
                    "kind": kind,
                    "attempt": attempt,
                    "raw_bytes_saved": False,
                }
                if kind == "monthly_zip":
                    ev["evidence_form"] = "raw_zip"
                evidence_write(ev)
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
                        "raw_bytes_saved": False,
                    }
                )
            if attempt < MAX_RETRIES:
                backoff = min(30.0, (2 ** attempt) * 0.5)
                log(f"{type(e).__name__}: {e}; retry {attempt}/{MAX_RETRIES} in {backoff:.1f}s")
                time.sleep(backoff)
                continue
            return f"{type(e).__name__}:{e}", None, request_utc
    return f"failed:{last_err}", None, request_utc


def hash_inputs() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, path in INPUT_LABELS:
        if not os.path.isfile(path):
            out[label] = {"error": "missing"}
            continue
        out[label] = {"bytes": os.path.getsize(path), "sha256": sha256_file(path)}
        log(f"Input SHA {label} {out[label]['bytes']} {out[label]['sha256']}")
    return out


def define_slices(inv_rows: list[dict[str, str]]) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    pending = [
        r for r in inv_rows
        if r["class"] == "pending_check" and (r["inst_id"], r["month_cst"]) != RVN_EXCL
    ]
    pending.sort(key=lambda r: (r["inst_id"], r["month_cst"]))
    n = len(pending)
    if n != 5882:
        log(f"WARNING: expected 5882 pending_check excluding RVN 2026-11, got {n}")
    base, rem = divmod(n, N_SLICES)
    sizes = [base + 1] * rem + [base] * (N_SLICES - rem)
    cuts = [0]
    for s in sizes:
        cuts.append(cuts[-1] + s)
    slices = []
    for i, (a, b) in enumerate(zip(cuts, cuts[1:]), 1):
        sl = pending[a:b]
        slices.append(
            {
                "slice": i,
                "index_range": [a, b],
                "count": len(sl),
                "first": {"inst_id": sl[0]["inst_id"], "month_cst": sl[0]["month_cst"]},
                "last": {"inst_id": sl[-1]["inst_id"], "month_cst": sl[-1]["month_cst"]},
            }
        )
    defn = {
        "universe": "inventory r2 class=pending_check excluding RVN-USDT-SWAP 2026-11",
        "universe_count": n,
        "sort": ["inst_id", "month_cst"],
        "n_slices": N_SLICES,
        "sizes": sizes,
        "method": "base, rem = divmod(universe_count, 3); the first rem slices get base+1, the rest get base",
        "slices": slices,
        "this_batch": THIS_SLICE,
        "this_batch_index_range": slices[0]["index_range"],
        "this_batch_count": slices[0]["count"],
        "this_batch_first": slices[0]["first"],
        "this_batch_last": slices[0]["last"],
    }
    pairs = [(r["inst_id"], r["month_cst"]) for r in pending[cuts[0]:cuts[1]]]
    return defn, pairs


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


def fetch_slice(
    pairs: list[tuple[str, str]],
    verified: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[tuple]]:
    os.makedirs(ZDIR, exist_ok=True)
    src_months: list[dict[str, Any]] = []
    official: list[tuple] = []
    t0 = time.monotonic()
    ok = fail = reused_n = skipped = 0
    http_counts: Counter[Any] = Counter()
    for i, (inst, ym) in enumerate(pairs, 1):
        yyyy, mm = ym.split("-")
        url = CDN_TMPL.format(yyyymm=yyyy + mm, inst=inst, yyyy=yyyy, mm=mm)
        fn = f"{inst}-fundingrates-{ym}.zip"
        rel = f"official_monthly_zips/{fn}"
        path = os.path.join(ZDIR, fn)
        if (inst, ym) in verified:
            skipped += 1
            ent = {
                "inst_id": inst,
                "month_cst": ym,
                "source_kind": "monthly_zip",
                "url": url,
                "http": None,
                "skipped_already_verified": True,
                "file": rel,
                "note": "Already covered_verified in a prior batch; not refetched and not re-compared in b3a.",
            }
            src_months.append(ent)
            evidence_write(
                {
                    "url": url,
                    "request_utc": utc_now_iso(),
                    "http": None,
                    "kind": "monthly_zip",
                    "skipped_already_verified": True,
                    "file": rel,
                    "raw_bytes_saved": False,
                }
            )
            log(f"SKIP already verified {inst} {ym}")
            continue
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
                        "evidence_form": "raw_zip",
                        "raw_bytes_saved": True,
                        "reused": True,
                        "file": rel,
                        "note": "Body kept from an earlier pass of this batch; not re-downloaded.",
                    }
                )
            except Exception:
                blob = None
                st, blob, fetched = http_get(url, kind="monthly_zip")
        else:
            st, blob, fetched = http_get(url, kind="monthly_zip")
        http_counts[st] += 1
        ent = {
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
                log(f"parse error {inst} {ym}: {e}")
                continue
            zsha = sha256_bytes(blob)
            flagged_here = 0
            numeric_here = 0
            for r in rows:
                tr = int(r["funding_time"])
                raw_rate = r.get("funding_rate")
                rate_s = "" if raw_rate is None else str(raw_rate)
                if not is_numeric_rate(rate_s):
                    stt = rate_status(rate_s)
                    FLAGGED_ROWS.append(
                        {
                            "inst_id": inst,
                            "funding_time_ms": tr,
                            "funding_time_utc": iso(tr, True),
                            "ts_snapped_ms": snap(tr),
                            "ts_snapped_utc": iso(snap(tr)),
                            "snap_offset_ms": tr - snap(tr),
                            "funding_rate_raw": rate_s,
                            "reject_type": stt,
                            "rate_field": "funding_rate",
                            "source_kind": "monthly_zip",
                            "source_month_cst": ym,
                            "source_file": rel,
                            "zip_sha256": zsha,
                            "fetched_utc": fetched,
                            "flag": reject_flag(stt),
                        }
                    )
                    flagged_here += 1
                    continue
                official.append(
                    (inst, tr, snap(tr), rate_s.strip(), ym, fetched, "monthly_zip", "funding_rate")
                )
                numeric_here += 1
            ent.update(
                {
                    "zip_bytes": len(blob),
                    "zip_sha256": zsha,
                    "rows": len(rows),
                    "rows_numeric": numeric_here,
                    "rows_flagged": flagged_here,
                    "min_ts_utc": iso(min(tss)) if tss else None,
                    "max_ts_utc": iso(max(tss)) if tss else None,
                    "raw_bytes_saved": True,
                    "evidence_form": "raw_zip",
                }
            )
            ok += 1
            if reused:
                reused_n += 1
        else:
            ent["error"] = "http_not_200_or_empty_body"
            ent["raw_bytes_saved"] = False
            fail += 1
        src_months.append(ent)
        if i % 50 == 0 or i == len(pairs):
            log(
                f"Fetch {i}/{len(pairs)} ok={ok} reused={reused_n} fail={fail} "
                f"skipped={skipped} official_rows={len(official)} flagged={len(FLAGGED_ROWS)} "
                f"{time.monotonic()-t0:.1f}s http={dict(http_counts)}"
            )
    return src_months, official


def compare(
    official: list[tuple],
    existing: dict[tuple[str, int], tuple[str, int, float]],
) -> tuple[list[tuple], list[dict[str, Any]], list[list], int, dict[str, int], dict[tuple[str, int], tuple]]:
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
    for k, o in seen.items():
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
                        "official_source_kind": o[6],
                        "type": "+".join(
                            [x for x, c in (("rate_diff", rd), ("ts_raw_diff", td)) if c]
                        ),
                    }
                )
            else:
                matched += 1
        else:
            new_rows.append(o)
    split = {
        "matched": matched,
        "new": len(new_rows),
        "conflicts": len(conflicts),
        "intra_official_dups": len(intra_dup),
    }
    return new_rows, conflicts, intra_dup, matched, split, seen


def write_delta(new_rows: list[tuple], official_seen_keys: dict[tuple[str, int], tuple]) -> tuple[str, bytes, dict[str, int]]:
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
    for o in new_rows:
        inst, tr, sn, rate, ym, fetched, kind, field = o
        p, n = gaps(inst, sn)
        is8 = sn % EIGHT_H_MS == 0
        grid["8h" if is8 else "non_8h"] += 1
        w.writerow(
            [
                inst, tr, iso(tr, True), sn, iso(sn), tr - sn, rate,
                "true" if is8 else "false", p, n, ym, fetched, SOURCE_YM_ZIP, kind, field,
            ]
        )
    csv_b = buf.getvalue().encode()
    delta_p = os.path.join(OUT, "funding_delta_v1_11_b3a.csv.gz")
    with gzip.GzipFile(delta_p, "wb", mtime=0) as g:
        g.write(csv_b)
    return delta_p, csv_b, grid


def write_inventory_r3(
    inv_rows: list[dict[str, str]],
    src_months: list[dict[str, Any]],
    slice_pairs: set[tuple[str, str]],
) -> tuple[str, dict[str, Any]]:
    src_map = {(s["inst_id"], s["month_cst"]): s for s in src_months}
    flagged_months: dict[tuple[str, str], set[str]] = {}
    for fr in FLAGGED_ROWS:
        flagged_months.setdefault((fr["inst_id"], fr["source_month_cst"]), set()).add(fr["flag"])
    out_rows: list[dict[str, str]] = []
    for r in inv_rows:
        rec = dict(r)
        key = (r["inst_id"], r["month_cst"])
        if key not in slice_pairs:
            out_rows.append(rec)
            continue
        s = src_map.get(key)
        if s is None:
            rec["complete"] = rec.get("complete") or ""
            out_rows.append(rec)
            continue
        if s.get("skipped_already_verified"):
            out_rows.append(rec)
            continue
        st = s.get("http")
        rec["http"] = str(st if st is not None else rec.get("http") or "")
        if st == 404:
            rec["class"] = "official_unavailable"
            rec["official_listed"] = "false"
            rec["sub_reason"] = "404_reason_unknown"
            rec["complete"] = ""
        elif st == 200 and s.get("zip_sha256") and "error" not in s:
            rec["official_listed"] = "true"
            rows_n = int(s.get("rows") or 0)
            flagged_n = int(s.get("rows_flagged") or 0)
            numeric_n = int(s.get("rows_numeric") or 0)
            if key in flagged_months:
                rec["class"] = "covered_verified"
                flags = flagged_months[key]
                if flags == {"official_rate_null"}:
                    rec["sub_reason"] = "official_rate_null"
                elif flags == {"official_rate_nonfinite"}:
                    rec["sub_reason"] = "official_rate_nonfinite"
                else:
                    rec["sub_reason"] = ",".join(sorted(flags))
                rec["complete"] = "false"
            elif rows_n > 0 and numeric_n == rows_n and flagged_n == 0:
                rec["class"] = "covered_verified"
                rec["sub_reason"] = ""
                rec["complete"] = "true"
            elif rows_n == 0:
                rec["class"] = "pending_check"
                rec["sub_reason"] = "zip_empty"
                rec["complete"] = ""
            else:
                rec["class"] = "pending_check"
                rec["sub_reason"] = "zip_incomplete_compare"
                rec["complete"] = ""
        else:
            rec["class"] = "pending_check"
            if s.get("error"):
                rec["sub_reason"] = "zip_error" if st == 200 else f"zip_http_{st}"
            else:
                rec["sub_reason"] = f"zip_http_{st}"
            rec["complete"] = ""
        out_rows.append(rec)

    path = os.path.join(OUT, "funding_month_inventory_v1_11_r3.csv")
    fields = list(inv_rows[0].keys()) if inv_rows else []
    if "complete" not in fields:
        fields.append("complete")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    class_c = Counter(r["class"] for r in out_rows)
    complete_c = Counter(r.get("complete") or "" for r in out_rows)
    sub_c = Counter(
        (r["class"] if not r.get("sub_reason") else f"{r['class']}|{r['sub_reason']}")
        + ("" if (r.get("complete") or "") == "" else f"|complete={r['complete']}")
        for r in out_rows
    )
    pending = sum(1 for r in out_rows if r["class"] == "pending_check")
    stats = {
        "class_counts": dict(class_c),
        "complete_counts": {"true": complete_c.get("true", 0), "false": complete_c.get("false", 0), "blank": complete_c.get("", 0)},
        "class_sub_reason_complete": dict(sub_c),
        "pending_check": pending,
    }
    return path, stats


def main() -> int:
    global _EVIDENCE_PATH
    start_utc = ORIGINAL_START_UTC or utc_now_iso()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(ZDIR, exist_ok=True)
    _EVIDENCE_PATH = os.path.join(OUT, EVIDENCE_NAME)
    if not os.path.isfile(_EVIDENCE_PATH) or os.path.getsize(_EVIDENCE_PATH) == 0:
        open(_EVIDENCE_PATH, "w", encoding="utf-8").close()
    else:
        log(f"Keeping existing evidence log ({os.path.getsize(_EVIDENCE_PATH)} bytes); will append only")

    log(f"v1.11-b3a start_utc={start_utc}")
    with open(INV_IN, newline="", encoding="utf-8") as f:
        inv_rows = list(csv.DictReader(f))
    slice_defn, pairs = define_slices(inv_rows)
    log(
        f"Slice {THIS_SLICE}: {len(pairs)} months "
        f"{pairs[0][0]} {pairs[0][1]} .. {pairs[-1][0]} {pairs[-1][1]}"
    )
    verified = {
        (r["inst_id"], r["month_cst"])
        for r in inv_rows
        if r["class"] == "covered_verified"
    }
    log(f"Already covered_verified months (will not refetch): {len(verified)}")
    overlap = [p for p in pairs if p in verified]
    if overlap:
        log(f"WARNING: slice 1 overlaps covered_verified: {len(overlap)}")

    inputs = hash_inputs()
    insts = {i for i, _ in pairs}
    existing = load_existing(insts)
    src_months, official = fetch_slice(pairs, verified)
    log(f"Fetch done: source months {len(src_months)}, official numeric rows {len(official)}, flagged {len(FLAGGED_ROWS)}")

    new_rows, conflicts, intra_dup, matched, split, seen = compare(official, existing)
    delta_p, csv_b, grid = write_delta(new_rows, seen)

    flag_p = os.path.join(OUT, FLAGGED_CSV_NAME)
    with open(flag_p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FLAG_FIELDS)
        w.writeheader()
        w.writerows(FLAGGED_ROWS)
    flagged_by_type = Counter(r["reject_type"] for r in FLAGGED_ROWS)
    flagged_by_flag = Counter(r["flag"] for r in FLAGGED_ROWS)
    log(f"Flagged rows: {len(FLAGGED_ROWS)} by_type={dict(flagged_by_type)} by_flag={dict(flagged_by_flag)}")

    conf_p = os.path.join(OUT, "funding_conflicts_v1_11_b3a.json")
    with open(conf_p, "w", encoding="utf-8") as f:
        json.dump(
            {"conflicts": conflicts, "intra_official_dups": intra_dup},
            f, ensure_ascii=False, indent=2,
        )
        f.write("\n")

    src_p = os.path.join(OUT, "funding_source_months_v1_11_b3a.json")
    with open(src_p, "w", encoding="utf-8") as f:
        json.dump(src_months, f, ensure_ascii=False, indent=2)
        f.write("\n")

    inv_p, inv_stats = write_inventory_r3(inv_rows, src_months, set(pairs))

    http_c: Counter[Any] = Counter()
    for s in src_months:
        if s.get("skipped_already_verified"):
            http_c["skipped_already_verified"] += 1
        else:
            http_c[s.get("http")] += 1
    fetched = sum(1 for s in src_months if not s.get("skipped_already_verified"))
    end_utc = utc_now_iso()

    def rel_sha(path: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        info = fs_rel(path)
        if extra:
            info.update(extra)
        return info

    files_meta = {
        "funding_delta_v1_11_b3a.csv.gz": rel_sha(
            delta_p,
            {"rows": len(new_rows), "csv_bytes": len(csv_b), "csv_sha256": sha256_bytes(csv_b)},
        ),
        FLAGGED_CSV_NAME: rel_sha(flag_p, {"rows": len(FLAGGED_ROWS)}),
        "funding_conflicts_v1_11_b3a.json": rel_sha(conf_p),
        "funding_source_months_v1_11_b3a.json": rel_sha(src_p, {"months": len(src_months)}),
        "funding_month_inventory_v1_11_r3.csv": rel_sha(inv_p, {"rows": len(inv_rows)}),
        EVIDENCE_NAME: rel_sha(_EVIDENCE_PATH),
        "build_delta_v1_11_b3a_public.py": rel_sha(os.path.abspath(__file__)) if os.path.isfile(__file__) else {},
    }

    official_unique = len(seen)
    zip_ok = sum(1 for s in src_months if s.get("http") == 200 and s.get("zip_sha256"))
    manifest = {
        "research_id": RESEARCH_ID,
        "version": VERSION,
        "batch": "v1.11-b3a",
        "slice": slice_defn,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "complete_definition": {
            "true": (
                "Passed per this batch's source and comparison scope only: an official "
                "monthly ZIP was obtained and all of its finite-numeric official keys "
                "were key-compared against existing settlements. This is not a full-period "
                "or cross-frequency verification."
            ),
            "false": (
                "Known incomplete in this batch: the official monthly ZIP was obtained "
                "but at least one official rate was empty, None, or non-finite "
                "(flagged official_rate_null or official_rate_nonfinite)."
            ),
            "blank": "Unknown. Only true means complete (within the limited scope above).",
            "note": (
                "Self-run scans and tests in this batch are team execution evidence, "
                "not ChatGPT runtime certification."
            ),
        },
        "fetch": {
            "pairs_in_slice": len(pairs),
            "fetched": fetched,
            "http_200": int(http_c.get(200, 0)),
            "http_404": int(http_c.get(404, 0)),
            "http_other": {
                str(k): int(v)
                for k, v in sorted(http_c.items(), key=lambda kv: str(kv[0]))
                if k not in (200, 404, "skipped_already_verified")
            },
            "skipped_already_verified": int(http_c.get("skipped_already_verified", 0)),
            "zips_saved": zip_ok,
            "reused_from_this_batch": sum(1 for s in src_months if s.get("reused_existing_zip")),
        },
        "official_rows_numeric": len(official),
        "official_unique_keys": official_unique,
        "already_matched_existing": matched,
        "new_rows": len(new_rows),
        "new_rows_grid": {"8h": grid["8h"], "non_8h": grid["non_8h"]},
        "conflicts": len(conflicts),
        "conflicts_by_type": {
            t: sum(1 for c in conflicts if c["type"] == t)
            for t in sorted({c["type"] for c in conflicts})
        },
        "conflicts_by_existing_source": {
            t: sum(1 for c in conflicts if c["existing_source"] == t)
            for t in sorted({c["existing_source"] for c in conflicts})
        },
        "intra_official_dups": len(intra_dup),
        "flagged": {
            "total": len(FLAGGED_ROWS),
            "by_reject_type": dict(flagged_by_type),
            "by_flag": dict(flagged_by_flag),
        },
        "inventory_r3": inv_stats,
        "inputs_sha256": inputs,
        "files": files_meta,
        "rule": (
            "v1.11-b3a slice 1 of 3: official monthly ZIPs for 1,961 pending_check months, "
            "key-compared against frozen + v1.7/v1.9/v1.10/v1.11_b1/v1.11_b2_r1. "
            "Already-verified ZIPs were not refetched. The v1.11-b2 r1 delta (198,354 rows) was not rebuilt. "
            "Non-finite/non-numeric official rates are flagged, never zero-filled. Conflicts never overwrite. "
            "404s stay official_unavailable / 404_reason_unknown. "
            "complete=true is passed per this batch's source and comparison scope only, not full-period or "
            "cross-frequency verified; blank=unknown. Team execution evidence, not ChatGPT runtime certification. "
            "FIB-4H-LONG-V3 remains NO-GO; live_approved is false."
        ),
        "remaining": {
            "pending_check": inv_stats["pending_check"],
            "includes_rvn_2026_11": True,
            "remaining_slices": [2, 3],
            "prior_404_reason_unknown": 4,
        },
    }

    # files_meta for the public script may be empty if __file__ is unusual; fill after copy
    mf_p = os.path.join(OUT, "funding_delta_v1_11_b3a_manifest.json")
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    open(mf_p, "w", encoding="utf-8").write(text)
    # add manifest sha later in a second write after CHANGELOG/script hashes; first write is enough for counts

    counts_p = os.path.join(OUT, "_counts_internal.json")
    # internal only — deleted before publish if it would leak; keep counts for CHANGELOG writer in-process
    log(
        f"DONE new={len(new_rows)} 8h={grid['8h']} non_8h={grid['non_8h']} "
        f"matched={matched} conflicts={len(conflicts)} flagged={len(FLAGGED_ROWS)} "
        f"http={dict(http_c)} pending={inv_stats['pending_check']} "
        f"complete={inv_stats['complete_counts']}"
    )
    log(f"end_utc={end_utc}")
    # write a counts sidecar without paths for the follow-up writer
    sidecar = {
        "start_utc": start_utc,
        "end_utc": end_utc,
        "fetch": manifest["fetch"],
        "official_rows_numeric": len(official),
        "official_unique_keys": official_unique,
        "already_matched_existing": matched,
        "new_rows": len(new_rows),
        "new_rows_grid": grid,
        "conflicts": len(conflicts),
        "conflicts_by_type": manifest["conflicts_by_type"],
        "conflicts_by_existing_source": manifest["conflicts_by_existing_source"],
        "intra_official_dups": len(intra_dup),
        "flagged": manifest["flagged"],
        "inventory_r3": inv_stats,
    }
    open(os.path.join(OUT, "funding_delta_v1_11_b3a_counts.json"), "w", encoding="utf-8").write(
        json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
