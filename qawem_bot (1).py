import logging
import os
import random
from datetime import time
import pytz
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# ============================================================
# الإعدادات الأساسية
# ============================================================
TOKEN = os.environ.get("TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
CAIRO_TZ = pytz.timezone("Africa/Cairo")

logging.basicConfig(level=logging.INFO)
ASK_NAME, ASK_LEVEL = range(2)

# ============================================================
# القوائم والأزرار
# ============================================================
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🎯 أهدافي اليومية"), KeyboardButton("📊 تقييم أدائي")],
        [KeyboardButton("🔥 الـ Streak الخاص بي"), KeyboardButton("🏆 لوحة المتصدرين")],
        [KeyboardButton("💡 نصيحة سريعة"), KeyboardButton("🤖 اسأل قاوم (AI)")],
        [KeyboardButton("⚙️ الإعدادات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ============================================================
# وظائف الذكاء الاصطناعي (محصورة للمشتركين)
# ============================================================
def ask_claude(question, user_name, context_info=""):
    if not ANTHROPIC_API_KEY:
        return "⚠️ خدمة المساعد الذكي غير متوفرة حالياً."
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            messages=[{"role": "user", "content": f"أنت 'قاوم'، مساعد إنتاجية مصري محفز. اسم المستخدم: {user_name}. {context_info}. أجب باختصار شديد وبشكل عملي على: {question}"}]
        )
        return message.content[0].text
    except Exception:
        return f"يا {user_name}، المساعد مشغول شوية، جرب تسألني كمان دقيقة! 😊"

# ============================================================
# معالجة المحادثة والمسارات
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = database.get_user(user_id)
    
    if not user:
        await update.message.reply_text("أهلاً بك في منظومة *قاوم*! 🚀\nأنا مساعدك الشخصي للإنتاجية. عشان نبدأ، ممكن تقولي اسمك إيه؟", parse_mode="Markdown")
        return ASK_NAME
    
    if user['is_allowed'] == 0:
        await update.message.reply_text("⛔ حسابك قيد المراجعة. تواصل مع إدارة المنظمة لتفعيل اشتراكك.")
        return ConversationHandler.END

    await update.message.reply_text(f"أهلاً بعودتك يا {user['name']}! 👋\nجاهز لإنجاز مهام النهارده؟", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name
    keyboard = [["🔴 مبتدئ", "🟡 متوسط", "🟢 متقدم"]]
    await update.message.reply_text(f"تشرفنا يا {name}! إنت فين دلوقتي في رحلة الإنتاجية؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return ASK_LEVEL

async def got_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = update.message.text
    chat_id = update.effective_chat.id
    name = context.user_data.get("name", "بطل")
    # بشكل افتراضي نجعله غير مفعل حتى يفعله المالك (أو اجعله 1 للتجربة)
    database.add_user_db(chat_id, name=name, level=level, is_allowed=1) 
    
    await update.message.reply_text(f"تم الإعداد بنجاح يا {name}! 🚀\nتقدر دلوقتي تستخدم القائمة تحت عشان تنظم يومك.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    user = database.get_user(user_id)
    
    if not user or user['is_allowed'] == 0:
        await update.message.reply_text("⛔ ميزة محصورة للمشتركين فقط.")
        return

    # المسارات المحددة (الأزرار)
    if text == "🎯 أهدافي اليومية":
        await update.message.reply_text("📝 اكتب أهدافك للنهارده في رسالة واحدة، وأنا هسجلها عندي عشان نتابعها بكرة!")
    
    elif text == "📊 تقييم أدائي":
        await update.message.reply_text("📉 من 1 لـ 10، قيم إنتاجيتك النهارده؟ وإيه أكتر حاجة عطلتك؟")
    
    elif text == "🔥 الـ Streak الخاص بي":
        await update.message.reply_text(f"🔥 الالتزام: {user['streak']} يوم متتالي!\n💰 رصيد نقاطك: {user['points']} نقطة.\nاستمر يا بطل! 💪")
    
    elif text == "🏆 لوحة المتصدرين":
        top = database.get_leaderboard()
        msg = "🏆 *أبطال المنظمة لهذا الأسبوع:*\n\n"
        for i, (name, pts) in enumerate(top, 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
            msg += f"{medal} {name} — {pts} نقطة\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    
    elif text == "💡 نصيحة سريعة":
        await update.message.chat.send_action("typing")
        res = ask_claude("اديني نصيحة إنتاجية عملية ومختصرة جداً", user['name'])
        await update.message.reply_text(f"💡 *نصيحة قاوم:*\n{res}", parse_mode="Markdown")
    
    elif text == "🤖 اسأل قاوم (AI)":
        await update.message.reply_text("🤖 أنا معاك! اسألني أي سؤال عن تنظيم الوقت أو الإنتاجية وهرد عليك فوراً.")
        context.user_data['waiting_for_ai'] = True
    
    elif text == "⚙️ الإعدادات":
        await update.message.reply_text("⚙️ قريباً: تعديل التذكيرات، تغيير الاسم، وإدارة الحساب.")

    # التدخل الذكي (عند الطلب فقط)
    elif context.user_data.get('waiting_for_ai'):
        await update.message.chat.send_action("typing")
        res = ask_claude(text, user['name'], f"مستوى: {user['level']}, نقاط: {user['points']}")
        await update.message.reply_text(res)
        context.user_data['waiting_for_ai'] = False # نعود للمسار الطبيعي بعد الرد
    
    else:
        await update.message.reply_text("اختار من القائمة تحت عشان أقدر أساعدك بشكل أفضل! 👇", reply_markup=main_menu_keyboard())

def main():
    if not TOKEN: return
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_level)]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    database.init_db()
    main()
