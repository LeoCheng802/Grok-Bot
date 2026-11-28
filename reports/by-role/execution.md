# 執行

此檔是「執行」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 08:21:09
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230844369

<!-- comment_id: 7230844369 -->

[執行] v1.11-b3a 待核月份第 1 批
【2026-11-28 08:20 台北時間（UTC+8）】

角色：執行
任務：BACKTEST-READINESS-01 v1.11-b3a（pending_check 第 1/3 批）
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，branch `research/ex-usdc-286-manifests-draft`，未合併、未 force-push）
新 head：`7852b42fe581ce15f1b5c84c8ca4f360c768e8fa`（父 commit `928beeb6cfeaa9fc686f0bdfe44154abba6e14ec`）
執行時間（UTC）：2026-11-28T00:06:36Z – 2026-11-28T00:18:03Z

文字更正一次：先前 Issue 評論 #7230617170 將 OL-USDT-SWAP 2025-10 的 official `None` 列寫成 2/85；正確為 **1/85**（ZK-USDT-SWAP 2024-06 仍為 1/54）。未重建 v1.11-b2 r1 的 198,354 列 delta（SHA `ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`）。以下計數與 manifest / flagged 檔一致。本批自跑掃描是團隊執行證據，不是 ChatGPT runtime 認證。

## 切片定義

宇宙：inventory r2 class=`pending_check` 排除 RVN-USDT-SWAP 2026-11，共 5,882 個月，按 `(inst_id, month_cst)` 排序。`divmod(5882, 3)` → 1,961 / 1,961 / 1,960。本批只處理 slice 1：index [0, 1961)，0G-USDT-SWAP 2025-12 … ETHFI-USDT-SWAP 2026-06。slice 2/3 未處理。已驗證的 1,364 個 covered_verified ZIP 未重抓。

## 抓取與比對

- fetched 1,961；HTTP 200：1,961；HTTP 404：0；HTTP other：0；skipped already-verified：0
- official numeric rows：232,095（unique keys 232,095；intra-official dups 0）
- matched：231,177
- new：**918**（8H 469 / 非 8H 449）
- conflicts：0
- flagged：0（literal_none 0，empty 0，nan 0，inf 0，neg_inf 0，other non-numeric 0；official_rate_null 0，official_rate_nonfinite 0）

slice 1 的 1,961 個月在 inventory r2 均已有 existing_rows>0，故絕大多數官方 ZIP 鍵已在 frozen 或既有 delta 中；僅 918 鍵為未記錄新列。不補 0、不內插。無 429 限流、無 403。

## Inventory r3（全表 7,536 列）

`complete=true` 僅表示「通過本批來源與比對範圍」：已取得官方月 ZIP，且其中所有有限數值官方鍵已逐鍵比對。不是全期或跨頻率驗證。`complete=false` 表示本批官方 ZIP 含 flagged 非數值／非有限 rate（已知未完整）。`blank` = 未知。只有 true 表示 complete（限上述範圍）。

- class：covered_verified 3,325；covered_verified_rest 285；pending_check 3,922；official_unavailable 4
- complete：true 3,608；false 2；blank 3,926
- complete=true 3,608 = covered_verified 3,323（既有 1,362 + 本批 1,961）+ covered_verified_rest 285
- complete=false 2 = OL-USDT-SWAP 2025-10、ZK-USDT-SWAP 2024-06（既有 official_rate_null；分別 1/85 與 1/54 literal None）
- pending_check 3,922 = slice 2（1,961）+ slice 3（1,960）+ RVN-USDT-SWAP 2026-11（`rest_51001_instrument_not_listed`）
- official_unavailable 4，全部 `404_reason_unknown`（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）

## 檔案 SHA-256

- `funding_delta_v1_11_b3a.csv.gz`：`0950a0d28966560a84b49a896e418f86ea2af8e866f61f6a15a9d321568cbaab`（10,941 B；918 列；解壓 CSV SHA `0b333493458e68bcf044b79e34d32118e22a02a3ee6ee6609938886c3454713d`）
- `funding_null_rate_rows_v1_11_b3a.csv`：`2d9b5d2900837efbc42086e8f0f37a909d34658b5aa2cc27d8fe880b10657021`（0 列）
- `funding_conflicts_v1_11_b3a.json`：`246073a7e1014e7a9d819eff7e6d3f131ba24c5e59229fc28e4b0d4064f425d2`
- `funding_source_months_v1_11_b3a.json`：`0f706f6c56d3f49c18e10dd759eea21e4f0fd6298cf135926b3e826e7d2ac0b3`
- `funding_month_inventory_v1_11_r3.csv`：`7755339784ddfdfd49d339427f97a90f92943e61cfde1192b0b434a140505d1f`
- `funding_delta_v1_11_b3a_manifest.json`：`5e3873e976a22db15a8ddd9afe8564320e250f9dfbae1cc591c9a9ec5a0e6acd`
- `fetch_evidence_v1_11_b3a.jsonl`：`77e37050c1d8cc4330c102fa3f7cf2d2ad2afbb91f61ddb41431bf7798b353bd`
- `build_delta_v1_11_b3a_public.py`：`a5dacbc4cc2179948506baca1bae6c1c5f442170126c6f226b633ae4de9d77a4`
- `CHANGELOG.md`：`3a5c87a09dfa53b5857b330142c7c615d33d815073092a0d4aa70a1023261ccd`

## 剩餘缺口與限制

- pending_check 仍為 3,922 個月，含 RVN-USDT-SWAP 2026-11，以及 slice 2、slice 3。
- 4 個既有官方 ZIP 404 維持 `official_unavailable` / `404_reason_unknown`。
- REST parsed-JSON 限制仍適用於既有 2026-11 REST 證據（本批未重抓 REST）。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線研究資料，未交易、未模擬、未擴窗、未補值。
