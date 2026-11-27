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
- A fresh derived `L1_DB` is copied from `B6_DB` only when that derived path does not already exist. Before any copy, reuse, or cleanup, `B6_DB`, `L1_DB`, and the sidecar must resolve to different paths. `<l1_db>.source_meta.json` records `b6_source_sha256`, `b6_source_name`, and `derived_l1_db_sha256` from the bytes of the derived file. An existing derived file is reused only when both recorded hashes match the current `B6_DB` and the current `L1_DB` bytes. Missing, malformed, or mismatched metadata raises `RuntimeError` and does not overwrite or repair the files. Fixed historical inputs are unchanged.
- The final report is written only after funding and simulation steps succeed, via a temp file and `os.replace`. Before that `try`, `_verify_output_paths_disjoint` requires every derived path (`L1_DB`, its sidecar, `l1_tp_result.json`, and their `.tmp` siblings) to be disjoint from `--funding-db`, `--manifest`, `--orig-long`, `--shared-risk`, and every manifest-registered file, and pairwise disjoint from each other. The check uses `Path.resolve()` and `os.path.samefile` when both paths exist. An overlap raises `RuntimeError` before any copy, write, or cleanup, and nothing is deleted to clear it. `_discard_final_report` also refuses to unlink a path that matches a fixed input.
- `indicators_180`, `build_cands_fib_long_exact`, scenario TP/SL pairs, slot/risk/TTL constants, and the pass-1/pass-2 study calls are unchanged.
- `--cache-dir`, `--funding-db`, and `--out-dir` still have their previous pack-relative defaults.

`offline_static_check.py`

- Stdlib only (`ast`, `hashlib`, `json`, `pathlib`, `re`).
- `REQUIRED_FILES` is a fixed non-empty tuple. A missing required file makes the result `FAIL` and the process exits non-zero.
- Any symlink component on a required file or on a parent directory between the check root and that file is `FAIL`, including an in-root alias and an `engine/` directory symlink. `is_file()` does not accept those links. A symlink anywhere in the tree whose target escapes the check root is also `FAIL`. The checker does not follow a symlinked directory.
- `PASS` also requires every required `.py` file to be in `checked_required_py` after AST parsing, leak scanning, and network-guard verification. The check is an `if`, not an `assert`.
- Parses Python with `ast.parse`, scans text for host-path prefixes and secret-shaped literals, checks the network guards above, and prints byte size plus SHA-256. A Windows `C:` or `D:` prefix counts only at a non-identifier boundary.
- Does not import strategy, `shared_risk`, or engine modules, and does not run `main()` or `--dry-check`.

## Status: 待驗

Every modified copy is **待驗**. Do not inherit original-version pass evidence, prior private-pack `--dry-check` results, or earlier SHA-256 acceptance. New copy SHA-256 values stay **待驗** until a later, formally approved run. `CANDIDATES.json` and `CANDIDATES.md` on `main` are untouched by this draft.

## Synthetic acceptance tests (UNEXECUTED)

These four designs use no network and no market data. SYN-NET-01, SYN-MANIFEST-02, and SYN-DB-03 stay **UNEXECUTED**. SYN-STATIC-04 is authorized for a later isolated run of the stdlib checker only, per issue comment `#7224263057`; this source change does not execute it. Every modified SHA remains **待驗**.

### SYN-NET-01

**UNEXECUTED.** After approval, call the FIB HTTP helper (`notify` or `Exchange.call`), construct `OkxClient` or call `public_get` / `private_req`, and call `fetch_okx_funding` and `backfill_missing_funding` with an artificial missing-funding stub. Each call raises `RuntimeError` (`OFFLINE_RESEARCH_COPY_NETWORK_DISABLED` for the network and funding entrypoints). A socket/`urlopen` counter stays at zero. There is no zero-fill. If the study path hits that funding error, no final report file remains.

### SYN-MANIFEST-02

**UNEXECUTED.** After approval, call `_verify_manifest_bindings` (not `_load_runtime_modules`, and not `main()` past the pre-check) with synthetic files. A SHA-256 mismatch, an empty `manifest["files"]`, a missing required entry, or an explicit `--orig-long` / `--shared-risk` path that is not the registered manifest file raises `RuntimeError` before any strategy or engine module is imported. Repeat under `python -O` and confirm the same `RuntimeError` (no `assert`).

### SYN-DB-03

**UNEXECUTED.** After approval, use two synthetic SQLite files and no market data:

- Point `_bind_isolated_funding_db` at a second `B6_DB` whose bytes differ from the hash recorded for an existing derived `L1_DB`. The call raises `RuntimeError` and does not reuse that file.
- Same `B6_DB` source and the old sidecar left in place, but the derived `L1_DB` bytes are replaced. `derived_l1_db_sha256` does not match the file on disk, so the call raises `RuntimeError` and does not overwrite or repair either file.
- The resolved `B6_DB` path is the same as the derived `L1_DB` path, or the same as the sidecar path. The call raises `RuntimeError` before any copy, reuse, or cleanup.
- `--funding-db` points at `out-dir/l1_tp_result.json` or `out-dir/l1_tp_result.json.tmp` (the same check covers the sidecar temp sibling). `_verify_output_paths_disjoint` raises `RuntimeError` before `main` enters the `try` that calls `_discard_final_report`. The fixed input is not deleted or renamed, and its SHA-256 is unchanged.

### SYN-STATIC-04

**Authorized for isolated execution, not run by this source change.** Issue comment `#7224263057` allows a later run of `offline_static_check.py` on an isolated temporary copy only. That run must not import strategy, `shared_risk`, or engine modules, must not call runner `main` or `--dry-check`, and must not read market data or use the network. It does not clear **待驗**. The cases are:

- A required file is removed.
- A symlink target is outside the check root.
- A required `.py` path is an in-root alias symlink to another file.
- `engine/` itself is a symlink.

`PASS` is allowed only when every required `.py` file has completed AST, leak, and network-guard checks. Restoring the tree is a separate observation and still does not clear **待驗**.

## Remaining blockers

- Formal review is required before any runtime test execution, acceptance decision, or merge.
- SYN-NET-01, SYN-MANIFEST-02, and SYN-DB-03 are **UNEXECUTED**. SYN-STATIC-04 is authorized for an isolated checker run and was not executed here. All candidate and runner SHAs remain **待驗**.
- This draft did not import or execute the trading modules, did not call `main()`, did not run `--dry-check`, and did not run historical replay, market scan, or candidate counting.
- No old test-pass evidence was copied onto these copies.
- `CANDIDATES.json` / `CANDIDATES.md` on `main` stay as they are. Registry rows for these new SHA-256 values remain **待驗** until a separate approved update.
- LONG-STRUCT-02 was not implemented.
- The draft pull request must stay unmerged and must not be deployed.
- Reachable strategy behavior is unchanged, but the unreachable HTTP/funding bodies are still present under the leading raises. There is no runtime switch that turns them back on.
- Importing `run_l1_tp_study.py` still parses CLI arguments. It does not import engine modules until `_load_runtime_modules` runs after the manifest check. SYN-NET-01, SYN-MANIFEST-02, and SYN-DB-03 stay blocked until execution is approved. SYN-STATIC-04 may be run later only as an isolated checker, and that run still leaves the SHAs **待驗**.
