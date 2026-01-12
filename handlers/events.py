import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import database as db
from utils import send_notification_to_admins

async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.old_chat_member.status in ['administrator', 'member'] and \
       result.new_chat_member.status in ['left', 'kicked']:
        
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title
        
        asyncio.create_task(send_notification_to_admins(context, f"⚠️ تم حذف البوت من <b>{chat_title}</b>"))
        db.remove_channel_db(chat_id)