# ============================================================
# 👑 KOHLI HOSTING + PREDICTION BOT — PROFESSIONAL v8.1
# ============================================================
# 🔒 BLOCKING DEPLOY — Bot live hone ke baad hi response
# ⚔️ Dragon Track | 🤖 Adaptive Quant | 🔑 Seed Hash Decrypter
# 🚀 Railway Ready — Fixed Python 3.11.10 build
# ============================================================

import asyncio
import json
import random
import os
import math
import hashlib
import time
import threading
import traceback
from datetime import datetime

import httpx
import pytz
from flask import Flask, request, jsonify

from telebot.async_telebot import AsyncTeleBot
from telebot import types, util
from telebot.apihelper import ApiTelegramException


# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────

HOST_BOT_TOKEN = "8372270378:AAEXNRXUD2xTwShxB7z7WR5uqX2NrWBvN6o"
ADMIN_ID = 7741897793

FIREBASE_URL = "https://glowbet-1b2ce-default-rtdb.firebaseio.com"
HISTORY_API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

DATA_DIR = os.environ.get("DATA_DIR", "kohli_data")
os.makedirs(DATA_DIR, exist_ok=True)

REGISTRY_FILE = os.path.join(DATA_DIR, "hosted_registry.json")
DATA_FILE = os.path.join(DATA_DIR, "bot_data.json")

REQUEST_TIMEOUT = 60
MAX_RETRIES = 5
RETRY_DELAY = 2

STICKER_START = "CAACAgUAAxkBAAFLuItqJPtZCBFQfGfRsJKl6boNvqKixQACuRMAAtgMEVayBm8tXDvNpDsE"
STICKER_WIN_LIST = [
    "CAACAgUAAxkBAAFLuI1qJPt6xyJZrPgYtmOdxJ2YMa6gFwACJxQAAhs_UVXBa4-Se7IejzsE",
    "CAACAgUAAxkBAAFL6I1qJ38O9fE3RKMdUU0R1iQpapxH8AACBxwAAqlQ2FYgxhZ0x6m0ojsE",
]
STICKER_STOP = "CAACAgUAAxkBAAFLuJFqJPuZKYQt4bz30u_39DM-JwW4agAClBEAAo-CGFb2yvdmMKOx1jsE"

DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━"
SUB_DIVIDER = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
LIGHTNING_STR = "⚡ KOHLI PREMIUM ENGINE ⚡"


# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────

bot = AsyncTeleBot(HOST_BOT_TOKEN)
bot.request_timeout = REQUEST_TIMEOUT

active_sessions = {}
hosted_bots = {}
hosted_by_id = {}
hosted_registry = {}

_async_loop = None
_loop_thread = None
_loop_ready = threading.Event()


# ──────────────────────────────────────────────────────────────────────────────
# DEDICATED ASYNC LOOP
# ──────────────────────────────────────────────────────────────────────────────

def _start_async_loop():
    global _async_loop
    _async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_async_loop)
    _loop_ready.set()
    _async_loop.run_forever()


def ensure_loop():
    global _loop_thread
    if _loop_thread is None or not _loop_thread.is_alive():
        _loop_ready.clear()
        _loop_thread = threading.Thread(target=_start_async_loop, daemon=True)
        _loop_thread.start()
        _loop_ready.wait(timeout=10)
    return _async_loop


def run_async_blocking(coro, timeout=60):
    """Run coroutine on background loop and WAIT for result."""
    loop = ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=timeout)


def schedule_async(coro):
    """Fire and forget."""
    loop = ensure_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop)


# ──────────────────────────────────────────────────────────────────────────────
# REGISTRY
# ──────────────────────────────────────────────────────────────────────────────

def load_registry():
    global hosted_registry
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                hosted_registry = json.load(f)
            print(f"[REGISTRY] Loaded {len(hosted_registry)} entries")
        except Exception as e:
            print(f"[REGISTRY] Load failed: {e}")
            hosted_registry = {}


def save_registry():
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(hosted_registry, f, indent=2, default=str)
    except Exception as e:
        print(f"[REGISTRY] Save failed: {e}")


def register_bot(hosted_id, owner_id, username, bot_id, token):
    hosted_registry[hosted_id] = {
        "owner_id": str(owner_id) if owner_id else "",
        "username": username,
        "bot_id": str(bot_id),
        "token": token,
        "created_at": datetime.now().isoformat(),
    }
    save_registry()


def update_registry_owner(hosted_id, owner_id):
    if hosted_id in hosted_registry:
        hosted_registry[hosted_id]["owner_id"] = str(owner_id)
        save_registry()


def unregister_bot(hosted_id):
    if hosted_id in hosted_registry:
        del hosted_registry[hosted_id]
        save_registry()


# ──────────────────────────────────────────────────────────────────────────────
# HTTP
# ──────────────────────────────────────────────────────────────────────────────

_http_client = None


async def get_http():
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=15.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _http_client


async def close_http():
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
    _http_client = None


# ──────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ──────────────────────────────────────────────────────────────────────────────

def now_str():
    return datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")


def _confidence_bar(pct):
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)


def generate_seed_hash_analysis(period: str):
    salt = "GLOWBET_SECURE_WIN_SEED_KEY_2026"
    hash_hex = hashlib.sha256(f"{period}_{salt}".encode('utf-8')).hexdigest()
    number = int(hash_hex[:8], 16) % 10
    prediction = "BIG" if number >= 5 else "SMALL"
    is_jackpot = (number in [0, 5])
    numeric_count = sum(1 for c in hash_hex if c.isdigit())
    confidence = 80 + (numeric_count % 16)
    return prediction, number, is_jackpot, hash_hex, confidence


def make_prediction_text(period, prediction, level, server, confidence=None,
                          signal_strength=None, jackpot=False, hash_val=None):
    bet_line = "😈𝐁ᴇᴛ ➪ 🔵𝐒ᴍᴀʟʟ ☠️" if prediction == "SMALL" else "😈𝐁ᴇᴛ ➪ 🔴𝐁ɪɢ 👑"

    conf_line = ""
    if confidence is not None:
        conf_line = f"\n📊 𝐂ᴏɴꜰɪᴅᴇɴᴄᴇ: {confidence}% {_confidence_bar(confidence)}"

    jackpot_line = "\n🚨 𝐉𝐀𝐂𝐊𝐏𝐎𝐓: 💜 𝐕ɪᴏʟᴇᴛ (0/5)!" if jackpot else ""

    hash_line = ""
    if hash_val:
        hash_line = f"\n🔑 𝐇ᴀsʜ: <code>{hash_val[:12]}...{hash_val[-12:]}</code>\n🔐 𝐒ᴇᴇᴅ: 𝐕ᴇʀɪꜰɪᴇᴅ"

    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"
    return (
        f"{sep}\n🏅𝐖ɪɴɢᴏ 1 𝐌ɪɴᴜᴛᴇ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ👻\n{sep}\n"
        f"💀𝐏ᴇʀɪᴏᴅ ❤️‍🔥 <code>{period}</code>\n"
        f"{bet_line}{conf_line}{jackpot_line}{hash_line}\n{sep}"
    )


def make_win_text(wins, losses):
    total = wins + losses
    win_rate = round(wins / total * 100) if total > 0 else 0
    stars = "⭐" * min(5, max(1, win_rate // 20))
    return f"✅ <b>𝐖ɪɴ!</b> {stars}\n🏆 𝐖ɪɴs: {wins} │ ❌ 𝐋ᴏss: {losses} │ 📈 {win_rate}%"


def build_session_summary(session, reason):
    wins = session.get('wins', 0)
    losses = session.get('losses', 0)
    total = wins + losses
    rate = round(wins / total * 100) if total > 0 else 0
    server = session.get('server', '1')
    recent = session.get('recent_results', [])
    started = session.get('started_at', '—')
    ended_at = now_str()
    max_streak = session.get('max_win_streak', 0)

    server_name = {"1": "⚔️ Dragon Track", "2": "🤖 Adaptive Quant",
                   "3": "🔑 Seed Hash"}.get(server, server)

    if recent:
        recent_visual = "".join("✅" if r == 1 else "❌" for r in recent[-10:])
        recent_rate = round(sum(recent[-10:]) / len(recent[-10:]) * 100)
    else:
        recent_visual = "❌" * 10
        recent_rate = 0

    status_line = "✅ Completed" if "COMPLETED" in reason else (
        "🛑 Stopped" if "STOPPED" in reason else f"⚠️ {reason}")

    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"
    return (
        f"{sep}\n☑️ 𝐊ᴏʜʟɪ 𝐀ᴜᴛᴏ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ ⚠️\n{sep}\n\n"
        f"🖥 {server_name}\n🕐 <code>{started}</code>\n🕑 <code>{ended_at}</code>\n\n"
        f"🎯 Rounds: {total}\n{sep}\n\n"
        f" ✅ Wins: {wins}\n ❌ Loss: {losses}\n"
        f" 🏆 Streak: {max_streak}\n 📈 Accuracy: {rate}%\n\n"
        f"{recent_visual} {recent_rate}%\n\n"
        f"📌 Status: {status_line}\n\n{sep}\n🚀 KOHLI ENGINE"
    )


# ──────────────────────────────────────────────────────────────────────────────
# PERSISTENCE
# ──────────────────────────────────────────────────────────────────────────────

_data_cache = None


async def load_data():
    global _data_cache
    if _data_cache is not None:
        return _data_cache

    empty = {"users": {}, "sessions": {}}

    if FIREBASE_URL:
        for attempt in range(3):
            try:
                r = await (await get_http()).get(f"{FIREBASE_URL.rstrip('/')}/bot_data.json")
                if r.status_code == 200:
                    d = r.json()
                    if d and isinstance(d, dict):
                        d.setdefault("users", {})
                        d.setdefault("sessions", {})
                        _data_cache = d
                        return _data_cache
            except Exception:
                if attempt < 2:
                    await asyncio.sleep(RETRY_DELAY)

    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                if d and isinstance(d, dict):
                    d.setdefault("users", {})
                    d.setdefault("sessions", {})
                    _data_cache = d
                    return _data_cache
    except Exception:
        pass

    _data_cache = empty
    return _data_cache


async def save_data(data):
    global _data_cache
    _data_cache = data
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception:
        pass
    if FIREBASE_URL:
        try:
            await (await get_http()).put(
                f"{FIREBASE_URL.rstrip('/')}/bot_data.json", json=data)
        except Exception:
            pass


async def add_channel(user_id, channel_link, channel_id, auto_detected=False):
    data = await load_data()
    uid = str(user_id)
    data['users'].setdefault(uid, {'channels': [], 'settings': {},
                                    'total_wins': 0, 'total_losses': 0})
    for ch in data['users'][uid]['channels']:
        if str(ch['channel_id']) == str(channel_id):
            return False
    data['users'][uid]['channels'].append({
        'channel_link': channel_link, 'channel_id': str(channel_id),
        'added_date': datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        'auto_detected': auto_detected,
        'total_sessions': 0, 'total_wins': 0, 'total_losses': 0,
    })
    await save_data(data)
    return True


async def remove_channel(user_id, channel_id):
    data = await load_data()
    uid = str(user_id)
    if uid not in data['users']:
        return False
    before = len(data['users'][uid]['channels'])
    data['users'][uid]['channels'] = [
        c for c in data['users'][uid]['channels']
        if str(c['channel_id']) != str(channel_id)
    ]
    if len(data['users'][uid]['channels']) < before:
        await save_data(data)
        return True
    return False


async def update_stats(user_id, channel_id, wins, losses):
    data = await load_data()
    uid = str(user_id)
    for ch in data.get('users', {}).get(uid, {}).get('channels', []):
        if str(ch['channel_id']) == str(channel_id):
            ch['total_sessions'] = ch.get('total_sessions', 0) + 1
            ch['total_wins'] = ch.get('total_wins', 0) + wins
            ch['total_losses'] = ch.get('total_losses', 0) + losses
            break
    await save_data(data)


async def get_channels(user_id):
    data = await load_data()
    return data.get('users', {}).get(str(user_id), {}).get('channels', [])


async def save_session_db(user_id, session_data):
    data = await load_data()
    clean = {k: v for k, v in session_data.items() if k != 'task'}
    data['sessions'][str(user_id)] = clean
    await save_data(data)


async def delete_session_db(user_id):
    data = await load_data()
    if str(user_id) in data.get('sessions', {}):
        del data['sessions'][str(user_id)]
        await save_data(data)


async def get_all_users():
    data = await load_data()
    return data.get('users', {})


# ──────────────────────────────────────────────────────────────────────────────
# HISTORY
# ──────────────────────────────────────────────────────────────────────────────

async def fetch_history():
    for attempt in range(MAX_RETRIES):
        try:
            await asyncio.sleep(0.3)
            r = await (await get_http()).get(HISTORY_API)
            if r.status_code == 200:
                j = r.json()
                records = (j.get('data', {}).get('list', []) or
                           j.get('data', []) or j.get('list', []) or [])
                if records:
                    return records
        except Exception:
            await asyncio.sleep(RETRY_DELAY)
    return []


def _issue(rec):
    for k in ('issueNumber', 'issue', 'period', 'periodNumber', 'no', 'id'):
        v = rec.get(k)
        if v is not None:
            return str(v).strip()
    return ""


def _number(rec):
    for k in ('number', 'openCode', 'result', 'num', 'value'):
        v = rec.get(k)
        if v is not None:
            try:
                return int(str(v).strip())
            except Exception:
                continue
    return 5


async def next_period():
    records = await fetch_history()
    if records:
        try:
            return str(int(_issue(records[0])) + 1)
        except Exception:
            pass
    now = datetime.now()
    return now.strftime("%Y%m%d") + str(now.hour * 60 + now.minute).zfill(4)


async def wait_for_result(period_str):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 150
    while loop.time() < deadline:
        records = await fetch_history()
        for r in records:
            if _issue(r) == period_str.strip():
                num = _number(r)
                return ('BIG' if num >= 5 else 'SMALL'), num
        await asyncio.sleep(3)
    return None, None


# ──────────────────────────────────────────────────────────────────────────────
# SAFE SEND
# ──────────────────────────────────────────────────────────────────────────────

async def safe_send(bot_obj, target, text, reply_markup=None, parse_mode="HTML"):
    for attempt in range(MAX_RETRIES):
        try:
            await asyncio.sleep(0.3)
            return await bot_obj.send_message(target, text, parse_mode=parse_mode,
                                               reply_markup=reply_markup)
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = e.result.get('parameters', {}).get('retry_after', 5)
                await asyncio.sleep(retry_after + 1)
            elif e.error_code in [403, 400]:
                return None
            else:
                await asyncio.sleep(1)
        except Exception:
            await asyncio.sleep(1)
    return None


async def safe_edit(bot_obj, msg, text, reply_markup=None):
    try:
        await asyncio.sleep(0.2)
        await bot_obj.edit_message_text(
            chat_id=msg.chat.id, message_id=msg.message_id,
            text=text, parse_mode='HTML', reply_markup=reply_markup)
    except Exception:
        pass


async def send_sticker(bot_obj, target, sticker_id):
    try:
        await asyncio.sleep(0.3)
        await bot_obj.send_sticker(target, sticker_id)
    except Exception:
        pass


async def send_win_sticker(bot_obj, target):
    await send_sticker(bot_obj, target, random.choice(STICKER_WIN_LIST))


# ──────────────────────────────────────────────────────────────────────────────
# PREDICTION ALGORITHMS
# ──────────────────────────────────────────────────────────────────────────────

def extract_outcomes(records, n=300):
    outcomes = []
    for r in records[:n]:
        try:
            outcomes.append('BIG' if _number(r) >= 5 else 'SMALL')
        except Exception:
            continue
    return outcomes


def extract_raw_numbers(records, n=50):
    nums = []
    for r in records[:n]:
        try:
            nums.append(_number(r))
        except Exception:
            continue
    return nums


def _mean(seq):
    return sum(seq) / len(seq) if seq else 0.0


def _big_rate(seq):
    return seq.count('BIG') / len(seq) if seq else 0.5


def _zscore(seq):
    n = len(seq)
    if n == 0:
        return 0.0
    p = seq.count('BIG') / n
    std_err = math.sqrt(0.25 / n)
    return (p - 0.5) / std_err if std_err > 0 else 0.0


def _weighted_big_rate(seq, decay=0.93):
    if not seq:
        return 0.5
    total_w = big_w = 0.0
    for i, x in enumerate(seq):
        w = decay ** i
        big_w += w * (1 if x == 'BIG' else 0)
        total_w += w
    return big_w / total_w if total_w > 0 else 0.5


def _shannon_entropy(seq):
    if len(seq) < 2:
        return 0.0
    p = _big_rate(seq)
    if p in (0.0, 1.0):
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def _autocorrelation(seq, lag=1):
    bits = [1 if x == 'BIG' else 0 for x in seq]
    if len(bits) <= lag:
        return 0.0
    m = _mean(bits)
    num = sum((bits[i] - m) * (bits[i + lag] - m) for i in range(len(bits) - lag))
    den = sum((x - m) ** 2 for x in bits)
    return num / den if den != 0 else 0.0


def _run_length_encode(seq):
    if not seq:
        return []
    runs, cur, cnt = [], seq[0], 1
    for x in seq[1:]:
        if x == cur:
            cnt += 1
        else:
            runs.append((cur, cnt))
            cur, cnt = x, 1
    runs.append((cur, cnt))
    return runs


def _streak_info(seq):
    if not seq:
        return 'BIG', 0, 0, 1.0
    runs = _run_length_encode(seq)
    cur_val, cur_len = runs[0]
    max_streak = max(r[1] for r in runs)
    avg_run = len(seq) / len(runs) if runs else 1.0
    return cur_val, cur_len, max_streak, avg_run


def _streak_exhaustion_score(seq):
    val, cur_len, max_s, avg_run = _streak_info(seq)
    if avg_run == 0:
        return 0.0
    return min(1.0, cur_len / max(avg_run * 1.6, 2))


def _alternation_rate(seq):
    if len(seq) < 2:
        return 0.5
    flips = sum(1 for i in range(len(seq) - 1) if seq[i] != seq[i + 1])
    return flips / (len(seq) - 1)


def _transition_matrix(seq):
    if len(seq) < 2:
        return {'BB': 0.5, 'BS': 0.5, 'SB': 0.5, 'SS': 0.5}
    counts = {'BB': 0, 'BS': 0, 'SB': 0, 'SS': 0}
    for i in range(len(seq) - 1):
        k = ('B' if seq[i] == 'BIG' else 'S') + ('B' if seq[i + 1] == 'BIG' else 'S')
        counts[k] += 1
    tB = counts['BB'] + counts['BS']
    tS = counts['SB'] + counts['SS']
    return {
        'BB': counts['BB'] / tB if tB > 0 else 0.5,
        'BS': counts['BS'] / tB if tB > 0 else 0.5,
        'SB': counts['SB'] / tS if tS > 0 else 0.5,
        'SS': counts['SS'] / tS if tS > 0 else 0.5,
    }


def _higher_order_transition(seq, order=2):
    if len(seq) < order + 3:
        return None, 0.5
    context = tuple(seq[:order])
    counts = {'BIG': 0, 'SMALL': 0}
    for i in range(order, len(seq)):
        if tuple(seq[i - order:i]) == context:
            counts[seq[i]] += 1
    total = counts['BIG'] + counts['SMALL']
    if total < 3:
        return None, 0.5
    pred = max(counts, key=counts.get)
    prob = counts[pred] / total
    return (pred, prob) if prob >= 0.58 else (None, 0.5)


def _detect_cycle(seq, max_lag=24):
    if len(seq) < max_lag * 2:
        return None, 0.0
    best_period, best_strength = None, 0.0
    for lag in range(2, min(max_lag, len(seq) // 2)):
        acf = _autocorrelation(seq, lag)
        if abs(acf) > best_strength and abs(acf) > 0.22:
            best_strength = abs(acf)
            best_period = lag
    return (best_period, best_strength) if best_period else (None, 0.0)


def _repeating_block_cycle(seq, min_len=2, max_len=8):
    best_score, best_cycle = 0.0, None
    n = len(seq)
    for clen in range(min_len, min(max_len + 1, n // 2)):
        cycle = seq[:clen]
        matches = checks = 0
        for i in range(clen, min(n, clen * 10)):
            if seq[i] == cycle[i % clen]:
                matches += 1
            checks += 1
        if checks == 0:
            continue
        score = matches / checks
        adjusted = score * (1 + 0.04 * clen)
        if adjusted > best_score and score >= 0.68:
            best_score = score
            best_cycle = cycle
    return best_cycle, best_score


def _ngram_predict(seq, n):
    if len(seq) < n + 3:
        return None, 0.0
    context = tuple(seq[:n - 1])
    counts = {'BIG': 0, 'SMALL': 0}
    for i in range(n - 1, len(seq)):
        if tuple(seq[i - (n - 1):i]) == context:
            counts[seq[i]] += 1
    total = counts['BIG'] + counts['SMALL']
    if total < 3:
        return None, 0.0
    winner = max(counts, key=counts.get)
    rate = counts[winner] / total
    return (winner, rate) if rate >= 0.60 else (None, 0.0)


def _historical_similarity(seq, lookback=8):
    if len(seq) < lookback * 2 + 2:
        return {'BIG': 0.5, 'SMALL': 0.5}, 0.0
    target = seq[:lookback]
    follow_counts = {'BIG': 0, 'SMALL': 0}
    for i in range(lookback, len(seq) - 1):
        if seq[i:i + lookback] == target:
            follow_counts[seq[i - 1]] += 1
    total = follow_counts['BIG'] + follow_counts['SMALL']
    if total < 2:
        return {'BIG': 0.5, 'SMALL': 0.5}, 0.0
    conf = min(0.90, total / 15.0)
    pb = follow_counts['BIG'] / total
    return {'BIG': pb, 'SMALL': 1 - pb}, conf


def _anomaly_score(seq, window=20):
    if len(seq) < window:
        return 0.0
    recent = seq[:window]
    freq_dev = abs(_big_rate(recent) - 0.5)
    n = len(recent)
    runs = 1 + sum(1 for i in range(1, n) if recent[i] != recent[i - 1])
    expected_runs = 1 + 2 * n * 0.5 * 0.5
    denom = math.sqrt(2 * n * 0.25 * (2 * n * 0.25 - n - 1) / (n - 1)) if n > 2 else 1
    runs_z = abs(runs - expected_runs) / denom if denom > 0 else 0.0
    return min(1.0, freq_dev * 2 + min(1.0, runs_z / 3.0))


def _cluster_exhaustion(seq, min_cluster=3):
    if len(seq) < min_cluster:
        return None, 0.0
    runs = _run_length_encode(seq)
    front_val, front_len = runs[0]
    if front_len < min_cluster:
        return None, 0.0
    _, _, max_s, avg_run = _streak_info(seq)
    exhaustion = min(1.0, (front_len - min_cluster + 1) / max(avg_run, 2))
    return front_val, exhaustion


def _momentum_shift(seq, window=5):
    if len(seq) < window * 2:
        return 0.0
    return _big_rate(seq[:window]) - _big_rate(seq[window:window * 2])


def _frequency_drift(seq, recent_w=15, baseline_w=60):
    if len(seq) < baseline_w:
        return 'BIG', 0.0
    drift = _big_rate(seq[:recent_w]) - _big_rate(seq[recent_w:baseline_w])
    return ('BIG' if drift > 0 else 'SMALL'), min(1.0, abs(drift) * 2)


def _fibonacci_window_votes(seq):
    fibs = [3, 5, 8, 13, 21, 34, 55, 89, 144]
    votes = {'BIG': 0.0, 'SMALL': 0.0}
    n = len(seq)
    for w in fibs:
        if n < w:
            continue
        br = _big_rate(seq[:w])
        bias = br - 0.5
        weight = 1.0 / math.log2(w + 1)
        if bias > 0.10:
            votes['SMALL'] += weight * abs(bias)
        elif bias < -0.10:
            votes['BIG'] += weight * abs(bias)
        elif abs(bias) < 0.04:
            votes['BIG' if br >= 0.5 else 'SMALL'] += weight * 0.15
    return votes


class _SignalBoard:
    def __init__(self):
        self.votes = {'BIG': 0.0, 'SMALL': 0.0}
        self._signals = []

    def add(self, name, direction, weight):
        if direction not in ('BIG', 'SMALL') or weight <= 0:
            return
        self.votes[direction] += weight
        self._signals.append((name, direction, weight))

    def leading(self):
        return 'BIG' if self.votes['BIG'] >= self.votes['SMALL'] else 'SMALL'

    def edge_ratio(self):
        total = self.votes['BIG'] + self.votes['SMALL']
        return max(self.votes.values()) / total if total > 0 else 0.5

    def contradictions(self):
        leader = self.leading()
        return sum(1 for _, d, _ in self._signals if d != leader)

    def confidence_pct(self):
        edge = self.edge_ratio()
        return max(50, min(92, round(50 + (edge - 0.5) * 90)))

    def top_factors(self, n=4):
        return [s[0] for s in sorted(self._signals, key=lambda x: x[2], reverse=True)[:n]]


def _validate_prediction(seq, prediction):
    test_windows = [15, 30, 60, 100]
    passes = total = 0
    for w in test_windows:
        if len(seq) < w:
            continue
        z = _zscore(seq[:w])
        if prediction == 'BIG' and z >= 0:
            passes += 1
        elif prediction == 'SMALL' and z <= 0:
            passes += 1
        total += 1
    agree = passes / total if total > 0 else 0.5
    return passes, total, agree


def _quant_core_predict(outcomes: list):
    n = len(outcomes)
    if n < 6:
        return 'BIG', 50, 'INSUFFICIENT', {}

    board = _SignalBoard()

    def _html_dragon_line(hist):
        if len(hist) < 2:
            return None
        ct = hist[0]
        s = 1
        for i in range(1, len(hist)):
            if hist[i] == ct:
                s += 1
            else:
                break
        return ct if 2 <= s <= 8 else None

    def _html_chop_chop(hist):
        if len(hist) < 4:
            return None
        if (hist[0] != hist[1] and hist[1] == hist[2] and hist[2] != hist[3]):
            return 'SMALL' if hist[0] == 'BIG' else 'BIG'
        return None

    def _html_density(hist, sample_size=6):
        n2 = min(sample_size, len(hist))
        if n2 < 3:
            return None
        sample = hist[:n2]
        bc = sample.count('BIG')
        if bc > n2 / 2:
            return 'SMALL'
        elif bc < n2 / 2:
            return 'BIG'
        return None

    dragon = _html_dragon_line(outcomes)
    if dragon:
        _, slen, _, _ = _streak_info(outcomes)
        board.add("HTML-DragonLine", dragon, 1.5 + slen * 0.3)

    chop = _html_chop_chop(outcomes)
    if chop:
        board.add("HTML-ChopChop", chop, 2.2)

    density = _html_density(outcomes, 6)
    if density:
        board.add("HTML-Density", density, 1.8)

    st_z = _zscore(outcomes[:min(10, n)])
    if abs(st_z) >= 0.4:
        board.add("ST-ZScore-Fade", 'SMALL' if st_z > 0 else 'BIG', min(3.0, abs(st_z) * 1.2))

    streak_val, streak_len, max_s, avg_run = _streak_info(outcomes)
    exhaust = _streak_exhaustion_score(outcomes)
    if streak_len >= 3:
        flip = 'SMALL' if streak_val == 'BIG' else 'BIG'
        board.add("StreakExhaustion", flip, 1.5 + exhaust * 4.5)

    tm = _transition_matrix(outcomes)
    last = outcomes[0]
    p_big_next = tm['BB'] if last == 'BIG' else tm['SB']
    p_sml_next = tm['BS'] if last == 'BIG' else tm['SS']
    if abs(p_big_next - 0.5) >= 0.08:
        board.add("Markov1", 'BIG' if p_big_next > p_sml_next else 'SMALL',
                  abs(p_big_next - 0.5) * 8)

    for order in (2, 3):
        ho_pred, ho_prob = _higher_order_transition(outcomes, order)
        if ho_pred is not None:
            board.add(f"Markov{order}", ho_pred, (ho_prob - 0.5) * (6 + order))

    for gram_n in (3, 4, 5):
        gp, grate = _ngram_predict(outcomes, gram_n)
        if gp is not None:
            board.add(f"{gram_n}Gram", gp, (grate - 0.5) * (gram_n * 2.5))

    fib_votes = _fibonacci_window_votes(outcomes)
    for side in ('BIG', 'SMALL'):
        if fib_votes[side] > 0.06:
            board.add("FibWindows", side, fib_votes[side] * 3.5)

    cycle_block, block_score = _repeating_block_cycle(outcomes, 2, 8)
    if cycle_block is not None and block_score >= 0.70:
        pos = n % len(cycle_block)
        board.add("BlockCycle", cycle_block[pos % len(cycle_block)], block_score * 4.5)

    cyc_period, cyc_strength = _detect_cycle(outcomes, 24)
    if cyc_period is not None and cyc_strength >= 0.22:
        phase = n % cyc_period
        if phase < len(outcomes):
            board.add("AutoCorrCycle", outcomes[phase], cyc_strength * 3.0)

    anom = _anomaly_score(outcomes, 20)
    if anom >= 0.65:
        board.add("AnomalyReversion",
                  'SMALL' if _big_rate(outcomes[:10]) > 0.5 else 'BIG', anom * 3.0)

    cluster_val, cluster_ex = _cluster_exhaustion(outcomes, 3)
    if cluster_val is not None:
        board.add("ClusterExhaustion",
                  'SMALL' if cluster_val == 'BIG' else 'BIG', cluster_ex * 3.5)

    sim_probs, sim_conf = _historical_similarity(outcomes, 7)
    if sim_conf >= 0.30:
        board.add("HistSimilarity",
                  'BIG' if sim_probs['BIG'] > sim_probs['SMALL'] else 'SMALL',
                  sim_conf * 4.0 * abs(sim_probs['BIG'] - 0.5) * 2)

    w_drift = _weighted_big_rate(outcomes[:25], 0.91) - 0.5
    if abs(w_drift) >= 0.09:
        board.add("WeightedRecencyFade", 'SMALL' if w_drift > 0 else 'BIG',
                  abs(w_drift) * 4.0)

    mom = _momentum_shift(outcomes, 5)
    if abs(mom) >= 0.20:
        board.add("MomentumCont", 'BIG' if mom > 0 else 'SMALL', abs(mom) * 2.5)

    ent = _shannon_entropy(outcomes[:20])
    if ent < 0.80:
        board.add("LowEntropyBoost", board.leading(), (0.80 - ent) * 3.5)

    drift_dir, drift_mag = _frequency_drift(outcomes)
    if drift_mag >= 0.15:
        board.add("FreqDriftFade", 'SMALL' if drift_dir == 'BIG' else 'BIG',
                  drift_mag * 3.0)

    if board.contradictions() >= 5 and board.edge_ratio() < 0.57:
        board.add("ConflictPenalty",
                  'SMALL' if board.leading() == 'BIG' else 'BIG', 1.8)

    alt_rate = _alternation_rate(outcomes[:12])
    if alt_rate > 0.72:
        board.votes['BIG'] *= 0.75
        board.votes['SMALL'] *= 0.75

    prediction = board.leading()
    passes, total_tests, agree_ratio = _validate_prediction(outcomes, prediction)
    if agree_ratio < 0.40 and total_tests >= 3:
        prediction = 'SMALL' if prediction == 'BIG' else 'BIG'
        board.add("ValidationFlip", prediction, 2.5)
        prediction = board.leading()

    for sub_offset in (0, 8, 16):
        sub = outcomes[sub_offset:sub_offset + 30]
        if len(sub) >= 10:
            sub_val, sub_len, _, sub_avg = _streak_info(sub)
            sub_ex = min(1.0, sub_len / max(sub_avg * 1.5, 2))
            sub_flip = 'SMALL' if sub_val == 'BIG' else 'BIG'
            if sub_flip == prediction and sub_ex > 0.45:
                board.add("SubWinConfirm", prediction, 0.8)

    prediction = board.leading()
    confidence = board.confidence_pct()
    edge_final = board.edge_ratio()

    if edge_final >= 0.72:
        sig = "⚡ EXTREME"
    elif edge_final >= 0.65:
        sig = "🔥 STRONG"
    elif edge_final >= 0.59:
        sig = "✅ MODERATE"
    elif edge_final >= 0.54:
        sig = "⚠️ WEAK"
    else:
        sig = "❓ MINIMAL"

    meta = {
        'edge': edge_final, 'entropy': ent,
        'streak': (streak_val, streak_len),
        'top_factors': board.top_factors(4),
    }
    return prediction, confidence, sig, meta


def server1_dragon_predict(outcomes, raw_nums, level, session):
    if len(outcomes) < 3:
        return 'BIG', 60, "INSUFFICIENT"

    def _html_dragon_line(hist):
        if len(hist) < 2:
            return None
        ct = hist[0]
        s = 1
        for i in range(1, len(hist)):
            if hist[i] == ct:
                s += 1
            else:
                break
        return ct if 2 <= s <= 8 else None

    def _html_chop_chop(hist):
        if len(hist) < 4:
            return None
        if (hist[0] != hist[1] and hist[1] == hist[2] and hist[2] != hist[3]):
            return 'SMALL' if hist[0] == 'BIG' else 'BIG'
        return None

    def _html_density(hist, sample_size=6):
        n2 = min(sample_size, len(hist))
        if n2 < 3:
            return None
        sample = hist[:n2]
        bc = sample.count('BIG')
        if bc > n2 / 2:
            return 'SMALL'
        elif bc < n2 / 2:
            return 'BIG'
        return None

    hist = outcomes
    pred = _html_dragon_line(hist)
    stage_used = "DragonLine"
    if pred is None:
        pred = _html_chop_chop(hist)
        stage_used = "ChopChop"
    if pred is None:
        pred = _html_density(hist)
        stage_used = "Density"
    if pred is None:
        pred = hist[0] if hist else 'BIG'
        stage_used = "RecencyFallback"

    streak = 1
    for i in range(1, min(10, len(hist))):
        if hist[i] == hist[0]:
            streak += 1
        else:
            break

    if stage_used == "DragonLine":
        base_conf = min(80, 58 + streak * 3)
    elif stage_used == "ChopChop":
        base_conf = 72
    elif stage_used == "Density":
        big_count = hist[:6].count('BIG') if len(hist) >= 6 else hist.count('BIG')
        base_conf = 60 + abs(big_count - 3) * 4
    else:
        base_conf = 58
    base_conf = max(54, min(82, base_conf))

    if level == 1:
        return pred, int(base_conf), f"L1/{stage_used}"

    votes = {'BIG': 0.0, 'SMALL': 0.0}
    votes[pred] += 2.0
    for size, w in [(6, 1.5), (10, 1.5), (20, 1.0)]:
        d = _html_density(hist, size) if len(hist) >= size else None
        if d:
            votes[d] += w

    if len(hist) >= 10:
        drift = hist[:5].count('BIG') / 5.0 - hist[:10].count('BIG') / 10.0
        if abs(drift) >= 0.20:
            votes['SMALL' if drift > 0 else 'BIG'] += 2.0

    if streak >= 4:
        votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 2.5
    elif streak >= 3:
        votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 1.5

    if len(hist) >= 20:
        bg = hist[:20].count('BIG')
        if bg >= 15:
            votes['SMALL'] += 2.0
        elif bg <= 5:
            votes['BIG'] += 2.0

    votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 1.0

    final_pred = 'BIG' if votes['BIG'] >= votes['SMALL'] else 'SMALL'
    total_v = votes['BIG'] + votes['SMALL']
    edge = votes[final_pred] / total_v if total_v > 0 else 0.5
    final_conf = min(88, max(60, int(50 + edge * 80)))
    return final_pred, final_conf, f"L2-ExtremeAnalysis/{stage_used}"


def server2_ultra_predict(outcomes, level, session):
    if len(outcomes) < 6:
        return 'BIG', 50, "INSUFFICIENT"

    if level == 1:
        probe_votes = {'BIG': 0.0, 'SMALL': 0.0}
        probe_confs = []
        for offset in range(4):
            if len(outcomes) <= offset + 8:
                continue
            p, c, _, _ = _quant_core_predict(outcomes[offset:])
            probe_votes[p] += 1.0 + (c - 50) / 50.0
            probe_confs.append(c)

        sv, sl, _, _ = _streak_info(outcomes)
        if sl >= 5:
            probe_votes['SMALL' if sv == 'BIG' else 'BIG'] += 2.5
        elif sl >= 4:
            probe_votes['SMALL' if sv == 'BIG' else 'BIG'] += 1.5
        elif sl >= 3:
            probe_votes['SMALL' if sv == 'BIG' else 'BIG'] += 0.8

        ensemble_pred = max(probe_votes, key=probe_votes.get)
        avg_conf = round(sum(probe_confs) / len(probe_confs)) if probe_confs else 65
        total_pv = sum(probe_votes.values())
        agree = probe_votes[ensemble_pred] / total_pv if total_pv > 0 else 0.5

        if agree >= 0.82:
            avg_conf = min(91, avg_conf + 9)
        elif agree >= 0.68:
            avg_conf = min(91, avg_conf + 5)
        elif agree < 0.54:
            avg_conf = max(52, avg_conf - 6)

        return ensemble_pred, avg_conf, f"Ensemble-Ultra(agree={agree:.0%})"

    board2 = _SignalBoard()
    sv, sl, _, _ = _streak_info(outcomes)
    flip = 'SMALL' if sv == 'BIG' else 'BIG'

    if sl >= 4:
        board2.add("L2-AntiStreak", flip, 4.0 + sl * 0.6)
    elif sl >= 3:
        board2.add("L2-AntiStreak", flip, 3.0)
    elif sl == 2:
        board2.add("L2-AntiStreak", flip, 1.8)
    else:
        board2.add("L2-AntiStreak", flip, 1.0)

    base, q_conf, q_sig, meta = _quant_core_predict(outcomes)
    board2.add("L2-QuantBase", base, 2.0)

    for win in [10, 20, 40]:
        if len(outcomes) >= win:
            br = _big_rate(outcomes[:win])
            if br >= 0.65:
                board2.add(f"L2-FreqBal{win}", 'SMALL', (br - 0.5) * 4)
            elif br <= 0.35:
                board2.add(f"L2-FreqBal{win}", 'BIG', (0.5 - br) * 4)

    l2_pred = board2.leading()
    l2_conf = min(90, max(56, board2.confidence_pct()))
    return l2_pred, l2_conf, f"L2-ExtremeScan/{q_sig}"


def adaptive_engine_predict(outcomes, raw_nums, session):
    consec_losses = session.get('consecutive_losses', 0)
    recent_res = session.get('recent_results', [])
    recent_win_rate = sum(recent_res[-5:]) / len(recent_res[-5:]) if recent_res else 1.0

    last_p = session.get('last_period', '0')
    try:
        next_p = str(int(last_p) + 1)
    except ValueError:
        next_p = last_p

    if consec_losses >= 1:
        pred, num, jackpot, h_hex, conf = generate_seed_hash_analysis(next_p)
        return pred, conf, "ADAPTIVE-RECOVERY", jackpot, h_hex

    if recent_win_rate < 0.40:
        pred, conf, sig, meta = _quant_core_predict(outcomes)
        flipped = "SMALL" if pred == "BIG" else "BIG"
        is_jackpot = len(raw_nums) >= 2 and raw_nums[0] in [0, 5, 1, 9]
        return flipped, max(55, conf - 5), "ADAPTIVE-COUNTER_TREND", is_jackpot, None

    pred, conf, sig, meta = _quant_core_predict(outcomes)
    is_jackpot = meta.get('streak', ('BIG', 0))[1] >= 4
    return pred, conf, f"ADAPTIVE-OPTIMAL ({sig})", is_jackpot, None


async def smart_predict(records, session):
    if not records:
        return 'BIG', 50, "NO_DATA", False, None

    outcomes = extract_outcomes(records, 300)
    raw_nums = extract_raw_numbers(records, 50)

    if len(outcomes) < 6:
        return 'BIG', 50, "INSUFFICIENT", False, None

    server = session.get('server', '1')
    level = session.get('current_level', 1)

    if server == '3':
        last_p = session.get('last_period', '0')
        try:
            next_p = str(int(last_p) + 1)
        except ValueError:
            next_p = last_p
        pred, num, jackpot, h_hex, conf = generate_seed_hash_analysis(next_p)
        return pred, conf, "DEC_SECURE", jackpot, h_hex

    if server == '1':
        pred, conf, sig = server1_dragon_predict(outcomes, raw_nums, level, session)
        _, _, jackpot, h_hex, _ = generate_seed_hash_analysis(session.get('last_period', '0'))
        return pred, conf, sig, jackpot, h_hex

    pred, conf, sig, jackpot, h_hex = adaptive_engine_predict(outcomes, raw_nums, session)
    return pred, conf, sig, jackpot, h_hex


# ──────────────────────────────────────────────────────────────────────────────
# HELP + CIPHER
# ──────────────────────────────────────────────────────────────────────────────

HELP_TEXT = (
    "❓ KOHLI VIP BOT HELP\n" + DIVIDER + "\n\n"
    "⚙️ Commands:\n• /start — Bot start\n• /predict — Start prediction\n"
    "• /add @Channel — Add channel\n• /help — Help\n• /cancel — Cancel\n\n"
    "📢 Auto Channel Setup:\nMake bot Admin → Auto detect!\n\n"
    "⚖️ Levels: Capped at L2\n\n"
    "📊 Engines:\n"
    "• ⚔️ Server 1 — Dragon Track\n"
    "• 🤖 Server 2 — Adaptive Quant\n"
    "• 🔑 Server 3 — Seed Hash Decrypter\n\n"
    "📞 Support: @xxLEGEND_KOHLI"
)


def encode_cid(channel_id: str) -> str:
    cid = str(channel_id).replace("-100", "").lstrip("-")
    try:
        return hex(int(cid))[2:]
    except Exception:
        return cid


def decode_cid(token: str) -> str:
    try:
        return f"-100{int(token, 16)}"
    except Exception:
        return token


def update_user_stats(user_id, file_path):
    if not file_path:
        return
    users = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                users = json.load(f)
        except Exception:
            users = {}
    now = datetime.now().strftime("%Y-%m-%d")
    if str(user_id) not in users:
        users[str(user_id)] = {"first_seen": now, "last_seen": now, "usage_count": 1}
    else:
        users[str(user_id)]["last_seen"] = now
        users[str(user_id)]["usage_count"] += 1
    try:
        with open(file_path, "w") as f:
            json.dump(users, f, indent=2)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# HOSTED BOT HANDLERS
# ──────────────────────────────────────────────────────────────────────────────

def _register_hosted_handlers(state):
    hosted = state["hosted"]
    active_dict = state["active_sessions"]
    user_states = state["user_states"]
    runtime = state["runtime"]
    current_owner = state["current_owner"]
    entry_ref = state["entry_ref"]

    def save_owner(uid):
        try:
            with open(state["owner_file"], "w") as f:
                f.write(str(uid))
            current_owner["id"] = uid
            if entry_ref[0] is not None:
                hosted_bots.setdefault(uid, {})[state["hosted_id"]] = entry_ref[0]
            update_registry_owner(state["hosted_id"], uid)
            print(f"[OWNER] Bot owner set: {uid}")
        except Exception as e:
            print(f"[OWNER] Save failed: {e}")

    def user_kb():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🚀 Start Prediction", "🛑 Stop Prediction")
        markup.row("➕ Add Channel", "📊 My Channels")
        markup.row("🗑 Remove Channel", "📈 My Stats")
        markup.row("❓ Help", "📞 Support")
        return markup

    @hosted.message_handler(commands=["start"])
    async def cmd_start(message: types.Message):
        try:
            if not os.path.exists(state["owner_file"]) or not current_owner["id"]:
                save_owner(message.from_user.id)
            if current_owner["id"] and entry_ref[0] is not None:
                hosted_bots.setdefault(current_owner["id"], {})[state["hosted_id"]] = entry_ref[0]

            update_user_stats(message.from_user.id, state["user_file"])

            await hosted.send_message(
                message.chat.id,
                f"🎯 Welcome, {message.from_user.first_name}!\n\n"
                f"{DIVIDER}\n🤖 KOHLI VIP PREDICTION BOT\n"
                f"⚔️ Server 1: Dragon HTML Engine\n"
                f"🤖 Server 2: Adaptive Quant Engine\n"
                f"🔑 Server 3: Seed Hash Decrypter\n{DIVIDER}\n\n"
                f"Use options below 👇",
                parse_mode="HTML",
                reply_markup=user_kb(),
            )
        except Exception as e:
            print(f"[START] Error: {e}")

    @hosted.message_handler(commands=["help"])
    async def cmd_help(message: types.Message):
        try:
            await hosted.send_message(message.chat.id, HELP_TEXT, parse_mode="HTML")
        except Exception:
            pass

    @hosted.message_handler(commands=["cancel"])
    async def cmd_cancel(message: types.Message):
        user_states.pop(message.from_user.id, None)
        try:
            await hosted.send_message(message.chat.id, "❌ Flow cancelled.")
        except Exception:
            pass

    @hosted.message_handler(commands=["predict"])
    async def cmd_predict(message: types.Message):
        await _trigger_start(hosted, message, message.from_user.id, state)

    @hosted.message_handler(commands=["add"])
    async def cmd_add(message: types.Message):
        user_id = message.from_user.id
        args = message.text.split()
        if len(args) < 2:
            await hosted.send_message(message.chat.id, "❌ Usage: /add @YourChannel")
            return
        channel_input = args[1].strip()
        status_msg = await hosted.send_message(message.chat.id, "🔄 Verifying...")
        try:
            chat = await hosted.get_chat(channel_input)
            channel_id = chat.id
            channel_uname = f"@{chat.username}" if chat.username else str(channel_id)
            channel_title = chat.title or channel_uname
            me = state["me"] or await hosted.get_me()
            member = await hosted.get_chat_member(channel_id, me.id)
            if member.status not in ["administrator", "creator"]:
                await safe_edit(hosted, status_msg, "❌ Bot is NOT Admin!")
                return
            added = await add_channel(user_id, channel_uname, channel_id, False)
            if added:
                await safe_edit(hosted, status_msg, f"✅ Channel Added: {channel_title}")
            else:
                await safe_edit(hosted, status_msg, f"ℹ️ Already added!")
        except Exception as e:
            await safe_edit(hosted, status_msg, f"❌ Failed: <code>{str(e)[:150]}</code>")

    @hosted.my_chat_member_handler()
    async def on_my_chat_member(update: types.ChatMemberUpdated):
        try:
            new_status = update.new_chat_member.status
            old_status = update.old_chat_member.status if update.old_chat_member else 'left'
            if new_status != 'administrator' or old_status == 'administrator':
                return
            await asyncio.sleep(2)
            chat = update.chat
            channel_id = chat.id
            channel_uname = f"@{chat.username}" if chat.username else str(channel_id)
            channel_title = chat.title or channel_uname
            promoted_by = update.from_user.id if update.from_user else None
            if not promoted_by:
                return
            added = await add_channel(promoted_by, channel_uname, channel_id, True)
            if added:
                kb = types.InlineKeyboardMarkup()
                kb.row(types.InlineKeyboardButton(
                    "🚀 Start Prediction Now!",
                    callback_data=f"quickstart_{channel_id}"))
                await hosted.send_message(
                    promoted_by,
                    f"✅ Channel Auto-Detected!\n\n{DIVIDER}\n"
                    f"📢 {channel_title}\n🔗 <code>{channel_uname}</code>\n"
                    f"🆔 <code>{channel_id}</code>\n{DIVIDER}\n\n🎉 👇",
                    parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"[AUTO-DETECT] Error: {e}")

    @hosted.message_handler(func=lambda m: True)
    async def on_text(message: types.Message):
        user_id = message.from_user.id
        text = message.text.strip() if message.text else ""
        s = user_states.get(user_id)

        if text.startswith("/"):
            return

        try:
            if text == "❓ Help":
                await hosted.send_message(message.chat.id, HELP_TEXT, parse_mode="HTML")
                return

            if text == "📞 Support":
                await hosted.send_message(message.chat.id,
                    "📞 <b>Support</b>\n\n👤 Owner: @xxLEGEND_KOHLI", parse_mode="HTML")
                return

            if text == "🚀 Start Prediction":
                await _trigger_start(hosted, message, user_id, state)
                return

            if text == "➕ Add Channel":
                await hosted.send_message(message.chat.id,
                    "📢 Add Channel:\n\n• Bot ko Admin banayein\n"
                    "• Manual: <code>/add @ChannelUsername</code>", parse_mode="HTML")
                return

            if text == "📊 My Channels":
                channels = await get_channels(user_id)
                if not channels:
                    await hosted.send_message(message.chat.id, "❌ No channels!")
                    return
                resp = f"📊 Your Channels ({len(channels)})\n{DIVIDER}\n\n"
                for i, ch in enumerate(channels, 1):
                    sN = ch.get('total_sessions', 0)
                    w = ch.get('total_wins', 0)
                    l = ch.get('total_losses', 0)
                    rate = f"{round(w / (w + l) * 100)}%" if (w + l) > 0 else "N/A"
                    resp += (f"<b>{i}. {ch['channel_link']}</b>\n"
                             f"🆔 <code>{ch['channel_id']}</code>\n"
                             f"🎮 {sN} | ✅ {w} | ❌ {l} | 📈 {rate}\n{DIVIDER}\n\n")
                await hosted.send_message(message.chat.id, resp, parse_mode="HTML")
                return

            if text == "🗑 Remove Channel":
                channels = await get_channels(user_id)
                if not channels:
                    await hosted.send_message(message.chat.id, "❌ No channels.")
                    return
                kb = types.InlineKeyboardMarkup()
                for ch in channels:
                    cid = encode_cid(ch['channel_id'])
                    kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}",
                                                       callback_data=f"manage_{cid}"))
                kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
                await hosted.send_message(message.chat.id, "🗑 Remove Channel:",
                                           reply_markup=kb)
                return

            if text == "📈 My Stats":
                channels = await get_channels(user_id)
                total_w = sum(c.get('total_wins', 0) for c in channels)
                total_l = sum(c.get('total_losses', 0) for c in channels)
                total_s = sum(c.get('total_sessions', 0) for c in channels)
                rate = f"{round(total_w / (total_w + total_l) * 100)}%" if (total_w + total_l) > 0 else "N/A"
                await hosted.send_message(message.chat.id,
                    f"📈 Statistics\n{DIVIDER}\n\n"
                    f"📢 Channels: {len(channels)}\n🎮 Sessions: {total_s}\n"
                    f"✅ Wins: {total_w}\n❌ Losses: {total_l}\n📊 Rate: {rate}\n{DIVIDER}",
                    parse_mode="HTML")
                return

            if text == "🛑 Stop Prediction":
                if user_id not in active_dict:
                    await hosted.send_message(message.chat.id, "❌ No session!")
                    return
                sess = active_dict[user_id]
                if sess.get('_ending'):
                    return
                sess['stop_flag'] = True
                task = sess.get('task')
                if task and not task.done():
                    task.cancel()
                await hosted.send_message(message.chat.id, "🛑 Stopped!")
                return

            if isinstance(s, dict) and s.get("step") == "select_bets":
                if not text.isdigit() or not (1 <= int(text) <= 50):
                    await hosted.send_message(message.chat.id, "❌ 1-50 only!")
                    return
                bets = int(text)
                server = s["server"]
                channel_link = s["channel_link"]
                channel_id = s["channel_id"]
                user_states.pop(user_id, None)

                if user_id in active_dict:
                    await hosted.send_message(message.chat.id, "⚠️ Already running.")
                    return

                active_dict[user_id] = {
                    'channel_link': channel_link, 'channel_id': channel_id,
                    'server': server, 'max_bets': bets, 'max_level': 2,
                    'current_bet': 0, 'current_level': 1,
                    'consecutive_losses': 0, 'consecutive_wins': 0,
                    'win_streak': 0, 'max_win_streak': 0, 'max_loss_streak': 0,
                    'stop_flag': False, 'wins': 0, 'losses': 0,
                    'started_at': datetime.now().strftime("%d-%m-%Y %I:%M %p"),
                    'recent_results': [], '_ending': False,
                }
                await save_session_db(user_id, active_dict[user_id])

                sname = {"1": "⚔️ Dragon Track", "2": "🤖 Adaptive Quant",
                         "3": "🔑 Seed H-Decryptor"}.get(server, server)

                await hosted.send_message(message.chat.id,
                    f"✅ Session Ready!\n{DIVIDER}\n\n"
                    f"📢 {channel_link}\n🖥 {sname}\n🎯 {bets} Rounds\n\n🔥 Starting...",
                    parse_mode="HTML")
                task = asyncio.create_task(
                    _prediction_loop(hosted, user_id, channel_link, server, state))
                active_dict[user_id]['task'] = task
        except Exception as e:
            print(f"[ON_TEXT] Error: {e}")
            traceback.print_exc()

    @hosted.callback_query_handler(func=lambda c: True)
    async def on_callback(cq: types.CallbackQuery):
        user_id = cq.from_user.id
        data = cq.data
        try:
            await hosted.answer_callback_query(cq.id)
        except Exception:
            pass

        try:
            if data == "cancel":
                user_states.pop(user_id, None)
                try:
                    await hosted.delete_message(cq.message.chat.id, cq.message.message_id)
                except Exception:
                    pass
                return

            if data == "back_to_manage":
                channels = await get_channels(user_id)
                kb = types.InlineKeyboardMarkup()
                for ch in channels:
                    cid = encode_cid(ch['channel_id'])
                    kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}",
                                                       callback_data=f"manage_{cid}"))
                kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
                await safe_edit(hosted, cq.message, "🗑 Remove Channel:", reply_markup=kb)
                return

            if data.startswith("manage_"):
                encoded = data.split("_", 1)[1]
                channel_id = decode_cid(encoded)
                channels = await get_channels(user_id)
                ch_data = next((c for c in channels
                                if str(c['channel_id']) == str(channel_id)), None)
                if not ch_data:
                    await safe_edit(hosted, cq.message, "❌ Not found.")
                    return
                kb = types.InlineKeyboardMarkup()
                kb.row(types.InlineKeyboardButton("🗑 Confirm Remove",
                                                   callback_data=f"del_{encoded}"))
                kb.row(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage"))
                await safe_edit(hosted, cq.message,
                    f"📢 Details\n{'─'*20}\n"
                    f"🏷 {ch_data['channel_link']}\n"
                    f"🆔 <code>{ch_data['channel_id']}</code>\n"
                    f"📅 {ch_data['added_date']}\n"
                    f"🎮 {ch_data.get('total_sessions', 0)}\n{'─'*20}\nRemove?",
                    reply_markup=kb)
                return

            if data.startswith("del_"):
                encoded = data.split("_", 1)[1]
                channel_id = decode_cid(encoded)
                removed = await remove_channel(user_id, channel_id)
                await safe_edit(hosted, cq.message,
                                "✅ Removed!" if removed else "❌ Not found.")
                return

            if data.startswith("quickstart_"):
                channel_id = data.split("_", 1)[1]
                channels = await get_channels(user_id)
                ch_data = next((c for c in channels
                                if str(c['channel_id']) == str(channel_id)), None)
                if not ch_data:
                    await safe_edit(hosted, cq.message, "❌ Not found.")
                    return
                if user_id in active_dict:
                    await safe_edit(hosted, cq.message, "⚠️ Already running.")
                    return
                user_states[user_id] = {"step": "select_server", "channels": channels}
                kb = types.InlineKeyboardMarkup()
                kb.row(types.InlineKeyboardButton("⚔️ SERVER 1 — Dragon Track",
                                                   callback_data="server_1"))
                kb.row(types.InlineKeyboardButton("🤖 SERVER 2 — Adaptive Quant",
                                                   callback_data="server_2"))
                kb.row(types.InlineKeyboardButton("🔑 SERVER 3 — Seed Hash",
                                                   callback_data="server_3"))
                kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
                await safe_edit(hosted, cq.message, "🎯 Select Engine:", reply_markup=kb)
                return

            if data.startswith("server_"):
                server = data.split("_")[1]
                s = user_states.get(user_id)
                if not isinstance(s, dict) or s.get("step") != "select_server":
                    await safe_edit(hosted, cq.message, "❌ Timed out.")
                    return
                channels = s["channels"]
                kb = types.InlineKeyboardMarkup()
                for ch in channels:
                    cid = encode_cid(ch['channel_id'])
                    kb.row(types.InlineKeyboardButton(
                        f"📢 {ch['channel_link']}",
                        callback_data=f"ch_{server}_{cid}"))
                kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
                sname = {"1": "⚔️ Dragon Track", "2": "🤖 Adaptive Quant",
                         "3": "🔑 Seed Hash"}.get(server, server)
                user_states[user_id] = {"step": "select_channel", "server": server,
                                         "channels": channels}
                await safe_edit(hosted, cq.message,
                                f"✅ {sname} Selected!\n\nChoose channel 👇",
                                reply_markup=kb)
                return

            if data.startswith("ch_"):
                parts = data.split("_", 2)
                server = parts[1]
                encoded = parts[2]
                channel_id = decode_cid(encoded)
                s = user_states.get(user_id, {})
                channels = s.get("channels", [])
                channel_link = next((c['channel_link'] for c in channels
                                     if str(c['channel_id']) == str(channel_id)), None)
                if not channel_link:
                    await safe_edit(hosted, cq.message, "❌ Missing.")
                    return
                user_states[user_id] = {
                    "step": "select_bets", "server": server,
                    "channel_link": channel_link, "channel_id": str(channel_id)
                }
                sname = {"1": "⚔️ Dragon Track", "2": "🤖 Adaptive Quant",
                         "3": "🔑 Seed Hash"}.get(server, server)
                await safe_edit(hosted, cq.message,
                    f"🎯 Final Config\n{DIVIDER}\n"
                    f"📢 {channel_link}\n🖥 {sname}\n{DIVIDER}\n\n"
                    f"How many predictions? (1–50)\nType a number now:")
                return

        except Exception as e:
            print(f"[CALLBACK] Error: {e}")
            try:
                await safe_edit(hosted, cq.message, f"❌ Error: <code>{str(e)[:150]}</code>")
            except Exception:
                pass


async def _trigger_start(hosted, message, user_id, state):
    user_states = state["user_states"]
    active_dict = state["active_sessions"]

    loading_msg = await hosted.send_message(message.chat.id,
        "⚡ Loading Prediction Engines...\n📡 Syncing Data...\n🧠 AI Ready...")
    try:
        channels = await get_channels(user_id)
        if not channels:
            await safe_edit(hosted, loading_msg,
                "❌ No Channels!\n\nBot ko channel Admin banayein ya /add @Channel.")
            return
        if user_id in active_dict:
            await safe_edit(hosted, loading_msg, "⚠️ Already running!")
            return

        user_states[user_id] = {"step": "select_server", "channels": channels}
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("⚔️ SERVER 1 — Dragon Track", callback_data="server_1"))
        kb.row(types.InlineKeyboardButton("🤖 SERVER 2 — Adaptive Quant", callback_data="server_2"))
        kb.row(types.InlineKeyboardButton("🔑 SERVER 3 — Seed Hash Decrypter", callback_data="server_3"))
        kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        await safe_edit(hosted, loading_msg,
            f"🎯 Select Server\n{'━'*20}\n"
            f"⚔️ Server 1 — Dragon Line + Chop + Density\n"
            f"🤖 Server 2 — Adaptive Quant Multi-Heuristic\n"
            f"🔑 Server 3 — Seed Hash Decrypter\n{'━'*20}\nChoose:",
            reply_markup=kb)
    except Exception as e:
        await safe_edit(hosted, loading_msg, f"❌ Error: <code>{str(e)[:150]}</code>")


# ──────────────────────────────────────────────────────────────────────────────
# PREDICTION LOOP
# ──────────────────────────────────────────────────────────────────────────────

async def _prediction_loop(hosted, user_id, channel_link, server, state):
    active_dict = state["active_sessions"]
    session = active_dict.get(user_id)
    if not session:
        return

    channel = int(session['channel_id'])
    sname = {"1": "⚔️ Dragon Track", "2": "🤖 Adaptive Quant",
             "3": "🔑 Seed Hash Decryptor"}.get(server, server)
    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"

    try:
        await send_sticker(hosted, channel, STICKER_START)
        await asyncio.sleep(1)

        intro = await safe_send(hosted, channel,
            f"{sep}\n🤖 KOHLI VIP PREDICTION\n{sep}\n"
            f"🖥 Server : {sname}\n"
            f"🎯 Limit : {session['max_bets']} predictions\n"
            f"🕐 Start : <code>{now_str()}</code>\n{sep}")

        if intro is None:
            await safe_send(hosted, user_id,
                            f"❌ Cannot post to {channel_link}!\nMake bot Channel Admin.")
            active_dict.pop(user_id, None)
            return

        await asyncio.sleep(1)
        max_bets = session['max_bets']
        bet_num = session.get('current_bet', 0)

        while True:
            if session.get('stop_flag'):
                await _end_session(hosted, user_id, channel, "🛑 STOPPED", state)
                return

            current_level = session.get('current_level', 1)
            bet_num += 1
            session['current_bet'] = bet_num

            records = await fetch_history()
            period = await next_period()
            session['last_period'] = period
            await save_session_db(user_id, session)

            prediction, confidence, signal_strength, jackpot, hash_val = \
                await smart_predict(records, session)

            sent = await safe_send(hosted, channel, make_prediction_text(
                period, prediction, current_level, server, confidence,
                signal_strength, jackpot, hash_val))
            if sent is None:
                await _end_session(hosted, user_id, channel,
                                    "⚠️ Posting permission lost.", state)
                return

            result, result_num = await wait_for_result(period)

            if session.get('stop_flag'):
                await _end_session(hosted, user_id, channel, "🛑 STOPPED", state)
                return

            if result is None:
                bet_num -= 1
                session['current_bet'] = bet_num
                await save_session_db(user_id, session)
                await asyncio.sleep(3)
                continue

            is_win = (result == prediction)

            if is_win:
                session['wins'] += 1
                session['consecutive_wins'] += 1
                session['consecutive_losses'] = 0
                session['win_streak'] = session.get('win_streak', 0) + 1
                session['max_win_streak'] = max(
                    session.get('max_win_streak', 0), session['win_streak'])
                session['current_level'] = 1
            else:
                session['losses'] += 1
                session['consecutive_losses'] += 1
                session['consecutive_wins'] = 0
                session['win_streak'] = 0
                session['max_loss_streak'] = max(
                    session.get('max_loss_streak', 0), session['consecutive_losses'])
                session['current_level'] = min(current_level + 1, 2)

            session['recent_results'].append(1 if is_win else 0)
            if len(session['recent_results']) > 20:
                session['recent_results'].pop(0)

            await save_session_db(user_id, session)
            completed = session['wins'] + session['losses']

            if is_win:
                await send_win_sticker(hosted, channel)
                await asyncio.sleep(0.5)
                await safe_send(hosted, channel,
                                make_win_text(session['wins'], session['losses']))
                if completed >= max_bets:
                    break

            await asyncio.sleep(2)

        await _end_session(hosted, user_id, channel, "✅ SESSION COMPLETED", state)

    except asyncio.CancelledError:
        await _end_session(hosted, user_id, channel, "🛑 SESSION TERMINATED", state)
    except Exception as e:
        print(f"[PREDICTION_LOOP] Error: {e}")
        traceback.print_exc()
        await _end_session(hosted, user_id, channel,
                            f"⚠️ ERROR: {str(e)[:80]}", state)


async def _end_session(hosted, user_id, channel, reason, state):
    active_dict = state["active_sessions"]
    session = active_dict.get(user_id)
    if not session:
        return
    if session.get('_ending'):
        return
    session['_ending'] = True

    channel_id_int = int(session['channel_id'])

    try:
        await send_sticker(hosted, channel_id_int, STICKER_STOP)
    except Exception:
        pass

    await asyncio.sleep(1)
    summary = build_session_summary(session, reason)

    try:
        await safe_send(hosted, channel_id_int, summary)
    except Exception:
        pass

    try:
        await safe_send(hosted, user_id, summary)
    except Exception:
        pass

    try:
        await update_stats(user_id, session['channel_id'],
                            session.get('wins', 0), session.get('losses', 0))
    except Exception:
        pass

    active_dict.pop(user_id, None)

    try:
        await delete_session_db(user_id)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# HOSTED BOT CREATION — BLOCKING
# ──────────────────────────────────────────────────────────────────────────────

async def _create_hosted_bot_async(token, initial_owner, hosted_id):
    """Create + launch hosted bot. Returns entry with REAL username."""
    print(f"[CREATE] Starting: {hosted_id}")

    hosted = AsyncTeleBot(token)
    hosted.request_timeout = REQUEST_TIMEOUT

    me = None
    last_err = None
    for attempt in range(3):
        try:
            print(f"[CREATE] Verify attempt {attempt+1}/3...")
            me = await asyncio.wait_for(hosted.get_me(), timeout=30)
            print(f"[CREATE] ✅ @{me.username} (ID: {me.id})")
            break
        except asyncio.TimeoutError:
            last_err = "Timeout"
            print(f"[CREATE] Timeout attempt {attempt+1}")
            await asyncio.sleep(3)
        except ApiTelegramException as e:
            last_err = f"Telegram API: {e.description or e}"
            print(f"[CREATE] API error: {last_err}")
            await asyncio.sleep(3)
        except Exception as e:
            last_err = str(e)
            print(f"[CREATE] Error attempt {attempt+1}: {e}")
            await asyncio.sleep(3)

    if me is None:
        raise RuntimeError(f"Token verification failed: {last_err}")

    owner_file = os.path.join(DATA_DIR, f"owner_{hosted_id}.txt")
    user_file = os.path.join(DATA_DIR, f"users_{me.id}.json")

    current_owner = {"id": initial_owner}
    if os.path.exists(owner_file):
        try:
            with open(owner_file, "r") as f:
                saved = f.read().strip()
                if saved:
                    current_owner["id"] = int(saved)
        except Exception:
            pass

    if hosted_id in hosted_registry:
        reg_owner = hosted_registry[hosted_id].get("owner_id", "")
        if reg_owner and reg_owner.lstrip("-").isdigit():
            current_owner["id"] = int(reg_owner)

    state = {
        "hosted": hosted,
        "active_sessions": {},
        "user_states": {},
        "runtime": {"paused": False},
        "current_owner": current_owner,
        "entry_ref": [None],
        "me": me,
        "owner_file": owner_file,
        "user_file": user_file,
        "hosted_id": hosted_id,
        "token": token,
    }

    _register_hosted_handlers(state)

    entry = {
        "token": token,
        "info": {"username": me.username, "id": me.id},
        "running": True,
        "runtime": state["runtime"],
        "hosted_id": hosted_id,
        "owner_file": owner_file,
        "user_file": user_file,
        "get_owner": lambda: state["current_owner"]["id"],
        "state": state,
    }
    state["entry_ref"][0] = entry
    hosted_by_id[hosted_id] = entry

    register_bot(hosted_id, current_owner["id"], me.username, me.id, token)

    if current_owner["id"]:
        hosted_bots.setdefault(current_owner["id"], {})[hosted_id] = entry

    asyncio.create_task(_poll_hosted(hosted, me.username))

    print(f"[CREATE] ✅ @{me.username} DEPLOYED")
    return entry


async def _poll_hosted(hosted_bot, username):
    print(f"[HOSTED @{username}] Polling...")
    try:
        await hosted_bot.polling(
            non_stop=True,
            allowed_updates=util.update_types,
            request_timeout=REQUEST_TIMEOUT,
        )
    except asyncio.CancelledError:
        print(f"[HOSTED @{username}] cancelled")
    except Exception as e:
        print(f"[HOSTED @{username}] Error: {e}")
        traceback.print_exc()


def start_hosted_prediction_bot(token, initial_owner, hosted_id):
    """Sync wrapper — schedule on background loop."""
    ensure_loop()
    return schedule_async(_create_hosted_bot_async(token, initial_owner, hosted_id))


# ──────────────────────────────────────────────────────────────────────────────
# FLASK API
# ──────────────────────────────────────────────────────────────────────────────

api_app = Flask(__name__)


@api_app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "KOHLI Premium Hosting",
        "version": "8.1",
        "hosted_bots": len(hosted_by_id),
        "registry_count": len(hosted_registry),
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat(),
    })


@api_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@api_app.route("/api/create_bot", methods=["POST"])
def api_create_bot():
    """Deploy bot — BLOCKS until bot is live, returns REAL username."""
    try:
        data = request.get_json() or {}
        token = (data.get("token") or "").strip()
        telegram_id = data.get("telegram_id") or data.get("owner_id")

        print(f"[API] Deploy request received")

        if not token or ":" not in token or len(token) < 30:
            return jsonify({"status": "error", "success": False,
                            "message": "Invalid bot token format"}), 400

        for hid, e in hosted_by_id.items():
            if e.get("token") == token:
                info = e.get("info", {})
                return jsonify({
                    "status": "ok", "success": True,
                    "username": info.get("username", "Bot"),
                    "bot_id": str(info.get("id", "")),
                    "hosted_id": hid,
                    "message": f"Bot @{info.get('username')} already running",
                })

        for hid, reg in list(hosted_registry.items()):
            if reg.get("token") == token and hid not in hosted_by_id:
                print(f"[API] Cleaning stale entry: {hid}")
                unregister_bot(hid)

        hosted_id = f"bot_{int(time.time())}_{random.randint(1000, 9999)}"

        initial_owner = None
        if telegram_id:
            try:
                initial_owner = int(str(telegram_id).strip())
            except Exception:
                pass

        loop = ensure_loop()
        future = asyncio.run_coroutine_threadsafe(
            _create_hosted_bot_async(token, initial_owner, hosted_id),
            loop
        )

        try:
            entry = future.result(timeout=60)
        except Exception as e:
            err_msg = str(e)[:250]
            print(f"[API] ❌ Deploy failed: {err_msg}")
            return jsonify({
                "status": "error",
                "success": False,
                "message": err_msg
            }), 500

        info = entry.get("info", {})
        real_username = info.get("username", "unknown")
        real_bot_id = info.get("id", 0)

        print(f"[API] ✅ Deployed @{real_username}")

        async def _notify_admin():
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"{DIVIDER}\n🔑 NEW BOT\n{DIVIDER}\n\n"
                    f"🤖 @{real_username}\n🆔 `{real_bot_id}`\n"
                    f"📦 `{hosted_id}`\n👤 `{initial_owner or 'pending'}`\n\n"
                    f"{SUB_DIVIDER}\n🚀 KOHLI",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"[API] notify failed: {e}")

        schedule_async(_notify_admin())

        return jsonify({
            "status": "ok",
            "success": True,
            "username": real_username,
            "bot_id": str(real_bot_id),
            "hosted_id": hosted_id,
            "message": f"Bot @{real_username} deployed successfully",
        })

    except Exception as e:
        print(f"[API] Error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "success": False,
                        "message": str(e)[:250]}), 500


@api_app.route("/api/list_bots", methods=["POST"])
def api_list_bots():
    try:
        data = request.get_json() or {}
        owner_id = str(data.get("owner_id") or data.get("telegram_id")
                        or data.get("user_id") or "").strip()

        if not owner_id or not owner_id.lstrip("-").isdigit():
            return jsonify({"status": "error", "success": False,
                            "message": "Invalid owner"}), 400

        owner_int = int(owner_id)
        result = []
        seen = set()

        for hid, entry in hosted_bots.get(owner_int, {}).items():
            if hid not in seen:
                seen.add(hid)
                info = entry.get("info", {})
                result.append({
                    "username": info.get("username", "Bot"),
                    "bot_id": str(info.get("id", "")),
                    "hosted_id": str(hid),
                    "running": entry.get("running", True),
                })

        for hid, entry in hosted_by_id.items():
            if hid in seen:
                continue
            try:
                get_owner = entry.get("get_owner")
                if get_owner and str(get_owner()) == owner_id:
                    seen.add(hid)
                    info = entry.get("info", {})
                    result.append({
                        "username": info.get("username", "Bot"),
                        "bot_id": str(info.get("id", "")),
                        "hosted_id": str(hid),
                        "running": entry.get("running", True),
                    })
            except Exception:
                pass

        for hid, entry in hosted_by_id.items():
            if hid in seen:
                continue
            owner_file = entry.get("owner_file")
            if owner_file and os.path.exists(owner_file):
                try:
                    with open(owner_file, "r") as f:
                        if f.read().strip() == owner_id:
                            seen.add(hid)
                            info = entry.get("info", {})
                            result.append({
                                "username": info.get("username", "Bot"),
                                "bot_id": str(info.get("id", "")),
                                "hosted_id": str(hid),
                                "running": entry.get("running", True),
                            })
                except Exception:
                    pass

        for hid, reg in hosted_registry.items():
            if hid in seen:
                continue
            if str(reg.get("owner_id", "")) == owner_id:
                seen.add(hid)
                result.append({
                    "username": reg.get("username", "Bot"),
                    "bot_id": str(reg.get("bot_id", "")),
                    "hosted_id": str(hid),
                    "running": hid in hosted_by_id,
                })

        return jsonify({"status": "ok", "success": True,
                        "bots": result, "count": len(result)})

    except Exception as e:
        return jsonify({"status": "error", "success": False,
                        "message": str(e)}), 500


@api_app.route("/api/toggle_bot", methods=["POST"])
def api_toggle_bot():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()
        action = (data.get("action") or "").strip().lower()

        if hosted_id not in hosted_by_id:
            return jsonify({"status": "error", "success": False,
                            "message": "Bot not found"}), 404

        entry = hosted_by_id[hosted_id]

        if action == "off":
            entry["running"] = False
            entry["runtime"]["paused"] = True
            return jsonify({"status": "ok", "success": True, "running": False})
        elif action == "on":
            entry["running"] = True
            entry["runtime"]["paused"] = False
            return jsonify({"status": "ok", "success": True, "running": True})
        else:
            return jsonify({"status": "error", "success": False,
                            "message": "Invalid action"}), 400

    except Exception as e:
        return jsonify({"status": "error", "success": False,
                        "message": str(e)}), 500


@api_app.route("/api/delete_bot", methods=["POST"])
def api_delete_bot():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()

        if hosted_id not in hosted_by_id and hosted_id not in hosted_registry:
            return jsonify({"status": "error", "success": False,
                            "message": "Bot not found"}), 404

        entry = hosted_by_id.get(hosted_id, {})

        if hosted_id in hosted_by_id:
            e = hosted_by_id[hosted_id]
            e["running"] = False
            e["runtime"]["paused"] = True
            del hosted_by_id[hosted_id]

        for uid, bots in list(hosted_bots.items()):
            if hosted_id in bots:
                del bots[hosted_id]

        owner_file = entry.get("owner_file") or os.path.join(DATA_DIR, f"owner_{hosted_id}.txt")
        if os.path.exists(owner_file):
            try:
                os.remove(owner_file)
            except Exception:
                pass

        unregister_bot(hosted_id)

        return jsonify({"status": "ok", "success": True, "message": "Deleted"})

    except Exception as e:
        return jsonify({"status": "error", "success": False,
                        "message": str(e)}), 500


@api_app.route("/api/bot_stats", methods=["POST"])
def api_bot_stats():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()

        if hosted_id not in hosted_by_id:
            return jsonify({"status": "error", "success": False,
                            "message": "Bot not found"}), 404

        entry = hosted_by_id[hosted_id]
        info = entry.get("info", {})
        bot_id = info.get("id")
        user_file = entry.get("user_file") or os.path.join(DATA_DIR, f"users_{bot_id}.json")

        users = {}
        if os.path.exists(user_file):
            try:
                with open(user_file, "r") as f:
                    users = json.load(f)
            except Exception:
                pass

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = datetime.fromtimestamp(
            datetime.now().timestamp() - 86400).strftime("%Y-%m-%d")
        d1 = sum(1 for u in users.values() if u.get("last_seen") == today)
        d2 = sum(1 for u in users.values() if u.get("last_seen") == yesterday_str)

        return jsonify({
            "status": "ok", "success": True,
            "total_users": len(users),
            "active_today": d1,
            "active_yesterday": d2,
            "running": entry.get("running", False),
            "username": info.get("username", "Bot"),
        })

    except Exception as e:
        return jsonify({"status": "error", "success": False,
                        "message": str(e)}), 500


@api_app.route("/api/broadcast", methods=["POST"])
def api_broadcast():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()
        message = (data.get("message") or "").strip()

        if hosted_id not in hosted_by_id:
            return jsonify({"status": "error", "success": False,
                            "message": "Bot not found"}), 404
        if not message:
            return jsonify({"status": "error", "success": False,
                            "message": "Empty message"}), 400

        entry = hosted_by_id[hosted_id]
        info = entry.get("info", {})
        bot_id = info.get("id")
        token = entry.get("token")
        user_file = entry.get("user_file") or os.path.join(DATA_DIR, f"users_{bot_id}.json")

        users = {}
        if os.path.exists(user_file):
            try:
                with open(user_file, "r") as f:
                    users = json.load(f)
            except Exception:
                pass

        if not users:
            return jsonify({"status": "ok", "success": True, "sent": 0, "failed": 0})

        async def _send_all():
            bcast_bot = AsyncTeleBot(token, parse_mode="Markdown")
            sent = 0
            failed = 0
            for uid in list(users.keys()):
                try:
                    await bcast_bot.send_message(
                        int(uid),
                        f"{DIVIDER}\n📢 BROADCAST\n{DIVIDER}\n\n"
                        f"{message}\n\n{LIGHTNING_STR}")
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    failed += 1
            try:
                await bcast_bot.close_session()
            except Exception:
                pass
            return sent, failed

        loop = ensure_loop()
        future = asyncio.run_coroutine_threadsafe(_send_all(), loop)
        sent, failed = future.result(timeout=180)

        return jsonify({"status": "ok", "success": True,
                        "sent": sent, "failed": failed})

    except Exception as e:
        return jsonify({"status": "error", "success": False,
                        "message": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# RESTORE
# ──────────────────────────────────────────────────────────────────────────────

async def restore_bots_from_registry():
    print("[RESTORE] Checking...")
    restored = 0
    for hid, reg in list(hosted_registry.items()):
        token = reg.get("token")
        owner_id = reg.get("owner_id")
        if not token:
            continue
        try:
            owner_int = int(owner_id) if owner_id and str(owner_id).lstrip("-").isdigit() else None
            await _create_hosted_bot_async(token, owner_int, hid)
            restored += 1
            print(f"[RESTORE] ✅ @{reg.get('username')}")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[RESTORE] ❌ {hid}: {e}")
    print(f"[RESTORE] Total: {restored}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN BOT HANDLERS
# ──────────────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
async def main_start(message: types.Message):
    await bot.send_message(
        message.chat.id,
        f"👑 KOHLI HOSTING BOT v8.1\n{DIVIDER}\n\n"
        f"🚀 Deploy & manage prediction bots.\n\n"
        f"📱 Use Web App to deploy.\n🔧 Admin: /admin",
        parse_mode="HTML",
    )


@bot.message_handler(commands=["admin"])
async def main_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "❌ Access denied.")
        return
    await bot.send_message(
        message.chat.id,
        f"🔧 ADMIN\n{DIVIDER}\n\n"
        f"📦 Registered: {len(hosted_registry)}\n"
        f"🟢 Live: {len(hosted_by_id)}\n"
        f"🔥 Sessions: {len(active_sessions)}\n\n"
        f"/resetdb — wipe data",
        parse_mode="HTML",
    )


@bot.message_handler(commands=["resetdb"])
async def main_resetdb(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "❌ Access denied.")
        return
    global _data_cache
    _data_cache = {"users": {}, "sessions": {}}
    await save_data(_data_cache)
    await bot.send_message(message.chat.id, "✅ DB wiped!")


# ──────────────────────────────────────────────────────────────────────────────
# RUNNERS
# ──────────────────────────────────────────────────────────────────────────────

def run_api():
    port = int(os.environ.get("PORT", 8080))
    print(f"[API] Starting Flask on port {port}")
    api_app.run(host="0.0.0.0", port=port, debug=False,
                use_reloader=False, threaded=True)


async def shutdown():
    print("\n⏳ Shutting down...")
    await close_http()
    try:
        await bot.close_session()
    except Exception:
        pass
    print("✅ Done.")


async def main():
    print("\n" + "=" * 60)
    print("👑 KOHLI HOSTING + PREDICTION BOT v8.1")
    print("=" * 60 + "\n")

    load_registry()

    for attempt in range(MAX_RETRIES):
        try:
            me = await bot.get_me()
            print(f"✅ Host bot: @{me.username}")
            break
        except ApiTelegramException as e:
            if e.error_code == 401:
                print("❌ FATAL: Invalid HOST_BOT_TOKEN")
                return
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"❌ Telegram error: {e}")
                return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"❌ Failed: {e}")
                return

    asyncio.create_task(restore_bots_from_registry())
    await get_http()

    print("✅ HOST BOT ONLINE\n")

    try:
        await bot.polling(non_stop=True, allowed_updates=util.update_types,
                          request_timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"❌ Polling error: {e}")
    finally:
        await shutdown()


if __name__ == "__main__":
    ensure_loop()
    print("[BOOT] Async loop started")

    threading.Thread(target=run_api, daemon=True).start()
    time.sleep(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Terminated.")
    except Exception as e:
        print(f"\n❌ Crash: {e}")
        traceback.print_exc()
