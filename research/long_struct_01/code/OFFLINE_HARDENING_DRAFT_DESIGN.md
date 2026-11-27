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
- `--manifest` and `--shared-risk` are explicit CLI arguments. `--orig-long` no longer defaults to a private `PACK_ROOT/scripts` path and no longer reads `REPRO_ORIG_LONG`.
- Private-pack `--dry-check` requires all three paths. If any required path is omitted, `argparse` exits with an error that names the missing flags. Relative manifest hashes resolve from the manifest file's parent (the target copy), and `shared_risk.py` is loaded from `--shared-risk`. Hashes must match that target copy.
- Public-directory static checks are not `--dry-check`. They are `offline_static_check.py`.
- `indicators_180`, `build_cands_fib_long_exact`, exit-target checks, scenario TP/SL pairs, slot/risk/TTL constants, and the pass-1/pass-2 study calls are unchanged.
- `--cache-dir`, `--funding-db`, and `--out-dir` still have their previous pack-relative defaults. That layout is outside this manifest/shared-risk split.

`offline_static_check.py`

- Stdlib only (`ast`, `hashlib`, `json`, `pathlib`, `re`).
- Parses the public `code/` tree, scans text for host-path prefixes and secret-shaped literals, checks the network guards above, and prints byte size plus SHA-256 for each file. A Windows `C:` or `D:` prefix counts only at a non-identifier boundary, so an identifier ending in those letters plus a Python newline escape is not a drive path.
- Does not import the trading scripts and does not run `main()` or `--dry-check`.

## Status: 待驗

Every modified copy is **待驗**. Do not inherit original-version pass evidence, prior private-pack `--dry-check` results, or earlier SHA-256 acceptance. New copy SHA-256 values stay **待驗** until a later, formally approved run. `CANDIDATES.json` and `CANDIDATES.md` on `main` are untouched by this draft.

## Synthetic acceptance tests (not executed as acceptance)

These four designs use no network and no market data. They are reserved for execution only after formal approval. Running a static inspection while preparing this draft does not mark any of them passed and does not clear **待驗**.

### SYN-NET-01

After approval, call the FIB HTTP helper (`notify` or `Exchange.call`), construct `OkxClient` or call `OkxClient.public_get` / `private_req`, and call `run_l1_tp_study.fetch_okx_funding`. Each call raises `RuntimeError` whose message starts with `OFFLINE_RESEARCH_COPY_NETWORK_DISABLED`, and a counter wrapped around `urlopen` / `requests.Session` / socket connect stays at zero.

Importing `run_l1_tp_study` also imports engine modules and parses CLI arguments at import time. That import is not approved in this draft.

### SYN-GAP-02

After approval, call `run_l1_tp_study.backfill_missing_funding` with an artificial missing-funding stub such as `[("stub", "BTC-USDT-SWAP", 0, "miss_8h")]` and an unused database path. The call raises the funding `RuntimeError` before opening the database, before zero-fill, and before any download. The same `urlopen` counter stays at zero.

### SYN-PATH-03

After approval, call `run_l1_tp_study._parse_args` (not `main()`, and not `--dry-check` execution) with temporary dummy paths:

- `--dry-check --manifest <tmp>/REPRO_MANIFEST.json --shared-risk <tmp>/shared_risk.py --orig-long <tmp>/FIB_4H_Long_v3.py`

The returned namespace resolves those three paths with `Path.expanduser()` and does not prefix `PACK_ROOT/scripts`. The dummy files do not need to exist for the parser step.

Omission fails clearly:

- `_parse_args(["--dry-check"])` raises `SystemExit` (argparse error) naming `--manifest`, `--shared-risk`, and `--orig-long`.
- `_parse_args([])` raises `SystemExit` naming `--orig-long`.

This call still requires importing `run_l1_tp_study`, which imports engine modules. Do not run it until that import is approved.

### SYN-STATIC-04

After approval, run `python3 research/long_struct_01/code/offline_static_check.py` on `research/long_struct_01/code/`. The process exits 0 only when AST/syntax parses, host-path and secret scans are clean, and every retained network entrypoint has the unconditional `OFFLINE_RESEARCH_COPY_NETWORK_DISABLED` guard. The process must not import `FIB_4H_Long_v3`, `RETEST24_R1_R2_Switchable_v1_5_auditfix`, `run_l1_tp_study`, or the engine modules.

## Remaining blockers

- Formal review is required before any runtime test execution, acceptance decision, or merge.
- This draft did not import or execute the trading modules, did not call `main()`, did not run `--dry-check`, and did not run historical replay, market scan, or candidate counting.
- No old test-pass evidence was copied onto these copies.
- `CANDIDATES.json` / `CANDIDATES.md` on `main` stay as they are. Registry rows for these new SHA-256 values remain **待驗** until a separate approved update.
- LONG-STRUCT-02 was not implemented.
- The draft pull request must stay unmerged and must not be deployed.
- Reachable strategy behavior is unchanged, but the unreachable HTTP/funding bodies are still present under the leading raises. Removing a raise would be a later source change; there is no runtime switch that turns them back on.
- `run_l1_tp_study.py` still imports engine modules and calls `_parse_args()` at import time, so SYN-NET-01, SYN-GAP-02, and SYN-PATH-03 are blocked on an explicit import approval even though they do not need market data.
