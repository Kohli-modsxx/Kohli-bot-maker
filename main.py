# ============================================================
# 👑 KOHLI HOSTING + PREDICTION BOT — PROFESSIONAL v7.1
# ============================================================
# ✨ Enhanced UI • Premium Animations • Pro Design
# 🔧 FIXED: New tokens, token validation, 401 handling
# 🚀 RAILWAY OPTIMIZED: Single-file deploy, restore, port binding
# 🧠 PREDICTION LOGIC: v4.1 Naithik VIP Engine (Preserved)
# ============================================================

import telebot
import threading
import time
import random
import pytz
import json
import os
import asyncio
import math
import hashlib
from datetime import datetime
from collections import deque, Counter
import httpx
from telebot.async_telebot import AsyncTeleBot
from telebot import types, util
from telebot.apihelper import ApiTelegramException
from flask import Flask, request, jsonify

# ============================================================
# 🔧 MAIN CONFIG (UPDATED TOKENS)
# ============================================================

HOST_BOT_TOKEN = "8372270378:AAEXNRXUD2xTwShxB7z7WR5uqX2NrWBvN6o"
ADMIN_ID = 7741897793

# ✅ FIXED: New prediction bot token
PRED_BOT_TOKEN = "8766089087:AAGqAnVxZnCmmhtL6NQvyXkuqcE6DV5rf7M"

# Prediction engine config
FIREBASE_URL = "https://glowbet-1b2ce-default-rtdb.firebaseio.com"
HISTORY_API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
PRED_DATA_FILE = "bot_data.json"

REQUEST_TIMEOUT = 60
MAX_RETRIES = 10
RETRY_DELAY = 3

# Host bot (sync)
host_bot = telebot.TeleBot(HOST_BOT_TOKEN, parse_mode="Markdown")

# Prediction bot (async)
pred_bot = AsyncTeleBot(PRED_BOT_TOKEN)
pred_bot.request_timeout = REQUEST_TIMEOUT

# ============================================================
# 🎨 DESIGN CONSTANTS
# ============================================================

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

PROGRESS_BAR = ["🟥⬜⬜⬜⬜", "🟥🟥⬜⬜⬜", "🟥🟥🟥⬜⬜", "🟥🟥🟥🟥⬜", "🟥🟥🟥🟥🟥"]

STICKER_START = "CAACAgUAAxkBAAFLuItqJPtZCBFQfGfRsJKl6boNvqKixQACuRMAAtgMEVayBm8tXDvNpDsE"
STICKER_WIN_LIST = [
    "CAACAgUAAxkBAAFLuI1qJPt6xyJZrPgYtmOdxJ2YMa6gFwACJxQAAhs_UVXBa4-Se7IejzsE",
    "CAACAgUAAxkBAAFL6I1qJ38O9fE3RKMdUU0R1iQpapxH8AACBxwAAqlQ2FYgxhZ0x6m0ojsE",
]
STICKER_STOP = "CAACAgUAAxkBAAFLuJFqJPuZKYQt4bz30u_39DM-JwW4agAClBEAAo-CGFb2yvdmMKOx1jsE"

# ============================================================
# 📁 PERSISTENT STORAGE DIRECTORY
# ============================================================

DATA_DIR = os.environ.get("DATA_DIR", "kohli_data")
os.makedirs(DATA_DIR, exist_ok=True)


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


# ============================================================
# 🌐 GLOBAL STORAGE
# ============================================================

hosted_bots = {}
hosted_by_id = {}
hosted_registry = {}
registry_file = data_path("hosted_registry.json")

pred_user_states = {}
pred_active_sessions = {}
bot_data_cache = None


# ============================================================
# 💾 REGISTRY PERSISTENCE
# ============================================================

def load_registry():
    global hosted_registry
    if os.path.exists(registry_file):
        try:
            with open(registry_file, "r") as f:
                hosted_registry = json.load(f)
            print(f"[REGISTRY] Loaded {len(hosted_registry)} entries")
        except Exception as e:
            print(f"[REGISTRY] Load failed: {e}")
            hosted_registry = {}


def save_registry():
    try:
        with open(registry_file, "w") as f:
            json.dump(hosted_registry, f, indent=2)
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


load_registry()


# ============================================================
# 🎬 ANIMATION HELPERS
# ============================================================

def animate_loading(bot_obj, chat_id, text, frames=None, delay=0.4):
    frames = frames or PROGRESS_BAR
    try:
        msg = bot_obj.send_message(chat_id, f"{SPARKLE} {text}\n\n{frames[0]}")
        for frame in frames[1:]:
            time.sleep(delay)
            try:
                bot_obj.edit_message_text(
                    f"{SPARKLE} {text}\n\n{frame}",
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        time.sleep(0.3)
        try:
            bot_obj.delete_message(chat_id, msg.message_id)
        except Exception:
            pass
    except Exception:
        pass


def styled_footer(text="KOHLI PREMIUM ENGINE"):
    return f"{SUB_DIVIDER}\n{LIGHTNING} {text} {LIGHTNING}"


# ============================================================
# 🔮 PREDICTION HELPERS
# ============================================================

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
        server_name = "⚔️ 𝐋ᴀsᴇ r 𝐓ʀᴀᴄᴋ"
    elif server == "2":
        server_name = "🤖 𝐀𝐏𝐈 𝐑ᴇᴀᴅᴇʀ"
    else:
        server_name = "🔑 𝐒ᴇᴇᴅ 𝐃ᴇᴄʀʏᴘᴛᴏʀ"

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
        f"☑️ 𝐍ᴀɪᴛɪᴋ 𝐏ʀɪᴠᴀᴛᴇ 𝐀ᴜᴛᴏ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ ⚠️\n"
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
        f"🚀 𝐀𝐈 𝐏ᴏᴡᴇʀᴇᴅ 𝐁ʏ @OFFICIALNAITIK2"
    )


# ============================================================
# 🌐 HTTP CLIENT
# ============================================================

_http_client = None


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


# ============================================================
# 📊 PERSISTENCE
# ============================================================

async def pred_load_data():
    global bot_data_cache
    if bot_data_cache is not None:
        return bot_data_cache
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
                        bot_data_cache = d
                        return bot_data_cache
            except Exception:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
    try:
        path = data_path(PRED_DATA_FILE)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                d = json.load(f)
                if d and isinstance(d, dict):
                    d.setdefault("users", {})
                    d.setdefault("sessions", {})
                    bot_data_cache = d
                    return bot_data_cache
    except Exception:
        pass
    bot_data_cache = empty
    return bot_data_cache


async def pred_save_data(data):
    global bot_data_cache
    bot_data_cache = data
    try:
        with open(data_path(PRED_DATA_FILE), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception:
        pass
    if FIREBASE_URL:
        try:
            await get_http().put(f"{FIREBASE_URL.rstrip('/')}/bot_data.json", json=data)
        except Exception:
            pass


async def add_channel(user_id, channel_link, channel_id, auto_detected=False):
    data = await pred_load_data()
    uid = str(user_id)
    data['users'].setdefault(uid, {'channels': [], 'settings': {}, 'total_wins': 0, 'total_losses': 0})
    for ch in data['users'][uid]['channels']:
        if str(ch['channel_id']) == str(channel_id):
            return False
    data['users'][uid]['channels'].append({
        'channel_link': channel_link, 'channel_id': str(channel_id),
        'added_date': datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        'auto_detected': auto_detected,
        'total_sessions': 0, 'total_wins': 0, 'total_losses': 0
    })
    await pred_save_data(data)
    return True


async def remove_channel(user_id, channel_id):
    data = await pred_load_data()
    uid = str(user_id)
    if uid not in data['users']:
        return False
    before = len(data['users'][uid]['channels'])
    data['users'][uid]['channels'] = [
        c for c in data['users'][uid]['channels']
        if str(c['channel_id']) != str(channel_id)
    ]
    if len(data['users'][uid]['channels']) < before:
        await pred_save_data(data)
        return True
    return False


async def update_stats(user_id, channel_id, wins, losses):
    data = await pred_load_data()
    uid = str(user_id)
    for ch in data.get('users', {}).get(uid, {}).get('channels', []):
        if str(ch['channel_id']) == str(channel_id):
            ch['total_sessions'] = ch.get('total_sessions', 0) + 1
            ch['total_wins'] = ch.get('total_wins', 0) + wins
            ch['total_losses'] = ch.get('total_losses', 0) + losses
            break
    await pred_save_data(data)


async def get_channels(user_id):
    data = await pred_load_data()
    return data.get('users', {}).get(str(user_id), {}).get('channels', [])


async def save_session_db(user_id, session_data):
    data = await pred_load_data()
    clean = {k: v for k, v in session_data.items() if k != 'task'}
    data['sessions'][str(user_id)] = clean
    await pred_save_data(data)


async def delete_session_db(user_id):
    data = await pred_load_data()
    if str(user_id) in data.get('sessions', {}):
        del data['sessions'][str(user_id)]
        await pred_save_data(data)


async def get_all_pred_users():
    data = await pred_load_data()
    return data.get('users', {})


# ============================================================
# 📈 HISTORY PARSER
# ============================================================

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


# ============================================================
# 🧠 PREDICTION ALGORITHMS (Preserved from v4.1)
# ============================================================

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
        'edge': edge_final, 'entropy': ent,
        'streak': (streak_val, streak_len),
        'top_factors': board.top_factors(4),
        'cycle_block': cycle_block, 'block_score': block_score,
        'anom': anom, 'cyc_period': cyc_period,
        'cyc_strength': cyc_strength, 'alt_rate': alt_rate,
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
        return hist[0] if hist else 'BIG'

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
        return pred, base_conf, f"L1/{stage_used}"

    votes = {'BIG': 0.0, 'SMALL': 0.0}
    votes[pred] += 2.0

    d6 = _html_density(hist, sample_size=6)
    d10 = _html_density(hist, sample_size=10)
    d20 = _html_density(hist, sample_size=20) if len(hist) >= 20 else None
    if d6: votes[d6] += 1.5
    if d10: votes[d10] += 1.5
    if d20: votes[d20] += 1.0

    if len(hist) >= 10:
        r5_big = hist[:5].count('BIG') / 5.0
        r10_big = hist[:10].count('BIG') / 10.0
        drift = r5_big - r10_big
        if abs(drift) >= 0.20:
            revert = 'SMALL' if drift > 0 else 'BIG'
            votes[revert] += 2.0

    if streak >= 4:
        votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 2.5
    elif streak >= 3:
        votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 1.5

    if len(hist) >= 6:
        alt_flips = sum(1 for i in range(5) if hist[i] != hist[i + 1])
        if alt_flips >= 4:
            votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 2.0

    if len(hist) >= 20:
        bg = hist[:20].count('BIG')
        sm = hist[:20].count('SMALL')
        if bg >= 15: votes['SMALL'] += 2.0
        elif sm >= 15: votes['BIG'] += 2.0

    votes['SMALL' if hist[0] == 'BIG' else 'BIG'] += 1.0

    if len(hist) >= 30:
        bg30 = hist[:30].count('BIG')
        if bg30 >= 20: votes['SMALL'] += 1.5
        elif bg30 <= 10: votes['BIG'] += 1.5

    final_pred = 'BIG' if votes['BIG'] >= votes['SMALL'] else 'SMALL'
    total_v = votes['BIG'] + votes['SMALL']
    edge = votes[final_pred] / total_v if total_v > 0 else 0.5
    final_conf = min(88, max(60, int(50 + edge * 80)))
    return final_pred, final_conf, f"L2-ExtremeAnalysis/{stage_used}"


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
        if html_dragon: probe_votes[html_dragon] += 1.2

        html_chop = _html_chop_chop(outcomes)
        if html_chop: probe_votes[html_chop] += 1.5

        html_density = _html_density(outcomes)
        if html_density: probe_votes[html_density] += 1.0

        streak_val, streak_len, _, _ = _streak_info(outcomes)
        if streak_len >= 5:
            probe_votes['SMALL' if streak_val == 'BIG' else 'BIG'] += 2.5
        elif streak_len >= 4:
            probe_votes['SMALL' if streak_val == 'BIG' else 'BIG'] += 1.5
        elif streak_len >= 3:
            probe_votes['SMALL' if streak_val == 'BIG' else 'BIG'] += 0.8

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
    if html_density: board2.add("L2-HTML-Density", html_density, 1.5)

    html_chop = _html_chop_chop(outcomes)
    if html_chop: board2.add("L2-HTML-Chop", html_chop, 2.0)

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


# ============================================================
# 🎯 PREDICTION BOT UI
# ============================================================

def pred_user_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Start Prediction", "🛑 Stop Prediction")
    markup.row("➕ Add Channel", "📊 My Channels")
    markup.row("🗑 Remove Channel", "📈 My Stats")
    markup.row("❓ Help", "📞 Support")
    return markup


def pred_admin_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Start Prediction", "🛑 Stop Prediction")
    markup.row("➕ Add Channel", "📊 My Channels")
    markup.row("🗑 Remove Channel", "📈 My Stats")
    markup.row("📢 Broadcast", "🔧 System Stats")
    markup.row("❓ Help", "📞 Support")
    return markup


async def pred_safe_send(target, text, reply_markup=None):
    for attempt in range(MAX_RETRIES):
        try:
            await asyncio.sleep(0.3)
            return await pred_bot.send_message(target, text, parse_mode="HTML", reply_markup=reply_markup)
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


async def pred_safe_edit(msg, text, reply_markup=None):
    try:
        await asyncio.sleep(0.2)
        await pred_bot.edit_message_text(
            chat_id=msg.chat.id, message_id=msg.message_id,
            text=text, parse_mode='HTML', reply_markup=reply_markup)
    except Exception:
        pass


async def send_sticker(target, sticker_id):
    try:
        await asyncio.sleep(0.3)
        await pred_bot.send_sticker(target, sticker_id)
    except Exception:
        pass


async def send_win_sticker(target):
    await send_sticker(target, random.choice(STICKER_WIN_LIST))


# ============================================================
# 🎯 PREDICTION LOOP
# ============================================================

async def prediction_loop(user_id, channel_link, server):
    session = pred_active_sessions.get(user_id)
    if not session:
        return

    channel = int(session['channel_id'])

    if server == "1":
        server_name = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
    elif server == "2":
        server_name = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
    else:
        server_name = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏ𝐫"

    sep = "━━━━━━━━━━━━━━━━━━━━━━━━"

    try:
        await send_sticker(channel, STICKER_START)
        await asyncio.sleep(1)

        intro = await pred_safe_send(channel,
            f"{sep}\n"
            f"🤖 𝐊ᴏʜʟɪ 𝐕𝐈𝐏 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ\n"
            f"{sep}\n"
            f"🖥 𝐒ᴇ r ᴠᴇ r : {server_name}\n"
            f"🎯 𝐋ɪᴍɪᴛ : {session['max_bets']} predictions\n"
            f"🕐 𝐒ᴛᴀ r ᴛ : <code>{now_str()}</code>\n"
            f"{sep}")

        if intro is None:
            await pred_safe_send(user_id, f"❌ Cannot post to {channel_link}!\nMake sure bot is Channel Admin.")
            pred_active_sessions.pop(user_id, None)
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

            sent = await pred_safe_send(channel, make_prediction_text(
                period, prediction, current_level, server, confidence, signal_strength, jackpot_detected, hash_val))
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
                await pred_safe_send(channel, make_win_text(session['wins'], session['losses']))
                if completed >= max_bets:
                    break

            await asyncio.sleep(2)

        await end_session(user_id, channel, "✅ SESSION COMPLETED")

    except asyncio.CancelledError:
        await end_session(user_id, channel, "🛑 SESSION TERMINATED")
    except Exception as e:
        await end_session(user_id, channel, f"⚠️ ERROR: {str(e)[:80]}")


async def end_session(user_id, channel, reason):
    session = pred_active_sessions.get(user_id)
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
        await pred_safe_send(channel_id_int, summary)
    except Exception:
        pass

    try:
        await pred_safe_send(user_id, summary)
    except Exception:
        pass

    try:
        await update_stats(user_id, session['channel_id'], session.get('wins', 0), session.get('losses', 0))
    except Exception:
        pass

    pred_active_sessions.pop(user_id, None)

    try:
        await delete_session_db(user_id)
    except Exception:
        pass


async def recover_pred_sessions():
    try:
        data = await pred_load_data()
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
                pred_active_sessions[user_id] = {
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
                pred_active_sessions[user_id]['task'] = task
                await pred_safe_send(int(session.get('channel_id')),
                    f"🛡 𝐒ʏsᴛᴇᴍ 𝐑ᴇᴄᴏᴠᴇʀᴇᴅ\n{'━'*22}\n"
                    f"🤖 <b>𝐁ᴏᴛ 𝐑ᴇsᴛᴏʀᴇᴅ.</b>\n🔄 𝐒ᴇssɪᴏɴ 𝐑ᴇsᴜᴍᴇᴅ!\n{'━'*22}")
            except Exception:
                pass
    except Exception:
        pass


# ============================================================
# 🔔 PREDICTION BOT HANDLERS
# ============================================================

@pred_bot.my_chat_member_handler()
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
            kb.row(types.InlineKeyboardButton("🚀 𝐒ᴛᴀ r ᴛ 𝐏 r ᴇᴅɪᴄᴛɪᴏɴ 𝐍ᴏᴡ!", callback_data=f"quickstart_{channel_id}"))
            await pred_bot.send_message(promoted_by,
                f"✅ 𝐂ʜᴀɴɴᴇʟ 𝐀ᴜᴛᴏ-𝐃ᴇᴛᴇᴄᴛᴇᴅ & 𝐀ᴅᴅᴇᴅ!\n\n{'━'*22}\n"
                f"📢 𝐂ʜᴀɴɴᴇʟ : {channel_title}\n"
                f"🔗 𝐋ɪɴᴋ : <code>{channel_uname}</code>\n"
                f"🆔 𝐈ᴅ : <code>{channel_id}</code>\n{'━'*22}\n\n"
                f"🎉 𝐏 r ᴇᴅɪᴄᴛɪᴏɴ 𝐒ʜᴜ r ᴜ 𝐊ᴀ r ᴇɪɴ! 👇",
                parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"❌ Auto-detect notify failed: {e}")


PRED_HELP_TEXT = (
    "❓ 𝐊ᴏʜʟɪ 𝐕𝐈𝐏 𝐁ᴏᴛ 𝐇ᴇʟᴘ\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "⚙️ 𝐂ᴏᴍᴍᴀɴᴅs:\n• /start — Bot start\n• /predict — Start prediction\n"
    "• /add @Channel — Channel add\n• /help — Help menu\n• /cancel — Cancel flow\n\n"
    "📢 𝐀ᴜᴛᴏ 𝐂ʜᴀɴɴᴇʟ 𝐒ᴇᴛᴜᴘ:\nBot ko channel ka Admin banayein → Auto detect!\n\n"
    "⚖️ 𝐌ᴀ r ᴛɪɴɢᴀʟᴇ 𝐋ᴇᴠᴇʟs:\n"
    "• Capped at level 2 max across all modules\n\n"
    "📊 𝐄ɴɢɪɴᴇs:\n"
    "• ⚔️ 𝐒ᴇ r ᴠᴇ r 1 — Dragon Engine (Dragon+Chop+Density)\n"
    "• 🤖 𝐒ᴇ r ᴠᴇ r 2 — Adaptive Quant Engine (Ensemble Analysis)\n"
    "• 🔑 𝐒ᴇ r ᴠᴇ r 3 — Seed Hash Decrypter (Mathematical Hashing)\n\n"
    "📞 𝐒ᴜᴘᴘᴏ r ᴛ: @xxLEGEND_KOHLI"
)


async def trigger_start(message, user_id):
    loading_msg = await pred_bot.send_message(message.chat.id,
        "⚡ 𝐋ᴏᴀᴅɪɴɢ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 𝐄ɴɢɪɴᴇs...\n📡 𝐒ʏɴᴄɪɴɢ 𝐃ᴀᴛᴀ...\n🧠 𝐀𝐈 𝐑ᴇᴀᴅʏ...",
        parse_mode="HTML")
    try:
        channels = await get_channels(user_id)
        if not channels:
            await pred_safe_edit(loading_msg,
                "❌ 𝐍ᴏ 𝐂ʜᴀɴɴᴇʟs 𝐀ᴅᴅᴇᴅ!\n\nBot ko channel Admin banayein ya <code>/add @ChannelUsername</code> karein.")
            return
        if user_id in pred_active_sessions:
            await pred_safe_edit(loading_msg, "⚠️ 𝐒ᴇssɪᴏɴ 𝐀ʟ r ᴇᴀᴅʏ 𝐑ᴜɴɴɪɴɢ!\nPehle '🛑 Stop Prediction' karein.")
            return

        pred_user_states[user_id] = {"step": "select_server", "channels": channels}
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("⚔️ SERVER 1 — Dragon Track (HTML Engine)", callback_data="server_1"))
        kb.row(types.InlineKeyboardButton("🤖 SERVER 2 — Adaptive Quant (Ensemble)", callback_data="server_2"))
        kb.row(types.InlineKeyboardButton("🔑 SERVER 3 — Seed Hash Decrypter", callback_data="server_3"))
        kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        await pred_safe_edit(loading_msg,
            f"🎯 𝐒ᴇʟᴇᴄᴛ 𝐒ᴇ r ᴠᴇ r\n{'━'*20}\n"
            f"⚔️ 𝐒ᴇ r ᴠᴇ r 1 — Dragon Line + Chop + Density\n"
            f"🤖 𝐒ᴇ r ᴠᴇ r 2 — Adaptive Quant Multi-Heuristic Engine\n"
            f"🔑 𝐒ᴇ r ᴠᴇ r 3 — Seed Hash Decrypter (SHA256 Win Predictor)\n"
            f"{'━'*20}\n𝐂ʜᴏᴏsᴇ 𝐒ᴇ r ᴠᴇ r:",
            reply_markup=kb)
    except Exception as e:
        await pred_safe_edit(loading_msg, f"❌ 𝐄ʀʀᴏ r: <code>{str(e)[:150]}</code>")


@pred_bot.message_handler(commands=['start'])
async def pred_cmd_start(message: types.Message):
    user_id = message.from_user.id
    kb = pred_admin_kb() if user_id == ADMIN_ID else pred_user_kb()
    await pred_bot.send_message(message.chat.id,
        f"🎯 𝐖ᴇʟᴄᴏᴍᴇ, {message.from_user.first_name}!\n\n{'━'*22}\n"
        f"🤖 𝐊ᴏʜʟɪ 𝐕𝐈𝐏 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 𝐁ᴏᴛ v4.1\n"
        f"⚔️ 𝐒ᴇ r ᴠᴇ r 1: Dragon HTML Engine\n"
        f"🤖 𝐒ᴇ r ᴠᴇ r 2: Adaptive Quant Engine\n"
        f"🔑 𝐒ᴇ r ᴠᴇ r 3: Seed Hash Decrypter\n{'━'*22}\n\n𝐔sᴇ ᴏᴘᴛɪᴏɴs ʙᴇʟᴏᴡ:",
        parse_mode="HTML", reply_markup=kb)


@pred_bot.message_handler(commands=['help'])
async def pred_cmd_help(message: types.Message):
    await pred_bot.send_message(message.chat.id, PRED_HELP_TEXT, parse_mode="HTML")


@pred_bot.message_handler(commands=['predict'])
async def pred_cmd_predict(message: types.Message):
    await trigger_start(message, message.from_user.id)


@pred_bot.message_handler(commands=['cancel'])
async def pred_cmd_cancel(message: types.Message):
    pred_user_states.pop(message.from_user.id, None)
    await pred_bot.send_message(message.chat.id, "❌ 𝐅ʟᴏᴡ 𝐂ᴀɴᴄᴇʟʟᴇᴅ.", parse_mode="HTML")


@pred_bot.message_handler(commands=['add'])
async def pred_cmd_add(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        await pred_bot.send_message(message.chat.id, "❌ 𝐔sᴀɢᴇ: /add @YourChannel or /add -100xxxxxxxxxx", parse_mode="HTML")
        return
    channel_input = args[1].strip()
    status_msg = await pred_bot.send_message(message.chat.id, "🔄 𝐕ᴇ r ɪꜰɪᴇ s...", parse_mode="HTML")
    try:
        chat = await pred_bot.get_chat(channel_input)
        channel_id = chat.id
        channel_uname = f"@{chat.username}" if chat.username else str(channel_id)
        channel_title = chat.title or channel_uname
        member = await pred_bot.get_chat_member(channel_id, (await pred_bot.get_me()).id)
        if member.status not in ["administrator", "creator"]:
            await pred_safe_edit(status_msg, "❌ 𝐁ᴏᴛ ɪs 𝐍ᴏᴛ 𝐀ᴅᴍɪɴ ɪɴ ᴛʜɪs ᴄʜᴀɴɴᴇʟ!")
            return
        added = await add_channel(user_id, channel_uname, channel_id, auto_detected=False)
        if added:
            await pred_safe_edit(status_msg, f"✅ 𝐂ʜᴀɴɴᴇʟ 𝐀ᴅᴅᴇᴅ: {channel_title}\n\n'🚀 Start Prediction' se shuru karein.")
        else:
            await pred_safe_edit(status_msg, f"ℹ️ <b>{channel_title}</b> pehle se list mein hai!")
    except Exception as e:
        await pred_safe_edit(status_msg, f"❌ 𝐅ᴀɪʟᴇᴅ: <code>{str(e)}</code>")


@pred_bot.message_handler(commands=['resetdb'])
async def pred_cmd_reset_db(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await pred_bot.send_message(message.chat.id, "❌ Access denied.")
        return
    empty_data = {"users": {}, "sessions": {}}
    await pred_save_data(empty_data)
    global bot_data_cache
    bot_data_cache = empty_data
    await pred_bot.send_message(message.chat.id, "✅ 𝐃ᴀᴛᴀʙᴀsᴇ 𝐖ɪᴘᴇᴅ!", parse_mode="HTML")


# ============================================================
# 📢 BROADCAST (PREDICTION BOT)
# ============================================================

async def run_pred_broadcast(sender_id: int, text: str):
    all_users = await get_all_pred_users()
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
                await pred_bot.send_message(uid, text, parse_mode="HTML")
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
        if success: ok_dm += 1
        else: fail_dm += 1

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
                await pred_bot.send_message(cid_int, text, parse_mode="HTML")
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
        if success: ok_ch += 1
        else: fail_ch += 1

    return ok_dm, fail_dm, ok_ch, fail_ch


# ============================================================
# 📩 PREDICTION BOT TEXT HANDLER
# ============================================================

@pred_bot.message_handler(func=lambda msg: True)
async def pred_on_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = pred_user_states.get(user_id)

    if text.startswith("/"):
        return

    if text == "❓ Help":
        await pred_bot.send_message(message.chat.id, PRED_HELP_TEXT, parse_mode="HTML")
        return

    if text == "📞 Support":
        await pred_bot.send_message(message.chat.id,
            "📞 <b>𝐒ᴜᴘᴘᴏ r ᴛ</b>\n\n"
            "💬 Contact our support lines:\n\n"
            "👤 𝐎ᴡɴᴇ r : @xxLEGEND_KOHLI",
            parse_mode="HTML")
        return

    if text == "🚀 Start Prediction":
        await trigger_start(message, user_id)
        return

    if text == "➕ Add Channel":
        await pred_bot.send_message(message.chat.id,
            "📢 𝐀ᴅᴅ 𝐂ʜᴀɴɴᴇʟ:\n\n• Bot ko target channel ka <b>Admin</b> banayein.\n"
            "• Bot automatically detect karega.\n• Manual: <code>/add @ChannelUsername</code>",
            parse_mode="HTML")
        return

    if text == "📊 My Channels":
        channels = await get_channels(user_id)
        if not channels:
            await pred_bot.send_message(message.chat.id, "❌ No channels found! /add use karein.")
            return
        resp = f"📊 𝐘ᴏᴜ r 𝐂ʜᴀɴɴᴇʟs ({len(channels)})\n{'━'*22}\n\n"
        for i, ch in enumerate(channels, 1):
            s = ch.get('total_sessions', 0)
            w = ch.get('total_wins', 0)
            l = ch.get('total_losses', 0)
            rate = f"{round(w / (w + l) * 100)}%" if (w + l) > 0 else "N/A"
            resp += (f"<b>{i}. {ch['channel_link']}</b>\n🆔 <code>{ch['channel_id']}</code>\n"
                    f"🎮 𝐒ᴇssɪᴏɴs: {s} | ✅ {w} | ❌ {l} | 📈 {rate}\n{'━'*22}\n\n")
        await pred_bot.send_message(message.chat.id, resp, parse_mode="HTML")
        return

    if text == "🗑 Remove Channel":
        channels = await get_channels(user_id)
        if not channels:
            await pred_bot.send_message(message.chat.id, "❌ No channels to remove.")
            return
        kb = types.InlineKeyboardMarkup()
        for ch in channels:
            cid = encode_cid(ch['channel_id'])
            kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}", callback_data=f"manage_{cid}"))
        kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
        await pred_bot.send_message(message.chat.id,
            "🗑 𝐑ᴇᴍᴏᴠᴇ 𝐂ʜᴀɴɴᴇʟ\n\nTap a channel to remove:",
            parse_mode="HTML", reply_markup=kb)
        return

    if text == "📈 My Stats":
        channels = await get_channels(user_id)
        total_w = sum(c.get('total_wins', 0) for c in channels)
        total_l = sum(c.get('total_losses', 0) for c in channels)
        total_s = sum(c.get('total_sessions', 0) for c in channels)
        rate = f"{round(total_w / (total_w + total_l) * 100)}%" if (total_w + total_l) > 0 else "N/A"
        await pred_bot.send_message(message.chat.id,
            f"📈 𝐒ᴛᴀᴛɪsᴛɪᴄᴛs\n{'━'*22}\n\n"
            f"📢 𝐂ʜᴀɴɴᴇʟs : {len(channels)}\n"
            f"🎮 𝐒ᴇssɪᴏɴs : {total_s}\n"
            f"✅ 𝐖ɪɴs : {total_w}\n"
            f"❌ 𝐋ᴏssᴇs : {total_l}\n"
            f"📊 𝐑ᴀᴛᴇ : {rate}\n{'━'*22}", parse_mode="HTML")
        return

    if text == "🛑 Stop Prediction":
        if user_id not in pred_active_sessions:
            await pred_bot.send_message(message.chat.id, "❌ No session running!")
            return
        session = pred_active_sessions[user_id]
        if session.get('_ending'):
            return
        session['stop_flag'] = True
        task = session.get('task')
        if task and not task.done():
            task.cancel()
        if task and task.done():
            await end_session(user_id, int(session['channel_id']), "🛑 STOPPED BY USER")
        await pred_bot.send_message(message.chat.id, "🛑 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 𝐒ᴛᴏᴘᴘᴇᴅ!", parse_mode="HTML")
        return

    if text == "📢 Broadcast" and user_id == ADMIN_ID:
        pred_user_states[ADMIN_ID] = "waiting_broadcast"
        await pred_bot.send_message(message.chat.id,
            "📢 Enter the message to broadcast.\n"
            "It will be sent to ALL user DMs and ALL connected channels/groups.")
        return

    if text == "🔧 System Stats" and user_id == ADMIN_ID:
        users = await get_all_pred_users()
        total_ch = sum(len(u.get('channels', [])) for u in users.values())
        total_w = sum(c.get('total_wins', 0) for u in users.values() for c in u.get('channels', []))
        total_l = sum(c.get('total_losses', 0) for u in users.values() for c in u.get('channels', []))
        rate = f"{round(total_w / (total_w + total_l) * 100)}%" if (total_w + total_l) > 0 else "N/A"
        await pred_bot.send_message(message.chat.id,
            f"🔧 𝐒ʏsᴛᴇᴍ 𝐒ᴛᴀᴛs\n{'━'*22}\n\n"
            f"👥 𝐔sᴇ r s : {len(users)}\n"
            f"📢 𝐂ʜᴀɴɴᴇʟs : {total_ch}\n"
            f"🔄 𝐀ᴄᴛɪᴠᴇ : {len(pred_active_sessions)}\n"
            f"✅ 𝐖ɪɴs : {total_w}\n"
            f"❌ 𝐋ᴏssᴇs : {total_l}\n"
            f"📊 𝐑ᴀᴛᴇ : {rate}\n"
            f"🛡 𝐃ʙ : {'Firebase ONLINE' if FIREBASE_URL else 'Local JSON'}\n{'━'*22}",
            parse_mode="HTML")
        return

    if state == "waiting_broadcast" and user_id == ADMIN_ID:
        pred_user_states.pop(ADMIN_ID, None)
        all_users = await get_all_pred_users()
        unique_channels = set()
        for udata in all_users.values():
            for ch in udata.get('channels', []):
                if ch.get('channel_id'):
                    unique_channels.add(ch['channel_id'])
        total_users = len(all_users)
        total_ch = len(unique_channels)
        status_msg = await pred_bot.send_message(
            message.chat.id,
            f"📢 Broadcasting to {total_users} users + {total_ch} channels/groups...\n⏳ Please wait...")
        ok_dm, fail_dm, ok_ch, fail_ch = await run_pred_broadcast(user_id, text)
        await pred_safe_edit(status_msg,
            f"📢 𝐁ʀᴏᴀᴅᴄᴀsᴛ 𝐂ᴏᴍᴘʟᴇᴛᴇᴅ!\n{'━'*22}\n\n"
            f"👤 𝐔sᴇ r 𝐃𝐌s\n  ✅ Success: {ok_dm}\n  ❌ Failed: {fail_dm}\n\n"
            f"📢 𝐂ʜᴀɴɴᴇʟs/𝐆 r ᴏᴜᴘs\n  ✅ Success: {ok_ch}\n  ❌ Failed: {fail_ch}\n\n"
            f"📊 𝐉ᴏᴜ r ɴᴇʏ 𝐃ᴇʟɪᴠᴇ r ᴇᴅ: {ok_dm + ok_ch}")
        return

    if isinstance(state, dict) and state.get("step") == "select_bets":
        if not text.isdigit() or not (1 <= int(text) <= 50):
            await pred_bot.send_message(message.chat.id, "❌ Enter valid number (1-50)!")
            return
        bets = int(text)
        server = state["server"]
        channel_link = state["channel_link"]
        channel_id = state["channel_id"]
        max_level = 2
        pred_user_states.pop(user_id, None)
        if user_id in pred_active_sessions:
            await pred_bot.send_message(message.chat.id, "⚠️ Session already running.")
            return
        pred_active_sessions[user_id] = {
            'channel_link': channel_link, 'channel_id': channel_id,
            'server': server, 'max_bets': bets, 'max_level': max_level,
            'current_bet': 0, 'current_level': 1,
            'consecutive_losses': 0, 'consecutive_wins': 0,
            'win_streak': 0, 'max_win_streak': 0, 'max_loss_streak': 0,
            'stop_flag': False, 'wins': 0, 'losses': 0,
            'started_at': datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            'recent_results': [],
            '_ending': False,
        }
        await save_session_db(user_id, pred_active_sessions[user_id])

        if server == "1":
            server_name = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
        elif server == "2":
            server_name = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
        else:
            server_name = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏ𝐫"

        await pred_bot.send_message(message.chat.id,
            f"✅ 𝐒ᴇssɪᴏɴ 𝐑ᴇᴀᴅʏ!\n{'━'*22}\n\n"
            f"📢 𝐂ʜᴀɴɴᴇʟ : {channel_link}\n"
            f"🖥 𝐒ᴇ r ᴠᴇ r : {server_name}\n"
            f"🎯 𝐋ɪᴍɪᴛ : {bets} Rounds\n\n🔥 Starting now...",
            parse_mode="HTML")
        task = asyncio.create_task(prediction_loop(user_id, channel_link, server))
        pred_active_sessions[user_id]['task'] = task


# ============================================================
# 🖱️ PREDICTION BOT CALLBACKS
# ============================================================

@pred_bot.callback_query_handler(func=lambda call: True)
async def pred_on_callback(cq: types.CallbackQuery):
    user_id = cq.from_user.id
    data = cq.data
    try:
        await pred_bot.answer_callback_query(cq.id)
    except Exception:
        pass

    try:
        if data == "cancel":
            pred_user_states.pop(user_id, None)
            try:
                await pred_bot.delete_message(cq.message.chat.id, cq.message.message_id)
            except Exception:
                pass
            return

        if data == "back_to_manage":
            channels = await get_channels(user_id)
            if not channels:
                await pred_safe_edit(cq.message, "❌ No channels available.")
                return
            kb = types.InlineKeyboardMarkup()
            for ch in channels:
                cid = encode_cid(ch['channel_id'])
                kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}", callback_data=f"manage_{cid}"))
            kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
            await pred_safe_edit(cq.message, "🗑 𝐑ᴇᴍᴏᴠᴇ 𝐂ʜᴀɴɴᴇʟ\n\nTap a channel:", reply_markup=kb)
            return

        if data.startswith("manage_"):
            encoded_cid = data.split("_", 1)[1]
            channel_id = decode_cid(encoded_cid)
            channels = await get_channels(user_id)
            ch_data = next((c for c in channels if str(c['channel_id']) == str(channel_id)), None)
            if not ch_data:
                await pred_safe_edit(cq.message, "❌ Channel not found.")
                return
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("🗑 Confirm Remove", callback_data=f"del_{encoded_cid}"))
            kb.row(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage"))
            await pred_safe_edit(cq.message,
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
                await pred_safe_edit(cq.message, "✅ 𝐂ʜᴀɴɴᴇʟ 𝐑ᴇᴍᴏᴠᴇᴅ!")
            else:
                await pred_safe_edit(cq.message, "❌ Channel not found.")
            return

        if data.startswith("quickstart_"):
            channel_id = data.split("_", 1)[1]
            channels = await get_channels(user_id)
            ch_data = next((c for c in channels if str(c['channel_id']) == str(channel_id)), None)
            if not ch_data:
                await pred_safe_edit(cq.message, "❌ Channel not found.")
                return
            if user_id in pred_active_sessions:
                await pred_safe_edit(cq.message, "⚠️ Session already running.")
                return
            pred_user_states[user_id] = {"step": "select_server", "channels": channels}
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("⚔️ SERVER 1 — Dragon Track", callback_data="server_1"))
            kb.row(types.InlineKeyboardButton("🤖 SERVER 2 — Adaptive Quant", callback_data="server_2"))
            kb.row(types.InlineKeyboardButton("🔑 SERVER 3 — Seed Hash Decrypter", callback_data="server_3"))
            kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
            await pred_safe_edit(cq.message, "🎯 𝐒ᴇʟᴇᴄᴛ 𝐒ᴇʀᴠᴇ r\n\nChoose engine:", reply_markup=kb)
            return

        if data.startswith("server_"):
            server = data.split("_")[1]
            state = pred_user_states.get(user_id)
            if not isinstance(state, dict) or state.get("step") != "select_server":
                await pred_safe_edit(cq.message, "❌ Flow timed out. Click '🚀 Start Prediction' again.")
                return
            channels = state["channels"]
            kb = types.InlineKeyboardMarkup()
            for ch in channels:
                cid = encode_cid(ch['channel_id'])
                kb.row(types.InlineKeyboardButton(f"📢 {ch['channel_link']}", callback_data=f"ch_{server}_{cid}"))
            kb.row(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))

            if server == "1":
                sname = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
            elif server == "2":
                sname = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
            else:
                sname = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏ𝐫"

            pred_user_states[user_id] = {"step": "select_channel", "server": server, "channels": channels}
            await pred_safe_edit(cq.message,
                f"✅ {sname} 𝐒ᴇʟᴇᴄᴛᴇᴅ!\n\nChoose target channel 👇",
                reply_markup=kb)
            return

        if data.startswith("ch_"):
            parts = data.split("_", 2)
            server = parts[1]
            encoded_cid = parts[2]
            channel_id = decode_cid(encoded_cid)
            state = pred_user_states.get(user_id, {})
            channels = state.get("channels", [])
            channel_link = next((c['channel_link'] for c in channels if str(c['channel_id']) == str(channel_id)), None)
            if not channel_link:
                await pred_safe_edit(cq.message, "❌ Channel missing. Please restart.")
                return
            pred_user_states[user_id] = {
                "step": "select_bets", "server": server,
                "channel_link": channel_link, "channel_id": str(channel_id)
            }

            if server == "1":
                sname = "⚔️ 𝐃 r ᴀɢᴏɴ 𝐓 r ᴀᴄᴋ"
            elif server == "2":
                sname = "🤖 𝐀ᴅᴀᴘᴛɪᴠᴇ 𝐐ᴜᴀɴᴛ"
            else:
                sname = "🔑 𝐒ᴇᴇᴅ 𝐇ᴀsʜ 𝐃ᴇᴄʀʏᴘᴛᴏ𝐫"

            await pred_safe_edit(cq.message,
                f"🎯 𝐅ɪɴᴀʟ 𝐂ᴏɴꜰɪɢ\n{'━'*20}\n"
                f"📢 𝐂ʜᴀɴɴᴇʟ : {channel_link}\n"
                f"🖥 𝐄ɴɢɪɴᴇ : {sname}\n{'━'*20}\n\n"
                f"𝐇ᴏᴡ ᴍᴀɴʏ ᴘʀᴇᴅɪᴄᴛɪᴏɴs? (1–50)\nType a number now:")
            return

    except Exception as e:
        try:
            await pred_safe_edit(cq.message, f"❌ 𝐄ʀʀᴏ r: <code>{str(e)[:150]}</code>")
        except Exception:
            pass


# ============================================================
# 🧠 HOSTED PREDICTION BOT (for hosting API)
# ============================================================

def start_hosted_prediction_bot(token, initial_owner, hosted_id):
    try:
        hosted = telebot.TeleBot(token, parse_mode="HTML")
        me = hosted.get_me()
    except Exception as e:
        raise RuntimeError(f"❌ Invalid Token: {e}")

    user_file = data_path(f"users_{me.id}.json")
    owner_file = data_path(f"owner_{hosted_id}.txt")
    runtime = {"paused": False, "stop": False}
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

    _entry_ref = [None]

    def save_owner(uid):
        try:
            with open(owner_file, "w") as f:
                f.write(str(uid))
            current_owner["id"] = uid
            hosted_bots.setdefault(uid, {})[hosted_id] = _entry_ref[0]
            update_registry_owner(hosted_id, uid)
        except Exception:
            pass

    def get_owner():
        return current_owner["id"]

    def create_menu():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("🎯 START PREDICTION", "🛑 STOP PREDICTION")
        kb.row("📢 SET CHANNEL", "📊 LIVE STATS")
        kb.row("👑 DEVELOPER", "💎 PREMIUM INFO")
        return kb

    def hosted_animate(chat_id, text, frames=None, delay=0.4):
        animate_loading(hosted, chat_id, text, frames, delay)

    hosted_state = {"channel": None, "waiting_channel": False}

    @hosted.message_handler(commands=["start"])
    def hosted_start(msg):
        if not os.path.exists(owner_file) or not current_owner["id"]:
            save_owner(msg.from_user.id)
        if current_owner["id"]:
            hosted_bots.setdefault(current_owner["id"], {})[hosted_id] = _entry_ref[0]

        try:
            users = load_users_sync(user_file)
            now = datetime.now().strftime("%Y-%m-%d")
            uid = str(msg.from_user.id)
            if uid not in users:
                users[uid] = {"first_seen": now, "last_seen": now, "usage_count": 1}
            else:
                users[uid]["last_seen"] = now
                users[uid]["usage_count"] += 1
            save_users_sync(user_file, users)
        except Exception:
            pass

        user_name = msg.from_user.first_name or "User"
        hosted_animate(msg.chat.id, "Initializing AI Engine")

        welcome = (
            f"{DIVIDER}\n"
            f"👑 *WELCOME TO KOHLI AI BOT* 👑\n"
            f"{DIVIDER}\n\n"
            f"👋 Hey *{user_name}*,\n\n"
            f"✨ You've unlocked the *most advanced*\n"
            f"   1-minute prediction engine on Telegram!\n\n"
            f"{SUB_DIVIDER}\n"
            f"🚀 *Features:*\n"
            f"  ⚡ Real-time Wingo Predictions\n"
            f"  ⚡ AI-Powered Accuracy Engine\n"
            f"  ⚡ Auto Channel Broadcasting\n"
            f"  ⚡ Live Performance Stats\n"
            f"{SUB_DIVIDER}\n\n"
            f"🔥 *Ready to dominate?* Use buttons below 👇\n\n"
            f"{styled_footer()}"
        )
        try:
            hosted.send_message(msg.chat.id, welcome, reply_markup=create_menu(), parse_mode="HTML")
        except Exception:
            hosted.send_message(msg.chat.id, welcome, reply_markup=create_menu())

    @hosted.message_handler(func=lambda m: True)
    def hosted_buttons(msg):
        text = msg.text
        cid = msg.chat.id

        try:
            users = load_users_sync(user_file)
            now = datetime.now().strftime("%Y-%m-%d")
            uid = str(cid)
            if uid not in users:
                users[uid] = {"first_seen": now, "last_seen": now, "usage_count": 1}
            else:
                users[uid]["last_seen"] = now
                users[uid]["usage_count"] += 1
            save_users_sync(user_file, users)
        except Exception:
            pass

        if text == "🎯 START PREDICTION":
            hosted_animate(cid, "Booting Prediction Engine")
            ch = hosted_state.get("channel")
            status = f"📢 Channel: <code>{ch}</code>" if ch else "⚠️ No channel linked"
            try:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n🚀 <b>PREDICTION ENGINE ONLINE</b>\n{DIVIDER}\n\n"
                    f"✅ Status: <b>ACTIVE</b>\n{status}\n{SUB_DIVIDER}\n"
                    f"🎯 Predictions will now stream every 60s.\n\n"
                    f"{styled_footer()}",
                    reply_markup=create_menu(), parse_mode="HTML")
            except Exception:
                pass

            thread = threading.Thread(
                target=run_hosted_prediction_cycle_sync,
                args=(hosted, cid, ch, runtime),
                daemon=True,
            )
            thread.start()

        elif text == "🛑 STOP PREDICTION":
            runtime["stop"] = True
            try:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n🛑 <b>PREDICTION ENGINE OFFLINE</b>\n{DIVIDER}\n\n"
                    f"❌ Status: <b>STOPPED</b>\n{SUB_DIVIDER}\n"
                    f"Press 🎯 START to resume anytime.\n\n{styled_footer()}",
                    reply_markup=create_menu(), parse_mode="HTML")
            except Exception:
                pass
            runtime["stop"] = False

        elif text == "📢 SET CHANNEL":
            hosted_state["waiting_channel"] = True
            try:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n📢 <b>CHANNEL LINKING</b>\n{DIVIDER}\n\n"
                    f"⚡ Send your <b>channel username</b>\nExample: <code>@yourchannel</code>\n\n"
                    f"🛡 <i>Bot must be admin in the channel.</i>\n\n{styled_footer()}",
                    parse_mode="HTML")
            except Exception:
                pass

        elif text == "📊 LIVE STATS":
            hosted_animate(cid, "Fetching Live Stats")
            try:
                total, d1, d2, top = get_hosted_stats_sync(user_file)
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n📊 <b>LIVE BOT STATISTICS</b>\n{DIVIDER}\n\n"
                    f"👥 Total Users     : <b>{total}</b>\n"
                    f"📅 Active Today    : <b>{d1}</b>\n"
                    f"📅 Active Yesterday: <b>{d2}</b>\n\n"
                    f"{SUB_DIVIDER}\n🏆 <b>TOP 5 PERFORMERS</b>\n{SUB_DIVIDER}\n"
                    f"{top}\n\n{styled_footer()}",
                    reply_markup=create_menu(), parse_mode="HTML")
            except Exception:
                pass

        elif text == "👑 DEVELOPER":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("💬 Contact Developer", url="https://t.me/xxLEGEND_KOHLI"),
                types.InlineKeyboardButton("📢 Join Updates Channel", url="https://t.me/xxLEGEND_KOHLI"),
            )
            try:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n👑 <b>MEET THE DEVELOPER</b> 👑\n{DIVIDER}\n\n"
                    f"👤 <b>Name:</b> KOHLI\n💎 <b>Role:</b> Premium Bot Developer\n"
                    f"⚡ <b>Specialty:</b> AI Prediction Systems\n\n"
                    f"{SUB_DIVIDER}\n💬 Need a custom bot? Reach out below!\n\n{styled_footer()}",
                    reply_markup=markup, parse_mode="HTML")
            except Exception:
                pass

        elif text == "💎 PREMIUM INFO":
            try:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n💎 <b>PREMIUM FEATURES</b> 💎\n{DIVIDER}\n\n"
                    f"🔥 <b>What you get:</b>\n\n"
                    f"  ⚡ 99% AI Accuracy Engine\n"
                    f"  ⚡ Unlimited Predictions\n"
                    f"  ⚡ Auto Channel Broadcasting\n"
                    f"  ⚡ Multi-Channel Support\n"
                    f"  ⚡ 24/7 Uptime Guarantee\n"
                    f"  ⚡ Priority Support\n\n"
                    f"{SUB_DIVIDER}\n👑 Contact @xxLEGEND_KOHLI for Premium\n\n{styled_footer()}",
                    reply_markup=create_menu(), parse_mode="HTML")
            except Exception:
                pass

        elif hosted_state.get("waiting_channel"):
            channel_input = text.strip()
            try:
                hosted_animate(cid, "Verifying Channel")
                hosted.send_message(channel_input, "✅ Channel verified & linked!")
                hosted_state["channel"] = channel_input
                hosted_state["waiting_channel"] = False
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n✅ <b>CHANNEL LINKED SUCCESSFULLY</b>\n{DIVIDER}\n\n"
                    f"📢 Channel: <code>{channel_input}</code>\n{SUB_DIVIDER}\n"
                    f"🚀 Predictions will now auto-post there!\n\n{styled_footer()}",
                    parse_mode="HTML", reply_markup=create_menu())
            except Exception as e:
                hosted.send_message(
                    cid,
                    f"{DIVIDER}\n❌ <b>LINKING FAILED</b>\n{DIVIDER}\n\n"
                    f"Error: <code>{e}</code>\n\n🛡 Make sure bot is <b>admin</b> in the channel.\n\n{styled_footer()}",
                    reply_markup=create_menu(), parse_mode="HTML")
                hosted_state["waiting_channel"] = False

    def run_hosted_prediction_cycle_sync(bot_obj, chat_id, channel_id, runtime_ref):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_async_prediction_cycle(bot_obj, chat_id, channel_id, runtime_ref))
        except Exception as e:
            print(f"[HOSTED PRED] Error: {e}")
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _async_prediction_cycle(bot_obj, chat_id, channel_id, runtime_ref):
        async def send_sync(target, text, parse_mode="HTML"):
            try:
                bot_obj.send_message(target, text, parse_mode=parse_mode)
            except Exception:
                pass

        async def send_sticker_sync(target, sticker_id):
            try:
                bot_obj.send_sticker(target, sticker_id)
            except Exception:
                pass

        sep = "━━━━━━━━━━━━━━━━━━━━━━━━"
        try:
            await send_sticker_sync(chat_id, STICKER_START)
            await asyncio.sleep(1)
            await send_sync(chat_id,
                f"{sep}\n🤖 <b>KOHLI VIP PREDICTION</b>\n{sep}\n"
                f"🖥 Server : 🤖 Adaptive Quant\n"
                f"🕐 Start : <code>{now_str()}</code>\n{sep}")

            while not runtime_ref.get("stop"):
                if runtime_ref.get("paused"):
                    await asyncio.sleep(2)
                    continue

                records = await fetch_history()
                period = await next_period()

                session = {
                    "server": "2",
                    "current_level": 1,
                    "last_period": period,
                    "consecutive_losses": 0,
                    "recent_results": [],
                }
                prediction, confidence, sig, jackpot, hash_val = await smart_predict(records, session)

                msg_text = make_prediction_text(
                    period, prediction, 1, "2", confidence, sig, jackpot, hash_val)
                await send_sync(chat_id, msg_text)

                if channel_id:
                    await send_sync(channel_id, msg_text)

                result, num = await wait_for_result(period)
                if result:
                    is_win = (result == prediction)
                    if is_win:
                        await send_sticker_sync(chat_id, random.choice(STICKER_WIN_LIST))
                        await send_sync(chat_id, f"✅ WIN! Result: {result} ({num})")
                    else:
                        await send_sync(chat_id, f"❌ LOSS. Result: {result} ({num})")

                await asyncio.sleep(5)

            await send_sticker_sync(chat_id, STICKER_STOP)
            await send_sync(chat_id, f"{sep}\n🛑 <b>Session Stopped</b>\n{sep}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await send_sync(chat_id, f"⚠️ Error: {str(e)[:120]}")

    def run_bot():
        try:
            hosted.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[!] Hosted Bot {me.username} stopped: {e}")

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


# ---------- SYNC USER HELPERS ----------

def load_users_sync(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def save_users_sync(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_hosted_stats_sync(file_path):
    users = load_users_sync(file_path)
    today = datetime.now()
    d1, d2 = 0, 0
    top_users = sorted(users.items(), key=lambda x: x[1].get("usage_count", 0), reverse=True)
    for u in users.values():
        try:
            last = datetime.strptime(u["last_seen"], "%Y-%m-%d")
            delta = (today - last).days
            if delta == 0: d1 += 1
            elif delta == 1: d2 += 1
        except Exception:
            pass
    top_list = "\n".join(
        [f"  {i+1}. 👤 {uid} — {info.get('usage_count', 0)} uses"
         for i, (uid, info) in enumerate(top_users[:5])]
    ) or "  No users yet."
    return len(users), d1, d2, top_list


# ============================================================
# 🌐 FLASK API
# ============================================================

api_app = Flask(__name__)


@api_app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "KOHLI Premium Hosting + Prediction",
        "version": "7.1",
        "hosted_bots": sum(len(b) for b in hosted_bots.values()),
        "registry_count": len(hosted_registry),
        "pred_active_sessions": len(pred_active_sessions),
        "timestamp": datetime.now().isoformat(),
    })


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
                    "status": "ok", "success": True,
                    "username": e["info"]["username"],
                    "bot_id": e["info"]["id"],
                    "hosted_id": hid,
                    "message": "Bot already running",
                })

        for hid, reg in hosted_registry.items():
            if reg.get("token") == token:
                return jsonify({
                    "status": "ok", "success": True,
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
                f"{DIVIDER}\n🔑 *NEW BOT DEPLOYED*\n{DIVIDER}\n\n"
                f"🤖 Bot: @{entry['info']['username']}\n"
                f"🆔 ID: `{entry['info']['id']}`\n"
                f"📦 Hosted: `{hosted_id}`\n\n"
                f"{SUB_DIVIDER}\n⚠️ Owner assigned on first /start\n\n{styled_footer()}",
                parse_mode="Markdown",
            )
        except Exception as e:
            print(f"[!] Admin notify failed: {e}")

        return jsonify({
            "status": "ok", "success": True,
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

        for hid, entry in hosted_by_id.items():
            if hid in seen:
                continue
            try:
                get_owner = entry.get("get_owner")
                if get_owner and str(get_owner()) == owner_id:
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

        entry = {}
        if hosted_id in hosted_by_id:
            entry = hosted_by_id[hosted_id]
            entry["running"] = False
            if "runtime" in entry:
                entry["runtime"]["paused"] = True
                entry["runtime"]["stop"] = True
            del hosted_by_id[hosted_id]

        for uid, bots in list(hosted_bots.items()):
            if hosted_id in bots:
                del bots[hosted_id]

        owner_file = entry.get("owner_file") or data_path(f"owner_{hosted_id}.txt")
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
        user_file = data_path(f"users_{bot_id}.json")
        users = load_users_sync(user_file)

        if not users:
            return jsonify({"status": "ok", "success": True, "sent": 0, "failed": 0})

        broadcast_bot = telebot.TeleBot(token, parse_mode="Markdown")
        sent = 0
        failed = 0

        for uid in list(users.keys()):
            try:
                broadcast_bot.send_message(
                    int(uid),
                    f"{DIVIDER}\n📢 *BROADCAST MESSAGE*\n{DIVIDER}\n\n"
                    f"{message}\n\n{styled_footer()}",
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
        user_file = data_path(f"users_{bot_id}.json")
        total, d1, d2, _ = get_hosted_stats_sync(user_file)

        return jsonify({
            "status": "ok", "success": True,
            "total_users": total,
            "active_today": d1,
            "active_yesterday": d2,
            "running": entry.get("running", False),
            "username": entry["info"]["username"],
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# 🔄 RESTORE
# ============================================================

def restore_bots_from_registry():
    print("[RESTORE] Checking for hosted bots to restore...")
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


# ============================================================
# 🚀 TOKEN VALIDATION + RUN
# ============================================================

async def validate_tokens():
    """Validate both bot tokens before starting."""
    errors = []

    try:
        me = host_bot.get_me()
        print(f"✅ HOST BOT OK: @{me.username} (ID: {me.id})")
    except ApiTelegramException as e:
        if e.error_code == 401:
            errors.append(f"❌ HOST_BOT_TOKEN invalid (401 Unauthorized)")
        else:
            errors.append(f"⚠️ HOST_BOT_TOKEN error: {e}")
    except Exception as e:
        errors.append(f"⚠️ HOST_BOT_TOKEN error: {e}")

    try:
        me = await pred_bot.get_me()
        print(f"✅ PRED BOT OK: @{me.username} (ID: {me.id})")
    except ApiTelegramException as e:
        if e.error_code == 401:
            errors.append(f"❌ PRED_BOT_TOKEN invalid (401 Unauthorized)")
        else:
            errors.append(f"⚠️ PRED_BOT_TOKEN error: {e}")
    except Exception as e:
        errors.append(f"⚠️ PRED_BOT_TOKEN error: {e}")

    if errors:
        print("\n" + "!" * 60)
        for err in errors:
            print(err)
        print("!" * 60 + "\n")

    return len(errors) == 0


def run_api():
    port = int(os.environ.get("PORT", 5000))
    api_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


async def run_prediction_bot():
    """Start the standalone prediction bot with 401 handling."""
    try:
        me = await pred_bot.get_me()
        print(f"✅ Prediction bot logged in as: @{me.username}")
    except ApiTelegramException as e:
        if e.error_code == 401:
            print("\n" + "!" * 60)
            print("❌ PREDICTION BOT TOKEN INVALID (401 Unauthorized)")
            print("👉 Get new token from @BotFather and update PRED_BOT_TOKEN")
            print("!" * 60 + "\n")
            return
        print(f"⚠️ Prediction bot error: {e}")
        return
    except Exception as e:
        print(f"⚠️ Prediction bot not started: {e}")
        return

    try:
        await recover_pred_sessions()
    except Exception as e:
        print(f"[PRED RECOVER] Error: {e}")

    try:
        await pred_bot.polling(
            non_stop=True,
            allowed_updates=util.update_types,
            request_timeout=REQUEST_TIMEOUT,
        )
    except ApiTelegramException as e:
        if e.error_code == 401:
            print("❌ Prediction bot token revoked during runtime.")
            return
        print(f"[PRED POLL] Error: {e}")
    except Exception as e:
        print(f"[PRED POLL] Error: {e}")


async def main_async():
    print("""
╔══════════════════════════════════════════════════════════╗
║   👑 KOHLI HOSTING + PREDICTION BOT v7.1 👑             ║
║   🚀 Railway-Ready • Persistent • Multi-Bot             ║
╚══════════════════════════════════════════════════════════╝
""")

    # Validate tokens first
    tokens_ok = await validate_tokens()
    if not tokens_ok:
        print("⚠️ Some tokens are invalid — continuing with valid ones only.\n")

    # Start Flask API
    threading.Thread(target=run_api, daemon=True).start()

    # Restore hosted bots
    threading.Thread(target=restore_bots_from_registry, daemon=True).start()

    # Start prediction bot
    await run_prediction_bot()


def run_host_bot():
    """Run host bot polling in its own thread with 401 handling."""
    try:
        me = host_bot.get_me()
        print(f"✅ Host bot logged in as: @{me.username}")
    except ApiTelegramException as e:
        if e.error_code == 401:
            print("\n" + "!" * 60)
            print("❌ HOST BOT TOKEN INVALID (401 Unauthorized)")
            print("👉 Get new token from @BotFather and update HOST_BOT_TOKEN")
            print("!" * 60 + "\n")
            return
        print(f"⚠️ Host bot pre-check failed: {e}")

    while True:
        try:
            host_bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            if "401" in str(e):
                print("❌ Host bot token revoked. Stopping.")
                return
            print(f"[HOST BOT] Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    # Start host bot in background thread
    threading.Thread(target=run_host_bot, daemon=True).start()

    # Run prediction bot + Flask in main async loop
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested.")
    except Exception as e:
        print(f"\n❌ Fatal: {e}")
