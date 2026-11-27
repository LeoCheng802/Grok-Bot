# 執行

此檔是「執行」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:56:52
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230527499

<!-- comment_id: 7230527499 -->

[執行] v1.11-b2 r1 D1 修正
【2026-11-28 07:56 台北時間（UTC+8）】

角色：執行
任務：BACKTEST-READINESS-01 v1.11-b2 r1（D1）
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，branch `research/ex-usdc-286-manifests-draft`，未合併、未 force-push）
新 head：`08ff3d5bdb02c8b28ed0170d234bf1f02e8cc0ca`（父 commit `74764f32`）
執行時間（UTC）：2026-11-27T23:52:09Z – 2026-11-27T23:56:28Z

## D1 驗證掃描

全量掃描結果：官方 `funding_rate` 為 literal `None` / null / 空 / 非數字的列，**恰好 2 筆**，沒有更多：
1. OL-USDT-SWAP 2025-10，funding_time 1761292800000 = 2025-10-24T08:00:00.000Z，ZIP SHA `3e989693d34dee5c55d1fe0985056b021dc0b6378e9742a064270b86487e3d34`
2. ZK-USDT-SWAP 2024-06，funding_time 1717660800000 = 2024-06-06T08:00:00.000Z，ZIP SHA `989a6dcfa7d84b6a47cdaa3a2f07c51f71492a9987922a9edbe3fd2b66341925`

掃描範圍：
- `funding_delta_v1_11_b2.csv.gz` 198,356 列：numeric 198,354 + literal_none 2
- 全部 1,279 個官方月 ZIP CSV：174,957 列，literal_none 2（即上述兩筆），其餘皆 numeric
- REST：未篩選 chosen rate 104,740 全部 numeric；視窗內 39,037 全部 numeric

兩個月都不是整月皆為 None（OL 2025-10：1/85；ZK 2024-06：1/54），class 維持 `covered_verified`，並設 `sub_reason=official_rate_null`，不是 plain `covered_verified`。

## 修正

- 從 delta 移除上述 2 列，不補 0、不內插；另存 `funding_null_rate_rows_v1_11_b2_r1.csv`，flag `official_rate_null`（含原始 ts、inst、raw rate 字串、來源 ZIP 與 ZIP SHA）。
- 以既存官方 ZIP / REST 重建（未重新抓取）。
- 新資料夾 `research/funding_delta_v1_11_b2_r1/`（不複製 1,279 個 ZIP）；舊 b2 檔保留，r1 為 D1 後的 supersede 產物。
- 公開產生腳本 `build_delta_v1_11_b2_r1_public.py` 改為拒絕非數字 rate 並寫入 flagged file。

## 計數

- 新 delta：**198,354**（ZIP 169,354 + REST 29,000）
- 8H / 非 8H：120,996 / 77,358
- matched 既有鍵：**15,638 不變**（ZIP 5,601 + REST 10,037）
- conflicts：0；intra-official dups：0
- official numeric unique keys：213,992
- Inventory r2 class 不變：covered_verified 1,364、covered_verified_rest 285、pending_check 5,883、official_unavailable 4；其中 covered_verified|official_rate_null = 2。

## 檔案 SHA-256

- `funding_delta_v1_11_b2_r1.csv.gz`：`ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`（3,035,583 B；解壓 CSV SHA `ba0805e6715a704d247584e721e77ed62bc78524085b97057c47bac95fa1e01c`）
- `funding_null_rate_rows_v1_11_b2_r1.csv`：`6bf5e0aa7db67ee718e57cd5fff558a44d480b6c5ea9eca7f8d1d910582af2e8`
- `funding_conflicts_v1_11_b2_r1.json`：`e1c0bc2bccf31826a531bdf56a14c3fde30c7325b1981bef8b24e446d6fb9f78`
- `funding_month_inventory_v1_11_r2.csv`：`0d8e34a2a1f759086826c025977dfd690af5355a5477183dd8287e2565dfa085`
- `funding_delta_v1_11_b2_r1_manifest.json`：`fc61b31d0eff6614808659d4a94b62636b2ec7dee3ed4346b2215d8e694154ed`
- `build_delta_v1_11_b2_r1_public.py`：`160986a542b9fa5a8c04b40ff438fcc5be3ab5b88b4e30d75951a24331bd957d`
- `CHANGELOG.md`：`b028fa6b261f8518a4ebf66484d83da1f283d42d3e82c3564c6995c52a90936e`

## 剩餘缺口與限制

- pending_check 仍為 5,883 個月，含 RVN-USDT-SWAP 2026-11（official REST code 51001，instrument ID 不存在）。
- 4 個官方 ZIP 404 維持 `official_unavailable` / `404_reason_unknown`（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）。
- REST evidence 存的是解析後的 JSON，不是 raw HTTP bytes（復盤已指出；本次不重新抓取，僅記錄此限制）。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線研究資料修正，未交易、未模擬、未擴窗、未補值。
