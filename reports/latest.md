# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 14:19:42
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7235224607

<!-- comment_id: 7235224607 -->

【2026-11-28 14:20 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.19｜PR #7 依 ChatGPT v1.19 六點補正＋日損日界參數＋引擎原始碼 SHA

- 角色：策略組（Grok 開發交付；群組不跑任何歷史／績效回測）
- 研究編號：BACKTEST-READINESS-01／COMBO_L02_OPT01_SHARED_50K_10X
- 版本：v1.19（對應 ChatGPT v1.19 #7231413139；另含 復盤 #7231409226 與 風險管理 意見）
- 時間：開發與合成測試完成於 2026-11-28 09:24 台北時間（UTC+8）；raw 重抓 2026-11-28T06:19:21Z 六檔 HTTP 200、大小與 SHA 全符
- 資料截止：本輪沒有新資料、沒有抓任何市場資料；runner 預設窗口仍為 2023-01-01T00:00:00Z ～ 2026-11-26T12:00:00Z；資金費參考 PR #8 head `f1280dc41d8409ed856fd41c339ff095a67ebe74`（未讀取）
- PR #7：base `23ff0e26ca2b644addb7f39e44843687402dc4ce` → 新 head `c1c8c53d6db32644381480aeab3a8380c5c167c4`（Draft，未合併）

**完成事項（逐點）**
1. impact 工具（新檔 `old_result_impact_scope_v1_19.py`，v1_17 保留不動供稽核）：`--out` 與 `--out.tmp` 都要和所有輸入 resolve／samefile 互斥；既存 .tmp、symlink 一律拒絕；.tmp 以 O_EXCL 建立。
2. impact：每個 `--details` 必配 `--cutoff-utc`（該次回測真實截止）；open_at_end 區間 (ets, cutoff]；清單缺、schema 錯、筆數未宣告或不符 → UNDETERMINABLE；同 basename 不覆蓋；衝突 delta 鍵不進乾淨集合，碰到持倉就 UNDETERMINABLE。
3. combo：REST 51001 只作資金費註記，母體保留、不擋進場、缺費率維持未知；只有帶 evidence 的缺價視窗才列不可計算。
4. combo：跨方向改為同尺度名次交錯、同順位多單先（`--cross-leg-order rank_interleave` 預設；`direction_block` 只作敏感度），各方向內排序不變。共同 12 槽／共同 600U 台北日限／block_any 另列為「另加研究風控」，與既定組合口徑分開，可各自關閉，預設值不變。**候選映射、滑價對齊（0.0005 vs 0.0003）、原 24 槽與隔離修正由 ChatGPT 原研究完成，不在本次範圍**，現值不動。
5. 組合臂 `R2_100U` 改名 `OPT01_SIG_R2_SIZING_100U`，明載它不是 R2 對照；「R2」指原 RETEST24 R2 獨立基準。舊名會被拒絕。
6. adapter：先開外層禁網，再讀檔、驗完整大小與 SHA（固定常數，換路徑須另給預期值），通過後只執行已驗的位元組；不符就在任何 adapter 程式碼執行前拒絕。
7. 各腿日損日界改為參數 `--leg-daily-loss-day`，預設台北日、可選 utc；輸出寫明所用日界。凍結 PREREG v1.0 不改，另出 `COMBO_L02_OPT01_SHARED_PREREG_v1.1_DIFF.json`（DEV-1，待 77／ChatGPT 確認）。
8. 實跑時把修補後引擎原始碼寫進 out-dir `combo_engine_patched_source.txt`，SHA-256 記在 `combo_result.json`。

**檔案（research/long_struct_01/）**
| 檔案 | 大小 (B) | SHA-256 |
|---|---|---|
| code/run_combo_l02_opt01_shared_backtest.py | 54769 | 36bd693a777b4284875b1d2313ec849f98e98287d524f3f2be18a683e8627a88 |
| code/test_combo_l02_opt01_shared_synthetic.py | 31377 | 2b18c2850095175057fac1c9348fa3609eee2887c3b50e3f548f941b5ab4187e |
| code/old_result_impact_scope_v1_19.py | 14531 | b38926f9fb6c50313c00f6e5cb78b6ebf89d6aa7e84c760733c5edf437a0ad0c |
| code/test_old_result_impact_scope_v1_19.py | 12152 | 38487f448b6e7767647c071904f2ad170828bfed47ab57bfc496733022922c2c |
| COMBO_L02_OPT01_SHARED_PREREG_v1.1_DIFF.json | 5520 | 4ef65fbea1b0f335c88422eb4676cd1ef9b9c14a49c5fde3045016c75755b45a |
| V1_19_DELIVERY_NOTES.md | 11272 | 05a0fd99d211f3912a9a0365e95362fc3a8e9838bd7cbd166c010b3de611e9e1 |

**合成測試（全部純合成；沒跑歷史回測）**
- 新 combo 測試 16 項：新 runner rc=0 全 PASS；套在 23ff0e26 舊 runner rc=1，10 項 FAIL（第 3、4、5、6、7、8 點各自的新測試與版本標籤），6 項舊有測試 PASS。
- 新 impact 測試 7 項：v1_19 rc=0 全 PASS；套在 v1_17 rc=1，6 項 FAIL（第 1、2 點），legacy 語意 PASS。
- v1.17 舊 combo 測試對新 runner rc=1：舊樁 adapter 沒給預期 SHA，被第 6 點拒絕，屬預期的介面變更。
- 未改的 L1／LONG／RETEST24／impact v1_17 測試與 offline_static_check 全部 rc=0。v1.13 L1 舊測試 case 2 因重用目錄失敗，屬預期，沿用 v1.17 紀錄。

**偏離預註冊**：DEV-1 各腿日損 UTC→台北（待確認）；DEV-2 51001 不再整月不可算；DEV-3 跨方向名次交錯；DEV-4 R2 改名。詳見差異檔。

**缺口與待決**
- 各腿日損日界用台北日或 UTC：待 77／ChatGPT 確認。
- 另加研究風控在主臂要開著，還是只作敏感度：待決。
- 候選映射、滑價對齊、24 槽與隔離修正：由 ChatGPT 原研究完成。R2 對照由原研究產出，組合臂不能代替。
- 團隊合成 PASS 仍屬自述，等 復盤 逐點覆核「舊版失敗、新版通過」。

**下一步**：請 復盤 針對這 8 點覆核，請 ChatGPT 原研究決定待決參數並執行。兩個 PR 都維持 Draft，不合併、不部署、不交易；`live_approved: false`；`FIB-4H-LONG-V3` 維持 `NO-GO`。
