import logging
import os
import random
from datetime import time
import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = os.environ.get("TOKEN", "")
CAIRO_TZ = pytz.timezone("Africa/Cairo")
logging.basicConfig(level=logging.INFO)

ASK_NAME, ASK_LEVEL = range(2)

QUOTES = [
    "الوقت كالسيف إن لم تقطعه قطعك — علي بن أبي طالب",
    "من جد وجد ومن زرع حصد — مثل عربي",
    "لا تؤجل عمل اليوم إلى الغد — ابن عقيل",
    "خير الأعمال أدومها وإن قل — حديث نبوي",
    "الصبر مفتاح الفرج — مثل عربي",
    "من تأنى نال ما تمنى — مثل عربي",
    "اطلب العلم من المهد إلى اللحد — حديث نبوي",
]

async def morning_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    level = user_data.get("level", "medium")
    streak = user_data.get("streak", 1)
    quote = random.choice(QUOTES)
    user_data["streak"] = streak + 1
    context.bot_data[str(chat_id)] = user_data

    if level == "beginner":
        goal_q = "قولي إيه *حاجة واحدة بس* هتعملها النهارده؟"
    elif level == "medium":
        goal_q = "قولي إيه *أهم 3 حاجات* هتعملها النهارده؟"
    else:
        goal_q = "قولي أهدافك وإيه *أصعب حاجة* هتواجهها؟"

    msg = f"🌅 *صباح النور يا {name}!*\n\n📌 _{quote}_\n\n🔥 اليوم {streak} متتالي!\n\n{goal_q}"
    if streak == 7:
        msg += f"\n\n🏆 *أسبوع كامل يا {name}! إنت أسطورة!*"
    elif streak == 30:
        msg += f"\n\n👑 *30 يوم يا {name}! إنت من فئة النخبة!*"

    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def noon_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    name = context.bot_data.get(str(chat_id), {}).get("name", "بطل")
    await context.bot.send_message(chat_id=chat_id, text=f"☀️ *تذكير منتصف اليوم يا {name}!*\n\nإيه اللي خلصته؟ 🎯\nكمّل وأنت قادر! 💥", parse_mode="Markdown")

async def evening_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    name = context.bot_data.get(str(chat_id), {}).get("name", "بطل")
    await context.bot.send_message(chat_id=chat_id, text=f"🌙 *وقت المحاسبة يا {name}!*\n\n✅ إيه اللي خلصته؟\n❌ إيه اللي فاتك؟\n⭐ أحسن حاجة حصلت؟", parse_mode="Markdown")

async def friday_review(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    streak = user_data.get("streak", 0)
    await context.bot.send_message(chat_id=chat_id, text=f"📊 *مراجعة الأسبوع يا {name}!*\n\n🔥 {streak} يوم متتالي!\n\n١. إيه أحسن حاجة الأسبوع ده؟\n٢. إيه أكبر تحدي؟\n٣. هدفك الأسبوع الجاي؟", parse_mode="Markdown")

def schedule_jobs(context, chat_id):
    for job in context.job_queue.get_jobs_by_name(str(chat_id)):
        job.schedule_removal()
    context.job_queue.run_daily(morning_message, time=time(7, 0, tzinfo=CAIRO_TZ), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(noon_message, time=time(13, 0, tzinfo=CAIRO_TZ), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(evening_message, time=time(21, 0, tzinfo=CAIRO_TZ), chat_id=chat_id, name=str(chat_id))
    context.job_queue.run_daily(friday_review, time=time(20, 0, tzinfo=CAIRO_TZ), days=(4,), chat_id=chat_id, name=str(chat_id)+"_fri")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً! 👋 أنا بوت *قاوم* 💪\n\n*إيه اسمك؟* 😊", parse_mode="Markdown")
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
    context.bot_data[str(chat_id)] = {"name": name, "level": level, "streak": 1}
    keyboard = [["🎯 أهدافي النهارده", "📊 تقييم يومي"], ["💡 تيب إنتاجية", "🔥 streak بتاعي"], ["🔔 فعّل التذكيرات"]]
    await update.message.reply_text(f"تمام يا *{name}*! {msg}\n\nالتذكيرات اتفعّلت ☀️7ص 🌤️1ظ 🌙9م 📊جمعة\n\nاختار من القايمة 👇", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    schedule_jobs(context, chat_id)
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    user_data = context.bot_data.get(str(chat_id), {})
    name = user_data.get("name", "بطل")
    streak = user_data.get("streak", 1)

    if "أهدافي" in text:
        await update.message.reply_text(f"🎯 يا *{name}* — إيه أهدافك النهارده؟ 📝", parse_mode="Markdown")
    elif "تقييم" in text:
        await update.message.reply_text(f"📊 يا *{name}* — من 1 لـ 10 إيه تقييمك لإنتاجيتك؟", parse_mode="Markdown")
    elif "تيب" in text or "إنتاجية" in text:
        tips = ["🧠 25 دقيقة شغل و5 راحة — Pomodoro", "📵 افتح السوشيال في أوقات محددة بس", "📋 اكتب مهامك بالليل", "🏃 ابدأ بأصعب مهمة الصبح", "💧 اشرب ميه كتير", "😴 7 ساعات نوم على الأقل"]
        await update.message.reply_text(f"💡 *تيب النهارده يا {name}:*\n\n{random.choice(tips)}", parse_mode="Markdown")
    elif "streak" in text or "🔥" in text:
        if streak < 7:
            extra = f"باقي {7-streak} أيام على أسبوع كامل!"
        elif streak < 30:
            extra = f"باقي {30-streak} يوم على شهر كامل! 🚀"
        else:
            extra = "إنت من فئة النخبة! 👑"
        await update.message.reply_text(f"🔥 *الـ Streak بتاعك يا {name}:*\n\nاليوم *{streak}* متتالي!\n\n{extra}", parse_mode="Markdown")
    elif "فعّل" in text or "تذكيرات" in text:
        schedule_jobs(context, chat_id)
        await update.message.reply_text(f"🔔 *التذكيرات اتفعّلت يا {name}!*\n\n☀️7ص 🌤️1ظ 🌙9م 📊جمعة8م", parse_mode="Markdown")
    else:
        user_data["last_goals"] = text
        context.bot_data[str(chat_id)] = user_data
        await update.message.reply_text(f"✅ *تمام يا {name}!* 💪\nيلا نقاوم سوا!", parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)], ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_level)]},
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("بوت قاوم المطور شغال!")
    app.run_polling()

if __name__ == "__main__":
    main()
