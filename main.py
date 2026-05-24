"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          ⚡ NEXUS BOT MANAGER  — v5.0 FINAL ⚡           ║
║                                                          ║
║   نظام إدارة البوتات الذكي والاحترافي — نسخة نهائية    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

  المميزات:
  ✦ تحليل ذكي للكود وتثبيت المكتبات تلقائياً
  ✦ دعم كامل لجميع إصدارات python-telegram-bot
  ✦ كشف وتثبيت النسخة المناسبة بناءً على الكود
  ✦ مراقبة لحظية مع إشعارات فورية
  ✦ لوحة تحكم احترافية كاملة
  ✦ نظام أدمنز متعدد المستويات
  ✦ إحصائيات CPU/RAM لكل بوت
  ✦ محرر كود مباشر من التليجرام
"""

# ══════════════════════════════════════════════════════════
#                      الاستيرادات
# ══════════════════════════════════════════════════════════
import os, sys, subprocess, threading, time, logging, json
import ast, io, re, select, traceback, hashlib
from datetime import datetime, timedelta
from pathlib import Path

import psutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from keep_alive import keep_alive


# ══════════════════════════════════════════════════════════
#                    الإعدادات الأساسية
# ══════════════════════════════════════════════════════════
BOT_TOKEN  = "8629731099:AAGfWSoH7stYf56qcogz1tlZOm8Nhj_opJc"
ADMIN_ID   = 7688107744
DATA_FILE  = "nexus_data.json"
BOTS_DIR   = "bots"
LOGS_DIR   = "bot_logs"
VERSION    = "5.0 FINAL"

os.makedirs(BOTS_DIR,  exist_ok=True)
os.makedirs(LOGS_DIR,  exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("NEXUS")

# ══════════════════════════════════════════════════════════
#                     قاعدة البيانات
# ══════════════════════════════════════════════════════════
def load_db() -> dict:
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log.error(f"خطأ قراءة البيانات: {e}")
    return {
        "sub_admins": [],
        "bot_notes": {},
        "upload_count": 0,
        "total_restarts": 0,
        "created_at": datetime.now().isoformat(),
    }

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()

# ══════════════════════════════════════════════════════════
#                      الصلاحيات
# ══════════════════════════════════════════════════════════
def is_owner(uid: int) -> bool:
    return uid == ADMIN_ID

def is_admin(update: Update) -> bool:
    uid = update.effective_user.id
    return uid == ADMIN_ID or uid in db.get("sub_admins", [])

def admin_level(uid: int) -> str:
    if uid == ADMIN_ID:
        return "🎖️المطور"
    if uid in db.get("sub_admins", []):
        return "🔰 أدمن"
    return "❌ غير مصرح"


# ══════════════════════════════════════════════════════════
#           محرك التحليل الذكي للمكتبات
# ══════════════════════════════════════════════════════════

# مكتبات Python المدمجة — لا تحتاج تثبيت
STDLIB = {
    "os","sys","re","json","time","datetime","math","random","threading",
    "subprocess","logging","pathlib","shutil","copy","io","abc","ast",
    "base64","hashlib","hmac","uuid","enum","functools","itertools",
    "collections","typing","dataclasses","contextlib","traceback","inspect",
    "string","struct","socket","asyncio","concurrent","queue","signal",
    "platform","warnings","weakref","gc","pickle","csv","html","http",
    "urllib","email","builtins","operator","stat","tempfile","glob",
    "select","psutil","keep_alive","__future__","textwrap","pprint",
    "numbers","decimal","heapq","bisect","array","types","keyword",
    "token","tokenize","sqlite3","configparser","argparse","getpass",
    "getopt","optparse","cmd","code","codeop","dis","py_compile",
    "compileall","zipfile","tarfile","gzip","bz2","lzma","zlib",
    "struct","codecs","unicodedata","difflib","calendar","locale",
    "gettext","secrets","ssl","atexit","sched","_thread","multiprocessing",
}

# خريطة الحزم الشاملة — import name → pip package
PIP_MAP = {
    # Telegram
    "telegram":      None,  # يُحدَّد ديناميكياً حسب الكود
    # HTTP & Web
    "requests":      "requests",
    "aiohttp":       "aiohttp",
    "httpx":         "httpx",
    "flask":         "Flask",
    "fastapi":       "fastapi",
    "uvicorn":       "uvicorn",
    "starlette":     "starlette",
    "sanic":         "sanic",
    "tornado":       "tornado",
    "quart":         "quart",
    # Databases
    "pymongo":       "pymongo",
    "motor":         "motor",
    "redis":         "redis",
    "sqlalchemy":    "SQLAlchemy",
    "aiosqlite":     "aiosqlite",
    "aiomysql":      "aiomysql",
    "asyncpg":       "asyncpg",
    "peewee":        "peewee",
    "tortoise":      "tortoise-orm",
    "databases":     "databases",
    # Data & Science
    "numpy":         "numpy",
    "pandas":        "pandas",
    "scipy":         "scipy",
    "matplotlib":    "matplotlib",
    "seaborn":       "seaborn",
    "sklearn":       "scikit-learn",
    "tensorflow":    "tensorflow",
    "torch":         "torch",
    "transformers":  "transformers",
    "cv2":           "opencv-python",
    "PIL":           "Pillow",
    "imageio":       "imageio",
    "skimage":       "scikit-image",
    # Config & Utils
    "dotenv":        "python-dotenv",
    "yaml":          "PyYAML",
    "toml":          "tomli",
    "pydantic":      "pydantic",
    "attrs":         "attrs",
    "click":         "click",
    "rich":          "rich",
    "tqdm":          "tqdm",
    "colorama":      "colorama",
    "tabulate":      "tabulate",
    "prettytable":   "prettytable",
    # Scheduling & Async
    "apscheduler":   "APScheduler",
    "celery":        "celery",
    "dramatiq":      "dramatiq",
    # Security & Crypto
    "cryptography":  "cryptography",
    "nacl":          "PyNaCl",
    "jwt":           "PyJWT",
    "bcrypt":        "bcrypt",
    "paramiko":      "paramiko",
    # Parsing & Scraping
    "bs4":           "beautifulsoup4",
    "lxml":          "lxml",
    "scrapy":        "scrapy",
    "selenium":      "selenium",
    "playwright":    "playwright",
    "pyppeteer":     "pyppeteer",
    # Time & Locale
    "pytz":          "pytz",
    "dateutil":      "python-dateutil",
    "arrow":         "arrow",
    "pendulum":      "pendulum",
    # Files & Documents
    "openpyxl":      "openpyxl",
    "xlrd":          "xlrd",
    "xlwt":          "xlwt",
    "docx":          "python-docx",
    "pdfplumber":    "pdfplumber",
    "pypdf2":        "PyPDF2",
    "reportlab":     "reportlab",
    # Media
    "qrcode":        "qrcode[pil]",
    "barcode":       "python-barcode",
    "pydub":         "pydub",
    "mutagen":       "mutagen",
    "pytube":        "pytube",
    "yt_dlp":        "yt-dlp",
    # Misc
    "googletrans":   "googletrans==4.0.0-rc1",
    "deep_translator":"deep-translator",
    "langdetect":    "langdetect",
    "num2words":     "num2words",
    "arabic_reshaper":"arabic-reshaper",
    "bidi":          "python-bidi",
    "telegramcalendar":"python-telegram-bot-calendar",
    "aiogram":       "aiogram",
    "pyrogram":      "pyrogram",
    "telethon":      "telethon",
    "tgcrypto":      "tgcrypto",
}

# ميزات تستلزم python-telegram-bot v21+
PTB_V21_FEATURES = {
    "ReactionTypeEmoji", "ReactionTypePaid", "MessageReactionUpdated",
    "ChatBoost", "ChatBoostUpdated", "ChatBoostRemoved",
    "InaccessibleMessage", "MaybeInaccessibleMessage",
    "Story", "UsersShared", "ChatShared", "KeyboardButtonRequestUsers",
    "KeyboardButtonRequestChat", "GiveawayCreated", "Giveaway",
    "GiveawayWinners", "GiveawayCompleted",
    "ExternalReplyInfo", "TextQuote", "ReplyParameters",
    "ForwardOrigin", "MessageOrigin",
    "LinkPreviewOptions", "BusinessConnection",
}

# ميزات تستلزم v20+
PTB_V20_FEATURES = {
    "ApplicationBuilder", "Application",
}

def detect_ptb_version(code: str) -> str:
    """
    يحلل كود البوت الفرعي ويحدد النسخة المطلوبة من python-telegram-bot.
    يرجع: "python-telegram-bot>=21.0" أو "python-telegram-bot>=20.0" أو "python-telegram-bot"
    """
    # تحقق من ميزات v21
    for feature in PTB_V21_FEATURES:
        if feature in code:
            log.info(f"✦ كشف ميزة v21+: {feature}")
            return "python-telegram-bot>=21.0"

    # تحقق من v20
    for feature in PTB_V20_FEATURES:
        if feature in code:
            return "python-telegram-bot>=20.0"

    # تحقق من رقم الإصدار المذكور صراحةً في الكود
    ver_match = re.search(r"telegram[^\n]*?(\d+\.\d+)", code)
    if ver_match:
        ver = float(ver_match.group(1))
        if ver >= 21:
            return "python-telegram-bot>=21.0"
        if ver >= 20:
            return "python-telegram-bot>=20.0"

    return "python-telegram-bot>=20.0"  # الافتراضي: v20 على الأقل

def extract_imports(code: str) -> set:
    """يستخرج أسماء المكتبات من الكود بطريقة دقيقة عبر AST"""
    pkgs = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    pkgs.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkgs.add(node.module.split(".")[0])
    except SyntaxError:
        # fallback للكودات التي فيها أخطاء جزئية
        for line in code.splitlines():
            s = line.strip()
            if s.startswith(("import ", "from ")):
                parts = s.split()
                if len(parts) >= 2:
                    pkgs.add(parts[1].split(".")[0])
    return pkgs

def build_install_list(code: str) -> list:
    """
    يبني قائمة الحزم اللازمة للتثبيت بذكاء:
    - يتجاهل المكتبات المدمجة
    - يحدد النسخة الصحيحة من telegram
    - يزيل التكرار
    """
    pkgs     = extract_imports(code)
    to_install = []
    has_telegram = False

    for p in pkgs:
        if not p or p in STDLIB or p.startswith("_"):
            continue
        if p == "telegram":
            has_telegram = True
            continue
        pip_name = PIP_MAP.get(p)
        if pip_name is None:
            pip_name = p  # استخدم الاسم مباشرة
        to_install.append(pip_name)

    # أضف telegram بالنسخة الصحيحة
    if has_telegram:
        ptb_pkg = detect_ptb_version(code)
        to_install.insert(0, ptb_pkg)

    return list(dict.fromkeys(to_install))  # إزالة التكرار مع الحفاظ على الترتيب

def install_packages(path: str) -> tuple:
    """
    يثبت مكتبات البوت بأذكى طريقة ممكنة.
    يجرب عدة طرق حتى تنجح إحداها.
    يرجع: (نجح, قائمة_المثبتة, رسالة_الخطأ)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        return False, [], f"خطأ قراءة الملف: {e}"

    to_install = build_install_list(code)

    if not to_install:
        log.info("  ✓ لا توجد مكتبات خارجية")
        return True, [], ""

    log.info(f"  📦 مكتبات مطلوبة: {to_install}")

    # طرق التثبيت المتاحة — مرتبة من الأفضل للاحتياطي
    base_cmd = [sys.executable, "-m", "pip", "install", "--quiet",
                "--no-warn-script-location"]
    methods = [
        base_cmd + to_install,
        base_cmd + ["--upgrade"] + to_install,
        base_cmd + ["--user"] + to_install,
        base_cmd + ["--break-system-packages"] + to_install,
        ["pip3", "install", "--quiet"] + to_install,
        ["pip",  "install", "--quiet"] + to_install,
    ]

    last_err = "فشلت جميع طرق التثبيت"
    for cmd in methods:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                log.info(f"  ✅ تثبيت ناجح")
                return True, to_install, ""
            last_err = (result.stderr or result.stdout or "")[:500].strip()
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return False, to_install, "⏰ انتهت مهلة التثبيت (5 دقائق)"
        except Exception as e:
            last_err = str(e)

    log.warning(f"  ⚠️ فشل التثبيت: {last_err[:200]}")
    return False, to_install, last_err

def check_syntax(code: str) -> tuple:
    """يتحقق من صحة صيغة Python"""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"السطر {e.lineno}: {e.msg}"


# ══════════════════════════════════════════════════════════
#              محرك تشغيل البوتات الفرعية
# ══════════════════════════════════════════════════════════
running_bots:     dict[str, subprocess.Popen] = {}
bot_start_times:  dict[str, float]            = {}
bot_crash_counts: dict[str, int]              = {}
bot_last_error:   dict[str, str]              = {}
bot_install_info: dict[str, list]             = {}
_bot_lock = threading.Lock()
_app = None  # مرجع للتطبيق الرئيسي


def get_all_bots() -> list:
    try:
        return sorted(f for f in os.listdir(BOTS_DIR) if f.endswith(".py"))
    except:
        return []

def _is_alive(name: str) -> bool:
    p = running_bots.get(name)
    return p is not None and p.poll() is None

def bot_status(name: str) -> str:
    return "🟢" if _is_alive(name) else "🔴"

def get_uptime(name: str) -> str:
    if not _is_alive(name) or name not in bot_start_times:
        return "—"
    s = int(time.time() - bot_start_times[name])
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:   return f"{h}س {m}د"
    if m:   return f"{m}د {sec}ث"
    return f"{sec}ث"

def get_resources(name: str) -> dict:
    empty = {"cpu": 0.0, "ram_mb": 0.0, "ram_pct": 0.0, "threads": 0}
    if not _is_alive(name): return empty
    try:
        p  = psutil.Process(running_bots[name].pid)
        mi = p.memory_info()
        return {
            "cpu":     p.cpu_percent(interval=0.3),
            "ram_mb":  mi.rss / 1024 / 1024,
            "ram_pct": p.memory_percent(),
            "threads": p.num_threads(),
        }
    except:
        return empty

def sys_stats() -> dict:
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    dsk = psutil.disk_usage(".")
    boot= datetime.fromtimestamp(psutil.boot_time())
    up  = datetime.now() - boot
    return {
        "cpu":        cpu,
        "ram_pct":    ram.percent,
        "ram_used":   ram.used   / 1024**2,
        "ram_total":  ram.total  / 1024**2,
        "disk_pct":   dsk.percent,
        "disk_used":  dsk.used   / 1024**3,
        "disk_total": dsk.total  / 1024**3,
        "uptime":     str(up).split(".")[0],
    }

def _save_bot_log(name: str, content: str):
    """يحفظ آخر سجل للبوت في ملف"""
    try:
        log_path = os.path.join(LOGS_DIR, f"{name}.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}]\n{content}")
    except:
        pass

def read_logs(name: str, chars: int = 3500) -> str:
    """يقرأ سجلات البوت — يحاول القراءة المباشرة أولاً ثم الملف"""
    p = running_bots.get(name)
    output = ""

    if p and p.poll() is None:
        try:
            r, _, _ = select.select([p.stdout], [], [], 0.8)
            if r:
                raw = os.read(p.stdout.fileno(), 16384)
                output = raw.decode("utf-8", errors="replace")
        except:
            pass

    if not output:
        # قراءة من ملف السجل
        log_path = os.path.join(LOGS_DIR, f"{name}.log")
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    output = f.read()
            except:
                pass

    if not output:
        output = bot_last_error.get(name, "")

    output = output.strip()
    if len(output) > chars:
        output = "...\n" + output[-chars:]
    return output or "✅ البوت يعمل بهدوء"

def start_bot(name: str) -> tuple:
    """
    يشغّل البوت الفرعي بشكل كامل ومضمون:
    1. فحص الملف
    2. تثبيت المكتبات
    3. تشغيل في subprocess منفصل
    4. مراقبة للتأكد من الاستقرار
    يرجع: (نجح, رسالة_تفصيلية)
    """
    path = os.path.join(BOTS_DIR, name)
    if not os.path.exists(path):
        return False, "الملف غير موجود في مجلد البوتات"

    with _bot_lock:
        if _is_alive(name):
            return True, "already"

        # قراءة الكود
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            return False, f"تعذر قراءة الملف: {e}"

        # تثبيت المكتبات
        ok_i, installed, install_err = install_packages(path)
        bot_install_info[name] = installed

        if not ok_i:
            log.warning(f"⚠️ {name}: تثبيت جزئي — {install_err[:100]}")

        # تشغيل في subprocess منفصل تماماً
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            proc = subprocess.Popen(
                [sys.executable, "-u", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,   # bytes لأن select يحتاجها
                bufsize=0,
                env=env,
            )
            running_bots[name]    = proc
            bot_start_times[name] = time.time()
            bot_crash_counts.setdefault(name, 0)
            bot_last_error.pop(name, None)

            log.info(f"  🚀 {name} — PID={proc.pid}")

            # انتظر 4 ثوانٍ وتحقق من الاستقرار
            time.sleep(4)
            if proc.poll() is not None:
                # البوت مات — اقرأ سبب الخطأ بالكامل
                try:
                    raw = proc.stdout.read()
                    err_text = raw.decode("utf-8", errors="replace").strip()
                except:
                    err_text = "تعذر قراءة الخطأ"

                # لو مات بسبب مكتبة ناقصة — حاول مجدداً
                if "ModuleNotFoundError" in err_text or "ImportError" in err_text:
                    missing = re.findall(r"No module named '([^']+)'", err_text)
                    if missing:
                        log.info(f"  🔧 مكتبات ناقصة مكتشفة: {missing} — محاولة تثبيت...")
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
                            timeout=120
                        )
                        # أعد التشغيل مرة ثانية
                        proc2 = subprocess.Popen(
                            [sys.executable, "-u", path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=False, bufsize=0, env=env,
                        )
                        running_bots[name]    = proc2
                        bot_start_times[name] = time.time()
                        time.sleep(4)
                        if proc2.poll() is None:
                            log.info(f"  ✅ {name} يعمل بعد التثبيت التلقائي")
                            return True, ""
                        try:
                            raw2 = proc2.stdout.read()
                            err_text = raw2.decode("utf-8", errors="replace").strip()
                        except:
                            pass

                _save_bot_log(name, err_text)
                bot_last_error[name] = err_text
                log.error(f"  ❌ {name} مات:\n{err_text[:300]}")
                return False, err_text

            log.info(f"  ✅ {name} مستقر ويعمل")
            return True, ""

        except Exception as e:
            err = traceback.format_exc()
            bot_last_error[name] = err
            log.error(f"  ❌ خطأ تشغيل {name}: {e}")
            return False, err

def stop_bot(name: str) -> bool:
    p = running_bots.get(name)
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
        log.info(f"  ⏹ {name} أُوقف")
        return True
    return False

def restart_bot(name: str) -> tuple:
    stop_bot(name)
    time.sleep(1.5)
    return start_bot(name)


# ══════════════════════════════════════════════════════════
#              المراقب الذكي التلقائي
# ══════════════════════════════════════════════════════════
def _notify(text: str):
    """يرسل إشعاراً لجميع الأدمنز"""
    global _app
    if not _app: return
    import asyncio
    targets = [ADMIN_ID] + db.get("sub_admins", [])
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_running(): return
        for t in targets:
            try:
                asyncio.run_coroutine_threadsafe(
                    _app.bot.send_message(
                        chat_id=t, text=text,
                        parse_mode="Markdown"
                    ), loop
                )
            except:
                pass
    except:
        pass

def _monitor_worker():
    """
    خيط المراقبة الدائم:
    • ينتظر اكتمال تشغيل البوت الرئيسي
    • يشغّل جميع البوتات الموجودة عند البداية
    • يراقب كل 12 ثانية ويعيد الميت فوراً
    """
    log.info("🔍 المراقب التلقائي بدأ")
    time.sleep(8)  # انتظر البوت الرئيسي

    # تشغيل أولي لجميع البوتات الموجودة
    all_bots = get_all_bots()
    if all_bots:
        log.info(f"🚀 تشغيل أولي لـ {len(all_bots)} بوت...")
        for name in all_bots:
            log.info(f"  ⟶ {name}")
            start_bot(name)
            time.sleep(3)  # تأخير بين كل بوت
        log.info("✅ الإقلاع الأولي اكتمل")

    # حلقة المراقبة الأبدية
    while True:
        time.sleep(12)
        for name in get_all_bots():
            if not _is_alive(name):
                bot_crash_counts[name] = bot_crash_counts.get(name, 0) + 1
                n = bot_crash_counts[name]
                db["total_restarts"] = db.get("total_restarts", 0) + 1
                save_db()
                log.warning(f"⚠️ {name} توقف (انقطاع #{n})")

                ok, err = start_bot(name)
                ts = datetime.now().strftime("%-I:%M %p")

                if ok:
                    _notify(
                        f"🔔 *تنبيه المراقب الذكي*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"⚠️ البوت `{name}` توقف\n"
                        f"✅ تمت إعادة التشغيل بنجاح\n\n"
                        f"🔁 إجمالي الانقطاعات: `{n}`\n"
                        f"🕐 الوقت: `{ts}`"
                    )
                else:
                    _notify(
                        f"🚨 *خطأ حرج — فشل الإنعاش*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"❌ `{name}` فشل في إعادة التشغيل\n\n"
                        f"```\n{err[:350]}\n```"
                    )


# ══════════════════════════════════════════════════════════
#            الواجهة — النصوص الاحترافية
# ══════════════════════════════════════════════════════════

def _stars(pct: float, total: int = 10) -> str:
    """يرسم شريط تقدم من رموز"""
    filled = round(pct / 100 * total)
    return "█" * filled + "░" * (total - filled)

def fmt_size(mb: float) -> str:
    if mb >= 1024: return f"{mb/1024:.1f} GB"
    return f"{mb:.0f} MB"


# ══════════════════════════════════════════════════════════
#                      الكيبوردات
# ══════════════════════════════════════════════════════════
def kb_main(uid: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("📋 البوتات",      callback_data="list"),
            InlineKeyboardButton("➕ رفع بوت",      callback_data="upload"),
        ],
        [
            InlineKeyboardButton("▶️ تشغيل الكل",  callback_data="start_all"),
            InlineKeyboardButton("⏹ إيقاف الكل",  callback_data="stop_all"),
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات",  callback_data="stats"),
            InlineKeyboardButton("⚙️ الإعدادات",   callback_data="settings"),
        ],
    ]
    if is_owner(uid):
        rows.append([
            InlineKeyboardButton("👥 إدارة الأدمنة",  callback_data="admins"),
            InlineKeyboardButton("ℹ️ عن النظام",       callback_data="about"),
        ])
    return InlineKeyboardMarkup(rows)

def kb_list() -> InlineKeyboardMarkup:
    bots = get_all_bots()
    rows = []
    if not bots:
        rows.append([InlineKeyboardButton(
            "📭 لا يوجد بوتات — اضغط هنا لرفع أول بوت",
            callback_data="upload"
        )])
    else:
        for b in bots:
            st = bot_status(b)
            up = get_uptime(b)
            label = f"{st}  {b}"
            if up != "—": label += f"  ·  ⏱{up}"
            rows.append([InlineKeyboardButton(label, callback_data=f"d|{b}")])
    rows.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")])
    return InlineKeyboardMarkup(rows)

def kb_detail(name: str, uid: int) -> InlineKeyboardMarkup:
    run = _is_alive(name)
    rows = [
        [
            InlineKeyboardButton(
                "🟢 يعمل" if run else "▶️ تشغيل",
                callback_data=f"run|{name}"
            ),
            InlineKeyboardButton("⏹ إيقاف",         callback_data=f"stp|{name}"),
        ],
        [
            InlineKeyboardButton("🔄 إعادة تشغيل",   callback_data=f"rst|{name}"),
            InlineKeyboardButton("📄 السجلات",        callback_data=f"log|{name}"),
        ],
        [
            InlineKeyboardButton("📊 الموارد",        callback_data=f"res|{name}"),
            InlineKeyboardButton("📝 تعديل الكود",    callback_data=f"edi|{name}"),
        ],
    ]
    if is_owner(uid):
        rows.append([
            InlineKeyboardButton("🗑 حذف نهائي",   callback_data=f"del|{name}"),
            InlineKeyboardButton("📋 معلومات",      callback_data=f"inf|{name}"),
        ])
    else:
        rows.append([InlineKeyboardButton("📋 معلومات", callback_data=f"inf|{name}")])
    rows.append([InlineKeyboardButton("🔙 قائمة البوتات", callback_data="list")])
    return InlineKeyboardMarkup(rows)

def kb_admins() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"❌ إزالة  {a}", callback_data=f"rm|{a}")]
        for a in db.get("sub_admins", [])
    ]
    rows.append([InlineKeyboardButton("➕ إضافة أدمن جديد", callback_data="add_adm")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="settings")])
    return InlineKeyboardMarkup(rows)

def kb_back(cb: str, label: str = "🔙 رجوع") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=cb)]])

def kb_refresh_back(refresh_cb: str, back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 تحديث", callback_data=refresh_cb),
        InlineKeyboardButton("🔙 رجوع",  callback_data=back_cb),
    ]])


# ══════════════════════════════════════════════════════════
#                   نص الصفحات
# ══════════════════════════════════════════════════════════
def _home_text(uid: int) -> str:
    bots = get_all_bots()
    act  = sum(1 for b in bots if _is_alive(b))
    stp  = len(bots) - act
    s    = sys_stats()
    role = admin_level(uid)
    now  = datetime.now().strftime("%I:%M %p  |  %a %d %b")
    return (
        f"*☇ 𝐍𝐄𝐗𝐔𝐒 𝐁𝐎𝐓 𝐑𝐈𝐕𝐄𝐍 ♛* |【 `v{VERSION}` 】\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐〖 {now} 〗\n\n"
        f"رتبتك :【 {role} 】\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *الــبــوتـــات :*\n"
        f" 🟢 يعمل: `{act}`   🔴 متوقف: `{stp}`   📂 الكل: `{len(bots)}`\n\n"
        f"🖥 *السيرفر*\n"
        f"   CPU `{s['cpu']:.0f}%` {_stars(s['cpu'],8)}\n"
        f"   RAM `{s['ram_pct']:.0f}%` {_stars(s['ram_pct'],8)}\n"
        f"   Disk `{s['disk_pct']:.0f}%` {_stars(s['disk_pct'],8)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"اختر من القائمة قائدي:"
    )

def _detail_text(name: str) -> str:
    st  = bot_status(name)
    up  = get_uptime(name)
    cr  = bot_crash_counts.get(name, 0)
    pid = running_bots[name].pid if _is_alive(name) else "—"
    pkgs = bot_install_info.get(name, [])
    pkg_str = ", ".join(pkgs[:5]) if pkgs else "لا شيء"
    return (
        f"🤖 *{name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الحالة : {st} {'يعمل بحب ✅' if st=='🟢' else 'متوقف للأسف ❌'}\n"
        f"⏱ وقت التشغيل : `{up}`\n"
        f"🔢 PID : `{pid}`\n"
        f"🔁 انقطاعات : `{cr}`\n"
        f"📦 مكتبات : `{pkg_str}`"
    )


# ══════════════════════════════════════════════════════════
#                   /start
# ══════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text(
            "⛔️ *غير مصرح لك يروحي*\n\n هذا النظام خاص..",
            parse_mode="Markdown"
        )
        return
    uid = update.effective_user.id
    await update.message.reply_text(
        _home_text(uid),
        parse_mode="Markdown",
        reply_markup=kb_main(uid)
    )


# ══════════════════════════════════════════════════════════
#                   معالج الأزرار
# ══════════════════════════════════════════════════════════
async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    data = q.data
    uid  = update.effective_user.id
    chat = update.effective_chat.id

    if not is_admin(update):
        await q.edit_message_text("⛔️ غير مصرح.")
        return

    # ─────────────── الرئيسية ───────────────
    if data == "home":
        await q.edit_message_text(
            _home_text(uid),
            parse_mode="Markdown",
            reply_markup=kb_main(uid)
        )

    # ─────────────── قائمة البوتات ───────────────
    elif data == "list":
        bots = get_all_bots()
        act  = sum(1 for b in bots if _is_alive(b))
        await q.edit_message_text(
            f"📋 *قائمة البوتات الفرعية :*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 شغّال: `{act}`   ·   🔴 متوقف: `{len(bots)-act}`   ·   📁 الكل: `{len(bots)}`\n\n"
            f"اختر بوتاً لإدارتة :-",
            parse_mode="Markdown",
            reply_markup=kb_list()
        )

    # ─────────────── رفع بوت ───────────────
    elif data == "upload":
        ctx.user_data["act"] = "upload"
        await q.edit_message_text(
            "📤 *رفع بوت جديد :*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "أرسل ملف `.py` الخاص بالبوت الآن.\n\n"
            "🧠 *ماذا سيحدث تلقائياً:*\n"
            "  ✦ فحص صحة كود البوت\n"
            "  ✦ تحليل المكتبات المطلوبة\n"
            "  ✦ كشف إصدار python-telegram-bot\n"
            "  ✦ تثبيت كل شيء بذكاء\n"
            "  ✦ تشغيل البوت فوراً\n"
            "  ✦ ربطه بنظام المراقبة الفورية",
            parse_mode="Markdown",
            reply_markup=kb_back("home")
        )

    # ─────────────── تشغيل الكل ───────────────
    elif data == "start_all":
        await q.edit_message_text(
            "⏳ *جارٍ تشغيل جميع البوتات...*",
            parse_mode="Markdown"
        )
        ok_count = 0
        fail_list = []
        for b in get_all_bots():
            if not _is_alive(b):
                r, err = start_bot(b)
                if r:
                    ok_count += 1
                else:
                    fail_list.append(b)
                time.sleep(1.5)

        fail_txt = ""
        if fail_list:
            fail_txt = f"\n\n❌ فشل تشغيل:\n" + "\n".join(f"  • `{f}`" for f in fail_list)

        await q.edit_message_text(
            f"▶️ *نتيجة التشغيل الشامل*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ تم تشغيل: `{ok_count}` بوت بنجاح"
            f"{fail_txt}",
            parse_mode="Markdown",
            reply_markup=kb_back("home")
        )

    # ─────────────── إيقاف الكل ───────────────
    elif data == "stop_all":
        n = sum(1 for b in get_all_bots() if stop_bot(b))
        await q.edit_message_text(
            f"⏹ *تم إيقاف جميع البوتات*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"عدد البوتات التي أُوقفت: `{n}`",
            parse_mode="Markdown",
            reply_markup=kb_back("home")
        )

    # ─────────────── تفاصيل بوت ───────────────
    elif data.startswith("d|"):
        name = data[2:]
        await q.edit_message_text(
            _detail_text(name),
            parse_mode="Markdown",
            reply_markup=kb_detail(name, uid)
        )

    # ─────────────── تشغيل بوت ───────────────
    elif data.startswith("run|"):
        name = data[4:]
        if _is_alive(name):
            await q.answer("✅ البوت يعمل بالفعل!", show_alert=True)
            await q.edit_message_text(_detail_text(name), parse_mode="Markdown", reply_markup=kb_detail(name, uid))
            return
        await q.edit_message_text(
            f"⏳ *جارٍ تشغيل {name}...*\n\nيتم تثبيت المكتبات وإقلاع البوت",
            parse_mode="Markdown"
        )
        ok, err = start_bot(name)
        if ok:
            await q.edit_message_text(
                f"✅ *تم التشغيل بنجاح!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 `{name}` يعمل الآن 🟢",
                parse_mode="Markdown",
                reply_markup=kb_detail(name, uid)
            )
        else:
            short_err = err.strip()[-600:] if err else "خطأ غير معروف"
            await q.edit_message_text(
                f"❌ *فشل تشغيل {name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"```\n{short_err}\n```\n\n"
                f"💡 تحقق من الكود أو الـ Token",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📄 السجلات",  callback_data=f"log|{name}"),
                     InlineKeyboardButton("📝 تعديل",    callback_data=f"edi|{name}")],
                    [InlineKeyboardButton("🔙 رجوع",     callback_data=f"d|{name}")],
                ])
            )

    # ─────────────── إيقاف بوت ───────────────
    elif data.startswith("stp|"):
        name = data[4:]
        done = stop_bot(name)
        await q.edit_message_text(
            f"{'⏹ *تم الإيقاف بنجاح*' if done else '⚠️ *البوت متوقف مسبقاً*'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 `{name}` 🔴",
            parse_mode="Markdown",
            reply_markup=kb_detail(name, uid)
        )

    # ─────────────── إعادة تشغيل ───────────────
    elif data.startswith("rst|"):
        name = data[4:]
        await q.edit_message_text(
            f"🔄 *جارٍ إعادة تشغيل {name}...*",
            parse_mode="Markdown"
        )
        ok, err = restart_bot(name)
        if ok:
            await q.edit_message_text(
                f"✅ *تمت إعادة التشغيل بنجاح!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 `{name}` يعمل الآن بحب 🟢",
                parse_mode="Markdown",
                reply_markup=kb_detail(name, uid)
            )
        else:
            await q.edit_message_text(
                f"❌ *فشل إعادة التشغيل*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"```\n{err.strip()[-400:]}\n```",
                parse_mode="Markdown",
                reply_markup=kb_detail(name, uid)
            )

    # ─────────────── السجلات ───────────────
    elif data.startswith("log|"):
        name = data[4:]
        logs = read_logs(name)
        await q.edit_message_text(
            f"📄 *سجلات {name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{logs}\n```",
            parse_mode="Markdown",
            reply_markup=kb_refresh_back(f"log|{name}", f"d|{name}")
        )

    # ─────────────── الموارد ───────────────
    elif data.startswith("res|"):
        name = data[4:]
        r = get_resources(name)
        s = sys_stats()
        await q.edit_message_text(
            f"📊 *موارد {name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*البوت:*\n"
            f"  🔵 CPU   `{r['cpu']:.1f}%` {_stars(r['cpu'])}\n"
            f"  🟣 RAM   `{r['ram_mb']:.1f} MB` ({r['ram_pct']:.1f}%)\n"
            f"  🧵 Threads `{r['threads']}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"*السيرفر الكلي:*\n"
            f"  🖥 CPU   `{s['cpu']:.1f}%` {_stars(s['cpu'])}\n"
            f"  💾 RAM   `{fmt_size(s['ram_used'])}/{fmt_size(s['ram_total'])}` ({s['ram_pct']:.1f}%)\n"
            f"  💿 Disk  `{s['disk_used']:.1f}/{s['disk_total']:.1f} GB` ({s['disk_pct']:.1f}%)\n"
            f"  ⏳ Uptime `{s['uptime']}`",
            parse_mode="Markdown",
            reply_markup=kb_refresh_back(f"res|{name}", f"d|{name}")
        )

    # ─────────────── تعديل الكود ───────────────
    elif data.startswith("edi|"):
        name = data[4:]
        ctx.user_data["act"] = f"edit|{name}"
        path = os.path.join(BOTS_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            lines = len(code.splitlines())
            size  = len(code.encode()) / 1024
            await q.edit_message_text(
                f"📝 *تعديل كود {name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📏 الأسطر : 〖 `{lines}` 〗\n"
                f"📦 الحجم : 〖 `{size:.1f} KB` 〗\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"أرسل الكود الجديد كـ :\n"
                f"  • رسالة نصية مباشرة\n"
                f"  • ملف `.py` جديد\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ سيتم إيقاف البوت وإعادة تشغيله",
                parse_mode="Markdown",
                reply_markup=kb_back(f"d|{name}")
            )
            await ctx.bot.send_document(
                chat_id=chat,
                document=io.BytesIO(code.encode("utf-8")),
                filename=name,
                caption=f"📄 الكود الحالي لـ `{name}`\n — `{lines}` سطر"
            )
        except Exception as e:
            await q.edit_message_text(
                f"❌ تعذر قراءة الكود: `{e}`",
                parse_mode="Markdown",
                reply_markup=kb_back(f"d|{name}")
            )

    # ─────────────── معلومات البوت ───────────────
    elif data.startswith("inf|"):
        name = data[4:]
        path = os.path.join(BOTS_DIR, name)
        size = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y/%m/%d %H:%M") if os.path.exists(path) else "—"
        pkgs = bot_install_info.get(name, [])
        code_hash = ""
        try:
            with open(path, "rb") as f:
                code_hash = hashlib.md5(f.read()).hexdigest()[:8]
        except: pass
        await q.edit_message_text(
            f"📋 *معلومات البوت: {name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 الحجم :〖 `{size:.1f} KB` 〗\n"
            f"🗓 آخر تعديل :〖 `{mtime}` 〗\n\n"
            f"🔑 Hash : 【 `{code_hash}` 】\n\n"
            f"🔁 انقطاعات :〖 `{bot_crash_counts.get(name,0)}` 〗\n"
            f"⏱ وقت التشغيل :〖 `{get_uptime(name)}` 〗\n"
            f"📚 مكتبات:〖 `{len(pkgs)}` 〗\n"
            + (f"  " + "\n  ".join(f"【 • `{p}` 】" for p in pkgs) if pkgs else ""),
            parse_mode="Markdown",
            reply_markup=kb_back(f"d|{name}")
        )

    # ─────────────── حذف بوت ───────────────
    elif data.startswith("del|"):
        if not is_owner(uid):
            await q.edit_message_text(
                "⛔️ *هذا الإجراء للمالك فقط*",
                parse_mode="Markdown",
                reply_markup=kb_back("list")
            )
            return
        name = data[4:]
        ctx.user_data["confirm_delete"] = name
        await q.edit_message_text(
            f"🗑 *تأكيد الحذف النهائي*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ هل أنت متأكد من حذف `{name}`؟\n"
            f"هذا الإجراء لا يمكن التراجع عنه!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ نعم، احذف",  callback_data=f"del_confirm|{name}"),
                    InlineKeyboardButton("❌ لا، رجوع",   callback_data=f"d|{name}"),
                ]
            ])
        )

    elif data.startswith("del_confirm|"):
        if not is_owner(uid): return
        name = data[12:]
        stop_bot(name)
        path = os.path.join(BOTS_DIR, name)
        if os.path.exists(path): os.remove(path)
        log_path = os.path.join(LOGS_DIR, f"{name}.log")
        if os.path.exists(log_path): os.remove(log_path)
        for d in [running_bots, bot_start_times, bot_crash_counts, bot_last_error, bot_install_info]:
            d.pop(name, None)
        await q.edit_message_text(
            f"🗑 *تم الحذف النهائي*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ البوت `{name}` حُذف بالكامل",
            parse_mode="Markdown",
            reply_markup=kb_back("list")
        )

    # ─────────────── الإحصائيات ───────────────
    elif data == "stats":
        bots = get_all_bots()
        act  = sum(1 for b in bots if _is_alive(b))
        s    = sys_stats()
        lines = [
            "📊 *لوحة الإحصائيات الشاملة :*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🖥 CPU   `{s['cpu']:.1f}%` {_stars(s['cpu'])}",
            f"💾 RAM   `{fmt_size(s['ram_used'])}/{fmt_size(s['ram_total'])}` {_stars(s['ram_pct'])}",
            f"💿 Disk  `{s['disk_used']:.1f}/{s['disk_total']:.1f} GB` {_stars(s['disk_pct'])}",
            f"⏳ Uptime `{s['uptime']}`",
            "━━━━━━━━━━━━━━━━━━━━━",
            f"🤖 البوتات النشطة : 〖 `{act}` / `{len(bots)}` 〗",
            f"🔁 إجمالي الإنعاشات : 〖 `{db.get('total_restarts',0)}` 〗",
            f"📤 إجمالي الرفع : 〖 `{db.get('upload_count',0)}` 〗",
            "━━━━━━━━━━━━━━━━━━━━━",
        ]
        for b in bots:
            st = bot_status(b)
            up = get_uptime(b)
            cr = bot_crash_counts.get(b, 0)
            r  = get_resources(b)
            lines.append(
                f"{st} `{b}`\n"
                f"   ⏱ {up}  🔁 {cr}  "
                f"CPU `{r['cpu']:.0f}%`  RAM `{r['ram_mb']:.0f}MB`"
            )
        await q.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=kb_refresh_back("stats", "home")
        )

    # ─────────────── الإعدادات ───────────────
    elif data == "settings":
        sub = db.get("sub_admins", [])
        await q.edit_message_text(
            f"⚙️ *إعدادات النظام*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 الأدمنة المرفوعين :〖 `{len(sub)}` 〗\n"
            f"📦 إصدار النظام:〖 `v{VERSION}` 〗",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 إدارة الأدمنة", callback_data="admins")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home")],
            ])
        )

    # ─────────────── إدارة الأدمنز ───────────────
    elif data == "admins":
        if not is_owner(uid):
            await q.edit_message_text("⛔️ للمالك فقط.", reply_markup=kb_back("home"))
            return
        sub  = db.get("sub_admins", [])
        text = (
            f"🎩 *إدارة أدمنة الـبــوت :*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        text += "\n".join(f"  🔰 `{a}`" for a in sub) if sub else "  لا يوجد أدمنة مرفوعين حالياً ."
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=kb_admins())

    elif data == "add_adm":
        if not is_owner(uid): return
        ctx.user_data["act"] = "add_adm"
        await q.edit_message_text(
            "➕ *لإضافة أدمن جديد*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✦ أرسل الـ ID للشخص الجديد :\n"
            "✦ يُمكن الحصول عليه من -> @userinfobot",
            parse_mode="Markdown",
            reply_markup=kb_back("admins")
        )

    elif data.startswith("rm|"):
        if not is_owner(uid): return
        target = int(data[3:])
        if target in db["sub_admins"]:
            db["sub_admins"].remove(target)
            save_db()
        await q.edit_message_text(
            f"✅ *تمت إزالة الأدمن*\n\n`{target}` لم يعد لديه صلاحيات.",
            parse_mode="Markdown",
            reply_markup=kb_back("admins")
        )

    # ─────────────── عن النظام ───────────────
    elif data == "about":
        bots  = get_all_bots()
        total = db.get("upload_count", 0)
        rst   = db.get("total_restarts", 0)
        since = db.get("created_at", "—")[:10]
        await q.edit_message_text(
            f"ℹ️ * ☇ 𝐍𝐄𝐗𝐔𝐒 𝐁𝐎𝐓 𝐑𝐈𝐕𝐄𝐍 ♛*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ الإصدار : 【 `v{VERSION}` 】\n"
            f"🗓 تاريخ الإنشاء : 〘 `{since}` 〙\n"
            f"📤 إجمالي الرفعات :〘 `{total}` 〙\n"
            f"🔁 إجمالي الإنعاشات : 〘 `{rst}` 〙\n"
            f"📁 عدد البوتات : 〘 `{len(bots)}` 〙\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f" *✯ مميــزات الــبـــوت :*\n"
            f"  ✦ تحليل ذكي للمكتبات\n"
            f"  ✦ كشف إصدار PTB تلقائياً\n"
            f"  ✦ مراقبة 24/7 مع إشعارات\n"
            f"  ✦ محرر كود مباشر\n"
            f"  ✦ إحصائيات لحظية\n"
            f"  ✦ نظام أدمن متعدد",
            parse_mode="Markdown",
            reply_markup=kb_back("home")
        )


# ══════════════════════════════════════════════════════════
#               استقبال الملفات — القلب النابض
# ══════════════════════════════════════════════════════════
async def on_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    doc = update.message.document
    if not doc or not doc.file_name.endswith(".py"):
        await update.message.reply_text(
            "⚠️ *خطأ في نوع الملف*\n\nالمقبول يعيوني فقط: ملفات `.py`",
            parse_mode="Markdown"
        )
        return

    act      = ctx.user_data.pop("act", "upload")
    is_edit  = act.startswith("edit|")
    bot_name = act.split("|", 1)[1] if is_edit else doc.file_name
    save_path = os.path.join(BOTS_DIR, bot_name)

    # تحميل الملف
    tg_file = await doc.get_file()
    await tg_file.download_to_drive(save_path)

    # قراءة الكود
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            code = f.read()
    except UnicodeDecodeError:
        await update.message.reply_text("❌ الملف يحتوي على ترميز غير صحيح. احفظه بـ UTF-8.")
        os.remove(save_path)
        return

    # ── فحص الصيغة ──
    ok_syn, syn_err = check_syntax(code)
    if not ok_syn:
        await update.message.reply_text(
            f"❌ *خطأ في صيغة الكود!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"`{syn_err}`\n\n"
            f"صحح الكود وأعد الرفع يروحي.",
            parse_mode="Markdown"
        )
        os.remove(save_path)
        return

    # ── رسالة البداية ──
    pkgs_needed = build_install_list(code)
    ptb_ver = detect_ptb_version(code) if "telegram" in code else None

    msg = await update.message.reply_text(
        f"📥 *{bot_name}* — تم الأستلام بنجاح\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ `1/3` الكود سليم\n"
        f"⏳ `2/3` تثبيت {len(pkgs_needed)} مكتبة..."
        + (f"\n🔍 إصدار PTB: `{ptb_ver.split('>=')[1] if ptb_ver else '—'}`" if ptb_ver else ""),
        parse_mode="Markdown"
    )

    db["upload_count"] = db.get("upload_count", 0) + 1
    save_db()

    def _pipeline():
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except:
            return

        def _edit(txt, kb=None):
            if not loop.is_running(): return
            kw = {"parse_mode": "Markdown"}
            if kb: kw["reply_markup"] = kb
            asyncio.run_coroutine_threadsafe(msg.edit_text(txt, **kw), loop)

        # إيقاف القديم لو تعديل
        if is_edit:
            stop_bot(bot_name)
            time.sleep(1.5)

        # ── الخطوة 2: تثبيت المكتبات ──
        ok_i, installed, install_err = install_packages(save_path)
        pkg_status = "✅" if ok_i else "⚠️"
        pkg_txt = f"{pkg_status} `2/3` " + (
            f"تم تثبيت {len(installed)} مكتبة" if ok_i
            else f"مشكلة في التثبيت:\n```{install_err[:150]}```"
        )

        _edit(
            f"📥 *{bot_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ `1/3` الكود سليم\n"
            f"{pkg_txt}\n"
            f"⏳ `3/3` تشغيل البوت..."
        )

        # ── الخطوة 3: التشغيل ──
        ok_r, run_err = start_bot(bot_name)

        if ok_r:
            label = "تعديل وتحديث" if is_edit else "رفع وتشغيل"
            installed_txt = ""
            if installed:
                installed_txt = "\n📚 المكتبات المثبتة:\n" + "\n".join(f"  • `{p}`" for p in installed[:8])
                if len(installed) > 8:
                    installed_txt += f"\n  _(و {len(installed)-8} أخرى)_"

            _edit(
                f"🎉 *تم {label} {bot_name} بنجاح!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✦ الكود سليم\n"
                f"✦ المكتبات مثبتة\n"
                f"✦ البوت يعمل الآن 🟢\n"
                f"✦ المراقبة الدائمة فعّالة"
                f"{installed_txt}",
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📊 التفاصيل",  callback_data=f"d|{bot_name}"),
                        InlineKeyboardButton("📄 السجلات", callback_data=f"log|{bot_name}"),
                    ],
                    [InlineKeyboardButton("📋 قائمة البوتات", callback_data="list")],
                ])
            )
        else:
            short = run_err.strip()[-500:] if run_err else "خطأ غير معروف"
            _edit(
                f"⚠️ *{bot_name} — توقف فوراً*\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✅ `1/3` الكود سليم\n"
                f"{pkg_status} `2/3` المكتبات\n"
                f"❌ `3/3` البوت انهار عند التشغيل\n\n"
                f"*سبب الخطأ:*\n"
                f"```\n{short}\n```\n\n"
                f"💡 تحقق من الـ Token أو المكتبات",
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📄 السجلات", callback_data=f"log|{bot_name}"),
                        InlineKeyboardButton("📝 تعديل",   callback_data=f"edi|{bot_name}"),
                    ],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="list")],
                ])
            )

    threading.Thread(target=_pipeline, daemon=True).start()


# ══════════════════════════════════════════════════════════
#               استقبال النصوص
# ══════════════════════════════════════════════════════════
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    text = update.message.text.strip()
    act  = ctx.user_data.get("act", "")

    # ─ إضافة أدمن ─
    if act == "add_adm":
        ctx.user_data.pop("act")
        try:
            nid = int(text)
            if nid == ADMIN_ID:
                await update.message.reply_text("⚠️ هذا هو المالك بالفعل.")
                return
            if nid not in db["sub_admins"]:
                db["sub_admins"].append(nid)
                save_db()
            await update.message.reply_text(
                f"✅ *تم إضافة الأدمن بنجاح*\n\n"
                f"🔰 `{nid}` أصبح أدمناً للبوت الآن.",
                parse_mode="Markdown",
                reply_markup=kb_admins()
            )
        except ValueError:
            await update.message.reply_text(
                "❌ *✦ خطأ*\n\nأرسل رقم ID صحيح (أرقام فقط).",
                parse_mode="Markdown"
            )
        return

    # ─ تعديل كود مباشر بنص ─
    if act.startswith("edit|"):
        name = act.split("|", 1)[1]
        ok, err = check_syntax(text)
        if not ok:
            await update.message.reply_text(
                f"❌ *خطأ في الكود*\n\n`{err}`\n\nصحح وأعد الإرسال يروحي.",
                parse_mode="Markdown"
            )
            return  # لا نمسح act

        ctx.user_data.pop("act")
        path = os.path.join(BOTS_DIR, name)
        stop_bot(name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        msg = await update.message.reply_text(
            f"💾 *جارٍ حفظ التعديلات وإعادة تشغيل {name}...*",
            parse_mode="Markdown"
        )
        time.sleep(1)
        ok_r, err_r = start_bot(name)
        if ok_r:
            await msg.edit_text(
                f"✅ *تم حفظ التعديلات بنجاح!*\n\n🤖 `{name}` يعمل الآن 🟢",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 تفاصيل", callback_data=f"d|{name}")
                ]])
            )
        else:
            await msg.edit_text(
                f"❌ *فشل التشغيل بعد الحفظ*\n\n```\n{err_r.strip()[-300:]}\n```",
                parse_mode="Markdown",
                reply_markup=kb_back(f"d|{name}")
            )


# ══════════════════════════════════════════════════════════
#                   نقطة الإطلاق
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    log.info("═" * 55)
    log.info(f"  ⚡ NEXUS BOT MANAGER  v{VERSION}")
    log.info("═" * 55)

    # تأكد من psutil
    try:
        import psutil
    except ImportError:
        log.info("تثبيت psutil...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "-q"])

    # تشغيل keep_alive
    keep_alive()

    # بناء التطبيق
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    _app = app

    # تسجيل الهاندلرز
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, on_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # تشغيل المراقب في خيط مستقل
    threading.Thread(target=_monitor_worker, daemon=True).start()

    log.info("✅ النظام جاهز — يستقبل الأوامر")
    log.info("═" * 55)

    app.run_polling(drop_pending_updates=True)