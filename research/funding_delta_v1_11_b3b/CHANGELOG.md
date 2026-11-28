# BACKTEST-READINESS-01 v1.11-b3b (pending_check slice 2 of 3 + generator fixes)

Official monthly ZIP fetch and key-compare for the second deterministic slice
of the original inventory r2 `pending_check` universe, excluding
RVN-USDT-SWAP 2026-11. Slice cuts are those recorded in the v1.11-b3a
manifest, rebuilt from inventory r2, and are not recomputed from the
remaining `pending_check` months in inventory r3.

Pending before this batch: **3,922** (`pending_check` = 3,921 remaining
slice months + RVN-USDT-SWAP 2026-11). The 4 `official_unavailable` /
`404_reason_unknown` months are listed separately and are not included in
this 3,922.

Prior deltas were not rebuilt (including v1.11-b2 r1 198,354 rows, SHA-256
`ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`, and
v1.11-b3a 918 rows, SHA-256
`0950a0d28966560a84b49a896e418f86ea2af8e866f61f6a15a9d321568cbaab`).
Already-verified official ZIPs (3,325 `covered_verified`) were not
refetched. Only keys verified as actual official settlement records are
added. Conflicts never overwrite. Non-finite/non-numeric official rates are
flagged, never zero-filled.

Self-run scans and tests in this batch are team execution evidence, not
ChatGPT runtime certification.

## Generator fixes (ChatGPT v1.17)

1. `load_existing`: when multiple existing inputs share a key, the first
   value is no longer kept silently. Same key + same rate and `ts_raw` is
   deduped and counted. Same key + different rate or `ts_raw` keeps both
   sides' evidence (source, rate, `ts_raw`) and is listed as an
   existing-input conflict with the affected months. The census covers the
   full baseline: frozen + v1.7 / v1.9 / v1.10 / v1.11_b1 / v1.11_b2_r1 /
   v1.11_b3a.
2. `write_inventory`: `complete=true` only if the month has zero conflicts
   of any kind (official-vs-existing, existing-input-internal,
   official-ZIP-internal same key different value). Official-ZIP-internal
   conflicts are saved with both rows, listed by month. If any r3
   `complete=true` month flips under this rule, r4 records it with an
   explanation.

## Slice definition (pinned to b3a / inventory r2)

Universe: inventory r2 class `pending_check` excluding RVN-USDT-SWAP 2026-11
(5,882 months), sorted by `(inst_id, month_cst)`.
`base, rem = divmod(5882, 3)` → sizes **1,961 / 1,961 / 1,960**.

| slice | index range | count | first | last |
|---|---|---|---|---|
| 1 | [0, 1961) | 1,961 | 0G-USDT-SWAP 2025-12 | ETHFI-USDT-SWAP 2026-06 |
| 2 (this batch) | [1961, 3922) | 1,961 | ETHFI-USDT-SWAP 2026-07 | PENDLE-USDT-SWAP 2026-01 |
| 3 | [3922, 5882) | 1,960 | PENDLE-USDT-SWAP 2026-02 | ZRX-USDT-SWAP 2026-08 |

## Baseline census (generator fix 1)

Rows by source: frozen 829,157; v1.7 6,748; v1.9 174; v1.10 10,633;
v1.11_b1 609; v1.11_b2_r1 198,354; v1.11_b3a 918 (sum 1,046,593).

- unique keys: 1,046,593
- clean keys (single occurrence or identical multi-source deduped): 1,046,593
- identical multi-source keys deduped: 0 (extra occurrences 0)
- existing-input conflict keys: 0 (affected months 0)

Every baseline key appears in exactly one source; the previous first-wins
behaviour would not have discarded a second value on this baseline.

## Fetch (slice 2 only)

- Fetched: 1,961
- HTTP 200: 1,961 (raw ZIPs saved under `official_monthly_zips/`)
- HTTP 404: 0
- HTTP other: 0
- Skipped already-verified: 0
- Official numeric rows: 261,822 (unique keys 261,822; official-ZIP-internal
  conflicts 0; official identical dups deduped 0)
- Flagged official rates: 0 (literal_none 0, empty 0, nan 0, inf/neg_inf 0,
  other non-numeric 0; official_rate_null 0, official_rate_nonfinite 0)
- Evidence: `fetch_evidence_v1_11_b3b.jsonl` (`evidence_form=raw_zip`,
  `raw_bytes_saved=true` for all 1,961 HTTP 200)

## Compare

Existing keys: frozen DB + v1.7 + v1.9 + v1.10 + v1.11_b1 + v1.11_b2_r1 +
v1.11_b3a, keyed by `(inst_id, snap to nearest hour)`. Conflicts never
overwrite. Only keys verified as actual official settlement records are
added.

- Matched: 260,738
- New: **1,084** (8H 542 / non-8H 542)
- Conflicts: official-vs-existing 0; existing-input-internal 0;
  official-ZIP-internal 0

All 1,961 slice-2 months already had `existing_rows>0` in inventory r3
(range 37–720), so most official ZIP keys were already present; only 1,084
keys were unrecorded.

## Inventory r4 (full, 7,536 rows)

`complete=true` means the month passed per this batch's source and
comparison scope only: an official monthly ZIP was obtained, all of its
finite-numeric official keys were key-compared against existing settlements,
and the month has zero conflicts of any kind (official-vs-existing,
existing-input-internal, official-ZIP-internal). It is not a full-period or
cross-frequency verification. `complete=false` means this batch's official
ZIP contained at least one flagged non-numeric or non-finite rate (known
incomplete). `blank` = unknown. Only `true` means complete (within that
limited scope).

r3 `complete=true` months that flip under the tighter conflict rule: **0**.
No r4 class or complete value was changed for a prior r3 `complete=true`
month.

- class: covered_verified 5,286; covered_verified_rest 285; pending_check 1,961; official_unavailable 4
- complete: true 5,569; false 2; blank 1,965
- complete=true 5,569 = 5,284 covered_verified (prior 3,323 + this batch's 1,961) + 285 covered_verified_rest
- complete=false 2 = OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06 (prior `official_rate_null`; ZIP official rows were 1/85 and 1/54 literal `None`)
- pending_check 1,961 = slice 3 (1,960) + RVN-USDT-SWAP 2026-11 (`rest_51001_instrument_not_listed`)
- official_unavailable 4, all `404_reason_unknown` (CC 2025-10, INJ 2023-11, MEGA 2026-04, ORDER 2025-09); complete blank
- blank 1,965 = pending_check 1,961 + official_unavailable 4

The 1,961 newly classified `covered_verified` months are exactly this
slice: ETHFI-USDT-SWAP 2026-07 … PENDLE-USDT-SWAP 2026-01, all
`complete=true`.

## Limits

- Remaining pending_check: 1,961 = slice 3 (1,960) + RVN-USDT-SWAP 2026-11
- 4 prior official ZIP 404s remain `404_reason_unknown` and are listed
  separately
- FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

Run UTC: 2026-11-28T00:30:43Z – 2026-11-28T00:41:42Z.
