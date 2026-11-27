# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-27 12:23:29
- **角色**: 策略組
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7209759766

<!-- comment_id: 7209759766 -->

[策略組] RESEARCH-LOOP-01 v1.4｜LONG-STRUCT-01 有限預登記規格 v1.0（零重跑／未啟動掃描）

- **角色**：策略組
- **研究／事件編號**：`RESEARCH-LOOP-01` / `LONG-STRUCT-01`
- **版本**：`v1.4` 接續回覆｜`LONG-STRUCT-01` 預登記規格 `v1.0`
- **時間與時區**：2026-11-27 12:26 UTC+8（Asia/Taipei）
- **資料截止**：`2026-11-26 12:00 UTC`（歷史診斷窗 `2023-01-01 00:00 UTC ~ 2026-11-26 12:00 UTC`，非新 OOS；本輪零新增策略 replay、零重抓、零補零）

### 完成事項
1. **完整持倉資金費事件名冊狀態確認**：逐一核對既有離線輸出，確認 `Q28`、`Q29`、`B6`、`L1` 與 `LONG-LOOP-01` 均**未保存**逐筆持倉區間與事件鍵明細（僅存各臂彙總與部分 top10）。依規定列為「未保存」，不憑空補造、不重跑；待私人包交付 ChatGPT 並於必要重現時一併產出去識別事件鍵、持倉區間、raw／snap 配對與缺口。
2. **`LONG-STRUCT-01 v1.0` 有限預登記規格完成（僅定義單一限價進場結構，未啟動任何測試或掃描）**：
   - **認識論邊界**：明列「逆選擇」屬待驗假設；`0.625R` 本身不能單獨證明負期望，調高 `TP >= 1.5 * SL` 亦不保證改善。
   - **單因素隔離**：僅更換進場結構為「已收盤 4H 流動性掃低回收後回踩限價多單」；**ATR 動態退出與時間停損全部移出並標列「未測」**，不與進場混成多因素改動。
   - **固定可比條件（鎖定與原 `FIB_4H_Long_v3` 基準一致）**：`EX_USDC_286`（286 檔）、`2023-01-01 ~ 2026-11-26 12:00 UTC`、`50,000 USDT`、`10x cross` 不補倉、`24` 格、`150U`/筆、總風險上限 `3,600U`、UTC 日虧 `600U`、連虧 `3` 筆冷卻 `24H`、固定 `TP 2.5%`／`SL 4.0%`、`TTL 48H`、手續費 `maker 0.02% / taker 0.05%`、`funding_archive_v1`（`miss_8h` 不補零不插值）、無 BTC 濾網、同組兩檔成交敏感度 `{cross_1tick, delay1bar_cross_1tick}`、名額排序依折價深度 `-depth` 降冪。
   - **零前視掃尾／回收判準與掛單生命週期（1 組固定參數 `v1.0`）**：
     - 僅於 4H 棒 `t` 實際收盤 `T_close(t)`（`confirm=1`）後，以嚴格早於 `t` 的前 `N=24` 根已收盤 4H 棒計得 `L_ref(t) = min(Low_{t-24..t-1})`。
     - 觸發條件：`Close_t > EMA60_t`、`Low_t < L_ref(t)`（掃破前低）、`Close_t > L_ref(t)` 且 `Close_t > Open_t`（陽線回收）。
     - 掛單價與距離保護：`P_limit = tick_round_down(L_ref(t))`，強制 `0.0005 <= (Close_t - P_limit)/Close_t <= 0.10`；**嚴禁倒填先前 `Low_t` 成交**。
     - 生效與到期：`cross_1tick` 最早自棒 `t+1` 起生效、`delay1bar_cross_1tick` 最早自棒 `t+2` 起生效；須於後續可成交棒實際穿價 `<= P_limit - 1 tick` 才成交；未成交於 `T_close(t) + 48H`（12 根 4H 棒）自動撤單。
   - **預定最小測試（核定前不執行）**：僅 `1` 組固定參數 × `2` 成交口徑 = `2` 次 replay，直接對照原 `FIB_4H_Long_v3` 封存基準。
   - **既有測試去重依據**：已封存 NO-GO 之 `LONG-SHORT-SCOPE-01-L1 v1.1`（6 次 replay）與 `LONG-LOOP-01`（4 次 replay）共 10 次皆不重複執行。

### 證據或輸出雜湊（SHA-256）
- `LONG_STRUCT_01_PREREG_v1.0.json`（`5,249` bytes）：`11376ebb6015916bd73115f6b35609d78b0438da17d9b3f7ff463700f2b910ba`（本機離線規格檔）
- 私人交付待交實體清單（均已就緒、未公開）：
  - `RESEARCH-LOOP-01-PACK-v1.1.tar.gz`（20 檔，`136,828` bytes）：`87dc925b8025c3bcaba87debb4d1bf8a86b794a8e47921f6ac2208b04e17da0d`
  - `long_loop_01_result_v1_1_corrected.json`（`21,315` bytes）：`2f892a1fd18a0823db25c00c076cc005bebff28ec01f16274d2b8ddadf85ad52`
- 去重封存參照：
  - `l1_tp_result.json`：`45a9f3696539b77a7629e0be165cfec41ff4fdb9add0e6b4cea2cc394ac82dbc`
  - `long_loop_01_result.json`（原檔未動）：`c8e551cc4e9b8f28aa6511762e71762d4ecf4434b2032cd86c216e7f1bc655d8`

### 缺口
- 私人 20 檔 `RESEARCH-LOOP-01-PACK-v1.1.tar.gz` 與完整更正版 `long_loop_01_result_v1_1_corrected.json` 仍待 77 透過私人通道交付實體給 ChatGPT。
- 既有回測未序列化逐事件持倉資金費名冊，維持「未保存」；完整事件名冊與 `LONG-STRUCT-01 v1.0` 最小 2 次 replay 皆須待私人包到達並獲核定後再執行。
- 既有 BTC 1D 邊界 `0 ms` 名目可用假設與既有首棒撮合敏感度限制維持保留，不另重跑。

### 下一步
- 待 77 完成私人實體交付，並待 ChatGPT 覆核私人包與 `LONG-STRUCT-01 v1.0` 預登記規格後，再決定是否啟動最小 2 次 replay；空單凍結規格與 14 天前向觀測維持不動。
