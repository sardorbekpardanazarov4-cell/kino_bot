import telebot
from telebot import types
import json
import os
from collections import Counter

TOKEN = "8211203712:AAHdM1wShReC3Jq60qX_PR9XesR0xtsxSg0"         # Bot tokenini o'zgartiring
ADMIN_ID = 8383448395       # Admin ID

bot = telebot.TeleBot(TOKEN)

DB_FILE = "kino_baza.json"

# 4 ta kanal zayavka linklari
CHANNEL_LINKS = [
    "https://t.me/+njI2s4fSLbJlZTBi",
    "https://t.me/+JFubXpf3EY40M2U6",
    "https://t.me/+_PYMzySJjn9jM2U6",
    "https://t.me/+R5IUtNr74rcwY2Y6"
]

CHANNEL_KEYS = ["kanal1", "kanal2", "kanal3", "kanal4"]

# Foydalanuvchi tugma bosganini saqlash
user_clicks = {}
user_list = set()           # Botdan foydalanuvchilar
code_usage = Counter()      # Kod ishlatilish soni

# --- Kino bazasi ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(baza):
    with open(DB_FILE, "w") as f:
        json.dump(baza, f, indent=4)

kino_baza = load_db()


# --- /start ---
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    user_list.add(chat_id)

    user_clicks[chat_id] = {k: False for k in CHANNEL_KEYS}

    markup = types.InlineKeyboardMarkup()
    for i, link in enumerate(CHANNEL_LINKS):
        btn = types.InlineKeyboardButton(
            f"📺 {i+1}-kanalga zayavka yuborish",
            url=link,
            callback_data=CHANNEL_KEYS[i]
        )
        markup.add(btn)

    # 5-chi tugma: Obuna bo‘ldim
    markup.add(types.InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check"))

    bot.send_message(
        chat_id,
        "👇 4 ta kanalga obuna boling, so‘ng 'Obuna bo‘ldim' tugmasini bosing:",
        reply_markup=markup
    )


# --- Callback tugmalar ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id

    # 4 kanal tugmalari bosilgan bo‘lsa
    if call.data in CHANNEL_KEYS:
        user_clicks[chat_id][call.data] = True

        # Adminga zayavka xabari
        bot.send_message(
            ADMIN_ID,
            f"📌 User {chat_id} → {call.data} tugmasini bosdi!"
        )

        bot.answer_callback_query(call.id, "obuna boldim ✔️")
        return

    # Obuna bo‘ldim tugmasi
    if call.data == "check":
        clicks = user_clicks.get(chat_id, {})
        if all(clicks.values()):
            bot.send_message(chat_id, "✔️ Siz barcha kanallarga obuna boldingiz!\nEndi kino kodini kiriting:")
        else:
            bot.send_message(chat_id, "obuna boldingiz kod kiriting!")
        bot.answer_callback_query(call.id)


# --- ADMIN /add kino qo‘shish ---
@bot.message_handler(commands=['add'])
def admin_add(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⚠️ Siz admin emassiz.")

    bot.send_message(msg.chat.id, "🎥 Kino videosini yuboring:")
    bot.register_next_step_handler(msg, get_video)


def get_video(msg):
    if not msg.video:
        return bot.reply_to(msg, "❗ Faqat video yuboring!")
    video_id = msg.video.file_id
    bot.send_message(msg.chat.id, "🎬 Kinoning nomini kiriting:")
    bot.register_next_step_handler(msg, lambda m: get_name(m, video_id))


def get_name(msg, video_id):
    name = msg.text.strip()
    bot.send_message(msg.chat.id, "🔑 Kino kodini kiriting:")
    bot.register_next_step_handler(msg, lambda m: save_kino(m, video_id, name))


def save_kino(msg, file_id, name):
    code = msg.text.strip()
    kino_baza[code] = {"name": name, "file_id": file_id}
    save_db(kino_baza)
    bot.send_message(msg.chat.id, f"✅ Kino saqlandi!\n🎬 {name}\n🔑 Kod: {code}")


# --- Foydalanuvchi kod yuborsa kino chiqarish ---
@bot.message_handler(func=lambda m: True)
def send_kino(msg):
    code = msg.text.strip()
    code_usage[code] += 1

    if code in kino_baza:
        d = kino_baza[code]
        bot.send_video(msg.chat.id, d["file_id"], caption=d["name"])
    else:
        bot.reply_to(msg, "❌ Bunday kod bo‘yicha kino topilmadi.")


# --- ADMIN STATISTIKA ---
@bot.message_handler(commands=['stat'])
def admin_stat(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⚠️ Siz admin emassiz!")

    total_users = len(user_list)
    total_kino = len(kino_baza)

    kanal_stats = {k: 0 for k in CHANNEL_KEYS}
    for uc in user_clicks.values():
        for k in CHANNEL_KEYS:
            if uc.get(k):
                kanal_stats[k] += 1

    most_used = code_usage.most_common(5)
    most_used_text = "\n".join([f"{c[0]} — {c[1]} marta" for c in most_used]) if most_used else "Hali kod ishlatilmagan"

    text = f"""
📊 <b>BOT STATISTIKASI</b>

👥 Foydalanuvchilar: {total_users}
🎬 Kinolar: {total_kino}

📌 Kanal tugmalari bosilgan soni:
1️⃣ Kanal1: {kanal_stats['kanal1']}
2️⃣ Kanal2: {kanal_stats['kanal2']}
3️⃣ Kanal3: {kanal_stats['kanal3']}
4️⃣ Kanal4: {kanal_stats['kanal4']}

⭐ Eng ko‘p ishlatilgan kino kodlari:
{most_used_text}
"""
    bot.send_message(msg.chat.id, text, parse_mode="HTML")


print("BOT ISHLAMOQDA...")
bot.infinity_polling()