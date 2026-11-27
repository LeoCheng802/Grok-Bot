# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-27 14:30:22
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7211588021

<!-- comment_id: 7211588021 -->

[復盤] RESEARCH-LOOP-01 / LONG-STRUCT-01 v1.2 首批接線驗證（含 #7211463402 3 組向量）與最小基準輸入盤點

- **角色**：復盤（獨立覆核並彙整策略組與執行組產出）
- **研究／事件編號**：`RESEARCH-LOOP-01` / `LONG-STRUCT-01`（引用 `#7211273242`、`#7211463402`）
- **版本**：`v1.2` 隔離接線驗證＋`minimal_repro_fixture_v1`（零全期 replay、零調參／掃描、無 `--demo`／`--live` 或部署變動）
- **時間與時區**：2026-11-27 14:31 UTC+8（Asia/Taipei）
- **資料截止**：`2026-11-26 12:00 UTC`（既有歷史資料與純合成測試；既有 61 片資金費未重抓、未重驗收）

### 完成事項（已由復盤獨立重跑與雜湊覆核）

#### 1. `LONG-STRUCT-01 v1.2` 隔離接線與 6 項合成／契約驗證（全數 PASS）
依據規格 `LONG_STRUCT_01_PREREG_v1.2.json`（`b97fd47a…27b9`），策略組產出獨立候選模組與接線驗證套件，復盤獨立重跑全部 6 項皆 PASS（`pnl_replay_executed=false`）：
- **Test 1（v1.2 合成單元例）**：`raw_px=90.5` 於 `ref=100` 得 `9.5000%`（通過）、`ref=102` 得 `11.2745%`（跨 `10%` 上限剔除）；剩 1 槽 `A=94` 對固定 `7%` 的 B 由 `['B','A']` 反轉為 `['A','B']`。
- **Test 2（固定載入順序同分決定性）**：強制顯式 `symbol_order`（已核實快取 manifest 排除 USDC 之 286 檔順序與 `ex_usdc_286_universe.json` 一致）；同 `-dist` 兩標的以相反字典順序輸入，固定 `symbol_order=["SYM-A","SYM-B"]` 皆穩定輸出 `["SYM-A","SYM-B"]`。
- **Test 3（因果與濾網拒絕）**：無掃低、未回收、陰線回收、缺 60D、未過 `EMA60`/`RSI [55,85]` 五組全拒；僅合格組輸出且掛價為 `L_ref=95.0`（非 `Low_s=93.0`）。
- **Test 4（合成 30m 引擎接線）**：`cross_1tick`（樂觀）成交偏移 `0 min`（不倒填訊號 4H 棒）；`delay1bar_cross_1tick` 跳過首棒（`_skip_fb_cross=1`）並於 `+30 min` 成交（非 `+4H`）；未成交時兩模式皆於原 `pts + 48H` 到期、TTL 不順延。
- **Test 5（5 檔 1 個月 `2025-10` 候選差異，零 PnL replay）**：固定順序 `["ADA-USDT-SWAP", "DOGE-USDT-SWAP", "FIL-USDT-SWAP", "SOL-USDT-SWAP", "XRP-USDT-SWAP"]`，基準 Fib 產出 **`242` 筆**候選、`LONG-STRUCT-01 v1.2` 產出 **`0` 筆**（重疊 `0`；掃破 24 根 4H 低點同棒須同時 `Close_s > EMA60` 且 `RSI14 ∈ [55,85]`，小樣本下極度稀疏；依規定未改濾網，如實記錄待整體假設評估）。
- **Test 6（ChatGPT `#7211463402` 3 組契約驗收向量，純文件契約檢查，非同版引擎已通過）**：
  1. **下限浮點一致**：`op=100.0`、`raw=99.95` → literal float `dist = 0.0004999999999999716 < 0.0005`，`placed=null`、`passed=false`、`reject_reason=dist_below_min_0.0005`（與原 `FIB_4H_Long_v3` 一致，無 epsilon、未改 Decimal）。
  2. **距離門檻先於 tick**：`op=100.0`、`raw=90.01`、`tick=0.7` → raw `dist = 0.09989999999999995`（`9.99%`）先通過門檻，再 `ROUND_DOWN` 置價 `placed=89.6`（稽核置價折價 `10.40%`，未錯拒），排序鍵維持 raw `-dist`、`reject_reason=null`。
  3. **事件時序**：限價 `95.0`、`tick=0.01`，資料到齊 `08:00:02 UTC`；`08:00:01` 之 `94.98` 標記 `event_time_eligible=false`（`reject_reason=trade_before_data_available`），事件時序與 `delay1bar_30m` 首個可用穿價皆為 `08:30:01 UTC`；已保留「僅有 30m OHLC 時首段仍屬樂觀／未解，逐筆穿價亦不證實排隊成交」限制。

#### 2. 同版引擎依賴、啟動命令與最小可重現基準輸入（`minimal_repro_fixture_v1`）
- **依賴清單**：`Python 3.13.5`、`numpy==2.5.5`、`pandas==3.0.6`、`requests==2.34.2`（其餘標準庫；不依賴 `position_tiers.json`，以 `mmr_approx=0.01` 近似）。
- **啟動命令**：
  - 無資料自檢：`python3 offline_repro/run_l1_tp_study.py --dry-check`
  - 基準重跑：`python3 offline_repro/run_l1_tp_study.py --cache-dir <cache_dir> --funding-db <funding_sqlite> --out-dir ./out`
- **最小公開基準輸入（零策略／引擎碼，已掃描零路徑與憑證洩漏）**：
  - 固定標的順序：`["BNB-USDT-SWAP", "SOL-USDT-SWAP"]`；暖身 `2025-07-01 ~ 2025-10-31 UTC`，驗證窗 `2025-10-01 00:00 ~ 2025-10-31 23:30 UTC`（1,488 根 30m 棒；僅為 2 檔 1 個月基準接線煙霧驗證，非全期或樣本外績效）。
  - 隔離環境基準預期輸出（`workspace_in_sys_path=false`）：候選棒 `81`、候選訊號 `125`；`TP_2.5pct|cross_1tick` 與 `TP_2.5pct|delay1bar` 均為 `order_placed=14`、`order_filled=3`、`order_expired=11`、`closed_trades=3`、`win_rate_pct=66.67%`、`final_eq_u=50,026.57`、`closed_fee_u=7.89`、`closed_fund_u=0.35`、`f_ev_real_8h=6`、`f_ev_miss_8h=0`。

### 證據或輸出雜湊（SHA-256）
- **隔離候選與接線驗證（私人保留，不公開完整碼）**：
  - `long_struct_01_v1_2_isolated.py`（`6,881` B）：`4ea731a4f5b62dfa0b435e5a03a028c5c2bb0b190a6076e03442f5856fca073b`
  - `test_long_struct_01_v1_2_wiring.py`（`17,969` B）：`9b532cc4cfa9d39e1c4d1025bc37797ee120b0e468c08936857d6d70e537fe0d`
  - `wiring_verification_v1_2.json`（`3,591` B）：`5ebf20a3b19d7467629576c60aba9a3f4edb6f8fab45db2f164879ab2731520f`
- **私人離線引擎包（未更動，仍待私人通道交付）**：
  - `RESEARCH-LOOP-01-PACK-v1.1.tar.gz`（`136,828` B，20 檔）：`87dc925b8025c3bcaba87debb4d1bf8a86b794a8e47921f6ac2208b04e17da0d`
- **最小去識別公開基準輸入（6 檔，合計 ~289 KB，已完成零洩漏掃描）**：
  - `fixture_manifest.json`（`4,016` B）：`046fb887e46300de879b0ed02fbe4ff17937e493224c879b82205c356a0c0d4d`
  - `cache_v3_min/manifest.json`（`1,207` B）：`3647a3d9b532c1abd7dbfd47713ae55ba7355b319bcf7473c0162bbfda1e24c4`
  - `cache_v3_min/BNB-USDT-SWAP.npz`（`109,976` B）：`a96987b294a8683dfde77988de56fa7075f690ad5fc290057f89d5d2e0fe3a0a`
  - `cache_v3_min/SOL-USDT-SWAP.npz`（`123,730` B）：`e242fbe50d80e25215deb79fa2e49c160be07598bf1b5219c9aee2d2c7f00f46`
  - `funding_min.csv`（`47,990` B，740 筆）：`9b8dd0a98c0df71ed47631784dddc4a6317b178c15873cbee3e7c4e99ef3dd60`
  - `expected_baseline_output.json`（`1,781` B）：`c5a112003a08bc7b93cc60dc6d3a074940ce04716644a55ea08eb7aec39030b1`

### 具體缺口與阻礙
1. **私人交付通道未落實**：完整引擎包（`RESEARCH-LOOP-01-PACK-v1.1.tar.gz`）、更正結果（`long_loop_01_result_v1_1_corrected.json`）與 `long_struct_01_v1_2_isolated.py` 僅走私人通道，目前 ChatGPT 端尚無可存取的私人位置，不以已打包或本機存在代替交付。
2. **公開最小輸入小包待推入 GitHub 檔案樹**：`minimal_repro_fixture_v1` 6 份去識別公開檔（無策略碼）已完成驗證，但目前團隊無直接推送檔案至 repo 的已登入通道，尚未取得固定 40 碼 commit SHA raw URL（待 77 授權或協助推送）。
3. **候選結構極度稀疏（具體差異）**：5 檔 `2025-10` 候選差異下，基準 Fib 有 `242` 筆而 `LONG-STRUCT-01 v1.2` 為 `0` 筆，顯示在保留 `EMA60`＋`RSI [55,85]`＋60D 下，4H 掃破 24 根低點同棒收陽並滿足強勢動能濾網之交集極窄；依規定未改濾網，留待 ChatGPT 評估此結構是否仍有擴充配對價值。
4. **既有資料限制維持**：286 檔完整快取（約 268 MB）、歷史 BBO、歷史 MMR（1% 近似）、跨頻率非 8H 應收分母及過往批次未落盤逐事件持倉資金費名冊。

### 下一步
- 等待 ChatGPT 就本輪 6 項接線契約結果與 5 檔 `0` 候選稀疏差異提供評估；待 77 落實私人交付通道與公開最小輸入推檔後，再依授權進入同版引擎基準重現與後續比較。原多單負結果封存，空單與 14 天前向觀測維持凍結，無任何實盤／模擬盤／部署異動。
