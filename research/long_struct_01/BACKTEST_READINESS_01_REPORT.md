# BACKTEST-READINESS-01 v1.0 — Phase A/B/C Offline Wiring & Backtest Readiness Report

- **Research ID:** `BACKTEST-READINESS-01 v1.0`
- **Authorization:** [Issue #1 #7225707059](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7225707059)
- **Fixed Starting Point:** PR #6 (`research/offline-packaging-hardening-draft`) head `3f67bd87fe5db2ec64d97b543fe780fa2f505f6f`
- **PR / Deployment Status:** Open Draft, NOT merged, NOT deployed. Zero live/demo orders.
- **Role:** `執行` (de-identified public summary; zero credentials, zero private code/data, zero trade-level traces)

---

## 1. Frozen Governance & Candidate Status (Unchanged)

| Item | Type | Frozen Version | Status | Script Delivered | Packaging Verified | Real-Engine Smoke (Phase B) | Full Baseline Replay (Phase C) | Known Adapter / Data Gaps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FIB-4H-LONG-V3` | **Baseline** (not a candidate) | v3 (`17b46a4e...`) | **`NO-GO`** (unchanged) | Yes (public PR #6) | Yes (`#7225486769`) | **PASS** (0 diffs vs fixture) | **ABORTED (`EXIT=2`)** on missing 8H funding (`158` / `128` gaps) | Missing historical 8H funding events in isolated DB; historical BBO / MMR / non-8H denominator unknown |
| `LONG-STRUCT-01` | **Script Candidate #1 (Long)** | v1.2 | **Frozen** | Private pack only | N/A (not in PR #6 code) | Not run (out of baseline scope) | Not run | Requires dedicated offline signal/sizing adapter & full-history funding coverage before any candidate replay |
| `RETEST24-R1-R2` | **Script Candidate #2 (Short)** | v1.5 (`c2b00a98...`) | **Frozen** | Yes (public PR #6) | Yes (`#7225486769`) | Not run (out of baseline scope) | Not run | Short-leg replay requires separate short-side bounded adapter; not mixed into L1 long baseline |
| `LONG-STRUCT-02` | Spec-only (`has_script: false`) | v1.2 | **Not implemented / Not counted as script candidate** | No | No | N/A | N/A | Explicitly excluded by `#7225707059` |

---

## 2. Phase A — Material Inventory & Bounded Offline Entry

### 2.1 Environment & Dependencies
- Python `3.13.5`, `numpy 2.5.5`, `pandas 3.0.6`, `sqlite3 3.46.1` (`scipy` not installed and not required).

### 2.2 Public Code (`PR #6 @ 3f67bd87`) vs Verified Private Pack (`RESEARCH-LOOP-01-PACK-v1.1`)
- Private pack archive reference (stays strictly local/private, NOT uploaded): `RESEARCH-LOOP-01-PACK-v1.1.tar.gz` (`136,828` B, SHA-256 `87dc925b8025c3bcaba87debb4d1bf8a86b794a8e47921f6ac2208b04e17da0d`), `REPRO_MANIFEST.json` (`4,661` B, SHA-256 `3dacf887135804560ee45d1e43a6f4162c322ec1a60cf5b5227440ba55399874`, 19/19 files verified).
- Private `scripts/shared_risk.py` (`25,125` B, SHA-256 `3bbb11a84ebd0bfd4fd46093828d2c55ebf696723645b14e325da0fc81802296`, stdlib only: `os, sqlite3, time, datetime, decimal`) — kept strictly private on local workspace; bound locally via explicit manifest, NEVER uploaded to public repo.
- Public vs private-pack diff audit (zero formula/strategy/cost/funding/risk changes):
  - `engine/b6_sim_portable.py` (`5,538` B, `b4b81446d50173bdd1d503fd3efc049cda3d35de53b7121b31996d3635723972`): **byte-identical**.
  - `engine/sim_50k_v3_2_sl_fix.py` (`13,996` B, `1d2aebf56eafa87820748c688ed778e625c483737fdda3dc714f79f4f67da7ca`): **byte-identical**.
  - `engine/audit_v3_1_full.py` (`26,951` B, `b4b264ef65654d5599221b0f58a399e704cee9e46535d2bd7e3c86e4844d4c02`): `+2/-1` Windows root path sanitization only (`OKX_RESEARCH_ROOT`).
  - `engine/run_q38_audit_01.py` (`27,984` B, `47efa8acf6933172b60e53237277b1adc9ddebf0bab664d22a90b28d5316b142`): `+3/-2` Windows root/engine path sanitization only.
  - `FIB_4H_Long_v3.py` (`55,001` B, `17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7`): `+10/-1` offline network/main hard-block only.
  - `RETEST24_R1_R2_Switchable_v1_5_auditfix.py` (`89,100` B, `c2b00a987150474a57aa0888234a91445d445d4026b49d86cc23a3f03d3c9f72`): `+19/-44` offline network/credential/main hard-block only.

### 2.3 New Bounded Offline Entry Point
- File: `research/long_struct_01/code/run_l1_bounded_backtest.py` (SHA-256 `26757d866146622176803c05948ed27007b87f9503aad3f4ef89934a74ddccbf`).
- Preserves `research/long_struct_01/code/run_l1_tp_study.py` untouched.
- Explicit CLI scope controls: `--symbols`, `--start-utc`, `--end-utc`, `--scenarios` (restricted to frozen `TP_2.5pct|cross_1tick` and `TP_2.5pct|delay1bar`; cannot accidentally trigger TP4/TP6 sweeps), `--out-dir`, `--dry-check`.
- Prints & writes resolved scope (`l1_bounded_scope.json`) before simulation; keeps outer-layer socket/HTTP `TransportBlocker` active for the entire run; enforces zero `assert`, zero top-level strategy/`shared_risk`/engine imports, manifest SHA-256 binding, read-only fixed inputs, path-disjointness guard, two-pass `_discard_final_report`, and **hard exit `2` with NO success report** on any `miss_8h > 0` funding gap.

---

## 3. Phase B — New-Version Integration Smoke Test (`minimal_repro_fixture_v1`)

- **Fixture Inputs:** `cache_v3_min` (`BNB-USDT-SWAP`, `SOL-USDT-SWAP`; `manifest.json` SHA-256 `3647a3d9b532c1abd7dbfd47713ae55ba7355b319bcf7473c0162bbfda1e24c4`), `funding_min.sqlite` (SHA-256 `ce0805fd3f09d4d83615354370d2e19bb462b7b595a0c54bdea5b7316dc41067`), eval window `2025-10-01T00:00:00Z .. 2025-10-31T23:30:00Z` (warmup from `2025-07-01T00:00:00Z`).
- **Execution UTC:**
  - `B.0 (--dry-check)`: `2026-11-27T18:47:48.970Z` → `EXIT=0`, `files_verified=6`, `modules_executed=false`, `transport_hits=[]`.
  - `B.1 (Valid fixture)`: `2026-11-27T18:50:05.462Z .. 2026-11-27T18:50:05.624Z` (`0.16s`) → **`EXIT=0` (`PASS`)**, `transport_hits=[]`, `inputs_unchanged=True`, `mapping_verification`: `200` bars checked, `81` signals matched, **`0` signal mismatches**, `4` exit target checks, **`0` exit target mismatches**.
  - **Comparison vs `expected_baseline_output.json`:** **0 diffs across all fields** for both `TP_2.5pct|cross_1tick` and `TP_2.5pct|delay1bar` (`closed_trades=3`, `win_rate_pct=66.67`, `closed_net_u=26.57`, `final_eq_u=50026.57`, `mtm_mdd_pct=0.41`, `pf=1.173`, `expectancy_u=8.856`, `f_ev_real_8h=6`, `f_ev_real_non8h=0`, `f_ev_miss_8h=0`). Output SHA-256: `8c29813592fdac8a57e9147172b5bd1161f7d0e8209a2d38497bd1757ec95ef4`.
  - `B.2 (Missing-funding negative check)`: `2026-11-27T18:50:05.754Z .. 2026-11-27T18:50:05.912Z` (`0.16s`) on isolated temp copy with October `BNB-USDT-SWAP` funding rows removed → **`EXIT=2` (`ABORTED_MISSING_FUNDING`)**, `l1_bounded_result.json` NOT created, `l1_bounded_missing_funding_abort.json` written (`a4775396ebeb0463917a0eb3712e1466a152e17c37c5cea8a2e36c548648c67b`, `miss_8h_count=1` at `2025-10-09T16:00:00Z`), `transport_hits=[]`, `inputs_unchanged=True`.

---

## 4. Phase C — Fixed Baseline Full Historical Replay (`EX_USDC_286`, TP2.5% Only)

- **Scope:** Full `EX_USDC_286` (`cache_v3/manifest.json` SHA-256 `b6b4fde6dc84cc26d72258a38e4b6059ca1fe2fa24bea369f9a792e5e36d71b8`, 286 symbols excluding `USDC-USDT-SWAP`, historical delisted preserved) + `funding_archive_l1_isolated.sqlite` (SHA-256 `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc`, `829,157` rows, `270` insts), window `2023-01-01T00:00:00Z .. 2026-11-26T12:00:00Z`, ONLY `TP_2.5pct|cross_1tick` and `TP_2.5pct|delay1bar` (no TP4/TP6 sweep).
- **Execution UTC:** `2026-11-27T18:50:19.041Z .. 2026-11-27T18:51:52.493Z` (`93.45s`).
- **Outcome:** **`ABORTED_MISSING_FUNDING` (`EXIT=2`)** — hard offline refusal triggered cleanly; **NO** `l1_bounded_result.json` success report written; zero zero-fill, zero interpolation, zero window shrinkage, zero network calls (`transport_hits=[]`, `inputs_unchanged=True`).
- **Pre-abort verification:** `symbols_loaded=286`, `bars_30m_in_window=68,425`, `candidate_bars_in_window=8,130`, `candidate_signals_in_window=267,734`, `mapping_verification`: `3,000` bars checked, `521` signals matched, **`0` signal mismatches**, `4` exit target checks, **`0` exit target mismatches**.
- **Exact Missing 8H Funding Event Gaps (Local Abort Report SHA-256 `54037c6f1c44a2db9b5a4e032aafbfd006366eeaba461dfd81ed6725385c6b1e`):**
  - `TP_2.5pct|cross_1tick`: **`miss_8h_count = 158`** across **55 distinct symbols** (`2023-09-29T16:00:00Z .. 2026-10-18T08:00:00Z`); matched `f_ev_real_8h = 6,415`, `f_ev_real_non8h = 1,228`.
  - `TP_2.5pct|delay1bar`: **`miss_8h_count = 128`** across **54 distinct symbols** (`2023-01-30T16:00:00Z .. 2026-08-14T16:00:00Z`); matched `f_ev_real_8h = 6,171`, `f_ev_real_non8h = 961`.
- **Known Data & Modeling Limitations:**
  - Missing historical BBO (`post_only` queue priority & fillability unknown); `cross_1tick` is a lower-bound crossing check, not proof of live fillability.
  - Historical MMR approximated at `1%`; historical tick size uses snapshot values; non-8H funding settlement denominator completeness remains unverified.
  - `delay1bar` is a sensitivity test, not measured live latency.
  - `FIB-4H-LONG-V3` remains **`NO-GO`** regardless of technical runnability.
