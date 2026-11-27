# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 05:26:50
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7228451464

<!-- comment_id: 7228451464 -->

[執行] BACKTEST-READINESS-01 v1.7｜PR #8（3 份 EX_USDC_286 可讀清單）live raw 驗收通過、前後版零差異說明、16 檔資金費官方 API 補齊（本機暫存）與剩餘缺項總表

- **角色**：執行
- **研究／事件編號**：`BACKTEST-READINESS-01 v1.7`（對應 Issue #1 `#7228269328`、`#7228325917`）
- **回報時間**：`2026-11-28 05:27 台北時間（UTC+8）`
- **本輪執行起迄（UTC）**：
  - 前後版清單比對：`2026-11-27T21:19:48Z`
  - 16 檔資金費官方公開 API 補齊：`2026-11-27T21:24:32Z` → `2026-11-27T21:24:55Z`
  - PR #8 live raw 驗收：`2026-11-27T21:26:14Z`

### 1. 已交可讀連結（Open Draft PR #8，未合併、未部署、`main`／PR #6／PR #7 未動）
- **PR**：https://github.com/LeoCheng802/Grok-Bot/pull/8 （分支 `research/ex-usdc-286-manifests-draft`，固定 head `6a9463ce2e32e504cac0ed65c664e72def0b9b6b`，Open Draft）
- **3/3 live raw HTTP 200、位元組／SHA-256 吻合且 `json.loads` 通過**：
  - `research/ex_usdc_286_manifests/cache_v3_manifest.json`：`98,451` B｜`b6b4fde6dc84cc26d72258a38e4b6059ca1fe2fa24bea369f9a792e5e36d71b8`
    - blob: https://github.com/LeoCheng802/Grok-Bot/blob/6a9463ce2e32e504cac0ed65c664e72def0b9b6b/research/ex_usdc_286_manifests/cache_v3_manifest.json
    - raw: https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/6a9463ce2e32e504cac0ed65c664e72def0b9b6b/research/ex_usdc_286_manifests/cache_v3_manifest.json
  - `research/ex_usdc_286_manifests/ex_usdc_286_npz_manifest_v1.json`：`63,016` B｜`cf0ee7b5bf006ccbe5d2ea64162df7a43411d62cd7049d9313afce1bc12d28c5`
    - blob: https://github.com/LeoCheng802/Grok-Bot/blob/6a9463ce2e32e504cac0ed65c664e72def0b9b6b/research/ex_usdc_286_manifests/ex_usdc_286_npz_manifest_v1.json
    - raw: https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/6a9463ce2e32e504cac0ed65c664e72def0b9b6b/research/ex_usdc_286_manifests/ex_usdc_286_npz_manifest_v1.json
  - `research/ex_usdc_286_manifests/ex_usdc_286_release_manifest_v1.json`：`10,401` B｜`07e408e86c06ad19c997e3ca4d166974d10d12bcc6192408322a941fadd987ce`
    - blob: https://github.com/LeoCheng802/Grok-Bot/blob/6a9463ce2e32e504cac0ed65c664e72def0b9b6b/research/ex_usdc_286_manifests/ex_usdc_286_release_manifest_v1.json
    - raw: https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/6a9463ce2e32e504cac0ed65c664e72def0b9b6b/research/ex_usdc_286_manifests/ex_usdc_286_release_manifest_v1.json

### 2. `ex_usdc_286_npz_manifest_v1.json` 前後版大小差異說明（純結構去重，原凍結 NPZ 零變動）
- 前版 `94,531` B（`bb40453c54f5dcddea8b3fc4c36c9f4bf6ad8831a5dd8afd041a13806e9e87a7`）同時包含 `files`（286 筆）與冗餘重複之 `all_files`（287 筆，含 `USDC-USDT-SWAP.npz`）；已交付版 `63,016` B（`cf0ee7b5…28c5`）僅移除冗餘 `all_files` 陣列，並補上 `relative_path`、`npz_keys_verified`、`npz_dtypes_verified` 與 `cache_v3_manifest` 參考欄位。
- 逐筆核對兩版 `files`（286 筆 `(filename, size_bytes, sha256)`）為 **100% 完全一致（0 筆差異）**，286 檔原凍結 NPZ 與 `cache_v3_manifest.json` 均未更動。

### 3. v1.7 最小必要資金費補齊進度（16 檔原 0 列標的，本機已抓完、尚未推上遠端）
- **來源**：OKX 官方公開端點 `https://www.okx.com/api/v5/public/funding-rate-history`（僅補原 61 分片中 0 列之 16 檔，截止 `2026-11-26T12:00:00Z`；原凍結 61 分片完全不動，零補零、零插值）。
- **本機產出（待推上 PR #8 Draft 分支後才算已驗交付）**：
  - `funding_delta_missing16_v1_7.csv.gz`：`6,748` 筆，`91,491` B，SHA-256 `34743db093b5673233693b0bfd4fa020abeb3928f7d4c0c29603c4d4c01311be`（未壓縮 CSV `873,635` B，SHA-256 `e4c322902f66fbc7a6ea5c9f6a6db7b7e4144f75344ceed37e776e2c3caa435e`）
  - `funding_delta_missing16_v1_7_manifest.json`：`7,315` B，SHA-256 `cfe952a932f005beb3600907fe3cfc5cb840bc1a9db01380f4931cbf70d56487`
- **補齊覆蓋與確切殘餘缺口**：12/16 檔降至 `0` 筆 8h 缺口；`BTW`/`QUANT` 各餘 1 筆上市首刻邊界；`DATA`（165 筆）與 `GRVT`（81 筆）觸及 OKX 公開 API 約 90 天保留下限（`2026-08-26T12:00:00Z`），維持缺列記錄。

### 4. 剩餘確切缺項、負責角色與預計交付時間
1. **`EX_USDC_286` 3 卷 `.tar`（~`261.2 MiB`）上架 GitHub Release `research-data-ex-usdc-286-v1`**：負責角色＝77（於 1:1 完成 `gh` 登入授權或網頁建立 Release）＋執行（上傳與驗收）；預計時間＝取決於 77 操作時點，授權後 `3–5` 分鐘內完成。已將最短步驟集中送交 77 1:1 私訊。
2. **`funding_delta_missing16_v1_7.csv.gz`＋manifest 推上 PR #8 Open Draft**：負責角色＝執行；預計時間＝下一批維護 `3–5` 分鐘內完成。
3. **2026-08 以前歷史活躍期資金費缺口**：OKX `/api/v5/public/funding-rate-history` 超過約 90 天返回空陣列，官方月 ZIP CDN 測試回 HTTP 404；目前無官方公開端點可補，維持確切缺口標註、不補零不插值。

- **治理狀態**：`FIB-4H-LONG-V3` 維持 `NO-GO`，所有候選維持 `live_approved: false`；零歷史回測、零合併、零部署、零下單。
