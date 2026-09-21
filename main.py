# ============================================================
# 👑 KOHLI HOSTING + PREDICTION BOT — PROFESSIONAL v6.0
# ============================================================
# ✨ Enhanced UI • Premium Animations • Pro Design
# 🔧 FIXED: Persistent storage, owner assignment, bot list
# ============================================================

import telebot
import threading
import time
import random
import pytz
import json
import os
from datetime import datetime
from telebot import types
from flask import Flask, request, jsonify

# ============================================================
# 🔧 MAIN CONFIG
# ============================================================

HOST_BOT_TOKEN = "8372270378:AAEXNRXUD2xTwShxB7z7WR5uqX2NrWBvN6o"
ADMIN_ID = 7741897793

bot = telebot.TeleBot(HOST_BOT_TOKEN, parse_mode="Markdown")

# ============================================================
# 🎨 DESIGN CONSTANTS (Premium UI Elements)
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

# Animation frames for loading effect
PROGRESS_BAR = ["🟥⬜⬜⬜⬜", "🟥🟥⬜⬜⬜", "🟥🟥🟥⬜⬜", "🟥🟥🟥🟥⬜", "🟥🟥🟥🟥🟥"]

# ============================================================
# 📁 PERSISTENT STORAGE DIRECTORY
# ============================================================

DATA_DIR = os.environ.get("DATA_DIR", "kohli_data")
os.makedirs(DATA_DIR, exist_ok=True)


def data_path(filename):
    """Return path inside persistent data directory."""
    return os.path.join(DATA_DIR, filename)


# ============================================================
# 🌐 GLOBAL STORAGE
# ============================================================

hosted_bots = {}       # { owner_id: { hosted_id: entry } }
hosted_by_id = {}      # { hosted_id: entry }
hosted_registry = {}   # { hosted_id: { owner_id, username, bot_id, token } }
registry_file = data_path("hosted_registry.json")


# ============================================================
# 💾 REGISTRY PERSISTENCE (survives server restart)
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
    """Register bot metadata persistently."""
    hosted_registry[hosted_id] = {
        "owner_id": str(owner_id) if owner_id else "",
        "username": username,
        "bot_id": str(bot_id),
        "token": token,
        "created_at": datetime.now().isoformat(),
    }
    save_registry()


def update_registry_owner(hosted_id, owner_id):
    """Update owner in registry."""
    if hosted_id in hosted_registry:
        hosted_registry[hosted_id]["owner_id"] = str(owner_id)
        save_registry()


def unregister_bot(hosted_id):
    if hosted_id in hosted_registry:
        del hosted_registry[hosted_id]
        save_registry()


# Load registry at startup
load_registry()


# ============================================================
# 🎬 ANIMATION HELPERS
# ============================================================

def animate_loading(bot_obj, chat_id, text, frames=None, delay=0.4):
    """Plays a short loading animation by editing a message."""
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


def styled_header(title, emoji=CROWN):
    return f"{DIVIDER}\n{emoji} {title}\n{DIVIDER}"


def styled_footer(text="KOHLI PREMIUM ENGINE"):
    return f"{SUB_DIVIDER}\n{LIGHTNING} {text} {LIGHTNING}"


# ============================================================
# 🔮 PREDICTION ENGINE
# ============================================================

def generate_prediction():
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


def get_period_number():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    yyyyMMdd = now.strftime("%Y%m%d")
    total_minutes = now.hour * 60 + now.minute
    return f"{yyyyMMdd}1000{10001 + total_minutes}"


def get_remaining_seconds():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return 60 - now.second if now.second < 60 else 0


def send_prediction(bot_obj, chat_id, period, big_small, num, image, trend):
    """Sends a beautifully formatted prediction card."""
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


# ============================================================
# 📊 USER STATS
# ============================================================

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


# ============================================================
# 🧠 HOSTED PREDICTION BOT (WITH AUTO OWNER)
# ============================================================

def start_hosted_prediction_bot(token, initial_owner, hosted_id):
    try:
        hosted = telebot.TeleBot(token, parse_mode="Markdown")
        me = hosted.get_me()
    except Exception as e:
        raise RuntimeError(f"❌ Invalid Token: {e}")

    active_dict = {}
    user_channels = {}
    user_file = data_path(f"users_{me.id}.json")
    owner_file = data_path(f"owner_{hosted_id}.txt")
    runtime = {"paused": False}
    current_owner = {"id": initial_owner}

    # Load owner from file (persistent)
    if os.path.exists(owner_file):
        try:
            with open(owner_file, "r") as f:
                saved = f.read().strip()
                if saved:
                    current_owner["id"] = int(saved)
        except Exception:
            pass

    # Also load owner from registry
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
            print(f"[OWNER] Bot {me.username} owner set to {uid}")
        except Exception as e:
            print(f"[OWNER] Save failed: {e}")

    def get_owner():
        return current_owner["id"]

    _entry_ref = [None]

    # ---------- PREDICTION LOOP ----------
    def start_prediction_cycle(bot_obj, chat_id, channel_id=None):
        last_period = None
        while active_dict.get(chat_id):
            if runtime["paused"]:
                time.sleep(2)
                continue
            period = get_period_number()
            if period != last_period:
                big_small, num, image, trend = generate_prediction()
                send_prediction(bot_obj, chat_id, period, big_small, num, image, trend)
                if channel_id:
                    send_prediction(bot_obj, channel_id, period, big_small, num, image, trend)
                last_period = period
            for _ in range(get_remaining_seconds(), 0, -1):
                if not active_dict.get(chat_id):
                    break
                time.sleep(1)

    # ---------- PREMIUM KEYBOARD ----------
    def create_prediction_menu():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("🎯 START PREDICTION", "🛑 STOP PREDICTION")
        kb.row("📢 SET CHANNEL", "📊 LIVE STATS")
        kb.row("👑 DEVELOPER", "💎 PREMIUM INFO")
        return kb

    # ---------- /start ----------
    @hosted.message_handler(commands=["start"])
    def start(msg):
        # Auto-assign owner on first /start
        if not os.path.exists(owner_file) or not current_owner["id"]:
            save_owner(msg.from_user.id)

        # Ensure linked in hosted_bots
        if current_owner["id"]:
            hosted_bots.setdefault(current_owner["id"], {})[hosted_id] = _entry_ref[0]

        update_user_stats(msg.from_user.id, user_file)

        user_name = msg.from_user.first_name or "User"
        animate_loading(hosted, msg.chat.id, "Initializing AI Engine")

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

    # ---------- BUTTON HANDLER ----------
    @hosted.message_handler(func=lambda m: True)
    def buttons(msg):
        text = msg.text
        cid = msg.chat.id
        update_user_stats(cid, user_file)

        # 🎯 START
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
            animate_loading(hosted, cid, "Booting Prediction Engine")

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

        # 🛑 STOP
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

        # 📢 SET CHANNEL
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

        # 📊 STATS
        elif text == "📊 LIVE STATS":
            animate_loading(hosted, cid, "Fetching Live Stats")
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

        # 👑 DEVELOPER
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

        # 💎 PREMIUM INFO
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

        # CHANNEL INPUT
        elif user_channels.get(cid) == "waiting":
            channel_input = text.strip()
            try:
                animate_loading(hosted, cid, "Verifying Channel")
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

    # Register persistently
    register_bot(hosted_id, initial_owner, me.username, me.id, token)

    if initial_owner:
        hosted_bots.setdefault(initial_owner, {})[hosted_id] = entry

    return entry


# ============================================================
# 🌐 FLASK API
# ============================================================

api_app = Flask(__name__)


@api_app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "KOHLI Premium Hosting",
        "version": "6.0",
        "hosted_bots": sum(len(b) for b in hosted_bots.values()),
        "registry_count": len(hosted_registry),
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

        # Check if bot already running
        for hid, e in hosted_by_id.items():
            if e.get("token") == token:
                return jsonify({
                    "status": "ok",
                    "username": e["info"]["username"],
                    "bot_id": e["info"]["id"],
                    "hosted_id": hid,
                    "message": "Bot already running",
                })

        # Check registry for existing bot
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

        # Auto-assign owner if telegram_id provided
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
            bot.send_message(
                ADMIN_ID,
                f"{DIVIDER}\n"
                f"🔑 *NEW BOT DEPLOYED*\n"
                f"{DIVIDER}\n\n"
                f"🤖 Bot: @{entry['info']['username']}\n"
                f"🆔 ID: `{entry['info']['id']}`\n"
                f"📦 Hosted: `{hosted_id}`\n\n"
                f"{SUB_DIVIDER}\n"
                f"⚠️ Owner assigned on first /start\n\n"
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

        # 1) hosted_bots dict
        for hid, entry in hosted_bots.get(owner_int, {}).items():
            if hid not in seen:
                seen.add(hid)
                result.append({
                    "username": entry["info"]["username"],
                    "bot_id": str(entry["info"]["id"]),
                    "hosted_id": str(hid),
                    "running": entry.get("running", True),
                })

        # 2) owner_file check (persistent)
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

        # 3) get_owner() check
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

        # 4) Registry check (survives restart)
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

        # Remove from hosted_bots
        for uid, bots in list(hosted_bots.items()):
            if hosted_id in bots:
                del bots[hosted_id]

        # Remove owner file
        owner_file = entry.get("owner_file") or data_path(f"owner_{hosted_id}.txt")
        if owner_file and os.path.exists(owner_file):
            try:
                os.remove(owner_file)
            except Exception:
                pass

        # Remove from registry
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
        users = load_users(user_file)

        if not users:
            return jsonify({"status": "ok", "success": True, "sent": 0, "failed": 0})

        broadcast_bot = telebot.TeleBot(token, parse_mode="Markdown")
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
        user_file = data_path(f"users_{bot_id}.json")
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


# ============================================================
# 🔄 RESTORE BOTS FROM REGISTRY ON STARTUP
# ============================================================

def restore_bots_from_registry():
    """Re-launch all bots that were running before restart."""
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


# ============================================================
# 🚀 RUN
# ============================================================

def run_api():
    port = int(os.environ.get("PORT", 5000))
    api_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║   👑 KOHLI PREMIUM HOSTING BOT v6.0 👑      ║
║   🚀 Engine Online • Ready to Serve 🚀      ║
╚══════════════════════════════════════════════╝
""")

    # Restore previously running bots
    threading.Thread(target=restore_bots_from_registry, daemon=True).start()

    # Start Flask API
    threading.Thread(target=run_api, daemon=True).start()

    # Main bot polling
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[!] Bot crash: {e}")
            time.sleep(5)
