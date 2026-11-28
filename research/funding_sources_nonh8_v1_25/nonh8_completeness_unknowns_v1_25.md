# Non-8H completeness unknowns (v1.25 correction of v1.23)

This is a new versioned file. The v1.23 files are kept unchanged. Offline only,
from already-saved official monthly ZIPs and 2026-11 REST parsed-JSON files; no
refetch, no backtest, no zero-fill, no interpolation, no change to any rate.

**No official settlement-schedule source has been used.** Every interval and every
expected-count denominator here is inferred from observed timestamps and is not
officially verified. `official_schedule_status` is
`unknown_no_official_schedule_source_used` on every row.

## Correction 1: 2H and other non-1H/4H/8H intervals

v1.23 `analyze_month` recognised only 1H/4H/8H. A month with a single constant
observed 2H interval fell into the fallback branch, which chose the smallest
divisible base (1H), labelled the month `not_determinable_internal_gaps` and wrote
`inferred_interval=1H`. A 2H grid is *consistent with* a 1H grid with missing slots,
but that does not mean 1H slots should exist and are missing. v1.25 keeps the observed
interval and leaves the official schedule unknown.

- v1.25 rule: a single constant observed gap of any whole-hour size is kept as the
  observed interval. If it is not 1H/4H/8H and spans the full CST month, the status is
  `inferred_constant_full_month_nonstandard_interval` (inferred only, not official).
- `inferred_interval` is assigned only when a single constant observed gap exists; v1.23
  wrote `1H` for non-constant months, which was not an observation. v1.25 leaves it blank.
- `interval_change_visible` means a gap-size change observed in the saved data only. It is
  not proof of an official interval change.
- Statuses of all other months are unchanged from v1.23.

### Non-8H months by denominator status (before / after)

| denominator_status | v1.23 | v1.25 |
| --- | --- | --- |
| inferred_constant_full_month | 2499 | 2499 |
| inferred_constant_full_month_nonstandard_interval | 0 | 7 |
| not_determinable_insufficient_points | 2 | 2 |
| not_determinable_internal_gaps | 8 | 0 |
| not_determinable_interval_change | 99 | 99 |
| not_determinable_interval_change_or_gaps | 195 | 195 |
| not_determinable_span_shorter_than_month | 121 | 122 |
| not_determinable_window_truncated | 198 | 198 |

### Non-8H months by inferred_interval (before / after)

| inferred_interval | v1.23 | v1.25 |
| --- | --- | --- |
| 1H | 207 | 4 |
| 2H | 0 | 8 |
| 4H | 2814 | 2814 |
| (blank) | 101 | 296 |

Changed rows vs v1.23: 204 (field changes: {'inferred_interval': 204, 'denominator_status': 8, 'inferred_expected_count': 7}).
Rows with changes outside denominator_status / inferred_interval / inferred_expected_count:
0. Boundary snap-count mismatches vs v1.23 `boundary_crossing_settlement_count`:
0. See `nonh8_v1_25_vs_v1_23_changed_rows.csv`.

### Months whose observed gaps include a non-1H/4H/8H value

Count: 125 of 3122 non-8H months (observed gap hours outside 1,4,8).

| key | count |
| --- | --- |
| 2 | 124 |
| 132 | 1 |

By v1.25 status:

| key | count |
| --- | --- |
| not_determinable_interval_change_or_gaps | 117 |
| inferred_constant_full_month_nonstandard_interval | 7 |
| not_determinable_span_shorter_than_month | 1 |

Only the 8 constant-2H months changed status; the other nonstandard-gap months keep their
v1.23 status (they have more than one gap size, so they remain not determinable).
The 2H gaps in mixed months and the single 132H gap (OL 2025-10) are observed gaps only;
whether they reflect an official interval, an interval change, or missing rows is unknown.

### The eight months (before / after)

| inst_id | month_cst | observed_settlements | before_denominator_status | before_inferred_interval | after_observed_intervals | after_denominator_status | after_inferred_interval | after_inferred_expected_count | after_official_schedule_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API3-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used |
| AUCTION-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used |
| KAITO-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used |
| LAYER-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used |
| LAYER-USDT-SWAP | 2025-03 | 372 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown_no_official_schedule_source_used |
| BARD-USDT-SWAP | 2025-09 | 144 | not_determinable_internal_gaps | 1H | 2H | not_determinable_span_shorter_than_month | 2H |  | unknown_no_official_schedule_source_used |
| SOPH-USDT-SWAP | 2025-08 | 372 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown_no_official_schedule_source_used |
| SYRUP-USDT-SWAP | 2025-08 | 372 | not_determinable_internal_gaps | 1H | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown_no_official_schedule_source_used |

## Correction 2: time basis (raw vs snap)

v1.23 `snap()` rounded each raw funding time to the nearest hour with no tolerance, then
de-duplicated, then assigned CST months and counted crossings. The v1.23 count of 6,109
is therefore a count over the post-snap, de-duplicated time set (snap basis). It is not a
raw-timestamp-by-raw-timestamp certification.

v1.25 records both bases from the saved raw values (ZIP `funding_time`, REST `fundingTime`):

- snap basis (v1.23 definition): 6,109 crossings over the 3,122 non-8H months
  (all months with a saved file: 10,387).
- raw basis (raw ts kept inside the window and inside the CST month, de-duplicated on raw ts):
  6,109 crossings over the same non-8H months (all months with a saved file: 10,387).
- Non-8H months where raw and snap crossing counts differ: 0.
- Rows parsed: 1,046,023 (ZIP 941,283 + REST 104,740); finite-rate
  rows 1,046,021; 2 ZIP rows have a null/None rate and are excluded. Rows with a non-zero raw-vs-snapped offset:
  95,471; maximum absolute offset: 45,000 ms.
  Offset buckets: {'0': 950550, '10-59s': 22105, '1-9s': 73366}.
- Raw vs snapped timestamp in a different CST month: 0; in a
  different UTC month: 0.
- Snap collisions (several raw rows mapping to the same snapped key within one file): keys
  0 (same raw time duplicated 0,
  distinct raw times 0); same snapped key with different
  rates: 0.
- Cross-file same snapped key: 65703 by source pair
  {'rest-zip': 65703}; with different rates: 0
  (by pair {}). The saved 2026-11 REST files also
  carry earlier history outside CST 2026-11 (rows excluded from the month sets: {'rest:earlier_cst_month': 65703, 'zip:before_window': 70}),
  which repeats keys present in the official monthly ZIPs; those overlaps are listed here as evidence and are not
  used to add or change any value.
- Months with no saved raw timestamps (listed as unknown, not estimated): 4
  (the four 404 months). RVN-USDT-SWAP 2026-11 has a saved REST 51001 response with zero data rows.

This evidence covers the finite-rate rows of the saved ZIP/REST files only. See
`time_basis_evidence_v1_25.json`.

## What was NOT verified

- Same-key-different-rate across sources and snap collisions were checked only inside the saved
  ZIP/REST files as reported above (including cross-file within the saved ZIPs). They were not
  re-checked against the frozen DB, v1.7, v1.9 or the other deltas here; those comparisons remain
  the per-batch evidence (conflicts 0 in the b3b/b3c manifests and earlier batch manifests) and
  are not re-verified in this compilation.
- The ZIP/REST SHA-256 listings are navigation aids. They are not per-file acceptance against the
  expected manifests, and nothing here claims full-rate completeness.
- Frozen DB SHA `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc` only matches the
  references in the b3b/b3c manifests. Equal row counts (829,157) do not mean the file is
  identical to any other version.
- No official settlement-schedule source was used, so no interval and no denominator is official.
- Inventory `complete=true` is passed per that batch's source and comparison scope only, not a
  full-period or cross-frequency verification.

Self-run checks are team execution evidence, not ChatGPT runtime certification.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

## Known gaps (unchanged)

- OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06: official_rate_null (1/85 and 1/54 literal `None`).
- RVN-USDT-SWAP 2026-11: pending_check / rest_51001_instrument_not_listed.
- CC-USDT-SWAP 2025-10, INJ-USDT-SWAP 2023-11, MEGA-USDT-SWAP 2026-04, ORDER-USDT-SWAP 2025-09:
  official_unavailable / 404_reason_unknown.

| record_kind | inst_id | month_cst | observed_intervals | nonstandard_gap_hours | observed_settlement_count | denominator_status | inferred_interval | inferred_expected_count | official_schedule_status | boundary_crossing_snap_count | boundary_crossing_raw_count | snap_collision_keys | partial_month | cst_vs_utc_completeness_may_differ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| known_gap_404 | CC-USDT-SWAP | 2025-10 |  |  | 0 | not_determinable_no_numeric_settlements |  |  | unknown_no_official_schedule_source_used | 0 | unknown | unknown | false | true |
| known_gap_404 | INJ-USDT-SWAP | 2023-11 |  |  | 0 | not_determinable_no_numeric_settlements |  |  | unknown_no_official_schedule_source_used | 0 | unknown | unknown | false | true |
| known_gap_404 | MEGA-USDT-SWAP | 2026-04 |  |  | 0 | not_determinable_no_numeric_settlements |  |  | unknown_no_official_schedule_source_used | 0 | unknown | unknown | false | true |
| known_gap_404 | ORDER-USDT-SWAP | 2025-09 |  |  | 0 | not_determinable_no_numeric_settlements |  |  | unknown_no_official_schedule_source_used | 0 | unknown | unknown | false | true |
| known_gap_pending | RVN-USDT-SWAP | 2026-11 |  |  | 0 | not_determinable_no_numeric_settlements |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | true | true |
| known_gap_official_rate_null | ZK-USDT-SWAP | 2024-06 | 8H+304H | 304 | 53 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |

## All non-8H inst/month rows

| record_kind | inst_id | month_cst | observed_intervals | nonstandard_gap_hours | observed_settlement_count | denominator_status | inferred_interval | inferred_expected_count | official_schedule_status | boundary_crossing_snap_count | boundary_crossing_raw_count | snap_collision_keys | partial_month | cst_vs_utc_completeness_may_differ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| non8h_month | 0G-USDT-SWAP | 2025-09 | 4H+2H | 2 | 97 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2025-10 | 1H+4H+2H | 2 | 433 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2025-11 | 1H+4H |  | 600 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2025-12 | 4H+1H |  | 282 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-01 | 1H+4H |  | 456 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-02 | 1H+4H |  | 408 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 0G-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | 2Z-USDT-SWAP | 2025-10 | 4H |  | 174 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | 2Z-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | A-USDT-SWAP | 2025-05 | 4H |  | 13 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | A-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ACH-USDT-SWAP | 2025-01 | 8H+4H |  | 104 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACH-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ACT-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-06 | 1H+4H+2H | 2 | 191 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ACU-USDT-SWAP | 2026-01 | 4H |  | 50 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ACU-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AEON-USDT-SWAP | 2026-07 | 4H |  | 25 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AEON-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEON-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEON-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEON-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AERO-USDT-SWAP | 2025-07 | 4H |  | 170 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AERO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AEVO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AEVO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AGLD-USDT-SWAP | 2026-06 | 8H+4H |  | 99 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | AGLD-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AGLD-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AGLD-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AGLD-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AGLD-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AI-USDT-SWAP | 2026-04 | 4H |  | 6 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-06 | 4H+2H | 2 | 182 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-07 | 4H+2H | 2 | 192 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-01 | 4H |  | 170 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AIXBT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AKE-USDT-SWAP | 2026-09 | 1H+4H+2H | 2 | 103 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AKE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AKE-USDT-SWAP | 2026-11 | 4H+2H | 2 | 160 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ALLO-USDT-SWAP | 2025-11 | 4H |  | 113 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ALLO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ANIME-USDT-SWAP | 2025-01 | 4H |  | 48 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2025-12 | 1H+4H |  | 243 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-03 | 1H+4H |  | 429 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-10 | 4H+2H | 2 | 191 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ANIME-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | API3-USDT-SWAP | 2025-03 | 4H+8H+2H | 2 | 207 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-04 | 2H | 2 | 360 | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-05 | 4H+2H | 2 | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-08 | 4H+2H | 2 | 259 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-09 | 4H+2H | 2 | 276 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | API3-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | APR-USDT-SWAP | 2025-10 | 4H |  | 44 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | APR-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ARX-USDT-SWAP | 2026-06 | 4H |  | 48 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ARX-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ARX-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ARX-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ARX-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ARX-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ASTER-USDT-SWAP | 2025-09 | 4H |  | 50 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ASTER-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AT-USDT-SWAP | 2025-10 | 4H |  | 7 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ATH-USDT-SWAP | 2026-02 | 8H+1H |  | 105 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-03 | 1H+4H |  | 726 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ATH-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AUCTION-USDT-SWAP | 2024-07 | 8H+4H |  | 112 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2024-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2024-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-03 | 4H+2H | 2 | 240 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-04 | 2H | 2 | 360 | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-05 | 4H+2H | 2 | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-01 | 1H+4H |  | 258 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AUCTION-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AVAX-USDT-SWAP | 2025-10 | 1H+8H |  | 170 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2025-09 | 4H |  | 48 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2025-10 | 4H+1H |  | 348 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2025-11 | 1H+4H |  | 252 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-01 | 1H+4H |  | 264 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AVNT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AXIS-USDT-SWAP | 2026-10 | 1H+4H+2H | 2 | 105 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AXIS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AXS-USDT-SWAP | 2026-01 | 1H+4H+8H |  | 351 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AXS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-02 | 1H+4H |  | 199 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | AZTEC-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BABY-USDT-SWAP | 2025-04 | 4H |  | 121 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-03 | 1H+4H |  | 579 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-06 | 1H+4H+2H | 2 | 197 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BABY-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BARD-USDT-SWAP | 2025-09 | 2H | 2 | 144 | not_determinable_span_shorter_than_month | 2H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2025-10 | 4H+2H | 2 | 312 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-02 | 4H+1H |  | 204 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-03 | 1H |  | 744 | inferred_constant_full_month | 1H | 744 | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-04 | 1H+4H |  | 540 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-07 | 4H+2H | 2 | 196 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BARD-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 228 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BASED-USDT-SWAP | 2026-03 | 4H |  | 7 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BASED-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BEAT-USDT-SWAP | 2025-11 | 4H |  | 107 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2025-12 | 1H+4H |  | 372 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BEAT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BERA-USDT-SWAP | 2025-02 | 4H |  | 132 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-02 | 1H+4H |  | 414 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BERA-USDT-SWAP | 2026-11 | 4H+2H | 2 | 161 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BICO-USDT-SWAP | 2026-08 | 4H+8H+2H | 2 | 142 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | BICO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BICO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BICO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIGTIME-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 176 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BILL-USDT-SWAP | 2026-05 | 4H |  | 151 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BILL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BILL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BILL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BILL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BILL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BILL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BIO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-08 | 4H+2H | 2 | 210 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-09 | 4H+2H | 2 | 276 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-10 | 4H+1H |  | 387 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-11 | 1H+4H |  | 252 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BIO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BLEND-USDT-SWAP | 2026-04 | 4H |  | 7 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLEND-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BLUR-USDT-SWAP | 2026-04 | 1H+4H+8H |  | 430 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-07 | 1H+4H+2H | 2 | 208 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-10 | 4H+2H | 2 | 201 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BLUR-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BOME-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BOME-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BRETT-USDT-SWAP | 2024-09 | 4H |  | 145 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BRETT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BREV-USDT-SWAP | 2025-12 | 4H |  | 6 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-01 | 1H+4H |  | 339 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-07 | 1H+4H+2H | 2 | 203 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BREV-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 191 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BSB-USDT-SWAP | 2026-04 | 4H |  | 169 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | BSB-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | BTW-USDT-SWAP | 2026-10 | 1H+4H+2H | 2 | 120 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | BTW-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 169 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CAP-USDT-SWAP | 2026-06 | 4H |  | 24 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | CAP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CAP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CAP-USDT-SWAP | 2026-09 | 4H+2H | 2 | 188 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CAP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CAP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CASHCAT-USDT-SWAP | 2026-09 | 4H |  | 165 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | CASHCAT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CASHCAT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CC-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CC-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CHIP-USDT-SWAP | 2026-04 | 4H |  | 54 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CHIP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CNPY-USDT-SWAP | 2026-09 | 1H+4H+2H | 2 | 176 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | CNPY-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CNPY-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | COAI-USDT-SWAP | 2025-10 | 1H |  | 384 | not_determinable_span_shorter_than_month | 1H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2025-11 | 1H+4H |  | 252 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | COAI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CP-USDT-SWAP | 2026-09 | 4H |  | 168 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | CP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CT-USDT-SWAP | 2026-09 | unknown_single_point |  | 1 | not_determinable_insufficient_points |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | CT-USDT-SWAP | 2026-10 | 4H+2H | 2 | 193 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | CVX-USDT-SWAP | 2026-01 | 1H+4H+8H |  | 386 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | CVX-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | DASH-USDT-SWAP | 2025-11 | 4H |  | 147 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DASH-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | DATA-USDT-SWAP | 2026-07 | 4H |  | 174 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | DATA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DATA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DATA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DATA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | DGAI-USDT-SWAP | 2026-09 | 4H |  | 165 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | DGAI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DGAI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | DNA-USDT-SWAP | 2026-10 | 4H |  | 90 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | DNA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | DOOD-USDT-SWAP | 2025-05 | 4H |  | 114 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-10 | 1H+4H |  | 444 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-03 | 4H+1H |  | 210 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-04 | 1H+4H |  | 456 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-10 | 4H+2H | 2 | 199 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOOD-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | DOS-USDT-SWAP | 2026-08 | 4H+2H | 2 | 131 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | DOS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | DOS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | EDEN-USDT-SWAP | 2025-09 | unknown_single_point |  | 1 | not_determinable_insufficient_points |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2025-12 | 1H+4H |  | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDEN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | EDGE-USDT-SWAP | 2026-04 | 4H |  | 174 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EDGE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | EIGEN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ENA-USDT-SWAP | 2025-09 | 4H |  | 80 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENA-USDT-SWAP | 2026-10 | 4H+8H |  | 119 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-03 | 8H+1H |  | 373 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-04 | 1H+4H+2H | 2 | 499 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENJ-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ENSO-USDT-SWAP | 2025-10 | 4H |  | 13 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-01 | 1H+4H |  | 267 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-02 | 4H+1H |  | 222 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-03 | 1H+4H |  | 726 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-04 | 4H+2H | 2 | 188 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ENSO-USDT-SWAP | 2026-11 | 4H+2H | 2 | 170 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ESP-USDT-SWAP | 2026-02 | 1H+4H |  | 131 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-04 | 1H+4H |  | 333 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-07 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ESP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHFI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ETHW-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ETHW-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | F-USDT-SWAP | 2025-10 | 1H |  | 148 | not_determinable_span_shorter_than_month | 1H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2025-11 | 1H+4H |  | 252 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-02 | 1H+4H |  | 585 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | F-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2024-12 | 4H |  | 67 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FARTCOIN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | FET-USDT-SWAP | 2026-09 | 4H |  | 153 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | FET-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FET-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | FLOCK-USDT-SWAP | 2026-09 | 4H |  | 109 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | FLOCK-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOCK-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | FLOW-USDT-SWAP | 2025-12 | 8H+1H |  | 177 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-01 | 1H+4H |  | 645 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-02 | 1H+4H |  | 495 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FLOW-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | FOGO-USDT-SWAP | 2026-01 | 4H |  | 126 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | FOGO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GAS-USDT-SWAP | 2024-07 | 8H+4H |  | 112 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2024-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2024-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-04 | 4H+2H | 2 | 302 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-05 | 4H+2H | 2 | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-02 | 1H+4H |  | 600 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GAS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GIGGLE-USDT-SWAP | 2025-10 | 4H |  | 38 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GIGGLE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GLM-USDT-SWAP | 2025-02 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-07 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 3 | 3 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-09 | 4H+2H | 2 | 188 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GLM-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GMT-USDT-SWAP | 2026-01 | 1H+4H+8H |  | 267 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GMT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GPS-USDT-SWAP | 2025-03 | 4H |  | 162 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-11 | 1H+4H |  | 267 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-01 | 1H+4H |  | 291 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GPS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GRAM-USDT-SWAP | 2026-06 | 4H |  | 79 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | GRAM-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRAM-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRAM-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRAM-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRAM-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GRASS-USDT-SWAP | 2024-10 | 4H |  | 18 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRASS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | GRVT-USDT-SWAP | 2026-07 | 4H |  | 6 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | GRVT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRVT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRVT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | GRVT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | H-USDT-SWAP | 2025-07 | 4H+2H | 2 | 290 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-06 | 1H+4H+2H | 2 | 311 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | H-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HMSTR-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | HOME-USDT-SWAP | 2025-06 | 4H |  | 103 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-06 | 1H+4H+2H | 2 | 352 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-07 | 4H+2H | 2 | 199 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-08 | 1H+4H+2H | 2 | 211 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HOME-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | HUMA-USDT-SWAP | 2025-05 | 4H |  | 30 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HUMA-USDT-SWAP | 2026-11 | 4H+2H | 2 | 173 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | HYPE-USDT-SWAP | 2025-02 | 4H |  | 44 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | HYPE-USDT-SWAP | 2026-04 | 4H+8H |  | 132 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IMX-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | INIT-USDT-SWAP | 2025-04 | 4H |  | 37 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-02 | 1H+4H |  | 345 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | INIT-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 177 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | IOST-USDT-SWAP | 2026-09 | 4H+8H+2H | 2 | 161 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | IOST-USDT-SWAP | 2026-10 | 1H+4H+2H | 2 | 207 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IOST-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | IRYS-USDT-SWAP | 2026-05 | 4H |  | 25 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | IRYS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IRYS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IRYS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IRYS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IRYS-USDT-SWAP | 2026-10 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | IRYS-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 181 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-03 | 4H |  | 30 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-01 | 1H+4H |  | 444 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-03 | 1H+4H |  | 552 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JELLYJELLY-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | JTO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-02 | 1H+4H |  | 315 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JTO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | JUP-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | JUP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KAITO-USDT-SWAP | 2025-02 | 4H |  | 48 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-03 | 4H+2H | 2 | 344 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-04 | 2H | 2 | 360 | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-05 | 4H+2H | 2 | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-09 | 4H+1H |  | 234 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-10 | 1H+4H |  | 564 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-11 | 1H+4H |  | 339 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-08 | 1H+4H+2H | 2 | 251 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAITO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KAT-USDT-SWAP | 2026-03 | 1H+4H |  | 250 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-04 | 1H+4H+2H | 2 | 208 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KAT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KGEN-USDT-SWAP | 2025-10 | 4H |  | 80 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KGEN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KII-USDT-SWAP | 2026-09 | 4H |  | 37 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | KII-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KII-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KITE-USDT-SWAP | 2026-04 | 4H |  | 129 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KITE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KMNO-USDT-SWAP | 2025-05 | 4H |  | 9 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KMNO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | KSM-USDT-SWAP | 2026-05 | 8H+4H |  | 165 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | KSM-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KSM-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KSM-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KSM-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KSM-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | KSM-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LA-USDT-SWAP | 2025-06 | 4H |  | 103 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2025-07 | 1H+4H |  | 456 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2025-09 | 4H+2H | 2 | 253 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2025-10 | 4H+2H | 2 | 312 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2025-11 | 1H+4H |  | 381 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-02 | 1H+4H |  | 501 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-06 | 4H+2H | 2 | 185 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-07 | 4H+2H | 2 | 212 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-08 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-09 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LAB-USDT-SWAP | 2025-11 | 4H |  | 174 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-06 | 1H+4H+2H | 2 | 338 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-07 | 1H+4H+2H | 2 | 265 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAB-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LAYER-USDT-SWAP | 2025-02 | 4H+2H | 2 | 201 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-03 | 2H | 2 | 372 | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-04 | 2H | 2 | 360 | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-05 | 4H+2H | 2 | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-11 | 1H+4H |  | 255 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2025-12 | 1H+4H |  | 327 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-05 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-06 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LAYER-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LIGHT-USDT-SWAP | 2025-12 | 1H+4H |  | 151 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-01 | 1H+4H |  | 453 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 5 | 5 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIGHT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LINEA-USDT-SWAP | 2025-09 | 4H |  | 174 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LINEA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LIT-USDT-SWAP | 2025-12 | 4H |  | 45 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LIT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LPT-USDT-SWAP | 2025-05 | 1H+4H+8H+2H | 2 | 142 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-06 | 1H |  | 720 | inferred_constant_full_month | 1H | 720 | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-07 | 1H+4H |  | 618 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LPT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | LUNA-USDT-SWAP | 2025-12 | 1H+4H+8H |  | 480 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | LUNA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-04 | 4H+8H+2H | 2 | 172 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-05 | 4H+2H | 2 | 318 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-07 | 4H+2H | 2 | 240 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MAGIC-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ME-USDT-SWAP | 2025-02 | 8H+4H |  | 141 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-09 | 4H+2H | 2 | 231 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-10 | 1H+4H+2H | 2 | 390 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-11 | 1H+4H |  | 252 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-01 | 1H+4H |  | 387 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-02 | 1H+4H |  | 408 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-07 | 4H+2H | 2 | 194 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ME-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MEGA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEGA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEGA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEGA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEGA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEGA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEGA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MEME-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEME-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MERL-USDT-SWAP | 2025-09 | 8H+2H | 2 | 216 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2025-10 | 1H+4H+2H | 2 | 372 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2025-11 | 1H+4H |  | 588 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2025-12 | 1H+4H |  | 384 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MERL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MET-USDT-SWAP | 2025-10 | 4H |  | 127 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MET-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | METIS-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | METIS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MEW-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-10 | 4H+2H | 2 | 195 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MEW-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MINA-USDT-SWAP | 2024-07 | 8H+4H |  | 112 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2024-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2024-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MINA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MMT-USDT-SWAP | 2025-11 | 1H+4H |  | 537 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-04 | 1H+4H |  | 366 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MMT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MON-USDT-SWAP | 2025-10 | 4H |  | 127 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MON-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MOODENG-USDT-SWAP | 2024-10 | 4H |  | 170 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOODENG-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MORPHO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MOVE-USDT-SWAP | 2025-05 | 8H+4H |  | 180 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2025-12 | 1H+4H |  | 480 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-01 | 1H+4H |  | 456 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-02 | 1H+4H |  | 405 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-06 | 4H+2H | 2 | 189 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MOVE-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 161 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-06 | 4H |  | 163 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | MUBARAK-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | NEIRO-USDT-SWAP | 2024-10 | 4H |  | 170 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NEIRO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | NES-USDT-SWAP | 2026-06 | 4H |  | 36 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | NES-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NES-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NES-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NES-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NES-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | NIGHT-USDT-SWAP | 2025-12 | 1H+4H |  | 172 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NIGHT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | NMR-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-08 | 4H+2H | 2 | 213 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-09 | 4H+2H | 2 | 319 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-10 | 4H+2H | 2 | 312 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-10 | 1H+4H+2H | 2 | 200 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NMR-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | NOT-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | NOT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | O-USDT-SWAP | 2026-06 | 4H |  | 77 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | O-USDT-SWAP | 2026-07 | 4H+2H | 2 | 192 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | O-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | O-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | O-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | O-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | OFC-USDT-SWAP | 2026-04 | 4H |  | 127 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OFC-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | OKB-USDT-SWAP | 2025-09 | 4H |  | 159 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OKB-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | OL-USDT-SWAP | 2025-10 | 4H+8H+132H | 132 | 84 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ONDO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONDO-USDT-SWAP | 2026-10 | 4H+8H |  | 119 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONE-USDT-SWAP | 2026-07 | 8H+4H |  | 123 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ONE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONE-USDT-SWAP | 2026-09 | 1H+4H+2H | 2 | 324 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ONT-USDT-SWAP | 2025-01 | 8H+4H |  | 146 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2025-12 | 4H+1H |  | 228 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-01 | 1H+4H |  | 456 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-03 | 1H+4H |  | 297 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-08 | 4H+2H | 2 | 196 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ONT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | OPG-USDT-SWAP | 2026-04 | 4H |  | 43 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPG-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | OPN-USDT-SWAP | 2026-02 | 4H |  | 31 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | OPN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ORDER-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-03 | 1H+4H |  | 339 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-10 | 1H+4H+2H | 2 | 206 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDER-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ORDI-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ORDI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PARTI-USDT-SWAP | 2025-03 | 4H |  | 36 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-11 | 1H+4H |  | 429 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-07 | 4H+2H | 2 | 192 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-10 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PARTI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PENDLE-USDT-SWAP | 2025-09 | 4H |  | 79 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENDLE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PENGU-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PENGU-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PI-USDT-SWAP | 2025-02 | 4H |  | 49 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2025-11 | 4H |  | 87 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2025-12 | 1H+4H |  | 402 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-01 | 1H+4H |  | 291 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIEVERSE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PIPPIN-USDT-SWAP | 2025-12 | 1H+4H |  | 453 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-01 | 1H+4H |  | 378 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-03 | 1H+4H |  | 435 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-04 | 1H+4H |  | 453 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PIPPIN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PLUME-USDT-SWAP | 2025-05 | 4H |  | 140 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-11 | 4H+1H |  | 258 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2025-12 | 1H+4H |  | 384 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PLUME-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PNUT-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PNUT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | POL-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PONS-USDT-SWAP | 2026-09 | 4H |  | 153 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PONS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PONS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | POPCAT-USDT-SWAP | 2024-08 | 4H |  | 13 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2024-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | POPCAT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PROS-USDT-SWAP | 2026-04 | 4H |  | 12 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-05 | 4H+2H | 2 | 191 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PROVE-USDT-SWAP | 2025-10 | 4H |  | 85 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-05 | 4H+2H | 2 | 196 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PROVE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | PUMP-USDT-SWAP | 2025-07 | 4H |  | 101 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PUMP-USDT-SWAP | 2026-10 | 4H+8H |  | 147 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | PYTH-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | QTUM-USDT-SWAP | 2025-02 | 8H+4H |  | 165 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | QTUM-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | QUANT-USDT-SWAP | 2026-10 | 4H |  | 181 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | QUANT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RAVE-USDT-SWAP | 2025-12 | 4H |  | 97 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-04 | 1H+4H |  | 351 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RAVE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RE-USDT-SWAP | 2026-06 | 4H+2H | 2 | 87 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | RE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RECALL-USDT-SWAP | 2025-10 | 4H |  | 7 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RECALL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RENDER-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RENDER-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-06 | 4H |  | 120 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-11 | 1H+4H |  | 474 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2025-12 | 1H+4H |  | 384 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-01 | 1H+4H |  | 345 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RESOLV-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RIVER-USDT-SWAP | 2026-01 | 1H+4H |  | 404 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-02 | 1H+4H |  | 360 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-03 | 1H+4H |  | 273 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RIVER-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RLS-USDT-SWAP | 2025-12 | 4H |  | 174 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | RLS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ROBO-USDT-SWAP | 2026-02 | 4H |  | 6 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ROBO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RSR-USDT-SWAP | 2026-10 | 4H+8H+2H | 2 | 160 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | RSR-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | RVN-USDT-SWAP | 2026-09 | 8H+4H |  | 150 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | RVN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-01 | 4H |  | 61 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | S-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-06 | 4H |  | 24 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-02 | 4H+1H |  | 189 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-03 | 1H+4H |  | 726 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-04 | 1H+4H |  | 390 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAHARA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SAND-USDT-SWAP | 2026-10 | 8H+4H |  | 180 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | SAND-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SAPIEN-USDT-SWAP | 2025-11 | 4H |  | 145 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SAPIEN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SEI-USDT-SWAP | 2025-11 | 4H |  | 98 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SEI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SENT-USDT-SWAP | 2025-11 | 4H |  | 96 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-01 | 4H+1H |  | 225 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-02 | 1H+4H |  | 618 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-03 | 1H+4H |  | 204 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SENT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SHELL-USDT-SWAP | 2025-02 | 4H |  | 6 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SHELL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SIGN-USDT-SWAP | 2025-04 | 4H |  | 13 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-04 | 4H+2H | 2 | 208 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SIGN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SKY-USDT-SWAP | 2025-09 | 4H |  | 115 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SKY-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SLX-USDT-SWAP | 2026-06 | 1H+4H+2H | 2 | 205 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SLX-USDT-SWAP | 2026-07 | 1H+4H+2H | 2 | 228 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | SLX-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SLX-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SLX-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SLX-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SOON-USDT-SWAP | 2025-05 | 4H |  | 49 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-08 | 4H+2H | 2 | 308 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-09 | 4H+2H | 2 | 276 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-11 | 1H+4H |  | 534 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-04 | 4H+2H | 2 | 205 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOON-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SOPH-USDT-SWAP | 2025-05 | 4H |  | 18 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-07 | 4H+2H | 2 | 230 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-08 | 2H | 2 | 372 | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-09 | 4H+2H | 2 | 276 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2025-12 | 1H+4H |  | 255 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-02 | 4H+1H |  | 177 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-03 | 1H+4H |  | 726 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-09 | 1H+4H+2H | 2 | 194 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-10 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SOPH-USDT-SWAP | 2026-11 | 1H+4H+2H | 2 | 179 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SPACE-USDT-SWAP | 2026-01 | 4H |  | 48 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-06 | 4H+2H | 2 | 190 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPACE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SPK-USDT-SWAP | 2025-06 | 4H |  | 79 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-04 | 4H+2H | 2 | 189 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPK-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SPX-USDT-SWAP | 2025-07 | 4H |  | 86 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SPX-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | STABLE-USDT-SWAP | 2025-12 | 4H |  | 138 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-04 | 1H+4H |  | 423 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STABLE-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | STRK-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | STRK-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | SYRUP-USDT-SWAP | 2025-07 | 4H+2H | 2 | 208 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2025-08 | 2H | 2 | 372 | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2025-09 | 4H+2H | 2 | 276 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | SYRUP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TAO-USDT-SWAP | 2024-09 | 4H |  | 62 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TAO-USDT-SWAP | 2026-04 | 4H+8H |  | 132 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TIA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TRB-USDT-SWAP | 2024-07 | 8H+4H |  | 133 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2024-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2024-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2024-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2024-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2024-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRB-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TRIA-USDT-SWAP | 2026-02 | 4H |  | 140 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRIA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-01 | 4H |  | 74 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUMP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TRUST-USDT-SWAP | 2025-11 | 1H+4H |  | 241 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUST-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TRUTH-USDT-SWAP | 2025-11 | 4H |  | 13 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TRUTH-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | TURBO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-11 | 4H+1H |  | 231 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2025-12 | 1H+4H |  | 384 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-03 | 1H+4H |  | 507 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | TURBO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | UB-USDT-SWAP | 2026-04 | 4H |  | 12 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UB-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | UMA-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UMA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | UP-USDT-SWAP | 2026-04 | 4H |  | 133 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | UP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | USELESS-USDT-SWAP | 2025-07 | 4H |  | 37 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | USELESS-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | VANA-USDT-SWAP | 2024-12 | 4H |  | 87 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-02 | 1H+4H |  | 456 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VANA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2024-12 | 4H |  | 121 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VIRTUAL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | VVV-USDT-SWAP | 2026-07 | 4H |  | 170 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | VVV-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VVV-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VVV-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | VVV-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | W-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | W-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | WAL-USDT-SWAP | 2025-05 | 4H |  | 140 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WAL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | WCT-USDT-SWAP | 2025-04 | 4H |  | 91 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-11 | 1H+4H |  | 363 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WCT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | WET-USDT-SWAP | 2025-12 | 1H+4H |  | 281 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-02 | 4H+1H |  | 210 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-03 | 1H+4H |  | 726 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WET-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | WIF-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WIF-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | WLFI-USDT-SWAP | 2025-08 | 4H |  | 48 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | WLFI-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | XDP-USDT-SWAP | 2026-09 | 4H+2H | 2 | 16 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | XDP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XDP-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | XPL-USDT-SWAP | 2025-08 | 4H |  | 19 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | XPL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | YB-USDT-SWAP | 2025-10 | 4H |  | 116 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YB-USDT-SWAP | 2026-11 | 4H+2H | 2 | 166 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | YGG-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | YGG-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-01 | 4H |  | 132 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZAMA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZBT-USDT-SWAP | 2025-10 | 1H+4H |  | 157 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZBT-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZEC-USDT-SWAP | 2025-11 | 4H |  | 147 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ZEC-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEC-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEC-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEC-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEC-USDT-SWAP | 2026-04 | 4H+8H |  | 132 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2025-11 | 4H |  | 164 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZEN-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZETA-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZETA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZIL-USDT-SWAP | 2026-02 | 1H+4H+8H |  | 576 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZIL-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZK-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-02 | 1H+4H |  | 603 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZK-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZKP-USDT-SWAP | 2026-01 | 1H+4H |  | 288 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-02 | 1H+4H |  | 609 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZKP-USDT-SWAP | 2026-11 | 4H+2H | 2 | 163 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZORA-USDT-SWAP | 2025-10 | 4H |  | 127 | not_determinable_span_shorter_than_month | 4H |  | unknown_no_official_schedule_source_used | 0 | 0 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-02 | 1H+4H |  | 609 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-08 | 4H+2H | 2 | 188 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-09 | 4H+2H | 2 | 184 | not_determinable_interval_change_or_gaps |  |  | unknown_no_official_schedule_source_used | 4 | 4 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZORA-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZRO-USDT-SWAP | 2025-05 | 8H+4H |  | 120 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-11 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2025-12 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-01 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRO-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
| non8h_month | ZRX-USDT-SWAP | 2025-12 | 8H+1H |  | 121 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 1 | 1 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-01 | 1H+4H |  | 456 | not_determinable_interval_change |  |  | unknown_no_official_schedule_source_used | 8 | 8 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-02 | 4H |  | 168 | inferred_constant_full_month | 4H | 168 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-03 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-04 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-05 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-06 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-07 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-08 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-09 | 4H |  | 180 | inferred_constant_full_month | 4H | 180 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-10 | 4H |  | 186 | inferred_constant_full_month | 4H | 186 | unknown_no_official_schedule_source_used | 2 | 2 | 0 | false | true |
| non8h_month | ZRX-USDT-SWAP | 2026-11 | 4H |  | 156 | not_determinable_window_truncated | 4H |  | unknown_no_official_schedule_source_used | 2 | 2 | 0 | true | true |
