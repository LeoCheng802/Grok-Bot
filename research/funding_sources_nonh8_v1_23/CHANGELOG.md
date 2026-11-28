# BACKTEST-READINESS-01 v1.23 (source register and non-8H completeness unknowns)

Offline compilation from already-saved PR #8 artifacts and the pinned frozen
funding DB (read-only). No official ZIP or REST file was refetched. No
backtest, no zero-fill, no interpolation, and no universe or window change.

No equivalent source-register or non-8H completeness-unknowns list was found
on this branch (search: funding_source_register, nonh8, non-8H completeness,
settlement denominator). Per-batch manifests, inventory r5, evidence jsonl,
and saved official files are cited as inputs; this folder is a new
compilation, not a duplicate of those files.

Self-run scans in this compilation are team execution evidence, not ChatGPT
runtime certification.

## Source register

`funding_source_register_v1_23.csv` / `.md` lists one row per source:
frozen DB l1, v1.7, v1.9, v1.10, v1.11_b1, v1.11_b2_r1, v1.11_b3a,
v1.11_b3b, v1.11_b3c, and REST 2026-11.

For each: source type, URL pattern, file count, row count, pinned SHA,
PR #8 path and commit (frozen DB is a pinned local read-only input, not
committed on PR #8), evidence form (raw bytes vs parsed), and review
status (復盤 PASS / ChatGPT acceptance comment IDs only where already
known to this compilation; IDs were not fetched from the network).

Delta SHA and row counts were re-read from the pinned files and match the
already-published manifests:

- frozen_db_l1: 829,157 rows, SHA `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc`
- v1.7: 6,748 rows (REST; raw bodies not retained on this branch)
- v1.9: 174 rows (ZIP and/or REST; raw evidence not retained on this branch)
- v1.10: 80 raw ZIPs; delta 10,633
- v1.11_b1: 5 raw ZIPs; delta 609
- v1.11_b2_r1: 1,279 raw ZIPs (kept under the b2 folder); delta 198,354
- v1.11_b3a: 1,961 raw ZIPs; delta 918
- v1.11_b3b: 1,961 raw ZIPs; delta 1,084
- v1.11_b3c: 1,960 raw ZIPs; delta 1,862
- REST 2026-11: 286 saved parsed-JSON files (285 histories + RVN 51001);
  39,037 official finite-numeric unique keys in CST 2026-11 inside the
  research window; evidence_form=parsed_json, raw_bytes_saved=false

Unique official monthly ZIPs indexed across v1.10–b3c: **7,246**. Official
ZIP numeric keys parsed for this compilation: 941,211 (2 flagged official
null rates: OL 2025-10 and ZK 2024-06).

## Non-8H completeness unknowns

Observed official settlements come from the saved official monthly ZIPs
where a ZIP exists for the inventory month, and from the saved 2026-11 REST
parsed-JSON files otherwise. **No official settlement-schedule source has
been used.** An expected-count denominator is written only when a single
observed interval in {1H, 4H, 8H} spans a full CST month that itself lies
inside the research window, with no internal missing slots. That figure is
an observed-assumption, inferred and not officially verified. All other
cases are not determinable from the saved data alone.

Inventory r5: 7,536 months.

- Months with at least one non-8H official settlement: **3,122**
- Official numeric months that are 8H-only (not listed as non-8H unknowns): 4,409
- Inventory months with no official numeric settlements in a saved ZIP/REST file: 5 (RVN 2026-11 + 4×404)
- Non-8H months with an *inferred* full-month constant-interval expected count (not official): **2,499**
- Non-8H months not determinable from the saved data alone: **623**
  (interval change or gaps 195; interval change 99; window truncated 198;
  span shorter than the month 121; internal gaps 8; insufficient points 2)
- Additional known-gap rows listed even if they have no non-8H settlements: 6
  (ZK 2024-06 official_rate_null is 8H-only; RVN 2026-11; 4×404).
  OL 2025-10 has non-8H settlements and is in the main 3,122.

Unknowns file rows: 3,128 (= 3,122 + 6).

Also listed:

- OL-USDT-SWAP 2025-10 and ZK-USDT-SWAP 2024-06: official_rate_null
  (1/85 and 1/54 literal `None`); inventory complete=false. Not zero-filled.
- RVN-USDT-SWAP 2026-11: pending_check / rest_51001_instrument_not_listed.
  Stays in the universe; no zero-fill.
- 4 official ZIP 404s, reason unknown: CC 2025-10, INJ 2023-11, MEGA 2026-04,
  ORDER 2025-09.

## CST vs UTC month-boundary effects (復盤 #7239320542)

Funding completeness in this research is bucketed by CST (UTC+8) month;
performance month buckets are UTC months, so boundaries can misalign. A
settlement whose UTC timestamp is on or after 16:00Z on the last UTC day of
a month falls in the next CST month and in the current UTC month.

These crossings are counted **one by one** from saved official timestamps
(not by formula). Typologically an 8H contract has exactly one such slot
per month (16:00Z); 4H and 1H contracts may have several in the last 8
hours (4H: 16:00Z and 20:00Z; 1H: 16:00Z through 23:00Z). Observed counts
match that typology on full constant-interval months (example: a full 4H
month lists two opening crossings; a full 1H month lists eight).

The research window ends 2026-11-26T12:00:00Z, so CST 2026-11 has **no
month-end crossing** in the saved data and is labelled a partial month.
Incoming opening crossings from 31 Oct 16:00Z+ are still counted when
present.

Columns added to `nonh8_completeness_unknowns_v1_23.csv` / `.md`:
`boundary_crossing_settlement_count`, `boundary_crossing_times_utc`,
`month_end_crossing_in_window`, `partial_month`,
`cst_vs_utc_boundary_effect`, `cst_vs_utc_completeness_may_differ`.

Among the 3,122 non-8H months:

- Opening boundary-crossing settlements counted one by one: **6,109**
- Months with at least one opening crossing: **2,974**
- Months flagged `cst_vs_utc_completeness_may_differ=true`: **3,122** (all of them; CST vs UTC endpoints can disagree even when no opening crossing is observed, because last-UTC-day 16:00Z+ slots of the same calendar month belong to the next CST month, except where the window already cuts the month short)
- CST 2026-11 non-8H rows: **212**, all `partial_month_no_month_end_crossing`
- Opening-crossing count histogram: 0×148; 1×69; 2×2,846; 3×1; 4×29; 5×1; 8×28

No performance numbers and no positions are reported.

## Limits

- complete=true in inventory r5 is passed per that batch's source and
  comparison scope only, not a full-period or cross-frequency verification.
- Inferred denominators are not official settlement-schedule figures.
- v1.7 / v1.9 raw official evidence is not retained on this branch (delta
  CSVs are the pinned artifacts).
- REST 2026-11 stored bodies are parsed JSON, not raw HTTP bytes.
- Review comment IDs are cited only where already known to this compilation.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

Run UTC: 2026-11-28T12:28:11Z – 2026-11-28T12:38:51Z.
