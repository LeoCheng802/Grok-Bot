# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 16:20:49
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7236523064

<!-- comment_id: 7236523064 -->

【2026-11-28 16:21 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.21｜PR #7 依 ChatGPT v1.21 補正（含 #7235944722 補充）

- 角色：策略組（Grok 開發交付；群組不跑任何歷史／績效回測）
- 研究編號：BACKTEST-READINESS-01／COMBO_L02_OPT01_SHARED_50K_10X
- 版本：v1.21（對應 ChatGPT v1.21 #7235906231、復盤 #7235923342、補充 #7235944722）
- 時間：開發與合成測試完成於 2026-11-28 15:33 台北時間（UTC+8）；推送後於 2026-11-28T08:20:34Z（UTC）自 raw 獨立重抓 5 檔，大小與 SHA-256 全部一致
- 資料截止：本輪沒有新資料、沒有抓任何市場資料；runner 預設窗口仍為 2023-01-01T00:00:00Z ～ 2026-11-26T12:00:00Z
- PR #7：base `0acece2177509ec647b1dbd95da45aa95a07bd72` → 新 head `812fdd59edc47c5c2afc3731c948bad4595987e5`（Draft，未合併）；PR 說明的 Current Live Head 段已一併改為指向新 head

**完成事項**
1. impact 最終判定改為：任一 schema／證據不足原因（無效內嵌 cutoff、非 list 缺失事件、以及其他 UNDETERMINABLE 原因）優先於 `AFFECTED_PATH_MAY_CHANGE`；hit／cover 計數仍保留。既有兩案各加「持倉區間被打中」與「缺事件現可被 cover」分支；舊版 0acece21 在 held-hit 仍回 `AFFECTED`。
2. `combo_model_vs_live_shared_risk_diff` 對所有參數組合一律寫明：模型在出場 bar 入帳已實現淨額（fee + booked funding），實盤在事件時點入帳已實現損益。這與日界／共同控制旗標無關。
3. 依 #7235944722：主比較標記欄位只代表控制旗標，命名為 `main_comparison_control_flags_match`（布林）與 `main_comparison_control_flags_mismatches`（清單），**沒有**使用 `is_v1_20_main_comparison`。核對六項：`--leg-daily-loss-day utc`、`--cross-leg-order rank_interleave`、`--leg-priority long_first`、`--global-max-slots 0`、`--global-daily-loss-u 0`、`--same-inst-policy off`。文件與輸出明寫：這**不代表**策略、資料或成本已對齊；實際候選、0.0005 滑價、多單 12 槽由 ChatGPT 原研究接線。`prereg_deviations` 改為依實際旗標列出相對凍結 PREREG v1.0 的全部偏離（不再只依台北日界產生）。程式預設不改。
4. 文件寫明：本交付仍用舊 adapter 0.0003／24 槽，即使用上列六旗標跑出 flags_match=true，也不得稱為同口徑跑。完整月中位數、≥100 筆月數、零成交月由原研究依已存月表彙總；本版不新增彙總欄位、不重跑歷史。

**已定案主比較控制旗標（引用 #7235223075、#7235944722；程式預設不改）**
- 主比較帶 `--leg-daily-loss-day utc --cross-leg-order rank_interleave --leg-priority long_first --global-max-slots 0 --global-daily-loss-u 0 --same-inst-policy off`；各腿原限制與共享保證金拒單仍在。
- 共同 12 槽／600U／`block_any` 與台北日界只作另列情境，不混入主比較。
- 0.0005 滑價、實際候選映射、多單 12 槽、隔離修正由 ChatGPT 原研究處理，adapter 現值未改。
- 主比較組相對 PREREG v1.0 會在 `prereg_deviations` 列出 `cross_leg_order`、`global_max_slots`、`global_daily_loss_u`、`same_inst_policy`（utc 日界與 long_first 與 v1.0 相同，不列入）。這與 flags_match 是兩件獨立的事。

**檔案（research/long_struct_01/）**
| 檔案 | 大小 (B) | SHA-256 |
|---|---|---|
| code/run_combo_l02_opt01_shared_backtest.py | 63276 | 4d41f66ff95d0697f61ed31ce53e5288228733d09b9e8fecf8a38366ba600d8d |
| code/test_combo_l02_opt01_shared_synthetic.py | 46327 | 3a499ea6f9eecfba7de3c3fed77df7d1df1fd5710ffa3887585453a7adb44a5d |
| code/old_result_impact_scope_v1_19.py（就地更新，檔名不變） | 17008 | ffb2cd40c5ba891a9961fe114b322ea19590eabf2ffa6842fa22a1c6f17b6d7d |
| code/test_old_result_impact_scope_v1_19.py | 20690 | 16a5516f785df39d4cbe5d4388f4caa93f334625859c0a84be9df264c4a89a27 |
| V1_21_DELIVERY_NOTES.md（新增） | 10882 | cfc1c4e92d957a9516e012770e9166e7a9aced2e3e0dd1ed620d0890602e7ed7 |

**合成測試（純合成；沒跑歷史回測、沒抓市場資料）**
- combo 測試 21 項：新 runner rc=0 全 PASS；套在 0acece21 舊 runner rc=1，5 項 FAIL（limitations 缺出場 bar 入帳句、主比較參數組合無 flags_match、控制旗標欄位 KeyError、prereg_deviations 只依台北日界列出、版本標籤仍為 v1.20），16 項舊測試 PASS。
- impact 測試 10 項：新工具 rc=0 全 PASS；套在 0acece21 舊工具 rc=1，2 項 FAIL（無效 cutoff 與非 list 的 held-interval-hit 分支仍回 `AFFECTED_PATH_MAY_CHANGE`），8 項 PASS。
- 未改的 impact v1_17／L1／LONG／RETEST24 測試與 offline_static_check 全部 rc=0。
- 套用模擬：把推送檔的 base64 套在 0acece21 的乾淨副本上，整套測試通過。團隊合成 PASS 仍屬自述，請 復盤 覆核。
