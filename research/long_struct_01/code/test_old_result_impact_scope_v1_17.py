#!/usr/bin/env python3
"""Synthetic tests for old_result_impact_scope_v1_17.py (no market data, no replay)."""
import gzip
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("impact_under_test", str(HERE / "old_result_impact_scope_v1_17.py"))
mod = importlib.util.module_from_spec(_s)
_s.loader.exec_module(mod)
H8 = 28800000
T0 = 1709251200000


def _check(c, m):
    if not c:
        raise AssertionError("SYNTHETIC_TEST_FAIL: " + m)


def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rows = ["inst_id,ts_snapped_ms,funding_rate,is_8h_grid",
                "AAA-USDT-SWAP,%d,0.0001,true" % (T0 + H8),        # inside held AAA interval
                "AAA-USDT-SWAP,%d,0.0001,false" % (T0 + 10 * H8),  # after AAA exit
                "BBB-USDT-SWAP,%d,None,true" % (T0 + H8),           # rejected
                "CCC-USDT-SWAP,%d,inf,true" % (T0 + H8),            # rejected
                "DDD-USDT-SWAP,%d,0.0002,true" % (T0 + 2 * H8)]     # covers old miss event
        dp = td / "delta.csv.gz"
        with gzip.open(dp, "wt", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
        det = {"scenarios": {
            "hit": {"closed_trades": [{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0, "xts_ms": T0 + H8}], "open_at_end": []},
            "edge": {"closed_trades": [{"inst_id": "AAA-USDT-SWAP", "ets_ms": T0 + H8, "xts_ms": T0 + 2 * H8}], "open_at_end": []},
            "miss": {"closed_trades": [], "open_at_end": [], "missing_funding_events_all": [{"inst_id": "DDD-USDT-SWAP", "ts_ms": T0 + 2 * H8}]},
            "l1_style": {"trades_detail": [{"inst_id": "ZZZ-USDT-SWAP", "entry_ts_ms": T0, "exit_ts_ms": T0 + H8}]},
        }}
        detp = td / "old_details.json"
        detp.write_text(json.dumps(det), encoding="utf-8")
        out = td / "impact.json"
        _check(mod.main(["--details", str(detp), "--delta", str(dp), "--out", str(out)]) == 0, "rc")
        r = json.loads(out.read_text(encoding="utf-8"))
        a = r["assessments"]["old_details.json"]
        _check(r["delta_stats"] == {"valid_keys": 3, "rejected_non_finite_or_empty": 2, "conflicting_duplicates": 0}, "delta stats %r" % r["delta_stats"])
        _check(a["hit"]["verdict"] == "AFFECTED_PATH_MAY_CHANGE" and a["hit"]["delta_keys_in_held_8h"] == 1, "(ets, xts] includes exit bar")
        _check(a["edge"]["verdict"] == "NOT_AFFECTED_BY_THESE_DELTAS", "ets bar itself excluded")
        _check(a["miss"]["old_miss_8h_now_covered"] == 1 and a["miss"]["verdict"] == "AFFECTED_PATH_MAY_CHANGE", "miss covered")
        _check(a["l1_style"]["verdict"] == "UNDETERMINABLE" and "open_at_end_not_serialized" in a["l1_style"]["undeterminable_reasons"], "L1 open positions not serialized")
        try:
            mod.main(["--details", str(detp), "--delta", str(dp), "--out", str(out)])
            _check(False, "existing --out must be refused")
        except RuntimeError:
            pass
    print("ALL_IMPACT_SCOPE_SYNTHETIC_TESTS_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
