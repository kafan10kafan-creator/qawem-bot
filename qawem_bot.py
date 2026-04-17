import logging
import asyncio
from datetime import time
import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ============================================================
#  ضع الـ Token بتاعك هنا
import os TOKEN = os.environ.get("TOKEN", "")
# ============================================================

CAIRO_TZ = pytz.timezone("Africa/Cairo")
logging.basicConfig(level=logging.INFO)

# مراحل المحادثة
ASK_GOALS, ASK_DONE = range(2)

# ============================================================
# رسائل الصبح - بيسأل عن أهداف اليوم
# ============================================================
async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🌅 *صباح النور يا بطل!*\n\n"
            "اليوم ده فرصة جديدة عشان تقاوم وتنجز 💪\n\n"
            "قولي إيه *أهم ٣ حاجات* هتعملها النهارده؟\n"
            "اكتبهم هنا وأنا هفضل معاك طول اليوم 📝"
        ),
        parse_mode="Markdown"
    )

# ============================================================
# رسالة الضهر - تذكير بالمهام
# ============================================================
async def noon_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    goals = context.bot_data.get(f"goals_{chat_id}", "مهامك اللي كتبتها الصبح")
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "☀️ *تذكير منتصف اليوم!*\n\n"
            f"فاكر أهدافك النهارده؟\n_{goals}_\n\n"
            "إيه اللي خلصته لحد دلوقتي؟ 🎯\n"
            "متوقفش — كمّل وأنت قادر! 💥"
        ),
        parse_mode="Markdown"
    )

# ============================================================
# رسالة المساء - المحاسبة
# ============================================================
async def evening_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🌙 *وقت المحاسبة يا بطل!*\n\n"
            "اليوم ده اتقفل — خليني أعرف:\n\n"
            "✅ إيه اللي *خلصته* النهارده؟\n"
            "❌ إيه اللي *فاتك* وهتعمله بكره؟\n"
            "⭐ إيه *أحسن حاجة* حصلت النهارده؟\n\n"
            "اكتب إجاباتك وأنا هحتفل معاك بكل خطوة 🏆"
        ),
        parse_mode="Markdown"
    )

# ============================================================
# أمر /start
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name

    keyboard = [["🎯 أهدافي النهارده", "📊 تقييم يومي"],
                ["💡 تيب إنتاجية", "🔔 فعّل التذكيرات"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"أهلاً *{name}* في بوت قاوم! 👊\n\n"
        "أنا هنا عشان أساعدك تقاوم التسويف وتستغل كل دقيقة في يومك 💪\n\n"
        "اختار من القايمة أو اكتب /help عشان تعرف أوامري",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # جدول الرسائل اليومية
    await schedule_daily_messages(context, chat_id)

# ============================================================
# جدولة الرسائل اليومية
# ============================================================
async def schedule_daily_messages(context, chat_id):
    # امسح الجداول القديمة لو موجودة
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # الصبح الساعة 7
    context.job_queue.run_daily(
        morning_message,
        time=time(7, 0, tzinfo=CAIRO_TZ),
        chat_id=chat_id,
        name=str(chat_id)
    )
    # الضهر الساعة 1
    context.job_queue.run_daily(
        noon_message,
        time=time(13, 0, tzinfo=CAIRO_TZ),
        chat_id=chat_id,
        name=str(chat_id)
    )
    # المساء الساعة 9
    context.job_queue.run_daily(
        evening_message,
        time=time(21, 0, tzinfo=CAIRO_TZ),
        chat_id=chat_id,
        name=str(chat_id)
    )

# ============================================================
# معالجة الأزرار والرسائل
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if "أهدافي النهارده" in text:
        await update.message.reply_text(
            "🎯 *إيه أهم ٣ أهداف ليك النهارده؟*\n\n"
            "اكتبهم ورقم كل واحد عشان نتابعهم سوا 📝",
            parse_mode="Markdown"
        )
        return ASK_GOALS

    elif "تقييم يومي" in text:
        await update.message.reply_text(
            "📊 *تقييم يومك النهارده*\n\n"
            "من ١ لـ ١٠ — إيه تقييمك لإنتاجيتك النهارده؟\n"
            "وإيه اللي ممكن تتحسن فيه بكره؟ 🤔",
            parse_mode="Markdown"
        )

    elif "تيب إنتاجية" in text:
        tips = [
            "🧠 قسّم أي مهمة كبيرة لخطوات صغيرة — ٢٥ دقيقة شغل ثم ٥ راحة (Pomodoro)",
            "📵 افتح الموبايل بس في أوقات محددة — مش كل دقيقة",
            "📋 اكتب مهامك بالليل عشان الصبح تبدأ على طول",
            "🏃 ابدأ بأصعب مهمة الصبح — ده اسمه 'Eat the Frog'",
            "💧 اشرب ميه كتير — الجفاف بيأثر على التركيز بجد",
        ]
        import random
        tip = random.choice(tips)
        await update.message.reply_text(
            f"💡 *تيب النهارده:*\n\n{tip}",
            parse_mode="Markdown"
        )

    elif "فعّل التذكيرات" in text:
        await schedule_daily_messages(context, chat_id)
        await update.message.reply_text(
            "🔔 *التذكيرات اتفعّلت!*\n\n"
            "هتوصلك رسايل كل يوم:\n"
            "☀️ الصبح الساعة ٧ — أهداف اليوم\n"
            "🌤️ الضهر الساعة ١ — تذكير بالمهام\n"
            "🌙 المساء الساعة ٩ — محاسبة اليوم\n\n"
            "يلا نقاوم سوا! 💪",
            parse_mode="Markdown"
        )

    else:
        # لو بعت أهدافه، احفظها
        context.bot_data[f"goals_{chat_id}"] = text
        await update.message.reply_text(
            "✅ *تمام! سجّلت أهدافك*\n\n"
            f"_{text}_\n\n"
            "هفضل أذكرك بيها خلال اليوم 💪\n"
            "يلا نقاوم!",
            parse_mode="Markdown"
        )

# ============================================================
# أمر /help
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *أوامر بوت قاوم:*\n\n"
        "/start — ابدأ من الأول\n"
        "/help — اعرض الأوامر\n\n"
        "أو استخدم الأزرار في الأسفل 👇",
        parse_mode="Markdown"
    )

# ============================================================
# تشغيل البوت
# ============================================================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ بوت قاوم شغال!")
    app.run_polling()

if __name__ == "__main__":
    main()
