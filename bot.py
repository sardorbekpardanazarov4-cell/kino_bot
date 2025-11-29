import telebot
from telebot import types
from pymongo import MongoClient
from collections import Counter

# --- BOT PARAMETRLARI ---
TOKEN = "8211203712:AAHdM1wShReC3Jq60qX_PR9XesR0xtsxSg0"
ADMIN_ID = 8383448395

bot = telebot.TeleBot(TOKEN)

# --- MONGODB SETUP ---
MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/kino?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client.kino
films = db.films  # Collection for movies

# --- KANAL LINKLARI ---
CHANNEL_LINKS = [
    "https://t.me/+njI2s4fSLbJlZTBi",
    "https://t.me/+JFubXpf3EY40M2U6",
    "https://t.me/+_PYMzySJjn9jM2U6",
    "https://t.me/+R5IUtNr74rcwY2Y6"
]
CHANNEL_KEYS = ["kanal1", "kanal2", "kanal3", "kanal4"]

# --- FOYDALANUVCHI MA'LUMOTLARI ---
user_clicks = {}
user_list = set()
code_usage = Counter()

# --- /START ---
@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    user_list.add(chat_id)
    user_clicks[chat_id] = {k: False for k in CHANNEL_KEYS}

    markup = types.InlineKeyboardMarkup()
    for i, link in enumerate(CHANNEL_LINKS):
        btn = types.InlineKeyboardButton(
            f"📺 {i+1}-kanalga zayavka yuborish",
            url=link
        )
        markup.add(btn)

    markup.add(types.InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check"))

    bot.send_message(
        chat_id,
        "👇 4 ta kanalga obuna bo‘ling, so‘ng 'Obuna bo‘ldim' tugmasini bosing:",
        reply_markup=markup
    )

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id

    if call.data == "check":
        clicks = user_clicks.get(chat_id, {})
        if clicks and all(clicks.values()):
            bot.send_message(chat_id, "✔️ Siz barcha kanallarga obuna boldingiz!\nEndi kino kodini kiriting:")
        else:
            bot.send_message(chat_id, "❗ KINI KODNI KIRITING!")
        bot.answer_callback_query(call.id)

# --- ADMIN: ADD KINO ---
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

def save_kino(msg, video_id, name):
    code = msg.text.strip()
    films.insert_one({"code": code, "name": name, "file_id": video_id})
    bot.send_message(msg.chat.id, f"✅ Kino saqlandi!\n🎬 {name}\n🔑 Kod: {code}")

# --- FOYDALANUVCHI KOD ORQALI KINO ---
@bot.message_handler(func=lambda m: True)
def send_kino(msg):
    code = msg.text.strip()
    code_usage[code] += 1
    d = films.find_one({"code": code})
    if d:
        bot.send_video(msg.chat.id, d["file_id"], caption=d["name"])
    else:
        bot.reply_to(msg, "❌ Bunday kod bo‘yicha kino topilmadi.")

# --- ADMIN STATISTIKA ---
@bot.message_handler(commands=['stat'])
def admin_stat(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "⚠️ Siz admin emassiz.")

    total_users = len(user_list)
    total_kino = films.count_documents({})

    most_used = code_usage.most_common(5)
    most_used_text = "\n".join([f"{c[0]} — {c[1]} marta" for c in most_used]) if most_used else "Hali kod ishlatilmagan"

    text = f"""
📊 <b>BOT STATISTIKASI</b>

👥 Foydalanuvchilar: {total_users}
🎬 Kinolar: {total_kino}

⭐ Eng ko‘p ishlatilgan kino kodlari:
{most_used_text}
"""
    bot.send_message(msg.chat.id, text, parse_mode="HTML")

print("BOT ISHLAMOQDA...")
bot.infinity_polling()
