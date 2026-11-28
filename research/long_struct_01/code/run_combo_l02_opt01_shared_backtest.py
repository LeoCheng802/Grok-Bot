#!/usr/bin/env python3
"""BACKTEST-READINESS-01 v1.20 | COMBO_L02_OPT01_SHARED_50K_10X offline runner.

One shared account, NOT two independent 50,000 USDT books added together:
  * leg 0 (long)  = LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT  (run_long_struct_bounded_backtest.py, unchanged rules/defaults)
  * leg 1 (short) = RETEST24_OPT_01_BEARISH_CLOSE_POS   (run_retest24_bounded_backtest.py, unchanged rules)
                    sized by the frozen R1_150U (150U / 600U) spec, or by the R2 sizing (100U / 400U) in the
                    combo arm OPT01_SIG_R2_SIZING_100U.  That arm is NOT the "R2" comparison: "R2" means the
                    original independent RETEST24 R2 baseline (ChatGPT v1.19 item 5); this arm can never replace it.
Both legs run inside ONE call of the registered B6/Q38 engine (patched copy, see _build_combo_sim):
  ESTABLISHED COMBO BASIS
  * one realised equity, one MTM equity / drawdown, one initial-margin pool (pending + open, both legs),
    one liquidation check, identical fair cost (maker 0.02%, taker 0.05%, slip 0.03%, MMR 1%, 10x cap);
    (candidate mapping, slippage alignment and isolation fixes vs the original research are done by the
     ChatGPT original research and are NOT in scope here; current adapter values are kept unchanged);
  * each leg keeps its own frozen per-leg rules; per-leg daily loss day boundary is a parameter
    (--leg-daily-loss-day, default taipei = Asia/Taipei 00:00 reset; utc = frozen PREREG v1.0 basis;
     the program default stays taipei = a DECLARED deviation from PREREG v1.0; the ChatGPT v1.20 main comparison
     explicitly passes --leg-daily-loss-day utc, so taipei is a separate scenario);
  * cross-leg order on one 4H bar (--cross-leg-order, default rank_interleave): each direction keeps its own
    frozen sort; directions are interleaved by same-scale rank (0, 1, 2, ...), equal rank -> --leg-priority
    (default long_first).  direction_block (whole direction first) is the v1.17 behaviour, sensitivity only.
  v1.20 decided main-comparison basis (ChatGPT v1.20, Issue #1 #7235223075; program defaults are NOT changed):
      --leg-daily-loss-day utc --cross-leg-order rank_interleave --global-max-slots 0 --global-daily-loss-u 0
      --same-inst-policy off   (each leg's own limits and the shared-margin rejection still apply);
      the research-added controls below are separate scenarios only.
  RESEARCH-ADDED RISK CONTROLS (listed separately; each can be switched off; differences must not be
  attributed to signals alone):
      - global active slots (open positions + resting entry orders, both legs)  --global-max-slots (0 = off)
      - global realised daily loss (Taipei day, net incl. fee and booked funding) --global-daily-loss-u (0 = off)
      - same-instrument cross-leg policy                                      --same-inst-policy block_any|allow_opposite|off
  * uncomputable windows: ONLY explicit, evidence-backed windows where required PRICE data is missing
    (--uncomputable-windows, each entry needs a non-empty "evidence") block new entries and flag overlaps.

v1.15 preliminary-data policy (data mostly complete -> run, annotate gaps):
  * missing funding rates stay UNKNOWN: never zero-filled, never interpolated, no symbol dropped;
    the engine books only rates present in the funding DB, so any result with unknown funding is a
    CONDITIONAL scenario (unknown funding not booked) and must not be called true net performance;
  * missing 8H grid events are listed in full (local details), no abort;
  * funding-month inventory: ONLY complete == "true" counts as complete; "false" / blank / anything else = not complete;
  * inventory sub_reason rest_51001_instrument_not_listed (e.g. RVN 2026-11) is a FUNDING annotation only
    (v1.19 item 3): the instrument stays in the population, entries are NOT blocked, the missing rates stay
    unknown and every position touching that month carries the note.

Adapter integrity (v1.19 item 6): the outer offline guard (socket / urllib / http.client blocked) is entered
BEFORE any adapter is read; both adapters are read once, their full size and SHA-256 are compared with the
expected values (pinned constants, or explicit --*-adapter-size/--*-adapter-sha256 for an override path),
and only the verified bytes are compiled and executed.  A mismatch refuses before any adapter code runs.

Output contract: --out-dir must be a NEW isolated directory (absent or empty); combo_result.json exists only
after a complete run; any failure leaves no result file and no *.tmp. The exact patched engine source is
written to combo_engine_patched_source.txt and its SHA-256 recorded in combo_result.json (v1.19 item 8).
Zero network, zero credentials, no order/exchange API. Results are always labelled PRELIMINARY (never PASS).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import types
import socket
import urllib.request
import http.client
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

RUNNER_VERSION = "v1.20"
TARGET_BAND_CLOSED_PER_MONTH = (100, 200)
STUDY_ID = "BACKTEST-READINESS-01"
COMBO_ID = "COMBO_L02_OPT01_SHARED_50K_10X"
LONG_CANDIDATE = "LONG_STRUCT_02_V1_0_TEMPORAL_SPLIT"
SHORT_CANDIDATE = "RETEST24_OPT_01_BEARISH_CLOSE_POS"
R2_SIZING_ARM = "OPT01_SIG_R2_SIZING_100U"
SHORT_SIZINGS = {"R1_150U": ("R1", 150.0, 600.0), R2_SIZING_ARM: ("R2", 100.0, 400.0)}
RENAMED_SIZINGS = {"R2_100U": R2_SIZING_ARM}
R2_ARM_NOTE = ("OPT01_SIG_R2_SIZING_100U = OPT01 short signal with R2 sizing (100U / 400U) inside the shared combo; "
               "it is NOT the R2 comparison. 'R2' = the original independent RETEST24 R2 baseline produced by the "
               "already-uploaded script; this arm must never substitute for that comparison.")
FILL_MODES = {"cross_1tick": False, "delay1bar": True}
DEFAULT_SCENARIOS = "R1_150U|cross_1tick,R1_150U|delay1bar,OPT01_SIG_R2_SIZING_100U|cross_1tick,OPT01_SIG_R2_SIZING_100U|delay1bar"
FUNDING_NOTE_SUB_REASONS = ("rest_51001_instrument_not_listed",)  # v1.19: annotation only, never an entry block
PINNED_ADAPTERS = {
    "long": ("run_long_struct_bounded_backtest.py", 57609, "8db9e3fd0f64f86493f39584b5a5849b6f7f1067026a5e75413a86b6e9010a59"),
    "short": ("run_retest24_bounded_backtest.py", 54101, "67094079a995fa6f751d5393127b12895264641ccadc99a105d75511c3742f89"),
}
LEG_DAY_OFFSETS = {"taipei": 8 * 3600000, "utc": 0}
CROSS_LEG_ORDERS = ("rank_interleave", "direction_block")
INVENTORY_REQUIRED_COLS = ("inst_id", "month_cst", "complete")

H1, H4, H8, DAY = 3600000, 14400000, 28800000, 86400000
TZ_UTC = timezone.utc
TZ_CST = timezone(timedelta(hours=8))
COST_KEYS = ("initial_capital_u", "leverage", "mmr_approx", "maker_fee", "taker_fee", "slip_mkt")

RESULT_NAME = "combo_result.json"
DETAILS_NAME = "combo_local_details.json"
SCOPE_NAME = "combo_scope.json"
DERIVED_DB_NAME = "funding_archive_combo_isolated.sqlite"
DERIVED_META_NAME = "funding_archive_combo_isolated.meta.json"
ENGINE_SRC_NAME = "combo_engine_patched_source.txt"


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def _iso(ts_ms):
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=TZ_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cst_month(ts_ms: int) -> str:
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=TZ_CST).strftime("%Y-%m")


def _cst_month_start_ms(month: str) -> int:
    y, m = month.split("-")
    return int(datetime(int(y), int(m), 1, tzinfo=TZ_CST).timestamp() * 1000)


def _next_month(month: str) -> str:
    y, m = (int(x) for x in month.split("-"))
    return "%04d-%02d" % (y + (m // 12), (m % 12) + 1)


def _months_spanned(a_ms: int, b_ms: int):
    """CST months touched by the funding interval (a, b]; empty when b <= a."""
    if b_ms <= a_ms:
        return []
    first, last = _cst_month(a_ms + 1), _cst_month(b_ms)
    out, cur = [], first
    while True:
        out.append(cur)
        if cur == last or len(out) > 1200:
            break
        cur = _next_month(cur)
    return out


class OfflineGuard:
    """Outer network block entered before any adapter is read (v1.19 item 6)."""

    def __init__(self):
        self.hits = []
        self._orig = {}

    def _deny(self, label):
        def _blocked(*args, **kwargs):
            self.hits.append(label)
            raise RuntimeError("OFFLINE_TRANSPORT_BLOCKED: " + label)
        return _blocked

    def __enter__(self):
        self._orig = {
            "create_connection": socket.create_connection, "socket_connect": socket.socket.connect,
            "socket_connect_ex": socket.socket.connect_ex, "getaddrinfo": socket.getaddrinfo,
            "urlopen": urllib.request.urlopen, "http_connect": http.client.HTTPConnection.connect,
            "https_connect": http.client.HTTPSConnection.connect,
        }
        socket.create_connection = self._deny("socket.create_connection")
        socket.socket.connect = self._deny("socket.socket.connect")
        socket.socket.connect_ex = self._deny("socket.socket.connect_ex")
        socket.getaddrinfo = self._deny("socket.getaddrinfo")
        urllib.request.urlopen = self._deny("urllib.request.urlopen")
        http.client.HTTPConnection.connect = self._deny("http.client.HTTPConnection.connect")
        http.client.HTTPSConnection.connect = self._deny("http.client.HTTPSConnection.connect")
        return self

    def __exit__(self, exc_type, exc, tb):
        socket.create_connection = self._orig["create_connection"]
        socket.socket.connect = self._orig["socket_connect"]
        socket.socket.connect_ex = self._orig["socket_connect_ex"]
        socket.getaddrinfo = self._orig["getaddrinfo"]
        urllib.request.urlopen = self._orig["urlopen"]
        http.client.HTTPConnection.connect = self._orig["http_connect"]
        http.client.HTTPSConnection.connect = self._orig["https_connect"]


def _expected_adapter(role, path, cli_size, cli_sha):
    """Expected size/SHA: explicit CLI values, else the pinned constants (never measured from the file itself)."""
    if (cli_size is None) != (cli_sha is None):
        raise RuntimeError(role + " adapter: give both --" + role + "-adapter-size and --" + role + "-adapter-sha256, or neither")
    if cli_sha is not None:
        cli_sha = str(cli_sha).strip().lower()
        if len(cli_sha) != 64 or any(c not in "0123456789abcdef" for c in cli_sha):
            raise RuntimeError(role + " adapter: expected sha256 must be 64 hex chars")
        return int(cli_size), cli_sha, "cli_expected"
    _name, size, digest = PINNED_ADAPTERS[role]
    return size, digest, "pinned_constant"


def _read_verified_adapter(role, path, exp_size, exp_sha):
    """Read the adapter ONCE and verify full size + SHA-256 BEFORE any of its code runs."""
    if not path.is_file():
        raise RuntimeError(role + " adapter is not a regular file: " + path.name)
    data = path.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if len(data) != int(exp_size) or got != exp_sha:
        raise RuntimeError("%s adapter size/SHA mismatch before load (expected %d B %s, got %d B %s); refusing before any adapter code runs"
                           % (role, int(exp_size), exp_sha, len(data), got))
    return data, got


def _load_module_from_bytes(name: str, path: Path, data: bytes):
    """Execute exactly the verified bytes (no second read of the file)."""
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    try:
        exec(compile(data, str(path), "exec"), mod.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def _require_fresh_out_dir(out_dir: Path) -> None:
    """Every run needs a NEW isolated output directory (old evidence is never mixed or overwritten)."""
    if out_dir.is_symlink():
        raise RuntimeError("out-dir must be a new isolated directory, not a symlink; refusing before any write")
    if out_dir.exists():
        if not out_dir.is_dir():
            raise RuntimeError("out-dir exists and is not a directory; refusing before any write")
        if any(out_dir.iterdir()):
            raise RuntimeError(
                "out-dir already contains files (possible stale result/abort evidence); "
                "every run needs a NEW isolated out-dir; refusing before any write"
            )


def load_funding_inventory(path: Path):
    """Parse the funding-month inventory. Only complete == 'true' (exact) counts as complete."""
    inv = {}
    uncomputable = {}
    stats = {"rows": 0, "complete_true": 0, "complete_false": 0, "complete_blank": 0, "complete_other": 0}
    with open(path, "r", encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames or []
        miss = [c for c in INVENTORY_REQUIRED_COLS if c not in cols]
        if miss:
            raise RuntimeError("funding inventory missing columns: " + ", ".join(miss))
        for row in rd:
            stats["rows"] += 1
            inst = (row.get("inst_id") or "").strip()
            month = (row.get("month_cst") or "").strip()
            if not inst or len(month) != 7 or month[4] != "-":
                raise RuntimeError("funding inventory row has invalid inst_id/month_cst")
            raw_c = row.get("complete")
            raw_c = "" if raw_c is None else raw_c
            if raw_c == "true":
                stats["complete_true"] += 1
                status = "complete_true"
            elif raw_c == "false":
                stats["complete_false"] += 1
                status = "complete_false"
            elif raw_c == "":
                stats["complete_blank"] += 1
                status = "unknown_blank"
            else:
                stats["complete_other"] += 1
                status = "unknown_unrecognised_value"
            rec = {
                "status": status,
                "class": (row.get("class") or "").strip(),
                "sub_reason": (row.get("sub_reason") or "").strip(),
            }
            key = (inst, month)
            if key in inv and inv[key] != rec:
                raise RuntimeError("funding inventory has conflicting duplicate rows for " + inst + " " + month)
            inv[key] = rec
            if rec["sub_reason"] in FUNDING_NOTE_SUB_REASONS:
                # v1.19 item 3: a REST 51001 funding query proves nothing about prices or trading in that month;
                # population kept, entries NOT blocked, missing rates stay unknown (annotation only).
                uncomputable.setdefault(inst, {})[month] = (
                    "funding_query:" + rec["sub_reason"] + ":" + month
                    + " (funding rates unknown, not booked, not zero-filled; NOT an entry block, NOT uncomputable by itself)")
    return inv, uncomputable, stats


def load_uncomputable_windows(path: Path, parse_utc_ms):
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("windows") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise RuntimeError("uncomputable windows JSON must be a list or {\"windows\": [...]}")
    out = {}
    for it in items:
        if not isinstance(it, dict) or not it.get("inst_id") or not it.get("from_utc"):
            raise RuntimeError("uncomputable window entry needs inst_id and from_utc")
        if not str(it.get("evidence") or "").strip():
            raise RuntimeError("uncomputable window for " + str(it["inst_id"]) + " needs non-empty 'evidence' that required PRICE data is missing "
                               "(v1.19: a missing funding rate alone is never uncomputable)")
        a = parse_utc_ms(str(it["from_utc"]))
        b = parse_utc_ms(str(it["to_utc"])) if it.get("to_utc") else None
        if b is not None and b <= a:
            raise RuntimeError("uncomputable window to_utc must be > from_utc")
        out.setdefault(str(it["inst_id"]), []).append({"from_ms": a, "to_ms": b, "reason": str(it.get("reason") or "explicit"),
                                                       "evidence": str(it["evidence"]).strip()})
    return out


# ---------------------------------------------------------------------------------------------
# combo engine: patched copy of the registered b6 engine (the registered files are not modified)
# ---------------------------------------------------------------------------------------------

def describe_controls(args):
    """Texts for limitations / model-vs-live diff, derived from the ACTUAL parameters of this run (v1.20 item 4)."""
    if args.leg_daily_loss_day == "utc":
        leg_day = "各腿日損日界：UTC 日（UTC 00:00 重置；凍結 PREREG v1.0 口徑）"
        leg_day_en = "per-leg daily loss day: UTC day (UTC 00:00 reset, frozen PREREG v1.0 basis)"
    else:
        leg_day = "各腿日損日界：台北日（Asia/Taipei 00:00 重置；偏離 PREREG v1.0 的 UTC 日；不是 ChatGPT v1.20 主比較口徑）"
        leg_day_en = "per-leg daily loss day: Taipei day (Asia/Taipei 00:00 reset; deviation from PREREG v1.0 UTC day)"
    if args.global_daily_loss_u > 0:
        g_loss = "共同日損限制（另加研究風控）：啟用，兩腿合計每台北日已實現淨損達 %gU 即停止新單（全局日界＝台北日）" % args.global_daily_loss_u
        g_loss_en = "global daily-loss gate (research-added): ON, %gU realised net loss per Taipei day, both legs; global day = Taipei day" % args.global_daily_loss_u
    else:
        g_loss = "共同日損限制：關閉（--global-daily-loss-u 0），本次沒有共同日損限制；全局日界不適用"
        g_loss_en = "global daily-loss gate: OFF in this run (no global daily-loss limit; no global day boundary applies)"
    if args.global_max_slots > 0:
        g_slots = "共同名額限制（另加研究風控）：啟用，持倉＋掛單合計上限 %d 格（兩腿合計）" % args.global_max_slots
    else:
        g_slots = "共同名額限制：關閉（--global-max-slots 0），本次沒有共同名額上限"
    if args.same_inst_policy == "off":
        g_same = "同幣跨腿規則：關閉（--same-inst-policy off），同一幣可兩腿同時持有"
    else:
        g_same = "同幣跨腿規則（另加研究風控）：%s" % args.same_inst_policy
    order = ("跨方向排序：同尺度名次交錯，同名次依 --leg-priority=%s；各方向內排序不變" % args.leg_priority
             if args.cross_leg_order == "rank_interleave" else "跨方向排序：整個方向先後（direction_block，僅敏感度）")
    return {
        "limitations": [leg_day, g_loss, g_slots, g_same, order],
        "diff": [
            leg_day_en,
            g_loss_en,
            "each leg keeps its own frozen per-leg slot / daily-loss / loss-streak limits (values: PREREG v1.0 legs); "
            "shared-margin rejection applies to the whole account",
            "live shared_risk.RiskLedger keys slots by (strategy, inst, pos_side); this run's same-instrument rule: " + args.same_inst_policy
            + (" (block_any is stricter than the live ledger)" if args.same_inst_policy == "block_any" else ""),
            "same-bar cross-leg order: --cross-leg-order " + args.cross_leg_order + " (equal rank -> --leg-priority " + args.leg_priority
            + "); each leg's own frozen sort key kept",
        ],
    }


def _monthly_combined(short_mod, ol, trades, leg_ym, start_ts, end_ts):
    """Long+short combined monthly stats: closed trades by EXIT UTC month, first fills, per-direction contribution (v1.20)."""
    allm = short_mod._build_by_year_month(ol, trades, start_ts_ms=start_ts, end_ts_ms=end_ts)
    lo, hi = TARGET_BAND_CLOSED_PER_MONTH
    out, full, inb, below, above = {}, 0, 0, 0, 0
    for ym, b in allm.items():
        l = leg_ym[0].get(ym) or {}
        sh = leg_ym[1].get(ym) or {}
        row = {
            "is_partial_month": b["is_partial_month"],
            "closed_trades_total": b["closed_trades"],
            "unique_first_fills_total": b["unique_first_fills"],
            "closed_net_u_total": b["closed_net_u"],
            "long_closed_trades": l.get("closed_trades", 0), "short_closed_trades": sh.get("closed_trades", 0),
            "long_unique_first_fills": l.get("unique_first_fills", 0), "short_unique_first_fills": sh.get("unique_first_fills", 0),
            "long_closed_net_u": l.get("closed_net_u", 0.0), "short_closed_net_u": sh.get("closed_net_u", 0.0),
        }
        if b["is_partial_month"] is False:
            full += 1
            n = b["closed_trades"]
            in_band = lo <= n <= hi
            row["in_target_band_%d_%d" % (lo, hi)] = in_band
            inb += 1 if in_band else 0
            below += 1 if n < lo else 0
            above += 1 if n > hi else 0
        else:
            row["in_target_band_%d_%d" % (lo, hi)] = None
        out[ym] = row
    return {
        "definition": ("closed_trades_total = long+short positions fully closed (final exit), counted by EXIT UTC month; "
                       "unique_first_fills_total = first fills by fill UTC month (includes still-open positions); "
                       "positions opened in a month are NOT counted as complete trades; open_at_end positions are not complete trades"),
        "target_band_closed_per_month": [lo, hi],
        "target_band_applies_to": "full UTC months only (partial months are reported but not judged)",
        "summary": {"full_months": full, "months_in_band": inb, "months_below_band": below, "months_above_band": above},
        "by_year_month": out,
    }


def _combo_init(ctrl):
    if ctrl is None:
        return None
    return {
        "global_max_slots": int(ctrl["global_max_slots"]),
        "global_daily_loss_u": float(ctrl["global_daily_loss_u"]),
        "same_inst_policy": ctrl["same_inst_policy"],
        "leg_sides": list(ctrl["leg_sides"]),
        "uncomputable": ctrl.get("uncomputable") or {},
        "gday": {},
        "blocked": {},
        "events": [],
    }


def _combo_block(cb, reason, li, inst, t30, extra=None):
    d = cb["blocked"].setdefault(reason, {})
    d[str(li)] = d.get(str(li), 0) + 1
    ev = {"reason": reason, "leg": li, "inst_id": inst, "ts_ms": int(t30)}
    if extra:
        ev.update(extra)
    cb["events"].append(ev)
    return True


def _combo_gate(cb, li, inst, t30, pos, pend, legs):
    for w in cb["uncomputable"].get(inst, ()):
        if w["from_ms"] <= t30 and (w["to_ms"] is None or t30 < w["to_ms"]):
            return _combo_block(cb, "uncomputable_window", li, inst, t30, {"window_reason": w["reason"]})
    holders = [] if cb["same_inst_policy"] == "off" else [(k, "open") for k in pos if k[1] == inst and k[0] != li]
    holders += [] if cb["same_inst_policy"] == "off" else [(k, "pending", od) for k, od in pend.items() if k[1] == inst and k[0] != li]
    for h in holders:
        k, state = h[0], h[1]
        same_side = cb["leg_sides"][k[0]] == cb["leg_sides"][li]
        if cb["same_inst_policy"] == "block_any" or same_side:
            same_bar = state == "pending" and int(h[2]["pts"]) == int(t30)
            return _combo_block(cb, "same_bar_cross_leg_same_inst" if same_bar else "same_inst_held_by_other_leg",
                                li, inst, t30, {"holder_leg": k[0], "holder_state": state})
    if cb["global_max_slots"] > 0 and len(pos) + len(pend) >= cb["global_max_slots"]:
        return _combo_block(cb, "global_slots_full", li, inst, t30, {"active": len(pos) + len(pend)})
    day = (int(t30) + 8 * H1) // DAY
    if cb["global_daily_loss_u"] > 0 and cb["gday"].get(day, 0.0) <= -cb["global_daily_loss_u"]:
        return _combo_block(cb, "global_daily_loss_taipei_day", li, inst, t30, {"day_net_u": round(cb["gday"][day], 6)})
    return False


def _combo_book(cb, t30, pnl):
    if cb is None:
        return
    day = (int(t30) + 8 * H1) // DAY
    cb["gday"][day] = cb["gday"].get(day, 0.0) + float(pnl)


def _combo_export(cb):
    if cb is None:
        return None
    return {
        "blocked_counts": cb["blocked"],
        "blocked_events": cb["events"],
        "taipei_day_realised_net_u": {
            datetime.fromtimestamp(d * DAY / 1000.0, tz=TZ_UTC).strftime("%Y-%m-%d"): round(v, 6)
            for d, v in sorted(cb["gday"].items())
        },
    }


_PATCHES = (
    ("signature",
     'def run_audit_sim_b6(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False, fill_mode="cross_1tick", delay_first_bar=False):',
     'def run_audit_sim_combo(raw, bars, spec, ov_raw_ts=None, cands_pre=None, max_lev_pre=None, boundary_mode="default", record_events=False, record_trades_detail=False, fill_mode="cross_1tick", delay_first_bar=False, combo=None):',
     1),
    ("init",
     '    trades, last_c = [], {}; _ord_log = []; _skip_fb_cross = 0; _same_bar_sl = 0',
     '    trades, last_c = [], {}; _ord_log = []; _skip_fb_cross = 0; _same_bar_sl = 0; _cb = _combo_init(combo); '
     '_leg_doff = int((combo or {}).get("leg_day_offset_ms", 0))',
     1),
    ("leg_day_boundary", 'ud = t30 // DAY', 'ud = (t30 + _leg_doff) // DAY', 3),
    ("gate",
     '                if (li, inst) in pos or (li, inst) in pend or blk.get((li, inst), 0) > t30 or t30 < pause_u[li]: continue\n',
     '                if (li, inst) in pos or (li, inst) in pend or blk.get((li, inst), 0) > t30 or t30 < pause_u[li]: continue\n'
     '                if _cb is not None and _combo_gate(_cb, li, inst, t30, pos, pend, legs): continue\n',
     1),
    ("book",
     'dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl;',
     'dpnl[(li, ud)] = dpnl.get((li, ud), 0.0) + pnl; _combo_book(_cb, t30, pnl);',
     2),
    ("leg_expired", '"outcome": "expired"', '"outcome": "expired", "leg": k[0]', 1),
    ("leg_margin_rej", '"outcome": "margin_rej"', '"outcome": "margin_rej", "leg": li', 1),
    ("leg_filled", '"outcome": "filled"', '"outcome": "filled", "leg": li', 1),
    ("leg_pend_at_end", '"outcome": "pend_at_end"', '"outcome": "pend_at_end", "leg": li', 1),
    ("export",
     '    out["_ord_log"] = _ord_log\n',
     '    out["_ord_log"] = _ord_log\n'
     '    out["_combo"] = _combo_export(_cb)\n'
     '    out["_combo_open"] = [{"leg": k[0], "inst": k[1], "side": p["side"], "ets": p["ets"]} for k, p in pos.items()]\n',
     1),
)


def _build_combo_sim(b6mod):
    src = getattr(b6mod, "_sim_src", None)
    q38a = getattr(b6mod, "q38a", None)
    if not isinstance(src, str) or q38a is None:
        raise RuntimeError("registered b6_sim_portable does not expose _sim_src/q38a; cannot build the shared-account combo engine")
    for name, old, new, cnt in _PATCHES:
        if src.count(old) != cnt:
            raise RuntimeError("combo engine patch anchor mismatch: " + name)
        src = src.replace(old, new)
    ns = dict(q38a.__dict__)
    ns.update({"_combo_init": _combo_init, "_combo_gate": _combo_gate, "_combo_book": _combo_book, "_combo_export": _combo_export})
    exec(compile(src, "<run_audit_sim_combo>", "exec"), ns)
    return ns["run_audit_sim_combo"], hashlib.sha256(src.encode("utf-8")).hexdigest(), src


# ---------------------------------------------------------------------------------------------
# annotations (v1.15)
# ---------------------------------------------------------------------------------------------

def _funding_status_for_months(inv, inst, months):
    if inv is None:
        return "inventory_not_supplied", {m: "inventory_not_supplied" for m in months}
    per = {m: (inv.get((inst, m)) or {"status": "unknown_not_in_inventory"})["status"] for m in months}
    if not months:
        return "no_funding_interval", per
    return ("complete_by_batch_scope" if all(v == "complete_true" for v in per.values()) else "incomplete_or_unknown"), per


def _overlaps(windows, a_ms, b_ms):
    hits = []
    for w in windows or ():
        lo, hi = w["from_ms"], w["to_ms"]
        if b_ms >= lo and (hi is None or a_ms < hi):
            hits.append(w["reason"])
    return hits


def _funding_notes_for(notes, inst, months):
    d = (notes or {}).get(inst) or {}
    return [d[m] for m in months if m in d]


def annotate_arm(r, leg_names, inv, unc, last_bar, funding_notes=None):
    trades_out = []
    flags = {"funding_incomplete_or_unknown_trades": 0, "uncomputable_trades": 0, "no_funding_interval_trades": 0,
             "funding_query_51001_note_positions": 0}
    side_to_leg = {"long": 0, "short": 1}
    for i, t in enumerate(r.get("_trades", [])):
        inst, ets, xts = t["inst"], int(t["ets"]), int(t["xts"])
        months = _months_spanned(ets, xts)
        fst, per = _funding_status_for_months(inv, inst, months)
        unc_hits = _overlaps(unc.get(inst), ets, xts)
        if fst == "incomplete_or_unknown" or fst == "inventory_not_supplied":
            flags["funding_incomplete_or_unknown_trades"] += 1
        if fst == "no_funding_interval":
            flags["no_funding_interval_trades"] += 1
        if unc_hits:
            flags["uncomputable_trades"] += 1
        fnotes = _funding_notes_for(funding_notes, inst, months)
        if fnotes:
            flags["funding_query_51001_note_positions"] += 1
        leg = side_to_leg[t["side"]]
        trades_out.append({
            "seq": i + 1, "leg": leg, "leg_name": leg_names[leg], "inst_id": inst, "side": t["side"],
            "ets_ms": ets, "ets_utc": _iso(ets), "xts_ms": xts, "xts_utc": _iso(xts),
            "net_pnl_u": round(float(t["net"]), 6), "fee_u": round(float(t["fee"]), 6), "fund_booked_u": round(float(t["fund"]), 6),
            "reason": t.get("reason"), "funding_status": fst, "funding_months_cst": per,
            "computability": "不可計算(UNCOMPUTABLE)" if unc_hits else "computable", "uncomputable_reasons": unc_hits,
            "funding_notes": fnotes,
        })
    open_out = []
    for p in r.get("_combo_open", []):
        ets = int(p["ets"])
        months = _months_spanned(ets, int(last_bar))
        fst, per = _funding_status_for_months(inv, p["inst"], months)
        unc_hits = _overlaps(unc.get(p["inst"]), ets, int(last_bar))
        if unc_hits:
            flags["uncomputable_trades"] += 1
        fnotes = _funding_notes_for(funding_notes, p["inst"], months)
        if fnotes:
            flags["funding_query_51001_note_positions"] += 1
        open_out.append({"leg": p["leg"], "leg_name": leg_names[p["leg"]], "inst_id": p["inst"], "side": p["side"],
                         "ets_ms": ets, "ets_utc": _iso(ets), "funding_status": fst, "funding_months_cst": per,
                         "computability": "不可計算(UNCOMPUTABLE)" if unc_hits else "computable", "uncomputable_reasons": unc_hits,
                         "funding_notes": fnotes})
    miss = sorted(e for e in r.get("events_set", set()) if len(e) >= 4 and e[3] == "miss_8h")
    miss_out = [{"leg": int(e[0]), "inst_id": e[1], "ts_ms": int(e[2]), "ts_utc": _iso(e[2]), "kind": e[3]} for e in miss]
    return trades_out, open_out, miss_out, flags


def _leg_stats(trades):
    n = len(trades)
    net = sum(t["net_pnl_u"] for t in trades)
    wins = [t["net_pnl_u"] for t in trades if t["net_pnl_u"] > 0]
    losses = [-t["net_pnl_u"] for t in trades if t["net_pnl_u"] < 0]
    return {
        "closed_trades": n,
        "win_rate_pct": round(100.0 * len(wins) / n, 2) if n else 0.0,
        "net_pnl_u_booked": round(net, 2),
        "profit_factor": (round(sum(wins) / sum(losses), 3) if losses else ("INF" if wins else 0.0)),
        "fee_u": round(sum(t["fee_u"] for t in trades), 2),
        "fund_booked_u": round(sum(t["fund_booked_u"] for t in trades), 2),
    }


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def parse_args(argv=None):
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="BACKTEST-READINESS-01 v1.19 shared 50,000 USDT / 10x combo (LONG_STRUCT_02 + RETEST24 OPT-01) offline runner")
    p.add_argument("--manifest", required=True, help="REPRO_MANIFEST.json (registers RETEST24 script, shared_risk.py, engine files)")
    p.add_argument("--retest24-script", required=True)
    p.add_argument("--shared-risk", required=True)
    p.add_argument("--cache-dir")
    p.add_argument("--funding-db")
    p.add_argument("--out-dir", help="NEW isolated output directory (must be absent or empty)")
    p.add_argument("--input-manifest", default="", help="per-symbol NPZ sha256/size_bytes manifest")
    p.add_argument("--symbols", default="", help="comma list; empty = all cache symbols excl. USDC-USDT-SWAP (EX_USDC_286)")
    p.add_argument("--start-utc", default="2023-01-01T00:00:00Z")
    p.add_argument("--end-utc", default="2026-11-26T12:00:00Z")
    p.add_argument("--scenarios", default=DEFAULT_SCENARIOS, help="comma list of <R1_150U|OPT01_SIG_R2_SIZING_100U>|<cross_1tick|delay1bar>")
    p.add_argument("--global-max-slots", type=int, default=12, help="RESEARCH-ADDED: open positions + resting entries, both legs (shared_risk default 12; 0 = off)")
    p.add_argument("--global-daily-loss-u", type=float, default=600.0, help="RESEARCH-ADDED: realised net loss per Taipei day, both legs (shared_risk default 600; 0 = off)")
    p.add_argument("--same-inst-policy", choices=("block_any", "allow_opposite", "off"), default="block_any", help="RESEARCH-ADDED cross-leg same-instrument rule")
    p.add_argument("--leg-priority", choices=("long_first", "short_first"), default="long_first", help="tie-break at equal cross-leg rank (or whole-direction order with direction_block)")
    p.add_argument("--cross-leg-order", choices=CROSS_LEG_ORDERS, default="rank_interleave",
                   help="rank_interleave: same-scale rank interleave, equal rank -> --leg-priority; direction_block: v1.17 whole-direction order (sensitivity)")
    p.add_argument("--leg-daily-loss-day", choices=tuple(LEG_DAY_OFFSETS), default="taipei",
                   help="per-leg daily-loss day boundary: taipei (Asia/Taipei 00:00, default; deviation from PREREG v1.0) or utc (PREREG v1.0)")
    p.add_argument("--long-adapter-size", type=int, default=None)
    p.add_argument("--long-adapter-sha256", default=None)
    p.add_argument("--short-adapter-size", type=int, default=None)
    p.add_argument("--short-adapter-sha256", default=None)
    p.add_argument("--funding-inventory", default="", help="funding month inventory CSV (only complete==true counts as complete)")
    p.add_argument("--uncomputable-windows", default="", help="optional JSON list of {inst_id, from_utc, to_utc?, reason}")
    p.add_argument("--long-adapter", default=str(here / "run_long_struct_bounded_backtest.py"))
    p.add_argument("--short-adapter", default=str(here / "run_retest24_bounded_backtest.py"))
    p.add_argument("--dry-check", action="store_true", help="verify manifest bindings and parse scope only")
    return p.parse_args(argv)


def main(argv=None) -> int:
    t0 = time.time()
    started_utc = datetime.now(TZ_UTC).isoformat()
    args = parse_args(argv)
    long_path = Path(args.long_adapter).expanduser().resolve()
    short_path = Path(args.short_adapter).expanduser().resolve()
    with OfflineGuard() as guard:
        exp_long = _expected_adapter("long", long_path, args.long_adapter_size, args.long_adapter_sha256)
        exp_short = _expected_adapter("short", short_path, args.short_adapter_size, args.short_adapter_sha256)
        long_bytes, long_sha_before = _read_verified_adapter("long", long_path, exp_long[0], exp_long[1])
        short_bytes, short_sha_before = _read_verified_adapter("short", short_path, exp_short[0], exp_short[1])
        adapter_verification = {
            "order": "outer_offline_guard_entered -> adapters read once -> full size+SHA verified -> verified bytes executed",
            "long": {"size": len(long_bytes), "sha256": long_sha_before, "expected_source": exp_long[2]},
            "short": {"size": len(short_bytes), "sha256": short_sha_before, "expected_source": exp_short[2]},
        }
        short_mod = _load_module_from_bytes("combo_short_adapter_retest24", short_path, short_bytes)
        return _main_guarded(args, t0, started_utc, guard, long_path, short_path, long_bytes, long_sha_before,
                             short_sha_before, short_mod, adapter_verification)


def _main_guarded(args, t0, started_utc, guard, long_path, short_path, long_bytes, long_sha_before,
                  short_sha_before, short_mod, adapter_verification) -> int:
    with short_mod.TransportBlocker() as tb:
        long_mod = _load_module_from_bytes("combo_long_adapter_long_struct", long_path, long_bytes)
        manifest_path = Path(args.manifest).expanduser()
        retest_path = Path(args.retest24_script).expanduser()
        shared_risk_path = Path(args.shared_risk).expanduser()
        bound = short_mod._verify_manifest_bindings(manifest_path, retest_path, shared_risk_path)

        scen = [s.strip() for s in args.scenarios.split(",") if s.strip()]
        if not scen:
            raise RuntimeError("at least one scenario is required")
        for s in scen:
            parts = s.split("|")
            if parts and parts[0] in RENAMED_SIZINGS:
                raise RuntimeError("scenario sizing " + parts[0] + " was renamed to " + RENAMED_SIZINGS[parts[0]]
                                   + " in v1.19 (it is NOT the R2 comparison; R2 = original independent RETEST24 R2 baseline)")
            if len(parts) != 2 or parts[0] not in SHORT_SIZINGS or parts[1] not in FILL_MODES:
                raise RuntimeError("unsupported scenario: " + s)
        if len(set(scen)) != len(scen):
            raise RuntimeError("duplicate scenario")
        if args.global_max_slots < 0:
            raise RuntimeError("global-max-slots must be >= 0 (0 = research control off)")
        if not (args.global_daily_loss_u >= 0):
            raise RuntimeError("global-daily-loss-u must be >= 0 (0 = research control off)")
        start_ts = short_mod.parse_utc_ms(args.start_utc)
        end_ts = short_mod.parse_utc_ms(args.end_utc)
        if end_ts < start_ts:
            raise RuntimeError("end-utc must be >= start-utc")
        requested_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

        scope = {
            "study_id": STUDY_ID, "version": RUNNER_VERSION, "combo_id": COMBO_ID,
            "capital_model": "SINGLE_SHARED_ACCOUNT_50000U_10X_ONE_EQUITY_ONE_MARGIN_POOL (not two books added)",
            "legs": {"0": {"name": LONG_CANDIDATE, "side": "long"}, "1": {"name": SHORT_CANDIDATE, "side": "short"}},
            "scenarios": scen, "start_utc": args.start_utc, "end_utc": args.end_utc,
            "universe": requested_symbols if requested_symbols else "ALL_CACHE_EX_USDC (EX_USDC_286)",
            "established_combo_basis": {
                "capital": "one shared 50,000U / 10x account, both legs in one engine call",
                "per_leg_rules": "each leg keeps its own frozen rules (long 24 slots / 600U / 3-loss pause; short 12 slots / R1 600U or R2-sizing 400U); per-leg day boundary = " + args.leg_daily_loss_day,
                "leg_daily_loss_day": args.leg_daily_loss_day,
                "leg_daily_loss_day_meaning": ("Asia/Taipei 00:00 reset (DEVIATION from PREREG v1.0 UTC day; NOT the ChatGPT v1.20 main-comparison basis, which passes utc explicitly)"
                                               if args.leg_daily_loss_day == "taipei" else "UTC 00:00 reset (PREREG v1.0 basis)"),
                "cross_leg_order": args.cross_leg_order, "leg_priority": args.leg_priority,
                "cross_leg_order_meaning": ("same-scale rank interleave; equal rank -> " + args.leg_priority + "; within-direction order unchanged"
                                            if args.cross_leg_order == "rank_interleave" else "v1.17 whole-direction order (sensitivity only)"),
                "out_of_scope": "candidate mapping, slippage alignment (original research 0.0005 vs current 0.0003), original 24-slot mapping and isolation fixes are done by the ChatGPT original research; current values kept",
            },
            "research_added_risk_controls": {
                "note": "NOT part of the established combo basis; listed separately, each switchable; result differences must not be attributed to signals alone",
                "global_max_slots": {"enabled": args.global_max_slots > 0, "value": args.global_max_slots},
                "global_daily_loss_u": {"enabled": args.global_daily_loss_u > 0, "value": args.global_daily_loss_u,
                                        "day": "Asia/Taipei (UTC+8) calendar day, realised net incl. fee and booked funding"},
                "same_inst_policy": {"enabled": args.same_inst_policy != "off", "value": args.same_inst_policy},
            },
            "global_max_slots": args.global_max_slots, "global_daily_loss_u": args.global_daily_loss_u,
            "global_daily_loss_day": "Asia/Taipei (UTC+8) calendar day, realised net incl. fee and booked funding",
            "same_inst_policy": args.same_inst_policy, "leg_priority": args.leg_priority,
            "cross_leg_order": args.cross_leg_order, "leg_daily_loss_day": args.leg_daily_loss_day,
            "prereg_deviations": ([{"item": "per-leg daily loss day boundary", "prereg_v1_0": "UTC day", "this_run": "Asia/Taipei day",
                                    "status": "SEPARATE_SCENARIO_NOT_MAIN_COMPARISON (ChatGPT v1.20 #7235223075: main comparison uses utc)"}] if args.leg_daily_loss_day == "taipei" else []),
            "r2_naming": R2_ARM_NOTE,
            "adapter_verification": adapter_verification,
            "funding_inventory_supplied": bool(args.funding_inventory),
            "started_utc": started_utc,
        }
        print("COMBO_SCOPE:", json.dumps(scope, ensure_ascii=False), flush=True)
        if args.dry_check:
            print(json.dumps({"dry_check": "PASS", "files_verified": bound["files_verified"], "scope": scope,
                              "transport_hits": list(tb.hits) + list(guard.hits)}, ensure_ascii=False, indent=2), flush=True)
            return 0
        if not args.cache_dir or not args.funding_db or not args.out_dir:
            raise RuntimeError("--cache-dir, --funding-db and --out-dir are required unless --dry-check")

        cache_dir = Path(args.cache_dir).expanduser()
        src_db = Path(args.funding_db).expanduser()
        out_dir = Path(args.out_dir).expanduser()
        _require_fresh_out_dir(out_dir)

        derived_db = out_dir / DERIVED_DB_NAME
        derived_meta = out_dir / DERIVED_META_NAME
        scope_file = out_dir / SCOPE_NAME
        result_file = out_dir / RESULT_NAME
        details_file = out_dir / DETAILS_NAME
        outputs = [("derived_db", derived_db), ("derived_meta", derived_meta), ("derived_meta.tmp", Path(str(derived_meta) + ".tmp")),
                   ("scope", scope_file), ("scope.tmp", Path(str(scope_file) + ".tmp")),
                   ("result", result_file), ("result.tmp", Path(str(result_file) + ".tmp")),
                   ("details", details_file), ("details.tmp", Path(str(details_file) + ".tmp")),
                   ("engine_src", out_dir / ENGINE_SRC_NAME), ("engine_src.tmp", Path(str(out_dir / ENGINE_SRC_NAME) + ".tmp"))]

        cache_manifest_path = cache_dir / "manifest.json"
        if not cache_manifest_path.is_file():
            raise RuntimeError("cache manifest.json missing")
        inv_path = Path(args.funding_inventory).expanduser() if args.funding_inventory else None
        unc_path = Path(args.uncomputable_windows).expanduser() if args.uncomputable_windows else None
        input_manifest_path, input_manifest_entries = short_mod._load_optional_input_manifest(args.input_manifest)
        cache_manifest = json.loads(cache_manifest_path.read_text(encoding="utf-8"))
        symbols_dict = cache_manifest["symbols"]
        if requested_symbols:
            missing = [s for s in requested_symbols if s not in symbols_dict]
            if missing:
                raise RuntimeError("requested symbols missing from cache manifest: " + ", ".join(missing))
            ordered_syms = requested_symbols
        else:
            ordered_syms = [s for s in symbols_dict.keys() if s != "USDC-USDT-SWAP"]

        fixed_inputs = [("funding_db", src_db), ("manifest", manifest_path), ("retest24_script", retest_path),
                        ("shared_risk", shared_risk_path), ("cache_manifest", cache_manifest_path),
                        ("long_adapter", long_path), ("short_adapter", short_path), ("runner", Path(__file__).resolve())]
        if inv_path is not None:
            fixed_inputs.append(("funding_inventory", inv_path))
        if unc_path is not None:
            fixed_inputs.append(("uncomputable_windows", unc_path))
        if input_manifest_path is not None:
            fixed_inputs.append(("input_manifest", input_manifest_path))
        for rel, pth in bound["files"].items():
            fixed_inputs.append(("manifest entry " + rel, pth))
        for inst in ordered_syms:
            fixed_inputs.append(("symbol npz " + inst, (cache_dir / (inst + ".npz")).resolve()))
        short_mod._verify_output_paths_disjoint(outputs, fixed_inputs)
        npz_paths, npz_records = short_mod._verify_and_record_npz_inputs(ordered_syms, cache_dir, symbols_dict, input_manifest_entries)

        inv, inv_unc, inv_stats = (None, {}, None)
        if inv_path is not None:
            inv, inv_unc, inv_stats = load_funding_inventory(inv_path)
        funding_notes = {k: dict(v) for k, v in inv_unc.items()}
        unc = {}
        if unc_path is not None:
            for k, v in load_uncomputable_windows(unc_path, short_mod.parse_utc_ms).items():
                unc.setdefault(k, []).extend(v)
        sha_before = {lbl: sha(p) for lbl, p in (("funding_db", src_db), ("cache_manifest", cache_manifest_path))}
        if inv_path is not None:
            sha_before["funding_inventory"] = sha(inv_path)
        if unc_path is not None:
            sha_before["uncomputable_windows"] = sha(unc_path)

        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            short_mod._atomic_write_text(scope_file, json.dumps(scope, ensure_ascii=False, indent=2) + "\n")
            short_mod._bind_isolated_funding_db(src_db, derived_db, derived_meta)
            loaded = short_mod._load_runtime_modules(bound)
            combo_sim, combo_src_sha, combo_src = _build_combo_sim(loaded["b6_sim_portable"])
            engine_src_file = out_dir / ENGINE_SRC_NAME
            short_mod._atomic_write_text(engine_src_file, combo_src)
            if sha(engine_src_file) != combo_src_sha:
                raise RuntimeError("patched engine source file SHA differs from the executed source SHA")
            fmaps, ov_raw = short_mod.load_funding_db(derived_db)

            raw, bars_set = {}, set()
            for inst in ordered_syms:
                info = symbols_dict[inst]
                z = np.load(npz_paths[inst])
                if len(z["ts30"]) == 0 or len(z["ts4"]) == 0:
                    raise RuntimeError("empty timestamp array in symbol npz: " + inst)
                ts30, o30, ts4, o4, ts1, o1 = z["ts30"], z["ohlc30"], z["ts4"], z["ohlc4"], z["ts1"], z["ohlc1"]
                ema, rsi = short_mod.indicators_ema55_rsi14(o4[:, 3])
                for t in ts30.tolist():
                    if start_ts <= int(t) <= end_ts:
                        bars_set.add(int(t))
                raw[inst] = {
                    "ts4": ts4, "o4": o4, "ts4_map": {int(t): j for j, t in enumerate(ts4.tolist())},
                    "ema": ema, "rsi": rsi,
                    "d30": ({int(t): j for j, t in enumerate(ts30.tolist())}, o30),
                    "d1h": ({int(t): j for j, t in enumerate(ts1.tolist())}, o1),
                    "d1_set": set(int(x) for x in z["d1_ts"].tolist()),
                    "tickSz": float(info["spec"]["tickSz"]), "tickSz_str": str(info["spec"]["tickSz"]),
                    "maxLever": float(info["spec"].get("maxLever", 10.0)),
                    "fmap": fmaps.get(inst, {}),
                }
            bars = sorted(bars_set)
            if not bars:
                raise RuntimeError("no 30m bars inside the window")

            l_cands, l_lev, l_diag = long_mod.build_cands_long_struct_02_temporal_split(raw, ordered_syms, start_ts, end_ts)
            s_cands, s_lev, s_diag = short_mod.build_cands_retest24(raw, start_ts, end_ts, SHORT_CANDIDATE)
            max_lev = {}
            for inst in set(l_lev) | set(s_lev):
                vals = [v[inst] for v in (l_lev, s_lev) if inst in v]
                max_lev[inst] = min(vals)
            rank = {"long_first": (0, 1), "short_first": (1, 0)}[args.leg_priority]
            merged, contested_bars = {}, 0
            for li, cands in ((0, l_cands), (1, s_cands)):
                for bt, lst in cands.items():
                    # stable sort by the leg's own frozen key == the engine's own within-direction order
                    for ordinal, (sk, _li, inst, px, tr) in enumerate(sorted(lst, key=lambda x: x[0])):
                        key = (ordinal, rank[li], sk) if args.cross_leg_order == "rank_interleave" else (rank[li], sk)
                        merged.setdefault(int(bt), []).append((key, li, inst, px, tr))
            for bt, lst in merged.items():
                if len({x[1] for x in lst}) > 1:
                    contested_bars += 1

            ldef = long_mod.DEFAULT_EXIT_BY_CANDIDATE[LONG_CANDIDATE]
            lspec = long_mod.make_sim_spec(LONG_CANDIDATE, ldef["tp_pct"], ldef["sl_pct"], ldef["ttl_hours"], ldef["max_slots"], ldef["risk_per_trade"])
            arms, details = {}, {}
            leg_names = {0: LONG_CANDIDATE, 1: SHORT_CANDIDATE}
            for name in scen:
                sizing, fill = name.split("|")
                rid, risk_u, dloss_u = SHORT_SIZINGS[sizing]
                sspec = short_mod.make_retest24_spec(rid, risk_u, dloss_u)
                for k in COST_KEYS:
                    if float(lspec[k]) != float(sspec[k]):
                        raise RuntimeError("fair-cost mismatch between legs on " + k)
                spec = {k: lspec[k] for k in COST_KEYS}
                spec["legs"] = [dict(lspec["legs"][0]), dict(sspec["legs"][0])]
                sides = ["long" if lg["mode"] == "fib_long" else "short" for lg in spec["legs"]]
                if sides != ["long", "short"]:
                    raise RuntimeError("combo legs must be exactly [long, short]")
                ctrl = {"global_max_slots": args.global_max_slots, "global_daily_loss_u": args.global_daily_loss_u,
                        "same_inst_policy": args.same_inst_policy, "leg_sides": sides, "uncomputable": unc,
                        "leg_day_offset_ms": LEG_DAY_OFFSETS[args.leg_daily_loss_day]}
                r = combo_sim(raw, bars, spec, ov_raw_ts=ov_raw, cands_pre=merged, max_lev_pre=max_lev,
                              record_events=True, record_trades_detail=True, fill_mode="cross_1tick",
                              delay_first_bar=FILL_MODES[fill], combo=ctrl)
                trades_out, open_out, miss_out, flags = annotate_arm(r, leg_names, inv, unc, bars[-1], funding_notes)
                ol = r.get("_ord_log", [])
                gaps = []
                if miss_out:
                    gaps.append("missing_8h_funding_events_not_booked")
                if inv is None:
                    gaps.append("funding_inventory_not_supplied_completeness_unknown")
                if flags["funding_incomplete_or_unknown_trades"] or any(o["funding_status"] != "complete_by_batch_scope" for o in open_out if o["funding_status"] != "no_funding_interval"):
                    gaps.append("positions_held_in_months_not_complete_true")
                if flags["uncomputable_trades"]:
                    gaps.append("uncomputable_positions_present")
                if flags["funding_query_51001_note_positions"]:
                    gaps.append("positions_in_rest_51001_funding_months_rates_unknown")
                gaps.append("non_8h_funding_denominator_unknown")
                leg_ym = {0: short_mod._build_by_year_month([o for o in ol if o.get("leg") == 0], [t for t in r.get("_trades", []) if t["side"] == "long"], start_ts_ms=start_ts, end_ts_ms=end_ts),
                          1: short_mod._build_by_year_month([o for o in ol if o.get("leg") == 1], [t for t in r.get("_trades", []) if t["side"] == "short"], start_ts_ms=start_ts, end_ts_ms=end_ts)}
                monthly_combined = _monthly_combined(short_mod, ol, r.get("_trades", []), leg_ym, start_ts, end_ts)
                arms[name] = {
                    "monthly_combined": monthly_combined,
                    "status": "PRELIMINARY_INCOMPLETE_DATA" if len(gaps) > 1 else "PRELIMINARY_BATCH_SCOPE",
                    "performance_label": "初步／資料不完整；未入帳的未知資金費為條件情境，不是真實淨績效",
                    "short_sizing": sizing, "fill_mode": fill,
                    "short_sizing_note": (R2_ARM_NOTE if sizing == R2_SIZING_ARM else "R1 frozen sizing (150U / 600U)"),
                    "account": {"final_eq_u": r.get("final_eq_u"), "ret_eq_pct": r.get("ret_eq_pct"),
                                "mtm_mdd_pct": r.get("mtm_mdd_pct"), "cagr_eq_pct": r.get("cagr_eq_pct")},
                    "legs": {
                        "0_long": dict(_leg_stats([t for t in trades_out if t["leg"] == 0]),
                                       orders_placed=sum(1 for o in ol if o.get("leg") == 0),
                                       by_year_month=short_mod._build_by_year_month([o for o in ol if o.get("leg") == 0], [t for t in r.get("_trades", []) if t["side"] == "long"], start_ts_ms=start_ts, end_ts_ms=end_ts)),
                        "1_short": dict(_leg_stats([t for t in trades_out if t["leg"] == 1]),
                                        orders_placed=sum(1 for o in ol if o.get("leg") == 1),
                                        by_year_month=short_mod._build_by_year_month([o for o in ol if o.get("leg") == 1], [t for t in r.get("_trades", []) if t["side"] == "short"], start_ts_ms=start_ts, end_ts_ms=end_ts)),
                    },
                    "combo_gates": {k: v for k, v in (r.get("_combo") or {}).items() if k != "blocked_events"},
                    "open_at_end": len(open_out),
                    "funding": {"f_ev_real_8h": r.get("f_ev_real_8h"), "f_ev_real_non8h": r.get("f_ev_real_non8h"),
                                "miss_8h_events": len(miss_out), "booked_fund_u": r.get("real_fund_u"),
                                "missing_rates_policy": "UNKNOWN_NOT_BOOKED (no zero-fill, no interpolation, no symbol dropped)"},
                    "annotation_flags": flags,
                    "gaps": gaps,
                }
                details[name] = {"counts": {"closed_trades": len(trades_out), "open_at_end": len(open_out)},
                                 "closed_trades": trades_out, "open_at_end": open_out, "missing_funding_events_all": miss_out,
                                 "combo_blocked_events": (r.get("_combo") or {}).get("blocked_events", []),
                                 "order_log": ol}

            after = {lbl: sha(p) for lbl, p in (("funding_db", src_db), ("cache_manifest", cache_manifest_path))}
            if inv_path is not None:
                after["funding_inventory"] = sha(inv_path)
            if unc_path is not None:
                after["uncomputable_windows"] = sha(unc_path)
            if after != sha_before or sha(long_path) != long_sha_before or sha(short_path) != short_sha_before or sha(engine_src_file) != combo_src_sha:
                raise RuntimeError("fixed input modified during run")
            for inst, pth in npz_paths.items():
                if sha(pth) != npz_records[inst]["sha256"]:
                    raise RuntimeError("symbol npz modified during run: " + inst)

            controls_txt = describe_controls(args)
            finished_utc = datetime.now(TZ_UTC).isoformat()
            short_mod._atomic_write_text(details_file, json.dumps({
                "public_repo_policy": "LOCAL_OFFLINE_DETAIL_ONLY_DO_NOT_AUTO_PUSH_TO_PUBLIC_REPO",
                "study_id": STUDY_ID, "version": RUNNER_VERSION, "combo_id": COMBO_ID,
                "cutoff_utc": _iso(end_ts), "last_bar_30m_utc": _iso(bars[-1]),
                "uncomputable_windows": {k: v for k, v in sorted(unc.items())},
                "funding_query_51001_notes": {k: v for k, v in sorted(funding_notes.items())},
                "npz_files": npz_records, "scenarios": details,
            }, ensure_ascii=False, indent=2) + "\n")
            payload = {
                "status": "PRELIMINARY_INCOMPLETE_DATA" if any(a["status"] == "PRELIMINARY_INCOMPLETE_DATA" for a in arms.values()) else "PRELIMINARY_BATCH_SCOPE",
                "never_pass_note": "初步情境結果；不是完整驗收 PASS，不是實盤核准（live_approved: false）",
                "study_id": STUDY_ID, "version": RUNNER_VERSION, "combo_id": COMBO_ID,
                "started_utc": started_utc, "finished_utc": finished_utc, "elapsed_sec": round(time.time() - t0, 2),
                "transport_blocker_active_entire_run": True, "transport_hits": list(tb.hits),
                "scope": scope, "symbols_loaded": len(raw), "bars_30m_in_window": len(bars),
                "candidates": {"long": l_diag, "short": s_diag, "bars_with_both_legs_signalling": contested_bars},
                "funding_inventory_stats": inv_stats,
                "uncomputable_windows_count": sum(len(v) for v in unc.values()),
                "funding_query_51001_note_months": sum(len(v) for v in funding_notes.values()),
                "outer_offline_guard_active_entire_run": True, "outer_guard_hits": list(guard.hits),
                "combo_engine_patched_source_file": ENGINE_SRC_NAME,
                "combo_engine_patched_source_sha256": combo_src_sha,
                "historical_model_vs_delivered_script_diff": short_mod.HISTORICAL_MODEL_VS_DELIVERED_SCRIPT_DIFF,
                "combo_model_vs_live_shared_risk_diff": controls_txt["diff"],
                "sha256": dict(after, manifest=sha(manifest_path), retest24_script=sha(bound["roles"]["retest24_script"]),
                               shared_risk=sha(bound["roles"]["shared_risk"]), long_adapter=long_sha_before, short_adapter=short_sha_before,
                               runner=sha(Path(__file__).resolve()), combo_engine_source=combo_src_sha,
                               derived_funding_db=sha(derived_db), details=sha(details_file), combo_engine_source_file=sha(engine_src_file)),
                "local_details_file": DETAILS_NAME,
                "limitations": [
                    "缺歷史 BBO，post_only 可否掛入與排隊順位未知；cross_1tick 只是穿價下界",
                    *controls_txt["limitations"],
                    "delay1bar 為敏感度，不是真實延遲；歷史 MMR 以 1% 近似",
                    "缺資金費維持未知、未入帳；非 8H 結算應有分母未知；complete=true 只代表該批來源核對口徑",
                    "REST 51001（例如 RVN 2026-11）只代表該次資金費查詢未列出；母體保留、不擋進場，該月資金費維持未知並逐筆註記",
                    "只有必要價格確實缺且有證據（--uncomputable-windows 的 evidence）才列不可計算",
                    "候選映射、滑價對齊（原研究 0.0005 vs 目前 0.0003）、原 24 槽與隔離修正由 ChatGPT 原研究完成，不在本次範圍",
                ],
                "arms": arms,
            }
            short_mod._atomic_write_text(result_file, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            print("COMBO_RESULT_SHA256:", sha(result_file), flush=True)
            return 0
        except Exception:
            short_mod._discard_final_report(result_file, fixed_inputs)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
