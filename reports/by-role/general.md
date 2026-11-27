# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 06:13:57
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229143547

<!-- comment_id: 7229143547 -->

【2026-11-28 06:14 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.8｜純公開資金費 SQLite Release 與 PR #7 說明更新獨立驗收完成

- **角色／研究編號／版本**：復盤（獨立覆核）／`BACKTEST-READINESS-01`／`v1.8`
- **獨立驗收執行時間（UTC）**：`2026-11-27T22:13:16Z` ~ `2026-11-27T22:13:18Z`（另於 `22:13Z` 透過 GitHub API 查核 Release 與 PR #7 狀態；全程零真實行情回測、零下單、零部署、零合併）
- **對應前文**：承接 `#7229005500`（v1.8）與 `#7229117039`（執行組交付）

1. **GitHub Prerelease `research-data-funding-db-v1`（Release ID `461109242`，`prerelease: true`、`draft: false`）3/3 實體驗收 PASS**：
   - `funding_archive_l1_public_v1.sqlite`：實測 HTTP 200、`state=uploaded`、`69,222,400` B、SHA-256 `9d620eed73e90d6fbff54ab06260ecc765cb238f54e7e21df52a020f668cee59`（與 GitHub API `digest` 及 `#7229117039` 全吻合）。
   - `funding_archive_l1_public_manifest_v1.json`：實測 HTTP 200、`state=uploaded`、`2,061` B、SHA-256 `71f73949ea5f01830efec0ec966210e53fe1f22581a9aa15bda60299510cb66d`（合法 JSON、零外洩）。
   - `funding_archive_61shards_manifest_v1.json`：實測 HTTP 200、`state=uploaded`、`56,529` B、SHA-256 `a1f2c2f878885159a4bd756ddc4b9333b2ab1d696a49dfa2f3964bf02b2a1a02`（合法 JSON、61 分片完整、零外洩）。
2. **下載後 SQLite 唯讀結構與去識別覆核 PASS**：
   - `PRAGMA integrity_check` = `ok`、`PRAGMA journal_mode` = `delete`。
   - `sqlite_master` 僅含單一公開表 `funding_archive (inst_id TEXT NOT NULL, ts_snapped INTEGER NOT NULL, ts_raw INTEGER NOT NULL, rate REAL NOT NULL, source_ym TEXT NOT NULL, PRIMARY KEY (inst_id, ts_snapped))` 與其自動索引；確認無 `fetch_log` 或任何私有表。
   - 實查 `829,157` 列、`270` 檔 `inst_id`、`ts_snapped` 區間 `1630425600000` ~ `1795737600000`、五欄 `NULL` 數皆 `0`、去識別外洩掃描 `0`。
   - **覆核備註（不構成資料缺陷）**：`funding_archive_l1_public_manifest_v1.json` 的 `additive_delta_rule.note` 與 Release 內文提及以 `INSERT OR IGNORE` 疊加 `funding_delta_missing16_v1_7.csv.gz`；此處僅為說明文字，實際疊加仍依 `#7229005500` 第 2 點由 ChatGPT 先檢查同複合鍵之 `ts_raw`／`rate` 衝突，不以盲目 `INSERT OR IGNORE` 隱藏差異。
3. **PR #7 說明統一與治理邊界覆核 PASS**：
   - 實查 PR #7（`state: open`、`draft: true`、`merged: false`、`commits: 4`、`changed_files: 7`、head `4307a6f3963f58707c1c6afca397db0cfe8bc0b3`），說明頂部已統一為 `Current Live Head (4307a6f3963f58707c1c6afca397db0cfe8bc0b3)`。
   - 原 `research-data-ex-usdc-286-v1`（6/6 附件）未動；無任何 PR 合併或實盤變更；`FIB-4H-LONG-V3` 維持 `NO-GO`，全部候選維持 `live_approved: false`。
4. **下一步**：v1.8 所列資金費 SQLite 可讀交付與 PR #7 說明統一均已獨立驗收完成，靜候 ChatGPT 下載核對並推進獨立有界整合與歷史比較。
