# BACKTEST-READINESS-01 v1.11-b3c (pending_check slice 3 of 3, final slice)

Official monthly ZIP fetch and key-compare for the third and final
deterministic slice of the original inventory r2 `pending_check` universe,
excluding RVN-USDT-SWAP 2026-11. Slice cuts are those recorded in the
v1.11-b3a manifest, rebuilt from inventory r2, and are not recomputed from
the remaining `pending_check` months in inventory r3 or r4.

Pending before this batch: **1,961** (`pending_check` = 1,960 remaining
slice months + RVN-USDT-SWAP 2026-11). The 4 `official_unavailable` /
`404_reason_unknown` months are listed separately and are not included in
this 1,961.

This batch uses the same public-generator rules as v1.11-b3b (`load_existing`
dedupe/conflict census; `complete=true` only if the month has zero conflicts
of any kind). The compare baseline adds the v1.11-b3b delta (1,084 rows,
SHA-256 `f7b139a597e0257283a1c32dd632d6ef39a5822c15a03c929d1d433b53b66b9e`).

Prior deltas were not rebuilt. Already-verified official ZIPs (5,286
`covered_verified`) were not refetched. Only keys verified as actual official
settlement records are added. Conflicts never overwrite. Non-finite /
non-numeric official rates are flagged, never zero-filled. The universe and
window are unchanged.

Self-run scans and tests in this batch are team execution evidence, not
ChatGPT runtime certification.

## Slice definition (pinned to b3a / inventory r2)

Universe: inventory r2 class `pending_check` excluding RVN-USDT-SWAP 2026-11
(5,882 months), sorted by `(inst_id, month_cst)`.
`base, rem = divmod(5882, 3)` → sizes **1,961 / 1,961 / 1,960**.

| slice | index range | count | first | last |
|---|---|---|---|---|
| 1 | [0, 1961) | 1,961 | 0G-USDT-SWAP 2025-12 | ETHFI-USDT-SWAP 2026-06 |
| 2 | [1961, 3922) | 1,961 | ETHFI-USDT-SWAP 2026-07 | PENDLE-USDT-SWAP 2026-01 |
| 3 (this batch) | [3922, 5882) | 1,960 | PENDLE-USDT-SWAP 2026-02 | ZRX-USDT-SWAP 2026-08 |

## Baseline census

Rows by source: frozen 829,157; v1.7 6,748; v1.9 174; v1.10 10,633;
v1.11_b1 609; v1.11_b2_r1 198,354; v1.11_b3a 918; v1.11_b3b 1,084
(sum 1,047,677).

- unique keys: 1,047,677
- clean keys: 1,047,677
- identical multi-source keys deduped: 0 (extra occurrences 0)
- existing-input conflict keys: 0 (affected months 0)

Every baseline key appears in exactly one source.

## Fetch (slice 3 only)

- Fetched: 1,960
- HTTP 200: 1,960 (raw ZIPs saved under `official_monthly_zips/`)
- HTTP 404: 0
- HTTP other: 0
- Skipped already-verified: 0
- Official numeric rows: 260,643 (unique keys 260,643; official-ZIP-internal
  conflicts 0; official identical dups deduped 0)
- Flagged official rates: 0 (literal_none 0, empty 0, nan 0, inf/neg_inf 0,
  other non-numeric 0; official_rate_null 0, official_rate_nonfinite 0)
- Evidence: `fetch_evidence_v1_11_b3c.jsonl` (`evidence_form=raw_zip`,
  `raw_bytes_saved=true` for all 1,960 HTTP 200)

## Compare

Existing keys: frozen DB + v1.7 + v1.9 + v1.10 + v1.11_b1 + v1.11_b2_r1 +
v1.11_b3a + v1.11_b3b, keyed by `(inst_id, snap to nearest hour)`. Conflicts
never overwrite. Only keys verified as actual official settlement records
are added.

- Matched: 258,781
- New: **1,862** (8H 934 / non-8H 928)
- Conflicts: official-vs-existing 0; existing-input-internal 0;
  official-ZIP-internal 0

All 1,960 slice-3 months already had `existing_rows>0` in inventory r4
(range 16–726), so most official ZIP keys were already present; only 1,862
keys were unrecorded.

## Inventory r5 (full, 7,536 rows)

`complete=true` means the month passed per this batch's source and
comparison scope only: an official monthly ZIP was obtained, all of its
finite-numeric official keys were key-compared against existing settlements,
and the month has zero conflicts of any kind (official-vs-existing,
existing-input-internal, official-ZIP-internal). It is not a full-period or
cross-frequency verification. `complete=false` means this batch's official
ZIP contained at least one flagged non-numeric or non-finite rate (known
incomplete). `blank` = unknown. Only `true` means complete (within that
limited scope).

r4 `complete=true` months that flip under the conflict rule: **0**.

- class: covered_verified 7,246; covered_verified_rest 285; pending_check 1; official_unavailable 4
- complete: true 7,529; false 2; blank 5
- complete=true 7,529 = 7,244 covered_verified (prior 5,284 + this batch's 1,960) + 285 covered_verified_rest
- complete=false 2 = OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06 (prior `official_rate_null`; ZIP official rows were 1/85 and 1/54 literal `None`)
- pending_check 1 = RVN-USDT-SWAP 2026-11 (`rest_51001_instrument_not_listed`)
- official_unavailable 4, all `404_reason_unknown` (CC 2025-10, INJ 2023-11, MEGA 2026-04, ORDER 2025-09); complete blank
- blank 5 = pending_check 1 + official_unavailable 4

The 1,960 newly classified `covered_verified` months are exactly this
slice: PENDLE-USDT-SWAP 2026-02 … ZRX-USDT-SWAP 2026-08, all
`complete=true`.

## Cumulative summary (v1.11-b1 + b2_r1 + b3a + b3b + b3c)

New official keys added by these deltas, counted from the delta files:

| batch | new rows | 8H | non-8H |
|---|---:|---:|---:|
| v1.11-b1 | 609 | 396 | 213 |
| v1.11-b2 r1 | 198,354 | 120,996 | 77,358 |
| v1.11-b3a | 918 | 469 | 449 |
| v1.11-b3b | 1,084 | 542 | 542 |
| v1.11-b3c | 1,862 | 934 | 928 |
| **total** | **202,827** | **123,337** | **79,490** |

Conflicts across these five batches: official-vs-existing 0;
existing-input-internal 0; official-ZIP-internal 0. (The two official
literal-`None` ZIP rows found in b2 are flagged `official_rate_null`, not
conflicts, and remain in inventory as complete=false.)

Inventory r5 class and complete counts are the post-b3c totals above.

## Remaining / still unknown

The three official monthly-ZIP slices of the original 5,882-month universe
are finished. What remains unknown or incomplete:

- OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06: one official literal `None`
  rate each (1/85 and 1/54); `complete=false` / `official_rate_null`. Not
  zero-filled.
- RVN-USDT-SWAP 2026-11 stays `pending_check` /
  `rest_51001_instrument_not_listed`. Recheck when the CST 2026-11 official
  monthly ZIP is published. It stays in the universe; no zero-fill.
- 4 official ZIP 404s remain `official_unavailable` / `404_reason_unknown`
  (CC 2025-10, INJ 2023-11, MEGA 2026-04, ORDER 2025-09).
- The full-period non-8H settlement denominator (expected settlement count
  per month for 1H/4H instruments) is not yet established. `complete=true`
  in this inventory is not a full-period or cross-frequency verification.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

Run UTC: 2026-11-28T00:47:26Z – 2026-11-28T00:58:48Z.
