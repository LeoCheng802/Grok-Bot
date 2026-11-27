# 執行

此檔是「執行」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 06:12:06
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229117039

<!-- comment_id: 7229117039 -->

[執行] BACKTEST-READINESS-01 v1.8｜純公開資金費 SQLite DB Release `research-data-funding-db-v1`（3 檔全數上線驗畢）

- **角色**：執行
- **研究／事件編號**：`BACKTEST-READINESS-01 v1.8`（對應 Issue #1 `#7229005500`）
- **回報時間**：`2026-11-28 06:12 台北時間（UTC+8）`
- **執行起迄（UTC）**：
  - 純公開表匯出與逐列雜湊核對：`2026-11-27T22:10:09Z` → `2026-11-27T22:11:36Z`
  - GitHub Release 建立與 3 檔上傳驗證：`2026-11-27T22:11:37Z` → `2026-11-27T22:11:41Z`
- **資料截止**：同原凍結 61 分片資金費（`2021-08 ~ 2026-11`，`829,157` 列）

### 1. 已交可讀連結 — 純公開資金費 SQLite DB Release（Prerelease，離線研究專用）
- **Release**：https://github.com/LeoCheng802/Grok-Bot/releases/tag/research-data-funding-db-v1 （`isPrerelease: true`，原 `research-data-ex-usdc-286-v1` 未動、無合併 PR、未部署、`live_approved: false`）
- **3/3 附件上線且 GitHub `sha256` 摘要全數吻合**：
  1. `funding_archive_l1_public_v1.sqlite`（`69,222,400` B，`9d620eed73e90d6fbff54ab06260ecc765cb238f54e7e21df52a020f668cee59`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-funding-db-v1/funding_archive_l1_public_v1.sqlite
  2. `funding_archive_l1_public_manifest_v1.json`（`2,061` B，`71f73949ea5f01830efec0ec966210e53fe1f22581a9aa15bda60299510cb66d`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-funding-db-v1/funding_archive_l1_public_manifest_v1.json
  3. `funding_archive_61shards_manifest_v1.json`（`56,529` B，`a1f2c2f878885159a4bd756ddc4b9333b2ab1d696a49dfa2f3964bf02b2a1a02`）：https://github.com/LeoCheng802/Grok-Bot/releases/download/research-data-funding-db-v1/funding_archive_61shards_manifest_v1.json

### 2. Schema、來源對齊與去識別稽核
- **來源對齊**：原檔（`74,924,032` B，SHA-256 `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc`，完全吻合 61 分片 manifest 所載 `l1_isolated_funding_sqlite_sha256`）含 `fetch_log` 抓取紀錄表；依 v1.8 規範以唯讀匯出純公開單表版本（`journal_mode=DELETE`、`VACUUM`），原凍結檔未修改。
- **僅含 1 張公開表 `funding_archive`**：
  ```sql
  CREATE TABLE funding_archive (
      inst_id TEXT NOT NULL,
      ts_snapped INTEGER NOT NULL,
      ts_raw INTEGER NOT NULL,
      rate REAL NOT NULL,
      source_ym TEXT NOT NULL,
      PRIMARY KEY (inst_id, ts_snapped)
  )
  ```
- **完整性與隱私驗證**：共 `829,157` 列、`270` 檔 `inst_id`（`ts_snapped` 與 `ts_raw` 區間 `1630425600000` ~ `1795737600000` ms），與原庫逐列正規化內容 SHA-256（`daef807a5308807d3cda2962dfc2fdd1f4e1c45c464cabf51b659e6867f3be17`）100% 吻合；二進位與 manifest 掃描零私有表、零帳密、零本機路徑。
- **與增量檔疊加方式**：先載入本 DB（829,157 列），再依 `INSERT OR IGNORE` 疊加 PR #8（head `57c30e539ffe73cb2378bc94a8a5c3432707944e`）之 `funding_delta_missing16_v1_7.csv.gz`（6,748 列）。

### 3. 下一步與治理聲明
- 請 `@復盤` 獨立驗收上述 3 檔線上連結與雜湊。
- `FIB-4H-LONG-V3` 維持 `NO-GO`，全案維持 `live_approved: false`；零歷史回測、零合併、零部署、零下單。
