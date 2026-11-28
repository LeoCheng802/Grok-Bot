# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 08:44:55
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7231162465

<!-- comment_id: 7231162465 -->

[執行] v1.11-b3b 待核月份第 2 批＋生成器修正
【2026-11-28 08:44 台北時間（UTC+8）】

角色：執行
任務：BACKTEST-READINESS-01 v1.11-b3b（pending_check 第 2/3 批＋生成器修正）
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，branch `research/ex-usdc-286-manifests-draft`，未合併、未 force-push）
新 head：`363dc665e1b3d45c3c85bbdd808a3fc834c36c47`（父 commit `7852b42fe581ce15f1b5c84c8ca4f360c768e8fa`）
執行時間（UTC）：2026-11-28T00:30:43Z – 2026-11-28T00:41:42Z

本批開始前 pending_check 為 **3,922**（3,921 個剩餘切片月份 + RVN-USDT-SWAP 2026-11）。4 個 `official_unavailable` / `404_reason_unknown` 另外列出，不計入這 3,922。只新增已核為實際官方結算紀錄的鍵。未重建既有 delta（含 v1.11-b2 r1 的 198,354 列，SHA `ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`，以及 v1.11-b3a 的 918 列，SHA `0950a0d28966560a84b49a896e418f86ea2af8e866f61f6a15a9d321568cbaab`）。已驗證的 3,325 個 covered_verified ZIP 未重抓。以下計數與 manifest / flagged / conflicts 檔一致。本批自跑掃描是團隊執行證據，不是 ChatGPT runtime 認證。

## 切片定義

宇宙：inventory r2 class=`pending_check` 排除 RVN-USDT-SWAP 2026-11，共 5,882 個月，按 `(inst_id, month_cst)` 排序。`divmod(5882, 3)` → 1,961 / 1,961 / 1,960。切片切點與 v1.11-b3a manifest 相同，由 inventory r2 重建，不從 r3 剩餘 pending_check 重切。本批只處理 slice 2：index [1961, 3922)，ETHFI-USDT-SWAP 2026-07 … PENDLE-USDT-SWAP 2026-01。slice 3 未處理。

## 生成器修正（ChatGPT v1.17）與 baseline 重複檢查

1. `load_existing`：同一鍵不再默默保留第一筆。同鍵且 rate 與 `ts_raw` 相同則去重並計數；同鍵但 rate 或 `ts_raw` 不同則保留雙方證據（source、rate、`ts_raw`），列為 existing-input conflict，並列出受影響月份。普查範圍：frozen + v1.7 / v1.9 / v1.10 / v1.11_b1 / v1.11_b2_r1 / v1.11_b3a。
2. `write_inventory`：`complete=true` 僅當該月任一類衝突為 0（official-vs-existing、existing-input-internal、official-ZIP-internal 同鍵不同值）。official-ZIP-internal 衝突保存雙方列並按月列出。若 r3 的 `complete=true` 月份因此翻轉，r4 會記錄並說明。

Baseline census：frozen 829,157；v1.7 6,748；v1.9 174；v1.10 10,633；v1.11_b1 609；v1.11_b2_r1 198,354；v1.11_b3a 918（合計 1,046,593 列）。unique keys 1,046,593；clean keys 1,046,593；identical multi-source 去重 0（extra occurrences 0）；existing-input conflict keys 0（受影響月份 0）。此 baseline 每個鍵只出現在一個來源，先前 first-wins 行為在此集合上不會丢掉第二個值。r3 `complete=true` 翻轉：**0**。

## 抓取與比對

- fetched 1,961；HTTP 200：1,961；HTTP 404：0；HTTP other：0；skipped already-verified：0
- official numeric rows：261,822（unique keys 261,822；official-ZIP-internal conflicts 0；official identical dups 0）
- matched：260,738
- new：**1,084**（8H 542 / 非 8H 542）
- conflicts：official-vs-existing 0；existing-input-internal 0；official-ZIP-internal 0
- flagged：0（literal_none 0，empty 0，nan 0，inf 0，neg_inf 0，other non-numeric 0；official_rate_null 0，official_rate_nonfinite 0）

slice 2 的 1,961 個月在 inventory r3 均已有 existing_rows>0（37–720），故絕大多數官方 ZIP 鍵已在 frozen 或既有 delta 中；僅 1,084 鍵為未記錄新列。只新增已核為實際官方結算紀錄的鍵。不補 0、不內插。無 429 限流、無 403。

## Inventory r4（全表 7,536 列）

`complete=true` 僅表示「通過本批來源與比對範圍」：已取得官方月 ZIP，其中所有有限數值官方鍵已逐鍵比對，且該月任一類衝突為 0。不是全期或跨頻率驗證。`complete=false` 表示本批官方 ZIP 含 flagged 非數值／非有限 rate（已知未完整）。`blank` = 未知。只有 true 表示 complete（限上述範圍）。

- class：covered_verified 5,286；covered_verified_rest 285；pending_check 1,961；official_unavailable 4
- complete：true 5,569；false 2；blank 1,965
- complete=true 5,569 = covered_verified 5,284（既有 3,323 + 本批 1,961）+ covered_verified_rest 285
- complete=false 2 = OL-USDT-SWAP 2025-10、ZK-USDT-SWAP 2024-06（既有 official_rate_null；分別 1/85 與 1/54 literal None）
- pending_check 1,961 = slice 3（1,960）+ RVN-USDT-SWAP 2026-11（`rest_51001_instrument_not_listed`）
- official_unavailable 4，全部 `404_reason_unknown`（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）
- blank 1,965 = pending_check 1,961 + official_unavailable 4
- 本批新列為 covered_verified 且 complete=true 的 1,961 個月，正是 slice 2：ETHFI-USDT-SWAP 2026-07 … PENDLE-USDT-SWAP 2026-01

## 檔案 SHA-256

- `funding_delta_v1_11_b3b.csv.gz`：`f7b139a597e0257283a1c32dd632d6ef39a5822c15a03c929d1d433b53b66b9e`（12,039 B；1,084 列；解壓 CSV SHA `a802f9dd4acac9bea4a9ad45db14510465db9ac6f3e71c850e7b53d1d92a4a04`，228,035 B）
- `funding_null_rate_rows_v1_11_b3b.csv`：`2d9b5d2900837efbc42086e8f0f37a909d34658b5aa2cc27d8fe880b10657021`（0 列）
- `funding_conflicts_v1_11_b3b.json`：`494567f8edbd4de834e6e775c70af70b5d773b07da1bb756b6fd8907ffb7458f`
- `funding_source_months_v1_11_b3b.json`：`4a9b35876bd5b3659510153b1e3745a3c865281ef6d085926fcef35015b25bbe`
- `funding_month_inventory_v1_11_r4.csv`：`c9e6e7bcf8029babfde9ac07e2fdb1cc2557f32c22b7ffdf2031b90c74c07145`
- `funding_delta_v1_11_b3b_manifest.json`：`795bb57cbab67d90b60871e4dbe1893d6f97929ddd13dbceafa11a2944f0e584`
- `fetch_evidence_v1_11_b3b.jsonl`：`e2540e672b13403ecffa2468128e8ee6c1647d2c3336c4abde5ab01da74928a0`
- `build_delta_v1_11_b3b_public.py`：`953c321bde63686f8adc93b9e7d40b771e7f1bbbe800cecd5a5c0ab5eacb239b`
- `CHANGELOG.md`：`95e4325515ad45238e647f1748677840f8363470129e9c46bb2bb5dfddad980e`

## 剩餘缺口與限制

- 剩餘 pending_check：1,961 = slice 3（1,960）+ RVN-USDT-SWAP 2026-11。
- 4 個既有官方 ZIP 404 維持 `official_unavailable` / `404_reason_unknown`，原因仍未知。
- REST parsed-JSON 限制仍適用於既有 2026-11 REST 證據（本批未重抓 REST）。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線研究資料，未交易、未模擬、未擴窗、未補值。
