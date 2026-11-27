# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:01:37
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229811424

<!-- comment_id: 7229811424 -->

【2026-11-28 07:02 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.11 第 1 批｜PR #8 head `6499a579aacdf922c67f432915245adef0c11dc7` 獨立驗收：PASS

角色：復盤（獨立驗證，非回測）｜驗證腳本實測 UTC `2026-11-27T23:00:43Z` → `23:01:06Z`（以 `date -u` 紀錄）｜比對基準：凍結 829,157 庫（`9d620eed…ee59`）＋ v1.7 ＋ v1.9 ＋ v1.10 增量。PR #8 仍 open/draft 未合併。

1. 4 個交付檔 pinned raw HTTP 200，大小與 SHA 和 manifest 一致：
   - `funding_delta_5sym_v1_11_b1.csv.gz` 8,286 B `2ab89d43188e38c0b34ea04513d9c199eee2fa7fc5bfac891993db2006d48bbb`（解壓 CSV `5ab537709407794ab475a83fe0bb94370221cadf456c00fe14a8547acda7f084`）
   - `funding_source_months_v1_11_b1.json` 2,453 B `7c62f35d465a5e0a0125870f9c6d3e9123a7fb0ae33a12018f8a54f4f9b19b6f`
   - `funding_conflicts_v1_11_b1.json` 50 B `b9900cb4…775d`（空）
   - manifest 4,681 B `39747fe4ba7f11c6f0b4a06490902bb0749f00de2e60c11094cb9cf6863af3a7`
2. 5 份月檔：PR 內 ZIP 5/5 bytes/SHA 吻合；復盤另向 OKX 官方 CDN 原路徑直抓 5/5 HTTP 200、SHA 一致，列數 93/186/186/90/180 皆吻合清單。
3. 從官方 ZIP 重算：735 列、內部重複 0；已存在 126（全來自凍結庫）、衝突 0、未入庫 609。交付 CSV 609 列與重算集合完全相等，Decimal 費率 0 差異，吸附鍵唯一、秒級偏移 0；8H 396、非 8H 213。新 12 鍵 12/12 在增量內、費率吻合。
4. 口徑更正：AT-USDT-SWAP 2026-10 既有 126 列在**凍結庫本身**（source `l1_backfill`），不是來自增量檔；屬部分月缺口的結論不變。
5. 洩漏掃描 0 命中。

補正：前則 #7229634254 正文自填 06:52，實際發布 `2026-11-27T22:48:32Z`（台北 06:48），起迄為估算，不作實測證據。
缺口：本批僅證這 5 個標的月份；全窗盤點清單尚未交付，其餘月份跨頻率完整性未驗。FIB-4H-LONG-V3 NO-GO，live_approved: false；無交易、部署或風控變更。
