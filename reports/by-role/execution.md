# 執行

此檔是「執行」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 04:36:52
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7227674934

<!-- comment_id: 7227674934 -->

[執行] BACKTEST-READINESS-01 v1.4｜既有 EX_USDC_286 行情快取與資金費盤點、逐檔 Manifest 與交付缺口回報

- **角色**：執行
- **研究／事件編號**：`BACKTEST-READINESS-01 v1.4`（對應 Issue #1 `#7227474241`、`#7227640538`）
- **回報時間**：`2026-11-28 04:37 台北時間（UTC+8）`
- **本輪唯讀盤點起迄（UTC）**：`2026-11-27T20:35:27Z` → `2026-11-27T20:36:05Z`（純唯讀雜湊盤點，零重抓、零補零、零換母體、零歷史回測）
- **資料截止**：`2026-11-26 20:00 CST`（凍結行情快取 `v3.0-public-merged`）；資金費分片至 `2026-11-27T00:00:00Z`

### 1. 既有資金費（已有公開可讀固定分片）
- **公開可讀途徑（`LeoCheng802/Grok-Bot` `main`）**：`research/RESEARCH-LOOP-01/funding_archive_v1/manifest.json`（`56,529` B，SHA-256 `a1f2c2f878885159a4bd756ddc4b9333b2ab1d696a49dfa2f3964bf02b2a1a02`），含 `61` 個月度 `.csv.gz` 分片（`2021-08` ~ `2026-11`，總壓縮 `9,785,235` B，`829,157` 筆，保留 `funding_time_ms` 與 `ts_snapped_ms`）。
- **本機同源對照雜湊**：
  - `funding_archive_l1_isolated.sqlite`：`74,924,032` B，SHA-256 `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc`（`829,157` 筆，`270/286` 幣，`2021-08-31T16:00:00Z` ~ `2026-11-27T00:00:00Z`，與上述 61 分片同源）。
  - `funding_archive_b6_isolated.sqlite`：`69,668,864` B，SHA-256 `dc547b1c6a8031ce730743d542277f11561f95263dd48f22a18017e3f5163c1b`（`779,908` 筆，`264/286` 幣，至 `2026-10-31T12:00:00Z`）。
  - `funding_archive_q38.sqlite`：`54,591,488` B，SHA-256 `bba6558c379f8f6b7adf7329f0d3d688cabb939acb5c7f038cf57c4fe0782970`（`614,463` 筆，`259/286` 幣，至 `2026-10-31T12:00:00Z`）。
- **已確認資金費缺項（不補零、不重抓）**：即使以最完整的 `L1`／公開 61 分片對齊 `EX_USDC_286`，仍有 **16 檔在資金費庫為 0 筆**（`AKE`、`AXIS`、`BTW`、`CASHCAT`、`CNPY`、`CT`、`DATA`、`DGAI`、`DNA`、`FET`、`FLOCK`、`GRVT`、`KII`、`PONS`、`QUANT`、`XDP`，皆 `-USDT-SWAP`）；另有先前回報之活躍期內段缺口與邊界缺口。

### 2. 既有 `EX_USDC_286` 行情快取（凍結 NPZ）與逐檔 Manifest
- **本機凍結快取現況**：共 `287` 檔 `.npz`（`274,350,146` B），排除 `USDC-USDT-SWAP.npz` 後為完整 `EX_USDC_286`（`286` 檔，總計 `273,659,565` B，約 `261.0 MiB`）。
- **原有快取 `manifest.json`**：`98,451` B，SHA-256 `b6b4fde6dc84cc26d72258a38e4b6059ca1fe2fa24bea369f9a792e5e36d71b8`（`data_hash: 91b7ab2f90442e4317a6a7adc3c01148fa3df98c9724abe78d875294d7944cc2`、`total_30m_bars: 13,261,060`、`total_4h_bars: 1,657,490`），**原本不含逐檔 NPZ SHA-256**。
- **本輪新建去識別逐檔 Manifest（暫存本機，未洩漏私人路徑）**：`ex_usdc_286_npz_manifest_v1.json`（`94,531` B，SHA-256 `bb40453c54f5dcddea8b3fc4c36c9f4bf6ad8831a5dd8afd041a13806e9e87a7`），已完整記錄 `EX_USDC_286` 全部 `286` 檔（及 `all_files` 287 檔對照）的檔名、位元組大小與逐檔 SHA-256。

### 3. 缺口與授權交付途徑（待 77 決定）
- **確切缺口**：`EX_USDC_286` 凍結 NPZ 本體（約 `261.0 MiB`）目前僅存在於本機共享磁碟，尚無公開或授權外部下載途徑供 ChatGPT 隔離環境直接拉取。
- **建議授權途徑**：
  1. 經 77 授權後，將凍結 `EX_USDC_286` NPZ 分卷打包（`<100 MiB`/卷）連同 `ex_usdc_286_npz_manifest_v1.json` 與逐卷 SHA-256 上架至 GitHub Release 附件（或授權私有庫 Release），供 ChatGPT 隔離環境唯讀拉取驗 hash。
  2. 由 77 透過私人雲端／離線封包將同一凍結快取與逐檔 manifest 交給 ChatGPT 隔離沙盒。
- **治理狀態**：`FIB-4H-LONG-V3` 維持 `NO-GO`，所有候選維持 `live_approved: false`，無新增回測、無下單／部署。
