import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ChatMemberHandler
)
import pyrogram
import config
import database as db
import utils
from handlers import start, buttons, messages, events, channel_monitor

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد Pyrogram Client (اختياري)
try:
    app_client = pyrogram.Client(
        "bot_account",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.TOKEN
    )
    pyrogram_available = True
except AttributeError:
    app_client = None
    pyrogram_available = False
    print("تنبيه: API_ID أو API_HASH غير موجودين في config.py.")

def main():
    db.Base.metadata.create_all(db.engine)
    
    application = Application.builder().token(config.TOKEN).build()

    # --- تسجيل المعالجات ---

    # 1. معالج الأوامر (مثل /start)
    application.add_handler(CommandHandler("start", start.start))

    # 2. معالج الأزرار (CallbackQuery)
    application.add_handler(CallbackQueryHandler(buttons.button_handler))
    
    # 3. معالج الرسائل في الخاص (تم التعديل هنا لقبول الملصقات)
    # أضفنا filters.Sticker.ALL لكي يقرأ الملصق
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & (filters.TEXT | filters.Document.MimeType("text/plain") | filters.Sticker.ALL), 
        messages.message_handler
    ))

    # 4. معالج كلمة "تفعيل" في المجموعات
    application.add_handler(MessageHandler(
        filters.Regex("^تفعيل$") & filters.ChatType.GROUPS, 
        messages.message_handler
    ))
    
    # 5. معالج مراقبة القنوات للملصق التفاعلي
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & (filters.TEXT | filters.PHOTO), 
        channel_monitor.channel_monitor
    ))

    # 6. أحداث العضوية (المغادرة)
    application.add_handler(
        ChatMemberHandler(events.chat_member_handler, ChatMemberHandler.CHAT_MEMBER)
    )

    # تشغيل النشر التلقائي
    job_queue = application.job_queue
    job_queue.run_repeating(utils.post_job, interval=60, first=10)

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    if hasattr(config, 'API_ID') and hasattr(config, 'API_HASH'):
        if config.API_ID and config.API_HASH:
            try:
                app_client.start()
            except Exception as e:
                print(f"Warning: Pyrogram failed to start: {e}")
    
    main()