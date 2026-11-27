# Synthetic hardening verification summary

De-identified record of one harness run. No credentials, market cache, host paths, or private-pack results are included.

- Fixed target commit: `c5f28d0b79593847bfa95a881127b89094e0d0ab`
- Harness: `research/long_struct_01/code/run_synthetic_hardening_verification.py`
- Harness SHA-256: `0b711cf75c8bf15df457a7600ff6fb6d28942d2b4092d5896deda23ba28f3e0b`
- Harness stdout JSON SHA-256: `e89e51de30c2e5a2b3ccaf2a7ba8c59e2ed6dcb1a3ac7021706f4b2af8dd8eac`
- Harness process exit code: `1`
- Overall: **FAIL** (one sub-case). This does not clear **待驗**.

Target file pins matched the fixed commit before any case ran:

| File | SHA-256 |
| --- | --- |
| `FIB_4H_Long_v3.py` | `17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7` |
| `RETEST24_R1_R2_Switchable_v1_5_auditfix.py` | `c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04` |
| `run_l1_tp_study.py` | `c9b5571c942ac863845e6863d814ae6a1d7f0501b4b73acf5e057b86ef579d94` |

Scope is packaging refusal only. `FIB-4H-LONG-V3` remains **NO-GO**. `LONG-STRUCT-02` is not implemented. Candidates, strategy rules, costs, and full history remain **待驗**. SYN-STATIC-04 was not part of this run.

Temporary files lived under `tempfile.mkdtemp()` and were removed on exit. Commands below use `<code>` and `<tmpdir>` instead of machine paths.

## SYN-NET-01 — PASS

Helper/function layer only. Functions were compiled from unmodified source slices. This does **not** claim full `main()` study execution.

Outer blocker: `socket.socket`, `socket.create_connection`, `urllib.request.urlopen`, `http.client.HTTPConnection`, `http.client.HTTPSConnection`. `transport_hits == 0`.

| Symbol | Lines | Expected | Actual |
| --- | --- | --- | --- |
| `notify` | L191–L214 | `RuntimeError` `OFFLINE_RESEARCH_COPY_NETWORK_DISABLED` | raised that `RuntimeError` |
| `Exchange.call` | L229–L261 | same | raised that `RuntimeError` |
| `Exchange.pages` | L263–L274 | same, via `call` | raised that `RuntimeError` |
| `OkxClient.__init__` | L422–L428 | same | raised that `RuntimeError` |
| `OkxClient.public_get` | L437–L450 | same | raised that `RuntimeError` |
| `OkxClient.private_req` | L452–L479 | same | raised that `RuntimeError` |
| `load_config_credentials` | L482–L484 | `("", "", "")` | `("", "", "")` |
| `fetch_okx_funding` | L296–L321 | same `RuntimeError` | raised that `RuntimeError` |
| `backfill_missing_funding` | L323–L353 | same `RuntimeError`; no zero-fill; sqlite SHA unchanged | raised that `RuntimeError`; row count stayed `1`; SHA `f27f2f0b55cb7dabca5cf277da3963f835dc2cd24ff73f7aab3b5c64fb1ebd76` before and after |

## SYN-MANIFEST-02 — PASS

Real subprocess CLI, both `python3` and `python3 -O`. `PYTHONPATH` supplied `sitecustomize.py` with the same transport blocker and a `sys.meta_path` sentinel. Synthetic `scripts/FIB_4H_Long_v3.py`, `scripts/shared_risk.py`, and `engine/*.py` bodies record execution if loaded.

Command shape:

`python3 <code>/run_l1_tp_study.py --dry-check --manifest <tmpdir>/REPRO_MANIFEST.json --orig-long <orig> --shared-risk <shared> --funding-db <tmpdir>/unused_funding.sqlite --out-dir <tmpdir>/out --cache-dir <tmpdir>/cache`

The `-O` command is the same with `python3 -O`. Every sub-case had `module_sentinel_hits == []`, `transport_hits == []`, and unchanged synthetic input SHA-256.

| Mode | Sub-case | Expected | Actual |
| --- | --- | --- | --- |
| `python3` | `valid_control` | exit `0`, `dry_check == "PASS"` | exit `0`, `PASS` |
| `python3` | `hash_mismatch` | non-zero | exit `1` |
| `python3` | `empty_files_map` | non-zero | exit `1` |
| `python3` | `missing_required_entry` | non-zero | exit `1` |
| `python3` | `unregistered_explicit_path` | non-zero | exit `1` |
| `python3 -O` | `valid_control` | exit `0`, `dry_check == "PASS"` | exit `0`, `PASS` |
| `python3 -O` | `hash_mismatch` | non-zero | exit `1` |
| `python3 -O` | `empty_files_map` | non-zero | exit `1` |
| `python3 -O` | `missing_required_entry` | non-zero | exit `1` |
| `python3 -O` | `unregistered_explicit_path` | non-zero | exit `1` |

## SYN-DB-03 — FAIL

Function layer of unmodified `sha` (L125–L130), `_paths_overlap` (L503–L520), `_verify_output_paths_disjoint` (L549–L567), `_atomic_write_text` (L570–L578), `_discard_final_report` (L581–L591), and `_bind_isolated_funding_db` (L594–L652). Two synthetic SQLite files, `source_a.sqlite` and `source_b.sqlite`. Not full `main()`.

| Sub-case | Expected | Actual |
| --- | --- | --- |
| `clean_bind_create` | sidecar stores source and derived hashes | pass |
| `clean_bind_reuse` | second bind keeps those bytes | pass |
| `source_changed` | `RuntimeError`; no overwrite | pass; source and derived SHAs unchanged |
| `stale_sidecar_derived_mutated` | `RuntimeError`; mutated derived bytes kept | pass |
| `missing_sidecar` | `RuntimeError`; no new sidecar | pass |
| `corrupt_sidecar` | `RuntimeError`; corrupt sidecar kept | pass |
| `overlap_b6_vs_l1` | `RuntimeError` before copy | pass; source SHA unchanged |
| `overlap_b6_vs_sidecar` | `RuntimeError` before copy | pass; source SHA unchanged |
| `overlap_funding_vs_report_verify` | `RuntimeError` before write | pass; report SHA unchanged |
| `overlap_funding_vs_report_discard` | `RuntimeError` before unlink | pass; report SHA unchanged |
| `overlap_funding_vs_report_tmp_verify` | `RuntimeError` before write | pass; report and `.tmp` SHAs unchanged |
| `overlap_funding_vs_report_tmp_discard` | `RuntimeError` before any unlink; report and `.tmp` SHAs unchanged | **fail** |
| `overlap_output_vs_output` | `RuntimeError`; no write | pass |
| `overlap_symlink_alias` | `RuntimeError` on the alias; source SHA unchanged | pass |

`overlap_funding_vs_report_tmp_discard` did raise `RuntimeError: refusing to delete l1_tp_result.json.tmp because it overlaps fixed input funding-db`, and the `.tmp` fixed input was not unlinked. `_discard_final_report` unlinks `l1_tp_result.json` first when that sibling does not itself overlap a fixed input, and only then checks `l1_tp_result.json.tmp`. The pre-existing report file was therefore removed before the refusal. The fixed `.tmp` SHA stayed the same; the report SHA did not, because the file was gone. The closed runner was not edited.

## What this run does not decide

Passing sub-cases show those packaging refusals behaved as exercised here. They do not approve a candidate, a strategy rule, a cost model, or a full historical replay. `FIB-4H-LONG-V3` stays **NO-GO**. `LONG-STRUCT-02` stays unimplemented. All of those remain **待驗**.
