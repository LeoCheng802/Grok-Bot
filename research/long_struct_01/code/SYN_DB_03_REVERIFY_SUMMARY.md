# SYN-DB-03 DB-only re-verification

De-identified record of one DB-only run. No credentials, market cache, host paths, or private-pack results are included. SYN-NET-01 and SYN-MANIFEST-02 were not run. This does not clear **待驗**.

- Command: `python3 research/long_struct_01/code/run_syn_db_03_reverify.py --json-out research/long_struct_01/code/SYN_DB_03_REVERIFY_RESULT.json`
- Process exit code: `0`
- `started_utc`: `2026-11-27T18:19:53.617964+00:00`
- `finished_utc`: `2026-11-27T18:19:53.659008+00:00`
- `transport_blocker_active_entire_run`: `true`
- `transport_hits`: `[]`
- `module_sentinel_hits`: `[]`
- Runner SHA-256 (`run_l1_tp_study.py`): `e920b95356db3636cc6083b1b6254042ee1f78fa963d4f7a66e86c52b23c75eb`
- Harness SHA-256 (`run_syn_db_03_reverify.py`): `e09d98cec0687855f51ba0817aa556de4a7943c1ee2e34a85d06886e8158b161`
- JSON SHA-256 (`SYN_DB_03_REVERIFY_RESULT.json`): `2e3fdd5d35f0ccd2d10832885129cd71ff9f60a5f6439a4bf49f9f0e2e83d4e3`
- Overall: **PASS**

The earlier harness FAIL for the temp-file discard sub-case remains in `SYNTHETIC_HARDENING_VERIFICATION_SUMMARY.md`. That DB section ran after the outer transport blocker had been restored. This re-run kept the blocker installed until every sub-case finished.

Extracted unmodified helpers from `run_l1_tp_study.py`:

| Function | Lines |
| --- | --- |
| `sha` | L125–L130 |
| `_paths_overlap` | L503–L520 |
| `_verify_output_paths_disjoint` | L549–L567 |
| `_atomic_write_text` | L570–L578 |
| `_discard_final_report` | L581–L594 |
| `_bind_isolated_funding_db` | L597–L655 |

`sha256` is omitted below when `exists` is false.

## control_clean_bind_create

No exception. `source_a` stayed `exists=true`, SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39`. `l1_db` went `exists=false` to `exists=true`, SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39`. `sidecar` went `exists=false` to `exists=true`, SHA `07e31cda7d98affa3ff411cd8f71d90f04ba8ad667c5266de9c5c7f03f2bcb63`.

## control_clean_bind_reuse

No exception. Before and after are identical for all three files: `source_a` and `l1_db` SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39`; `sidecar` SHA `07e31cda7d98affa3ff411cd8f71d90f04ba8ad667c5266de9c5c7f03f2bcb63`. Each stayed `exists=true`.

## Rejection sub-cases

Each rejection raised `RuntimeError`. Watched `exists` and SHA-256 values were unchanged.

| Sub-case | Watched result |
| --- | --- |
| `source_changed_rejected` | `source_a` and `l1_db` SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39`; `source_b` SHA `16f3164c85463750652f1fee7443ac3c9b3058cd55c0c8098102277272b9a6d9`; `sidecar` SHA `07e31cda7d98affa3ff411cd8f71d90f04ba8ad667c5266de9c5c7f03f2bcb63`; all `exists=true` |
| `stale_sidecar_derived_mutated_rejected` | `l1_db` stayed the mutated SHA `23ddde2566df128aa44f0734abe55cac4f5acb67dbc8e1856ea15a1a29489d82`; `sidecar` SHA `07e31cda7d98affa3ff411cd8f71d90f04ba8ad667c5266de9c5c7f03f2bcb63`; `source_a` SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39`; all `exists=true` |
| `missing_sidecar_rejected` | `sidecar` stayed `exists=false`; `l1_db` and `source_a` SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39` |
| `corrupt_sidecar_rejected` | `sidecar` stayed SHA `021fb596db81e6d02bf3d2586ee3981fe519f275c0ac9ca76bbcf2ebb4097d96`; `l1_db` and `source_a` SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39`; all `exists=true` |
| `overlap_b6_with_l1_db` | `source_a` SHA unchanged; extra sidecar stayed `exists=false` |
| `overlap_b6_with_sidecar` | `source_a` SHA unchanged; derived file stayed `exists=false` |
| `overlap_funding_db_with_final_report` | both `l1_tp_result.json` (SHA `e002b5d26e1539448bc6b569f9a8ae64b38877c9e9746e16175cb417fce0e4bd`) and `l1_tp_result.json.tmp` (SHA `68dedb2473d25ddc36cf14cf4d5d990bef59cb810048594a59f2cafbb13c61b5`) stayed `exists=true` through `_verify_output_paths_disjoint` and `_discard_final_report` |
| `overlap_funding_db_with_final_report_tmp` | the same two files and the same two SHAs stayed `exists=true` through both calls |
| `overlap_output_with_output` | output file SHA `c818669a0e5af7dc1be2cbf7883dcb16264d7d8f81781cec6c0b9187b18f448c` unchanged; `source_a` unchanged |
| `overlap_symlink_alias_with_fixed_input` | alias and `source_a` stayed `exists=true` with SHA `7aff5af28ad59bc8dace0549b0acb4804f74009b75fa43f9e089f364fb0d7b39` |

## What this run does not decide

`FIB-4H-LONG-V3` stays **NO-GO**. `LONG-STRUCT-02` stays unimplemented. Candidates, strategy rules, costs, and full history stay **待驗**.
