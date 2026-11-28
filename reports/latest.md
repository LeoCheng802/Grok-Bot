# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 09:02:13
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7231372486

<!-- comment_id: 7231372486 -->

[執行] v1.11-b3c 待核月份第 3 批（末批）
【2026-11-28 09:02 台北時間（UTC+8）】

角色：執行
任務：BACKTEST-READINESS-01 v1.11-b3c（pending_check 第 3/3 批，末批）
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，branch `research/ex-usdc-286-manifests-draft`，未合併、未 force-push；b3b head `363dc665` 已釘在本批推送之前）
新 head：`f1280dc41d8409ed856fd41c339ff095a67ebe74`（父 commit `363dc665e1b3d45c3c85bbdd808a3fc834c36c47`）
執行時間（UTC）：2026-11-28T00:47:26Z – 2026-11-28T00:58:48Z

本批開始前 pending_check 為 **1,961**（1,960 個剩餘切片月份 + RVN-USDT-SWAP 2026-11）。4 個 `official_unavailable` / `404_reason_unknown` 另外列出，不計入這 1,961。沿用 b3b 公開生成器規則（`load_existing` 去重／衝突普查；`complete=true` 僅當該月任一類衝突為 0）。比對基準新增 v1.11-b3b delta（1,084 列，SHA `f7b139a597e0257283a1c32dd632d6ef39a5822c15a03c929d1d433b53b66b9e`）。只新增已核為實際官方結算紀錄的鍵。未重建既有 delta。已驗證的 5,286 個 covered_verified ZIP 未重抓。不補 0、不內插、不改宇宙與視窗。以下計數與 manifest / flagged / conflicts / 各批 delta 檔一致。本批自跑掃描是團隊執行證據，不是 ChatGPT runtime 認證。

## 切片定義

宇宙：inventory r2 class=`pending_check` 排除 RVN-USDT-SWAP 2026-11，共 5,882 個月，按 `(inst_id, month_cst)` 排序。`divmod(5882, 3)` → 1,961 / 1,961 / 1,960。切片切點與 v1.11-b3a manifest 相同，由 inventory r2 重建，不從 r3/r4 剩餘 pending_check 重切。本批只處理 slice 3：index [3922, 5882)，PENDLE-USDT-SWAP 2026-02 … ZRX-USDT-SWAP 2026-08。

## 抓取與比對

Baseline census：frozen 829,157；v1.7 6,748；v1.9 174；v1.10 10,633；v1.11_b1 609；v1.11_b2_r1 198,354；v1.11_b3a 918；v1.11_b3b 1,084（合計 1,047,677 列）。unique keys 1,047,677；clean keys 1,047,677；identical multi-source 去重 0；existing-input conflict keys 0。r4 `complete=true` 翻轉：0。

- fetched 1,960；HTTP 200：1,960；HTTP 404：0；HTTP other：0；skipped already-verified：0
- official numeric rows：260,643（unique keys 260,643；official-ZIP-internal conflicts 0；official identical dups 0）
- matched：258,781
- new：**1,862**（8H 934 / 非 8H 928）
- conflicts：official-vs-existing 0；existing-input-internal 0；official-ZIP-internal 0
- flagged：0（literal_none 0，empty 0，nan 0，inf 0，neg_inf 0，other non-numeric 0；official_rate_null 0，official_rate_nonfinite 0）

slice 3 的 1,960 個月在 inventory r4 均已有 existing_rows>0（16–726）；僅 1,862 鍵為未記錄新列。無 429 限流、無 403。

## Inventory r5（全表 7,536 列）

`complete=true` 僅表示「通過本批來源與比對範圍」：已取得官方月 ZIP，其中所有有限數值官方鍵已逐鍵比對，且該月任一類衝突為 0。不是全期或跨頻率驗證。`complete=false` 表示本批官方 ZIP 含 flagged 非數值／非有限 rate（已知未完整）。`blank` = 未知。只有 true 表示 complete（限上述範圍）。

- class：covered_verified 7,246；covered_verified_rest 285；pending_check 1；official_unavailable 4
- complete：true 7,529；false 2；blank 5
- complete=true 7,529 = covered_verified 7,244（既有 5,284 + 本批 1,960）+ covered_verified_rest 285
- complete=false 2 = OL-USDT-SWAP 2025-10、ZK-USDT-SWAP 2024-06（既有 official_rate_null；分別 1/85 與 1/54 literal None）
- pending_check 1 = RVN-USDT-SWAP 2026-11（`rest_51001_instrument_not_listed`）
- official_unavailable 4，全部 `404_reason_unknown`（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）
- blank 5 = pending_check 1 + official_unavailable 4
- 本批新列為 covered_verified 且 complete=true 的 1,960 個月，正是 slice 3：PENDLE-USDT-SWAP 2026-02 … ZRX-USDT-SWAP 2026-08

## 累計（v1.11-b1 + b2_r1 + b3a + b3b + b3c）

各批 delta 檔實數（新官方鍵）：

- v1.11-b1：609（8H 396 / 非 8H 213）
- v1.11-b2 r1：198,354（8H 120,996 / 非 8H 77,358）
- v1.11-b3a：918（8H 469 / 非 8H 449）
- v1.11-b3b：1,084（8H 542 / 非 8H 542）
- v1.11-b3c：1,862（8H 934 / 非 8H 928）
- 合計：**202,827**（8H **123,337** / 非 8H **79,490**）

五批衝突合計：official-vs-existing 0；existing-input-internal 0；official-ZIP-internal 0。b2 發現的 2 筆官方 literal `None` 列是 flagged `official_rate_null`，不是衝突，inventory 維持 complete=false。Inventory class / complete 即以 r5 上列為準。

## 檔案 SHA-256

- `funding_delta_v1_11_b3c.csv.gz`：`8f49f40fa0d47297ab7f4d3b5d21a7b60177f1936079519eccba05ab7137cfda`（23,008 B；1,862 列；解壓 CSV SHA `e99fee683c1736e6b867c6302813e61112e27ec18f27e275f2d38c6a87d6faac`，392,828 B）
- `funding_null_rate_rows_v1_11_b3c.csv`：`2d9b5d2900837efbc42086e8f0f37a909d34658b5aa2cc27d8fe880b10657021`（0 列）
- `funding_conflicts_v1_11_b3c.json`：`978a6187bac36767191a4af9626e30ccca51a030427686d87689ef16fd76b97c`
- `funding_source_months_v1_11_b3c.json`：`6f77060a4b13bc7e637b93d5ecc3681932f936953f06e0a515d8925433393d34`
- `funding_month_inventory_v1_11_r5.csv`：`27361ccc0aeec209979965d72fa235f8fb80818b2c9c813927f80469cf6603f9`
- `funding_delta_v1_11_b3c_manifest.json`：`eaa3dde246eb723cb91ba5fc855e7d81c3a392374ee4f4061365f90219f07ddd`
- `fetch_evidence_v1_11_b3c.jsonl`：`39935b93d9e53da7c1ae9d70f82c4318ebfac5c1d8cee42b9720c9d499768fd0`
- `build_delta_v1_11_b3c_public.py`：`f0474c74fa61487e10769f2919966f897715ebaf12ea164572f7f4dd78ba6eae`
- `CHANGELOG.md`：`4de3fdb4aeb5e710b78c5a07613da81e5b144d64714583d6e83acb2314f6ee44`

## 剩餘缺口與限制

三個官方月 ZIP 切片（5,882 個月）已完成。仍未知或未完整者：

- OL-USDT-SWAP 2025-10、ZK-USDT-SWAP 2024-06：各 1 筆官方 literal `None` rate（1/85 與 1/54）；`complete=false` / `official_rate_null`。不補 0。
- RVN-USDT-SWAP 2026-11 維持 `pending_check` / `rest_51001_instrument_not_listed`。待 CST 2026-11 官方月 ZIP 公布後再核。仍留在宇宙內，不補 0。
- 4 個既有官方 ZIP 404 維持 `official_unavailable` / `404_reason_unknown`（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09），原因仍未知。
- 全期非 8H 結算分母（1H/4H 合約每個月份的預期結算筆數）尚未建立。本庫存的 `complete=true` 不是全期或跨頻率驗證。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線研究資料，未交易、未模擬、未擴窗、未補值。
