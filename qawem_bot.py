import logging
import os
import random
from datetime import time
import pytz
import anthropic
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ============================================================
# الإعدادات الأساسية
# ============================================================
TOKEN = os.environ.get("TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))  # ID بتاعك كمالك
CAIRO_TZ = pytz.timezone("Africa/Cairo")
logging.basicConfig(level=logging.INFO)

ASK_NAME, ASK_LEVEL = range(2)

# قائمة المستخدمين المسموح ليهم
ALLOWED_USERS = set()

# اقتباسات عربية
QUOTES = [
    "الوقت كالسيف إن لم تقطعه قطعك — علي بن أبي طالب",
    "من جد وجد ومن زرع حصد — مثل عربي",
    "خير الأعمال أدومها وإن قل — حديث نبوي",
    "الصبر مفتاح الفرج — مثل عربي",
    "من تأنى نال ما تمنى — مثل عربي",
    "لا تؤجل عمل اليوم إلى الغد — ابن عقيل",
    "النجاح ليس نهاية الطريق — مثل عربي",
]

# ============================================================
# وظيفة Claude AI
# ============================================================
def ask_claude(question, user_name, context_info=""):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": f"""أنت مساعد ذكي اسمه "قاوم" متخصص في الإنتاجية وتنظيم الوقت وتحقيق الأهداف.
اسم المستخدم: {user_name}
{context_info}

مهم جداً:
- اردد دايماً بالعربية
- كن إيجابياً ومحفزاً دايماً
- خليك مختصر (3-5 جمل)
- استخدم اسم المستخدم في ردك
- لو السؤال مش عن الإنتاجية، ارد بشكل عام ومفيد

السؤال: {question}"""
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        logging.error(f"Claude error: {e}")
        return f"معلش يا {user_name}، فيه مشكلة صغيرة دلوقتي. جرب تاني بعد شوية 😊"

# ============================================================
# التحقق من الصلاحيات
# ============================================================
def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed(user_id):
    return user_id == OWNER_ID or user_id in ALLOWED_USERS

# ============================================================
# الرسائل التلقائية
# ============================================================
async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    streak = user_data.get("streak", 1)
    level = user_data.get("level", "medium")
    quote = random.choice(QUOTES)
    user_data["streak"] = streak + 1
    context.bot_data[str(chat_id)] = user_data

    if level == "beginner":
        goal_q = "قولي إيه *حاجة واحدة* هتعملها النهارده؟ 🎯"
    elif level == "medium":
        goal_q = "قولي إيه *أهم 3 حاجات* هتعملها النهارده؟ 🎯"
    else:
        goal_q = "قولي أهدافك وإيه *أصعب تحدي* هتواجهه النهارده؟ 🎯"

    msg = f"🌅 *صباح النور يا {name}!*\n\n📌 _{quote}_\n\n🔥 اليوم *{streak}* متتالي!\n\n{goal_q}"

    if streak == 7:
        msg += f"\n\n🏆 *أسبوع كامل يا {name}! إنت أسطورة!*"
    elif streak == 30:
        msg += f"\n\n👑 *30 يوم يا {name}! إنت من فئة النخبة!*"
    elif streak == 100:
        msg += f"\n\n🌟 *100 يوم يا {name}! إنت ملهمة!*"

    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def noon_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    last_goals = user_data.get("last_goals", "")
    if last_goals:
        msg = f"☀️ *تذكير منتصف اليوم يا {name}!*\n\nفاكر أهدافك؟\n_{last_goals}_\n\nإيه اللي خلصته لحد دلوقتي؟ 💪"
    else:
        msg = f"☀️ *تذكير منتصف اليوم يا {name}!*\n\nإيه اللي خلصته لحد دلوقتي؟ 🎯\nكمّل وأنت قادر! 💥"
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def evening_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    name = context.bot_data.get(str(chat_id), {}).get("name", "بطل")
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🌙 *وقت المحاسبة يا {name}!*\n\n✅ إيه اللي خلصته النهارده؟\n❌ إيه اللي فاتك؟\n⭐ أحسن حاجة حصلت؟\n\nاكتب إجاباتك وأنا هحتفل معاك 🎉",
        parse_mode="Markdown"
    )

async def friday_review(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    streak = user_data.get("streak", 0)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📊 *مراجعة الأسبوع يا {name}!*\n\n🔥 {streak} يوم متتالي!\n\n١. إيه أحسن حاجة الأسبوع ده؟\n٢. إيه أكبر تحدي؟\n٣. هدفك الأسبوع الجاي؟",
        parse_mode="Markdown"
    )

def schedule_jobs(context, chat_id):
    for job in context.job_queue.get_jobs_by_name(str(chat_id)):
        job.schedule_removal()
    context.job_queue.run_daily(morning_message, time=time(7, 0, tzinfo=CAIRO_TZ), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(noon_message, time=time(13, 0, tzinfo=CAIRO_TZ), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(evening_message, time=time(21, 0, tzinfo=CAIRO_TZ), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(friday_review, time=time(20, 0, tzinfo=CAIRO_TZ), days=(4,), chat_id=chat_id, name=str(chat_id)+"_fri")

# ============================================================
# أوامر المالك
# ============================================================
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ مش عندك صلاحية!")
        return
    if not context.args:
        await update.message.reply_text("استخدم: /adduser [ID المستخدم]")
        return
    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.add(user_id)
        await update.message.reply_text(f"✅ تم إضافة المستخدم {user_id}")
        try:
            await context.bot.send_message(chat_id=user_id, text="🎉 *أهلاً! تم قبولك في منظومة قاوم!*\n\nابعت /start عشان تبدأ رحلتك 💪", parse_mode="Markdown")
        except:
            pass
    except:
        await update.message.reply_text("❌ ID غلط!")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ مش عندك صلاحية!")
        return
    if not context.args:
        await update.message.reply_text("استخدم: /removeuser [ID المستخدم]")
        return
    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.discard(user_id)
        await update.message.reply_text(f"✅ تم إزالة المستخدم {user_id}")
    except:
        await update.message.reply_text("❌ ID غلط!")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not ALLOWED_USERS:
        await update.message.reply_text("📋 مفيش مستخدمين مضافين دلوقتي")
        return
    users_list = "\n".join([f"• {uid}" for uid in ALLOWED_USERS])
    await update.message.reply_text(f"📋 *المستخدمين المسموح ليهم:*\n\n{users_list}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("استخدم: /broadcast [الرسالة]")
        return
    msg = " ".join(context.args)
    sent = 0
    for uid in ALLOWED_USERS:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 *رسالة من قاوم:*\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ تم إرسال الرسالة لـ {sent} شخص")

async def owner_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    total = len(ALLOWED_USERS)
    active = sum(1 for uid in ALLOWED_USERS if context.bot_data.get(str(uid), {}).get("streak", 0) > 0)
    await update.message.reply_text(
        f"📊 *إحصائيات قاوم:*\n\n👥 إجمالي المستخدمين: {total}\n✅ النشطين: {active}\n\n*أوامرك يا مالك:*\n/adduser [ID] — إضافة مستخدم\n/removeuser [ID] — إزالة مستخدم\n/listusers — قائمة المستخدمين\n/broadcast [رسالة] — رسالة لكل الناس",
        parse_mode="Markdown"
    )

# ============================================================
# بداية المحادثة
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("⛔ عذراً، البوت ده حصري.\n\nتواصل مع المالك عشان تنضم لمنظومة قاوم 💪")
        if OWNER_ID:
            await context.bot.send_message(chat_id=OWNER_ID, text=f"🔔 *طلب انضمام جديد!*\n\nID: `{user_id}`\nالاسم: {update.effective_user.first_name}", parse_mode="Markdown")
        return ConversationHandler.END
    await update.message.reply_text("أهلاً! 👋 أنا بوت *قاوم* — رفيقك في رحلة الإنتاجية 💪\n\n*إيه اسمك؟* 😊", parse_mode="Markdown")
    return ASK_NAME

async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name
    keyboard = [["🔴 محتاج أبدأ من الصفر"], ["🟡 بدأت بس بتتعثر"], ["🟢 كويس وعايز أتحسن"]]
    await update.message.reply_text(f"أهلاً يا *{name}*! 🎉\n\n*إنت دلوقتي فين في رحلتك؟*", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return ASK_LEVEL

async def got_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    name = context.user_data.get("name", "بطل")
    if "الصفر" in text:
        level, msg = "beginner", "هنبدأ بخطوات صغيرة 🌱"
    elif "بتتعثر" in text:
        level, msg = "medium", "هنبني عليك 💪"
    else:
        level, msg = "advanced", "هنتحداك أكتر 🚀"
    context.bot_data[str(chat_id)] = {"name": name, "level": level, "streak": 1, "last_goals": ""}
    keyboard = [["🎯 أهدافي النهارده", "📊 تقييم يومي"], ["💡 تيب إنتاجية", "🔥 streak بتاعي"], ["🔔 فعّل التذكيرات"]]
    await update.message.reply_text(f"تمام يا *{name}*! {msg}\n\nالتذكيرات اتفعّلت تلقائياً ☀️7ص 🌤️1ظ 🌙9م 📊جمعة\n\nاختار من القايمة أو *اسألني أي سؤال* 👇", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    schedule_jobs(context, chat_id)
    if OWNER_ID:
        await context.bot.send_message(chat_id=OWNER_ID, text=f"🎉 *مستخدم جديد انضم!*\n\nالاسم: {name}\nالمستوى: {level}\nID: `{chat_id}`", parse_mode="Markdown")
    return ConversationHandler.END

# ============================================================
# معالجة الرسائل
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("⛔ مش عندك صلاحية. تواصل مع المالك.")
        return

    text = update.message.text
    chat_id = update.effective_chat.id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    streak = user_data.get("streak", 1)
    level = user_data.get("level", "medium")

    if "أهدافي" in text:
        await update.message.reply_text(f"🎯 يا *{name}* — إيه أهدافك النهارده؟ 📝\n\nاكتبهم وأنا هساعدك تخططلهم!", parse_mode="Markdown")

    elif "تقييم" in text:
        await update.message.reply_text(f"📊 يا *{name}* — من 1 لـ 10 إيه تقييمك لإنتاجيتك النهارده؟\n\nوإيه اللي هتتحسن فيه بكره؟", parse_mode="Markdown")

    elif "تيب" in text or "إنتاجية" in text:
        await update.message.chat.send_action("typing")
        tip = ask_claude("اديني تيب إنتاجية عملي ومختصر ومحفز", name, f"مستوى المستخدم: {level}, streak: {streak} يوم")
        await update.message.reply_text(f"💡 *تيب النهارده يا {name}:*\n\n{tip}", parse_mode="Markdown")

    elif "streak" in text or "🔥" in text:
        if streak < 7:
            extra = f"باقي {7-streak} أيام على أسبوع كامل! 💪"
        elif streak < 30:
            extra = f"باقي {30-streak} يوم على شهر كامل! 🚀"
        else:
            extra = "إنت من فئة النخبة! 👑"
        await update.message.reply_text(f"🔥 *الـ Streak بتاعك يا {name}:*\n\nاليوم *{streak}* متتالي!\n\n{extra}", parse_mode="Markdown")

    elif "فعّل" in text or "تذكيرات" in text:
        schedule_jobs(context, chat_id)
        await update.message.reply_text(f"🔔 *التذكيرات اتفعّلت يا {name}!*\n\n☀️7ص — أهداف اليوم\n🌤️1ظ — تذكير\n🌙9م — محاسبة\n📊جمعة8م — مراجعة أسبوعية", parse_mode="Markdown")

    else:
        await update.message.chat.send_action("typing")
        context_info = f"مستوى المستخدم: {level}, streak: {streak} يوم, آخر أهداف: {user_data.get('last_goals', 'مش محددة')}"
        response = ask_claude(text, name, context_info)
        user_data["last_goals"] = text
        context.bot_data[str(chat_id)] = user_data
        await update.message.reply_text(response)

# ============================================================
# تشغيل البوت
# ============================================================
def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_level)]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", owner_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ بوت قاوم الذكي شغال!")
    app.run_polling()

if __name__ == "__main__":
    main()
