import logging
from telegram import Update
from telegram.ext import ContextTypes, filters
import database as db

logger = logging.getLogger(__name__)

async def channel_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هذه الدالة تراقب الرسائل القادمة من القنوات فقط.
    """
    if not update.channel_post:
        return

    # الفلتر في main.py يضمن أننا هنا فقط في حالة وجود نص أو صورة
    if update.channel_post.text or update.channel_post.photo:
        chat_id = update.effective_chat.id

        session = db.Session()
        try:
            channel = session.query(db.Channel).filter_by(channel_id=chat_id).first()
            
            # التأكد من وجود القناة وتفعيل خاصية الملصق التفاعلي
            if channel and channel.sticker_file_id and channel.sticker_interval:
                
                # زيادة العداد
                channel.msg_counter += 1
                
                # حفظ العداد
                session.commit()
                
                # التحقق هل حان وقت النشر؟
                if channel.msg_counter >= channel.sticker_interval:
                    sticker_sender_id = channel.sticker_sender_id
                    
                    try:
                        # إرسال الملصق كرسالة جديدة مستقلة (بدون reply_to_message_id)
                        # سواء كان الهدف مرسلاً محدداً أم البوت، سنرسله بشكل مستقل
                        await context.bot.send_sticker(
                            chat_id=chat_id,
                            sticker=channel.sticker_file_id
                            # لاحظ حذف: reply_to_message_id=...
                        )
                        
                        # تصفير العداد بعد النشر
                        channel.msg_counter = 0
                        session.commit()
                        
                        logger.info(f"✅ Sticker sent to {channel.title} (Standalone).")

                    except Exception as e:
                        logger.error(f"❌ Failed to send sticker in {channel.title}: {e}")

        except Exception as e:
            logger.error(f"Error in channel monitor: {e}")
        finally:
            session.close()
