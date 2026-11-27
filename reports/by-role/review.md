# 復盤

此檔是「復盤」的最新回報。

- **時間（Asia/Taipei）**: 2026-11-27 10:35:31
- **角色**: 復盤
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7208264510

<!-- comment_id: 7208264510 -->

[復盤] RESEARCH-LOOP-01 v1.2｜非 8H／正規化資金費試點已上傳（commit `9b3d937`）＋ LONG-LOOP-01 結案（NO-GO）

- **角色**：復盤（總召／獨立覆核）
- **研究編號／版本**：`RESEARCH-LOOP-01 v1.2`（承接 `#7208108881`）｜公開分片 `funding_mixed_shard_v1`｜多單單因素檢驗 `LONG-LOOP-01 v1.0`
- **時間與時區**：2026-11-27 10:36（Asia/Taipei, UTC+8）
- **資料截止**：`EX_USDC_286`、`2023-01-01` 至 `2026-11-26 12:00 UTC`（已觀測樣本內歷史診斷，不稱新 OOS；全程未重抓資金費、未補零、未重跑 L1）
- **各交付狀態總覽**：
  - 公開資金費試點 `funding_pilot_v1`（commit `8bf4c15ed50d5dc3f1f66a01dd3df83f5521b668`）：`ChatGPT 已取得驗證`
  - 公開非 8H／時間正規化分片 `funding_mixed_shard_v1`（commit `9b3d93768c1581b985bf01283af353d59c9f93cc`）：`已上傳，待 ChatGPT 取得驗證`
  - 私人離線包 `RESEARCH-LOOP-01-PACK v1.1`：`待收（僅走私人交付，不公開）`
  - `LONG-LOOP-01 v1.0`：`已完成，NO-GO（留存負結果，停止原多單結構續調）`

---

### 1. 公開非 8H／時間正規化資金費分片（經復盤獨立驗證 HTTP 200、大小與 SHA-256 全符，零路徑／憑證洩漏）
- **固定 Commit**：[`9b3d93768c1581b985bf01283af353d59c9f93cc`](https://github.com/LeoCheng802/Grok-Bot/commit/9b3d93768c1581b985bf01283af353d59c9f93cc)（目錄 `research/RESEARCH-LOOP-01/funding_mixed_shard_v1/`，僅新增以下 2 檔，前次試點未更動，皆採完整 commit SHA 固定連結）
- **[manifest.json](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/9b3d93768c1581b985bf01283af353d59c9f93cc/research/RESEARCH-LOOP-01/funding_mixed_shard_v1/manifest.json)**（`4,357` bytes，SHA-256 `8e4fdaa137eefd494d8ba990a9cb9b0a065c11a6aaed24897791a4de7c76b493`）
- **[FIL-USDT-SWAP_2022-12.csv](https://raw.githubusercontent.com/LeoCheng802/Grok-Bot/9b3d93768c1581b985bf01283af353d59c9f93cc/research/RESEARCH-LOOP-01/funding_mixed_shard_v1/FIL-USDT-SWAP_2022-12.csv)**（`11,869` bytes，SHA-256 `a850777c31a9a7887ef497fe943ece919771df6ef0ec023e944b02d0b97aa4c0`）
- **分片診斷**：UTC `2022-12` 嚴格依結算時戳選窗（保留 `funding_time_ms`、`ts_snapped_ms`、`snap_offset_ms` 對照，不以 `source_ym` 剔除）；共 `93` 筆（原始鍵與正規化鍵皆 `93` 唯一、重複鍵 `0`）、`92` 筆時間正規化偏移（`-43,000 ms`～`+23,000 ms`）、`2` 筆非 8H（`2022-12-18 09:00:00Z` 與未 snap 之 `18:54:08Z`）、對應 `2` 格 8H 缺口（`2022-12-18 08:00:00Z`／`16:00:00Z`，標記 `miss_8h` 不補零）、`source_ym` 含 `2022-12`（92 筆）與 `2023-01`（1 筆）。待 ChatGPT 驗證通過後再補其餘既有分片與實際持倉涵蓋之資金費名冊缺口。

---

### 2. `LONG-LOOP-01 v1.0` 獨立覆核結果（僅改 `BTC_FILTER`，上限 4 次新增 replay — **NO-GO**）
- **輸入與規則核對**：
  - 與 L1 基準（`FIB_4H_Long_v3.py` `c52ea221...cdbe9`、`TP 2.5%`／`SL 4.0%`、50,000U 10x、24 槽、限價進場、同資金費庫）完全一致；未偷換 `off` 基準，未以其他 TP 臂代替基準。
  - BTC 訊號資料：OKX 公開 `BTC-USDT-SWAP` `1D`（UTC+8 00:00 = `16:00 UTC`，僅 `confirm='1'`，`1,671` 筆 `2022-05-01T16:00:00Z`～`2026-11-26T16:00:00Z`，`0` 缺日、`0` 錯位、剔除 `1` 筆未收盤；`btc_usdt_swap_1d_okx.json` SHA-256 `7b7f3fc59549abb6f033bb3df41e65913ca100ab60429689240440ed8dec26f0`）。`2023-01-01` 前已有 `244` 筆暖機（暖機／缺資料阻擋均 `0`）；僅用訊號當時已收盤 `t < day` 資料，與原檔 `btc_allows()` 核對 `17,108` 次 `0` 誤差；BTC 僅作市場訊號不交易；濾網擋下僅跳過當根 4H 新限價進場，既有掛單與持倉不動。
  - 輸出與腳本雜湊：`long_loop_01_result.json`（SHA-256 `c8e551cc4e9b8f28aa6511762e71762d4ecf4434b2032cd86c216e7f1bc655d8`）、`run_long_loop_01.py`（SHA-256 `fc23baf08ae360a134e6e2f9c116afc71bb4d5219c65490efb672cfb34c7dce8`）。
- **全期條件性績效對照**（含 `miss_8h` 未入帳缺口，不標完整淨績效；8H 持倉人槽以 `f_ev_real_8h + f_ev_miss_8h` 估算）：
  - `off`（L1 基準引用）：`cross_1tick` 4,535 筆、WR 58.57%、淨損益 `-49,668.23U`（`-99.34%`）、MTM MDD `99.38%`、PF `0.828`、期望 `-10.952U`（`real_8h=6,415`／`non8h=1,228`／`miss_8h=158`）；`delay1bar` 4,297 筆、WR 58.32%、`-49,752.41U`（`-99.50%`）、MDD `99.54%`、PF `0.819`、期望 `-11.578U`（`real_8h=6,171`／`non8h=961`／`miss_8h=128`）。
  - `200ma`（拒 `2,920` 根 4H／`34.14%`、`101,904` 候選／`38.06%`）：
    - `cross_1tick`：3,570 筆、WR `57.45%`、淨損益 `-49,195.75U`（`-98.39%`）、MTM MDD `98.46%`、PF `0.789`、期望 **`-13.780U`**（2023 `-9.456U`／2024 `-16.562U`／2025 `-14.369U`／2026 `-27.089U`，四年全負；`real_8h=4,974`／`non8h=659`／`miss_8h=76` 跨 30 檔）
    - `delay1bar`：3,391 筆、WR `57.12%`、淨損益 `-49,427.93U`（`-98.86%`）、MTM MDD `98.90%`、PF `0.779`、期望 **`-14.576U`**（`skip_first_bar_cross=84`；四年全負；`real_8h=4,802`／`non8h=543`／`miss_8h=66` 跨 26 檔）
  - `10pct`（拒 `7,858` 根 4H／`91.86%`、`233,827` 候選／`87.34%`）：
    - `cross_1tick`：594 筆、WR `62.29%`、淨損益 `-1,158.96U`（`-2.32%`）、MTM MDD `16.95%`、PF `0.966`、期望 **`-1.951U`**（2023 `+327.98U` 193 筆／2024 `-1,201.65U` 247 筆／2025 `-1,827.56U` 115 筆／2026 `+1,542.27U` 39 筆；`real_8h=580`／`non8h=80`／`miss_8h=23` 跨 11 檔）
    - `delay1bar`：`skip_first_bar_cross=4`，其餘已平倉筆數（594）、淨損益（`-1,158.96U`）、MDD（`16.95%`）、PF（`0.966`）、期望（**`-1.951U`**）與 `miss_8h=23` 跨 11 檔皆與 `cross_1tick` 一致。
- **覆核揭露之程式缺口**：`long_loop_01_result.json` 因彙整鍵名未對上引擎輸出，致 `monthly_summary` 與 `exposure` 欄位皆寫入 `0`（逐年表、逐筆期望、下單／成交／到期與 `miss_8h` 分佈完整存在）；為嚴守最多 4 次新增 replay 上限且 4 臂皆已明確負期望，未另重跑。
- **結論**：4 個新增 replay 全數為負期望（`200ma` 逐筆期望更較 `off` 惡化；`10pct` 虧損收斂主因僅為進場次數縮減 87%，並非轉正）。依 `#7208108881` 準則留存負結果，**停止原 `FIB_4H_Long_v3` 多單結構續調，不擴大掃描**。

---

### 3. 安全邊界與下一步
- 空單已凍結規格不動，14 天公開前向觀測仍未啟動；全部維持離線研究，無 `--demo`／`--live`、下撤平單、部署或實盤風控變更授權。
- 待 ChatGPT 驗證 `funding_mixed_shard_v1`（commit `9b3d93768c1581b985bf01283af353d59c9f93cc`）格式與解析無誤後，再接續上傳既有資金費其餘分片與實際持倉涵蓋名冊缺口；並待 ChatGPT 就原多單結構退場後的下一研究方向指示。
