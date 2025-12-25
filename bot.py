import telebot
from telebot import types
import json
import os

# ============================
# BOT SOZLAMALARI
# ============================
TOKEN = "8211203712:AAHdM1wShReC3Jq60qX_PR9XesR0xtsxSg0"
ADMIN_ID = 8383448395

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ============================
# FAYLLAR
# ============================
DB_FILE = "kino_baza.json"
USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"
CLICKS_FILE = "clicks.json"

# ============================
# YORDAMCHI FUNKSIYALAR
# ============================
def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ============================
# MA’LUMOTLAR
# ============================
kino_baza = load_json(DB_FILE, {})
users = load_json(USERS_FILE, [])
channels = load_json(CHANNELS_FILE, [
    ["1-kanal", "https://t.me/kinolar_proo"],
    ["Instagram", "https://www.instagram.com/_pardanazarov1_?igsh=MXBodWFtdWF3MDcwdA=="]
])
clicks = load_json(CLICKS_FILE, {})

# ============================
# START
# ============================
@bot.message_handler(commands=["start"])
def start(msg):
    chat_id = str(msg.chat.id)

    if chat_id not in users:
        users.append(chat_id)
        save_json(USERS_FILE, users)

    clicks[chat_id] = [0] * len(channels)
    save_json(CLICKS_FILE, clicks)

    inline = types.InlineKeyboardMarkup()
    for name, link in channels:
        inline.add(types.InlineKeyboardButton(f"📌 {name}", url=link))
    inline.add(types.InlineKeyboardButton("✔ Obuna bo‘ldim", callback_data="check"))

    bot.send_message(chat_id, "👇 Kanallar tugmalarini bosing:", reply_markup=inline)

    user_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(chat_id, "📩 Menyudan tanlang:", reply_markup=user_kb)

    if msg.from_user.id == ADMIN_ID:
        admin_panel(msg.chat.id)

# ============================
# ADMIN PANEL
# ============================
def admin_panel(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Kino qo‘shish", "❌ Kino o‘chirish")
    kb.row("➕ Kanal qo‘shish", "❌ Kanal o‘chirish")
    kb.row("📊 Statistika")
    kb.row("📢 Reklama yuborish")
    bot.send_message(chat_id, "🔧 Admin panel:", reply_markup=kb)

# ============================
# OBUNA (FAKE)
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "check")
def check(call):
    chat_id = str(call.message.chat.id)
    clicks[chat_id] = [1] * len(channels)
    save_json(CLICKS_FILE, clicks)
    bot.answer_callback_query(call.id, "Qabul qilindi!")
    bot.send_message(chat_id, "🎬 Endi kino kodini yuboring!")

# ============================
# ADMIN TUGMALARI
# ============================
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_buttons(msg):

    if msg.text == "➕ Kino qo‘shish":
        bot.send_message(msg.chat.id, "🎥 Video yuboring:")
        return bot.register_next_step_handler(msg, add_video)

    if msg.text == "❌ Kino o‘chirish":
        bot.send_message(msg.chat.id, "🗑 Kino kodini yuboring:")
        return bot.register_next_step_handler(msg, delete_kino)

    if msg.text == "➕ Kanal qo‘shish":
        bot.send_message(msg.chat.id, "📛 Kanal nomini yuboring:")
        return bot.register_next_step_handler(msg, get_channel_name)

    if msg.text == "❌ Kanal o‘chirish":
        bot.send_message(msg.chat.id, "🔢 Kanal raqami (1,2,3):")
        return bot.register_next_step_handler(msg, delete_channel)

    if msg.text == "📊 Statistika":
        return send_stat(msg)

    if msg.text == "📢 Reklama yuborish":
        bot.send_message(msg.chat.id, "📢 Reklama matnini yuboring:")
        return bot.register_next_step_handler(msg, send_advert)

# ============================
# KINO QO‘SHISH
# ============================
def add_video(msg):
    if not msg.video:
        return bot.send_message(msg.chat.id, "❌ Video yuboring!")

    file_id = msg.video.file_id
    bot.send_message(msg.chat.id, "🎬 Kino nomi:")
    bot.register_next_step_handler(msg, lambda m: get_kino_code(m, file_id))

def get_kino_code(msg, file_id):
    name = msg.text
    bot.send_message(msg.chat.id, "🔑 Kino kodi:")
    bot.register_next_step_handler(msg, lambda m: save_kino(m, file_id, name))

def save_kino(msg, file_id, name):
    code = msg.text.strip()
    kino_baza[code] = {"name": name, "file_id": file_id}
    save_json(DB_FILE, kino_baza)
    bot.send_message(msg.chat.id, "✅ Kino saqlandi!")

# ============================
# KINO O‘CHIRISH
# ============================
def delete_kino(msg):
    code = msg.text.strip()
    if code in kino_baza:
        del kino_baza[code]
        save_json(DB_FILE, kino_baza)
        bot.send_message(msg.chat.id, "❌ Kino o‘chirildi!")
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kod yo‘q!")

# ============================
# KANAL QO‘SHISH / O‘CHIRISH
# ============================
def get_channel_name(msg):
    name = msg.text
    bot.send_message(msg.chat.id, "🔗 Kanal linki:")
    bot.register_next_step_handler(msg, lambda m: save_channel(m, name))

def save_channel(msg, name):
    link = msg.text
    channels.append([name, link])
    save_json(CHANNELS_FILE, channels)
    bot.send_message(msg.chat.id, "✅ Kanal qo‘shildi!")

def delete_channel(msg):
    try:
        i = int(msg.text) - 1
        removed = channels.pop(i)
        save_json(CHANNELS_FILE, channels)
        bot.send_message(msg.chat.id, f"❌ O‘chirildi: {removed[0]}")
    except:
        bot.send_message(msg.chat.id, "❌ Noto‘g‘ri raqam!")

# ============================
# STATISTIKA
# ============================
def send_stat(msg):
    text = (
        f"📊 STATISTIKA\n\n"
        f"👥 Foydalanuvchilar: {len(users)}\n"
        f"🎬 Kinolar: {len(kino_baza)}\n"
        f"📌 Kanallar: {len(channels)}"
    )
    bot.send_message(msg.chat.id, text)

# ============================
# USER KOD YUBORADI
# ============================
@bot.message_handler(func=lambda m: True)
def user_code(msg):
    code = msg.text.strip()
    if code in kino_baza:
        d = kino_baza[code]
        bot.send_video(msg.chat.id, d["file_id"], caption=d["name"])
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kod topilmadi!")

# ============================
# BOT ISHLASHI
# ============================
print("BOT ISHLAMOQDA...")
bot.infinity_polling()
