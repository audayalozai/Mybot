import logging
from telegram import Update
from telegram.ext import ContextTypes, filters
import database as db

logger = logging.getLogger(__name__)

async def channel_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هذه الدالة تراقب الرسائل القادمة من القنوات فقط وتقوم بتحديث العداد وإرسال الملصق.
    """
    if not update.channel_post:
        return

    # التأكد من أن الرسالة نص أو صورة
    if update.channel_post.text or update.channel_post.photo:
        chat_id = update.effective_chat.id
        message_id = update.channel_post.message_id

        session = db.Session()
        try:
            channel = session.query(db.Channel).filter_by(channel_id=chat_id).first()
            
            # التأكد من وجود القناة وتفعيل خاصية الملصق التفاعلي
            if channel and channel.sticker_file_id and channel.sticker_interval:
                
                # 1. زيادة العداد
                channel.msg_counter += 1
                
                # 2. حفظ العداد في قاعدة البيانات فوراً (هذا هو الإصلاح)
                session.commit()
                
                # 3. التحقق هل حان وقت النشر؟
                if channel.msg_counter >= channel.sticker_interval:
                    sticker_sender_id = channel.sticker_sender_id
                    
                    try:
                        # محاولة إرسال الملصق
                        if sticker_sender_id:
                            # إذا كان هناك معرف مرسل، نرسل الملصق كرد
                            await context.bot.send_sticker(
                                chat_id=chat_id,
                                sticker=channel.sticker_file_id,
                                reply_to_message_id=message_id
                            )
                        else:
                            # افتراضي: البوت يرسل الملصق
                            await context.bot.send_sticker(
                                chat_id=chat_id,
                                sticker=channel.sticker_file_id,
                                reply_to_message_id=message_id
                            )
                        
                        # تصفير العداد بعد النشر
                        channel.msg_counter = 0
                        session.commit()
                        
                        logger.info(f"✅ Sticker sent to {channel.title}. Counter reset.")

                    except Exception as e:
                        logger.error(f"❌ Failed to send sticker in {channel.title}: {e}")

        except Exception as e:
            logger.error(f"Error in channel monitor: {e}")
        finally:
            session.close()