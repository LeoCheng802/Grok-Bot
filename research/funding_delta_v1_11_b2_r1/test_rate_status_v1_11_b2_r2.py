#!/usr/bin/env python3
"""Synthetic tests for funding-rate rejection (v1.11-b2 r1 / v1.16 supplement).

Compares the published r1 rate_status (commit 08ff3d5: float(text) plus exact
lowercase 'nan') with the updated function that requires math.isfinite and is
case-insensitive. Official_rate_null and official_rate_nonfinite are distinct.

This file does not fetch, rebuild, or modify the official delta
(funding_delta_v1_11_b2_r1.csv.gz, 198,354 rows).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

CASES = [
    "",
    "None",
    "none",
    "NaN",
    "nan",
    "-nan",
    "+nan",
    "inf",
    "-inf",
    "Inf",
    "Infinity",
    "-Infinity",
    "1e-4",
    "-0.0001",
]


def rate_status_old_r1(value):
    """Published r1 classifier from commit 08ff3d5 (float() + exact lowercase 'nan')."""
    if value is None:
        return "python_none"
    text = str(value).strip()
    if text == "":
        return "empty"
    low = text.lower()
    if low == "none":
        return "literal_none"
    if low in {"null", "nan", "na", "n/a"}:
        return f"literal_{low}"
    try:
        float(text)
        return "numeric"
    except ValueError:
        return "non_numeric"


def load_new():
    path = Path(__file__).resolve().parent / "build_delta_v1_11_b2_r1_public.py"
    spec = importlib.util.spec_from_file_location("b2_r1_public", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    new = load_new()
    rows = []
    print("test_rate_status_v1_11_b2_r2")
    print("OLD = published r1 rate_status (08ff3d5): float(text) plus exact lowercase 'nan'")
    print("NEW = math.isfinite, case-insensitive; flags official_rate_null vs official_rate_nonfinite")
    print()
    header = f"{'token':<14} {'OLD_status':<16} {'OLD_accept':<11} {'NEW_status':<16} {'NEW_accept':<11} {'NEW_flag'}"
    print(header)
    print("-" * len(header))
    old_accepted_nonfinite = []
    new_accepted_bad = []
    new_rejected_good = []
    for token in CASES:
        old_s = rate_status_old_r1(token)
        new_s = new.rate_status(token)
        old_ok = old_s == "numeric"
        new_ok = new_s == "numeric"
        flag = "" if new_ok else new.reject_flag(new_s)
        label = repr(token)
        print(f"{label:<14} {old_s:<16} {str(old_ok):<11} {new_s:<16} {str(new_ok):<11} {flag}")
        rows.append(
            {
                "token": token,
                "old_status": old_s,
                "old_accepted_as_numeric": old_ok,
                "new_status": new_s,
                "new_accepted_as_numeric": new_ok,
                "new_flag": flag,
            }
        )
        finite_expected = token in {"1e-4", "-0.0001"}
        if (not finite_expected) and old_ok:
            old_accepted_nonfinite.append(token)
        if (not finite_expected) and new_ok:
            new_accepted_bad.append(token)
        if finite_expected and not new_ok:
            new_rejected_good.append(token)

    print()
    print("SUMMARY")
    print(f"OLD accepted as numeric (non-finite / null tokens that should be rejected): {old_accepted_nonfinite or 'none'}")
    print(f"NEW incorrectly accepted (should be 0): {new_accepted_bad or 'none'}")
    print(f"NEW incorrectly rejected finite rates (should be 0): {new_rejected_good or 'none'}")
    print(
        "OLD already rejected exact lowercase 'nan' / 'NaN' (via .lower()=='nan') and empty / None; "
        "it accepted inf / Infinity / +/-nan because float() succeeds and isfinite was not checked."
    )
    print(
        "NEW rejects empty and None with flag official_rate_null, and rejects "
        "NaN/Inf (any case, including +/-nan) with flag official_rate_nonfinite. "
        "Finite values 1e-4 and -0.0001 remain accepted."
    )
    ok = not new_accepted_bad and not new_rejected_good
    print("RESULT:", "PASS" if ok else "FAIL")
    # machine-readable copy printed last for the committed output file
    print()
    print("JSON")
    print(json.dumps({"cases": rows, "old_accepted_nonfinite": old_accepted_nonfinite, "pass": ok}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
