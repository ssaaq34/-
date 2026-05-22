import os
import subprocess
import threading
import time
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ContextTypes, filters
)
from keep_alive import keep_alive

# ===================== الإعدادات =====================
BOT_TOKEN = "8629731099:AAFEI1sBKbj2aLgTGJpghWnAfAC_x4YYOwg"
ADMIN_ID  = 7688107744  # ضع الـ Chat ID هنا

BOTS_DIR = "bots"
os.makedirs(BOTS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

# ===================== إدارة البوتات =====================
running_bots: dict[str, subprocess.Popen] = {}

def get_all_bots():
    return [f for f in os.listdir(BOTS_DIR) if f.endswith(".py")]

def start_bot(name):
    path = os.path.join(BOTS_DIR, name)
    if not os.path.exists(path):
        return False
    if name in running_bots and running_bots[name].poll() is None:
        return "already"
    proc = subprocess.Popen(
        ["python", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    running_bots[name] = proc
    return True

def stop_bot(name):
    if name in running_bots and running_bots[name].poll() is None:
        running_bots[name].terminate()
        running_bots[name].wait()
        return True
    return False

def bot_status(name):
    if name in running_bots and running_bots[name].poll() is None:
        return "🟢"
    return "🔴"

def get_bot_logs(name, lines=10):
    if name not in running_bots:
        return "لا توجد سجلات."
    proc = running_bots[name]
    try:
        out = ""
        for _ in range(lines):
            line = proc.stdout.readline()
            if not line:
                break
            out += line
        return out.strip() or "لا توجد سجلات حديثة."
    except:
        return "تعذر قراءة السجلات."

def auto_restart():
    """يراقب البوتات ويعيد تشغيل أي بوت توقف"""
    while True:
        for name, proc in list(running_bots.items()):
            if proc.poll() is not None:
                logging.info(f"إعادة تشغيل {name}...")
                start_bot(name)
        time.sleep(15)

# ===================== التحقق من الأدمن =====================
def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID

# ===================== الكيبوردات =====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 البوتات", callback_data="list_bots"),
            InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot"),
        ],
        [
            InlineKeyboardButton("▶️ تشغيل الكل", callback_data="start_all"),
            InlineKeyboardButton("⏹ إيقاف الكل", callback_data="stop_all"),
        ],
        [
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
        ]
    ])

def bots_list_keyboard():
    bots = get_all_bots()
    keyboard = []
    if not bots:
        keyboard.append([InlineKeyboardButton("لا يوجد بوتات بعد ➕", callback_data="add_bot")])
    for bot in bots:
        status = bot_status(bot)
        keyboard.append([
            InlineKeyboardButton(f"{status} {bot}", callback_data=f"bot_detail_{bot}"),
        ])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def bot_detail_keyboard(name):
    status = bot_status(name)
    is_running = status == "🟢"
    keyboard = [
        [
            InlineKeyboardButton("▶️ تشغيل" if not is_running else "▶️ تشغيل (يعمل)", callback_data=f"start_{name}"),
            InlineKeyboardButton("⏹ إيقاف", callback_data=f"stop_{name}"),
        ],
        [
            InlineKeyboardButton("🔄 إعادة تشغيل", callback_data=f"restart_{name}"),
            InlineKeyboardButton("📄 السجلات", callback_data=f"logs_{name}"),
        ],
        [
            InlineKeyboardButton("🗑 حذف البوت", callback_data=f"delete_{name}"),
        ],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="list_bots")]
    ]
    return InlineKeyboardMarkup(keyboard)

def settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ])

# ===================== الهاندلرز =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔️ غير مصرح لك باستخدام هذا البوت.")
        return
    await update.message.reply_text(
        "👋 *مرحباً بك في لوحة التحكم!*\n\nاختر ما تريد من الأزرار أدناه:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not is_admin(update):
        await query.edit_message_text("⛔️ غير مصرح.")
        return

    # ===== الرئيسية =====
    if data == "main_menu":
        await query.edit_message_text(
            "👋 *لوحة التحكم الرئيسية*\n\nاختر ما تريد:",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    # ===== قائمة البوتات =====
    elif data == "list_bots":
        bots = get_all_bots()
        count = len(bots)
        active = sum(1 for b in bots if bot_status(b) == "🟢")
        await query.edit_message_text(
            f"📋 *قائمة البوتات*\n\n🟢 يعمل: {active} | 🔴 متوقف: {count - active} | المجموع: {count}",
            parse_mode="Markdown",
            reply_markup=bots_list_keyboard()
        )

    # ===== إضافة بوت =====
    elif data == "add_bot":
        context.user_data["waiting_for_bot"] = True
        await query.edit_message_text(
            "📤 *إضافة بوت جديد*\n\nأرسل ملف `.py` الخاص بالبوت الآن:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
            ]])
        )

    # ===== تشغيل الكل =====
    elif data == "start_all":
        bots = get_all_bots()
        count = 0
        for bot in bots:
            result = start_bot(bot)
            if result is True:
                count += 1
        await query.edit_message_text(
            f"▶️ تم تشغيل {count} بوت بنجاح!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
            ]])
        )

    # ===== إيقاف الكل =====
    elif data == "stop_all":
        bots = get_all_bots()
        count = 0
        for bot in bots:
            if stop_bot(bot):
                count += 1
        await query.edit_message_text(
            f"⏹ تم إيقاف {count} بوت.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
            ]])
        )

    # ===== تفاصيل بوت =====
    elif data.startswith("bot_detail_"):
        name = data.replace("bot_detail_", "")
        status = bot_status(name)
        await query.edit_message_text(
            f"🤖 *{name}*\n\nالحالة: {status} {'يعمل' if status == '🟢' else 'متوقف'}",
            parse_mode="Markdown",
            reply_markup=bot_detail_keyboard(name)
        )

    # ===== تشغيل بوت =====
    elif data.startswith("start_"):
        name = data.replace("start_", "")
        result = start_bot(name)
        if result == "already":
            msg = f"⚠️ {name} يعمل بالفعل!"
        elif result:
            msg = f"✅ تم تشغيل {name} بنجاح!"
        else:
            msg = f"❌ فشل تشغيل {name}."
        await query.edit_message_text(
            msg,
            reply_markup=bot_detail_keyboard(name)
        )

    # ===== إيقاف بوت =====
    elif data.startswith("stop_"):
        name = data.replace("stop_", "")
        if stop_bot(name):
            msg = f"⏹ تم إيقاف {name}."
        else:
            msg = f"⚠️ {name} لم يكن يعمل."
        await query.edit_message_text(
            msg,
            reply_markup=bot_detail_keyboard(name)
        )

    # ===== إعادة تشغيل =====
    elif data.startswith("restart_"):
        name = data.replace("restart_", "")
        stop_bot(name)
        time.sleep(1)
        start_bot(name)
        await query.edit_message_text(
            f"🔄 تمت إعادة تشغيل {name}!",
            reply_markup=bot_detail_keyboard(name)
        )

    # ===== السجلات =====
    elif data.startswith("logs_"):
        name = data.replace("logs_", "")
        logs = get_bot_logs(name)
        await query.edit_message_text(
            f"📄 *آخر سجلات {name}:*\n\n```\n{logs}\n```",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data=f"bot_detail_{name}")
            ]])
        )

    # ===== حذف بوت =====
    elif data.startswith("delete_"):
        name = data.replace("delete_", "")
        stop_bot(name)
        path = os.path.join(BOTS_DIR, name)
        if os.path.exists(path):
            os.remove(path)
        if name in running_bots:
            del running_bots[name]
        await query.edit_message_text(
            f"🗑 تم حذف {name} بنجاح.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 للقائمة", callback_data="list_bots")
            ]])
        )

    # ===== الإعدادات =====
    elif data == "settings":
        await query.edit_message_text(
            "⚙️ *الإعدادات*",
            parse_mode="Markdown",
            reply_markup=settings_keyboard()
        )

    # ===== إحصائيات =====
    elif data == "stats":
        bots = get_all_bots()
        active = sum(1 for b in bots if bot_status(b) == "🟢")
        stopped = len(bots) - active
        await query.edit_message_text(
            f"📊 *إحصائيات النظام*\n\n"
            f"🟢 بوتات تعمل: {active}\n"
            f"🔴 بوتات متوقفة: {stopped}\n"
            f"📁 إجمالي البوتات: {len(bots)}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="settings")
            ]])
        )

# ===== استقبال ملفات البوتات =====
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    doc = update.message.document
    if not doc.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ فقط ملفات `.py` مقبولة.")
        return
    file = await doc.get_file()
    save_path = os.path.join(BOTS_DIR, doc.file_name)
    await file.download_to_drive(save_path)
    await update.message.reply_text(
        f"✅ تم رفع *{doc.file_name}* بنجاح!\n\nاذهب للقائمة لتشغيله:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 عرض البوتات", callback_data="list_bots")
        ]])
    )

# ===================== التشغيل =====================
if __name__ == "__main__":
    keep_alive()

    # تشغيل مراقب البوتات في الخلفية
    monitor = threading.Thread(target=auto_restart, daemon=True)
    monitor.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("✅ البوت المدير يعمل!")
    app.run_polling()
