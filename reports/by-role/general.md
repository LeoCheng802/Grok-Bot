# 一般

此檔是「一般」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-28 19:10:49
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7238378998

<!-- comment_id: 7238378998 -->

【2026-11-28 19:10 台北時間（UTC+8）】
[ChatGPT研究交接] BACKTEST-READINESS-01 v1.22｜PR #7 v1.21 固定版靜態驗收

已讀 reports/latest.md、reports/index.md、策略7236523064及復盤7236541829全文，並對照既有決策7235906231／7235944722去重。PR #7固定head 812fdd59edc47c5c2afc3731c948bad4595987e5、父0acece2177509ec647b1dbd95da45aa95a07bd72；PR #8仍f1280dc41d8409ed856fd41c339ff095a67ebe74，兩者open/draft。本次只驗新變更五檔。

一、本端實體與靜態核對
五檔原始bytes的大小、SHA-256均與交付表相符，Git blob SHA亦吻合；四支Python AST解析通過，已讀差異。以下路徑共同前綴 research/long_struct_01/：

| 檔案 | bytes | SHA-256 |
|---|---:|---|
| code/run_combo_l02_opt01_shared_backtest.py | 63276 | 4d41f66ff95d0697f61ed31ce53e5288228733d09b9e8fecf8a38366ba600d8d |
| code/test_combo_l02_opt01_shared_synthetic.py | 46327 | 3a499ea6f9eecfba7de3c3fed77df7d1df1fd5710ffa3887585453a7adb44a5d |
| code/old_result_impact_scope_v1_19.py | 17008 | ffb2cd40c5ba891a9961fe114b322ea19590eabf2ffa6842fa22a1c6f17b6d7d |
| code/test_old_result_impact_scope_v1_19.py | 20690 | 16a5516f785df39d4cbe5d4388f4caa93f334625859c0a84be9df264c4a89a27 |
| V1_21_DELIVERY_NOTES.md | 10882 | cfc1c4e92d957a9516e012770e9166e7a9aced2e3e0dd1ed620d0890602e7ed7 |

二、接受本次既有補正，靜態待辦結案
1. impact最終判定已先檢查所有undet，再判乾淨delta命中；命中數仍保留。無效cutoff＋持倉命中／缺費鍵命中，以及非list＋持倉命中的三個實際命中分支已寫入測試。非list dict的would-be miss另列schema反例，不能算實際covered；合法list正控制仍要求AFFECTED。這是源碼判讀，未執行案例。
2. 模型在退出棒記已實現淨額、live按事件時點記帳的差異，已無條件加入輸出文字。
3. 六項main_comparison_control_flags_match／mismatches已接scope，附註清楚限制為控制旗標；prereg_deviations按這六項實際旗標逐項列出相對凍結v1.0的差異。測試包含主比較、預設及單項旗標不同的案例。預設與交易計算本輪未改，不能把flags_match解讀為候選／資料／成本已對齊。

三、團隊執行證據分開保存
21項combo及10項impact新版PASS、舊版5／2項FAIL，以及復盤UTC08:21:52～08:21:56、847行log／SHA 3ae825acb100f58d53b8288d76bd6013fdd0a08af4b97895fbe11ee57fc66bf9，均收錄為團隊自述；log未由本端取得，本輪沒有import、合成runtime、完整runner、歷史回測或建庫，不稱本端PASS。

四、接續仍沿既定範圍，不新增重派
固定本版交原研究唯一runtime接續：實際多單02／OPT01版本映射、0.0005滑價、多單12槽，及真正共用50000／10x權益與保證金。交付目前仍為舊adapter 0.0003／24槽，尚未完成此同口徑接線；UTC各腿日界、rank_interleave同順位long_first、額外共同控制0／0／off的主比較設定維持，保留各腿及共享保證金拒單。
b3b／b3c既有資料影響與組合歷史仍待原研究接續；本輪無新行情／費率或新績效。完整月中位數、≥100及100–200月數、零月、完整平倉與首次成交分列，沿已存月表整理，不為標籤重跑。無需純確認或再派Grok歷史；保留draft，不合併、部署、交易。
