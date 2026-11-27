# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 07:32:45
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230222835

<!-- comment_id: 7230222835 -->

【2026-11-28 07:33 台北時間（UTC+8）】
[復盤] BACKTEST-READINESS-01 v1.13 修正｜PR #7 head 3a2ba82 的 L1 main 接線獨立合成複驗：PASS（舊版失敗、新版通過）

角色：復盤（獨立覆核）｜head 3a2ba82caec450d9b0bc854de0630618d6431e94（parent 59dea52b）｜執行 UTC 23:32:05Z → 23:32:17Z

變更範圍：只改 2 檔
- `run_l1_bounded_backtest.py` 加了 10 行：47,609 B，SHA 9b206115…dfcce8。
- 新增 `test_l1_bounded_main_synthetic.py`：14,391 B，SHA 7881609c…1a6a。
兩者大小與 SHA 都和 ChatGPT v1.14（#7230156045）一致。diff 只加了路徑定義、兩個互斥清單項目、ABORT 明細欄位（performance_valid=false、只供本機診斷、arms、by_year_month、缺費明細）、成功明細的 by_year_month，以及例外時清除明細。沒有新的 import 或網路呵叫。

自行複驗（純合成、stub engine，在隔離暫存目錄執行）：
- 新版：成功出口 rc=0，明細檔存在且記錄了 SHA，by_year_month=2024-01、2024-02；缺費出口沒有成功報告，明細帶齊 arms、by_year_month、missing_funding_gaps、performance_valid；3 種路徑重合全部在寫入前拒絕，哨兵 writes/copy2/np_load/load_mods=0，受害檔未變；最後輸出 ALL_L1_MAIN_SYNTHETIC_TESTS_PASS。
- 舊版 59dea52b 跑同一套：3 項全部 FAIL，都是 NameError。路徑重合時哨兵 writes=2、copy2=1，寫入前沒有被擋下。
- 既有的 LONG、RETEST24 兩套 synthetic 在新 head 上仍然 PASS。

限制：這是合成資料加 stub，不是歷史 runtime。L1 仍需外層 NPZ 逐檔 hash 保全（同 v1.14）。ABORT／PASS 明細的 version 標籤還寫著 "v1.9"，屬標籤小瑕疵，不影響邏輯。
另已對 PR #8 盤點覆核過（#7230156643），接受 v1.14 對分類的限定：「確缺」只算優先候選，不等於已證明應付缺費。
邊界：draft、不合併、FIB-4H-LONG-V3 維持 NO-GO、live_approved: false。
