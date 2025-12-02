import telebot
from telebot import types
from collections import Counter
import json, os

# ---------------------------
# Bot sozlamalari
# ---------------------------
TOKEN = "8211203712:AAHdM1wShReC3Jq60qX_PR9XesR0xtsxSg0"
ADMIN_ID = 8383448395

bot = telebot.TeleBot(TOKEN)

CHANNEL_LINKS = [
    "https://t.me/+njI2s4fSLbJlZTBi",      # 1-kanal
    "https://t.me/+JFubXpf3EY40M2U6",      # 2-kanal
    "https://t.me/+_PYMzySJjn9jM2U6",      # 3-kanal
    "https://t.me/+R5IUtNr74rcwY2Y6",      # 4-kanal
    "https://www.instagram.com/kinolar_pro7?igsh=MXgyNnIzOWZ2aHpjYw=="      # Instagram
]

CHANNEL_KEYS = ["kanal1", "kanal2", "kanal3", "kanal4", "instagram"]

user_clicks = {}
user_list = set()
code_usage = Counter()

DB_FILE = "kino_baza.json"

# ---------------------------
# Kino bazasini yuklash
# ---------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(baza):
    with open(DB_FILE, "w") as f:
        json.dump(baza, f, indent=4)

kino_baza = load_db()

# ---------------------------
# /start komandasi
# ---------------------------
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    user_list.add(chat_id)
    user_clicks[chat_id] = {k: False for k in CHANNEL_KEYS}

    markup = types.InlineKeyboardMarkup()
    for i, link in enumerate(CHANNEL_LINKS):
        if i < 4:
            btn_text = f"📌 {i+1}-kanalga obuna bo‘lish"
        else:
            btn_text = "📸 Instagramga obuna bo‘lish"
        btn = types.InlineKeyboardButton(
            btn_text,
            url=link,
            callback_data=CHANNEL_KEYS[i]
        )
        markup.add(btn)

    markup.add(types.InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check"))

    bot.send_message(
        chat_id,
        "👇 4 ta kanal va Instagram tugmalarini bosing, so‘ng 'Obuna bo‘ldim' tugmasini bosing:",
        reply_markup=markup
    )

# ---------------------------
# Callback tugmalar
# ---------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id

    if call.data in CHANNEL_KEYS:
        user_clicks[chat_id][call.data] = True
        bot.send_message(ADMIN_ID, f"User {chat_id} → {call.data} tugmasini bosdi!")
        bot.answer_callback_query(call.id, "✔️ Bosildi")
        return

    if call.data == "check":
        clicks = user_clicks.get(chat_id, {})
        if all(clicks.values()):
            bot.send_message(chat_id, "🎉 Siz barcha tugmalarni bosdingiz! Endi kino kodini yuboring:")
        else:
            bot.send_message(chat_id, "barcha kanalga obuna boldingiz  kino kodni kiriting:")
        bot.answer_callback_query(call.id)

# ---------------------------
# Admin kino qo‘shish
# ---------------------------
@bot.message_handler(commands=['add'])
def admin_add(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⚠️ Siz admin emassiz.")
    bot.send_message(msg.chat.id, "🎥 Kinoni yuboring:")
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

# ---------------------------
# Foydalanuvchi kod yuborsa kino chiqarish
# ---------------------------
@bot.message_handler(func=lambda m: True)
def send_kino(msg):
    code = msg.text.strip()
    code_usage[code] += 1
    if code in kino_baza:
        d = kino_baza[code]
        bot.send_video(msg.chat.id, d["file_id"], caption=d["name"])
    else:
        bot.reply_to(msg, "❌ Bunday kod bo‘yicha kino topilmadi.")

# ---------------------------
# Admin statistika
# ---------------------------
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

👥 Foydalanuvchilar soni: {total_users}
🎬 Kinolar soni: {total_kino}

📌 Kanal/Instagram tugmalari bosilgan soni:
1️⃣ Kanal1: {kanal_stats['kanal1']}
2️⃣ Kanal2: {kanal_stats['kanal2']}
3️⃣ Kanal3: {kanal_stats['kanal3']}
4️⃣ Kanal4: {kanal_stats['kanal4']}
5️⃣ Instagram: {kanal_stats['instagram']}

⭐ Eng ko‘p ishlatilgan kino kodlari:
{most_used_text}
"""
    bot.send_message(msg.chat.id, text, parse_mode="HTML")

# ---------------------------
# Bot ishga tushdi
# ---------------------------
print("BOT ISHLAMOQDA...")
bot.infinity_polling()
