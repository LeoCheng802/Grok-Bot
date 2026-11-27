# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 06:48:32
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7229634254

<!-- comment_id: 7229634254 -->

【2026-11-28 06:52 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.10｜PR #8 head `b0dcf61e26db0e99b178ad0fe59d3944edbe6492` 獨立驗收：PASS

角色：復盤（獨立驗證，非回測）｜資料截止同凍結庫 v1 + v1.7 + v1.9 增量｜驗收 UTC 約 2026-11-27T22:48Z～22:52Z

1. 4 個交付檔以 pinned raw 下載均 HTTP 200，大小與 SHA256 全部吻合：
   - `funding_delta_full75plus_v1_10.csv.gz` 158,227 B `4fe33c0efe78f1398b02cb231760d3817b13f985de013e51df9c273dec7c999b`（解壓 CSV `7b7166f291629cd93e338330c58614b634a6956f9cf702b9d8f08c08c45c663d`，與 manifest 相同）
   - `funding_source_months_v1_10.json` 38,910 B `04a86793fa08624bf0e60c20cc01f54a716e45019dd265f1b870351ad118ff2e`
   - `funding_conflicts_v1_10.json` 50 B `b9900cb4aae6670829d75b3bb989bbc4227172b656dc28e6da0b6a606f95775d`（衝突與官方內部重複皆為空）
   - manifest 3,783 B `ab64f5b4a4c579f05d9bee0f068c7de17a791b3c4f370f17958d0363fdfca14d`
2. 80 份月檔：PR 內 ZIP 80/80 與清單 bytes/SHA 吻合；另向 OKX 官方 CDN 原路徑直抓 80/80，SHA 全一致（含 0G 2025-11 `78748b1a…9407`）。
3. 本端從 80 份 ZIP 重算（不信任交付 CSV）：官方 11,031 列、內部重複 0；對凍結 829,157 庫（SHA `9d620eed…ee59`）＋ v1.7（6,748）＋ v1.9（174）按 raw 與整點吸附鍵比對，已存在 398、數值衝突 0、未入庫 10,633。交付 CSV 10,633 列與本端重算集合**完全相等**，費率逐列 Decimal 比對 0 差異；與既有庫/增量鍵重合 0；吸附鍵唯一 10,633；69 標的；8H 整點 7,036、非 8H 3,597。
4. 新 7 鍵 7/7 在增量內，費率與間隔與交付一致：AEVO／USELESS／YB×2／O 前後間隔皆 4H，THETA／IOTA 為 8H。0G 2025-11-24：14:00、15:00、17:00 UTC 在增量內（費率吻合 ChatGPT 所列），16:00 位於 v1.9 增量、未重複。
5. 365 列 raw 晚 2～33 秒（集中 LUNA／UNI／XTZ／WLD），原 raw 保留、吸附到整點，吸附後無碰撞；不以吸附宣稱來源邊界完整。
6. 洩漏掃描（憑證、本機路徑、訂單/持倉識別）0 命中。

口徑：174 鍵已恢復（v1.9）；新路徑 7 鍵已取得，待 ChatGPT 疊加重播；已證非 8H 漏列 3,597 列，**僅限這 80 個標的月份**；凍結庫其他月份的跨頻率完整性**仍未驗**，不得稱資金費已完整。
缺口／下一步：全標的全期月檔逐鍵比對尚未授權執行，留給 77 或 ChatGPT 決定。PR #7 / #8 仍 open/draft 未合併。FIB-4H-LONG-V3 維持 NO-GO，live_approved: false；無下單、部署或風控變更。
