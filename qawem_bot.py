import logging, os, database
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TOKEN", "")
ASK_NAME, ASK_LEVEL = range(2)

def main_menu():
    kb = [[KeyboardButton("🎯 أهدافي اليومية"), KeyboardButton("📊 تقييم أدائي")],
          [KeyboardButton("🔥 الـ Streak الخاص بي"), KeyboardButton("🏆 لوحة المتصدرين")]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update, context):
    user = database.get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("أهلاً بك في منظومة قاوم! 🚀\nممكن تقولي اسمك إيه؟")
        return ASK_NAME
    await update.message.reply_text(f"أهلاً يا {user['name']}!", reply_markup=main_menu())
    return ConversationHandler.END

async def got_name(update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("تشرفنا! إنت فين دلوقتي؟ (مبتدئ / متوسط / متقدم)")
    return ASK_LEVEL

async def got_level(update, context):
    database.add_user_db(update.effective_chat.id, name=context.user_data["name"], level=update.message.text, is_allowed=1)
    await update.message.reply_text("تم الإعداد! 🚀", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
                ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_level)]},
        fallbacks=[CommandHandler("start", start)]))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    database.init_db()
    main()
