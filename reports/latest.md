# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 05:44:05
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7228706966

<!-- comment_id: 7228706966 -->

[執行] BACKTEST-READINESS-01 v1.7｜GitHub Release `research-data-ex-usdc-286-v1`（6 檔全數上線驗畢）＋PR #8 新 head `57c30e53…`（16 檔官方資金費增量檔上線驗畢）

- **角色**：執行
- **研究／事件編號**：`BACKTEST-READINESS-01 v1.7`（對應 Issue #1 `#7228325917`、`#7228451464`）
- **回報時間**：`2026-11-28 05:44 台北時間（UTC+8）`
- **本輪執行起迄（UTC）**：
  - GitHub Release 建立與 6 檔上傳驗證：`2026-11-27T21:43:01Z` → `2026-11-27T21:43:07Z`
  - PR #8 增量資金費推送與 live raw 驗證：`2026-11-27T21:43:26Z` → `2026-11-27T21:43:28Z`
- **資料截止**：凍結行情 `2026-11-26 20:00 CST`；資金費增量檔截止 `2026-11-26T12:00:00Z`

### 1. 已交可讀連結 — `EX_USDC_286` 凍結行情快取 Release（286 NPZ，Prerelease，離線研究專用）
- **Release**：https://github.com/LeoCheng802/Grok-Bot/releases/tag/research-data-ex-usdc-286-v1 （`isPrerelease: true`，未合併 PR、未部署、`live_approved: false`）
- **6/6 附件上線且 GitHub `sha256` 摘要全數吻合**：
  1. `ex_usdc_286_npz_vol_01_of_03.tar`（`99,594,240` B，`103` 檔，`82235070b2229dd688946911ba2c5ec3e97441b30882d416bda313840f12a5d7`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-ex-usdc-286-v1/ex_usdc_286_npz_vol_01_of_03.tar
  2. `ex_usdc_286_npz_vol_02_of_03.tar`（`98,682,880` B，`110` 檔，`ec910a3e76a402bcfacc9167c860fe84a86b580b497079b99c9a69bab3ca3495`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-ex-usdc-286-v1/ex_usdc_286_npz_vol_02_of_03.tar
  3. `ex_usdc_286_npz_vol_03_of_03.tar`（`75,622,400` B，`73` 檔，`6f80e79931cc9fa5d9ffad330e95eb91354e04af910fbf685ab84c4e1b77d06f`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-ex-usdc-286-v1/ex_usdc_286_npz_vol_03_of_03.tar
  4. `cache_v3_manifest.json`（`98,451` B，`b6b4fde6dc84cc26d72258a38e4b6059ca1fe2fa24bea369f9a792e5e36d71b8`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-ex-usdc-286-v1/cache_v3_manifest.json
  5. `ex_usdc_286_npz_manifest_v1.json`（`63,016` B，`cf0ee7b5bf006ccbe5d2ea64162df7a43411d62cd7049d9313afce1bc12d28c5`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-ex-usdc-286-v1/ex_usdc_286_npz_manifest_v1.json
  6. `ex_usdc_286_release_manifest_v1.json`（`10,401` B，`07e408e86c06ad19c997e3ca4d166974d10d12bcc6192408322a941fadd987ce`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-ex-usdc-286-v1/ex_usdc_286_release_manifest_v1.json
- **還原方式**：於同一工作目錄執行 `tar -xf ex_usdc_286_npz_vol_01_of_03.tar && tar -xf ex_usdc_286_npz_vol_02_of_03.tar && tar -xf ex_usdc_286_npz_vol_03_of_03.tar`，即得完整 `cache_v3/<SYMBOL>.npz`（286 檔），直接以 `ex_usdc_286_npz_manifest_v1.json` 驗逐檔 SHA-256。

### 2. 已交可讀連結 — 16 檔原 0 列標的官方公開資金費增量檔（PR #8 Open Draft 新 head）
- **PR**：https://github.com/LeoCheng802/Grok-Bot/pull/8 （分支 `research/ex-usdc-286-manifests-draft`，新 head `57c30e539ffe73cb2378bc94a8a5c3432707944e`，維持 Open Draft、未合併、`main`／PR #6／PR #7 未動）
- **2/2 live raw HTTP 200 且位元組／SHA-256 吻合**（保留原凍結 61 分片不動，先載原 61 分片再 `INSERT OR IGNORE` 疊加本增量檔）：
  - `research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz`（`91,491` B，`6,748` 筆，`34743db093b5673233693b0bfd4fa020abeb3928f7d4c0c29603c4d4c01311be`）：
    - blob: https://github.com/LeoCheng802/Grok-Bot/blob/57c30e539ffe73cb2378bc94a8a5c3432707944e/research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz
    - raw: https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/57c30e539ffe73cb2378bc94a8a5c3432707944e/research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz
  - `research/funding_delta_v1_7/funding_delta_missing16_v1_7_manifest.json`（`7,315` B，`cfe952a932f005beb3600907fe3cfc5cb840bc1a9db01380f4931cbf70d56487`）：
    - blob: https://github.com/LeoCheng802/Grok-Bot/blob/57c30e539ffe73cb2378bc94a8a5c3432707944e/research/funding_delta_v1_7/funding_delta_missing16_v1_7_manifest.json
    - raw: https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/57c30e539ffe73cb2378bc94a8a5c3432707944e/research/funding_delta_v1_7/funding_delta_missing16_v1_7_manifest.json

### 3. 執行組剩餘確切缺項
- 執行組於 `v1.7` 負責之資料交付項目（286 NPZ 三卷＋三清單 Release、16 檔官方資金費增量檔）已全數上線並通過線上雜湊驗證。
- 僅餘「2026-08 以前歷史資金費活躍期缺口」因 OKX 公開 API 90 天保留上限且月 ZIP CDN 回 404，無官方公開端點可補，維持確切缺口記錄（不補零、不插值、不刪標的）。
- `FIB-4H-LONG-V3` 維持 `NO-GO`，所有候選維持 `live_approved: false`；零歷史回測、零合併、零部署、零下單。
