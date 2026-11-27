#!/usr/bin/env python3
# =====================================================================
# SANITIZED OFFLINE RESEARCH REFERENCE COPY (PUBLIC REPOSITORY)
# Research ID: RETEST24 R1/R2 v1.5 | Status: 凍結 (FROZEN) | live_approved: false
# Offline-only reference: config.json credential loading and CLI live/demo
# execution entrypoints are intentionally disabled in this public copy.
# OkxClient construction and HTTP methods raise OFFLINE_RESEARCH_COPY_NETWORK_DISABLED.
# No flag or environment variable re-enables network or live trading.
# =====================================================================
# -*- coding: utf-8 -*-
"""
OKX 永續合約腳本｜RETEST24 R1 / R2 可切換版
版本：v1.5-auditfix (離線審核修復候選版；NO-GO；未經全角色覆核、--demo 實測與用戶核准前，不得標示可直接實盤)
取代：v1.4-auditfix (sha256 95835e02c33e65b088a445ea30e50183d696601da1913a0d563c04884ba5613a)；v1.4 原檔保留不動。
v1.5 修復項目（風險管理／執行實測 UNKNOWN-RECOVERY-01 BLOCKER）：
  * 移除 51603 + 60s 寬限自動釋放（NOT_FOUND_GRACE_MS / RESOLVED_NOT_PLACED 自動轉換已刪除）。
  * 「可能已受理但暫不可見」一律維持 UNKNOWN_SUBMIT（持續計入 occupied 與 active_slots，HALT_UNKNOWN_INTENT，
    不重送、不撤單、不平倉）：送單逾時／斷線／5xx／非明確錯誤；送單僅有頂層錯誤碼而無單筆 sCode（網關錯誤、空 data）；
    送單回傳 sCode≠0 但帶有 ordId；查單 51603（不論經過多久）；查單逾時／5xx／限流；查單回傳 clOrdId 不符或狀態不明。
  * 「已證明未受理」才可自動解除：
    (a) 送單同步明確拒單：code ∈ {"0","1","2"} 且 data[0].sCode 非空非 "0" 且 data[0].ordId 為空 → RESOLVED_REJECTED；
    (b) 查單回傳同一 clOrdId 終態 canceled/mmp_canceled 且 accFillSz == 0 → RESOLVED_CANCELED。
  * 人工核對顯式解除：--resolve-unknown-intent <clOrdId> --resolve-reason "<audit note>"（或 resolve_unknown_intent()）；
    需非空原因；先查單，若交易所顯示委託存在／已成交則拒絕解除並改轉 CONFIRMED；解除寫入 state.intent_audit
    （時間、原狀態、新狀態、原因、操作者、查單結果）。平常掃描絕不自動解除。
  * 延遲恢復可見：查單見 live/partially_filled/filled → CONFIRMED + ledger；原單、部分成交持倉與意圖以 instId
    唯一實體合併計 1 槽，不重送、不超限。
（以下 v1.4 說明保留）
版本（前版）：v1.4-auditfix
取代：v1.3-auditfix (sha256 ede9dde41c38b0275baa1912b054516a3db65ddd6db4fab4e6e848ad1fc28850)；v1.3 原檔保留不動。
v1.4 修復項目（全組覆核 G-4-OWNERSHIP-01 BLOCKER ＋ 同批收斂）：
  G-4-OWNERSHIP-01 (BLOCKER)：
     * is_managed_clord() 改嚴格正則 ^R24R[12]YYMMDDHH<序號2~3位>(TS)?$（next_clord_id 實際格式）；
       is_similar_prefix_clord()：以 R24 開頭但不符嚴格格式（如 R24R2FAKEEXT99、R24R1EXT99）→ 疑似外部。
     * 占用與所有權分離：疑似前綴之掛單/algo/持倉只入 occupied 並記 ownership_unknown → HALT_OWNERSHIP_UNKNOWN；
       絕不認領進 family_positions/family_pending，絕不撤銷或操作。
     * _position_is_ours() 三態：cTime==0/缺失 → None（未知）→ 只入 occupied + ownership_unknown。
     * check_daily_realized_pnl()：歸因倉位以 orders-history 交叉核對（本策略 clOrdId 成交張數 vs 倉位
       openMaxPos/closeTotalPos；同倉位時間窗內任何非本策略開空成交）→ 混合或無法核對 → pnl_ok=False
       （HALT_PNL_OWNERSHIP_UNKNOWN），絕不把合併倉位 realizedPnl 灌入本策略。
       本機 state 無任何家族紀錄但當日有空單平倉紀錄、且無法以 orders-history 完整解釋為外部成交 → pnl_ok=False，
       絕不假定 0.0 U；本輪對帳存在 ownership_unknown → pnl_ok=False。
  C2 跨日部分平倉增量：同一 (instId,posId,cTime) 視為累計值；當日損益 = 今日最後一筆 realizedPnl − 基準；
     基準 = 台北 00:00 前最後一筆（分頁延伸至最早歸因倉位 cTime），否則取 state.pnl_marks 中 00:00 前之紀錄，皆無則 0。
     ※ OKX positions-history 對「部分平倉中」倉位之 realizedPnl 是否為累計值、是否逐次產生紀錄，須於 --demo 實測驗證。
  保護單異常與日虧同輪：HALT_PROTECTION_UNVERIFIED / HALT_OWNERSHIP_UNKNOWN / HALT_UNKNOWN_INTENT 不再提前 return；
     同輪仍計算日虧，達上限即 cancel_family_entries_on_daily_halt()（只撤嚴格格式家族進場單），最終一律 0 筆新單。
  E2 可用保證金預檢：GET /api/v5/account/balance?ccy=USDT（availEq，缺則 availBal）；失敗 → HALT_BALANCE_UNKNOWN；
     每筆候選估算 notional/lever + notional*(maker+taker) 再乘 MARGIN_BUFFER，扣減本輪已預留，不足即跳過該筆。
  Minor：① ledger 依 last_seen_ms（無則 created_ms）清理；已結案 intents 超過保留期清理，並設 INTENT_MAX_RESOLVED 上限，
     保留當日與未結案意圖。② --dry-run 全程唯讀：save_state() 不寫檔（含 active_profile）。
     ③ set-leverage：先 GET /api/v5/account/leverage-info，已為 10x 不 POST；--skip-set-leverage 完全不碰；
     查詢失敗跳過該筆；已占用幣種一律不碰。
  動態標的：state=="live"、settleCcy=="USDT"、ctType=="linear"、instCategory（若有）=="1"；排除清單＝內建
     DEFAULT_EXCLUDED_BASES ∪ --exclude-file；名稱含 USD 且未列名者，近 30 根 1D 高低波幅 < 5% 或 K 線取得失敗
     → 隔離並告警（HALT_STABLECOIN_ANOMALY 告警，僅排除該標的，不影響其他標的）。
  訊號掃描（calc_indicators/evaluate_signal/scan_candidates/fetch_4h_history/align_tick_*/compute_order_plan/
     SIGNAL_SPECS 與訊號常數）與 v1.1/v1.2/v1.3 逐字相同；fetch_universe / EXCLUDED_BASES 屬標的池過濾，依第 5 項刻意變更。
（以下 v1.3 說明保留）
版本（前版）：v1.3-auditfix
取代：v1.2-auditfix (sha256 aa003596c0d3db10d419c9ae5a5ab5bc19e34e8e1ee3c75e1555c2a55fe8679a)；v1.2 原檔保留不動。
v1.3 修復項目（開單審核第三次複驗）：
  CHECKLIST-D-DAILY-LOSS-CANCEL-PENDING (HIGH)：觸發日虧停機（attributed_pnl <= -daily_loss_limit）時，
     呼叫 cancel_family_entries_on_daily_halt()：只撤 RETEST24 全家族（R24R1/R24R2）未成交進場掛單
     （orders-pending 中 clOrdId 為家族前綴者）；不碰任何 algo 單（TP/SL 保護單保留）、不平倉、不碰外部單。
     逐筆檢查 code 與 sCode；成功且未成交 → ledger/intent 標記 RESOLVED_CANCELED；成功但已部分成交 →
     保留原狀態（持倉仍受管）僅記 cancel_ack；失敗（含已成交）→ 不假裝成功、不刪紀錄，記錄失敗原因；
     撤單後重新對帳刷新狀態；--dry-run 只列擬撤清單不送撤單；最後存檔並回傳 HALT_DAILY_LOSS（開 0 筆新倉）。
     ※ 與 Q28/Q29 回測差異：回測觸發日虧僅阻擋新訊號，不撤既有掛單；此為 77 定案之實盤風控強化。
  check_family_protection()：pos_sz 只累加空方倉位（posSide=short，或單向模式 pos<0）的絕對張數，
     與本策略只做空、TP/SL 只保護空倉的語意一致；同幣外部多倉不再計入（避免語意混淆），
     空方覆蓋不足仍判不完整 → 停開新倉。
  訊號掃描函式與常數與 v1.1 / v1.2 逐字相同（v1.1 對 Q28/Q29 引擎 8187/8187 = 100% 一致）。
（以下 v1.2 說明保留）
版本（前版）：v1.2-auditfix
取代：v1.1-auditfix (sha256 e6e112cd9c4183f31c62678080aa60a36be25ad5b634efb6ecbfa24a802f6484)；v1.1 原檔保留不動。
v1.2 修復項目（開單審核二次複驗殘留缺口）：
  EXTRA-01-MOVE-ORDER-STOP-OMITTED (BLOCKER)：reconcile_account() 的 algo 掛單查詢改為完整覆蓋
     ("conditional", "oco", "trigger", "move_order_stop")，各型別皆分頁；任一型別查詢失敗 → 對帳失敗 → 停開新倉；
     任何 algo 掛單（含移動止損 move_order_stop）所在幣種一律列入 occupied。
     保護單型別區分：只有 RETEST24 自己附掛的 TP/SL（algoClOrdId=<clOrdId>TS，型別 oco/conditional，
     且 tpTriggerPx 與 slTriggerPx 皆有值）才算「本策略保護單」；trigger / move_order_stop 只用於占用互斥，不算保護。
  EXTRA-02-ACKED-FILL-PROTECTION-UNCHECKED (HIGH)：新增 check_family_protection()，每輪於撤單後對帳完成時，
     對「所有」RETEST24 持倉（不論來源是正常受理 ACKED、崩潰恢復 CONFIRMED，或僅由 algo 認定）實際回查交易所
     pending algo：雙邊 TP/SL 齊全且數量覆蓋持倉 → 清除 protection_unverified；缺單或不完整 → 標記
     protection_unverified 並停開新倉（不補單、不撤單、不平倉）；已無持倉（正常平倉）→ 清除旗標正常收斂。
     reconcile_intents() 只負責未決意圖的存在性對帳，保護單檢核統一交由 check_family_protection()。
  訊號掃描（calc_indicators / evaluate_signal / scan_candidates / fetch_4h_history / align_tick_str /
     compute_order_plan / SIGNAL_SPECS）與 v1.1 逐字相同（v1.1 對 Q28/Q29 引擎 8187/8187 = 100% 一致）。
（以下 v1.1 說明保留）
====================================================================================
對應研究交接：[ChatGPT研究交接] RETEST24-RELEASE-AUDIT-01 v1.0 (GitHub Issue #1 comment #7200864466)
取代：RETEST24_R1_R2_Switchable.py v1.0 (sha256 7f87a1f00eb17725cec13eb472045ba2467d9e65cc3c5fa421a3a651acf31a78)
      ※ v1.0 原檔保留不動，本檔為隔離副本。

策略：breakout_retest_short（4H 跌破前低後回抽做空，僅做空）
  ─ 訊號口徑「對齊產出 Q28/Q29 result.json 的回測引擎 sim_50k_v3.run_v3」
    （亦即 audit_v3_1_full.build_cands / sim_50k_v3_2_sl_fix 共用之訊號規則）：
      * EMA 期數 55（k = 2/56，以前 55 根收盤 SMA 起算）── v1.0 誤用 signals_v2.py 的 EMA60
      * Wilder RSI(14) ∈ [20, 40]
      * 收盤 cp < EMA55；pl = 前 12 根（i-13..i-2）最低價；需 cp < pl 且 當根開盤 op < pl
      * 進場價 raw = pl × 0.9995（v1.0 誤用 pl），dist = (raw-op)/op ∈ [0, 0.15]（v1.0 誤用 [0.0005, 0.10]）
      * 價格 floor 對齊 tickSz；排序 sort_key = -RSI（RSI 高者優先）
      * 上市檢查：當根所屬台北日之前 60 個台北日的 1D K 線必須全數存在（同回測 d1_set 檢查）
      * 指標暖機：抓取最多 INDICATOR_BARS 根已收盤 4H（v1.0 僅 99 根，EMA 種子殘差顯著）
  ─ 可用 SIGNAL_SPEC = "signals_v2_legacy" 切回 v1.0 口徑（僅供比對，非 Q28/Q29 口徑）。

R1 / R2：
  - R2 (預設，對應 Q29)：單筆風險 100 USDT / 日虧上限 400 USDT / 上限 12 槽
  - R1 (對應 Q28)     ：單筆風險 150 USDT / 日虧上限 600 USDT / 上限 12 槽
  - 兩者屬同一策略家族 RETEST24；槽位、逾時撤單、日虧歸因一律以「家族」為單位計算，
    切換 R1<->R2 時，另一 profile 遺留的掛單／持倉仍計入槽位並受 24h 逾時撤單管理。

v1.1 修復項目（對應審核缺陷 #2～#5）：
  #2 跨 profile 所有權：辨識所有 RETEST24 前綴（R24R1/R24R2）與 state 中 strategy_family="RETEST24"
     之 ledger / intents；記錄 profile 切換歷史；跨平台單例檔案鎖（fcntl.flock / msvcrt.locking）
     包住整輪（含槽位分配），第二個程序取鎖失敗即乾淨中止。
  #3 日虧歸因：positions-history 以 after 游標分頁直到台北 00:00 之前或資料耗盡（不止於 100 筆）；
     只歸因 RETEST24 ledger 內的交易（instId + posSide=short + cTime 落在本策略委託建立後之成交窗）；
     realizedPnl 已含 pnl+fee+fundingFee+liqPenalty，不重複加計；任一頁失敗 → pnl_ok=False → 停開新倉。
  #4 撤單：每筆同時檢查頂層 code=="0" 與 data[0].sCode=="0"；絕不以撤單數扣減槽位；
     撤單後一律重新查詢持倉＋掛單並以「唯一 instId 實體」重算槽位（部分成交後撤單仍佔 1 槽）；
     重算失敗 → 狀態未知 → 停開新倉。
  #5 預寫意圖（write-ahead intent）：送出 POST /api/v5/trade/order 前，先以 flush+fsync+os.replace
     原子寫入 PENDING_SUBMIT 意圖；每輪啟動先以 GET /api/v5/trade/order?instId&clOrdId 對帳所有
     PENDING_SUBMIT/UNKNOWN_SUBMIT 意圖：確認存在 → 升級 CONFIRMED 並核對附掛 TP/SL；
     確認撤銷/拒單/51603 不存在（且意圖已超過寬限期）→ 結案；查詢失敗/逾時 → 本輪停開新倉，
     絕不盲目重送、絕不無條件撤單或平倉。每一次單筆狀態轉換後立即持久化。

日虧歸因與換日規格（Ledger & Taipei 00:00 reset spec）：
  - 換日點：台北時間 (UTC+8) 每日 00:00:00.000；begin_ms = 當日台北 00:00 之 epoch ms。
    （注意：Q28/Q29 回測以 UTC 00:00 換日，兩者相差 8 小時，屬已知口徑差異。）
  - 資料源：GET /api/v5/account/positions-history?instType=SWAP&limit=100[&after=<最舊一筆 uTime>]
    依 uTime 由新到舊分頁；當頁最舊 uTime < begin_ms 或回傳筆數 < limit 即停止；
    頁數超過 PNL_MAX_PAGES 視為未知（pnl_ok=False）。
  - 歸因：row.uTime >= begin_ms，且 row.instId 存在於 ledger（任一 RETEST24 profile），
    row.posSide=="short"（或單向持倉模式下 direction=="short"），
    且 ledger.created_ms - 5s <= row.cTime <= ledger.created_ms + TTL + 60s（委託建立後、逾時撤單前成交開倉）。
    同一 (posId, cTime, uTime) 只計一次。外部 F4V3 倉位、本策略建單前即已存在之倉位一律排除。
  - 金額：只取 realizedPnl（OKX 定義已含平倉損益、手續費、資金費與強平罰金），不再另加 fee/fundingFee。
  - 停機：attributed_pnl <= -daily_loss_limit → 當日停開新倉；pnl_ok=False → 本輪停開新倉。

安全預設：DRY_RUN = True；--live 才會送單；--demo 走模擬盤。
本檔為離線審核候選版，未經全角色覆核與用戶核准前，不得標示可直接實盤。
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import json
import math
import os
import re
import sys
import time
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

try:  # requests 僅實盤需要；離線測試以 mock client 注入
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

SCRIPT_VERSION = "v1.5-auditfix"
RELEASE_STATUS = "離線審核修復候選版；未經全角色覆核與用戶核准前，不得標示可直接實盤"

# =====================================================================
# 1. 使用者切換區
# =====================================================================
PROFILE = "R2"
DRY_RUN = True
DEMO_TRADING = False
COUNT_EXTERNAL_SLOTS = False

STRATEGY_FAMILY = "RETEST24"
PROFILES = {
    "R1": {"name": "Q28-RETEST24-R1", "risk_per_trade": 150.0, "daily_loss_limit": 600.0,
           "max_slots": 12, "clord_prefix": "R24R1"},
    "R2": {"name": "Q29-RETEST24-R2", "risk_per_trade": 100.0, "daily_loss_limit": 400.0,
           "max_slots": 12, "clord_prefix": "R24R2"},
}
MANAGED_PREFIXES: Tuple[str, ...] = tuple(p["clord_prefix"] for p in PROFILES.values())
FAMILY_MAX_SLOTS = 12   # 家族共用槽位上限（R1/R2 不可疊加為 24）

# 訊號口徑
SIGNAL_SPEC = "sim_50k_v3"          # "sim_50k_v3"（Q28/Q29 回測口徑）或 "signals_v2_legacy"（v1.0 口徑）
SIGNAL_SPECS = {
    "sim_50k_v3":        {"ema_period": 55, "entry_mult": 0.9995, "dist_min": 0.0,    "dist_max": 0.15,
                          "require_open_below": True,  "listing_check": "taipei_d1_60"},
    "signals_v2_legacy": {"ema_period": 60, "entry_mult": 1.0,    "dist_min": 0.0005, "dist_max": 0.10,
                          "require_open_below": False, "listing_check": "count_60"},
}
LEVERAGE = 10
LOOKBACK = 12
RSI_PERIOD = 14
RSI_LO = 20.0
RSI_HI = 40.0
SL_PCT = 0.05
TP_PCT = 0.05
TTL_HOURS = 24
MIN_LISTING_DAYS = 60
INDICATOR_BARS = 600                 # 已收盤 4H 暖機根數（EMA55 殘差 ≈ (54/56)^540 ≈ 3e-9）

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005
SLIP_MKT = 0.0005                    # 實盤保守停損滑價（回測為 0.0003）

DEFAULT_EXCLUDED_BASES = {
    "BTC", "ETH", "USDC", "USDT", "DAI", "TUSD", "FDUSD", "USDG", "PYUSD", "USDE", "USD1", "RLUSD",
    "XAU", "XAG", "XAUT", "PAXG",
    # v1.1~v1.3 既有清單保留（較保守）
    "USDP", "EURC", "USTC", "BUSD",
}
EXCLUDED_BASES = set(DEFAULT_EXCLUDED_BASES)   # 執行時 ∪ --exclude-file
STABLE_GUARD_RANGE = 0.05                      # 名稱含 USD 未列名標的：30 日高低波幅 < 5%（=TP/SL 門檻）→ 隔離
STABLE_GUARD_DAYS = 30

BASE_URL = "https://www.okx.com"
TZ_TAIPEI = datetime.timezone(datetime.timedelta(hours=8))
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
STATE_FILE = SCRIPT_DIR / "retest24_v11_state.json"
LOG_FILE = SCRIPT_DIR / "retest24_v11_live.log"
# 機器層級家族鎖：即使 R1/R2 放在不同資料夾，同一台機器上也只允許一個 RETEST24 程序執行一輪
import tempfile as _tempfile
LOCK_FILE = Path(_tempfile.gettempdir()) / "RETEST24_family_v11.lock"

H4_MS = 14_400_000
DAY_MS = 86_400_000
H8_MS = 28_800_000
TTL_MS = TTL_HOURS * 3600 * 1000
PNL_MAX_PAGES = 50
LIST_MAX_PAGES = 20
# v1.5：已移除 51603 寬限期常數；51603 不論經過多久都不得視為「確認未下單」（UNKNOWN-RECOVERY-01）
LEDGER_RETENTION_MS = 3 * DAY_MS
INTENT_RETENTION_MS = 3 * DAY_MS
INTENT_MAX_RESOLVED = 500
ORDERS_HISTORY_WINDOW_MS = 7 * DAY_MS      # orders-history 僅近 7 日；更早開倉無法核對 → 未知
MARGIN_BUFFER = 1.10
SKIP_SET_LEVERAGE = False
_STATE_READ_ONLY = False                   # --dry-run：save_state() 不寫檔
CLORD_RE = re.compile(r"^R24R[12]\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([01]\d|2[0-3])\d{2,3}(TS)?$")

OCCUPANCY_ALGO_TYPES: Tuple[str, ...] = ("conditional", "oco", "trigger", "move_order_stop")
PROTECTION_ALGO_TYPES: Tuple[str, ...] = ("oco", "conditional")   # 附掛 TP/SL 成交後的型別；trigger/move_order_stop 不算保護

INTENT_PENDING = "PENDING_SUBMIT"
INTENT_UNKNOWN = "UNKNOWN_SUBMIT"
INTENT_ACKED = "ACKED"
INTENT_CONFIRMED = "CONFIRMED"
INTENT_REJECTED = "RESOLVED_REJECTED"
INTENT_CANCELED = "RESOLVED_CANCELED"
INTENT_NOT_PLACED = "RESOLVED_NOT_PLACED"     # v1.5 起不再自動產生（僅保留以相容舊 state）
INTENT_MANUAL = "RESOLVED_MANUAL_CLEARED"     # 人工核對後顯式解除
UNRESOLVED_INTENT = {INTENT_PENDING, INTENT_UNKNOWN}
LIVE_INTENT = {INTENT_PENDING, INTENT_UNKNOWN, INTENT_ACKED, INTENT_CONFIRMED}


class LockContention(RuntimeError):
    pass


# =====================================================================
# 2. 日誌 / 狀態（耐久原子寫入）/ 單例鎖
# =====================================================================
def now_taipei() -> datetime.datetime:
    return datetime.datetime.now(TZ_TAIPEI)


def now_ms() -> int:
    return int(time.time() * 1000)


def log(msg: str) -> None:
    line = f"[{now_taipei().strftime('%Y-%m-%d %H:%M:%S CST')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _empty_state() -> Dict[str, Any]:
    return {
        "schema": "retest24-state-v1.1",
        "strategy_family": STRATEGY_FAMILY,
        "last_bar_ms": 0,
        "active_profile": None,
        "profile_history": [],      # [{ts_ms, from, to}]
        "managed_insts": {},        # instId -> 最新 ledger 摘要（相容 v1.0）
        "ledger": {},               # clOrdId -> {strategy_family, profile, owner_prefix, instId, created_ms, ..., status}
        "intents": {},              # clOrdId -> write-ahead intent
        "placed_bars": {},          # "{bar_ms}:{instId}" -> clOrdId
        "clord_seq": {},            # "{prefix}:{bar_ms}" -> 已用最大序號
    }


def load_state() -> Dict[str, Any]:
    base = _empty_state()
    if STATE_FILE.exists():
        # 狀態檔損毀 ≠ 空狀態：拋例外讓呼叫端停手，不得以空白狀態續跑
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for k, v in base.items():
            data.setdefault(k, v)
        return data
    return base


def save_state(state: Dict[str, Any]) -> None:
    """耐久原子寫入：寫 tmp → flush → fsync → os.replace → fsync 目錄（POSIX）。--dry-run 時不寫檔。"""
    if _STATE_READ_ONLY:
        return
    tmp = STATE_FILE.with_name(STATE_FILE.name + ".tmp")
    data = json.dumps(state, indent=2, ensure_ascii=False)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE_FILE)
    if os.name == "posix":
        try:
            dfd = os.open(str(STATE_FILE.parent), os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except Exception:
            pass


class SingleInstanceLock:
    """跨平台非阻塞單例鎖。取鎖失敗拋 LockContention。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.fh = None

    def __enter__(self):
        self.fh = open(self.path, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError) as e:
            self.fh.close()
            self.fh = None
            raise LockContention(f"另一個 RETEST24 程序正持有鎖 {self.path}: {e}")
        try:
            self.fh.seek(0)
            self.fh.truncate()
            self.fh.write(f"pid={os.getpid()} ts_ms={now_ms()}\n")
            self.fh.flush()
        except Exception:
            pass
        return self

    def __exit__(self, *exc):
        if self.fh is not None:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.fh.seek(0)
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            finally:
                self.fh.close()
                self.fh = None
        return False


def floor_step(val: float, step: float) -> str:
    if step <= 0:
        return f"{val:.8f}".rstrip("0").rstrip(".")
    d_val = Decimal(str(val))
    d_step = Decimal(str(step))
    q = (d_val / d_step).to_integral_value(rounding=ROUND_DOWN) * d_step
    return format(q.normalize(), "f")


def is_managed_clord(cl: Any) -> bool:
    """G-4：嚴格格式 R24R1/R24R2 + YYMMDDHH + 2~3 位序號 + 可選 TS（附掛 TP/SL）。"""
    return bool(CLORD_RE.match(str(cl or "")))


def is_similar_prefix_clord(cl: Any) -> bool:
    """以 R24 開頭（不分大小寫）但不符嚴格格式 → 疑似外部／仿冒，只能占用、不可認領。"""
    s = str(cl or "")
    return s.upper().startswith("R24") and not is_managed_clord(s)


def prefix_profile(cl: str) -> Optional[str]:
    for k, p in PROFILES.items():
        if str(cl).startswith(p["clord_prefix"]):
            return k
    return None


def ok_item(res: Dict[str, Any]) -> bool:
    """單筆交易類回應：頂層 code=="0" 且 data[0].sCode=="0" 才算成功。"""
    if not isinstance(res, dict) or res.get("code") != "0":
        return False
    data = res.get("data") or []
    return bool(data) and str(data[0].get("sCode", "")) == "0"


# =====================================================================
# 3. OKX API
# =====================================================================
class OkxClient:
    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", demo: bool = False):
        # Permanent offline refusal. No flag or environment variable re-enables network access.
        raise RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: OkxClient network access is permanently disabled in this sanitized research copy.")
        self.api_key, self.secret_key, self.passphrase, self.demo = api_key, secret_key, passphrase, demo
        self.session = requests.Session() if requests is not None else None
        if self.session is not None:
            self.session.headers.update({"User-Agent": "curl/8.0"})

    @property
    def has_auth(self) -> bool:
        return bool(self.api_key and self.secret_key and self.passphrase)

    def _iso_ts(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def public_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Permanent offline refusal. No flag or environment variable re-enables network access.
        raise RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: OkxClient network access is permanently disabled in this sanitized research copy.")
        url = BASE_URL + path
        for attempt in range(3):
            try:
                r = self.session.get(url, params=params, timeout=15)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                if attempt == 2:
                    return {"code": "error", "msg": str(e), "data": []}
                time.sleep(0.5 * (attempt + 1))
        return {"code": "error", "msg": "unknown", "data": []}

    def private_req(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                    body_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Permanent offline refusal. No flag or environment variable re-enables network access.
        raise RuntimeError("OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: OkxClient network access is permanently disabled in this sanitized research copy.")
        if not self.has_auth:
            return {"code": "no_auth", "msg": "config.json 未設定 API 憑證", "data": []}
        method = method.upper()
        req_path = path
        if method == "GET" and params:
            qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if qs:
                req_path = f"{path}?{qs}"
        body = json.dumps(body_dict, separators=(",", ":")) if (method == "POST" and body_dict is not None) else ""
        ts = self._iso_ts()
        sign = base64.b64encode(hmac.new(self.secret_key.encode(), f"{ts}{method}{req_path}{body}".encode(),
                                         hashlib.sha256).digest()).decode()
        headers = {"OK-ACCESS-KEY": self.api_key, "OK-ACCESS-SIGN": sign, "OK-ACCESS-TIMESTAMP": ts,
                   "OK-ACCESS-PASSPHRASE": self.passphrase, "Content-Type": "application/json"}
        if self.demo:
            headers["x-simulated-trading"] = "1"
        try:
            r = self.session.request(method, BASE_URL + req_path, headers=headers,
                                     data=body if method == "POST" else None, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            # 傳輸層錯誤 / 逾時：送單結果「未知」，呼叫端不得視為失敗或成功
            return {"code": "error", "msg": str(e), "data": [], "transport_error": True}


def load_config_credentials() -> Tuple[str, str, str]:
    # Disabled in sanitized public offline-research copy (no config.json / API keys).
    return "", "", ""


# =====================================================================
# 4. 指標（逐行對齊 sim_50k_v3.indicators / audit_v3_1_full.indicators）
# =====================================================================
def calc_indicators(closes: np.ndarray, ema_period: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    ema_period = int(ema_period or SIGNAL_SPECS[SIGNAL_SPEC]["ema_period"])
    n = len(closes)
    ema = np.full(n, np.nan)
    rsi = np.full(n, np.nan)
    if n < ema_period:
        return ema, rsi
    k = 2.0 / (ema_period + 1.0)
    ema[ema_period - 1] = float(np.mean(closes[:ema_period]))
    for i in range(ema_period, n):
        ema[i] = closes[i] * k + ema[i - 1] * (1.0 - k)
    df = np.diff(closes)
    g = float(np.mean(np.maximum(df[:RSI_PERIOD], 0.0)))
    lo = float(np.mean(np.maximum(-df[:RSI_PERIOD], 0.0)))
    rsi[RSI_PERIOD] = 100.0 * g / (g + lo) if (g + lo) else 50.0
    for i in range(RSI_PERIOD, n - 1):
        d = df[i]
        g = (g * (RSI_PERIOD - 1.0) + (d if d > 0 else 0.0)) / RSI_PERIOD
        lo = (lo * (RSI_PERIOD - 1.0) + (-d if d < 0 else 0.0)) / RSI_PERIOD
        rsi[i + 1] = 100.0 * g / (g + lo) if (g + lo) else 50.0
    return ema, rsi


def align_tick_float(px: float, t: float) -> float:
    return math.floor(px / t) * t if t > 0 else px


def align_tick_str(px: float, t: float) -> str:
    """與回測 align_tick 相同的 tick 索引 n = floor(px/t)（含其浮點行為），再以 Decimal 輸出精確字串。"""
    if t <= 0:
        return floor_step(px, 0)
    n = math.floor(px / t)
    return format((Decimal(n) * Decimal(str(t))).normalize(), "f")


def evaluate_signal(closed_bars: List[List[Any]], cur_bar: List[Any], tick_sz: float,
                    d1_ts: Optional[Set[int]] = None, spec_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    純函式：給定由舊到新的已收盤 4H K 線（OKX 格式 [ts,o,h,l,c,...]）與當根（未收盤）K 線，
    依 SIGNAL_SPEC 計算是否產生 breakout_retest_short 掛單訊號。
    """
    sp = SIGNAL_SPECS[spec_name or SIGNAL_SPEC]
    ema_period = sp["ema_period"]
    if len(closed_bars) < max(ema_period, LOOKBACK + 1) + 1:
        return None
    bt = int(cur_bar[0])
    if int(closed_bars[-1][0]) != bt - H4_MS:
        return None
    closes = np.array([float(x[4]) for x in closed_bars], dtype=float)
    lows = np.array([float(x[3]) for x in closed_bars], dtype=float)
    ema, rsi = calc_indicators(closes, ema_period)
    cp, ep, rp = float(closes[-1]), float(ema[-1]), float(rsi[-1])
    if math.isnan(ep) or math.isnan(rp):
        return None
    if cp >= ep or not (RSI_LO <= rp <= RSI_HI):
        return None
    if sp["listing_check"] == "taipei_d1_60":
        if d1_ts is None:
            return None
        dk = (bt + H8_MS) // DAY_MS * DAY_MS - H8_MS
        if not all((dk - d * DAY_MS) in d1_ts for d in range(1, MIN_LISTING_DAYS + 1)):
            return None
    else:
        if d1_ts is None or len(d1_ts) < MIN_LISTING_DAYS:
            return None
    op = float(cur_bar[1])
    pl = float(np.min(lows[-(LOOKBACK + 1):-1]))
    if sp["require_open_below"]:
        if not (cp < pl and op < pl):
            return None
    elif cp >= pl:
        return None
    raw_px = pl * sp["entry_mult"]
    dist = (raw_px - op) / op
    if not (sp["dist_min"] <= dist <= sp["dist_max"]):
        return None
    px_str = align_tick_str(raw_px, tick_sz)
    entry_px = float(px_str)
    if entry_px <= 0:
        return None
    return {"sort_key": -rp, "bar_ms": bt, "entry_px": entry_px, "entry_px_str": px_str, "raw_px": raw_px,
            "close_prev": cp, "ema": ep, "rsi14": rp, "op": op, "pl": pl, "dist_pct": dist * 100.0,
            "signal_spec": spec_name or SIGNAL_SPEC}


# =====================================================================
# 5. 標的池 / 分頁查詢 / 對帳 / 撤單 / 日虧
# =====================================================================
def fetch_universe(client) -> List[Dict[str, Any]]:
    res = client.public_get("/api/v5/public/instruments", {"instType": "SWAP"})
    if res.get("code") != "0":
        raise RuntimeError(f"取得 SWAP 標的失敗: {res}")
    out = []
    for item in res.get("data", []):
        if item.get("state") != "live" or item.get("settleCcy") != "USDT":
            continue
        if item.get("ctType") != "linear":
            continue
        if "instCategory" in item and str(item.get("instCategory")) != "1":
            continue
        inst_id = item["instId"]
        if inst_id.split("-")[0].upper() in EXCLUDED_BASES:
            continue
        out.append({"instId": inst_id, "ctVal": float(item["ctVal"]), "lotSz": float(item["lotSz"]),
                    "minSz": float(item["minSz"]), "tickSz": float(item["tickSz"])})
    return out


def load_exclude_file(path: Optional[str]) -> Set[str]:
    """--exclude-file：每行一個 base（# 註解），或 JSON 陣列；讀取失敗直接拋例外（fail-closed，不以空清單續跑）。"""
    if not path:
        return set()
    txt = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(txt)
        if isinstance(data, list):
            return {str(x).strip().upper() for x in data if str(x).strip()}
    except ValueError:
        pass
    out = set()
    for line in txt.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line.upper())
    return out


def stablecoin_guard(client, universe: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """名稱含 USD 且未列名之標的：近 30 根 1D 高低波幅 < STABLE_GUARD_RANGE 或資料不可得 → 隔離告警。"""
    kept: List[Dict[str, Any]] = []
    isolated: List[Dict[str, Any]] = []
    for u in universe:
        base = u["instId"].split("-")[0].upper()
        if "USD" not in base or base in EXCLUDED_BASES:
            kept.append(u)
            continue
        r = client.public_get("/api/v5/market/candles",
                              {"instId": u["instId"], "bar": "1Dutc", "limit": str(STABLE_GUARD_DAYS)})
        rows = r.get("data") or [] if r.get("code") == "0" else []
        try:
            hi = max(float(x[2]) for x in rows)
            lo = min(float(x[3]) for x in rows)
            rng = (hi - lo) / lo if lo > 0 else 0.0
        except (ValueError, IndexError, TypeError):
            rng = None
        if rng is None or rng < STABLE_GUARD_RANGE:
            isolated.append({"instId": u["instId"], "range_30d": rng})
            log(f"🚨 HALT_STABLECOIN_ANOMALY：{u['instId']} 疑似穩定幣（30 日波幅 {rng}）→ 隔離不交易，請確認後加入排除清單。")
        else:
            kept.append(u)
    return kept, isolated


def _paged_list(client, path: str, params: Dict[str, Any], cursor_key: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """以 after=<最後一筆 id> 分頁，直到回傳 < 100 筆；任何一頁失敗 → (False, [])。"""
    rows: List[Dict[str, Any]] = []
    after: Optional[str] = None
    for _ in range(LIST_MAX_PAGES):
        p = dict(params)
        p["limit"] = "100"
        if after:
            p["after"] = after
        r = client.private_req("GET", path, p)
        if r.get("code") != "0":
            return False, []
        data = r.get("data", []) or []
        rows.extend(data)
        if len(data) < 100:
            return True, rows
        after = str(data[-1].get(cursor_key, ""))
        if not after:
            return False, []
    return False, []


def _ledger_entries_for(state: Dict[str, Any], inst: str) -> List[Dict[str, Any]]:
    out = []
    for cl, e in state.get("ledger", {}).items():
        if e.get("strategy_family") == STRATEGY_FAMILY and e.get("instId") == inst:
            out.append(e)
    for cl, it in state.get("intents", {}).items():
        if it.get("strategy_family") == STRATEGY_FAMILY and it.get("instId") == inst and it.get("status") in LIVE_INTENT:
            out.append(it)
    return out


def _position_is_ours(state: Dict[str, Any], p: Dict[str, Any]) -> Optional[bool]:
    """三態：True=本策略；False=非本策略；None=所有權未知（cTime 缺失/0 且同幣有家族紀錄）。"""
    inst = p.get("instId")
    pos_side = str(p.get("posSide", ""))
    pos_val = float(p.get("pos", "0") or "0")
    short = pos_side == "short" or (pos_side == "net" and pos_val < 0)
    if not short:
        return False
    try:
        c_time = int(p.get("cTime", "0") or "0")
    except (TypeError, ValueError):
        c_time = 0
    ents = _ledger_entries_for(state, inst)
    if c_time <= 0:
        return None                              # G-4：cTime 缺失/0 → 所有權未知，不認領
    for e in ents:
        created = int(e.get("created_ms", 0))
        # 與日虧歸因同一成交窗：委託建立後、逾時撤單（+60s 緩衝）前開倉者才算本策略持倉
        if created - 5000 <= c_time <= created + TTL_MS + 60_000:
            return True
    return False


def reconcile_account(client, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    全帳對帳（持倉 + 一般掛單 + 條件/OCO/觸發/移動止損 algo 單，皆分頁）。
    回傳 {ok, occupied, active_insts, active_slots, family_pending}。
    active_insts = 家族持倉 instId ∪ 家族掛單 instId ∪ 未決意圖 instId（唯一實體計 1 槽）。
    """
    pos_res = client.private_req("GET", "/api/v5/account/positions", {"instType": "SWAP"})
    if pos_res.get("code") != "0":
        log(f"⚠️ 對帳失敗 (positions): {pos_res.get('code')} {pos_res.get('msg')}")
        return {"ok": False}
    ok_o, orders = _paged_list(client, "/api/v5/trade/orders-pending", {"instType": "SWAP"}, "ordId")
    if not ok_o:
        log("⚠️ 對帳失敗 (orders-pending)")
        return {"ok": False}
    algos: List[Dict[str, Any]] = []
    for ot in OCCUPANCY_ALGO_TYPES:
        ok_a, rows = _paged_list(client, "/api/v5/trade/orders-algo-pending",
                                 {"instType": "SWAP", "ordType": ot}, "algoId")
        if not ok_a:
            log(f"⚠️ 對帳失敗 (algo-{ot})；任何 algo 型別查詢失敗皆保守停開新倉")
            return {"ok": False, "failed": f"algo-{ot}"}
        for r_ in rows:
            r_ = dict(r_)
            r_["_queried_ordType"] = ot
            algos.append(r_)

    occupied: Set[str] = set()
    fam_pos: Set[str] = set()
    all_pos: Set[str] = set()
    ownership_unknown: List[Dict[str, Any]] = []
    unknown_pos_insts: Set[str] = set()
    positions = pos_res.get("data", []) or []
    for p in positions:
        if abs(float(p.get("pos", "0") or "0")) > 0:
            occupied.add(p["instId"])
            all_pos.add(p["instId"])
            own = _position_is_ours(state, p)
            if own is True:
                fam_pos.add(p["instId"])
            elif own is None:
                unknown_pos_insts.add(p["instId"])
                ownership_unknown.append({"kind": "position", "instId": p["instId"], "reason": "cTime_missing",
                                          "posId": p.get("posId")})

    fam_pending: List[Dict[str, Any]] = []
    fam_pend_insts: Set[str] = set()
    all_pend: Set[str] = set()
    for o in orders:
        occupied.add(o["instId"])
        all_pend.add(o["instId"])
        cl = o.get("clOrdId")
        if is_managed_clord(cl):
            fam_pending.append(o)
            fam_pend_insts.add(o["instId"])
        elif is_similar_prefix_clord(cl):
            ownership_unknown.append({"kind": "order", "instId": o["instId"], "clOrdId": cl,
                                      "reason": "similar_prefix"})
    fam_algo_insts: Set[str] = set()
    for a in algos:
        if a.get("instId"):
            occupied.add(a["instId"])
            ids = (a.get("algoClOrdId"), a.get("attachAlgoClOrdId"))
            # 成交後附掛 TP/SL 會轉為 algoClOrdId = <clOrdId>TS 的獨立 algo 單 → 嚴格格式才是所有權證據
            if any(is_managed_clord(x) for x in ids):
                fam_algo_insts.add(a["instId"])
            elif any(is_similar_prefix_clord(x) for x in ids):
                ownership_unknown.append({"kind": "algo", "instId": a["instId"],
                                          "clOrdId": next(x for x in ids if is_similar_prefix_clord(x)),
                                          "reason": "similar_prefix"})
    for p in positions:
        # 嚴格格式家族 algo 為所有權證據（state 遺失亦可）；所有權未知之持倉（cTime 缺失）不認領
        if abs(float(p.get("pos", "0") or "0")) > 0 and p["instId"] in fam_algo_insts \
                and p["instId"] not in unknown_pos_insts:
            fam_pos.add(p["instId"])
    if ownership_unknown:
        log(f"🚨 HALT_OWNERSHIP_UNKNOWN：{ownership_unknown}；只列占用、不認領、不操作，停開新倉。")

    intent_insts = {it["instId"] for it in state.get("intents", {}).values()
                    if it.get("status") in UNRESOLVED_INTENT}
    occupied |= intent_insts

    active_insts = fam_pos | fam_pend_insts | intent_insts
    active_slots = len(all_pos | all_pend | intent_insts) if COUNT_EXTERNAL_SLOTS else len(active_insts)

    # 更新 ledger / managed_insts 狀態（只標記，不刪除，日虧歸因需要歷史）
    t = now_ms()
    for cl, e in state.get("ledger", {}).items():
        inst = e.get("instId")
        e["live"] = inst in active_insts
        if e["live"]:
            e["last_seen_ms"] = t
    state["managed_insts"] = {}
    for cl, e in state.get("ledger", {}).items():
        if e.get("live"):
            prev = state["managed_insts"].get(e["instId"])
            if prev is None or e.get("created_ms", 0) >= prev.get("created_ms", 0):
                state["managed_insts"][e["instId"]] = {k: e.get(k) for k in
                                                      ("clOrdId", "ordId", "profile", "owner_prefix",
                                                       "strategy_family", "created_ms", "bar_ms")}
    # Minor①：依最後在場時間（last_seen_ms，無則 created_ms）清理
    for cl in [cl for cl, e in state.get("ledger", {}).items()
               if not e.get("live") and
               t - int(e.get("last_seen_ms") or e.get("created_ms") or t) > LEDGER_RETENTION_MS]:
        del state["ledger"][cl]
    _prune_intents(state, t, active_insts)

    return {"ok": True, "occupied": occupied, "active_insts": active_insts, "active_slots": active_slots,
            "family_pending": fam_pending, "algos": algos, "positions": positions,
            "family_positions": sorted(fam_pos), "ownership_unknown": ownership_unknown}


def _prune_intents(state: Dict[str, Any], t: int, active_insts: Set[str]) -> None:
    """保留：未結案（PENDING/UNKNOWN）、當日（台北）建立/結案、仍在場者；其餘超過保留期清除，並設數量上限。"""
    day0 = int(now_taipei().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    ints = state.get("intents", {})

    def ts(it: Dict[str, Any]) -> int:
        return int(max(int(it.get("resolved_ms") or 0), int(it.get("last_seen_ms") or 0),
                       int(it.get("created_ms") or 0)))

    def keep(cl: str, it: Dict[str, Any]) -> bool:
        if it.get("status") in UNRESOLVED_INTENT or it.get("protection_unverified"):
            return True
        if ts(it) >= day0:
            return True
        if it.get("instId") in active_insts and it.get("status") in LIVE_INTENT:
            return True
        return False

    removable = [cl for cl, it in ints.items() if not keep(cl, it)]
    expired = [cl for cl in removable if t - ts(ints[cl]) > INTENT_RETENTION_MS]
    for cl in expired:
        del ints[cl]
    rest = sorted([cl for cl in removable if cl in ints], key=lambda c: ts(ints[c]))
    while len(rest) > INTENT_MAX_RESOLVED:
        del ints[rest.pop(0)]


def cancel_expired_family_orders(client, family_pending: List[Dict[str, Any]], dry_run: bool,
                                 state: Dict[str, Any]) -> Dict[str, Any]:
    """撤銷所有 RETEST24 家族（不分 R1/R2）逾時掛單。回傳統計；絕不回傳可用於扣槽的數字。"""
    t = now_ms()
    stats = {"attempted": 0, "confirmed": 0, "failed": 0, "dry_run": 0, "items": []}
    for o in family_pending:
        c_time = int(o.get("cTime", "0") or "0")
        if not (c_time > 0 and (t - c_time) >= TTL_MS):
            continue
        inst, ord_id, cl = o["instId"], o.get("ordId", ""), o.get("clOrdId", "")
        if dry_run:
            log(f"[DRY-RUN] 家族掛單逾時 {TTL_HOURS}h，模擬撤單: {inst} {cl}")
            stats["dry_run"] += 1
            continue
        stats["attempted"] += 1
        res = client.private_req("POST", "/api/v5/trade/cancel-order", body_dict={"instId": inst, "ordId": ord_id})
        good = ok_item(res)
        stats["items"].append({"instId": inst, "clOrdId": cl, "ok": good,
                               "code": res.get("code"),
                               "sCode": (res.get("data") or [{}])[0].get("sCode") if res.get("data") else None})
        if good:
            stats["confirmed"] += 1
            log(f"🧹 逾時撤單成功 ({TTL_HOURS}h, {prefix_profile(cl)}): {inst} {cl}")
            e = state.get("ledger", {}).get(cl)
            if e is not None:
                e["cancel_ack_ms"] = t
                save_state(state)
        else:
            stats["failed"] += 1
            log(f"⚠️ 逾時撤單失敗（code/sCode 非 0）: {inst} {cl} -> {res}")
    return stats


def cancel_family_entries_on_daily_halt(client, family_pending: List[Dict[str, Any]], dry_run: bool,
                                        state: Dict[str, Any]) -> Dict[str, Any]:
    """
    CHECKLIST-D：日虧停機時撤回 RETEST24 全家族（R1/R2）未成交進場掛單。
    - 只處理 orders-pending 中 clOrdId 為家族前綴的一般委託；algo（TP/SL、外部條件單、移動止損）一律不碰。
    - 不平倉、不碰外部（非 RETEST24）委託。
    - 每筆檢查 code 與 sCode；失敗不假裝成功、不刪紀錄。
    - dry_run：只列擬撤清單，不送撤單。
    """
    t = now_ms()
    stats: Dict[str, Any] = {"dry_run": dry_run, "would_cancel": [], "attempted": 0, "confirmed": 0,
                             "failed": 0, "items": []}
    for o in family_pending:
        cl = str(o.get("clOrdId", ""))
        if not is_managed_clord(cl) or o.get("state", "live") not in ("live", "partially_filled"):
            continue
        inst, ord_id = o["instId"], o.get("ordId", "")
        if dry_run:
            stats["would_cancel"].append({"instId": inst, "clOrdId": cl, "ordId": ord_id})
            log(f"[DRY-RUN] 日虧停機擬撤家族進場掛單: {inst} {cl}")
            continue
        stats["attempted"] += 1
        res = client.private_req("POST", "/api/v5/trade/cancel-order", body_dict={"instId": inst, "ordId": ord_id})
        good = ok_item(res)
        s_code = (res.get("data") or [{}])[0].get("sCode") if res.get("data") else None
        item = {"instId": inst, "clOrdId": cl, "ok": good, "code": res.get("code"), "sCode": s_code,
                "accFillSz_before": o.get("accFillSz")}
        stats["items"].append(item)
        ents = [e for e in (state.get("ledger", {}).get(cl), state.get("intents", {}).get(cl)) if e is not None]
        if good:
            stats["confirmed"] += 1
            filled = float(o.get("accFillSz", "0") or "0")
            for e in ents:
                e["cancel_ack_ms"] = t
                e["cancel_reason"] = "DAILY_LOSS_HALT"
                if filled <= 0:
                    e["status"] = INTENT_CANCELED          # 完全未成交 → 結案
                # 已部分成交：保留原狀態，持倉仍受家族槽位 / TP/SL 檢核管理
            log(f"🧹 日虧停機撤單成功 ({prefix_profile(cl)}): {inst} {cl}")
        else:
            stats["failed"] += 1
            for e in ents:
                e["cancel_failed_ms"] = t
                e["cancel_failed_reason"] = f"DAILY_LOSS_HALT code={res.get('code')} sCode={s_code}"
            log(f"⚠️ 日虧停機撤單失敗（不視為成功、保留紀錄）: {inst} {cl} -> {res}")
        save_state(state)                                   # 每筆轉換立即持久化
    return stats


def _row_short(r: Dict[str, Any]) -> bool:
    side = str(r.get("posSide", ""))
    return side == "short" or (side == "net" and str(r.get("direction", "")) == "short")


def _f(v: Any) -> Optional[float]:
    try:
        if v in (None, ""):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _orders_history(client, inst: str, cache: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    if inst not in cache:
        cache[inst] = _paged_list(client, "/api/v5/trade/orders-history", {"instType": "SWAP", "instId": inst},
                                  "ordId")
    return cache[inst]


def _is_short_open(o: Dict[str, Any]) -> bool:
    ps = str(o.get("posSide", "net"))
    return str(o.get("side", "")) == "sell" and ps in ("short", "net", "")


def _fill_ts(o: Dict[str, Any]) -> int:
    for k in ("fillTime", "uTime", "cTime"):
        v = _f(o.get(k))
        if v:
            return int(v)
    return 0


def _row_size(rows: List[Dict[str, Any]]) -> Optional[float]:
    vals = [x for r in rows for x in (_f(r.get("openMaxPos")), _f(r.get("closeTotalPos"))) if x is not None]
    return max(vals) if vals else None


def _verify_position_ownership(client, cache: Dict[str, Any], entries: List[Dict[str, Any]],
                               inst: str, c_time: int, rows: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    """G-4：以 orders-history 交叉核對倉位是否「純本策略」。任何無法確認 → (False, 原因)。"""
    last_u = max(int(_f(r.get("uTime")) or 0) for r in rows)
    size = _row_size(rows)
    if size is None:
        return False, {"reason": "size_fields_missing(openMaxPos/closeTotalPos)"}
    if now_ms() - c_time > ORDERS_HISTORY_WINDOW_MS:
        return False, {"reason": "opened_before_orders_history_window"}
    ok, hist = _orders_history(client, inst, cache)
    if not ok:
        return False, {"reason": "orders_history_unavailable"}
    ours_cl = {str(e.get("clOrdId")) for e in entries if e.get("instId") == inst and
               int(e.get("created_ms", 0)) - 5000 <= c_time <= int(e.get("created_ms", 0)) + TTL_MS + 60_000}
    ours_ord = {str(e.get("ordId")) for e in entries if e.get("instId") == inst and e.get("ordId") and
                str(e.get("clOrdId")) in ours_cl}
    ours_sz = 0.0
    ext_sz = 0.0
    ext_ids: List[str] = []
    for o in hist:
        filled = _f(o.get("accFillSz")) or 0.0
        if filled <= 0 or not _is_short_open(o):
            continue
        cl = str(o.get("clOrdId") or "")
        if cl in ours_cl or str(o.get("ordId")) in ours_ord:
            ours_sz += filled
            continue
        ts = _fill_ts(o)
        if c_time - 5000 <= ts <= last_u:
            ext_sz += filled
            ext_ids.append(cl or str(o.get("ordId")))
    det = {"pos_size": size, "ours_filled": ours_sz, "foreign_open_filled": ext_sz, "foreign_ids": ext_ids[:10]}
    if ext_sz > 0:
        det["reason"] = "mixed_source_same_position"
        return False, det
    if size > ours_sz + 1e-9:
        det["reason"] = "position_size_exceeds_strategy_fills"
        return False, det
    return True, det


def _explained_as_external(client, cache: Dict[str, Any], r: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """state 遺失時：當日空單平倉須能由 orders-history 完整解釋為非本策略成交，否則未知。"""
    inst = str(r.get("instId"))
    c_time = int(_f(r.get("cTime")) or 0)
    u_time = int(_f(r.get("uTime")) or 0)
    size = _row_size([r])
    if size is None or c_time <= 0:
        return False, {"instId": inst, "reason": "size_or_ctime_missing"}
    if now_ms() - c_time > ORDERS_HISTORY_WINDOW_MS:
        return False, {"instId": inst, "reason": "opened_before_orders_history_window"}
    ok, hist = _orders_history(client, inst, cache)
    if not ok:
        return False, {"instId": inst, "reason": "orders_history_unavailable"}
    ext = 0.0
    for o in hist:
        filled = _f(o.get("accFillSz")) or 0.0
        if filled <= 0 or not _is_short_open(o):
            continue
        ts = _fill_ts(o)
        if not (c_time - 5000 <= ts <= u_time):
            continue
        cl = o.get("clOrdId")
        if is_managed_clord(cl) or is_similar_prefix_clord(cl):
            return False, {"instId": inst, "reason": "strategy_or_similar_prefix_fill", "clOrdId": cl}
        ext += filled
    if ext + 1e-9 < size:
        return False, {"instId": inst, "reason": "close_not_explained_by_orders_history",
                       "pos_size": size, "explained": ext}
    return True, {"instId": inst, "explained": ext}


def check_daily_realized_pnl(client, state: Dict[str, Any],
                             rec: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, Dict[str, Any]]:
    """
    v1.4：RETEST24 家族台北當日已實現損益（G-4 所有權 fail-closed ＋ C2 跨日部分平倉增量）。
    回傳 (pnl_ok, attributed_pnl, detail)。detail["halt_reason"] 於 pnl_ok=False 時給出。
    """
    t0 = now_taipei().replace(hour=0, minute=0, second=0, microsecond=0)
    begin_ms = int(t0.timestamp() * 1000)
    if rec is not None and rec.get("ownership_unknown"):
        return False, 0.0, {"halt_reason": "HALT_PNL_OWNERSHIP_UNKNOWN", "error": "ownership_unknown_in_reconcile",
                            "items": rec.get("ownership_unknown")}
    entries = [e for e in list(state.get("ledger", {}).values()) + list(state.get("intents", {}).values())
               if e.get("strategy_family") == STRATEGY_FAMILY]

    def attributable(r: Dict[str, Any]) -> bool:
        if not _row_short(r):
            return False
        c = int(_f(r.get("cTime")) or 0)
        if c <= 0:
            return False
        for e in entries:
            if e.get("instId") != r.get("instId"):
                continue
            created = int(e.get("created_ms", 0))
            if created - 5000 <= c <= created + TTL_MS + 60_000:
                return True
        return False

    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, ...]] = set()
    after: Optional[str] = None
    pages = 0
    complete = False
    while pages < PNL_MAX_PAGES:
        params: Dict[str, Any] = {"instType": "SWAP", "limit": "100"}
        if after:
            params["after"] = after
        res = client.private_req("GET", "/api/v5/account/positions-history", params)
        pages += 1
        if res.get("code") != "0":
            log(f"⚠️ positions-history 第 {pages} 頁失敗: {res.get('code')} {res.get('msg')}")
            return False, 0.0, {"pages": pages, "error": res.get("msg"), "halt_reason": "HALT_PNL_UNKNOWN"}
        data = res.get("data", []) or []
        for r in data:
            key = (str(r.get("instId")), str(r.get("posId", "")), str(r.get("cTime", "")),
                   str(r.get("uTime", "")), str(r.get("realizedPnl", "")))
            if key not in seen:
                seen.add(key)
                rows.append(r)
        if len(data) < 100:
            complete = True
            break
        oldest = min(int(_f(r.get("uTime")) or 0) for r in data)
        # C2：延伸分頁至「今日有紀錄之歸因倉位」最早 cTime，以取得 00:00 前基準列
        floor = begin_ms
        for r in rows:
            if int(_f(r.get("uTime")) or 0) >= begin_ms and attributable(r):
                floor = min(floor, int(_f(r.get("cTime")) or begin_ms))
        if oldest < floor:
            complete = True
            break
        after = str(oldest)
    if not complete:
        return False, 0.0, {"pages": pages, "error": "page_limit", "halt_reason": "HALT_PNL_UNKNOWN"}

    today_short = [r for r in rows if int(_f(r.get("uTime")) or 0) >= begin_ms and _row_short(r)]
    cache: Dict[str, Any] = {}
    detail: Dict[str, Any] = {"pages": pages, "rows": len(rows), "begin_ms": begin_ms}

    # G-4 S2：本機 state 無任何家族紀錄，但當日有空單平倉 → 必須能完整解釋為外部，否則未知
    if not entries:
        checks = []
        for r in today_short:
            ok_x, dx = _explained_as_external(client, cache, r)
            checks.append(dx)
            if not ok_x:
                log(f"⛔ HALT_PNL_OWNERSHIP_UNKNOWN：本機 state 無家族紀錄，當日空單平倉無法確認非本策略 {dx}")
                return False, 0.0, {**detail, "halt_reason": "HALT_PNL_OWNERSHIP_UNKNOWN",
                                    "error": "state_lost_unverifiable", "check": dx}
        return True, 0.0, {**detail, "matched": 0, "state_empty_confirmed_external": checks}

    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    excluded = 0
    for r in rows:
        if attributable(r):
            groups.setdefault((str(r.get("instId")), str(r.get("posId", "")), str(r.get("cTime", ""))), []).append(r)
        elif int(_f(r.get("uTime")) or 0) >= begin_ms:
            excluded += 1
            # G-4：本策略委託成交併入「非本策略開倉」之倉位（同 posId 先有外部倉） → 無法拆分 → 未知
            if _row_short(r):
                c = int(_f(r.get("cTime")) or 0)
                u = int(_f(r.get("uTime")) or 0)
                for e in entries:
                    if e.get("instId") != r.get("instId"):
                        continue
                    st = e.get("status")
                    filled_ev = (_f(e.get("accFillSz")) or 0) > 0 or st in (INTENT_ACKED, INTENT_CONFIRMED,
                                                                            INTENT_PENDING, INTENT_UNKNOWN)
                    if st == INTENT_CANCELED and (_f(e.get("accFillSz")) or 0) <= 0:
                        filled_ev = False
                    if filled_ev and c > 0 and c + 5000 < int(e.get("created_ms", 0)) <= u:
                        log(f"⛔ HALT_PNL_OWNERSHIP_UNKNOWN：{r.get('instId')} 本策略委託可能併入既有外部倉位 posId={r.get('posId')}")
                        return False, 0.0, {**detail, "halt_reason": "HALT_PNL_OWNERSHIP_UNKNOWN",
                                            "error": "strategy_fill_into_foreign_position",
                                            "posId": r.get("posId"), "instId": r.get("instId")}

    marks = state.setdefault("pnl_marks", {})
    total = 0.0
    matched = 0
    per_pos = []
    t = now_ms()
    for (inst, pos_id, c_str), g in groups.items():
        g.sort(key=lambda r: int(_f(r.get("uTime")) or 0))
        today = [r for r in g if int(_f(r.get("uTime")) or 0) >= begin_ms]
        if not today:
            continue
        ok_o, dv = _verify_position_ownership(client, cache, entries, inst, int(c_str or 0), g)
        if not ok_o:
            log(f"⛔ HALT_PNL_OWNERSHIP_UNKNOWN：{inst} posId={pos_id} {dv}；不把合併倉位 realizedPnl 計入本策略。")
            return False, 0.0, {**detail, "halt_reason": "HALT_PNL_OWNERSHIP_UNKNOWN",
                                "error": dv.get("reason"), "instId": inst, "posId": pos_id, "verify": dv}
        before = [r for r in g if int(_f(r.get("uTime")) or 0) < begin_ms]
        mk = f"{inst}|{pos_id}|{c_str}"
        base_src = "none"
        base = 0.0
        if before:
            base = _f(before[-1].get("realizedPnl")) or 0.0
            base_src = "history_before_00"
        elif mk in marks and int(marks[mk].get("uTime", 0)) < begin_ms:
            base = float(marks[mk].get("realizedPnl", 0.0))
            base_src = "state_pnl_marks"
        last = _f(today[-1].get("realizedPnl")) or 0.0
        inc = last - base
        total += inc
        matched += 1
        per_pos.append({"instId": inst, "posId": pos_id, "cum_today_last": last, "baseline": base,
                        "baseline_src": base_src, "increment": inc, "verify": dv})
        marks[mk] = {"realizedPnl": last, "uTime": int(_f(today[-1].get("uTime")) or 0), "seen_ms": t}
    for k in [k for k, v in marks.items() if t - int(v.get("seen_ms", t)) > 7 * DAY_MS]:
        del marks[k]
    return True, total, {**detail, "matched": matched, "excluded": excluded, "positions": per_pos}


def detect_pos_mode(client) -> Optional[str]:
    res = client.private_req("GET", "/api/v5/account/config")
    if res.get("code") == "0" and res.get("data"):
        return res["data"][0].get("posMode", "long_short_mode")
    return None


# =====================================================================
# 6. 意圖對帳（啟動時）
# =====================================================================
def _px_set(v: Any) -> bool:
    try:
        return v not in (None, "") and float(v) > 0
    except (TypeError, ValueError):
        return False


def _is_family_protection_algo(a: Dict[str, Any]) -> bool:
    ot = a.get("ordType") or a.get("_queried_ordType")
    return ot in PROTECTION_ALGO_TYPES and (is_managed_clord(a.get("algoClOrdId")) or
                                            is_managed_clord(a.get("attachAlgoClOrdId")))


def _protection_status(inst: str, pos_sz: float, algos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """雙邊 TP/SL 齊全且數量覆蓋持倉才算 complete。sz 空白/0 或 closeFraction=="1" 視為全倉。"""
    tp_cover = sl_cover = 0.0
    tp_full = sl_full = False
    ids = []
    for a in algos:
        if a.get("instId") != inst or not _is_family_protection_algo(a):
            continue
        ids.append(a.get("algoClOrdId") or a.get("attachAlgoClOrdId"))
        full = str(a.get("closeFraction", "")) == "1"
        try:
            sz = float(a.get("sz") or 0)
        except (TypeError, ValueError):
            sz = 0.0
        if sz <= 0:
            full = True
        if _px_set(a.get("tpTriggerPx")):
            tp_full = tp_full or full
            tp_cover += sz
        if _px_set(a.get("slTriggerPx")):
            sl_full = sl_full or full
            sl_cover += sz
    eps = 1e-9
    tp_ok = tp_full or tp_cover + eps >= pos_sz
    sl_ok = sl_full or sl_cover + eps >= pos_sz
    has_tp = tp_full or tp_cover > 0
    has_sl = sl_full or sl_cover > 0
    return {"complete": bool(has_tp and has_sl and tp_ok and sl_ok), "has_tp": has_tp, "has_sl": has_sl,
            "tp_covers_pos": tp_ok, "sl_covers_pos": sl_ok, "pos_sz": pos_sz, "protection_algos": ids}


def check_family_protection(state: Dict[str, Any], rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    EXTRA-02：對所有 RETEST24 持倉回查交易所 TP/SL（資料取自本輪 reconcile_account 的分頁 algo 清單）。
    只讀、只標記；絕不補單、撤單或平倉。回傳 {halt, verified, unverified, closed}。
    """
    out: Dict[str, Any] = {"halt": False, "verified": [], "unverified": [], "closed": []}
    fam_pos = set(rec.get("family_positions") or [])
    # pos_sz：只累加「空方」倉位張數（posSide=short，或單向持倉模式 posSide=net 且 pos<0）。
    # 本策略只做空，附掛 TP/SL 只保護空倉；同幣外部多倉不屬本策略、也不由本策略 TP/SL 保護，故不計入。
    # 若某家族幣種的空方張數為 0（理論上不會發生），_protection_status 以 pos_sz=0 計算時仍要求 tp 與 sl 皆存在。
    pos_sz: Dict[str, float] = {}
    for p in rec.get("positions") or []:
        if p.get("instId") not in fam_pos:
            continue
        side = str(p.get("posSide", ""))
        v = float(p.get("pos", "0") or "0")
        if side == "short" or (side == "net" and v < 0):
            pos_sz[p["instId"]] = pos_sz.get(p["instId"], 0.0) + abs(v)
    tracked = [e for e in list(state.get("ledger", {}).values()) + list(state.get("intents", {}).values())
               if e.get("strategy_family") == STRATEGY_FAMILY]
    t = now_ms()
    for inst in sorted(fam_pos):
        st = _protection_status(inst, pos_sz.get(inst, 0.0), rec.get("algos") or [])
        ents = [e for e in tracked if e.get("instId") == inst]
        if st["complete"]:
            for e in ents:
                e.pop("protection_unverified", None)
                e["protection_verified_ms"] = t
            out["verified"].append({"instId": inst, **st})
        else:
            for e in ents:
                e["protection_unverified"] = True
                e["protection_detail"] = st
            out["unverified"].append({"instId": inst, **st})
            out["halt"] = True
            log(f"🚨 {inst} RETEST24 持倉 TP/SL 保護未齊全 {st}；停開新倉，請人工檢查（不補單/不撤單/不平倉）。")
    for e in tracked:
        if e.get("protection_unverified") and e.get("instId") not in fam_pos:
            e.pop("protection_unverified", None)
            e["position_closed_seen_ms"] = t
            out["closed"].append(e.get("clOrdId"))
    return out


def _promote(state: Dict[str, Any], it: Dict[str, Any], order: Dict[str, Any], status: str) -> None:
    cl = it["clOrdId"]
    it["status"] = status
    it["ordId"] = order.get("ordId", it.get("ordId", ""))
    it["resolved_ms"] = now_ms()
    entry = dict(it)
    entry["exchange_state"] = order.get("state")
    entry["accFillSz"] = order.get("accFillSz")
    state.setdefault("ledger", {})[cl] = entry
    state.setdefault("placed_bars", {})[f"{it['bar_ms']}:{it['instId']}"] = cl


def reconcile_intents(client, state: Dict[str, Any]) -> Dict[str, Any]:
    """每輪啟動先處理所有 PENDING_SUBMIT / UNKNOWN_SUBMIT 意圖。任何未知 → halt=True。"""
    out = {"halt": False, "resolved": [], "unknown": []}
    for cl, it in list(state.get("intents", {}).items()):
        if it.get("status") not in UNRESOLVED_INTENT:
            continue      # 保護單檢核統一由 check_family_protection() 處理（含 ACKED / CONFIRMED）
        inst = it["instId"]
        r = client.private_req("GET", "/api/v5/trade/order", {"instId": inst, "clOrdId": cl})
        code = str(r.get("code"))
        data = r.get("data") or []
        o = data[0] if (code == "0" and data) else None
        if o is not None and str(o.get("clOrdId") or cl) != cl:
            o = None                                   # 回傳非同一 clOrdId → 不採信
        if o is not None:
            st = o.get("state")
            try:
                filled = float(o.get("accFillSz", "0") or "0")
            except (TypeError, ValueError):
                filled = None
            if filled is None:
                it["status"] = INTENT_UNKNOWN
                out["unknown"].append(cl)
                out["halt"] = True
            elif st in ("live", "partially_filled", "filled") or (st in ("canceled", "mmp_canceled") and filled > 0):
                _promote(state, it, o, INTENT_CONFIRMED)
                out["resolved"].append({"clOrdId": cl, "result": INTENT_CONFIRMED, "state": st})
            elif st in ("canceled", "mmp_canceled") and filled == 0:
                it["status"] = INTENT_CANCELED          # 已證明未受理(b)：同 clOrdId 終態撤銷且 0 成交
                it["resolved_ms"] = now_ms()
                it["resolve_evidence"] = {"state": st, "accFillSz": o.get("accFillSz"), "ordId": o.get("ordId")}
                out["resolved"].append({"clOrdId": cl, "result": INTENT_CANCELED})
            else:
                it["status"] = INTENT_UNKNOWN
                out["unknown"].append(cl)
                out["halt"] = True
        else:
            # v1.5：51603（不論經過多久）、逾時、5xx、限流 → 可能已受理但暫不可見 → 維持未知、鎖槽、停開
            it["status"] = INTENT_UNKNOWN
            it["last_query_error"] = f"{code} {r.get('msg')}"
            it["last_query_ms"] = now_ms()
            out["unknown"].append(cl)
            out["halt"] = True
            log(f"⛔ 意圖 {cl} 狀態未知（{code} {r.get('msg')}）；本輪停開新倉，不重送、不撤單、不平倉。")
        save_state(state)   # 每筆狀態轉換立即持久化
    return out


# =====================================================================
# 7. 訊號掃描
# =====================================================================
def fetch_4h_history(client, inst: str, n_closed: int = INDICATOR_BARS) -> Optional[List[List[Any]]]:
    r = client.public_get("/api/v5/market/candles", {"instId": inst, "bar": "4H", "limit": "300"})
    if r.get("code") != "0" or not r.get("data"):
        return None
    bars = {int(x[0]): x for x in r["data"]}
    while len(bars) < n_closed + 1:
        oldest = min(bars)
        h = client.public_get("/api/v5/market/history-candles",
                              {"instId": inst, "bar": "4H", "after": str(oldest), "limit": "100"})
        if h.get("code") != "0":
            return None      # 歷史不完整 → 指標可能偏離，略過此標的
        d = h.get("data") or []
        if not d:
            break            # 已到上市起點
        for x in d:
            bars[int(x[0])] = x
        if len(d) < 100:
            break
    return [bars[k] for k in sorted(bars)]


def scan_candidates(client, universe: List[Dict[str, Any]], occupied: Set[str]) -> Tuple[int, List[Dict[str, Any]]]:
    candidates: List[Dict[str, Any]] = []
    latest_bar_ms = 0
    for idx, info in enumerate(universe, 1):
        inst = info["instId"]
        if inst in occupied:
            continue
        raw4 = fetch_4h_history(client, inst)
        if not raw4 or len(raw4) < 3:
            continue
        if str(raw4[-1][8]) != "0":
            continue
        cur_bar, closed_bars = raw4[-1], raw4[:-1]
        bt = int(cur_bar[0])
        latest_bar_ms = max(latest_bar_ms, bt)
        r1d = client.public_get("/api/v5/market/candles", {"instId": inst, "bar": "1D", "limit": "65"})
        if r1d.get("code") != "0":
            continue
        d1_ts = {int(x[0]) for x in r1d.get("data", [])}
        sig = evaluate_signal(closed_bars, cur_bar, info["tickSz"], d1_ts)
        if sig is None:
            continue
        sig.update({"instId": inst, "spec": info, "ema60": sig["ema"]})
        candidates.append(sig)
        if idx % 15 == 0:
            time.sleep(0.25)
    candidates.sort(key=lambda x: x["sort_key"])
    return latest_bar_ms, candidates


# =====================================================================
# 8. 張數與下單
# =====================================================================
def compute_order_plan(cand: Dict[str, Any], risk_u: float) -> Optional[Dict[str, Any]]:
    spec = cand["spec"]
    entry_px = cand["entry_px"]
    loss_rate = SL_PCT + MAKER_FEE + TAKER_FEE + SLIP_MKT
    per_contract_loss = spec["ctVal"] * entry_px * loss_rate
    if per_contract_loss <= 0:
        return None
    sz_str = floor_step(risk_u / per_contract_loss, spec["lotSz"])
    sz = float(sz_str)
    if sz < spec["minSz"] or sz <= 0:
        return None
    return {"sz_str": sz_str, "sz": sz, "notional_u": sz * spec["ctVal"] * entry_px,
            "est_sl_loss_u": sz * per_contract_loss,
            "sl_px_str": floor_step(entry_px * (1.0 + SL_PCT), spec["tickSz"]),
            "tp_px_str": floor_step(entry_px * (1.0 - TP_PCT), spec["tickSz"])}


def is_sync_explicit_reject(res: Any) -> bool:
    """已證明未受理(a)：code ∈ {0,1,2} 且 data[0].sCode 非空非 "0" 且 data[0] 無 ordId。
    僅頂層錯誤碼（無 sCode／空 data）、或帶 ordId、或逾時斷線 → 一律不是明確拒單（維持 UNKNOWN_SUBMIT）。"""
    if not isinstance(res, dict) or str(res.get("code")) not in ("0", "1", "2"):
        return False
    data = res.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return False
    s_code = str(data[0].get("sCode") if data[0].get("sCode") is not None else "").strip()
    if s_code in ("", "0"):
        return False
    if str(data[0].get("ordId") or "").strip():
        return False
    return True


def estimate_initial_margin(notional_u: float, lever: float) -> float:
    """E2：初始保證金 = notional/lever + 進出場手續費緩衝，再乘 MARGIN_BUFFER。"""
    return (notional_u / max(float(lever), 1.0) + notional_u * (MAKER_FEE + TAKER_FEE)) * MARGIN_BUFFER


def fetch_avail_usdt(client) -> Optional[float]:
    """E2：GET /api/v5/account/balance?ccy=USDT → details[USDT].availEq（缺則 availBal）；失敗/缺值 → None。"""
    res = client.private_req("GET", "/api/v5/account/balance", {"ccy": "USDT"})
    if not isinstance(res, dict) or res.get("code") != "0" or not res.get("data"):
        return None
    for d in (res["data"][0].get("details") or []):
        if str(d.get("ccy")) == "USDT":
            v = _f(d.get("availEq"))
            if v is None:
                v = _f(d.get("availBal"))
            return v
    return None


def ensure_leverage(client, inst: str, pos_mode: Optional[str], occupied: Set[str]) -> bool:
    """Minor③：已占用幣種絕不碰；--skip-set-leverage 不查不設；現值已 10x 不 POST；查詢失敗 → 跳過該筆。"""
    if inst in occupied:
        return False
    if SKIP_SET_LEVERAGE:
        return True
    li = client.private_req("GET", "/api/v5/account/leverage-info", {"instId": inst, "mgnMode": "cross"})
    if li.get("code") != "0" or not li.get("data"):
        log(f"  ⚠️ 查詢槓桿失敗，跳過 {inst}: {li.get('code')} {li.get('msg')}")
        return False
    rows = li["data"]
    if pos_mode == "long_short_mode":
        rows = [r for r in rows if str(r.get("posSide", "short")) in ("short", "")] or rows
    if rows and all(abs((_f(r.get("lever")) or 0) - LEVERAGE) < 1e-9 for r in rows):
        log(f"  ℹ️ {inst} 槓桿已為 {LEVERAGE}x，略過 set-leverage")
        return True
    lev_body: Dict[str, Any] = {"instId": inst, "lever": str(LEVERAGE), "mgnMode": "cross"}
    if pos_mode == "long_short_mode":
        lev_body["posSide"] = "short"
    lev_res = client.private_req("POST", "/api/v5/account/set-leverage", body_dict=lev_body)
    if lev_res.get("code") != "0":
        log(f"  ⚠️ 設定槓桿失敗，跳過 {inst}: {lev_res}")
        return False
    return True


def next_clord_id(state: Dict[str, Any], prefix: str, bar_ms: int) -> str:
    key = f"{prefix}:{bar_ms}"
    seq = int(state.setdefault("clord_seq", {}).get(key, 0)) + 1
    state["clord_seq"][key] = seq
    dt = datetime.datetime.fromtimestamp(bar_ms / 1000, tz=TZ_TAIPEI)
    return f"{prefix}{dt.strftime('%y%m%d%H')}{seq:02d}"


def _record_profile_switch(state: Dict[str, Any], profile_key: str) -> None:
    prev = state.get("active_profile")
    if prev != profile_key:
        state.setdefault("profile_history", []).append({"ts_ms": now_ms(), "from": prev, "to": profile_key})
        state["active_profile"] = profile_key
        log(f"🔁 profile 切換紀錄: {prev} -> {profile_key}（另一 profile 遺留部位仍計入家族槽位並受逾時管理）")


def resolve_unknown_intent(client, cl_ord_id: str, reason: str, operator: str = "manual") -> Dict[str, Any]:
    """
    人工核對交易所（委託、成交、持倉）後顯式解除單一未決意圖；寫入 state.intent_audit 審計紀錄。
    安全規則：只處理 PENDING_SUBMIT / UNKNOWN_SUBMIT；原因必填；持單例鎖；
    先查單：若交易所顯示同 clOrdId 委託存在或有成交 → 拒絕解除並轉 CONFIRMED（交由正常流程管理）。
    """
    reason = (reason or "").strip()
    if not reason:
        return {"ok": False, "error": "resolve_reason_required"}
    with SingleInstanceLock(LOCK_FILE):
        state = load_state()
        it = state.get("intents", {}).get(cl_ord_id)
        if it is None:
            return {"ok": False, "error": "intent_not_found"}
        if it.get("status") not in UNRESOLVED_INTENT:
            return {"ok": False, "error": f"intent_not_unresolved:{it.get('status')}"}
        q = {"code": None}
        if client is not None and getattr(client, "has_auth", False):
            q = client.private_req("GET", "/api/v5/trade/order", {"instId": it["instId"], "clOrdId": cl_ord_id})
            data = q.get("data") or []
            if str(q.get("code")) == "0" and data and str(data[0].get("clOrdId") or cl_ord_id) == cl_ord_id:
                o = data[0]
                filled = float(o.get("accFillSz", "0") or "0")
                if o.get("state") in ("live", "partially_filled", "filled") or filled > 0:
                    _promote(state, it, o, INTENT_CONFIRMED)
                    save_state(state)
                    log(f"⛔ 人工解除被拒：{cl_ord_id} 在交易所存在（{o.get('state')} accFillSz={filled}），已轉 CONFIRMED。")
                    return {"ok": False, "error": "order_exists_on_exchange", "promoted": INTENT_CONFIRMED}
        prev = it.get("status")
        t = now_ms()
        it["status"] = INTENT_MANUAL
        it["resolved_ms"] = t
        it["manual_resolve"] = {"reason": reason, "operator": operator, "ts_ms": t}
        rec = {"ts_ms": t, "ts_taipei": datetime.datetime.fromtimestamp(t / 1000, tz=TZ_TAIPEI).strftime("%Y-%m-%d %H:%M:%S UTC+8"),
               "clOrdId": cl_ord_id, "instId": it.get("instId"), "from_status": prev, "to_status": INTENT_MANUAL,
               "reason": reason, "operator": operator, "exchange_query_code": q.get("code"),
               "script_version": SCRIPT_VERSION}
        state.setdefault("intent_audit", []).append(rec)
        save_state(state)
        log(f"📝 人工解除未決意圖 {cl_ord_id}: {prev} -> {INTENT_MANUAL}；原因：{reason}")
        return {"ok": True, "audit": rec}


def run_cycle(client, profile_key: str, dry_run: bool) -> Dict[str, Any]:
    """整輪以單例鎖包覆；回傳結果 dict（供測試與日誌）。--dry-run 全程不寫共用狀態檔。"""
    global _STATE_READ_ONLY
    prev_ro = _STATE_READ_ONLY
    _STATE_READ_ONLY = bool(dry_run)
    try:
        with SingleInstanceLock(LOCK_FILE):
            return _run_cycle_locked(client, profile_key, dry_run)
    except LockContention as e:
        log(f"⛔ 鎖競爭：{e}；本程序中止，不開單。")
        return {"status": "LOCK_CONTENTION", "placed": 0}
    finally:
        _STATE_READ_ONLY = prev_ro


def _run_cycle_locked(client, profile_key: str, dry_run: bool) -> Dict[str, Any]:
    prof = PROFILES[profile_key]
    risk_u, daily_limit, prefix = prof["risk_per_trade"], prof["daily_loss_limit"], prof["clord_prefix"]
    max_slots = min(prof["max_slots"], FAMILY_MAX_SLOTS)
    result: Dict[str, Any] = {"status": "OK", "profile": profile_key, "placed": 0, "placed_clords": []}
    log(f"=== {SCRIPT_VERSION} 開始 | 模式={profile_key} | 風險={risk_u}U | 日虧限={daily_limit}U | "
        f"家族上限={max_slots}槽 | DRY_RUN={dry_run} | 訊號口徑={SIGNAL_SPEC} ===")

    state = load_state()
    _record_profile_switch(state, profile_key)
    save_state(state)

    occupied: Set[str] = set()
    active_slots = 0
    pos_mode: Optional[str] = "long_short_mode"

    if client.has_auth:
        # (a) 先對帳所有未決意圖
        ir = reconcile_intents(client, state)
        result["intent_reconcile"] = ir
        # (b) 全帳對帳 → 逾時撤單 → 再次對帳重算槽位
        rec = reconcile_account(client, state)
        if not rec["ok"]:
            save_state(state)
            result["status"] = "HALT_RECONCILE_FAILED"
            return result
        cstats = cancel_expired_family_orders(client, rec["family_pending"], dry_run, state)
        result["cancel"] = cstats
        rec2 = reconcile_account(client, state)
        save_state(state)
        if not rec2["ok"]:
            result["status"] = "HALT_POST_CANCEL_RECONCILE_FAILED"
            return result
        occupied, active_slots = rec2["occupied"], rec2["active_slots"]
        result["active_slots_after_reconcile"] = active_slots
        prot = check_family_protection(state, rec2)
        save_state(state)
        result["protection"] = prot
        result["ownership_unknown"] = rec2.get("ownership_unknown") or []
        halts: List[str] = []
        if prot["halt"]:
            halts.append("HALT_PROTECTION_UNVERIFIED")
        if result["ownership_unknown"]:
            halts.append("HALT_OWNERSHIP_UNKNOWN")
        if ir["halt"]:
            log("⛔ 存在狀態未知之意圖，本輪停開新倉。")
            halts.append("HALT_UNKNOWN_INTENT")
        # v1.4：保護單異常 / 所有權未知 / 意圖未知不再提前 return；同輪仍計算日虧（必要時撤回家族進場單）
        pnl_ok, daily_pnl, pdet = check_daily_realized_pnl(client, state, rec2)
        save_state(state)
        result["daily_pnl"] = {"ok": pnl_ok, "pnl": daily_pnl, **pdet}
        if not pnl_ok:
            log(f"⛔ 今日已實現損益未知（{pdet.get('halt_reason')}），保守停開新倉。")
            halts.append(pdet.get("halt_reason") or "HALT_PNL_UNKNOWN")
        else:
            log(f"帳戶現況：全帳占用 {len(occupied)} 檔 | RETEST24 家族槽位 {active_slots}/{max_slots} | "
                f"家族今日已實現 {daily_pnl:+.2f} U")
        if pnl_ok and daily_pnl <= -daily_limit:
            log(f"🛑 家族今日虧損達上限 ({daily_pnl:.2f} <= -{daily_limit:.2f})，今日停開新倉並撤回家族未成交進場掛單。")
            hstats = cancel_family_entries_on_daily_halt(client, rec2["family_pending"], dry_run, state)
            result["daily_halt_cancel"] = hstats
            if hstats["attempted"] > 0:
                rec3 = reconcile_account(client, state)       # 撤單後重新對帳（部分成交 / 撤單失敗留存正確狀態）
                result["post_halt_reconcile_ok"] = bool(rec3.get("ok"))
                if rec3.get("ok"):
                    result["active_slots_after_halt_cancel"] = rec3["active_slots"]
            save_state(state)
            halts.insert(0, "HALT_DAILY_LOSS")
        if halts:
            result["halt_reasons"] = halts
            result["status"] = halts[0]
            save_state(state)
            return result
        pos_mode = detect_pos_mode(client)
        if pos_mode is None:
            result["status"] = "HALT_POS_MODE_UNKNOWN"
            return result
    else:
        if not dry_run:
            log("⛔ 未找到有效 config.json 憑證，無法執行實盤模式。")
            result["status"] = "HALT_NO_AUTH"
            return result
        log("ℹ️ 未載入 config.json，以公開資料乾跑（未扣除帳戶既有占用）。")

    if active_slots >= max_slots:
        log(f"ℹ️ 家族槽位已滿 ({active_slots}/{max_slots})，本輪不開新單。")
        result["status"] = "SLOTS_FULL"
        return result

    universe = fetch_universe(client)
    universe, isolated = stablecoin_guard(client, universe)
    if isolated:
        result["stablecoin_isolated"] = isolated
        result["alerts"] = result.get("alerts", []) + ["HALT_STABLECOIN_ANOMALY"]
    bar_ms, cands = scan_candidates(client, universe, occupied)
    result["candidates"] = len(cands)
    if not cands:
        state["last_bar_ms"] = max(state.get("last_bar_ms", 0), bar_ms)
        save_state(state)
        return result

    avail_u: Optional[float] = None
    if client.has_auth:
        avail_u = fetch_avail_usdt(client)
        if avail_u is None:
            log("⛔ HALT_BALANCE_UNKNOWN：無法取得 USDT 可用保證金，停開新倉。")
            result["status"] = "HALT_BALANCE_UNKNOWN"
            save_state(state)
            return result
        result["avail_usdt"] = avail_u
    reserved_u = 0.0
    result["margin_skipped"] = []
    free_slots = max_slots - active_slots
    for c in cands:
        if result["placed"] >= free_slots:
            break
        inst = c["instId"]
        if inst in occupied:
            continue
        dedup_key = f"{c['bar_ms']}:{inst}"
        if dedup_key in state.get("placed_bars", {}):
            continue
        plan = compute_order_plan(c, risk_u)
        if not plan:
            continue
        need_u = estimate_initial_margin(plan["notional_u"], LEVERAGE)
        if avail_u is not None and need_u > avail_u - reserved_u:
            log(f"  ⚠️ 可用保證金不足，跳過 {inst}：需 {need_u:.2f}U，可用 {avail_u - reserved_u:.2f}U（已預留 {reserved_u:.2f}U）")
            result["margin_skipped"].append({"instId": inst, "need_u": round(need_u, 4),
                                             "free_u": round(avail_u - reserved_u, 4)})
            continue
        summary = (f"{inst} SHORT post_only @ {c['entry_px_str']} | SL {plan['sl_px_str']} | TP {plan['tp_px_str']} "
                   f"| sz={plan['sz_str']} | 預估停損={plan['est_sl_loss_u']:.1f}U | RSI={c['rsi14']:.1f}")
        if dry_run:
            log(f"  [DRY-RUN 候選] {summary}")
            result["placed"] += 1
            reserved_u += need_u
            continue

        if not ensure_leverage(client, inst, pos_mode, occupied):
            continue

        cl_id = next_clord_id(state, prefix, c["bar_ms"])
        intent = {"clOrdId": cl_id, "instId": inst, "profile": profile_key, "owner_prefix": prefix,
                  "strategy_family": STRATEGY_FAMILY, "bar_ms": c["bar_ms"], "sz": plan["sz_str"],
                  "px": c["entry_px_str"], "sl_px": plan["sl_px_str"], "tp_px": plan["tp_px_str"],
                  "created_ms": now_ms(), "status": INTENT_PENDING, "script_version": SCRIPT_VERSION}
        state.setdefault("intents", {})[cl_id] = intent
        state.setdefault("placed_bars", {})[dedup_key] = cl_id
        save_state(state)                                  # ← write-ahead：送單前耐久落盤

        payload: Dict[str, Any] = {
            "instId": inst, "tdMode": "cross", "side": "sell", "ordType": "post_only",
            "px": c["entry_px_str"], "sz": plan["sz_str"], "clOrdId": cl_id,
            "attachAlgoOrds": [{"attachAlgoClOrdId": f"{cl_id}TS",
                                "tpTriggerPx": plan["tp_px_str"], "tpOrdPx": "-1", "tpTriggerPxType": "last",
                                "slTriggerPx": plan["sl_px_str"], "slOrdPx": "-1", "slTriggerPxType": "last"}],
        }
        if pos_mode == "long_short_mode":
            payload["posSide"] = "short"
        ord_res = client.private_req("POST", "/api/v5/trade/order", body_dict=payload)
        if ok_item(ord_res):
            intent["status"] = INTENT_ACKED
            intent["ordId"] = ord_res["data"][0].get("ordId", "")
            state.setdefault("ledger", {})[cl_id] = dict(intent)
            state.setdefault("managed_insts", {})[inst] = {k: intent.get(k) for k in
                                                          ("clOrdId", "ordId", "profile", "owner_prefix",
                                                           "strategy_family", "created_ms", "bar_ms")}
            occupied.add(inst)
            save_state(state)
            reserved_u += need_u
            result["placed"] += 1
            result["placed_clords"].append(cl_id)
            log(f"  ✅ 已受理 [{cl_id}] {summary}")
        elif is_sync_explicit_reject(ord_res):
            intent["status"] = INTENT_REJECTED
            intent["reject"] = {"code": ord_res.get("code"), "sCode": ord_res["data"][0].get("sCode"),
                                "sMsg": ord_res["data"][0].get("sMsg")}
            save_state(state)
            log(f"  ❌ 交易所明確拒單 {inst}: {intent['reject']}")
        else:
            intent["status"] = INTENT_UNKNOWN
            intent["last_submit_error"] = f"{ord_res.get('code')} {ord_res.get('msg')}"
            reserved_u += need_u
            occupied.add(inst)
            save_state(state)
            log(f"  ⛔ 送單結果未知 {inst} ({intent['last_submit_error']})；停止本輪後續送單，下輪先對帳。")
            result["status"] = "HALT_SUBMIT_UNKNOWN"
            break

    state["last_bar_ms"] = max(state.get("last_bar_ms", 0), bar_ms)
    save_state(state)
    log(f"=== 本輪結束（處理 {result['placed']} 筆）===")
    return result


def seconds_until_next_4h_close() -> float:
    now = now_taipei()
    next_hour = ((now.hour // 4) + 1) * 4
    if next_hour >= 24:
        target = (now + datetime.timedelta(days=1)).replace(hour=0, minute=1, second=30, microsecond=0)
    else:
        target = now.replace(hour=next_hour, minute=1, second=30, microsecond=0)
    return max(5.0, (target - now).total_seconds())


def main() -> None:
    raise SystemExit(
        "OFFLINE RESEARCH REFERENCE ONLY: live/demo execution is disabled in this public repository copy."
    )


if __name__ == "__main__":
    main()
