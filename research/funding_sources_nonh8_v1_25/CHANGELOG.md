# BACKTEST-READINESS-01 v1.25 (correction of v1.23 non-8H completeness unknowns)

Offline correction from already-saved PR #8 files only. No refetch, no network
fetch, no backtest, no zero-fill, no interpolation, no change to any real rate.
The v1.23 folder is kept unchanged (its CSV SHA is
`dc4689a663b7552ef8688d6392b18ca8eba3cfec14096d2350502899df8938ce`). The v1.25
files are new and versioned. Self-run scans here are team execution evidence,
not ChatGPT runtime certification. No official settlement-schedule source has
been used: every denominator remains inferred, not officially verified.
FIB-4H-LONG-V3 remains NO-GO; live_approved is false.

Source: ChatGPT v1.25, Issue #1 comment 7239505073.

## 1. 2H misclassification (fixed)

v1.23 `analyze_month` recognised only 1H, 4H and 8H. A month that showed only a
constant 2H grid was folded into a 1H base and labelled
`not_determinable_internal_gaps` with `inferred_interval=1H`. That was a
classification error. In v1.25 a single constant observed gap of any whole-hour
size is kept as the observed interval; the official schedule is recorded as
`official_schedule_status=unknown_no_official_schedule_source_used`; any 2H
expectation is inferred only. `inferred_interval` is written only for a single
constant observed gap, and is blank for non-constant months. A constant
non-1H/4H/8H full month gets the new status
`inferred_constant_full_month_nonstandard_interval`. `interval_change_visible`
means an observed change in the saved data only, not proof of an official
interval change.

Eight months were affected (before / after):

| inst | CST month | observed pts | v1.23 status | v1.23 inferred | v1.23 expected | v1.25 observed | v1.25 status | v1.25 inferred | v1.25 expected | official schedule |
|---|---|---|---|---|---|---|---|---|---|---|
| API3-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown |
| AUCTION-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown |
| KAITO-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown |
| LAYER-USDT-SWAP | 2025-04 | 360 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 360 | unknown |
| LAYER-USDT-SWAP | 2025-03 | 372 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown |
| BARD-USDT-SWAP | 2025-09 | 144 | not_determinable_internal_gaps | 1H | (blank) | 2H | not_determinable_span_shorter_than_month | 2H | (blank) | unknown |
| SOPH-USDT-SWAP | 2025-08 | 372 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown |
| SYRUP-USDT-SWAP | 2025-08 | 372 | not_determinable_internal_gaps | 1H | (blank) | 2H | inferred_constant_full_month_nonstandard_interval | 2H | 372 | unknown |

The same bug also wrote `inferred_interval=1H` on 196 rows with status
`not_determinable_interval_change_or_gaps` (195 non-8H months plus the ZK-USDT-SWAP
2024-06 known-gap row); these are now blank because a non-constant month has no
single inferred interval. (The 204 changed rows = 8 + 196.)

General check for other unrecognised intervals: 125 months have an observed gap
outside 1H/4H/8H, namely 124 with 2H and 1 with 132H (the 4H+8H+132H month).
By v1.25 status: 117 `not_determinable_interval_change_or_gaps`, 7
`inferred_constant_full_month_nonstandard_interval`, 1
`not_determinable_span_shorter_than_month` (BARD 2025-09, listed mid-month).
No other gap size (for example 3H, 6H) occurs in the saved data.

## 2. Time basis: raw vs snap (documented)

`parse_zip_numeric` / `parse_rest_numeric` in the earlier scripts snap each
timestamp to the nearest hour with no tolerance before de-duplication, so the
6,109 in v1.23 is a snap-basis count. v1.25 reads the raw millisecond values
that are present in the saved official ZIPs (and in the saved parsed-JSON REST
files) and reports both bases separately. Evidence from the saved files:

- Rows parsed: 1,046,023 (ZIP 941,283 + REST 104,740); finite-rate rows
  1,046,021; 2 ZIP rows with a null/None rate are excluded (OL 2025-10, ZK 2024-06).
- Raw-vs-snap offset: 950,550 rows with zero offset, 95,471 with a non-zero
  offset (all in ZIP rows; REST rows are zero), maximum absolute offset 45,000 ms
  (1-9 s: 73,366; 10-59 s: 22,105).
- Raw ts vs snapped ts falling in different CST months: **0**; different UTC
  months: **0**.
- Months where the raw time set differs from the snapped time set: **0**.
- In-file snap collisions (several raw rows to one snapped key): **0**, so same
  snapped key with different rates inside one file is also **0**.
- Boundary-crossing settlements (UTC >= 16:00Z on the last UTC day of a month),
  non-8H months: **snap basis 6,109, raw basis 6,109**, 0 months where they
  differ; 0 mismatches against the v1.23 column. Including 8H months with files:
  10,387 on both bases. CST 2026-11 is partial with no month-end crossing in the window.
- Cross-file same snapped key: 65,703, all between a saved REST 2026-11 file and
  an official monthly ZIP (the REST files carry earlier history outside CST
  2026-11); different rate: **0**. ZIP-vs-ZIP: 0. These overlap rows are not
  used to add or change any value.
- Rows outside the month/window filter: 65,773 (REST earlier CST month 65,703;
  ZIP before the window start 70).
- **Unknown** (raw timestamps not saved): 4 months, the 404_reason_unknown set
  (CC-USDT-SWAP 2025-10, INJ-USDT-SWAP 2023-11, MEGA-USDT-SWAP 2026-04,
  ORDER-USDT-SWAP 2025-09). RVN-USDT-SWAP 2026-11 has a saved REST 51001
  response with zero data rows. The 2026-11 REST files are parsed JSON, so
  original HTTP bytes were not retained; the raw fundingTime values from the
  parsed JSON are used.
- v1.7 and v1.9 raw official bodies and the frozen DB were not used as a time
  source here; their raw timestamps are unknown on this branch.

## 3. NOT verified (explicit)

- Same-key-different-rate and snap collisions were checked only inside the saved
  ZIP/REST files described above. They were not re-run across the frozen DB,
  v1.7, v1.9, v1.10, b1..b3c deltas (the per-batch manifests report their own
  conflict counts; not re-checked here).
- A ZIP/REST hash listing is not per-file manifest acceptance, and makes no claim
  of full-rate completeness.
- Frozen DB `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc`
  only matches the b3b/b3c manifest references. Equal row counts do not mean
  equal to any other version.
- No official settlement-schedule source was used. All expected counts remain
  inferred, not verified. complete=true means passed for that batch's source and
  comparison scope only; blank means unknown.

## 4. Text correction

The v1.23 Issue #1 post called the 2,499 inferred months "可推斷（非常數全月區間，非官方）".
That was wrong. These are the **constant** full-month months
(`inferred_constant_full_month`: a single observed constant interval across a full
CST month inside the window). The wording is corrected here in the same batch,
without a separate re-run.

## Diff summary vs 3280b7a6 (v1.23)

Rows are the same set: 3,128 (3,122 non-8H months + 6 known-gap rows; the tables below count the 3,122 non-8H months). 204 rows
changed, all in `denominator_status` / `inferred_interval` / `inferred_expected_count`;
0 unexpected field changes.

| denominator_status | v1.23 | v1.25 |
|---|---:|---:|
| inferred_constant_full_month | 2,499 | 2,499 |
| inferred_constant_full_month_nonstandard_interval | 0 | 7 |
| not_determinable_window_truncated | 198 | 198 |
| not_determinable_interval_change_or_gaps | 195 | 195 |
| not_determinable_span_shorter_than_month | 121 | 122 |
| not_determinable_interval_change | 99 | 99 |
| not_determinable_internal_gaps | 8 | 0 |
| not_determinable_insufficient_points | 2 | 2 |

| inferred_interval | v1.23 | v1.25 |
|---|---:|---:|
| 4H | 2,814 | 2,814 |
| 1H | 207 | 4 |
| 2H | 0 | 8 |
| (blank) | 101 | 296 |

Observed-interval histogram is unchanged in shape; the 8 months keep observed `2H`.

## Synthetic old-fails / new-passes test

`test_2h_classification_v1_25.py` builds synthetic settlement grids only (no real
data): A full-month constant 2H, B 4H control, C 2H with one missing slot, D 2H
listed mid-month, and E (v1.25 only) raw-vs-snap offsets and a snap collision
with different rates. It is run from the repository root with a relative script path.

- Old logic (v1.23 generator at 3280b7a6): `test_2h_run_old_3280b7a6.log`:
  FAIL, 10 of 17 checks fail, exit code 1 (internal_gaps + inferred 1H).
- New logic (v1.25 generator): `test_2h_run_new_v1_25.log`: PASS, 22 of 22, exit code 0.

## Files

See `funding_sources_nonh8_v1_25_manifest.json` for sizes and SHA-256 of every
file. The `funding_sources_nonh8_v1_25_counts.json` sidecar is not committed.
