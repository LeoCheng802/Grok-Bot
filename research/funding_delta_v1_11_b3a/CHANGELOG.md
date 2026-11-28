# BACKTEST-READINESS-01 v1.11-b3a (pending_check slice 1 of 3)

Official monthly ZIP fetch and key-compare for the first deterministic slice
of inventory r2 `pending_check` months, excluding RVN-USDT-SWAP 2026-11.
The v1.11-b2 r1 delta (198,354 rows, SHA-256
`ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`) was not
rebuilt. Already-verified official ZIPs (1,364 `covered_verified`) were not
refetched.

Self-run scans in this batch are team execution evidence, not ChatGPT runtime
certification.

## Slice definition

Universe: inventory r2 class `pending_check` excluding RVN-USDT-SWAP 2026-11
(5,882 months), sorted by `(inst_id, month_cst)`.
`base, rem = divmod(5882, 3)` → sizes **1,961 / 1,961 / 1,960**.

| slice | index range | count | first | last |
|---|---|---|---|---|
| 1 (this batch) | [0, 1961) | 1,961 | 0G-USDT-SWAP 2025-12 | ETHFI-USDT-SWAP 2026-06 |
| 2 | [1961, 3922) | 1,961 | ETHFI-USDT-SWAP 2026-07 | PENDLE-USDT-SWAP 2026-01 |
| 3 | [3922, 5882) | 1,960 | PENDLE-USDT-SWAP 2026-02 | ZRX-USDT-SWAP 2026-08 |

## Fetch (slice 1 only)

- Fetched: 1,961
- HTTP 200: 1,961 (raw ZIPs saved under `official_monthly_zips/`)
- HTTP 404: 0
- HTTP other: 0
- Skipped already-verified: 0
- Official numeric rows: 232,095 (unique keys 232,095; intra-official dups 0)
- Flagged official rates: 0 (literal_none 0, empty 0, nan 0, inf/neg_inf 0, other non-numeric 0)
- Evidence: `fetch_evidence_v1_11_b3a.jsonl` (`evidence_form=raw_zip`, `raw_bytes_saved=true` for HTTP 200)

## Compare

Existing keys: frozen DB + v1.7 + v1.9 + v1.10 + v1.11_b1 + v1.11_b2_r1,
keyed by `(inst_id, snap to nearest hour)`. Conflicts never overwrite.

- Matched: 231,177
- New: **918** (8H 469 / non-8H 449)
- Conflicts: 0

All 1,961 slice-1 months already had `existing_rows>0` in inventory r2, so
most official ZIP keys were already present; only 918 keys were unrecorded.

## Inventory r3 (full, 7,536 rows)

`complete=true` means the month passed per this batch's source and comparison
scope only: an official monthly ZIP was obtained and all of its finite-numeric
official keys were key-compared. It is not a full-period or cross-frequency
verification. `complete=false` means this batch's official ZIP contained at
least one flagged non-numeric or non-finite rate (known incomplete).
`blank` = unknown. Only `true` means complete (within that limited scope).

- class: covered_verified 3,325; covered_verified_rest 285; pending_check 3,922; official_unavailable 4
- complete: true 3,608; false 2; blank 3,926
- complete=true 3,608 = 3,323 covered_verified (prior 1,362 + this batch's 1,961) + 285 covered_verified_rest
- complete=false 2 = OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06 (prior r2 `official_rate_null`; ZIP official rows were 1/85 and 1/54 literal `None`, not 2/85)
- pending_check 3,922 = slice 2 (1,961) + slice 3 (1,960) + RVN-USDT-SWAP 2026-11 (`rest_51001_instrument_not_listed`)
- official_unavailable 4, all `404_reason_unknown` (CC 2025-10, INJ 2023-11, MEGA 2026-04, ORDER 2025-09); complete blank

## Limits

- Remaining pending_check: 3,922, including RVN-USDT-SWAP 2026-11 and slices 2 and 3
- 4 prior official ZIP 404s remain `404_reason_unknown`
- FIB-4H-LONG-V3 remains NO-GO. live_approved is false.
