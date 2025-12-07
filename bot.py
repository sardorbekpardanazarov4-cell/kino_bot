import telebot
from telebot import types
import json
import os
from collections import Counter

# ============================
# BOT SOZLAMALARI
# ============================
TOKEN = "8211203712:AAHdM1wShReC3Jq60qX_PR9XesR0xtsxSg0"
ADMIN_ID = 8383448395

bot = telebot.TeleBot(TOKEN)

# 6 KANAL + INSTAGRAM
CHANNEL_LINKS = [
    ("1-kanal", "https://t.me/+njI2s4fSLbJlZTBi"),
    ("2-kanal", "https://t.me/+JFubXpf3EY40M2U6"),
    ("3-kanal", "https://t.me/+_PYMzySJjn9jM2U6"),
    ("4-kanal", "https://t.me/+R5IUtNr74rcwY2Y6"),
    ("5-kanal", "https://t.me/+JFubXpf3EY40M2U6"),
    ("Instagram", "https://www.instagram.com/kinolar_pro7?igsh=MXgyNnIzOWZ2aHpjYw==")
]

# Fayllar
DB_FILE = "kino_baza.json"
USERS_FILE = "users.json"
CLICKS_FILE = "clicks.json"

# ============================
# JSON FUNKSIYALARI
# ============================
def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

kino_baza = load_json(DB_FILE, {})
user_list = load_json(USERS_FILE, [])
user_clicks = load_json(CLICKS_FILE, {})
code_usage = Counter()

# ============================
# START
# ============================
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = str(msg.chat.id)

    # Admin panel tugmasi – faqat admin uchun
    if msg.from_user.id == ADMIN_ID:
        admin_panel(msg.chat.id)

    if chat_id not in user_list:
        user_list.append(chat_id)
        save_json(USERS_FILE, user_list)

    user_clicks[chat_id] = [0] * len(CHANNEL_LINKS)
    save_json(CLICKS_FILE, user_clicks)

    markup = types.InlineKeyboardMarkup()

    for name, link in CHANNEL_LINKS:
        btn = types.InlineKeyboardButton(f"📌 {name}", url=link)
        markup.add(btn)

    markup.add(types.InlineKeyboardButton("✔ Obuna bo‘ldim", callback_data="check"))

    bot.send_message(
        chat_id,
        "👇 Quyidagi barcha tugmalarni bosing, so‘ng 'Obuna bo‘ldim' tugmasini bosing:",
        reply_markup=markup
    )

# ============================
# ADMIN PANEL
# ============================
def admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Reklama yuborish")
    bot.send_message(chat_id, "🔧 Admin panel:", reply_markup=markup)

# ============================
# CALLBACK — OBUNA
# ============================
@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_subscription(call):
    chat_id = str(call.message.chat.id)

    user_clicks[chat_id] = [1] * len(CHANNEL_LINKS)
    save_json(CLICKS_FILE, user_clicks)

    bot.answer_callback_query(call.id, "Tekshirildi!")
    bot.send_message(chat_id, "🎉 Endi kino kodini yuboring!")

# ============================
# ADMIN — VIDEO QO‘SHISH
# ============================
@bot.message_handler(commands=['add'])
def admin_add(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⛔ Siz admin emassiz!")

    bot.send_message(msg.chat.id, "🎥 Video yuboring:")
    bot.register_next_step_handler(msg, get_video)

def get_video(msg):
    if not msg.video:
        return bot.reply_to(msg, "❗ Faqat video yuboring!")

    video_id = msg.video.file_id
    bot.send_message(msg.chat.id, "🎬 Kino nomi:")
    bot.register_next_step_handler(msg, lambda m: get_name(m, video_id))

def get_name(msg, file_id):
    name = msg.text
    bot.send_message(msg.chat.id, "🔑 Kodni kiriting:")
    bot.register_next_step_handler(msg, lambda m: save_kino(m, file_id, name))

def save_kino(msg, file_id, name):
    code = msg.text.strip()
    kino_baza[code] = {"name": name, "file_id": file_id}
    save_json(DB_FILE, kino_baza)

    bot.send_message(msg.chat.id, f"✅ Saqlandi!\n🎬 {name}\n🔑 Kod: {code}")

# ============================
# USER KOD YUBORADI
# ============================
@bot.message_handler(func=lambda msg: True)
def user_text(msg):

    # ---- ADMIN PANEL TUGMALARI ----
    if msg.text == "📊 Statistika":
        return send_stat(msg)
    if msg.text == "📢 Reklama yuborish":
        return ask_ad(msg)

    # ---- Kinoni qaytarish ----
    code = msg.text.strip()
    code_usage[code] += 1

    if code in kino_baza:
        d = kino_baza[code]
        bot.send_video(msg.chat.id, d["file_id"], caption=d["name"])
    else:
        bot.reply_to(msg, "❌ Bunday kod topilmadi!")

# ============================
# STATISTIKA (TUGMA + /stat)
# ============================
def send_stat(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⛔ Ruxsat yo‘q!")

    total_users = len(user_list)
    total_movies = len(kino_baza)

    clicks = load_json(CLICKS_FILE, {})
    kanal_counts = [0] * len(CHANNEL_LINKS)

    for user in clicks.values():
        for i, v in enumerate(user):
            if v == 1:
                kanal_counts[i] += 1

    popular = code_usage.most_common(5)
    popular_txt = "\n".join([f"{c[0]} — {c[1]} marta" for c in popular]) if popular else "Hali ishlatilmagan"

    text = "📊 <b>STATISTIKA</b>\n\n"
    text += f"👥 Foydalanuvchilar: {total_users}\n"
    text += f"🎬 Kinolar: {total_movies}\n\n"

    text += "📌 Tugmalar bosilishi:\n"
    for i, (name, _) in enumerate(CHANNEL_LINKS):
        text += f"{name}: {kanal_counts[i]}\n"

    text += f"\n⭐ Eng ko‘p ishlatilgan kodlar:\n{popular_txt}"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")

# ============================
# REKLAMA YUBORISH
# ============================
def ask_ad(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⛔ Ruxsat yo‘q!")

    bot.send_message(msg.chat.id, "📢 Reklama matnini yuboring:")
    bot.register_next_step_handler(msg, send_advert)

def send_advert(msg):
    text = msg.text
    users = user_list
    sent = 0

    for user in users:
        try:
            bot.send_message(user, f"📢 <b>Reklama</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except:
            pass

    bot.send_message(msg.chat.id, f"✔ Reklama yuborildi: {sent} ta foydalanuvchi.")

# ============================
# BOT ISHLAMOQDA
# ============================
print("BOT ISHLAMOQDA...")
bot.infinity_polling()
