# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 05:45:51
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7228733014

<!-- comment_id: 7228733014 -->

【2026-11-28 05:46 台北時間（UTC+8）】
[復盤] `BACKTEST-READINESS-01 v1.7`｜獨立覆核 Release `research-data-ex-usdc-286-v1`（6/6 附件）與 PR #8 新 head `57c30e539ffe73cb2378bc94a8a5c3432707944e`（增量資金費 2/2 檔）通過

- **獨立覆核起迄（UTC）**：`2026-11-27T21:45:14Z` → `2026-11-27T21:45:40Z`（僅遠端唯讀 API／HEAD／gzip／JSON 驗證與去識別掃描；零歷史回測、零合併、零部署、零交易）。
- **已交可讀連結（1）GitHub Prerelease `research-data-ex-usdc-286-v1`（`prerelease=true`、`draft=false`、6/6 附件 `state=uploaded`、HEAD 全數 HTTP 200 且 `Content-Length` 與 GitHub API `digest` 全吻合）**：
  1. `ex_usdc_286_npz_vol_01_of_03.tar`：`99,594,240` B｜`82235070b2229dd688946911ba2c5ec3e97441b30882d416bda313840f12a5d7`
  2. `ex_usdc_286_npz_vol_02_of_03.tar`：`98,682,880` B｜`ec910a3e76a402bcfacc9167c860fe84a86b580b497079b99c9a69bab3ca3495`
  3. `ex_usdc_286_npz_vol_03_of_03.tar`：`75,622,400` B｜`6f80e79931cc9fa5d9ffad330e95eb91354e04af910fbf685ab84c4e1b77d06f`
  4. `cache_v3_manifest.json`：`98,451` B｜`b6b4fde6dc84cc26d72258a38e4b6059ca1fe2fa24bea369f9a792e5e36d71b8`
  5. `ex_usdc_286_npz_manifest_v1.json`：`63,016` B｜`cf0ee7b5bf006ccbe5d2ea64162df7a43411d62cd7049d9313afce1bc12d28c5`
  6. `ex_usdc_286_release_manifest_v1.json`：`10,401` B｜`07e408e86c06ad19c997e3ca4d166974d10d12bcc6192408322a941fadd987ce`
- **已交可讀連結（2）PR #8 新固定 head `57c30e539ffe73cb2378bc94a8a5c3432707944e`（`state=open`、`draft=true`、`merged=false`、`commits=2`、`changed_files=5`、`main` 未動）**：
  1. `research/funding_delta_v1_7/funding_delta_missing16_v1_7.csv.gz`：HTTP 200、`91,491` B｜SHA-256 `34743db093b5673233693b0bfd4fa020abeb3928f7d4c0c29603c4d4c01311be`（實測解壓通過，`6,748` 列、涵蓋全 `16` 檔標的、欄位 `inst_id, funding_time_ms, funding_time_utc, ts_snapped_ms, ts_snapped_utc, snap_offset_ms, funding_rate, is_8h_grid, source_ym`、零外洩）。
  2. `research/funding_delta_v1_7/funding_delta_missing16_v1_7_manifest.json`：HTTP 200、`7,315` B｜SHA-256 `cfe952a932f005beb3600907fe3cfc5cb840bc1a9db01380f4931cbf70d56487`（JSON 可解析、零外洩）。
- **剩餘確切缺項／負責角色／預估時間**：
  1. **PR #7 主入口接線 4 檔新 commit 推送**（本機已過哨兵回歸，線上仍為舊 head `d8855199…`）｜負責：策略組＋77（1:1 觸發雲端代理）｜觸發後 `3–5` 分鐘，落地後由復盤獨立覆核。
  2. **2026-08 以前歷史資金費活躍期缺口**（OKX API 90 天限制且月 ZIP CDN 回 404，無官方公開端點可補）｜維持確切缺口記錄，不補零、不刪標的。
- **治理邊界**：PR #6／#7／#8 維持 Open Draft，不合併、不部署、不關閉 Issue #1；`FIB-4H-LONG-V3` 維持 `NO-GO`，所有候選維持 `live_approved: false`。
