"""[PUBLIC OFFLINE REFERENCE COPY] 4H Fib v3 baseline strategy specification & indicator logic.
Sanitized for public offline research collaboration: live/demo execution is hard-disabled in main().
"""
"""OKX 主帳戶或子帳戶，4H Fib v3 多單。啟動：python FIB_4H_Long_v3.py --live
直接執行即為實盤；--check 為唯讀；--confirm 可加回 LIVE 二次確認。
同目錄 config.json：API_KEY、SECRET_KEY、PASSPHRASE。使用全倉，支援淨持倉與雙向持倉。
保留本程式的 sqlite 狀態檔；同一帳戶只運行一份。BTC、ETH、XAU 由使用者自行管理；其他合約勿混用策略。
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import queue
import sys
import sqlite3
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
from statistics import mean
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent
HOST = 'https://www.okx.com'
H4 = 14_400_000
DAY = 86_400_000
PREFIX = 'F4V3'
ZERO = D(0)

# 風控（v3）。原版是固定 5000U 名義 → 每筆風險固定 300U，且完全沒有總量上限。
# 這裡改成「固定風險金額」並加上總量天花板。全部可用環境變數覆蓋。
def _num(name, default):
    """環境變數轉 Decimal，錯誤時給出可讀訊息而不是 InvalidOperation。"""
    raw = os.getenv(name, default)
    try:
        return D(str(raw).strip())
    except Exception:
        raise SystemExit(f'環境變數 {name}={raw!r} 不是有效數字') from None


RISK_PER_TRADE = _num('RISK_PER_TRADE_USDT', '150')      # 每筆最大虧損 U
MAX_TOTAL_RISK = _num('MAX_TOTAL_RISK_USDT', '3600')     # 全部未平倉風險上限 U (= 24 × 150)
DAILY_LOSS_LIMIT = _num('DAILY_LOSS_LIMIT_USDT', '600')  # 單日已實現虧損上限 (= 4 × 每筆)
# 日限說明：24 槽回測顯示 600U 五年僅觸發 0 次（多單），放寬到 900/1200/無上限
# 結果完全相同，收緊到 300U 只差 -0.5%（樣本內外方向不一致，屬雜訊）。
# 故維持 600U：它不影響正常獲利，只在交易所異常或邏輯失控時當最後一道煞車。
# 未成交掛單存活時數。到期自動撤單，釋放名額。
# capped 回測（12 槽，含連虧暫停與日限）：TTL 24h +40,219U｜48h +49,444U。
# 深度 0.94 的回撤單需要更久才被觸及，48h 才涵蓋足夠成交機會。
try:
    ORDER_TTL_HOURS = float(os.getenv('ORDER_TTL_HOURS', '48'))
except ValueError:
    raise SystemExit('ORDER_TTL_HOURS 必須是數字') from None
if not 0.5 <= ORDER_TTL_HOURS <= 168:
    raise SystemExit('ORDER_TTL_HOURS 必須介於 0.5 與 168 小時')
ORDER_TTL_MS = int(ORDER_TTL_HOURS * 3_600_000)
# 附加 TP/SL 生效前的觀察窗（秒）。父單部分成交時，OKX 可能還沒建立
# attachAlgoOrds；這段時間內不要撤餘單、也不要平倉。
try:
    PROTECTION_GRACE_SECONDS = float(os.getenv('PROTECTION_GRACE_SECONDS', '600'))
except ValueError:
    raise SystemExit('PROTECTION_GRACE_SECONDS 必須是數字') from None

# 連續虧損暫停：連虧 N 筆後停止開新倉 M 小時。
# 2000 天回測（多單）：連虧 3 筆暫停 24h → 獲利 +123,150U（vs 不暫停 +88,850U）
#                     最大回撤 4,950U（vs 9,350U）。0 = 停用。
try:
    LOSS_STREAK_LIMIT = int(os.getenv('LOSS_STREAK_LIMIT', '3'))
    LOSS_STREAK_PAUSE_HOURS = float(os.getenv('LOSS_STREAK_PAUSE_HOURS', '24'))
except ValueError:
    raise SystemExit('LOSS_STREAK_LIMIT / LOSS_STREAK_PAUSE_HOURS 必須是數字') from None
if LOSS_STREAK_LIMIT < 0 or LOSS_STREAK_PAUSE_HOURS < 0:
    raise SystemExit('LOSS_STREAK_* 不可為負')
LOSS_STREAK_PAUSE_MS = int(LOSS_STREAK_PAUSE_HOURS*3_600_000)
if not 0 <= PROTECTION_GRACE_SECONDS <= 1800:
    raise SystemExit('PROTECTION_GRACE_SECONDS 必須介於 0 與 1800 秒')
# TP/SL 百分比。capped 回測（名額+TTL 正確計入，29 檔 x 5 年，順勢濾網）：
#   tp4/sl6 -36,550U｜tp2.5/sl4 +47,438U（最佳）
# 舊的 4%/6% 來自「無名額上限」的回測，加上名額與 TTL 後是虧的。
TP_PCT = _num('TP_PCT', '0.025')
SL_PCT = _num('SL_PCT', '0.04')
if not (D(0) < TP_PCT < D(1) and D(0) < SL_PCT < D(1)):
    raise SystemExit('TP_PCT / SL_PCT 必須介於 0 與 1')
STOP_DIST = _num('STOP_DIST_PCT', str(SL_PCT))           # 與 SL_PCT 保持一致
# 進場層級（Fib 回撤）。capped 回測在既有順勢濾網（價格高於 EMA60）下越深越好：
#   0.886 -36,550U｜0.94 +49,444U（最佳）
# 濾網方向維持不變：多單只在價格高於 EMA60 時掛單，不在跌勢中接刀
# （若改成價格低於 EMA60，0.886 x RSI30-60 是 -179,100U）。
#
# Swing 視窗根數（4H）。capped 回測：每筆 EV 24 根優於 12 根
# （lb12 +62,531U / EV +18.3U → lb24 +49,444U / EV +31.5U）。
try:
    LOOKBACK_BARS = int(os.getenv('LOOKBACK_BARS', '24'))
except ValueError:
    raise SystemExit('LOOKBACK_BARS 必須是整數') from None
if not 5 <= LOOKBACK_BARS <= 180:
    raise SystemExit('LOOKBACK_BARS 必須介於 5 與 180')

# RSI 區間。capped 回測：RSI 55-85 遠優於 30-60
# （30-60 -36,550U → 55-85 +5,100U，其餘參數不變）。
RSI_LO = _num('RSI_LO', '55')
RSI_HI = _num('RSI_HI', '85')
if not (D(0) <= RSI_LO < RSI_HI <= D(100)):
    raise SystemExit('RSI_LO / RSI_HI 必須介於 0 與 100 且 RSI_LO < RSI_HI')

ENTRY_LEVEL = _num('ENTRY_LEVEL', '0.618')
if not (D(0) < ENTRY_LEVEL < D(1)):
    raise SystemExit('ENTRY_LEVEL 必須介於 0 與 1')
try:
    # 24 槽：capped 回測 12→24 槽由 +49,444U 提升到 +64,238U，24→36 槽僅 +956U 已飽和。
    # 最大回撤反而略降（-3,300U → -3,225U），因部位分散到更多幣種與時間點。
    MAX_OPEN_TRADES = int(os.getenv('MAX_OPEN_TRADES', '24'))
    MAX_NEW_ENTRIES_PER_DAY = int(os.getenv('MAX_NEW_ENTRIES_PER_DAY', '100'))
except ValueError:
    raise SystemExit('MAX_OPEN_TRADES / MAX_NEW_ENTRIES_PER_DAY 必須是整數') from None
if not (D(0) < RISK_PER_TRADE and D(0) < MAX_TOTAL_RISK
        and D(0) <= DAILY_LOSS_LIMIT
        and D(0) < STOP_DIST < D(1) and MAX_OPEN_TRADES > 0 and MAX_NEW_ENTRIES_PER_DAY >= 0):
    raise SystemExit('風控參數不合法：金額需為正、STOP_DIST_PCT 需介於 0 與 1、'
                     'MAX_OPEN_TRADES > 0、MAX_NEW_ENTRIES_PER_DAY >= 0')


default_notional = min(MAX_OPEN_TRADES * RISK_PER_TRADE / STOP_DIST,
                       MAX_TOTAL_RISK / max(STOP_DIST, SL_PCT))
MAX_TOTAL_NOTIONAL = _num('MAX_TOTAL_NOTIONAL_USDT', str(default_notional))
if not MAX_TOTAL_NOTIONAL.is_finite() or MAX_TOTAL_NOTIONAL <= 0:
    raise SystemExit('MAX_TOTAL_NOTIONAL_USDT 必須是有限正數')

EXCLUDED_BASES = frozenset({'BTC', 'ETH', 'XAU'})


def is_excluded(inst):
    return inst.partition('-')[0].upper() in EXCLUDED_BASES


def log(*args):
    print(datetime.now().astimezone().isoformat(timespec='seconds'), *args, flush=True)


# ---------------------------------------------------------------- Telegram 通知
# 只送出「值得知道」的事件（掛單、成交、停損、風控觸發），不送一般掃描訊息。
#
# 設定優先序：
#   1. 環境變數 TG_TOKEN / TG_CHAT
#   2. config.json 的 TG_TOKEN / TG_CHAT（與 API_KEY 放同一個檔）
# 兩者都沒設 → 靜默停用，不影響交易。
def _cfg_value(settings, *names):
    """從 config.json 取值（先環境變數）。"""
    for n in names:
        v = os.getenv(n)
        if v and str(v).strip():
            return str(v).strip()
    for n in names:
        v = settings.get(n)
        if v and str(v).strip():
            return str(v).strip()
    return ''


_API_SETTINGS = {}


def _load_api_settings():
    """只為了讀 TG_TOKEN/TG_CHAT，把 config.json 內容快取起來備用。"""
    for candidate in (ROOT / 'config.json', ROOT.parent / 'config.json', Path.cwd() / 'config.json'):
        try:
            if candidate.is_file():
                data = json.loads(candidate.read_text(encoding='utf-8-sig'))
                if isinstance(data, dict):
                    return data
        except Exception:
            continue
    return {}


_API_SETTINGS = _load_api_settings()
TG_TOKEN = _cfg_value(_API_SETTINGS, 'TG_TOKEN', 'TELEGRAM_BOT_TOKEN')
TG_CHAT = _cfg_value(_API_SETTINGS, 'TG_CHAT', 'TELEGRAM_CHAT_ID')
TG_ENABLED = bool(TG_TOKEN and TG_CHAT)
_tg_lock = threading.Lock()
_tg_last = 0.0
TG_MIN_INTERVAL = 1.2        # 秒；避免連續推送被 Telegram 限流


def notify(text):
    """送出 Telegram 通知；任何失敗都只記錄、不影響交易。"""
    if not TG_ENABLED:
        return
    global _tg_last
    with _tg_lock:
        wait = TG_MIN_INTERVAL - (time.monotonic() - _tg_last)
        if wait > 0:
            time.sleep(wait)
        _tg_last = time.monotonic()
        try:
            body = urlencode({'chat_id': TG_CHAT, 'text': text,
                              'parse_mode': 'HTML', 'disable_web_page_preview': 'true'}).encode()
            req = Request(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
                          data=body, method='POST',
                          headers={'Content-Type': 'application/x-www-form-urlencoded'})
            with urlopen(req, timeout=10) as r:
                out = json.load(r)
            if not out.get('ok'):
                log('Telegram 通知失敗', out.get('description'))
        except Exception as exc:
            log('Telegram 通知異常', type(exc).__name__)


class APIError(RuntimeError):
    pass


class SizeLimitRejected(APIError):
    pass


class Exchange:
    def __init__(self, config):
        self.config = config

    def call(self, path, params=None, body=None, private=True):
        route = '/api/v5/' + path
        if params:
            route += '?' + urlencode(params)
        method = 'GET' if body is None else 'POST'
        payload = '' if body is None else json.dumps(body, separators=(',', ':'))
        headers = {'Content-Type': 'application/json', 'User-Agent': 'FibOriginal/1'}
        if private:
            stamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            message = (stamp + method + route + payload).encode()
            sig = hmac.new(self.config['SECRET_KEY'].encode(), message, hashlib.sha256).digest()
            headers.update({'OK-ACCESS-KEY': self.config['API_KEY'], 'OK-ACCESS-TIMESTAMP': stamp,
                            'OK-ACCESS-SIGN': base64.b64encode(sig).decode(), 'OK-ACCESS-PASSPHRASE': self.config['PASSPHRASE']})
        request = Request(HOST + route, headers=headers, method=method, data=payload.encode() if payload else None)
        try:
            with urlopen(request, timeout=10) as response:
                out = json.load(response)
        except HTTPError as e:
            raise APIError(f'{path} HTTP {e.code}: {e.read(500).decode(errors="replace")}') from e
        if path=='trade/order' and body and body.get('ordType')=='post_only':
            rows = out.get('data')
            if isinstance(rows,list) and len(rows)==1 and isinstance(rows[0],dict):
                row = rows[0]
                if str(row.get('sCode'))=='51004' and row.get('ordId')=='' and row.get('clOrdId')==body.get('clOrdId'):
                    raise SizeLimitRejected(row.get('sMsg') or '51004')
        if out.get('code') != '0':
            raise APIError(f'{path}: {out.get("code")} {out.get("msg")} {str(out.get("data"))[:300]}')
        for item in out['data']:
            if isinstance(item, dict) and item.get('sCode', '0') != '0':
                raise APIError(f'{path}: {item.get("sCode")} {item.get("sMsg")}')
        return out['data']

    def pages(self, path, params, key):
        rows = []
        params = dict(params, limit=100)
        while True:
            page = self.call(path, params)
            rows.extend(page)
            if len(page) < 100:
                return rows
            cursor = page[-1][key]
            if cursor == params.get('after'):
                raise RuntimeError('分頁未前進')
            params['after'] = cursor


def indicators(prices):
    ema = mean(prices[:60])
    for price in prices[60:]:
        ema += (price-ema)*2/61
    moves = [b-a for a,b in zip(prices,prices[1:])]
    gain = mean(max(0,v) for v in moves[:14])
    loss = mean(max(0,-v) for v in moves[:14])
    for v in moves[14:]:
        gain = (gain*13+max(0,v))/14
        loss = (loss*13+max(0,-v))/14
    return ema, 100*gain/(gain+loss) if gain+loss else 50.


def align(value, tick):
    return (value/tick).to_integral_value(rounding=ROUND_DOWN)*tick


def price_targets(avg, tick):
    return align(avg*(D(1)+TP_PCT),tick), align(avg*(D(1)-SL_PCT),tick)


def signal(api, sp, bar):
    inst = sp['instId']
    candles = api.call('market/candles', dict(instId=inst, bar='4H', limit=181), private=False)
    rows = {int(r[0]):r for r in candles}
    if bar not in rows:
        return
    recent = []
    for n in range(1,181):
        r = rows.get(bar-n*H4)
        if r is None or r[8]!='1':
            break
        recent.append(r)
    if len(recent)<60:
        return
    closes = [float(r[4]) for r in reversed(recent)]
    ema,rsi = indicators(closes)
    # capped 回測（名額+TTL 正確計入）：順勢區間 RSI 55-85 才是正期望值；
    # 舊的 RSI 30-60 是 -36,550U。方向濾網不變：價格須高於 EMA60。
    if closes[-1]<=ema or not float(RSI_LO)<=rsi<=float(RSI_HI):
        return
    daily = api.call('market/candles',dict(instId=inst,bar='1D',limit=62),private=False)
    days = {int(r[0]) for r in daily if r[8]=='1'}
    day = (bar+28_800_000)//DAY*DAY-28_800_000
    if not all(day-i*DAY in days for i in range(1,61)):
        return
    op = float(rows[bar][1])
    hi = max([op]+[float(r[2]) for r in recent[:LOOKBACK_BARS]])
    lo = min([op]+[float(r[3]) for r in recent[:LOOKBACK_BARS]])
    # v3 多單：只掛單一深層回撤位，可用 ENTRY_LEVEL 調整。
    # capped 回測（名額+TTL 正確計入，29 檔 × 5 年，價格須高於 EMA60）：
    #   0.886 -36,550U｜0.94 +49,444U（預設）
    # 越深越好；淺回撤（0.382/0.5）等於追高，在多單是虧的。改動前請重跑回測。
    for level in (float(ENTRY_LEVEL),):
        raw = round(hi-(hi-lo)*level,4)
        if .0005 <= (op-raw)/op <= .10:
            px = align(D(str(raw)),D(sp['tickSz']))
            if px>0:
                return px, rsi, (op - float(raw)) / op   # 回傳 (價, RSI, 進場深度)
            break


# 掃描節奏。SCAN_INTERVAL_MINUTES=0 → 只在 4H 收盤後掃一次（原行為）。
# 設成 >0 則每 N 分鐘掃描一次（同一 4H 內重複掃描，委託用 clOrdId 去重，不會重複下單）。
try:
    _scan_interval_min = float(os.getenv('SCAN_INTERVAL_MINUTES', '0') or 0)
except ValueError:
    raise SystemExit('SCAN_INTERVAL_MINUTES 必須是數字') from None
if _scan_interval_min < 0:
    raise SystemExit('SCAN_INTERVAL_MINUTES 不可為負')
if 0 < _scan_interval_min < 1:
    raise SystemExit('SCAN_INTERVAL_MINUTES 至少 1 分鐘（避免 API 限速）')
SCAN_INTERVAL_MS = int(_scan_interval_min * 60_000)

# 偵測到訊號後，允許送單的時間窗（分鐘）。避免掃描跑很久後仍在舊價位下單。
try:
    _entry_window_min = float(os.getenv('ENTRY_WINDOW_MINUTES', '15') or 15)
except ValueError:
    raise SystemExit('ENTRY_WINDOW_MINUTES 必須是數字') from None
ENTRY_WINDOW_MS = max(60_000, int(_entry_window_min * 60_000))

# 相容舊名：enter() 預設 deadline 使用
SCAN_WINDOW = ENTRY_WINDOW_MS


# v3: BTC daily filter is OFF by default.
# Measured on the same 20-symbol sample: the "+10% in 7 days" gate removed 86% of
# signals (334 -> 45 trades) without improving win rate enough to pay for the lost
# opportunity (total P&L 18,200 -> 3,100). Set BTC_FILTER=200ma or BTC_FILTER=10pct
# to re-enable one of the variants.
BTC_FILTER = (os.getenv('BTC_FILTER') or 'off').strip().lower()
if BTC_FILTER not in ('off', '10pct', '200ma'):
    raise SystemExit('BTC_FILTER 只接受 off / 10pct / 200ma')


def btc_allows(api, bar):
    """Optional BTC regime gate. Returns True when the filter is off."""
    if BTC_FILTER == 'off':
        return True
    day = (bar + 28_800_000)//DAY*DAY - 28_800_000
    if BTC_FILTER == '10pct':
        rows = api.call('market/candles', dict(instId='BTC-USDT-SWAP', bar='1D', limit=10), private=False)
        closes = {int(row[0]):D(row[4]) for row in rows if row[8]=='1'}
        days = [day-i*DAY for i in range(1,9)]
        return all(t in closes for t in days) and closes[days[0]] > closes[days[-1]]*D('1.10')
    # 200ma: latest completed BTC daily close above its own 200-day mean.
    rows = api.call('market/candles', dict(instId='BTC-USDT-SWAP', bar='1D', limit=250), private=False)
    hist = sorted(((int(r[0]), D(r[4])) for r in rows if r[8]=='1'), key=lambda x: x[0])
    prior = [c for t, c in hist if t < day]
    if len(prior) < 200:
        return False
    return prior[-1] > sum(prior[-200:], D(0)) / 200


def scanner(api, events):
    previous_bar = None
    last_scan = 0.0
    while True:
        try:
            now = int(time.time()*1000)
            bar = now//H4*H4
            startup = previous_bar is None
            if startup:
                due = True
            elif SCAN_INTERVAL_MS > 0:
                # 定時掃描：每 N 分鐘一次，不受 4H 收盤限制
                due = (time.monotonic()*1000 - last_scan) >= SCAN_INTERVAL_MS
            else:
                # 原行為：只在 4H 收盤後 ENTRY_WINDOW 內掃一次
                due = (bar != previous_bar) and (now-bar >= 2000) and (now < bar+ENTRY_WINDOW_MS)
            if not due:
                time.sleep(1)
                continue
            if not btc_allows(api,bar):
                previous_bar = bar
                last_scan = time.monotonic()*1000
                log('已收 BTC 日線未通過，本輪略過新增掛單')
                time.sleep(1)
                continue
            specs = api.call('public/instruments',dict(instType='SWAP'),private=False)
            deadline = min(bar+H4, now+ENTRY_WINDOW_MS)
            previous_bar = bar
            last_scan = time.monotonic()*1000
            candidates = 0
            pending_signals = []
            log('啟動首輪掃描' if startup else ('定時掃描' if SCAN_INTERVAL_MS else '4H 收盤掃描'), '開始檢查掛多訊號')
            for sp in specs:
                if int(time.time()*1000) >= deadline:
                    log('本輪進場時窗結束')
                    break
                if (sp['state']!='live' or sp.get('instCategory')!='1' or sp.get('ctType')!='linear'
                    or sp.get('settleCcy')!='USDT' or is_excluded(sp['instId'])):
                    continue
                try:
                    out = signal(api,sp,bar)
                    if out:
                        px, rsi, depth = out
                        pending_signals.append((depth,sp,px))
                        candidates += 1
                except Exception as e:
                    log('行情略過',sp['instId'],e)
                time.sleep(.08)
            # 多單：進場越深（回撤越深）越優先。
            # 500 天 x 38 檔回測：這個排序在全部樣本 +1500U，樣本外 +2450U，
            # 而 RSI 排序在樣本內是負的。
            pending_signals.sort(key=lambda x: -x[0])
            for rsi_v, sp_, px_ in pending_signals:
                events.put((bar, sp_, px_, deadline))
            log('本輪掃描結束，候選訊號數 %d（已依進場深度排序）' % candidates)
        except Exception as e:
            log('掃描錯誤',e)
            time.sleep(5)


def order_size(sp, px):
    """固定風險金額 → 張數。風險 = 張數 × ctVal × 停損距離。

    原版用固定 5000U 名義，等於每筆固定虧 300U，帳戶小的時候一筆就重傷。
    這裡改由 RISK_PER_TRADE 反推張數，風險與價格、停損距離無關。
    """
    lot = D(sp['lotSz'])
    unit = D(sp['ctVal'])*D(sp.get('ctMult') or '1')
    if unit<=0 or px<=0 or STOP_DIST<=0:
        return ZERO
    risk_per_contract = unit*px*STOP_DIST
    if risk_per_contract<=0:
        return ZERO
    raw = RISK_PER_TRADE/risk_per_contract
    sz = (raw/lot).to_integral_value(rounding=ROUND_DOWN)*lot
    # 名義額上限（避免小幣 / 低價幣張數爆量）
    notional = sz*unit*px
    if notional>MAX_TOTAL_NOTIONAL:
        sz = (MAX_TOTAL_NOTIONAL/(unit*px)/lot).to_integral_value(rounding=ROUND_DOWN)*lot
    cap = D(sp.get('maxLmtSz') or '0')
    if cap>0:
        sz = min(sz,align(cap,lot))
    return sz if sz>=D(sp['minSz']) else ZERO


def fmt(value):
    return format(value,'f')


def client_id(inst,bar):
    return PREFIX + hashlib.sha256(f'{inst}:{bar}'.encode()).hexdigest()[:23]


def risk_budget(mgr, proposed):
    if mgr.unresolved:
        return False, '前次送單或成交狀態待確認'
    occupied = set(mgr.pos) | {i for i, rows in mgr.pending.items() if rows}
    if len(occupied) >= MAX_OPEN_TRADES:
        return False, '活動合約數已滿'
    used = ZERO
    for inst in occupied:
        unit = mgr._ctval_cache.get(inst)
        if unit is None:
            rows = mgr.api.call('public/instruments', dict(instType='SWAP', instId=inst), private=False)
            spec = next(r for r in rows if r['instId']==inst)
            unit = D(spec['ctVal'])*D(spec.get('ctMult') or '1')
            if unit <= 0:
                raise ValueError(f'{inst} 合約面值無效')
            mgr._ctval_cache[inst] = unit
        position = mgr.pos.get(inst)
        if position:
            used += abs(D(position['pos']))*unit*max(D(position['avgPx']),D(position.get('markPx') or position['avgPx']))
        for order in mgr.pending.get(inst, []):
            remaining = D(order['sz'])-D(order['accFillSz'])
            price = D(order['px'])
            if remaining < 0 or price <= 0:
                return False, f'{inst} 掛單金額無法確認'
            used += remaining*unit*price
    if used+proposed > MAX_TOTAL_NOTIONAL:
        return False, (f'總名義額度不足：已用 {used:,.2f} U，本單 {proposed:,.2f} U，'
                       f'上限 {MAX_TOTAL_NOTIONAL:,.2f} U，尚可使用 {max(ZERO, MAX_TOTAL_NOTIONAL-used):,.2f} U')
    if (used+proposed)*max(STOP_DIST, SL_PCT) > MAX_TOTAL_RISK:
        return False, '總計畫風險額度不足'
    return True, ''


def daily_state(mgr):
    """回傳 (今日已實現損益, 今日新增筆數)。跨日自動歸零。"""
    day = int(time.time()*1000)//DAY
    row = mgr.db.execute("select v from stats where k='day'").fetchone()
    pnl = mgr.db.execute("select v from stats where k='day_pnl'").fetchone()
    cnt = mgr.db.execute("select v from stats where k='day_cnt'").fetchone()
    if not row or D(row[0]) != day:
        return D(0), 0, day
    return D(pnl[0]) if pnl else D(0), int(cnt[0]) if cnt else 0, day


def bump_daily(mgr, day, pnl_delta=None, count_delta=0):
    cur_pnl, cur_cnt, stored = daily_state(mgr)
    if stored != day:
        cur_pnl, cur_cnt = D(0), 0
    np = cur_pnl + (D(str(pnl_delta)) if pnl_delta is not None else D(0))
    nc = cur_cnt + count_delta
    with mgr.db:
        mgr.db.execute("insert or replace into stats values('day',?)",(str(day),))
        mgr.db.execute("insert or replace into stats values('day_pnl',?)",(fmt(np),))
        mgr.db.execute("insert or replace into stats values('day_cnt',?)",(str(nc),))


def entry_gate(mgr, proposed):
    """所有新增倉前的統一檢查。回傳 (可否, 原因)。"""
    day = int(time.time()*1000)//DAY
    pnl, cnt, stored = daily_state(mgr)
    if stored != day:
        pnl, cnt = D(0), 0
    if pnl <= -DAILY_LOSS_LIMIT:
        key = 'warned_loss_%d' % day
        row = mgr.db.execute("select 1 from stats where k=?", (key,)).fetchone()
        if not row:
            mgr.db.execute("insert or replace into stats values(?,?)", (key, '1'))
            mgr.db.commit()
            notify(f'🚫 <b>風控停止新增</b>\n今日已實現虧損 {float(pnl):.1f}U '
                   f'達上限 -{float(DAILY_LOSS_LIMIT):.0f}U\n已停止開新倉')
        return False, f'今日已實現虧損 {pnl}U 達上限 -{DAILY_LOSS_LIMIT}U，停止新增'
    if cnt >= MAX_NEW_ENTRIES_PER_DAY:
        return False, f'今日新增 {cnt} 筆已達上限 {MAX_NEW_ENTRIES_PER_DAY}'
    if LOSS_STREAK_LIMIT > 0:
        row = mgr.db.execute("select v from stats where k='pause_until'").fetchone()
        until = int(float(row[0])) if row else 0
        if until and int(time.time()*1000) < until:
            left = (until-int(time.time()*1000))/60_000
            return False, f'連續虧損暫停中（剩 {left:.0f} 分鐘）'
    return risk_budget(mgr, proposed)


def index_by_inst(rows):
    result = {}
    for row in rows:
        result.setdefault(row['instId'], []).append(row)
    return result


class Manager:
    def __init__(self, api, db, pos_side="net", shared=False):
        self.shared = shared
        self.unresolved = set()
        self.final_fills = {}
        self.pos_side = pos_side
        self.api, self.db = api, db
        self.uncovered = {}
        self.alert = set()
        self.next_leverage = set()
        self._record_close_pending = {}
        self._ctval_cache = {}
        db.executescript("""
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, inst TEXT, bar INTEGER, tick TEXT, phase TEXT, sent REAL);
        CREATE TABLE IF NOT EXISTS sizes(inst TEXT PRIMARY KEY, qty TEXT);
        CREATE TABLE IF NOT EXISTS seen_legs(inst TEXT, algo TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS binding(uid TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS stats(k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS closed(inst TEXT, bar INTEGER, pnl TEXT, closed_ms INTEGER, PRIMARY KEY(inst,bar));
        """)

    def record(self, sql, args):
        with self.db:
            self.db.execute(sql,args)

    def cancel(self, inst, rows):
        for r in rows:
            self.api.call('trade/cancel-order',body=dict(instId=inst,ordId=r['ordId']))

    def owns_position(self, inst, orders, position):
        # Positive identification by the actual filled quantity and cost of our entries.
        # After an ambiguous partial exit, leave the symbol blocked until flat.
        qty = ZERO
        cost = ZERO
        for cid, symbol, _, _, phase, _ in orders.values():
            if symbol != inst or phase not in ('intent','active'):
                continue
            fill = self.final_fills.get(cid)
            if fill is None:
                row = self.api.call('trade/order',dict(instId=inst,clOrdId=cid))[0]
                if (row['clOrdId'] != cid or row['instId'] != inst or
                    row['side'] != 'buy' or row['posSide'] != self.pos_side or row['tdMode'] != 'cross'):
                    return False
                fill = D(row['accFillSz']), D(row.get('avgPx') or '0')
                if row['state'] in ('filled','canceled','mmp_canceled'):
                    self.final_fills[cid] = fill
            qty += fill[0]
            cost += fill[0]*fill[1]
        # 張數必須完全相符（避免歸屬錯誤），但均價用寬鬆容差：
        # 交易所 avgPx 與本地累計 cost/qty 會有小數尾差（實測到 4e-5），
        # 1e-8 的容差會誤判成「不是我們的部位」而永久封鎖該幣。
        held = abs(D(position['pos']))
        if qty <= 0 or qty != held:
            return False
        avg = D(position['avgPx'])
        if avg <= 0:
            return True
        return abs(cost/qty-avg) <= max(avg*D('0.0005'), D('0.00000001'))

    def sync(self):
        api = self.api
        pending = api.pages('trade/orders-pending',dict(instType='SWAP'),'ordId')
        algos = []
        for kind in ('oco','conditional'):
            algos.extend(api.pages('trade/orders-algo-pending',dict(instType='SWAP',ordType=kind),'algoId'))
        # 只算「本策略方向」的掛單。否則空單會把多單的掛單算進自己的名額，
        # 反之亦然（多空同時跑時會互相吃掉額度）。
        self.foreign_order_insts = {r['instId'] for r in pending if not is_excluded(r['instId']) and r.get('posSide')!=self.pos_side}
        pending = [r for r in pending
                   if not is_excluded(r['instId']) and r.get('posSide') == self.pos_side]
        # 同樣只保留本方向的保護單；別方向的 OCO 屬於另一個策略，不該干擾核對。
        algos = [r for r in algos
                 if not is_excluded(r['instId']) and r.get('posSide') in (self.pos_side, '', None)]
        poses = [r for r in api.call('account/positions',dict(instType='SWAP')) if not is_excluded(r['instId']) and D(r['pos'])]
        self.pos = {}
        self.blocked = set(self.foreign_order_insts)
        self.protection_pending = set()
        for r in poses:
            if r['instId'] in self.pos or r['posSide']!=self.pos_side or r['mgnMode']!='cross' or D(r['pos'])<0:
                self.blocked.add(r['instId'])
                continue
            self.pos[r['instId']] = r
        self.pending = index_by_inst(pending)
        grouped = index_by_inst(algos)
        orders = {r[0]:r for r in self.db.execute('select id,inst,bar,tick,phase,sent from orders') if not is_excluded(r[1])}
        expired = set()
        now = int(time.time()*1000)
        for row in pending:
            saved = orders.get(row['clOrdId'])
            # 用「下單時間」(sent，秒) 判斷 TTL，不是 bar（K 線時間）。
            # 原本用 bar 會讓 TTL 隨 K 線位移，最多偏差一根 4H。
            placed_ms = int(float(saved[5])*1000) if saved and saved[5] else 0
            if saved and saved[1]==row['instId'] and placed_ms and now >= placed_ms + ORDER_TTL_MS:
                # 到期撤單：釋放名額。撤單成功後「不」封鎖該幣，
                # 否則這一輪即使有訊號也進不去，等於 TTL 反而卡住自己。
                try:
                    self.cancel(row['instId'],[row])
                    expired.add(row['ordId'])
                    # 保留原單，直到查單確認終態並核對持倉。
                    log(row['instId'], '掛單超過 %.1f 小時已送撤單，等待成交與終態核對' % ORDER_TTL_HOURS)
                except Exception as exc:
                    # 撤單結果不明 → 保守封鎖，等下一輪確認
                    self.blocked.add(row['instId'])
                    log('%s 到期撤單失敗，暫時封鎖：%s',row['instId'],exc)
        known = {v[1] for v in orders.values() if v[4] in ('intent','active')}
        valid_children = {'B'+cid for cid in orders}
        for row in pending:
            if row['clOrdId'] not in orders:
                self.blocked.add(row['instId'])
        for row in algos:
            if row.get('algoClOrdId') not in valid_children and row.get('attachAlgoClOrdId') not in valid_children:
                self.blocked.add(row['instId'])
        self.blocked.update(set(self.pos)-known)
        ambiguous = {inst for inst in self.pos if sum(r['instId']==inst and r['posSide']==self.pos_side for r in poses)>1}
        for cid,inst,bar,tick,phase,sent in orders.values():
            if phase!='intent':
                continue
            try:
                detail = api.call('trade/order',dict(instId=inst,clOrdId=cid))[0]
                self.record('update orders set phase=? where id=?',('active',cid))
            except APIError as e:
                # Ambiguous submission must never be retried with a fresh ID.
                if '51603' in str(e) and time.time()-sent>60 and inst not in self.pos and not self.pending.get(inst):
                    self.record('update orders set phase=? where id=?',('done',cid))
                else:
                    self.blocked.add(inst)
        owned = {cid for cid,row in orders.items() if row[4] in ('intent','active')}
        visible = {r['clOrdId'] for r in pending}
        # 部分成交已可見、持倉快照尚未跟上時，暫停新增。
        pending_fills = {r['clOrdId'] for r in pending if r['clOrdId'] in owned and
                         D(r.get('accFillSz') or '0') > abs(D(self.pos.get(r['instId'],{}).get('pos') or '0'))}
        self.unresolved = pending_fills | {cid for cid in owned if orders[cid][4]=='intent' or
                           (cid not in visible and orders[cid][1] not in self.pos)}
        for inst in known:
            if inst in ambiguous:
                self.blocked.add(inst)
                continue
            try:
                if self.shared and inst in self.pos and not self.owns_position(inst,orders,self.pos[inst]):
                    self.blocked.add(inst)
                    continue
                children = {'B'+cid for cid in owned if orders[cid][1]==inst}
                legs = grouped.get(inst,[])
                own_legs = [r for r in legs if r.get('algoClOrdId') in children or r.get('attachAlgoClOrdId') in children]
                self.protect(inst, orders, own_legs, has_external=len(own_legs)!=len(legs))
            except Exception as e:
                self.blocked.add(inst)
                log('保護單核對異常',inst,e)
        if self.shared:
            # 只撤「確實不該存在」的掛單。
            # 保護單尚未生效（self.protection_pending）不算，否則會在
            # 部分成交的空窗期把餘單撤掉，造成有部位卻沒有後續成交機會。
            for inst in self.blocked:
                if inst in getattr(self,'protection_pending',set()):
                    continue
                ours = [r for r in self.pending.get(inst,[]) if r['clOrdId'] in orders and r['ordId'] not in expired]
                if ours:
                    self.cancel(inst,ours)
        if self.blocked and self.blocked!=self.alert:
            log('以下合約暫停新增掛單',sorted(self.blocked))
        self.alert = self.blocked.copy()

    def protect(self,inst,orders,legs,has_external=False):
        working = [r for r in self.pending.get(inst,[]) if r['clOrdId'] in orders and orders[r['clOrdId']][4] in ('intent','active')]
        position = self.pos.get(inst)
        qty = abs(D(position['pos'])) if position else ZERO
        old = self.db.execute('select qty from sizes where inst=?',(inst,)).fetchone()
        old_qty = D(old[0]) if old else ZERO
        previous = {r[0] for r in self.db.execute('select algo from seen_legs where inst=?',(inst,))}
        current = {leg['algoId'] for leg in legs}
        partial = any(r['state']=='partially_filled' for r in working)
        # 部分成交不要立刻撤餘單：attachAlgoOrds 要等父單結束才生效，
        # 這段空窗期撤單會造成「有部位、沒保護」，反而更危險。
        # 只有在「持倉已減少」或「保護單消失」這兩個確定的情況下才撤。
        cancel_remaining = False
        if working and (qty<old_qty or previous-current):
            disappeared = previous-current
            # 保護單消失 = 可能已觸發止盈/停損 → 撤掉餘單避免重新開倉
            # 沒有消失 = 只是持倉變動，先不撤
            cancel_remaining = bool(disappeared)
            for algo in disappeared:
                try:
                    detail = self.api.call('trade/order-algo',dict(algoId=algo))[0]
                    cancel_remaining |= detail.get('actualSide')!='tp' or detail['state']!='effective'
                except (APIError,OSError,IndexError):
                    cancel_remaining = True
        if working and cancel_remaining:
            self.cancel(inst,working)
            self.blocked.add(inst)
            return
        with self.db:
            self.db.execute('delete from seen_legs where inst=?',(inst,))
            self.db.executemany('insert into seen_legs values(?,?)',[(inst,x) for x in current])
        if not qty:
            self.uncovered.pop(inst,None)
            if working or legs:
                return
            # Verify terminal parents before forgetting a flat cycle (snapshots can race).
            for cid,_,_,_,phase,_ in [r for r in orders.values() if r[1]==inst and r[4]=='active']:
                detail = self.api.call('trade/order',dict(instId=inst,clOrdId=cid))[0]
                if detail.get('clOrdId')!=cid or detail.get('instId')!=inst or detail.get('accFillSz') in (None,'') or detail['state'] not in ('filled','canceled','mmp_canceled'):
                    self.blocked.add(inst)
                    return
                if time.time()*1000-int(detail['uTime'])<15000:
                    self.blocked.add(inst)
                    return
                fresh = self.api.call('account/positions',dict(instId=inst))
                if any(D(r['pos']) and r['posSide']==self.pos_side for r in fresh):
                    self.blocked.add(inst)
                    return
                self.record('update orders set phase=? where id=?',('done',cid))
            self.record('insert or replace into sizes values(?,?)',(inst,'0'))
            self._record_close(inst, orders)
            return
        self._record_close_pending[inst] = (qty, D(position['avgPx']), orders)
        self.record('insert or replace into sizes values(?,?)',(inst,fmt(qty)))
        tick = D(next(r[3] for r in reversed(list(orders.values())) if r[1]==inst and r[4] in ('intent','active')))
        tp,sl = price_targets(D(position['avgPx']),tick)
        tp_qty = sl_qty = ZERO
        seen = set()
        for leg in legs:
            aid = leg.get('algoId')
            if not aid or aid in seen or leg.get('side')!='sell' or leg.get('state')!='live':
                continue
            kind = leg.get('ordType')
            has_tp = bool(leg.get('tpTriggerPx'))
            has_sl = bool(leg.get('slTriggerPx'))
            if not ((kind=='oco' and has_tp and has_sl) or
                    (kind=='conditional' and has_tp!=has_sl)):
                continue
            seen.add(aid)
            size = qty if leg.get('closeFraction')=='1' else D(leg.get('sz') or '0')
            if size <= 0:
                continue
            changes = {}
            for prefix, target in (('tp',tp),('sl',sl)):
                trigger = leg.get(prefix+'TriggerPx')
                if not trigger:
                    continue
                if D(trigger)!=target:
                    changes['new'+prefix.capitalize()+'TriggerPx'] = fmt(target)
                    changes['new'+prefix.capitalize()+'OrdPx'] = '-1'
                elif leg.get(prefix+'OrdPx')=='-1' and leg.get(prefix+'TriggerPxType','last')=='last':
                    if prefix=='tp':
                        tp_qty += size
                    else:
                        sl_qty += size
            if changes:
                self.api.call('trade/amend-algos',body=dict(instId=inst,algoId=aid,cxlOnFail=False,**changes))
        covered = min(tp_qty,sl_qty)
        if tp_qty==qty and sl_qty==qty:
            self.uncovered.pop(inst,None)
            self.protection_pending.discard(inst)
            return
        # 保護單不足。可能是：(a) 附加單還沒生效（父單仍活著）、(b) 真的缺保護。
        # 先給一個觀察窗，不要在第一次看到 covered=0 就撤單或平倉。
        since = self.uncovered.setdefault(inst,time.monotonic())
        waited = time.monotonic()-since
        if working and waited < PROTECTION_GRACE_SECONDS:
            # 父單還活著、附加保護尚未出現 → 只標記「待生效」，不封鎖、不撤單。
            self.protection_pending.add(inst)
            log(inst, '保護待生效（持倉 %s，已驗證 %s）；父單仍活躍，等 %.0f/%.0f 秒'
                % (fmt(qty), fmt(covered), waited, PROTECTION_GRACE_SECONDS))
            return
        self.protection_pending.discard(inst)
        self.blocked.add(inst)
        log('保護數量待核對',inst,'持倉',fmt(qty),'已核對止盈',fmt(tp_qty),'已核對止損',fmt(sl_qty))
        if has_external:
            log(inst,'另有歸屬未確認的保護單，請人工核對；已封鎖新增', 'TP',fmt(tp_qty),'SL',fmt(sl_qty))
            return
        if working:
            self.cancel(inst,working)
        elif waited>=PROTECTION_GRACE_SECONDS:
            # Dedicated account only. Reduce-only market orders cannot reverse the position.
            fresh = self.api.call('account/positions',dict(instId=inst))
            long = next((r for r in fresh if r['posSide']==self.pos_side and r['mgnMode']=='cross' and D(r['pos'])>0),None)
            if long and (not self.shared or self.owns_position(inst,orders,long)):
                exit_order = dict(instId=inst,tdMode='cross',posSide=self.pos_side,
                                  side='sell',ordType='market',sz=long['pos'])
                if self.pos_side == 'net':
                    exit_order['reduceOnly'] = True
                self.api.call('trade/order',body=exit_order)
                log('保護數量不符，已送出只減倉市價退出',inst)
                self.uncovered[inst]=time.monotonic()

    def _track_streak(self, pnl):
        """連續虧損計數；達門檻就設定暫停到期時間。"""
        if LOSS_STREAK_LIMIT <= 0:
            return
        row = self.db.execute("select v from stats where k='loss_streak'").fetchone()
        streak = int(row[0]) if row else 0
        if pnl < 0:
            streak += 1
        else:
            streak = 0
        with self.db:
            self.db.execute("insert or replace into stats values('loss_streak',?)", (str(streak),))
            if streak >= LOSS_STREAK_LIMIT:
                until = int(time.time()*1000) + LOSS_STREAK_PAUSE_MS
                self.db.execute("insert or replace into stats values('pause_until',?)", (str(until),))
                self.db.execute("insert or replace into stats values('loss_streak','0')")
        if streak >= LOSS_STREAK_LIMIT:
            log('連續虧損 %d 筆，暫停開新倉 %.1f 小時' % (streak, LOSS_STREAK_PAUSE_HOURS))
            notify(f'⏸ <b>連續虧損暫停</b>\n連虧 {streak} 筆，'
                   f'停止開新倉 {LOSS_STREAK_PAUSE_HOURS:g} 小時')

    def _record_close(self, inst, orders):
        """一個持倉週期結束（回到 flat）時結算已實現損益，供每日虧損煞車使用。"""
        pending_info = getattr(self, '_record_close_pending', {}).pop(inst, None)
        if not pending_info:
            return
        qty_seen, entry, _ = pending_info
        # 用最近的成交價當出場價估算；僅作為煞車用途，不需精確到分。
        try:
            fills = self.api.call('trade/fills', dict(instType='SWAP', instId=inst, limit='20'), private=True)
            sells = [D(f['fillPx']) for f in fills if f.get('side') == 'sell' and D(f.get('fillSz')) > 0]
            exit_px = sells[0] if sells else entry
        except Exception:
            exit_px = entry
        # 以 ctVal 換算成 U：qty × ctVal × 價差
        ct = getattr(self, '_ctval_cache', {}).get(inst)
        if ct is None:
            try:
                spec = self.api.call('public/instruments', dict(instType='SWAP'), private=False)
                self._ctval_cache = {r['instId']: D(r['ctVal']) * D(r.get('ctMult') or '1') for r in spec}
                ct = self._ctval_cache.get(inst, D(0))
            except Exception:
                ct = D(0)
        pnl = (exit_px - entry) * qty_seen * ct
        bump_daily(self, int(time.time()*1000)//DAY, pnl_delta=pnl)
        self._track_streak(pnl)
        log('週期結算', inst, '進場', fmt(entry), '出場', fmt(exit_px), '損益約 %.2fU' % float(pnl))
        day_pnl, day_cnt, _ = daily_state(self)
        icon = '✅' if pnl > 0 else '🛑'
        notify(f'{icon} <b>平倉</b> {inst}\n'
               f'{fmt(entry)} → {fmt(exit_px)}｜{float(pnl):+.1f}U\n'
               f'今日累計 {float(day_pnl):+.1f}U / {day_cnt} 筆')

    def enter(self,bar,sp,px,deadline=None):
        if deadline is None:
            deadline = bar + SCAN_WINDOW
        inst = sp['instId']
        if is_excluded(inst) or (inst in self.blocked if self.shared else bool(self.blocked)) or self.pending.get(inst) or int(time.time()*1000)>=deadline:
            return
        cid = client_id(inst,bar)
        # 只有「已經真的送出並存活」的單才擋重複。
        # 上一輪失敗（done/rejected）必須允許在同一根 K 線內重試，
        # 否則一次錯誤就會讓這個幣在整個 4H 內靜默跳過。
        prior = self.db.execute('select phase from orders where id=?',(cid,)).fetchone()
        if self.db.execute("SELECT 1 FROM orders WHERE inst=? AND phase IN ('intent','active') LIMIT 1", (inst,)).fetchone():
            return
        if prior and prior[0] in ('intent','active','rejected'):
            return
        if prior:
            # 清掉失敗紀錄以便重試（clOrdId 由 inst:bar 決定，交易所端也沒有殘留）
            self.record('delete from orders where id=?',(cid,))
        position = self.pos.get(inst)
        if position:
            return
        sz = order_size(sp,px)
        tp,sl = price_targets(px,D(sp['tickSz']))
        if not sz or not (0<sl<px<tp):
            return
        unit = D(sp['ctVal'])*D(sp.get('ctMult') or '1')
        self._ctval_cache[inst] = unit
        ok, why = entry_gate(self, sz*px*unit)
        if not ok:
            log('略過進場',inst,why)
            return
        if self.shared:
            settings = self.api.call('account/leverage-info',dict(instId=inst,mgnMode='cross'))
            valid = [r for r in settings if r['instId']==inst and r['mgnMode']=='cross' and
                     r.get('posSide','') in ('','net',self.pos_side)]
            if not valid or any(D(r['lever'])!=10 for r in valid):
                log('略過訊號，此合約全倉槓桿未確認為 10 倍',inst)
                return
        elif inst not in self.next_leverage:
            self.api.call('account/set-leverage',body=dict(instId=inst,lever='10',mgnMode='cross'))
            self.next_leverage.add(inst)
        if int(time.time()*1000) >= deadline:
            return
        self.record('insert into orders values(?,?,?,?,?,?)',(cid,inst,bar,sp['tickSz'],'intent',time.time()))
        self.unresolved.add(cid)
        try:
            self.api.call('trade/order',body=dict(instId=inst,tdMode='cross',posSide=self.pos_side,side='buy',
                ordType='post_only',px=fmt(px),sz=fmt(sz),clOrdId=cid,attachAlgoOrds=[dict(
                attachAlgoClOrdId='B'+cid,tpTriggerPx=fmt(tp),tpOrdPx='-1',slTriggerPx=fmt(sl),slOrdPx='-1',
                tpTriggerPxType='last',slTriggerPxType='last')]))
        except SizeLimitRejected as exc:
            self.record('update orders set phase=? where id=?',('rejected',cid))
            self.unresolved.discard(cid)
            log('交易所張數限制 51004，略過本根訊號',inst,exc)
            return
        except APIError as exc:
            # 交易所明確拒單（有 sCode、無 ordId）→ 標記 done，不封鎖幣種、不重試。
            # 只有「回應不明」才留在 intent 等下輪核對。
            msg = str(exc)
            if 'sCode' in msg and 'ordId' in msg and "'ordId': ''" in msg:
                self.record('update orders set phase=? where id=?',('done',cid))
                self.unresolved.discard(cid)
                log('明確拒單',inst,msg[:180])
                notify(f'⚠️ <b>拒單</b> {inst}\n<code>{msg[:160]}</code>')
                return
            raise
        self.record('update orders set phase=? where id=?',('active',cid))
        self.pending.setdefault(inst, []).append(dict(clOrdId=cid, sz=fmt(sz), accFillSz='0', px=fmt(px)))
        self.unresolved.discard(cid)
        bump_daily(self, int(time.time()*1000)//DAY, count_delta=1)
        risk_u = float(sz)*float(D(sp['ctVal'])*D(sp.get('ctMult') or '1'))*float(px)*float(STOP_DIST)
        log('已送出掛多',inst,fmt(px),fmt(sz),'風險≈%.0fU'%risk_u,cid)
        notify(f'🔺 <b>掛多</b> {inst}\n'
               f'進場 {fmt(px)}｜TP {fmt(tp)}｜SL {fmt(sl)}\n'
               f'張數 {fmt(sz)}｜風險 ≈ {risk_u:.0f}U')


def account_status(acc):
    uid, main_uid = acc.get('uid'), acc.get('mainUid')
    role = '未知' if not uid or not main_uid else ('主帳戶' if uid == main_uid else '子帳戶')
    mode = acc.get('posMode', '')
    level = acc.get('acctLv', '')
    levels = {'1':'現貨', '2':'合約', '3':'跨幣種保證金', '4':'組合保證金'}
    modes = {'net_mode':'淨持倉', 'long_short_mode':'雙向持倉'}
    log('帳戶診斷', role, levels.get(level,'未知帳戶模式'), f'acctLv={level}',
        modes.get(mode,'未知持倉模式'), f'posMode={mode}')
    errors = []
    if role == '未知':
        errors.append('無法從 OKX 回應核對帳戶身分')
    if level not in ('2','3'):
        errors.append('此版本支援合約模式或跨幣種保證金模式')
    if mode not in modes:
        errors.append('無法辨識持倉模式')
    return ('long' if mode == 'long_short_mode' else 'net'), errors


def main():
    raise SystemExit('Offline research reference copy only: live/demo execution is disabled.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='明確啟動正式盤')
    parser.add_argument('--check',action='store_true',help='只讀取帳戶模式並列出啟動條件')
    parser.add_argument('--confirm',action='store_true',help='啟動前額外要求輸入 LIVE（預設不需要）')
    args=parser.parse_args()
    # v3.1: 不再要求輸入 LIVE。直接執行即為實盤；--check 仍為唯讀。
    # 若仍想保留二段確認，加上 --confirm。
    if args.confirm and not args.check:
        try:
            if input('即將送出真實訂單，輸入 LIVE 確認：').strip() != 'LIVE':
                return
        except EOFError:
            return
    log('唯讀檢查 OKX 帳戶' if args.check else '實盤啟動，正在核對 OKX 帳戶')
    api=Exchange(json.loads((ROOT/'config.json').read_text(encoding='utf-8-sig')))
    acc=api.call('account/config')[0]
    pos_side, errors = account_status(acc)
    if errors:
        raise SystemExit('；'.join(errors))
    if args.check:
        print('帳戶模式檢查通過，唯讀檢查完成。',flush=True)
        return
    # An exclusive SQLite transaction on a separate file prevents simultaneous local runners.
    lock=sqlite3.connect(ROOT/'fib_v3_live.lock.sqlite',timeout=0)
    lock.execute('BEGIN EXCLUSIVE')
    db=sqlite3.connect(ROOT/'fib_v3_live.sqlite')
    mgr=Manager(api,db,pos_side,shared=acc["uid"]==acc["mainUid"])
    uid=acc['uid']
    bound=db.execute('select uid from binding').fetchone()
    if bound and uid!=bound[0]:
        raise SystemExit('狀態檔屬於其他帳戶')
    mgr.record('insert or ignore into binding values(?)',(uid,))
    log(f'策略參數｜BTC 過濾={BTC_FILTER}')
    log('候選排序｜進場越深優先（取前 %d 筆）' % MAX_OPEN_TRADES)
    log('進場層級｜Fib %s｜Swing 視窗 %d 根（%d 小時）｜TP %s%% / SL %s%%｜RSI %s～%s'
        % (fmt(ENTRY_LEVEL), LOOKBACK_BARS, LOOKBACK_BARS*4, fmt(TP_PCT*100), fmt(SL_PCT*100), fmt(RSI_LO), fmt(RSI_HI)))
    log('掛單時效｜%.1f 小時未成交自動撤單並釋放名額' % ORDER_TTL_HOURS)
    log('連續虧損｜%s' % (f'連虧 {LOSS_STREAK_LIMIT} 筆暫停 {LOSS_STREAK_PAUSE_HOURS:g} 小時'
                          if LOSS_STREAK_LIMIT > 0 else '停用'))
    log('Telegram 通知｜%s' % ('已啟用' if TG_ENABLED else '未設定（TG_TOKEN / TG_CHAT）'))
    log('掃描節奏｜%s｜進場時窗=%d 分鐘'
        % ('每 %g 分鐘定時掃描' % _scan_interval_min if SCAN_INTERVAL_MS else '僅 4H 收盤後掃描',
           int(ENTRY_WINDOW_MS//60_000)))
    log('風控｜每筆風險=%sU｜同時上限=%d 筆｜總風險上限=%sU｜總名義上限=%sU｜'
        '單日虧損上限=%sU｜單日新增上限=%d 筆'
        % (fmt(RISK_PER_TRADE), MAX_OPEN_TRADES, fmt(MAX_TOTAL_RISK),
           fmt(MAX_TOTAL_NOTIONAL), fmt(DAILY_LOSS_LIMIT), MAX_NEW_ENTRIES_PER_DAY))
    log('帳戶檢查通過，開始核對持倉與掛單。核對成功後立即掃描當前 4H。')
    events=queue.Queue()
    scanner_started = False
    while True:
        try:
            mgr.sync()
            if not scanner_started:
                threading.Thread(target=scanner,args=(api,events),daemon=True).start()
                scanner_started = True
            # 一次把佇列排空。原本每 2 秒只處理 1 筆，54 個候選要 108 秒，
            # 常常還沒處理完就超過進場時窗，導致「有候選卻沒掛單」。
            budget = 20          # 單輪最多處理筆數，避免長時間卡住 watchdog
            handled = 0
            while handled < budget:
                try:
                    args=events.get_nowait()
                except queue.Empty:
                    break
                if not args:
                    continue
                if not (mgr.shared or not mgr.blocked):
                    break
                try:
                    mgr.enter(*args)
                except Exception as e:
                    log('送單失敗，續處理下一筆', e)
                handled += 1
        except Exception as e:
            log('本輪暫停送單，重新核對',e)
        time.sleep(2)


if __name__=='__main__':
    try:
        main()
    except (Exception, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code in (None, 0):
            raise
        print('啟動或執行失敗：', exc, file=sys.stderr, flush=True)
        if len(sys.argv) == 1 and sys.stdin and sys.stdin.isatty():
            input('按 Enter 離開：')
        raise SystemExit(1)
