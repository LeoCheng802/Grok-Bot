# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 08:03:49
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230617170

<!-- comment_id: 7230617170 -->

[執行] v1.11-b2 r1 D1 修正（v1.16）
【2026-11-28 08:03 台北時間（UTC+8）】

角色：執行
任務：BACKTEST-READINESS-01 v1.11-b2 r1 D1 追討（v1.16 及補充 #7230544291）
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，branch `research/ex-usdc-286-manifests-draft`，未合併、未 force-push）
先前已推的 r1：`08ff3d5bdb02c8b28ed0170d234bf1f02e8cc0ca`（Issue 評論 #7230527499）
新 head：`928beeb6cfeaa9fc686f0bdfe44154abba6e14ec`
執行時間（UTC）：2026-11-27T23:57:43Z – 2026-11-28T00:03:12Z

本次為追討 commit，未重建、未重抓 official 資料。r1 delta 仍為 **198,354** 列，SHA-256 `ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86` 不變。

## 1. 費率拒絕規則與驗證掃描

公開產生腳本現在明確拒絕 empty、literal `None`、`NaN`、`Inf`/`-Inf` 及任何非有限／非數值 rate：須 `float(text)` **並** `math.isfinite`（大小寫不敏，含 `+nan`/`-nan`/`Infinity`）。拒絕列寫入 flagged 檔，保留來源 ZIP 檔名與 SHA。flag 工分：
- `official_rate_null`：empty / literal None / null
- `official_rate_nonfinite`：NaN / Inf / -Inf（與 null 區分）

受影響月份保留 class，但標為未完整（`complete=false`，對應 `sub_reason`）。不補 0、不內插。

全量掃描（新規則，未重抓）拒絕計數 by type：
- literal_none：**2**（flag official_rate_null）— OL-USDT-SWAP 2025-10（2025-10-24T08:00:00.000Z，ZIP SHA `3e989693d34dee5c55d1fe0985056b021dc0b6378e9742a064270b86487e3d34`）、ZK-USDT-SWAP 2024-06（2024-06-06T08:00:00.000Z，ZIP SHA `989a6dcfa7d84b6a47cdaa3a2f07c51f71492a9987922a9edbe3fd2b66341925`）；兩月都非整月皆 None（2/85、1/54）
- empty：0
- nan：0
- inf / neg_inf：0
- 其他 non-numeric：0

掃描範圍：r1 delta 198,354 列全為有限數值；1,279 個官方 ZIP CSV 174,957 列（174,955 finite + 2 literal None）；REST 未篩選 chosen / realizedRate / fundingRate 104,740 及視窗內 39,037 全為有限數值。有效新列仍為 **198,354**（matched 15,638 不變，conflicts 0；8H 120,996 / 非 8H 77,358）。

## 2. rate_status 合成測試（v1.16 補充）

`test_rate_status_v1_11_b2_r2.py` （輸出已並存 `test_rate_status_v1_11_b2_r2_output.txt`）對照已發佈 r1（08ff3d5）與新函式。標記：`''`, `None`, `none`, `NaN`, `nan`, `-nan`, `+nan`, `inf`, `-inf`, `Inf`, `Infinity`, `-Infinity`, `1e-4`, `-0.0001`。

- OLD 誤將以下非有限 token 當成 numeric：`-nan`, `+nan`, `inf`, `-inf`, `Inf`, `Infinity`, `-Infinity`（`float()` 成功且未檢 isfinite）。OLD 已經拒絕 `''`、`None`/`none`，以及經 `.lower()=='nan'` 的 `nan`/`NaN`。
- NEW 拒絕所有非有限 token，flag `official_rate_nonfinite`；empty/None 為 `official_rate_null`；`1e-4` 與 `-0.0001` 仍接受。
- RESULT：**PASS**。

## 3. REST evidence 形式

已在 manifest / `rest_evidence_form.json` 標示：`evidence_form=parsed_json`，`raw_bytes_saved=false`。已存 REST 內容為解析後 JSON；復用時 `response_sha256` 為 `json.dumps(parsed, separators=(',', ':'))` 的 SHA-256，不是原始 raw HTTP bytes。fetch evidence log 在請求時曾對 HTTP body 做集，之後僅保留解析後物件，raw bytes 已丟棄。未重新抓取已驗證資料。

## 4. RVN-USDT-SWAP 2026-11

class 仍為 `pending_check`；`sub_reason` 改為 `rest_51001_instrument_not_listed`（原 `rest_error`）。已將存檔的 official REST 51001 回應附於 `rvn_usdt_swap_2026_11_rest_51001_evidence.json`（HTTP 200，code 51001，msg 「Instrument ID, Instrument ID code, or Spread ID doesn't exist.」；response_sha256 `230e2c076484f09587d279fd86ac17dce541f4acec83ffd9d40e60daf729f491`，97 B compact JSON）。待 CST 2026-11 官方月 ZIP 公佈後再檢。不補 0；RVN 留在 EX_USDC_286 宇宙。

## Inventory r2 計數（class 不變）

- covered_verified 1,364（其中 2 個 complete=false、sub_reason official_rate_null：OL 2025-10、ZK 2024-06；不是 plain covered_verified）
- covered_verified_rest 285
- pending_check 5,883（含 RVN 2026-11）
- official_unavailable 4，全部 `404_reason_unknown`（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）

## 檔案 SHA-256

- `funding_delta_v1_11_b2_r1.csv.gz`（不變）：`ac3890c5de16b7254ef3b51afbb9af7826467a3c14fe193ce3a04ddc583d2e86`（3,035,583 B）
- `funding_null_rate_rows_v1_11_b2_r1.csv`：`5dd6478409eba0a5e7644394a0e71ec366d9c786469b0e6e788b7f88a7035e2f`
- `funding_conflicts_v1_11_b2_r1.json`（不變）：`e1c0bc2bccf31826a531bdf56a14c3fde30c7325b1981bef8b24e446d6fb9f78`
- `funding_month_inventory_v1_11_r2.csv`：`1634a4d449ae7b239920be6ff0a8fa72ba305ee8c53ad4d4e09cfa56f229b59e`
- `funding_delta_v1_11_b2_r1_manifest.json`：`e0e95b6a61882855066ac424aac5f49274a946e6f066ec6d7a92853fbc6bd68d`
- `build_delta_v1_11_b2_r1_public.py`：`1e09dbcae0e37cd1968532725a087f315ed5cae5f80b4714f62296598bb17258`
- `CHANGELOG.md`：`509597f253d06a39d1803d2b4d2e404a5e0f0e7fb13b5d5b0ab057c3744ccb8a`
- `rest_evidence_form.json`：`5ea53c523001070de522c5db4f360f46a85e67944f67d84e4cdaffa0e75bfdf5`
- `rvn_usdt_swap_2026_11_rest_51001_evidence.json`：`c74b71d80169355980f2c5f45f46a96996d1b77e1e7e8ea25ad1ed8fbedd92bd`
- `test_rate_status_v1_11_b2_r2.py`：`0fb9b4b9cb401f9184f4a8c8b27ae2c9ede2d28b70383a7baa4eec3f9abb45bf`
- `test_rate_status_v1_11_b2_r2_output.txt`：`b029d28c3bab978e02d45c444a2621f251bb6ff0f0860d2310fd3d5f98691cd8`

## 剩餘缺口與限制

- pending_check 仍為 5,883 個月，含 RVN-USDT-SWAP 2026-11（official REST code 51001）。
- 4 個官方 ZIP 404 維持 `official_unavailable` / `404_reason_unknown`。
- REST evidence 存的是解析後 JSON，不是 raw HTTP bytes（已標示；evidence_form=parsed_json，raw_bytes_saved=false；未重抓）。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線研究資料修正，未交易、未模擬、未擴窗、未補值。
