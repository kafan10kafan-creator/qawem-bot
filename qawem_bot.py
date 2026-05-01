import logging
import os
import random
import pytz
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# المتغيرات
TOKEN = os.environ.get("TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CAIRO_TZ = pytz.timezone("Africa/Cairo")
ASK_NAME, ASK_LEVEL = range(2)

def main_menu():
    kb = [[KeyboardButton("🎯 أهدافي اليومية"), KeyboardButton("📊 تقييم أدائي")],
          [KeyboardButton("🔥 الـ Streak الخاص بي"), KeyboardButton("🏆 لوحة المتصدرين")],
          [KeyboardButton("💡 نصيحة سريعة"), KeyboardButton("🤖 اسأل قاوم (AI)")]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = database.get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("أهلاً بك في منظومة قاوم! 🚀\nممكن تقولي اسمك إيه؟")
        return ASK_NAME
    await update.message.reply_text(f"أهلاً يا {user['name']}! جاهز للعمل؟", reply_markup=main_menu())
    return ConversationHandler.END

async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("تشرفنا! إنت فين دلوقتي؟ (مبتدئ / متوسط / متقدم)")
    return ASK_LEVEL

async def got_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_user_db(update.effective_chat.id, name=context.user_data["name"], level=update.message.text, is_allowed=1)
    await update.message.reply_text("تم الإعداد! 🚀", reply_markup=main_menu())
    return ConversationHandler.END

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = database.get_user(update.effective_user.id)
    if not user: return

    if text == "🏆 لوحة المتصدرين":
        top = database.get_leaderboard()
        msg = "🏆 المتصدرين:\n" + "\n".join([f"{i+1}. {u[0]} - {u[1]} نقطة" for i, u in enumerate(top)])
        await update.message.reply_text(msg)
    elif text == "🔥 الـ Streak الخاص بي":
        await update.message.reply_text(f"🔥 الالتزام: {user['streak']} يوم!")
    elif "🤖" in text:
        await update.message.reply_text("🤖 اسألني أي سؤال!")
        context.user_data['ai'] = True
    elif context.user_data.get('ai'):
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        res = client.messages.create(model="claude-3-haiku-20240307", max_tokens=300, messages=[{"role":"user","content":text}])
        await update.message.reply_text(res.content[0].text)
        context.user_data['ai'] = False
    else:
        await update.message.reply_text("اختار من القائمة! 👇", reply_markup=main_menu())

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
                ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_level)]},
        fallbacks=[CommandHandler("start", start)]))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    database.init_db()
    main()
