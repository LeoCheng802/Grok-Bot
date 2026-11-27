# BACKTEST-READINESS-01 v1.11-b2 r1 (D1)

Supersedes `research/funding_delta_v1_11_b2/` for the funding delta and
inventory classification only. Official monthly ZIPs and REST raw pages are
not duplicated here; they remain under
`../funding_delta_v1_11_b2/official_monthly_zips/` and
`../funding_delta_v1_11_b2/rest_2026_11/`.

## Defect D1

The v1.11-b2 delta included two new rows whose official `funding_rate` field
was the literal string `None` (not a numeric rate). They came from official
monthly ZIP CSVs, not from REST history.

A full scan of:

- every row in `funding_delta_v1_11_b2.csv.gz` (198,356 rows)
- every CSV inside all 1,279 official monthly ZIPs (174,957 rows)
- every REST history row (104,740 unfiltered; 39,037 in the 2026-11 window)

found **exactly two** non-numeric / empty / null rates, both `None`:

| inst_id | month_cst | funding_time_utc | source ZIP | zip SHA-256 |
|---|---|---|---|---|
| OL-USDT-SWAP | 2025-10 | 2025-10-24T08:00:00.000Z | `../funding_delta_v1_11_b2/official_monthly_zips/OL-USDT-SWAP-fundingrates-2025-10.zip` | `3e989693d34dee5c55d1fe0985056b021dc0b6378e9742a064270b86487e3d34` |
| ZK-USDT-SWAP | 2024-06 | 2024-06-06T08:00:00.000Z | `../funding_delta_v1_11_b2/official_monthly_zips/ZK-USDT-SWAP-fundingrates-2024-06.zip` | `989a6dcfa7d84b6a47cdaa3a2f07c51f71492a9987922a9edbe3fd2b66341925` |

Neither month was entirely null (OL 2025-10: 1 of 85 official rows; ZK 2024-06:
1 of 54). Numeric official rows from those months stay in the r1 delta.

## Fix

- The two rows were removed from the delta. They were not zero-filled or
  interpolated. They are listed in `funding_null_rate_rows_v1_11_b2_r1.csv`
  with flag `official_rate_null`, raw timestamps, the raw rate string, and
  the source ZIP path and SHA-256.
- The r1 delta was rebuilt from the saved official ZIPs and REST pages (no
  refetch) with non-numeric official rates excluded. New row count: **198,354**
  (8H 120,996 / non-8H 77,358). Matched existing keys are unchanged at
  15,638. Conflicts 0. Intra-official duplicates 0.
- Inventory r2 keeps class `covered_verified` for those two months and sets
  `sub_reason` to `official_rate_null` (they are not plain `covered_verified`).
- The public generator `build_delta_v1_11_b2_r1_public.py` now rejects
  non-numeric official rates into the flagged file.

## Unchanged gaps and limitations

- 5,883 `pending_check` months, including RVN-USDT-SWAP 2026-11 (official REST
  code 51001: instrument ID does not exist).
- 4 official ZIP 404s remain `official_unavailable` / `404_reason_unknown`
  (CC 2025-10, INJ 2023-11, MEGA 2026-04, ORDER 2025-09). Instruments
  `listTime` is evidence only and was not used to reclassify.
- REST evidence stores parsed JSON, not raw HTTP response bytes. r1 does not
  refetch; this limitation is documented only.
- `FIB-4H-LONG-V3` remains `NO-GO`. `live_approved` is false.
