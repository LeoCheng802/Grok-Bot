# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:27:33
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230156643

<!-- comment_id: 7230156643 -->

【2026-11-28 07:27 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.11｜全窗盤點清單獨立覆核：PASS（對應執行 #7230133680）

角色：復盤（獨立覆核）｜PR #8 head eaf46daabfd8fdb80f19ced56640363ebfd64e50（parent 313829d6）｜執行 UTC 23:26:29Z → 23:27:09Z｜資料截止：凍結 DB 加 v1.7、v1.9、v1.10、v1.11_b1 delta

範圍：相對 6499a579 只新增 2 檔
- `funding_month_inventory_v1_11.csv`：771,000 B，SHA 038d59cd…2e08e21
- `funding_month_inventory_v1_11_manifest.json`：6,709 B，SHA d84d67cb…fba0d8a
兩檔均未包含本機路徑。

覆核結果：
1. 總共 7,536 列，涵蓋 286 個標的，(inst, month) 無重複。分類為已存可用 85／待核 5,882／確缺 1,279（其中 0 列 1,157、低於 8H 下限 122）／官方不可得 290（CST 2026-11 共 286、404 共 4），與回報一致。
2. 自行從凍結 DB 加 4 份 delta，依 UTC+8 月份重算每個標的×月份的 existing_rows，和 7,536 列逐列比對，不一致 0。
3. 實測官方 CDN：CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09 都是 404，對應的 NPZ 首棒都在月底最後幾小時；抓樣本 2026-11 月檔也是 404（尚未月結）。
4. 確缺的月數以 PEPE、SHIB 各 13 個月最多，與回報一致。

限制：「待核」只代表列數達到 8H 下限，仍可能缺 1H／4H，不等於完整。本輪只核清單，未下載任何 ZIP。
下一步：第 2 批（確缺 1,279 份）交件後，我照 v1.10／v1.11_b1 的方式從官方 ZIP 重算並比對集合。
邊界：draft、不合併、FIB-4H-LONG-V3 維持 NO-GO、live_approved: false。
