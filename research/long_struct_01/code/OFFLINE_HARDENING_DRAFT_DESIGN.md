# Offline packaging hardening draft

Status of every modified copy in this branch: **待驗**.

This document is a design note for an isolated draft pull request. It is not a test report. Nothing below was accepted as a pass, and original-version pass evidence does not transfer to these copies.

## Scope

Branch: `research/offline-packaging-hardening-draft` (from `main`).

Touched paths:

- `research/long_struct_01/code/FIB_4H_Long_v3.py`
- `research/long_struct_01/code/RETEST24_R1_R2_Switchable_v1_5_auditfix.py`
- `research/long_struct_01/code/run_l1_tp_study.py`
- `research/long_struct_01/code/offline_static_check.py` (new, stdlib static verifier)
- `research/long_struct_01/code/OFFLINE_HARDENING_DRAFT_DESIGN.md` (this note)

Not touched:

- `CANDIDATES.json` and `CANDIDATES.md` on `main`
- `research/long_struct_01/code/engine/`
- LONG-STRUCT-02 strategy code (not implemented)
- private data, caches, archives, credentials, or full private-pack results

## Exact diff summary

Packaging and refusal only. No signal, indicator, ranking, cost, position-sizing, exit, TTL, or risk-control rule was edited.

`FIB_4H_Long_v3.py`

- `main()` is unchanged and still begins with `SystemExit` (live/demo execution stays hard-blocked).
- `notify` and `Exchange.call` (the `urlopen` wrappers) now begin with an unconditional `RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: network/OKX HTTP access is permanently disabled in this sanitized research copy.")`.
- There is no flag and no environment variable that skips that raise.
- The previous HTTP bodies remain below the raise and are unreachable. Indicator, entry, TTL, and risk constants are unchanged.

`RETEST24_R1_R2_Switchable_v1_5_auditfix.py`

- `load_config_credentials()` is unchanged and still returns `"", "", ""`.
- `main()` is unchanged and still begins with `SystemExit`.
- `OkxClient.__init__`, `OkxClient.public_get`, and `OkxClient.private_req` now begin with an unconditional `RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: OkxClient network access is permanently disabled in this sanitized research copy.")`.
- There is no toggle back to network or live trading. Signal, indicator, sizing, exit, TTL, and risk-control functions are unchanged.

`run_l1_tp_study.py`

- `fetch_okx_funding` and `backfill_missing_funding` now begin with an unconditional `RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: funding fetch/backfill is disabled; missing funding must fail explicitly without zero-fill or network download.")`.
- The raise in `backfill_missing_funding` is the first statement, so the old `except Exception: return []` path cannot swallow it, zero-fill a gap, or download. That old body is unreachable.
- Top-level engine imports are gone. `_load_runtime_modules` runs only after `_verify_manifest_bindings` has read the manifest and matched SHA-256. `--dry-check` returns after that read and does not import strategy, `shared_risk`, or engine modules.
- `--manifest`, `--shared-risk`, and `--orig-long` are all required. `manifest["files"]` must be a non-empty object that contains `scripts/FIB_4H_Long_v3.py`, `scripts/shared_risk.py`, and exactly one `engine/<filename>` entry for each of `audit_v3_1_full.py`, `sim_50k_v3_2_sl_fix.py`, `run_q38_audit_01.py`, and `b6_sim_portable.py`. The explicit CLI paths must resolve to those registered files. A hash mismatch, an empty `files` object, a missing entry, or an unregistered explicit path raises `RuntimeError` before any module load. Integrity checks use `RuntimeError` / `SystemExit`, not `assert`.
- A derived `L1_DB` is copied from `B6_DB` only when it does not already exist. `<l1_db>.source_meta.json` records `b6_source_sha256` and `b6_source_name`. An existing `L1_DB` without that metadata, or with a different hash, raises `RuntimeError` and does not reuse the file. Fixed historical inputs are unchanged.
- The final report is written only after funding and simulation steps succeed, via a temp file and `os.replace`. Any exception on that path, including the missing-funding `RuntimeError`, deletes the final report and its temp file before the error propagates.
- `indicators_180`, `build_cands_fib_long_exact`, scenario TP/SL pairs, slot/risk/TTL constants, and the pass-1/pass-2 study calls are unchanged.
- `--cache-dir`, `--funding-db`, and `--out-dir` still have their previous pack-relative defaults.

`offline_static_check.py`

- Stdlib only (`ast`, `hashlib`, `json`, `pathlib`, `re`).
- `REQUIRED_FILES` is a fixed non-empty tuple. A missing required file makes the result `FAIL` and the process exits non-zero.
- Any symlink in the tree, including a required path, whose target escapes the check root (or is broken) is `FAIL`. The checker does not follow a symlinked directory.
- Parses Python with `ast.parse`, scans text for host-path prefixes and secret-shaped literals, checks the network guards above, and prints byte size plus SHA-256. A Windows `C:` or `D:` prefix counts only at a non-identifier boundary.
- Does not import strategy, `shared_risk`, or engine modules, and does not run `main()` or `--dry-check`.

## Status: 待驗

Every modified copy is **待驗**. Do not inherit original-version pass evidence, prior private-pack `--dry-check` results, or earlier SHA-256 acceptance. New copy SHA-256 values stay **待驗** until a later, formally approved run. `CANDIDATES.json` and `CANDIDATES.md` on `main` are untouched by this draft.

## Synthetic acceptance tests (UNEXECUTED)

These four designs use no network and no market data. Status: **UNEXECUTED**, pending formal approval. Every modified SHA remains **待驗**. A static inspection while preparing this draft does not mark any of them passed.

### SYN-NET-01

After approval, call the FIB HTTP helper (`notify` or `Exchange.call`), construct `OkxClient` or call `public_get` / `private_req`, and call `fetch_okx_funding` and `backfill_missing_funding` with an artificial missing-funding stub. Each call raises `RuntimeError` (`OFFLINE_RESEARCH_COPY_NETWORK_DISABLED` for the network and funding entrypoints). A socket/`urlopen` counter stays at zero. There is no zero-fill. If the study path hits that funding error, no final report file remains.

### SYN-MANIFEST-02

After approval, call `_verify_manifest_bindings` (not `_load_runtime_modules`, and not `main()` past the pre-check) with synthetic files. A SHA-256 mismatch, an empty `manifest["files"]`, a missing required entry, or an explicit `--orig-long` / `--shared-risk` path that is not the registered manifest file raises `RuntimeError` before any strategy or engine module is imported. Repeat under `python -O` and confirm the same `RuntimeError` (no `assert`).

### SYN-DB-03

After approval, create two synthetic SQLite `B6_DB` files with different bytes and an existing derived `L1_DB` in `out-dir`. Point the run at the second source. The sidecar `b6_source_sha256` does not match, `_bind_isolated_funding_db` raises `RuntimeError`, and the existing database is not reused. No market data is read.

### SYN-STATIC-04

After approval, run `offline_static_check.py` once with a required file removed and once with a symlink whose target is outside the check root. Both return `FAIL` and exit non-zero. The process does not import strategy, `shared_risk`, or engine modules. Restoring the tree and removing the symlink is a separate static pass/fail observation and still does not clear **待驗**.

## Remaining blockers

- Formal review is required before any runtime test execution, acceptance decision, or merge.
- SYN-NET-01, SYN-MANIFEST-02, SYN-DB-03, and SYN-STATIC-04 are **UNEXECUTED**.
- This draft did not import or execute the trading modules, did not call `main()`, did not run `--dry-check`, and did not run historical replay, market scan, or candidate counting.
- No old test-pass evidence was copied onto these copies.
- `CANDIDATES.json` / `CANDIDATES.md` on `main` stay as they are. Registry rows for these new SHA-256 values remain **待驗** until a separate approved update.
- LONG-STRUCT-02 was not implemented.
- The draft pull request must stay unmerged and must not be deployed.
- Reachable strategy behavior is unchanged, but the unreachable HTTP/funding bodies are still present under the leading raises. There is no runtime switch that turns them back on.
- Importing `run_l1_tp_study.py` still parses CLI arguments. It does not import engine modules until `_load_runtime_modules` runs after the manifest check. The four synthetic tests stay blocked until that execution is approved.
