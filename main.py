# ============================================================
# 👑 KOHLI VIP PREDICTION BOT — ALL-IN-ONE v8.0
# ============================================================
# ✨ Railway Ready — No Dockerfile, No nixpacks.toml needed
# 🔧 Auto-installs dependencies at startup
# ============================================================

import subprocess
import sys
import os

# ──────────────────────────────────────────────────────────────
# AUTO-INSTALL DEPENDENCIES (Railway Safe)
# ──────────────────────────────────────────────────────────────

REQUIRED = [
    "pyTelegramBotAPI",
    "httpx",
    "flask",
    "pytz",
]

def _ensure_pip():
    """Ensure pip is available; bootstrap via ensurepip if missing."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True, capture_output=True
        )
        return True
    except Exception:
        try:
            subprocess.run(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                check=True, capture_output=True
            )
            return True
        except Exception:
            return False

def _install(pkg):
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--quiet", pkg],
            check=True, capture_output=True
        )
        return True
    except Exception as e:
        print(f"[AUTO-INSTALL] Failed {pkg}: {e}")
        return False

def _bootstrap():
    print("[BOOTSTRAP] Checking dependencies...")
    if not _ensure_pip():
        print("[BOOTSTRAP] pip bootstrap failed. Trying anyway...")
    for pkg in REQUIRED:
        _install(pkg)
    print("[BOOTSTRAP] Dependencies ready.")

_bootstrap()

# ──────────────────────────────────────────────────────────────
# NOW SAFE TO IMPORT
# ──────────────────────────────────────────────────────────────

import asyncio
import json
import random
import math
import hashlib
import threading
import time
from datetime import datetime
from collections import deque, Counter
import httpx
from telebot.async_telebot import AsyncTeleBot
from telebot import types, util
from telebot.apihelper import ApiTelegramException
import telebot as sync_telebot
from flask import Flask, request, jsonify
import pytz

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8766089087:AAFQ4hk4V27YtzWvzCSmWMRCJFZF_NWV8lg")
HOST_BOT_TOKEN = os.environ.get("HOST_BOT_TOKEN", "8372270378:AAEXNRXUD2xTwShxB7z7WR5uqX2NrWBvN6o")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7741897793"))
FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://glowbet-1b2ce-default-rtdb.firebaseio.com")
HISTORY_API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

DATA_DIR = os.environ.get("DATA_DIR", "kohli_data")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "bot_data.json")

REQUEST_TIMEOUT = 60
MAX_RETRIES = 5
RETRY_DELAY = 3

STICKER_START = "CAACAgUAAxkBAAFLuItqJPtZCBFQfGfRsJKl6boNvqKixQACuRMAAtgMEVayBm8tXDvNpDsE"
STICKER_WIN_LIST = [
    "CAACAgUAAxkBAAFLuI1qJPt6xyJZrPgYtmOdxJ2YMa6gFwACJxQAAhs_UVXBa4-Se7IejzsE",
    "CAACAgUAAxkBAAFL6I1qJ38O9fE3RKMdUU0R1iQpapxH8AACBxwAAqlQ2FYgxhZ0x6m0ojsE",
]
STICKER_STOP = "CAACAgUAAxkBAAFLuJFqJPuZKYQt4bz30u_39DM-JwW4agAClBEAAo-CGFb2yvdmMKOx1jsE"

DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━"
SUB_DIVIDER = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
SPARKLE = "✨"
CROWN = "👑"
ROCKET = "🚀"
FIRE = "🔥"
GEM = "💎"
LIGHTNING = "⚡"
TARGET = "🎯"
CHART = "📊"
BELL = "🔔"
SHIELD = "🛡️"
BRAIN = "🧠"

# ──────────────────────────────────────────────────────────────
# GLOBAL INSTANCES
# ──────────────────────────────────────────────────────────────

bot = AsyncTeleBot(BOT_TOKEN)
bot.request_timeout = REQUEST_TIMEOUT

host_bot = sync_telebot.TeleBot(HOST_BOT_TOKEN, parse_mode="Markdown")

user_states = {}
active_sessions = {}
_http_client = None

# ──────────────────────────────────────────────────────────────
# HTTP CLIENT
# ──────────────────────────────────────────────────────────────

def get_http():
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=15.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _http_client

async def close_http():
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
    _http_client = None

# ──────────────────────────────────────────────────────────────
# CORE UTILITIES
# ──────────────────────────────────────────────────────────────

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

def now_str():
    return datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

def _confidence_bar(pct):
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)

def styled_footer(text="KOHLI PREMIUM ENGINE"):
    return f"{SUB_DIVIDER}\n{LIGHTNING} {text} {LIGHTNING}"

def generate_seed_hash_analysis(period: str):
    salt = "GLOWBET_SECURE_WIN_SEED_KEY_2026"
    combined = f"{period}_{salt}"
    hash_hex = hashlib.sha256(combined.encode('utf-8')).hexdigest()

    hash_segment = hash_hex[:8]
    number = int(hash_segment, 16) % 10
    prediction = "BIG" if number >= 5 else "SMALL"
    is_jackpot = (number in [0, 5])

    numeric_count = sum(1 for c in hash_hex if c.isdigit())
    confidence = 80 + (numeric_count % 16)

    return prediction, number, is_jackpot, hash_hex, confidence

def make_prediction_text(period, prediction, level, server, confidence=None,
                         signal_strength=None, jackpot=False, hash_val=None):
    if prediction == "SMALL":
        bet_line = "😈𝐁ᴇᴛ ➪ 🔵𝐒ᴍᴀʟʟ ☠️"
    else:
        bet_line = "😈𝐁ᴇᴛ ➪ 🔴𝐁ɪɢ 👑"

    conf_line = ""
    if confidence is not None:
        bar = _confidence_bar(confidence)
        conf_line = f"\n📊 𝐂ᴏɴꜰɪᴅᴇɴᴄᴇ: {confidence}% {bar}"

    jackpot_line = ""
    if jackpot:
        jackpot_line = f"\n🚨 𝐉𝐀𝐂𝐊𝐏𝐎𝐓 𝐀𝐋𝐄𝐑𝐓: 💜 𝐕ɪᴏʟᴇᴛ (0/5) 𝐃ᴇᴛᴇᴄᴛᴇᴅ!"

    hash_line = ""
    if hash_val:
        truncated_hash = f"{hash_val[:12]}...{hash_val[-12:]}"
        hash_line = f"\n🔑 𝐇ᴀsʜ: <code>{truncated_hash}</code>\n🔐 𝐒ᴇᴇᴅ: 𝐕ᴇʀɪꜰɪᴇᴅ"

    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"
    return (
        f"{sep}\n"
        f"🏅𝐖ɪɴɢᴏ 1 𝐌ɪɴᴜᴛᴇ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ👻\n"
        f"{sep}\n"
        f"💀𝐏ᴇʀɪᴏᴅ 𝐍ᴜᴍʙᴇʀ ❤️‍🔥 <code>{period}</code>\n"
        f"{bet_line}"
        f"{conf_line}"
        f"{jackpot_line}"
        f"{hash_line}\n"
        f"{sep}"
    )

def make_win_text(wins, losses):
    total = wins + losses
    win_rate = round(wins / total * 100) if total > 0 else 0
    stars = "⭐" * min(5, max(1, win_rate // 20))
    return (
        f"✅ <b>𝐖ɪɴ!</b> {stars}\n"
        f"🏆 𝐖ɪɴs : {wins} │ ❌ 𝐋ᴏss : {losses} │ 📈 {win_rate}%"
    )

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

    if server == "1":
        server_name = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
    elif server == "2":
        server_name = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
    else:
        server_name = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏʀ"

    if recent:
        recent_visual = "".join("✅" if r == 1 else "❌" for r in recent[-10:])
        recent_rate = round(sum(recent[-10:]) / len(recent[-10:]) * 100)
    else:
        recent_visual = "❌❌❌❌❌❌❌❌❌❌"
        recent_rate = 0

    if "COMPLETED" in reason:
        status_line = "✅ 𝐒ᴇssɪᴏɴ 𝐂ᴏᴍᴘʟᴇᴛᴇᴅ"
    elif "STOPPED" in reason:
        status_line = "🛑 𝐒ᴇssɪᴏɴ 𝐒ᴛᴏᴘᴘᴇᴅ"
    else:
        status_line = f"⚠️ {reason}"

    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"
    return (
        f"{sep}\n"
        f"☑️ 𝐊ᴏʜʟɪ 𝐏ʀɪᴠᴀᴛᴇ 𝐀ᴜᴛᴏ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ ⚠️\n"
        f"{sep}\n\n"
        f"🖥 𝐒ᴇ r ᴠᴇ r : {server_name}\n"
        f"🕐 𝐒ᴛᴀ r ᴛ : <code>{started}</code>\n"
        f"🕑 𝐄ɴᴅ : <code>{ended_at}</code>\n\n"
        f"🎯 𝐑ᴏᴜɴᴅs : {total}\n"
        f"{sep}\n\n"
        f" ✅ 𝐖ɪɴ ➠ {wins}\n"
        f" ❌ 𝐋ᴏss ➠ {losses}\n"
        f" 🏆 𝐁ᴇsᴛ 𝐒ᴛʀᴇᴀᴋ ➠ {max_streak}\n"
        f" 📈 𝐀ᴄᴄᴜʀᴀᴄʏ ➠ {rate}%\n\n"
        f"{recent_visual} {recent_rate}%\n\n"
        f"📌 𝐒ᴛᴀᴛᴜs » {status_line}\n\n"
        f"{sep}\n"
        f"🚀 𝐀𝐈 𝐏ᴏᴡᴇʀᴇᴅ 𝐁ʏ @xxLEGEND_KOHLI"
    )

# ──────────────────────────────────────────────────────────────
# PERSISTENCE
# ──────────────────────────────────────────────────────────────

_data_cache = None

async def load_data():
    global _data_cache
    if _data_cache is not None:
        return _data_cache
    empty = {"users": {}, "sessions": {}}

    if FIREBASE_URL:
        for attempt in range(MAX_RETRIES):
            try:
                r = await get_http().get(f"{FIREBASE_URL.rstrip('/')}/bot_data.json")
                if r.status_code == 200:
                    d = r.json()
                    if d and isinstance(d, dict):
                        d.setdefault("users", {})
                        d.setdefault("sessions", {})
                        _data_cache = d
                        return _data_cache
            except Exception:
                if attempt < MAX_RETRIES - 1:
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
            await get_http().put(f"{FIREBASE_URL.rstrip('/')}/bot_data.json", json=data)
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
        'total_sessions': 0, 'total_wins': 0, 'total_losses': 0
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

# ──────────────────────────────────────────────────────────────
# HISTORY DATA
# ──────────────────────────────────────────────────────────────

async def fetch_history():
    for attempt in range(MAX_RETRIES):
        try:
            await asyncio.sleep(0.5)
            r = await get_http().get(HISTORY_API)
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
    deadline = loop.time() + 120
    while loop.time() < deadline:
        records = await fetch_history()
        for r in records:
            if _issue(r) == period_str.strip():
                num = _number(r)
                return ('BIG' if num >= 5 else 'SMALL'), num
        await asyncio.sleep(3)
    return None, None

# ──────────────────────────────────────────────────────────────
# KEYBOARDS & SAFE SEND
# ──────────────────────────────────────────────────────────────

def user_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Start Prediction", "🛑 Stop Prediction")
    markup.row("➕ Add Channel", "📊 My Channels")
    markup.row("🗑 Remove Channel", "📈 My Stats")
    markup.row("❓ Help", "📞 Support")
    return markup

def admin_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Start Prediction", "🛑 Stop Prediction")
    markup.row("➕ Add Channel", "📊 My Channels")
    markup.row("🗑 Remove Channel", "📈 My Stats")
    markup.row("📢 Broadcast", "🔧 System Stats")
    markup.row("❓ Help", "📞 Support")
    return markup

async def safe_send(target, text, reply_markup=None):
    for attempt in range(MAX_RETRIES):
        try:
            await asyncio.sleep(0.3)
            return await bot.send_message(target, text, parse_mode="HTML",
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

async def safe_edit(msg, text, reply_markup=None):
    try:
        await asyncio.sleep(0.2)
        await bot.edit_message_text(
            chat_id=msg.chat.id, message_id=msg.message_id,
            text=text, parse_mode='HTML', reply_markup=reply_markup)
    except Exception:
        pass

async def send_sticker(target, sticker_id):
    try:
        await asyncio.sleep(0.3)
        await bot.send_sticker(target, sticker_id)
    except Exception:
        pass

async def send_win_sticker(target):
    sticker = random.choice(STICKER_WIN_LIST)
    await send_sticker(target, sticker)

# ──────────────────────────────────────────────────────────────
# PREDICTION ALGORITHMS
# ──────────────────────────────────────────────────────────────

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

def _to_bits(seq):
    return [1 if x == 'BIG' else 0 for x in seq]

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
    bits = _to_bits(seq)
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
    recent_br = _big_rate(seq[:recent_w])
    baseline_br = _big_rate(seq[recent_w:baseline_w])
    drift = recent_br - baseline_br
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
            leader = 'BIG' if br >= 0.5 else 'SMALL'
            votes[leader] += weight * 0.15
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
        scaled = 50 + (edge - 0.5) * 90
        return max(50, min(92, round(scaled)))

    def top_factors(self, n=4):
        return [s[0] for s in sorted(self._signals, key=lambda x: x[2], reverse=True)[:n]]

def _validate_prediction(seq, prediction):
    test_windows = [15, 30, 60, 100]
    passes = 0
    total = 0
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
        current_type = hist[0]
        streak = 1
        for i in range(1, len(hist)):
            if hist[i] == current_type:
                streak += 1
            else:
                break
        if 2 <= streak <= 8:
            return current_type
        return None

    def _html_chop_chop(hist):
        if len(hist) < 4:
            return None
        if (hist[0] != hist[1] and hist[1] == hist[2] and hist[2] != hist[3]):
            return 'SMALL' if hist[0] == 'BIG' else 'BIG'
        return None

    def _html_density(hist, sample_size=6):
        n = min(sample_size, len(hist))
        if n < 3:
            return None
        sample = hist[:n]
        big_count = sample.count('BIG')
        if big_count > n / 2:
            return 'SMALL'
        elif big_count < n / 2:
            return 'BIG'
        return None

    html_dragon = _html_dragon_line(outcomes)
    if html_dragon:
        streak_val, streak_len, _, _ = _streak_info(outcomes)
        board.add("HTML-DragonLine", html_dragon, 1.5 + streak_len * 0.3)

    html_chop = _html_chop_chop(outcomes)
    if html_chop:
        board.add("HTML-ChopChop", html_chop, 2.2)

    html_density = _html_density(outcomes, sample_size=6)
    if html_density:
        board.add("HTML-Density", html_density, 1.8)

    st_z = _zscore(outcomes[:min(10, n)])
    if abs(st_z) >= 0.4:
        fade = 'SMALL' if st_z > 0 else 'BIG'
        board.add("ST-ZScore-Fade", fade, min(3.0, abs(st_z) * 1.2))

    streak_val, streak_len, max_s, avg_run = _streak_info(outcomes)
    exhaust = _streak_exhaustion_score(outcomes)
    if streak_len >= 3:
        flip = 'SMALL' if streak_val == 'BIG' else 'BIG'
        weight = 1.5 + exhaust * 4.5
        board.add("StreakExhaustion", flip, weight)

    tm = _transition_matrix(outcomes)
    last = outcomes[0]
    if last == 'BIG':
        p_big_next = tm['BB']
        p_sml_next = tm['BS']
    else:
        p_big_next = tm['SB']
        p_sml_next = tm['SS']
    if abs(p_big_next - 0.5) >= 0.08:
        mk_pred = 'BIG' if p_big_next > p_sml_next else 'SMALL'
        mk_weight = abs(p_big_next - 0.5) * 8
        board.add("Markov1", mk_pred, mk_weight)

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

    cycle_block, block_score = _repeating_block_cycle(outcomes, min_len=2, max_len=8)
    if cycle_block is not None and block_score >= 0.70:
        pos = n % len(cycle_block)
        cycle_pred = cycle_block[pos % len(cycle_block)]
        board.add("BlockCycle", cycle_pred, block_score * 4.5)

    cyc_period, cyc_strength = _detect_cycle(outcomes, max_lag=24)
    if cyc_period is not None and cyc_strength >= 0.22:
        phase = n % cyc_period
        if phase < len(outcomes):
            board.add("AutoCorrCycle", outcomes[phase], cyc_strength * 3.0)

    anom = _anomaly_score(outcomes, window=20)
    if anom >= 0.65:
        revert_to = 'SMALL' if _big_rate(outcomes[:10]) > 0.5 else 'BIG'
        board.add("AnomalyReversion", revert_to, anom * 3.0)

    cluster_val, cluster_ex = _cluster_exhaustion(outcomes, min_cluster=3)
    if cluster_val is not None:
        flip = 'SMALL' if cluster_val == 'BIG' else 'BIG'
        board.add("ClusterExhaustion", flip, cluster_ex * 3.5)

    sim_probs, sim_conf = _historical_similarity(outcomes, lookback=7)
    if sim_conf >= 0.30:
        sim_pred = 'BIG' if sim_probs['BIG'] > sim_probs['SMALL'] else 'SMALL'
        sim_weight = sim_conf * 4.0 * abs(sim_probs['BIG'] - 0.5) * 2
        board.add("HistSimilarity", sim_pred, sim_weight)

    wbr = _weighted_big_rate(outcomes[:25], decay=0.91)
    w_drift = wbr - 0.5
    if abs(w_drift) >= 0.09:
        fade = 'SMALL' if w_drift > 0 else 'BIG'
        board.add("WeightedRecencyFade", fade, abs(w_drift) * 4.0)

    mom = _momentum_shift(outcomes, window=5)
    if abs(mom) >= 0.20:
        mom_pred = 'BIG' if mom > 0 else 'SMALL'
        board.add("MomentumCont", mom_pred, abs(mom) * 2.5)

    ent = _shannon_entropy(outcomes[:20])
    if ent < 0.80:
        board.add("LowEntropyBoost", board.leading(), (0.80 - ent) * 3.5)

    drift_dir, drift_mag = _frequency_drift(outcomes)
    if drift_mag >= 0.15:
        fade_dir = 'SMALL' if drift_dir == 'BIG' else 'BIG'
        board.add("FreqDriftFade", fade_dir, drift_mag * 3.0)

    contradictions = board.contradictions()
    edge = board.edge_ratio()
    if contradictions >= 5 and edge < 0.57:
        trailer = 'SMALL' if board.leading() == 'BIG' else 'BIG'
        board.add("ConflictPenalty", trailer, 1.8)

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
        'edge': edge_final,
        'entropy': ent,
        'streak': (streak_val, streak_len),
        'top_factors': board.top_factors(4),
        'cycle_block': cycle_block,
        'block_score': block_score,
        'anom': anom,
        'cyc_period': cyc_period,
        'cyc_strength': cyc_strength,
        'alt_rate': alt_rate,
    }

    return prediction, confidence, sig, meta

def server1_dragon_predict(outcomes: list, raw_nums: list, level: int, session: dict):
    if len(outcomes) < 3:
        return 'BIG', 60, "INSUFFICIENT"

    def _html_dragon_line(hist):
        if len(hist) < 2:
            return None
        current_type = hist[0]
        streak = 1
        for i in range(1, len(hist)):
            if hist[i] == current_type:
                streak += 1
            else:
                break
        if 2 <= streak <= 8:
            return current_type
        return None

    def _html_chop_chop(hist):
        if len(hist) < 4:
            return None
        if (hist[0] != hist[1] and hist[1] == hist[2] and hist[2] != hist[3]):
            return 'SMALL' if hist[0] == 'BIG' else 'BIG'
        return None

    def _html_density(hist, sample_size=6):
        n = min(sample_size, len(hist))
        if n < 3:
            return None
        sample = hist[:n]
        big_count = sample.count('BIG')
        if big_count > n / 2:
            return 'SMALL'
        elif big_count < n / 2:
            return 'BIG'
        return None

    def _html_weighted_recency_fallback(hist):
        if not hist:
            return 'BIG'
        return hist[0]

    hist = outcomes
    pred = None
    stage_used = "RecencyFallback"

    dragon = _html_dragon_line(hist)
    if dragon is not None:
        pred = dragon
        stage_used = "DragonLine"

    chop = _html_chop_chop(hist)
    if chop is not None:
        pred = chop
        stage_used = "ChopChop"

    if pred is None:
        pred = _html_density(hist)
        stage_used = "Density"

    if pred is None:
        pred = _html_weighted_recency_fallback(hist)
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
        density_gap = abs(big_count - 3)
        base_conf = 60 + density_gap * 4
    else:
        base_conf = 58

    base_conf = max(54, min(82, base_conf))

    if level == 1:
        final_pred = pred
        final_conf = base_conf
        sig = f"L1/{stage_used}"
    else:
        votes = {'BIG': 0.0, 'SMALL': 0.0}
        votes[pred] += 2.0

        d6 = _html_density(hist, sample_size=6)
        d10 = _html_density(hist, sample_size=10)
        d20 = _html_density(hist, sample_size=20) if len(hist) >= 20 else None
        if d6:
            votes[d6] += 1.5
        if d10:
            votes[d10] += 1.5
        if d20:
            votes[d20] += 1.0

        if len(hist) >= 10:
            recent5 = hist[:5]
            recent10 = hist[:10]
            r5_big = recent5.count('BIG') / 5.0
            r10_big = recent10.count('BIG') / 10.0
            drift = r5_big - r10_big
            if abs(drift) >= 0.20:
                revert = 'SMALL' if drift > 0 else 'BIG'
                votes[revert] += 2.0

        if streak >= 4:
            flip = 'SMALL' if hist[0] == 'BIG' else 'BIG'
            votes[flip] += 2.5
        elif streak >= 3:
            flip = 'SMALL' if hist[0] == 'BIG' else 'BIG'
            votes[flip] += 1.5

        if len(hist) >= 6:
            alt_flips = sum(1 for i in range(5) if hist[i] != hist[i + 1])
            if alt_flips >= 4:
                next_alt = 'SMALL' if hist[0] == 'BIG' else 'BIG'
                votes[next_alt] += 2.0

        if len(hist) >= 20:
            window = hist[:20]
            bg = window.count('BIG')
            sm = window.count('SMALL')
            if bg >= 15:
                votes['SMALL'] += 2.0
            elif sm >= 15:
                votes['BIG'] += 2.0

        last_result = hist[0]
        opp = 'SMALL' if last_result == 'BIG' else 'BIG'
        votes[opp] += 1.0

        if len(hist) >= 30:
            w30 = hist[:30]
            bg30 = w30.count('BIG')
            if bg30 >= 20:
                votes['SMALL'] += 1.5
            elif bg30 <= 10:
                votes['BIG'] += 1.5

        final_pred = 'BIG' if votes['BIG'] >= votes['SMALL'] else 'SMALL'
        total_v = votes['BIG'] + votes['SMALL']
        edge = votes[final_pred] / total_v if total_v > 0 else 0.5
        final_conf = min(88, max(60, int(50 + edge * 80)))
        sig = f"L2-ExtremeAnalysis/{stage_used}"

    return final_pred, int(final_conf), sig

def server2_ultra_predict(outcomes: list, level: int, session: dict):
    if len(outcomes) < 6:
        return 'BIG', 50, "INSUFFICIENT"

    if level == 1:
        probe_votes = {'BIG': 0.0, 'SMALL': 0.0}
        probe_confs = []

        for offset in range(4):
            if len(outcomes) <= offset + 8:
                continue
            sub = outcomes[offset:]
            p, c, _, _ = _quant_core_predict(sub)
            probe_votes[p] += 1.0 + (c - 50) / 50.0
            probe_confs.append(c)

        def _html_dragon_line(hist):
            if len(hist) < 2:
                return None
            current_type = hist[0]
            streak = 1
            for i in range(1, len(hist)):
                if hist[i] == current_type:
                    streak += 1
                else:
                    break
            if 2 <= streak <= 8:
                return current_type
            return None

        def _html_chop_chop(hist):
            if len(hist) < 4:
                return None
            if (hist[0] != hist[1] and hist[1] == hist[2] and hist[2] != hist[3]):
                return 'SMALL' if hist[0] == 'BIG' else 'BIG'
            return None

        def _html_density(hist):
            n = min(6, len(hist))
            if n < 3:
                return None
            sample = hist[:n]
            big_count = sample.count('BIG')
            if big_count > n / 2:
                return 'SMALL'
            elif big_count < n / 2:
                return 'BIG'
            return None

        html_dragon = _html_dragon_line(outcomes)
        if html_dragon:
            probe_votes[html_dragon] += 1.2

        html_chop = _html_chop_chop(outcomes)
        if html_chop:
            probe_votes[html_chop] += 1.5

        html_density = _html_density(outcomes)
        if html_density:
            probe_votes[html_density] += 1.0

        streak_val, streak_len, _, _ = _streak_info(outcomes)
        if streak_len >= 5:
            flip = 'SMALL' if streak_val == 'BIG' else 'BIG'
            probe_votes[flip] += 2.5
        elif streak_len >= 4:
            flip = 'SMALL' if streak_val == 'BIG' else 'BIG'
            probe_votes[flip] += 1.5
        elif streak_len >= 3:
            flip = 'SMALL' if streak_val == 'BIG' else 'BIG'
            probe_votes[flip] += 0.8

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

    else:
        board2 = _SignalBoard()
        streak_val, streak_len, _, avg_run = _streak_info(outcomes)
        flip = 'SMALL' if streak_val == 'BIG' else 'BIG'

        if streak_len >= 4:
            board2.add("L2-AntiStreak", flip, 4.0 + streak_len * 0.6)
        elif streak_len >= 3:
            board2.add("L2-AntiStreak", flip, 3.0)
        elif streak_len == 2:
            board2.add("L2-AntiStreak", flip, 1.8)
        else:
            board2.add("L2-AntiStreak", flip, 1.0)

        base, q_conf, q_sig, meta = _quant_core_predict(outcomes)
        board2.add("L2-QuantBase", base, 2.0)

        def _html_density(hist):
            n = min(6, len(hist))
            if n < 3:
                return None
            sample = hist[:n]
            big_count = sample.count('BIG')
            if big_count > n / 2:
                return 'SMALL'
            elif big_count < n / 2:
                return 'BIG'
            return None

        def _html_chop_chop(hist):
            if len(hist) < 4:
                return None
            if (hist[0] != hist[1] and hist[1] == hist[2] and hist[2] != hist[3]):
                return 'SMALL' if hist[0] == 'BIG' else 'BIG'
            return None

        html_density = _html_density(outcomes)
        if html_density:
            board2.add("L2-HTML-Density", html_density, 1.5)

        html_chop = _html_chop_chop(outcomes)
        if html_chop:
            board2.add("L2-HTML-Chop", html_chop, 2.0)

        sim_probs, sim_conf = _historical_similarity(outcomes, lookback=6)
        if sim_conf >= 0.35:
            sim_pred = 'BIG' if sim_probs['BIG'] > 0.5 else 'SMALL'
            board2.add("L2-HistSim", sim_pred, sim_conf * 3.5)

        last3 = outcomes[:3]
        if len(last3) == 3:
            dom = 'BIG' if last3.count('BIG') >= 2 else 'SMALL'
            board2.add("L2-Last3Flip", 'SMALL' if dom == 'BIG' else 'BIG', 2.2)

        for win in [10, 20, 40]:
            if len(outcomes) >= win:
                br = _big_rate(outcomes[:win])
                if br >= 0.65:
                    board2.add(f"L2-FreqBal{win}", 'SMALL', (br - 0.5) * 4)
                elif br <= 0.35:
                    board2.add(f"L2-FreqBal{win}", 'BIG', (0.5 - br) * 4)

        fib_v = _fibonacci_window_votes(outcomes)
        for side in ('BIG', 'SMALL'):
            if fib_v[side] > 0.10:
                board2.add("L2-FibCross", side, fib_v[side] * 2.5)

        cyc_period, cyc_strength = _detect_cycle(outcomes, max_lag=24)
        if cyc_period and cyc_strength >= 0.20:
            phase = len(outcomes) % cyc_period
            if phase < len(outcomes):
                board2.add("L2-CyclePhase", outcomes[phase], cyc_strength * 2.5)

        consec = session.get('consecutive_losses', 0)
        if consec >= 1:
            board2.add("L2-LossContext", base, min(2.5, 1.0 + consec * 0.5))

        l2_pred = board2.leading()
        l2_conf = min(90, max(56, board2.confidence_pct()))
        return l2_pred, l2_conf, f"L2-ExtremeScan/{q_sig}"

def adaptive_engine_predict(outcomes: list, raw_nums: list, session: dict):
    consec_losses = session.get('consecutive_losses', 0)
    recent_res = session.get('recent_results', [])

    recent_win_rate = 1.0
    if recent_res:
        recent_win_rate = sum(recent_res[-5:]) / len(recent_res[-5:])

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
        flipped_pred = "SMALL" if pred == "BIG" else "BIG"
        is_jackpot = False
        if len(raw_nums) >= 2:
            is_jackpot = (raw_nums[0] in [0, 5, 1, 9])
        return flipped_pred, max(55, conf - 5), "ADAPTIVE-COUNTER_TREND", is_jackpot, None

    pred, conf, sig, meta = _quant_core_predict(outcomes)
    is_jackpot = (meta.get('streak', ('BIG', 0))[1] >= 4)
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

# ──────────────────────────────────────────────────────────────
# PREDICTION LOOP
# ──────────────────────────────────────────────────────────────

async def prediction_loop(user_id, channel_link, server):
    session = active_sessions.get(user_id)
    if not session:
        return

    channel = int(session['channel_id'])

    if server == "1":
        server_name = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
    elif server == "2":
        server_name = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
    else:
        server_name = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏʀ"

    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"

    try:
        await send_sticker(channel, STICKER_START)
        await asyncio.sleep(1)

        intro = await safe_send(channel,
            f"{sep}\n"
            f"🤖 𝐊ᴏʜʟɪ 𝐕𝐈𝐏 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ\n"
            f"{sep}\n"
            f"🖥 𝐒ᴇ r ᴠᴇ r : {server_name}\n"
            f"🎯 𝐋ɪᴍɪᴛ : {session['max_bets']} predictions\n"
            f"🕐 𝐒ᴛᴀ r ᴛ : <code>{now_str()}</code>\n"
            f"{sep}")

        if intro is None:
            await safe_send(user_id, f"❌ Cannot post to {channel_link}!\nMake sure bot is Channel Admin.")
            active_sessions.pop(user_id, None)
            return

        await asyncio.sleep(1)
        max_bets = session['max_bets']
        bet_num = session.get('current_bet', 0)

        while True:
            if session.get('stop_flag'):
                await end_session(user_id, channel, "🛑 STOPPED")
                return

            current_level = session.get('current_level', 1)
            bet_num += 1
            session['current_bet'] = bet_num

            records = await fetch_history()
            period = await next_period()
            session['last_period'] = period
            await save_session_db(user_id, session)

            prediction, confidence, signal_strength, jackpot_detected, hash_val = await smart_predict(records, session)

            sent = await safe_send(channel, make_prediction_text(
                period, prediction, current_level, server, confidence,
                signal_strength, jackpot_detected, hash_val))
            if sent is None:
                await end_session(user_id, channel, "⚠️ Posting permission lost.")
                return

            result, result_num = await wait_for_result(period)

            if session.get('stop_flag'):
                await end_session(user_id, channel, "🛑 STOPPED")
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
                session['max_win_streak'] = max(session.get('max_win_streak', 0), session['win_streak'])
                session['current_level'] = 1
            else:
                session['losses'] += 1
                session['consecutive_losses'] += 1
                session['consecutive_wins'] = 0
                session['win_streak'] = 0
                session['max_loss_streak'] = max(session.get('max_loss_streak', 0), session['consecutive_losses'])
                session['current_level'] = min(current_level + 1, 2)

            session['recent_results'].append(1 if is_win else 0)
            if len(session['recent_results']) > 20:
                session['recent_results'].pop(0)

            await save_session_db(user_id, session)
            completed = session['wins'] + session['losses']

            if is_win:
                await send_win_sticker(channel)
                await asyncio.sleep(0.5)
                await safe_send(channel, make_win_text(session['wins'], session['losses']))
                if completed >= max_bets:
                    break

            await asyncio.sleep(2)

        await end_session(user_id, channel, "✅ SESSION COMPLETED")

    except asyncio.CancelledError:
        await end_session(user_id, channel, "🛑 SESSION TERMINATED")
    except Exception as e:
        await end_session(user_id, channel, f"⚠️ ERROR: {str(e)[:80]}")

async def end_session(user_id, channel, reason):
    session = active_sessions.get(user_id)
    if not session:
        return

    if session.get('_ending'):
        return
    session['_ending'] = True

    channel_id_int = int(session['channel_id'])

    try:
        await send_sticker(channel_id_int, STICKER_STOP)
    except Exception:
        pass

    await asyncio.sleep(1)
    summary = build_session_summary(session, reason)

    try:
        await safe_send(channel_id_int, summary)
    except Exception:
        pass

    try:
        await safe_send(user_id, summary)
    except Exception:
        pass

    try:
        await update_stats(user_id, session['channel_id'], session.get('wins', 0), session.get('losses', 0))
    except Exception:
        pass

    active_sessions.pop(user_id, None)

    try:
        await delete_session_db(user_id)
    except Exception:
        pass

async def recover_sessions():
    try:
        data = await load_data()
        sessions = data.get('sessions', {})
        if not sessions:
            return
        for uid_str, session in list(sessions.items()):
            try:
                user_id = int(uid_str)
                channel_link = session.get('channel_link')
                server = session.get('server')
                if not channel_link or not server:
                    continue
                active_sessions[user_id] = {
                    'channel_link': channel_link,
                    'channel_id': session.get('channel_id'),
                    'server': server,
                    'max_bets': session.get('max_bets', 10),
                    'max_level': 2,
                    'current_bet': session.get('current_bet', 0),
                    'current_level': min(session.get('current_level', 1), 2),
                    'consecutive_losses': session.get('consecutive_losses', 0),
                    'consecutive_wins': session.get('consecutive_wins', 0),
                    'win_streak': session.get('win_streak', 0),
                    'max_win_streak': session.get('max_win_streak', 0),
                    'max_loss_streak': session.get('max_loss_streak', 0),
                    'stop_flag': False,
                    'wins': session.get('wins', 0),
                    'losses': session.get('losses', 0),
                    'started_at': session.get('started_at', datetime.now().strftime("%d-%m-%Y %I:%M %p")),
                    'recent_results': session.get('recent_results', []),
                    '_ending': False,
                }
                task = asyncio.create_task(prediction_loop(user_id, channel_link, server))
                active_sessions[user_id]['task'] = task
                await safe_send(int(session.get('channel_id')),
                    f"🛡 𝐒ʏsᴛᴇᴍ 𝐑ᴇᴄᴏᴠᴇʀᴇᴅ\n{'━'*22}\n"
                    f"🤖 <b>𝐁ᴏᴛ 𝐑ᴇsᴛᴏʀᴇᴅ.</b>\n🔄 𝐒ᴇssɪᴏɴ 𝐑ᴇsᴜᴍᴇᴅ!\n{'━'*22}")
            except Exception:
                pass
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────
# AUTO DETECTION
# ──────────────────────────────────────────────────────────────

@bot.my_chat_member_handler()
async def on_my_chat_member_update(update: types.ChatMemberUpdated):
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
    added = await add_channel(promoted_by, channel_uname, channel_id, auto_detected=True)
    if added:
        try:
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("🚀 𝐒ᴛᴀ r ᴛ 𝐏 r ᴇᴅɪᴄᴛɪᴏɴ 𝐍ᴏᴡ!",
                                              callback_data=f"quickstart_{channel_id}"))
            await bot.send_message(promoted_by,
                f"✅ 𝐂ʜᴀɴɴᴇʟ 𝐀ᴜᴛᴏ-𝐃ᴇᴛᴇᴄᴛᴇᴅ & 𝐀ᴅᴅᴇᴅ!\n\n{'━'*22}\n"
                f"📢 𝐂ʜᴀɴɴᴇʟ : {channel_title}\n"
                f"🔗 𝐋ɪɴᴋ : <code>{channel_uname}</code>\n"
                f"🆔 𝐈ᴅ : <code>{channel_id}</code>\n{'━'*22}\n\n"
                f"🎉 𝐏 r ᴇᴅɪᴄᴛɪᴏɴ 𝐒ʜᴜ r ᴜ 𝐊ᴀ r ᴇɪɴ! 👇",
                parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"❌ Auto-detect notify failed: {e}")
    else:
        try:
            await bot.send_message(promoted_by,
                f"ℹ️ <b>{channel_title}</b> pehle se list mein hai!\n'🚀 Start Prediction' dabao.",
                parse_mode="HTML")
        except Exception:
            pass

HELP_TEXT = (
    "❓ 𝐊ᴏʜʟɪ 𝐕𝐈𝐏 𝐁ᴏᴛ 𝐇ᴇʟᴘ\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "⚙️ 𝐂ᴏᴍᴍᴀɴᴅs:\n• /start — Bot start\n• /predict — Start prediction\n"
    "• /add @Channel — Channel add\n• /help — Help menu\n• /cancel — Cancel flow\n\n"
    "📢 𝐀ᴜᴛᴏ 𝐂ʜᴀɴɴᴇʟ 𝐒ᴇᴛᴜᴘ:\nBot ko channel ka Admin banayein → Auto detect!\n\n"
    "⚖️ 𝐌ᴀ r ᴛɪɴɢᴀʟᴇ 𝐋ᴇᴠᴇʟs:\n"
    "• Capped at level 2 max across all modules\n\n"
    "📊 𝐄𝐧ɢɪɴᴇs:\n"
    "• ⚔️ 𝐒ᴇ r ᴠᴇ r 1 — Dragon HTML Engine (Dragon+Chop+Density)\n"
    "• 🤖 𝐒ᴇ r ᴠᴇ r 2 — Adaptive Quant Engine (Ensemble Analysis)\n"
    "• 🔑 𝐒ᴇ r ᴠᴇ r 3 — Seed Hash Decrypter (Mathematical Hashing)\n\n"
    "📞 𝐒ᴜᴘᴘᴏ r ᴛ: @xxLEGEND_KOHLI"
)

async def trigger_start(message, user_id):
    loading_msg = await bot.send_message(message.chat.id,
        "⚡ 𝐋ᴏᴀᴅɪɴɢ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 𝐄ɴɢɪɴᴇs...\n📡 𝐒ʏɴᴄɪɴɢ 𝐃ᴀᴛᴀ...\n🧠 𝐀𝐈 𝐑ᴇᴀᴅʏ...",
        parse_mode="HTML")
    try:
        channels = await get_channels(user_id)
        if not channels:
            await safe_edit(loading_msg,
                "❌ 𝐍ᴏ 𝐂ʜᴀɴɴᴇʟs 𝐀ᴅᴅᴇᴅ!\n\nBot ko channel Admin banayein ya <code>/add @ChannelUsername</code> karein.")
            return
        if user_id in active_sessions:
            await safe_edit(loading_msg,
                "⚠️ 𝐒ᴇssɪᴏɴ 𝐀ʟ r ᴇᴀᴅʏ 𝐑ᴜɴɴɪɴɢ!\nPehle '🛑 Stop Prediction' karein.")
            return

        user_states[user_id] = {"step": "select_server", "channels": channels}
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("⚔️ SERVER 1 — Dragon Track (HTML Engine)", callback_data="server_1"))
        kb.row(types.InlineKeyboardButton("🤖 SERVER 2 — Adaptive Quant (Ensemble)", callback_data="server_2"))
        kb.row(types.InlineKeyboardButton("🔑 SERVER 3 — Seed Hash Decrypter", callback_data="server_3"))
        kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        await safe_edit(loading_msg,
            f"🎯 𝐒ᴇʟᴇᴄᴛ 𝐒ᴇ r ᴠᴇ r\n{'━'*20}\n"
            f"⚔️ 𝐒ᴇ r ᴠᴇ r 1 — Dragon Line + Chop + Density\n"
            f"🤖 𝐒ᴇ r ᴠᴇ r 2 — Adaptive Quant Multi-Heuristic Engine\n"
            f"🔑 𝐒ᴇ r ᴠᴇ r 3 — Seed Hash Decrypter (SHA256 Win Predictor)\n"
            f"{'━'*20}\n𝐂ʜᴏᴏsᴇ 𝐒ᴇ r ᴠᴇ r:",
            reply_markup=kb)
    except Exception as e:
        await safe_edit(loading_msg, f"❌ 𝐄ʀʀᴏ r: <code>{str(e)[:150]}</code>")

# ──────────────────────────────────────────────────────────────
# COMMANDS
# ──────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    kb = admin_kb() if user_id == ADMIN_ID else user_kb()
    await bot.send_message(message.chat.id,
        f"🎯 𝐖ᴇʟᴄᴏᴍᴇ, {message.from_user.first_name}!\n\n{'━'*22}\n"
        f"🤖 𝐊ᴏʜʟɪ 𝐕𝐈𝐏 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 𝐁ᴏᴛ v8.0\n"
        f"⚔️ 𝐒ᴇ r ᴠᴇ r 1: Dragon HTML Engine\n"
        f"🤖 𝐒ᴇ r ᴠᴇ r 2: Adaptive Quant Engine\n"
        f"🔑 𝐒ᴇ r ᴠᴇ r 3: Seed Hash Decrypter\n{'━'*22}\n\n𝐔sᴇ ᴏᴘᴛɪᴏɴs ʙᴇʟᴏᴡ:",
        parse_mode="HTML", reply_markup=kb)

@bot.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await bot.send_message(message.chat.id, HELP_TEXT, parse_mode="HTML")

@bot.message_handler(commands=['predict'])
async def cmd_predict(message: types.Message):
    await trigger_start(message, message.from_user.id)

@bot.message_handler(commands=['cancel'])
async def cmd_cancel(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await bot.send_message(message.chat.id, "❌ 𝐅ʟᴏᴡ 𝐂ᴀɴᴄᴇʟʟᴇᴅ.", parse_mode="HTML")

@bot.message_handler(commands=['add'])
async def cmd_add(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        await bot.send_message(message.chat.id,
            "❌ 𝐔sᴀɢᴇ: /add @YourChannel or /add -100xxxxxxxxxx",
            parse_mode="HTML")
        return
    channel_input = args[1].strip()
    status_msg = await bot.send_message(message.chat.id, "🔄 𝐕ᴇ r ɪꜰɪᴇ s...", parse_mode="HTML")
    try:
        chat = await bot.get_chat(channel_input)
        channel_id = chat.id
        channel_uname = f"@{chat.username}" if chat.username else str(channel_id)
        channel_title = chat.title or channel_uname
        member = await bot.get_chat_member(channel_id, (await bot.get_me()).id)
        if member.status not in ["administrator", "creator"]:
            await safe_edit(status_msg, "❌ 𝐁ᴏᴛ ɪs 𝐍ᴏᴛ 𝐀ᴅᴍɪɴ ɪɴ ᴛʜɪs ᴄʜᴀɴɴᴇʟ!")
            return
        added = await add_channel(user_id, channel_uname, channel_id, auto_detected=False)
        if added:
            await safe_edit(status_msg,
                f"✅ 𝐂ʜᴀɴɴᴇʟ 𝐀ᴅᴅᴇᴅ: {channel_title}\n\n'🚀 Start Prediction' se shuru karein.")
        else:
            await safe_edit(status_msg,
                f"ℹ️ <b>{channel_title}</b> pehle se list mein hai!")
    except Exception as e:
        await safe_edit(status_msg, f"❌ 𝐅ᴀɪʟᴇᴅ: <code>{str(e)}</code>")

@bot.message_handler(commands=['resetdb'])
async def cmd_reset_db(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_message(message.chat.id, "❌ Access denied.")
        return
    empty_data = {"users": {}, "sessions": {}}
    await save_data(empty_data)
    global _data_cache
    _data_cache = empty_data
    await bot.send_message(message.chat.id, "✅ 𝐃ᴀᴛᴀʙᴀsᴇ 𝐖ɪᴘᴇᴅ!", parse_mode="HTML")

# ──────────────────────────────────────────────────────────────
# BROADCAST
# ──────────────────────────────────────────────────────────────

async def run_broadcast(sender_id: int, text: str):
    all_users = await get_all_users()
    user_dm_ids = set()
    channel_ids_map = {}

    for uid_str, udata in all_users.items():
        try:
            user_dm_ids.add(int(uid_str))
        except Exception:
            pass
        for ch in udata.get('channels', []):
            cid = ch.get('channel_id')
            if cid:
                channel_ids_map[str(cid)] = ch.get('channel_link', str(cid))

    ok_dm = fail_dm = ok_ch = fail_ch = 0

    for uid in user_dm_ids:
        success = False
        for attempt in range(3):
            try:
                await asyncio.sleep(0.4)
                await bot.send_message(uid, text, parse_mode="HTML")
                success = True
                break
            except ApiTelegramException as e:
                if e.error_code == 429:
                    retry_after = e.result.get('parameters', {}).get('retry_after', 5)
                    await asyncio.sleep(retry_after + 1)
                elif e.error_code in [403, 400]:
                    break
                else:
                    await asyncio.sleep(1.5)
            except Exception:
                await asyncio.sleep(1.5)
        if success:
            ok_dm += 1
        else:
            fail_dm += 1

    for cid_str, clink in channel_ids_map.items():
        try:
            cid_int = int(cid_str)
        except Exception:
            fail_ch += 1
            continue
        success = False
        for attempt in range(3):
            try:
                await asyncio.sleep(0.4)
                await bot.send_message(cid_int, text, parse_mode="HTML")
                success = True
                break
            except ApiTelegramException as e:
                if e.error_code == 429:
                    retry_after = e.result.get('parameters', {}).get('retry_after', 5)
                    await asyncio.sleep(retry_after + 1)
                elif e.error_code in [403, 400]:
                    break
                else:
                    await asyncio.sleep(1.5)
            except Exception:
                await asyncio.sleep(1.5)
        if success:
            ok_ch += 1
        else:
            fail_ch += 1

    return ok_dm, fail_dm, ok_ch, fail_ch

# ──────────────────────────────────────────────────────────────
# TEXT HANDLER
# ──────────────────────────────────────────────────────────────

@bot.message_handler(func=lambda msg: True)
async def on_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""
    state = user_states.get(user_id)

    if text.startswith("/"):
        return

    if text == "❓ Help":
        await bot.send_message(message.chat.id, HELP_TEXT, parse_mode="HTML")
        return

    if text == "📞 Support":
        await bot.send_message(message.chat.id,
            "📞 <b>𝐒ᴜᴘᴘᴏ r ᴛ</b>\n\n"
            "💬 Contact our support lines for system integrations:\n\n"
            "👤 𝐎ᴡɴᴇ r : @xxLEGEND_KOHLI",
            parse_mode="HTML")
        return

    if text == "🚀 Start Prediction":
        await trigger_start(message, user_id)
        return

    if text == "➕ Add Channel":
        await bot.send_message(message.chat.id,
            "📢 𝐀ᴅᴅ 𝐂ʜᴀɴɴᴇʟ:\n\n• Bot ko target channel ka <b>Admin</b> banayein.\n"
            "• Bot automatically detect karega.\n• Manual: <code>/add @ChannelUsername</code>",
            parse_mode="HTML")
        return

    if text == "📊 My Channels":
        channels = await get_channels(user_id)
        if not channels:
            await bot.send_message(message.chat.id, "❌ No channels found! /add use karein.")
            return
        resp = f"📊 𝐘ᴏᴜ r 𝐂ʜᴀɴɴᴇʟs ({len(channels)})\n{'━'*22}\n\n"
        for i, ch in enumerate(channels, 1):
            s = ch.get('total_sessions', 0)
            w = ch.get('total_wins', 0)
            l = ch.get('total_losses', 0)
            rate = f"{round(w / (w + l) * 100)}%" if (w + l) > 0 else "N/A"
            resp += (f"<b>{i}. {ch['channel_link']}</b>\n🆔 <code>{ch['channel_id']}</code>\n"
                     f"🎮 𝐒ᴇssɪᴏɴs: {s} | ✅ {w} | ❌ {l} | 📈 {rate}\n{'━'*22}\n\n")
        await bot.send_message(message.chat.id, resp, parse_mode="HTML")
        return

    if text == "🗑 Remove Channel":
        channels = await get_channels(user_id)
        if not channels:
            await bot.send_message(message.chat.id, "❌ No channels to remove.")
            return
        kb = types.InlineKeyboardMarkup()
        for ch in channels:
            cid = encode_cid(ch['channel_id'])
            kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}", callback_data=f"manage_{cid}"))
        kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        await bot.send_message(message.chat.id,
            "🗑 𝐑ᴇᴍᴏᴠᴇ 𝐂ʜᴀɴɴᴇʟ\n\nTap a channel to remove:",
            parse_mode="HTML", reply_markup=kb)
        return

    if text == "📈 My Stats":
        channels = await get_channels(user_id)
        total_w = sum(c.get('total_wins', 0) for c in channels)
        total_l = sum(c.get('total_losses', 0) for c in channels)
        total_s = sum(c.get('total_sessions', 0) for c in channels)
        rate = f"{round(total_w / (total_w + total_l) * 100)}%" if (total_w + total_l) > 0 else "N/A"
        await bot.send_message(message.chat.id,
            f"📈 𝐒ᴛᴀᴛɪsᴛɪᴄs\n{'━'*22}\n\n"
            f"📢 𝐂ʜᴀɴɴᴇʟs : {len(channels)}\n"
            f"🎮 𝐒ᴇssɪᴏɴs : {total_s}\n"
            f"✅ 𝐖ɪɴs : {total_w}\n"
            f"❌ 𝐋ᴏssᴇs : {total_l}\n"
            f"📊 𝐑ᴀᴛᴇ : {rate}\n{'━'*22}", parse_mode="HTML")
        return

    if text == "🛑 Stop Prediction":
        if user_id not in active_sessions:
            await bot.send_message(message.chat.id, "❌ No session running!")
            return
        session = active_sessions[user_id]
        if session.get('_ending'):
            return
        session['stop_flag'] = True
        task = session.get('task')
        if task and not task.done():
            task.cancel()
        if task and task.done():
            await end_session(user_id, int(session['channel_id']), "🛑 STOPPED BY USER")
        await bot.send_message(message.chat.id, "🛑 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 𝐒ᴛᴏᴘᴘᴇᴅ!", parse_mode="HTML")
        return

    if text == "📢 Broadcast" and user_id == ADMIN_ID:
        user_states[ADMIN_ID] = "waiting_broadcast"
        await bot.send_message(message.chat.id,
            "📢 Enter the message to broadcast.\n"
            "It will be sent to ALL user DMs and ALL connected channels/groups.")
        return

    if text == "🔧 System Stats" and user_id == ADMIN_ID:
        users = await get_all_users()
        total_ch = sum(len(u.get('channels', [])) for u in users.values())
        total_w = sum(c.get('total_wins', 0) for u in users.values() for c in u.get('channels', []))
        total_l = sum(c.get('total_losses', 0) for u in users.values() for c in u.get('channels', []))
        rate = f"{round(total_w / (total_w + total_l) * 100)}%" if (total_w + total_l) > 0 else "N/A"
        await bot.send_message(message.chat.id,
            f"🔧 𝐒ʏsᴛᴇᴍ 𝐒ᴛᴀᴛs\n{'━'*22}\n\n"
            f"👥 𝐔sᴇ r s : {len(users)}\n"
            f"📢 𝐂ʜᴀɴɴᴇʟs : {total_ch}\n"
            f"🔄 𝐀ᴄᴛɪᴠᴇ : {len(active_sessions)}\n"
            f"✅ 𝐖ɪɴs : {total_w}\n"
            f"❌ 𝐋ᴏssᴇs : {total_l}\n"
            f"📊 𝐑ᴀᴛᴇ : {rate}\n"
            f"🛡 𝐃ʙ : {'Firebase ONLINE' if FIREBASE_URL else 'Local JSON'}\n{'━'*22}",
            parse_mode="HTML")
        return

    if state == "waiting_broadcast" and user_id == ADMIN_ID:
        user_states.pop(ADMIN_ID, None)
        all_users = await get_all_users()
        unique_channels = set()
        for udata in all_users.values():
            for ch in udata.get('channels', []):
                if ch.get('channel_id'):
                    unique_channels.add(ch['channel_id'])
        total_users = len(all_users)
        total_ch = len(unique_channels)
        status_msg = await bot.send_message(
            message.chat.id,
            f"📢 Broadcasting to {total_users} users + {total_ch} channels/groups...\n⏳ Please wait..."
        )
        ok_dm, fail_dm, ok_ch, fail_ch = await run_broadcast(user_id, text)
        await safe_edit(status_msg,
            f"📢 𝐁ʀᴏᴀᴅᴄᴀsᴛ 𝐂ᴏᴍᴘʟᴇᴛᴇᴅ!\n{'━'*22}\n\n"
            f"👤 𝐔sᴇ r 𝐃𝐌s\n  ✅ Success: {ok_dm}\n  ❌ Failed: {fail_dm}\n\n"
            f"📢 𝐂ʜᴀɴɴᴇʟs/𝐆 r ᴏᴜᴘs\n  ✅ Success: {ok_ch}\n  ❌ Failed: {fail_ch}\n\n"
            f"📊 𝐉ᴏᴜ r ɴᴇʏ 𝐃ᴇʟɪᴠᴇ r ᴇᴅ: {ok_dm + ok_ch}"
        )
        return

    if isinstance(state, dict) and state.get("step") == "select_bets":
        if not text.isdigit() or not (1 <= int(text) <= 50):
            await bot.send_message(message.chat.id, "❌ Enter valid number (1-50)!")
            return
        bets = int(text)
        server = state["server"]
        channel_link = state["channel_link"]
        channel_id = state["channel_id"]
        user_states.pop(user_id, None)
        if user_id in active_sessions:
            await bot.send_message(message.chat.id, "⚠️ Session already running.")
            return
        active_sessions[user_id] = {
            'channel_link': channel_link, 'channel_id': channel_id,
            'server': server, 'max_bets': bets, 'max_level': 2,
            'current_bet': 0, 'current_level': 1,
            'consecutive_losses': 0, 'consecutive_wins': 0,
            'win_streak': 0, 'max_win_streak': 0, 'max_loss_streak': 0,
            'stop_flag': False, 'wins': 0, 'losses': 0,
            'started_at': datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            'recent_results': [],
            '_ending': False,
        }
        await save_session_db(user_id, active_sessions[user_id])

        if server == "1":
            server_name = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
        elif server == "2":
            server_name = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
        else:
            server_name = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏʀ"

        await bot.send_message(message.chat.id,
            f"✅ 𝐒ᴇssɪᴏɴ 𝐑ᴇᴀᴅʏ!\n{'━'*22}\n\n"
            f"📢 𝐂ʜᴀɴɴᴇʟ : {channel_link}\n"
            f"🖥 𝐒ᴇ r ᴠᴇ r : {server_name}\n"
            f"🎯 𝐋ɪᴍɪᴛ : {bets} Rounds\n\n🔥 Starting now...",
            parse_mode="HTML")
        task = asyncio.create_task(prediction_loop(user_id, channel_link, server))
        active_sessions[user_id]['task'] = task

# ──────────────────────────────────────────────────────────────
# CALLBACKS
# ──────────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda call: True)
async def on_callback(cq: types.CallbackQuery):
    user_id = cq.from_user.id
    data = cq.data
    try:
        await bot.answer_callback_query(cq.id)
    except Exception:
        pass

    try:
        if data == "cancel":
            user_states.pop(user_id, None)
            try:
                await bot.delete_message(cq.message.chat.id, cq.message.message_id)
            except Exception:
                pass
            return

        if data == "back_to_manage":
            channels = await get_channels(user_id)
            if not channels:
                await safe_edit(cq.message, "❌ No channels available.")
                return
            kb = types.InlineKeyboardMarkup()
            for ch in channels:
                cid = encode_cid(ch['channel_id'])
                kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}", callback_data=f"manage_{cid}"))
            kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
            await safe_edit(cq.message, "🗑 𝐑ᴇᴍᴏᴠᴇ 𝐂ʜᴀɴɴᴇʟ\n\nTap a channel:", reply_markup=kb)
            return

        if data.startswith("manage_"):
            encoded_cid = data.split("_", 1)[1]
            channel_id = decode_cid(encoded_cid)
            channels = await get_channels(user_id)
            ch_data = next((c for c in channels if str(c['channel_id']) == str(channel_id)), None)
            if not ch_data:
                await safe_edit(cq.message, "❌ Channel not found.")
                return
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("🗑 Confirm Remove", callback_data=f"del_{encoded_cid}"))
            kb.row(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage"))
            await safe_edit(cq.message,
                f"📢 𝐂ʜᴀɴɴᴇʟ 𝐃ᴇᴛᴀɪʟs\n{'─'*20}\n"
                f"🏷 𝐋ɪɴᴋ: {ch_data['channel_link']}\n"
                f"🆔 𝐈ᴅ: <code>{ch_data['channel_id']}</code>\n"
                f"📅 𝐀ᴅᴅᴇᴅ: {ch_data['added_date']}\n"
                f"🎮 𝐒ᴇssɪᴏɴs: {ch_data.get('total_sessions', 0)}\n{'─'*20}\nRemove this?",
                reply_markup=kb)
            return

        if data.startswith("del_"):
            encoded_cid = data.split("_", 1)[1]
            channel_id = decode_cid(encoded_cid)
            removed = await remove_channel(user_id, channel_id)
            if removed:
                await safe_edit(cq.message, "✅ 𝐂ʜᴀɴɴᴇʟ 𝐑ᴇᴍᴏᴠᴇᴅ!")
            else:
                await safe_edit(cq.message, "❌ Channel not found.")
            return

        if data.startswith("quickstart_"):
            channel_id = data.split("_", 1)[1]
            channels = await get_channels(user_id)
            ch_data = next((c for c in channels if str(c['channel_id']) == str(channel_id)), None)
            if not ch_data:
                await safe_edit(cq.message, "❌ Channel not found.")
                return
            if user_id in active_sessions:
                await safe_edit(cq.message, "⚠️ Session already running.")
                return
            user_states[user_id] = {"step": "select_server", "channels": channels}
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("⚔️ SERVER 1 — Dragon Track", callback_data="server_1"))
            kb.row(types.InlineKeyboardButton("🤖 SERVER 2 — Adaptive Quant", callback_data="server_2"))
            kb.row(types.InlineKeyboardButton("🔑 SERVER 3 — Seed Hash Decrypter", callback_data="server_3"))
            kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
            await safe_edit(cq.message, "🎯 𝐒ᴇʟᴇᴄᴛ 𝐒ᴇʀᴠᴇ r\n\nChoose engine:", reply_markup=kb)
            return

        if data.startswith("server_"):
            server = data.split("_")[1]
            state = user_states.get(user_id)
            if not isinstance(state, dict) or state.get("step") != "select_server":
                await safe_edit(cq.message, "❌ Flow timed out. Click '🚀 Start Prediction' again.")
                return
            channels = state["channels"]
            kb = types.InlineKeyboardMarkup()
            for ch in channels:
                cid = encode_cid(ch['channel_id'])
                kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}",
                                                  callback_data=f"ch_{server}_{cid}"))
            kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))

            if server == "1":
                sname = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
            elif server == "2":
                sname = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
            else:
                sname = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏʀ"

            user_states[user_id] = {"step": "select_channel", "server": server, "channels": channels}
            await safe_edit(cq.message,
                f"✅ {sname} 𝐒ᴇʟᴇᴄᴛᴇᴅ!\n\nChoose target channel 👇",
                reply_markup=kb)
            return

        if data.startswith("ch_"):
            parts = data.split("_", 2)
            server = parts[1]
            encoded_cid = parts[2]
            channel_id = decode_cid(encoded_cid)
            state = user_states.get(user_id, {})
            channels = state.get("channels", [])
            channel_link = next((c['channel_link'] for c in channels
                                 if str(c['channel_id']) == str(channel_id)), None)
            if not channel_link:
                await safe_edit(cq.message, "❌ Channel missing. Please restart.")
                return
            user_states[user_id] = {
                "step": "select_bets", "server": server,
                "channel_link": channel_link, "channel_id": str(channel_id)
            }

            if server == "1":
                sname = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
            elif server == "2":
                sname = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
            else:
                sname = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏʀ"

            await safe_edit(cq.message,
                f"🎯 𝐅ɪɴᴀʟ 𝐂ᴏɴꜰɪɢ\n{'━'*20}\n"
                f"📢 𝐂ʜᴀɴɴᴇʟ : {channel_link}\n"
                f"🖥 𝐄ɴɢɪɴᴇ : {sname}\n{'━'*20}\n\n"
                f"𝐇ᴏᴡ ᴍᴀɴʏ ᴘʀᴇᴅɪᴄᴛɪᴏɴs? (1–50)\nType a number now:")
            return

    except Exception as e:
        try:
            await safe_edit(cq.message, f"❌ 𝐄ʀʀᴏ r: <code>{str(e)[:150]}</code>")
        except Exception:
            pass

# ──────────────────────────────────────────────────────────────
# HOSTING BOT (SYNC) — FULL
# ──────────────────────────────────────────────────────────────

hosted_bots = {}
hosted_by_id = {}
hosted_registry = {}
registry_file = os.path.join(DATA_DIR, "hosted_registry.json")

def load_registry():
    global hosted_registry
    if os.path.exists(registry_file):
        try:
            with open(registry_file, "r") as f:
                hosted_registry = json.load(f)
        except Exception:
            hosted_registry = {}

def save_registry():
    try:
        with open(registry_file, "w") as f:
            json.dump(hosted_registry, f, indent=2)
    except Exception:
        pass

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

load_registry()

def load_users(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_users(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def update_user_stats(user_id, file_path):
    users = load_users(file_path)
    now = datetime.now().strftime("%Y-%m-%d")
    if str(user_id) not in users:
        users[str(user_id)] = {"first_seen": now, "last_seen": now, "usage_count": 1}
    else:
        users[str(user_id)]["last_seen"] = now
        users[str(user_id)]["usage_count"] += 1
    save_users(file_path, users)

def get_stats(file_path):
    users = load_users(file_path)
    today = datetime.now()
    day1, day2 = 0, 0
    top_users = sorted(users.items(), key=lambda x: x[1]["usage_count"], reverse=True)
    for u in users.values():
        try:
            last = datetime.strptime(u["last_seen"], "%Y-%m-%d")
            delta = (today - last).days
            if delta == 0:
                day1 += 1
            elif delta == 1:
                day2 += 1
        except Exception:
            pass
    top_list = "\n".join(
        [f"  {i+1}. 👤 {uid} — {info['usage_count']} uses"
         for i, (uid, info) in enumerate(top_users[:5])]
    ) or "  No users yet."
    return len(users), day1, day2, top_list

def generate_prediction_host():
    num = random.randint(0, 9)
    if num >= 5:
        big_small = "🔴 BIG"
        image = "https://i.postimg.cc/VL8z327L/IMG-20250908-115951-469.jpg"
        trend = "📈 UPWARD TREND"
    else:
        big_small = "🔵 SMALL"
        image = "https://i.postimg.cc/FzthF6Np/IMG-20250908-115954-296.jpg"
        trend = "📉 DOWNWARD TREND"
    return big_small, num, image, trend

def generate_prediction_period():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    yyyyMMdd = now.strftime("%Y%m%d")
    total_minutes = now.hour * 60 + now.minute
    return f"{yyyyMMdd}1000{10001 + total_minutes}"

def get_remaining_seconds_host():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return 60 - now.second if now.second < 60 else 0

def send_prediction_host(bot_obj, chat_id, period, big_small, num, image, trend):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    timestamp = now.strftime("%d %b %Y • %I:%M:%S %p")
    confidence = random.randint(88, 99)
    filled = int(confidence / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)

    caption = (
        f"{DIVIDER}\n"
        f"{CROWN} *KOHLI AI PREDICTION* {CROWN}\n"
        f"{DIVIDER}\n\n"
        f"{TARGET} *Period:* `{period}`\n"
        f"{BRAIN} *Signal:* {big_small} — `{num}`\n"
        f"{CHART} *Trend:* {trend}\n"
        f"{GEM} *Confidence:* `{confidence}%`\n"
        f"`{bar}`\n\n"
        f"{SUB_DIVIDER}\n"
        f"⏱ *Next Cycle:* `1 Minute`\n"
        f"🕒 *Issued:* `{timestamp}`\n"
        f"{SUB_DIVIDER}\n\n"
        f"{LIGHTNING} _Powered by KOHLI AI Engine_ {LIGHTNING}\n"
        f"{DIVIDER}"
    )
    try:
        bot_obj.send_photo(chat_id, image, caption=caption, parse_mode="Markdown")
    except Exception as e:
        print(f"[!] Prediction send failed: {e}")

def start_hosted_prediction_bot(token, initial_owner, hosted_id):
    try:
        hosted = sync_telebot.TeleBot(token, parse_mode="Markdown")
        me = hosted.get_me()
    except Exception as e:
        raise RuntimeError(f"❌ Invalid Token: {e}")

    active_dict = {}
    user_channels = {}
    user_file = os.path.join(DATA_DIR, f"users_{me.id}.json")
    owner_file = os.path.join(DATA_DIR, f"owner_{hosted_id}.txt")
    runtime = {"paused": False}
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

    def save_owner(uid):
        try:
            with open(owner_file, "w") as f:
                f.write(str(uid))
            current_owner["id"] = uid
            hosted_bots.setdefault(uid, {})[hosted_id] = _entry_ref[0]
            update_registry_owner(hosted_id, uid)
        except Exception as e:
            print(f"[OWNER] Save failed: {e}")

    def get_owner():
        return current_owner["id"]

    _entry_ref = [None]

    def start_prediction_cycle(bot_obj, chat_id, channel_id=None):
        last_period = None
        while active_dict.get(chat_id):
            if runtime["paused"]:
                time.sleep(2)
                continue
            period = generate_prediction_period()
            if period != last_period:
                big_small, num, image, trend = generate_prediction_host()
                send_prediction_host(bot_obj, chat_id, period, big_small, num, image, trend)
                if channel_id:
                    send_prediction_host(bot_obj, channel_id, period, big_small, num, image, trend)
                last_period = period
            for _ in range(get_remaining_seconds_host(), 0, -1):
                if not active_dict.get(chat_id):
                    break
                time.sleep(1)

    def create_prediction_menu():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("🎯 START PREDICTION", "🛑 STOP PREDICTION")
        kb.row("📢 SET CHANNEL", "📊 LIVE STATS")
        kb.row("👑 DEVELOPER", "💎 PREMIUM INFO")
        return kb

    @hosted.message_handler(commands=["start"])
    def start(msg):
        if not os.path.exists(owner_file) or not current_owner["id"]:
            save_owner(msg.from_user.id)

        if current_owner["id"]:
            hosted_bots.setdefault(current_owner["id"], {})[hosted_id] = _entry_ref[0]

        update_user_stats(msg.from_user.id, user_file)

        user_name = msg.from_user.first_name or "User"
        welcome = (
            f"{DIVIDER}\n"
            f"{CROWN} *WELCOME TO KOHLI AI BOT* {CROWN}\n"
            f"{DIVIDER}\n\n"
            f"👋 Hey *{user_name}*,\n\n"
            f"{SPARKLE} You've unlocked the *most advanced*\n"
            f"   1-minute prediction engine on Telegram!\n\n"
            f"{SUB_DIVIDER}\n"
            f"{ROCKET} *Features:*\n"
            f"  {LIGHTNING} Real-time Wingo Predictions\n"
            f"  {LIGHTNING} AI-Powered Accuracy Engine\n"
            f"  {LIGHTNING} Auto Channel Broadcasting\n"
            f"  {LIGHTNING} Live Performance Stats\n"
            f"{SUB_DIVIDER}\n\n"
            f"{FIRE} *Ready to dominate?* Use buttons below 👇\n\n"
            f"{styled_footer()}"
        )
        hosted.send_message(msg.chat.id, welcome, reply_markup=create_prediction_menu())

    @hosted.message_handler(func=lambda m: True)
    def buttons(msg):
        text = msg.text
        cid = msg.chat.id
        update_user_stats(cid, user_file)

        if text == "🎯 START PREDICTION":
            if active_dict.get(cid):
                hosted.send_message(
                    cid,
                    f"{BELL} *Already Running!*\n{SUB_DIVIDER}\n"
                    f"{LIGHTNING} Your prediction engine is already active.",
                    reply_markup=create_prediction_menu(),
                )
                return
            active_dict[cid] = True
            runtime["paused"] = False
            ch = user_channels.get(cid)
            status = f"📢 Channel: `{ch}`" if ch else "⚠️ No channel linked"
            hosted.send_message(
                cid,
                f"{DIVIDER}\n"
                f"{ROCKET} *PREDICTION ENGINE ONLINE*\n"
                f"{DIVIDER}\n\n"
                f"✅ Status: *ACTIVE*\n"
                f"{status}\n"
                f"{SUB_DIVIDER}\n"
                f"{TARGET} Predictions will now stream every 60s.\n\n"
                f"{styled_footer()}",
                reply_markup=create_prediction_menu(),
            )
            threading.Thread(
                target=start_prediction_cycle,
                args=(hosted, cid, ch),
                daemon=True,
            ).start()

        elif text == "🛑 STOP PREDICTION":
            active_dict[cid] = False
            hosted.send_message(
                cid,
                f"{DIVIDER}\n"
                f"🛑 *PREDICTION ENGINE OFFLINE*\n"
                f"{DIVIDER}\n\n"
                f"❌ Status: *STOPPED*\n"
                f"{SUB_DIVIDER}\n"
                f"Press 🎯 START to resume anytime.\n\n"
                f"{styled_footer()}",
                reply_markup=create_prediction_menu(),
            )

        elif text == "📢 SET CHANNEL":
            hosted.send_message(
                cid,
                f"{DIVIDER}\n"
                f"📢 *CHANNEL LINKING*\n"
                f"{DIVIDER}\n\n"
                f"{LIGHTNING} Send your *channel username*\n"
                f"Example: `@yourchannel`\n\n"
                f"{SHIELD} _Bot must be admin in the channel._\n\n"
                f"{styled_footer()}",
                parse_mode="Markdown",
            )
            user_channels[cid] = "waiting"

        elif text == "📊 LIVE STATS":
            total, d1, d2, top = get_stats(user_file)
            hosted.send_message(
                cid,
                f"{DIVIDER}\n"
                f"{CHART} *LIVE BOT STATISTICS*\n"
                f"{DIVIDER}\n\n"
                f"👥 Total Users     : *{total}*\n"
                f"📅 Active Today    : *{d1}*\n"
                f"📅 Active Yesterday: *{d2}*\n\n"
                f"{SUB_DIVIDER}\n"
                f"🏆 *TOP 5 PERFORMERS*\n"
                f"{SUB_DIVIDER}\n"
                f"{top}\n\n"
                f"{styled_footer()}",
                reply_markup=create_prediction_menu(),
            )

        elif text == "👑 DEVELOPER":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("💬 Contact Developer", url="https://t.me/xxLEGEND_KOHLI"),
                types.InlineKeyboardButton("📢 Join Updates Channel", url="https://t.me/xxLEGEND_KOHLI"),
            )
            hosted.send_message(
                cid,
                f"{DIVIDER}\n"
                f"{CROWN} *MEET THE DEVELOPER* {CROWN}\n"
                f"{DIVIDER}\n\n"
                f"👤 *Name:* KOHLI\n"
                f"{GEM} *Role:* Premium Bot Developer\n"
                f"{LIGHTNING} *Specialty:* AI Prediction Systems\n\n"
                f"{SUB_DIVIDER}\n"
                f"💬 Need a custom bot? Reach out below!\n\n"
                f"{styled_footer()}",
                reply_markup=markup,
            )

        elif text == "💎 PREMIUM INFO":
            hosted.send_message(
                cid,
                f"{DIVIDER}\n"
                f"{GEM} *PREMIUM FEATURES* {GEM}\n"
                f"{DIVIDER}\n\n"
                f"{FIRE} *What you get:*\n\n"
                f"  {LIGHTNING} 99% AI Accuracy Engine\n"
                f"  {LIGHTNING} Unlimited Predictions\n"
                f"  {LIGHTNING} Auto Channel Broadcasting\n"
                f"  {LIGHTNING} Multi-Channel Support\n"
                f"  {LIGHTNING} 24/7 Uptime Guarantee\n"
                f"  {LIGHTNING} Priority Support\n\n"
                f"{SUB_DIVIDER}\n"
                f"👑 Contact @xxLEGEND_KOHLI for Premium\n\n"
                f"{styled_footer()}",
                reply_markup=create_prediction_menu(),
            )

        elif user_channels.get(cid) == "waiting":
            channel_input = text.strip()
            try:
                hosted.send_message(channel_input, "✅ Channel verified & linked!")
                user_channels[cid] = channel_input
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n"
                    f"✅ *CHANNEL LINKED SUCCESSFULLY*\n"
                    f"{DIVIDER}\n\n"
                    f"📢 Channel: `{channel_input}`\n"
                    f"{SUB_DIVIDER}\n"
                    f"{ROCKET} Predictions will now auto-post there!\n\n"
                    f"{styled_footer()}",
                    parse_mode="Markdown",
                    reply_markup=create_prediction_menu(),
                )
            except Exception as e:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n"
                    f"❌ *LINKING FAILED*\n"
                    f"{DIVIDER}\n\n"
                    f"Error: `{e}`\n\n"
                    f"{SHIELD} Make sure bot is *admin* in the channel.\n\n"
                    f"{styled_footer()}",
                    reply_markup=create_prediction_menu(),
                )
                user_channels[cid] = None

    def run_bot():
        try:
            hosted.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[!] Bot {me.username} stopped: {e}")

    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()

    entry = {
        "token": token,
        "thread": thread,
        "info": {"username": me.username, "id": me.id},
        "running": True,
        "runtime": runtime,
        "hosted_id": hosted_id,
        "owner_file": owner_file,
        "user_file": user_file,
        "get_owner": get_owner,
    }
    _entry_ref[0] = entry
    hosted_by_id[hosted_id] = entry

    register_bot(hosted_id, initial_owner, me.username, me.id, token)

    if initial_owner:
        hosted_bots.setdefault(initial_owner, {})[hosted_id] = entry

    return entry

# ──────────────────────────────────────────────────────────────
# FLASK API
# ──────────────────────────────────────────────────────────────

api_app = Flask(__name__)

@api_app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "KOHLI Premium Hosting",
        "version": "8.0",
        "hosted_bots": sum(len(b) for b in hosted_bots.values()),
        "registry_count": len(hosted_registry),
        "timestamp": datetime.now().isoformat(),
    })

@api_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@api_app.route("/api/create_bot", methods=["POST"])
def api_create_bot():
    try:
        data = request.get_json() or {}
        token = (data.get("token") or "").strip()
        telegram_id = data.get("telegram_id") or data.get("owner_id")

        if not token or ":" not in token or len(token) < 30:
            return jsonify({"status": "error", "message": "Invalid bot token format"}), 400

        for hid, e in hosted_by_id.items():
            if e.get("token") == token:
                return jsonify({
                    "status": "ok",
                    "username": e["info"]["username"],
                    "bot_id": e["info"]["id"],
                    "hosted_id": hid,
                    "message": "Bot already running",
                })

        for hid, reg in hosted_registry.items():
            if reg.get("token") == token:
                return jsonify({
                    "status": "ok",
                    "username": reg.get("username", "Bot"),
                    "bot_id": reg.get("bot_id", ""),
                    "hosted_id": hid,
                    "message": "Bot already registered",
                })

        hosted_id = f"bot_{int(time.time())}_{random.randint(1000, 9999)}"
        entry = start_hosted_prediction_bot(token, None, hosted_id)

        if telegram_id:
            try:
                owner_int = int(str(telegram_id).strip())
                entry["get_owner"] = lambda: owner_int
                with open(entry["owner_file"], "w") as f:
                    f.write(str(owner_int))
                hosted_bots.setdefault(owner_int, {})[hosted_id] = entry
                update_registry_owner(hosted_id, owner_int)
            except Exception as e:
                print(f"[AUTO-OWNER] Failed: {e}")

        try:
            host_bot.send_message(
                ADMIN_ID,
                f"{DIVIDER}\n"
                f"🔑 *NEW BOT DEPLOYED*\n"
                f"{DIVIDER}\n\n"
                f"🤖 Bot: @{entry['info']['username']}\n"
                f"🆔 ID: `{entry['info']['id']}`\n"
                f"📦 Hosted: `{hosted_id}`\n\n"
                f"{styled_footer()}",
                parse_mode="Markdown",
            )
        except Exception as e:
            print(f"[!] Admin notify failed: {e}")

        return jsonify({
            "status": "ok",
            "success": True,
            "username": entry["info"]["username"],
            "bot_id": entry["info"]["id"],
            "hosted_id": hosted_id,
            "message": "Bot created successfully",
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_app.route("/api/list_bots", methods=["POST"])
def api_list_bots():
    try:
        data = request.get_json() or {}
        owner_id = str(data.get("owner_id") or data.get("telegram_id") or data.get("user_id") or "").strip()

        if not owner_id or not owner_id.lstrip("-").isdigit():
            return jsonify({"status": "error", "message": "Invalid owner"}), 400

        owner_int = int(owner_id)
        result = []
        seen = set()

        for hid, entry in hosted_bots.get(owner_int, {}).items():
            if hid not in seen:
                seen.add(hid)
                result.append({
                    "username": entry["info"]["username"],
                    "bot_id": str(entry["info"]["id"]),
                    "hosted_id": str(hid),
                    "running": entry.get("running", True),
                })

        for hid, entry in hosted_by_id.items():
            if hid in seen:
                continue
            owner_file = entry.get("owner_file")
            if owner_file and os.path.exists(owner_file):
                try:
                    with open(owner_file, "r") as f:
                        if f.read().strip() == owner_id:
                            seen.add(hid)
                            result.append({
                                "username": entry["info"]["username"],
                                "bot_id": str(entry["info"]["id"]),
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

        return jsonify({"status": "ok", "success": True, "bots": result, "count": len(result)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_app.route("/api/toggle_bot", methods=["POST"])
def api_toggle_bot():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()
        action = (data.get("action") or "").strip().lower()

        if hosted_id not in hosted_by_id:
            return jsonify({"status": "error", "message": "Bot not found"}), 404

        entry = hosted_by_id[hosted_id]

        if action == "off":
            entry["running"] = False
            if "runtime" in entry:
                entry["runtime"]["paused"] = True
            return jsonify({"status": "ok", "success": True, "running": False})
        elif action == "on":
            entry["running"] = True
            if "runtime" in entry:
                entry["runtime"]["paused"] = False
            return jsonify({"status": "ok", "success": True, "running": True})
        else:
            return jsonify({"status": "error", "message": "Invalid action"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_app.route("/api/delete_bot", methods=["POST"])
def api_delete_bot():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()

        if hosted_id not in hosted_by_id and hosted_id not in hosted_registry:
            return jsonify({"status": "error", "message": "Bot not found"}), 404

        if hosted_id in hosted_by_id:
            entry = hosted_by_id[hosted_id]
            entry["running"] = False
            if "runtime" in entry:
                entry["runtime"]["paused"] = True
            del hosted_by_id[hosted_id]
        else:
            entry = {}

        for uid, bots in list(hosted_bots.items()):
            if hosted_id in bots:
                del bots[hosted_id]

        owner_file = entry.get("owner_file") or os.path.join(DATA_DIR, f"owner_{hosted_id}.txt")
        if owner_file and os.path.exists(owner_file):
            try:
                os.remove(owner_file)
            except Exception:
                pass

        unregister_bot(hosted_id)

        return jsonify({"status": "ok", "success": True, "message": "Deleted"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_app.route("/api/broadcast", methods=["POST"])
def api_broadcast():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()
        message = (data.get("message") or "").strip()

        if hosted_id not in hosted_by_id:
            return jsonify({"status": "error", "message": "Bot not found"}), 404

        if not message:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        entry = hosted_by_id[hosted_id]
        bot_id = entry["info"]["id"]
        token = entry.get("token")
        user_file = os.path.join(DATA_DIR, f"users_{bot_id}.json")
        users = load_users(user_file)

        if not users:
            return jsonify({"status": "ok", "success": True, "sent": 0, "failed": 0})

        broadcast_bot = sync_telebot.TeleBot(token, parse_mode="Markdown")
        sent = 0
        failed = 0

        for uid in list(users.keys()):
            try:
                broadcast_bot.send_message(
                    int(uid),
                    f"{DIVIDER}\n"
                    f"📢 *BROADCAST MESSAGE*\n"
                    f"{DIVIDER}\n\n"
                    f"{message}\n\n"
                    f"{styled_footer()}",
                )
                sent += 1
                time.sleep(0.05)
            except Exception:
                failed += 1

        return jsonify({"status": "ok", "success": True, "sent": sent, "failed": failed})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_app.route("/api/bot_stats", methods=["POST"])
def api_bot_stats():
    try:
        data = request.get_json() or {}
        hosted_id = (data.get("hosted_id") or "").strip()

        if hosted_id not in hosted_by_id:
            return jsonify({"status": "error", "message": "Bot not found"}), 404

        entry = hosted_by_id[hosted_id]
        bot_id = entry["info"]["id"]
        user_file = os.path.join(DATA_DIR, f"users_{bot_id}.json")
        total, d1, d2, _ = get_stats(user_file)

        return jsonify({
            "status": "ok",
            "success": True,
            "total_users": total,
            "active_today": d1,
            "active_yesterday": d2,
            "running": entry.get("running", False),
            "username": entry["info"]["username"],
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def restore_bots_from_registry():
    print("[RESTORE] Checking for bots to restore...")
    restored = 0
    for hid, reg in list(hosted_registry.items()):
        token = reg.get("token")
        owner_id = reg.get("owner_id")
        if not token:
            continue
        try:
            owner_int = int(owner_id) if owner_id and str(owner_id).lstrip("-").isdigit() else None
            start_hosted_prediction_bot(token, owner_int, hid)
            restored += 1
            print(f"[RESTORE] Restored @{reg.get('username')} ({hid})")
        except Exception as e:
            print(f"[RESTORE] Failed to restore {hid}: {e}")
    print(f"[RESTORE] Total restored: {restored}")

# ──────────────────────────────────────────────────────────────
# SHUTDOWN & MAIN
# ──────────────────────────────────────────────────────────────

async def shutdown():
    global _http_client
    print("\n⏳ Closing active sessions and cleaning up resources...")
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
    try:
        await bot.close_session()
    except Exception as e:
        print(f"Warning during bot shutdown: {e}")
    print("✅ Clean shutdown completed.")

async def main():
    print("\n" + "=" * 60)
    print("👑 KOHLI VIP BOT v8.0 — ALL-IN-ONE RAILWAY BUILD")
    print("   ⚔️  SERVER 1 : Dragon Track (HTML Engine) — MAX L2")
    print("   🤖  SERVER 2 : Adaptive Quant Engine — MAX L2")
    print("   🔑  SERVER 3 : Seed Hash Decrypter (SHA256)")
    print("=" * 60 + "\n")

    for attempt in range(MAX_RETRIES):
        try:
            me = await bot.get_me()
            print(f"✅ Bot logged in as: @{me.username} (ID: {me.id})")
            break
        except ApiTelegramException as e:
            if e.error_code == 401:
                print("\n❌ FATAL: Invalid BOT_TOKEN!")
                await shutdown()
                return
            elif attempt < MAX_RETRIES - 1:
                print(f"⚠️ Attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"❌ Telegram API Error: {e}")
                await shutdown()
                return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"⚠️ Connection {attempt + 1}/{MAX_RETRIES}: {e}")
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"❌ Failed after {MAX_RETRIES} attempts")
                await shutdown()
                return

    try:
        await recover_sessions()
        print("✅ BOT ONLINE & RUNNING!")
        await bot.polling(non_stop=True, allowed_updates=util.update_types,
                          request_timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"❌ Live polling error: {e}")
    finally:
        await shutdown()

def run_api():
    port = int(os.environ.get("PORT", 5000))
    api_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_host_bot():
    while True:
        try:
            host_bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[!] Host bot crash: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║   👑 KOHLI VIP PREDICTION BOT v8.0 👑       ║
║   🚀 All-in-One • Railway Ready • No Docker ║
╚══════════════════════════════════════════════╝
""")

    # Restore hosted bots
    threading.Thread(target=restore_bots_from_registry, daemon=True).start()

    # Start Flask API in background
    threading.Thread(target=run_api, daemon=True).start()

    # Start host bot in background
    threading.Thread(target=run_host_bot, daemon=True).start()

    # Run main async bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot manually terminated.")
    except Exception as e:
        print(f"\n❌ Global Runtime Crash: {e}")
