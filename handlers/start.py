from telegram import Update
from telegram.ext import ContextTypes
import database as db
import config
from keyboards import get_dev_keyboard, get_admin_keyboard, get_user_keyboard
from utils import send_notification_to_admins

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    session = db.Session()
    user = session.query(db.User).filter_by(user_id=user_id).first()
    is_new_user = False
    if not user:
        user = db.User(user_id=user_id, username=username)
        session.add(user)
        session.commit()
        is_new_user = True
    else:
        if username != user.username:
            user.username = username
            session.commit()
    session.close()

    welcome_text = "أهلاً بك في بوت النشر التلقائي! 🤖"
    
    if is_new_user:
        user_tag = f"@{username}" if username else "بدون يوزر"
        msg = f"🔔 <b>تنبيه:</b> دخول شخص جديد.\n👤 الاسم: {user_tag}\n🆔 الآيدي: <code>{user_id}</code>"
        await send_notification_to_admins(context, msg)

    if user_id == config.DEVELOPER_ID:
        await update.message.reply_text(welcome_text + "\n\n🔹 <b>لوحة المطور</b> 🔹", reply_markup=get_dev_keyboard(), parse_mode='HTML')
    elif db.is_admin(user_id):
        await update.message.reply_text(welcome_text + "\n\n🔹 <b>لوحة المشرف</b> 🔹", reply_markup=get_admin_keyboard(), parse_mode='HTML')
    else:
        await update.message.reply_text(welcome_text + "\n\n🔹 <b>القائمة الرئيسية</b> 🔹", reply_markup=get_user_keyboard(), parse_mode='HTML')
