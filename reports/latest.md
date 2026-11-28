# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 20:40:31
- **角色**: 執行
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7239389862

<!-- comment_id: 7239389862 -->

[執行] v1.23 來源清單與非 8H 完整性未知項
【2026-11-28 20:40 台北時間（UTC+8）】

角色：執行
任務：BACKTEST-READINESS-01 v1.23（來源清單與非 8H 完整性未知項，離線彙編）
倉庫：LeoCheng802/Grok-Bot
PR：#8（draft，branch `research/ex-usdc-286-manifests-draft`，未合併、未 force-push）
新 head：`3280b7a6975d272c24238476af80820c9668b6c7`（父 commit `f1280dc41d8409ed856fd41c339ff095a67ebe74`）
執行時間（UTC）：2026-11-28T12:28:11Z – 2026-11-28T12:38:51Z

離線彙編：只讀已保存的官方月 ZIP、2026-11 REST parsed JSON、inventory r5、各批 manifest／evidence，以及 pinned frozen DB（mode=ro）。未重抓任何已驗證來源，未跑回測，未補 0，未改宇宙與視窗。本分支上未找到等價的來源清單或非 8H 完整性未知項清單（已搜尋後新編，不重複既有 manifest）。以下計數與 manifest／CSV 檔一致。本編自跑掃描是團隊執行證據，不是 ChatGPT runtime 認證。

本批並依 復盤 Issue #1 評論 https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7239320542 第 5 點，在 `nonh8_completeness_unknowns_v1_23` 增加 CST（UTC+8）月份與 UTC 月份邊界效應欄位。跨月結算逐筆點算，不以公式代替：8H 合約每個月典型恰好 1 筆（該日 16:00Z）；1H／4H 在該 UTC 月最後 8 小時可能有多筆。研究窗結束於 2026-11-26T12:00:00Z，故 CST 2026-11 在保存資料中沒有月末 crossing，只標為部分月份；10/31 16:00Z 起的月初 opening crossings 若存在仍逐筆記數。無績效數字、無倉位。

## 來源清單（10 列）

見 `research/funding_sources_nonh8_v1_23/funding_source_register_v1_23.csv`／`.md`。每批列出來源類型、URL 模式、檔案數、列數、釘選 SHA、PR #8 路徑與 commit、證據形式（raw bytes vs parsed）、以及已知的 復盤 PASS／ChatGPT 接受評論 ID（未知者不引用、不另向網路抓取）。frozen DB 不在 PR #8 內，只以釘選 SHA 記錄。

- frozen_db_l1：829,157 列，SHA `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc`
- v1.7：6,748（REST；本分支未保留 raw body）
- v1.9：174（ZIP 與／或 REST；本分支未保留 raw 證據）
- v1.10：80 個 raw ZIP；delta 10,633
- v1.11_b1：5 個 raw ZIP；delta 609
- v1.11_b2_r1：1,279 個 raw ZIP；delta 198,354
- v1.11_b3a：1,961 個 raw ZIP；delta 918
- v1.11_b3b：1,961 個 raw ZIP；delta 1,084
- v1.11_b3c：1,960 個 raw ZIP；delta 1,862
- REST 2026-11：286 個已保存 parsed JSON（285 份行情 + RVN 51001）；窗內 CST 2026-11 有限數值獨特鍵 39,037；`evidence_form=parsed_json`，`raw_bytes_saved=false`

已索引不重複官方月 ZIP：**7,246**。本編解析官方 ZIP 數值鍵 941,211（flagged official null 2：OL 2025-10、ZK 2024-06）。

## 非 8H 完整性未知項

未使用任何官方結算時程來源。僅當觀察到的區間在 {1H, 4H, 8H} 中為單一常數、且覆蓋整個位於研究窗內的 CST 月、內部無缺檔時，才寫出預期筆數；此數是觀察假設，屬推斷，不是官方核實。其餘情況由保存資料無法判定。inventory r5 的 `complete=true` 只表示通過該批來源與比對範圍，不是全期或跨頻率驗證。

- inventory r5：7,536 個月
- 至少有 1 筆非 8H 官方結算的月份：**3,122**
- 官方數值結算但全為 8H 的月份（不列為非 8H 未知項）：4,409
- 保存的 ZIP／REST 中無官方數值結算的庫存月份：5（RVN 2026-11 + 4×404）
- 可推斷（非常數全月區間，非官方）：**2,499**
- 由保存資料無法判定預期筆數：**623**（interval change or gaps 195；interval change 99；window truncated 198；span shorter than month 121；internal gaps 8；insufficient points 2）
- 未知項檔共 3,128 列（3,122 + 6 筆即使無非 8H 也列出的已知缺口；OL 2025-10 已在 3,122 內）

亦列出：OL-USDT-SWAP 2025-10、ZK-USDT-SWAP 2024-06 official_rate_null（1/85 與 1/54 literal `None`，complete=false，不補 0）；RVN-USDT-SWAP 2026-11 pending_check／rest_51001_instrument_not_listed（仍留在宇宙，不補 0）；4 個官方 ZIP 404 原因未知（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）。

## CST vs UTC 月份邊界（復盤 #7239320542）

在 3,122 個非 8H 月份中：

- 月初 opening 跨月結算（UTC 月末日 ≥16:00Z，屬本 CST 月、屬上一 UTC 月）逐筆點算合計：**6,109**
- 至少有 1 筆 opening crossing 的月份：2,974
- `cst_vs_utc_completeness_may_differ=true`：3,122（全部；即使沒有觀察到 opening crossing，該日曆月 UTC 月末 16:00Z+ 仍屬下一個 CST 月，完整／部分判定可能與 UTC 分桶不同，研究窗已截斷者除外）
- CST 2026-11 非 8H 列：212，全部標 `partial_month_no_month_end_crossing`
- opening crossing 筆數分布：0×148；1×69；2×2,846；3×1；4×29；5×1；8×28（全日常數 4H 月見 2 筆 16:00Z／20:00Z；全日常數 1H 月見 8 筆 16:00Z–23:00Z）

## 檔案 SHA-256

- `funding_source_register_v1_23.csv`：`65dcdbbd45b8b82b7e3323eea076fdc6efc31573f3d8f1ade9ee7a8d899a65ca`（8,012 B；10 列）
- `funding_source_register_v1_23.md`：`600aeebea72acacd8b0156e3612f8021758e670fc484fbc86a1ba416aa8d9c06`
- `nonh8_completeness_unknowns_v1_23.csv`：`dc4689a663b7552ef8688d6392b18ca8eba3cfec14096d2350502899df8938ce`（3,567,782 B；3,128 列）
- `nonh8_completeness_unknowns_v1_23.md`：`7a5d5675bff9562b2230d74bade889a06ee491e41cc8cbe9a12107340808fc22`
- `rest_2026_11_file_sha256s_v1_23.txt`：`1412704ba9925a6595d12dce55e4b9377a7013ce969a52670422f9f786361038`
- `funding_sources_nonh8_v1_23_manifest.json`：`c1ebc83c041070c72c4a44ba8a37418af8a6a3be917d5ade70c8d871a8a1d510`
- `build_sources_nonh8_v1_23_public.py`：`19d1b69acc6655e8756bc49ac877cf40195202b26d26641a4e60cd44d047f6b6`
- `CHANGELOG.md`：`6a90e003693a839080fb414a8a1df11615d04c91252b3b6031ba7852190145cd`

## 限制

- 未使用官方結算時程來源；推斷分母未經官方核實。
- v1.7／v1.9 raw 官方證據未留在本分支。REST 2026-11 保存的是 parsed JSON，不是 raw HTTP bytes。
- 復盤／ChatGPT 評論 ID 僅列出本編已知者。

FIB-4H-LONG-V3 維持 NO-GO。live_approved = false。
離線研究資料，未交易、未模擬、未擴窗、未補值。
