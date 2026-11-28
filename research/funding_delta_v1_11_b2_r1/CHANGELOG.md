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

## v1.16 follow-up (no refetch, delta unchanged)

Follow-up to the already-pushed r1 commit `08ff3d5bdb02c8b28ed0170d234bf1f02e8cc0ca`.
The r1 delta file is not rebuilt: 198,354 rows, SHA-256
`ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`.

### Rate rejection (including v1.16 supplement #7230544291)

The public generator now rejects any official rate that is empty, the literal
string `None`, `NaN`, `Inf`/`-Inf`, or otherwise non-finite / non-numeric.
Acceptance requires `float(text)` **and** `math.isfinite`, case-insensitive
(including `+nan`/`-nan`/`Infinity`).

Rejected rows go to `funding_null_rate_rows_v1_11_b2_r1.csv` with the source
ZIP name and SHA retained. Flags are distinct:

- `official_rate_null` — empty / literal `None` / null
- `official_rate_nonfinite` — NaN / Inf / -Inf (any case)

Affected months stay in their class but are marked incomplete
(`complete=false`) with the corresponding `sub_reason`.

Full rescan of the r1 delta, all 1,279 official ZIP CSVs, and all REST
chosen / realizedRate / fundingRate fields, using the new rules:

| reject_type | count | flag |
|---|---|---|
| literal_none | 2 | official_rate_null |
| empty | 0 | official_rate_null |
| nan | 0 | official_rate_nonfinite |
| inf / neg_inf | 0 | official_rate_nonfinite |
| other non-numeric | 0 | official_rate_null |

The two `literal_none` rows are unchanged (OL-USDT-SWAP 2025-10,
ZK-USDT-SWAP 2024-06). No official `NaN`/`Inf` rows exist in this batch, so no
month carries `official_rate_nonfinite`. Valid new count remains **198,354**.

Synthetic test `test_rate_status_v1_11_b2_r2.py` (output committed in
`test_rate_status_v1_11_b2_r2_output.txt`) compares the published r1
`rate_status` (08ff3d5) with the new function. OLD accepted as numeric:
`-nan`, `+nan`, `inf`, `-inf`, `Inf`, `Infinity`, `-Infinity`. OLD already
rejected `''`, `None`/`none`, and exact `nan`/`NaN`. NEW rejects all
non-finite tokens with `official_rate_nonfinite`, keeps empty/None as
`official_rate_null`, and still accepts `1e-4` and `-0.0001`. RESULT: PASS.

### REST evidence form

Stored REST content is parsed JSON, not original raw HTTP bytes:

- `evidence_form=parsed_json`
- `raw_bytes_saved=false`
- On reuse, `response_sha256` is SHA-256 of
  `json.dumps(parsed_object, separators=(',', ':'))`.
- The fetch evidence log hashed the HTTP body at request time; that body was
  then parsed and only the parsed object was saved. Raw bytes were discarded.

See `rest_evidence_form.json`. Verified REST was not refetched.

### RVN-USDT-SWAP 2026-11

Class stays `pending_check`. `sub_reason` is now
`rest_51001_instrument_not_listed` (was `rest_error`). The saved official
REST 51001 page is attached in `rvn_usdt_swap_2026_11_rest_51001_evidence.json`
(HTTP 200, code 51001, msg "Instrument ID, Instrument ID code, or Spread ID
doesn't exist."). Recheck once the official monthly ZIP for CST 2026-11 is
published. No zero-fill. RVN stays in the EX_USDC_286 universe.

Inventory r2 class counts are unchanged: covered_verified 1,364 (2 of them
incomplete with `official_rate_null`), covered_verified_rest 285,
pending_check 5,883 (including RVN), official_unavailable 4 all
`404_reason_unknown`.
