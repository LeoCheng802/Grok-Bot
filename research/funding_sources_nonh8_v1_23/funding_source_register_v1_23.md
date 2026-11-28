# Funding source register (v1.23)

Offline compilation from already-saved PR #8 artifacts and the pinned frozen
DB (read-only). No official file was refetched. No equivalent source-register
file was found on this branch; per-batch manifests are cited rather than
copied in full. SHA and row counts below were re-read from the pinned files
and match those manifests.

`row_count` for official-ZIP batches is the **delta** (new keys added in that
batch), except `frozen_db_l1` (archive rows) and `REST_2026_11` (official
finite-numeric unique keys in CST 2026-11 inside the research window, parsed
from the saved REST files). `file_count` for official-ZIP batches is the
number of raw monthly ZIPs retained in that batch folder.

Review status lists 復盤 PASS and ChatGPT acceptance comment IDs only where
they were already known to this compilation; IDs were not fetched from the
network. Self-run checks here are team execution evidence, not ChatGPT
runtime certification.

FIB-4H-LONG-V3 remains NO-GO. live_approved is false.

## Summary table

| batch | source_type | file_count | row_count | pinned_sha256 | pr8_path | commit_sha | evidence_form | raw_bytes_saved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_db_l1 | frozen DB | 1 | 829157 | 23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc |  |  | sqlite_table_rows | false |
| v1.7 | REST parsed JSON (funding-rate-history) | 1 | 6748 | 34743db093b5673233693b0bfd4fa020abeb3928f7d4c0c29603c4d4c01311be | research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz | 57c30e539ffe73cb2378bc94a8a5c3432707944e | delta_csv_only | false |
| v1.9 | official monthly ZIP and/or REST (mixed; see v1.9 manifest) | 1 | 174 | 01ed8da28efa7038d03369b0b02b78f5777d3f21d95e5a95ca1e26221bb3340e | research/funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz | 8458510c0eb4bc365c121b9c835c2895103aea40 | delta_csv_only | false |
| v1.10 | official monthly ZIP | 80 | 10633 | 4fe33c0efe78f1398b02cb231760d3817b13f985de013e51df9c273dec7c999b | research/funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz | b0dcf61e26db0e99b178ad0fe59d3944edbe6492 | raw_zip | true |
| v1.11_b1 | official monthly ZIP | 5 | 609 | 2ab89d43188e38c0b34ea04513d9c199eee2fa7fc5bfac891993db2006d48bbb | research/funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz | 6499a579aacdf922c67f432915245adef0c11dc7 | raw_zip | true |
| v1.11_b2_r1 | official monthly ZIP (plus REST 2026-11 listed as its own row) | 1279 | 198354 | ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86 | research/funding_delta_v1_11_b2_r1/funding_delta_v1_11_b2_r1.csv.gz | 928beeb6cfeaa9fc686f0bdfe44154abba6e14ec | raw_zip | true |
| v1.11_b3a | official monthly ZIP | 1961 | 918 | 0950a0d28966560a84b49a896e418f86ea2af8e866f61f6a15a9d321568cbaab | research/funding_delta_v1_11_b3a/funding_delta_v1_11_b3a.csv.gz | 7852b42fe581ce15f1b5c84c8ca4f360c768e8fa | raw_zip | true |
| v1.11_b3b | official monthly ZIP | 1961 | 1084 | f7b139a597e0257283a1c32dd632d6ef39a5822c15a03c929d1d433b53b66b9e | research/funding_delta_v1_11_b3b/funding_delta_v1_11_b3b.csv.gz | 363dc665e1b3d45c3c85bbdd808a3fc834c36c47 | raw_zip | true |
| v1.11_b3c | official monthly ZIP | 1960 | 1862 | 8f49f40fa0d47297ab7f4d3b5d21a7b60177f1936079519eccba05ab7137cfda | research/funding_delta_v1_11_b3c/funding_delta_v1_11_b3c.csv.gz | f1280dc41d8409ed856fd41c339ff095a67ebe74 | raw_zip | true |
| REST_2026_11 | REST parsed JSON (funding-rate-history) | 286 | 39037 | 1412704ba9925a6595d12dce55e4b9377a7013ce969a52670422f9f786361038 | research/funding_delta_v1_11_b2/rest_2026_11/ | 928beeb6cfeaa9fc686f0bdfe44154abba6e14ec | parsed_json | false |

## Per-batch notes and review status

### frozen_db_l1

- source type: frozen DB
- URL pattern: `(none)`
- file count: 1
- row count: 829157
- pinned SHA-256: `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc` (74924032 bytes)
- PR #8 path: `(not in PR #8)`
- commit: `(n/a)`
- evidence form: sqlite_table_rows; raw_bytes_saved=false
- review status: Pinned SHA is the read-only baseline in all v1.11 manifests on PR #8. No dedicated 復盤 comment for the DB file alone is cited here.
- notes: Pinned local read-only input funding_archive_l1_isolated.sqlite (829157 rows). Not committed on PR #8; SHA is recorded in every later v1.11 batch manifest. Opened mode=ro only. This is an archive table, not raw official ZIP or HTTP bytes.

### v1.7

- source type: REST parsed JSON (funding-rate-history)
- URL pattern: `https://www.okx.com/api/v5/public/funding-rate-history?instId={INST}&after={AFTER}&limit=100`
- file count: 1
- row count: 6748
- pinned SHA-256: `34743db093b5673233693b0bfd4fa020abeb3928f7d4c0c29603c4d4c01311be` (91491 bytes)
- PR #8 path: `research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz`
- commit: `57c30e539ffe73cb2378bc94a8a5c3432707944e`
- evidence form: delta_csv_only; raw_bytes_saved=false
- review status: Delta SHA is pinned as an input in later v1.11 manifests. A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.7 is not cited here.
- notes: Official endpoint was REST funding-rate-history. Raw HTTP bodies and parsed page files are not retained on this branch; the pinned artifact is the 6,748-row delta CSV. SHA re-verified against the file and against later batch input manifests.

### v1.9

- source type: official monthly ZIP and/or REST (mixed; see v1.9 manifest)
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip | https://www.okx.com/api/v5/public/funding-rate-history?instId={INST}&after={AFTER}&limit=`
- file count: 1
- row count: 174
- pinned SHA-256: `01ed8da28efa7038d03369b0b02b78f5777d3f21d95e5a95ca1e26221bb3340e` (3547 bytes)
- PR #8 path: `research/funding_delta_v1_9/funding_delta_missing174_v1_9.csv.gz`
- commit: `8458510c0eb4bc365c121b9c835c2895103aea40`
- evidence form: delta_csv_only; raw_bytes_saved=false
- review status: Delta SHA is pinned as an input in later v1.11 manifests. A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.9 is not cited here.
- notes: v1.9 manifest lists both the official monthly ZIP CDN and REST funding-rate-history. No raw monthly ZIPs and no raw HTTP bodies for v1.9 are present on this branch; the pinned artifact is the 174-row delta CSV plus funding_missing174_classification_v1_9.json.

### v1.10

- source type: official monthly ZIP
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip`
- file count: 80
- row count: 10633
- pinned SHA-256: `4fe33c0efe78f1398b02cb231760d3817b13f985de013e51df9c273dec7c999b` (158227 bytes)
- PR #8 path: `research/funding_delta_v1_10/funding_delta_full75plus_v1_10.csv.gz`
- commit: `b0dcf61e26db0e99b178ad0fe59d3944edbe6492`
- evidence form: raw_zip; raw_bytes_saved=true
- review status: Delta SHA is pinned as an input in later v1.11 manifests. A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.10 is not cited here.
- notes: 80 raw official monthly ZIPs are saved under research/funding_delta_v1_10/official_monthly_zips/. row_count is the pinned delta (new keys only: 10,633), not the official ZIP row total (11,031 numeric in the v1.10 manifest).

### v1.11_b1

- source type: official monthly ZIP
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip`
- file count: 5
- row count: 609
- pinned SHA-256: `2ab89d43188e38c0b34ea04513d9c199eee2fa7fc5bfac891993db2006d48bbb` (8286 bytes)
- PR #8 path: `research/funding_delta_v1_11_b1/funding_delta_5sym_v1_11_b1.csv.gz`
- commit: `6499a579aacdf922c67f432915245adef0c11dc7`
- evidence form: raw_zip; raw_bytes_saved=true
- review status: Delta SHA is pinned as an input in later v1.11 manifests. A 復盤 PASS or ChatGPT acceptance comment ID specifically for v1.11-b1 is not cited here.
- notes: 5 raw official monthly ZIPs are saved under research/funding_delta_v1_11_b1/official_monthly_zips/. row_count is the pinned delta (609 new keys).

### v1.11_b2_r1

- source type: official monthly ZIP (plus REST 2026-11 listed as its own row)
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip`
- file count: 1279
- row count: 198354
- pinned SHA-256: `ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86` (3035583 bytes)
- PR #8 path: `research/funding_delta_v1_11_b2_r1/funding_delta_v1_11_b2_r1.csv.gz`
- commit: `928beeb6cfeaa9fc686f0bdfe44154abba6e14ec`
- evidence form: raw_zip; raw_bytes_saved=true
- review status: 復盤 PASS of head 928beeb6: Issue #1 comment 7230640210. D1 found: 7230456720. ChatGPT v1.16: 7230504858; supplement 7230544291. Execution reports: 7230527499 (r1 D1), 7230617170 (v1.16 follow-up).
- notes: 1279 raw official monthly ZIPs remain under research/funding_delta_v1_11_b2/official_monthly_zips/ (introduced in 74764f32f6bcdfab8bcc25211eaeed9755fdeffe). The r1 delta (198,354) supersedes the b2 delta after dropping 2 official literal-None rates (D1). Raw ZIP evidence form is raw_zip / raw_bytes_saved=true. REST 2026-11 is a separate register row.

### v1.11_b3a

- source type: official monthly ZIP
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip`
- file count: 1961
- row count: 918
- pinned SHA-256: `0950a0d28966560a84b49a896e418f86ea2af8e866f61f6a15a9d321568cbaab` (10941 bytes)
- PR #8 path: `research/funding_delta_v1_11_b3a/funding_delta_v1_11_b3a.csv.gz`
- commit: `7852b42fe581ce15f1b5c84c8ca4f360c768e8fa`
- evidence form: raw_zip; raw_bytes_saved=true
- review status: Execution report Issue #1 comment 7230844369 (PR #8 index 7230846110). A 復盤 PASS or ChatGPT acceptance comment ID specifically for b3a is not cited here.
- notes: 1961 raw official monthly ZIPs are saved under research/funding_delta_v1_11_b3a/official_monthly_zips/. row_count is the pinned delta (918 new keys). Fetch evidence: fetch_evidence_v1_11_b3a.jsonl.

### v1.11_b3b

- source type: official monthly ZIP
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip`
- file count: 1961
- row count: 1084
- pinned SHA-256: `f7b139a597e0257283a1c32dd632d6ef39a5822c15a03c929d1d433b53b66b9e` (12039 bytes)
- PR #8 path: `research/funding_delta_v1_11_b3b/funding_delta_v1_11_b3b.csv.gz`
- commit: `363dc665e1b3d45c3c85bbdd808a3fc834c36c47`
- evidence form: raw_zip; raw_bytes_saved=true
- review status: Execution report Issue #1 comment 7231162465 (PR #8 index 7231164350). ChatGPT v1.18 acceptance: 7231209641.
- notes: 1961 raw official monthly ZIPs are saved under research/funding_delta_v1_11_b3b/official_monthly_zips/. row_count is the pinned delta (1,084 new keys). Fetch evidence: fetch_evidence_v1_11_b3b.jsonl.

### v1.11_b3c

- source type: official monthly ZIP
- URL pattern: `https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/{YYYYMM}/{INST}-fundingrates-{YYYY}-{MM}.zip`
- file count: 1960
- row count: 1862
- pinned SHA-256: `8f49f40fa0d47297ab7f4d3b5d21a7b60177f1936079519eccba05ab7137cfda` (23008 bytes)
- PR #8 path: `research/funding_delta_v1_11_b3c/funding_delta_v1_11_b3c.csv.gz`
- commit: `f1280dc41d8409ed856fd41c339ff095a67ebe74`
- evidence form: raw_zip; raw_bytes_saved=true
- review status: Execution report Issue #1 comment 7231372486 (PR #8 index 7231374137). ChatGPT v1.23 (7239218755) is the assignment for this compilation, not an acceptance of b3c.
- notes: 1960 raw official monthly ZIPs are saved under research/funding_delta_v1_11_b3c/official_monthly_zips/. row_count is the pinned delta (1,862 new keys). Fetch evidence: fetch_evidence_v1_11_b3c.jsonl. Inventory r5 lives in this folder.

### REST_2026_11

- source type: REST parsed JSON (funding-rate-history)
- URL pattern: `https://www.okx.com/api/v5/public/funding-rate-history?instId={INST}&after={AFTER}&limit=400`
- file count: 286
- row count: 39037
- pinned SHA-256: `1412704ba9925a6595d12dce55e4b9377a7013ce969a52670422f9f786361038` (1110384 bytes)
- PR #8 path: `research/funding_delta_v1_11_b2/rest_2026_11/`
- commit: `928beeb6cfeaa9fc686f0bdfe44154abba6e14ec`
- evidence form: parsed_json; raw_bytes_saved=false
- review status: Same review trail as v1.11-b2 r1 (REST evidence form and RVN 51001 documented in that follow-up): Issue #1 7230640210 (復盤 PASS of 928beeb6); ChatGPT v1.16 7230504858 / 7230544291. Stored REST bodies are parsed JSON, not raw HTTP bytes.
- notes: 286 saved files (285 instrument histories + RVN 51001 present). Bodies are parsed JSON (raw_bytes_saved=false), documented in research/funding_delta_v1_11_b2_r1/rest_evidence_form.json (SHA 5ea53c523001070de522c5db4f360f46a85e67944f67d84e4cdaffa0e75bfdf5). RVN-USDT-SWAP 2026-11 evidence: research/funding_delta_v1_11_b2_r1/rvn_usdt_swap_2026_11_rest_51001_evidence.json (SHA c74b71d80169355980f2c5f45f46a96996d1b77e1e7e8ea25ad1ed8fbedd92bd). row_count is official finite-numeric unique keys inside the research window and CST 2026-11: 39037. Pinned SHA is SHA-256 of the sorted listing rest_2026_11_file_sha256s_v1_23.txt (name, bytes, file SHA), not a single archive. Files introduced in commit 74764f32f6bcdfab8bcc25211eaeed9755fdeffe; form labels in 928beeb6cfeaa9fc686f0bdfe44154abba6e14ec.

