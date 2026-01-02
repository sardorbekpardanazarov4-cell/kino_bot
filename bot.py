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

# ============================
# KANALLAR (4 TA)
# BOTNI SHULARGA ADMIN QILING
# ============================
CHANNELS = [
    ["Kanal 1", "@kinolar_prooo"],
    ["Kanal 2", "@kinolar_proooo"],
    ["Kanal 3", "@kinolar_prooooo"],
    ["Kanal 4", "@kinolar_proo"]
]

INSTAGRAM_LINK = "https://www.instagram.com/_pardanazarov1_/"

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

kino_baza = load_json(DB_FILE, {})
users = load_json(USERS_FILE, [])

# ============================
# OBUNANI REAL TEKSHIRISH
# ============================
def is_subscribed(user_id):
    for name, channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ============================
# START
# ============================
@bot.message_handler(commands=["start"])
def start(msg):
    chat_id = msg.chat.id

    if chat_id not in users:
        users.append(chat_id)
        save_json(USERS_FILE, users)

    kb = types.InlineKeyboardMarkup()

    for name, channel in CHANNELS:
        kb.add(
            types.InlineKeyboardButton(
                f"📢 {name}",
                url=f"https://t.me/{channel.replace('@','')}"
            )
        )

    kb.add(types.InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_LINK))
    kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))

    bot.send_message(
        chat_id,
        "👇 Quyidagi kanallarga obuna bo‘ling:",
        reply_markup=kb
    )

    if msg.from_user.id == ADMIN_ID:
        admin_panel(chat_id)

# ============================
# OBUNANI TEKSHIRISH
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
        bot.send_message(user_id, "🎬 Endi kino kodini yuboring!")
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Hamma Telegram kanalga obuna bo‘ling!",
            show_alert=True
        )

# ============================
# ADMIN PANEL
# ============================
def admin_panel(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Kino qo‘shish", "❌ Kino o‘chirish")
    kb.row("📊 Statistika")
    bot.send_message(chat_id, "🔧 Admin panel:", reply_markup=kb)

# ============================
# ADMIN BUYRUQLARI
# ============================
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_buttons(msg):

    if msg.text == "➕ Kino qo‘shish":
        bot.send_message(msg.chat.id, "🎥 Video yuboring:")
        return bot.register_next_step_handler(msg, add_video)

    if msg.text == "❌ Kino o‘chirish":
        bot.send_message(msg.chat.id, "🗑 Kino kodini yuboring:")
        return bot.register_next_step_handler(msg, delete_kino)

    if msg.text == "📊 Statistika":
        bot.send_message(
            msg.chat.id,
            f"👥 Foydalanuvchilar: {len(users)}\n🎬 Kinolar: {len(kino_baza)}"
        )

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
# USER KINO KOD YUBORADI
# ============================
@bot.message_handler(func=lambda m: True)
def user_code(msg):
    code = msg.text.strip()
    if code in kino_baza:
        d = kino_baza[code]
        bot.send_video(msg.chat.id, d["file_id"], caption=d["name"])
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kino topilmadi!")

# ============================
# BOT ISHLASHI
# ============================
print("✅ BOT ISHLAMOQDA...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
