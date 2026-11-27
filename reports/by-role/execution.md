# 執行

此檔是「執行」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 04:50:23
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7227889721

<!-- comment_id: 7227889721 -->

[執行] BACKTEST-READINESS-01 v1.5｜EX_USDC_286 分卷打包與潔淨稽核完成、GitHub Release 權限阻礙如實回報、61 分片重建 SQLite 零差異驗證

- **角色**：執行
- **研究／事件編號**：`BACKTEST-READINESS-01 v1.5`（對應 Issue #1 `#7227820407`）
- **回報時間**：`2026-11-28 04:50 台北時間（UTC+8）`
- **本輪執行起迄（UTC）**：`2026-11-27T20:48:08Z` → `2026-11-27T20:49:10Z`（零重抓、零補零、零換母體、零歷史回測、未合併 PR、未部署）
- **資料截止**：`2026-11-26 20:00 CST`（凍結快取 `v3.0-public-merged`）；資金費 61 分片至 `2026-11-27T00:00:00Z`

### 1. `EX_USDC_286`（286 NPZ）潔淨稽核與確定性分卷打包（本機已備妥，尚未上傳 Release）
- **286/286 NPZ 內容稽核通過**：全數通過 `numpy.load(..., allow_pickle=False)`；286 檔欄位聯集嚴格限於 `['d1_ts', 'frt', 'fts', 'ohlc1', 'ohlc30', 'ohlc4', 'ts1', 'ts30', 'ts4']`，資料型別聯集嚴格限於 `['float64', 'int64']`（零字串、零物件陣列、零帳戶／設定／憑證／私人路徑）。原快取 `manifest.json` 掃描亦為零敏感／零私人路徑。
- **確定性 `<95 MiB` 分卷與清單（標準 PAX `.tar`，成員相對路徑 `cache_v3/<SYMBOL>.npz`，uid/gid=0、固定 mtime，本機自述暫存、尚未上線）**：
  - `ex_usdc_286_npz_vol_01_of_03.tar`：`99,594,240` B（`94.98 MiB`，`103` 檔），SHA-256 `82235070b2229dd688946911ba2c5ec3e97441b30882d416bda313840f12a5d7`
  - `ex_usdc_286_npz_vol_02_of_03.tar`：`98,682,880` B（`94.11 MiB`，`110` 檔），SHA-256 `ec910a3e76a402bcfacc9167c860fe84a86b580b497079b99c9a69bab3ca3495`
  - `ex_usdc_286_npz_vol_03_of_03.tar`：`75,622,400` B（`72.12 MiB`，`73` 檔），SHA-256 `6f80e79931cc9fa5d9ffad330e95eb91354e04af910fbf685ab84c4e1b77d06f`
  - `cache_v3_manifest.json`（原快取清單複本）：`98,451` B，SHA-256 `b6b4fde6dc84cc26d72258a38e4b6059ca1fe2fa24bea369f9a792e5e36d71b8`
  - `ex_usdc_286_npz_manifest_v1.json`（逐檔 286 NPZ 大小／SHA-256）：`63,016` B，SHA-256 `cf0ee7b5bf006ccbe5d2ea64162df7a43411d62cd7049d9313afce1bc12d28c5`
  - `ex_usdc_286_release_manifest_v1.json`（逐卷大小／SHA-256＋各卷完整檔名清單，建議 tag `research-data-ex-usdc-286-v1`）：`10,401` B，SHA-256 `07e408e86c06ad19c997e3ca4d166974d10d12bcc6192408322a941fadd987ce`
- **GitHub Release 上傳阻礙（如實回報、不繞過）**：
  - **被拒／缺口動作**：建立 GitHub Release 與上傳大型二進位 Release 附件（~`261.2 MiB`）。
  - **實際工具狀態**：GitHub 連接器僅提供唯讀 Release 查詢（`list_releases` / `get_latest_release` / `get_release_by_tag`），無建立 Release 或上傳資產工具；本機 `gh auth status` 回報 `You are not logged into any GitHub hosts`。依規範不在群組發起 `gh auth login`，亦不把大型 `.tar` 塞入 Git 歷史。
  - **解除條件**：需由 77 於 1:1 對話完成 `gh` 登入授權（或由 77 直接於 `LeoCheng802/Grok-Bot` 建立 `research-data-ex-usdc-286-v1` Release 並掛載上述 6 檔）。如 ChatGPT 需先取得可讀文字版 3 份 manifest JSON，本端可另以獨立 Draft 分支先交純文字清單。

### 2. 公開 61 份資金費分片 → 重建 Runner 所需 SQLite 之確切 Schema、映射與零差異驗證
- **來源**：`LeoCheng802/Grok-Bot` `main` 既公開之 `research/RESEARCH-LOOP-01/funding_archive_v1/manifest.json` 與 `shards/funding_YYYY-MM.csv.gz`（61 檔，`2021-08` ~ `2026-11`，無須重傳；目前公開庫尚無現成重建腳本，以下為完整可重現規格）。
- **確切目標 SQLite Schema（與各 runner 讀取介面完全一致）**：
  ```sql
  CREATE TABLE funding_archive (
      inst_id TEXT NOT NULL,
      ts_snapped INTEGER NOT NULL,
      ts_raw INTEGER NOT NULL,
      rate REAL NOT NULL,
      source_ym TEXT NOT NULL,
      PRIMARY KEY (inst_id, ts_snapped)
  );
  ```
  （註：原庫另含 `fetch_log` 表供當初抓取紀錄，所有回測 runner 僅查詢 `SELECT inst_id, ts_snapped, ts_raw, rate FROM funding_archive`，無須 `fetch_log`。）
- **CSV 分片欄位 → SQLite 欄位映射**（分片表頭：`inst_id,funding_time_ms,funding_time_utc,ts_snapped_ms,ts_snapped_utc,snap_offset_ms,funding_rate,is_8h_grid,source_ym`）：
  - `inst_id` → `inst_id` (`TEXT`)
  - `int(ts_snapped_ms)` → `ts_snapped` (`INTEGER`)
  - `int(funding_time_ms)` → `ts_raw` (`INTEGER`)
  - `float(funding_rate)` → `rate` (`REAL`)
  - `source_ym` → `source_ym` (`TEXT`)
- **本輪實測重建零差異驗證**：以標準庫 Python 依檔名排序讀取全 61 檔 `.csv.gz` 寫入臨時 SQLite，實測匯入 `829,157` 筆，與本機原 `funding_archive_l1_isolated.sqlite` 逐列比對（雙向 `EXCEPT`）結果為 **`0` 筆差異**（重建檔大小 `72,114,176` B，SHA-256 `05206d201085b262e78b97ec03f16036a70596b6b1a30b7fee19955f573d2c00`；`EX_USDC_286` 中 16 檔在 61 分片原即 0 筆，維持缺列、不補零、不刪標的）。

### 3. 治理狀態
- `FIB-4H-LONG-V3` 維持 `NO-GO`，所有候選維持 `live_approved: false`；零回測、零合併、零部署、零下單。
