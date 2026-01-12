import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import config
from keyboards import get_back_keyboard

logger = logging.getLogger(__name__)

async def is_user_admin_in_channel(bot, user_id, channel_id):
    try:
        chat_member = await bot.get_chat_member(channel_id, bot.id)
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def send_notification_to_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    session = db.Session()
    admins = session.query(db.User).filter_by(is_admin=True).all()
    for admin in admins:
        try:
            await context.bot.send_message(chat_id=admin.user_id, text=message, parse_mode='HTML')
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin.user_id}: {e}")
    
    try:
        await context.bot.send_message(chat_id=config.DEVELOPER_ID, text=message, parse_mode='HTML')
    except Exception as e:
        logger.warning(f"Failed to notify dev: {e}")
    session.close()

async def post_job(context: ContextTypes.DEFAULT_TYPE, force_one=False):
    session = db.Session()
    setting = session.query(db.BotSettings).filter_by(key='posting_status').first()
    
    print(f"--- Job Check --- Status: {setting.value if setting else 'None'}, Force: {force_one}")

    if not force_one and (not setting or setting.value == 'off'):
        session.close()
        return

    channels = session.query(db.Channel).filter_by(is_active=True).all()
    session.close()
    print(f"Found {len(channels)} active channels.")

    if not channels:
        return

    now = datetime.now()
    
    for channel in channels:
        try:
            should_post = False
            reason = ""
            
            if force_one:
                should_post = True
                reason = "Force Post"
            elif channel.time_type == 'default':
                import random
                if random.random() < 0.05:
                    should_post = True
                    reason = "Random Post (5%)"
            
            elif channel.time_type == 'fixed':
                if channel.time_value:
                    allowed_hours = [int(h.strip()) for h in channel.time_value.split(',')]
                    current_hour = now.hour
                    if current_hour in allowed_hours:
                         if channel.last_post_at:
                            last_hour = channel.last_post_at.hour
                            if last_hour != current_hour:
                                should_post = True
                                reason = f"Fixed Time {current_hour}"
                         else:
                             should_post = True

            elif channel.time_type == 'interval':
                if channel.time_value and channel.last_post_at:
                    interval_minutes = int(channel.time_value)
                    diff = now - channel.last_post_at
                    if diff.total_seconds() >= (interval_minutes * 60):
                        should_post = True
                        reason = "Interval Passed"
                elif not channel.last_post_at:
                    should_post = True

            if should_post:
                text = db.get_next_content(channel.category)
                if not text:
                    continue

                parse_mode = 'HTML' if channel.msg_format == 'blockquote' else None
                if channel.msg_format == 'blockquote':
                    text = f"<blockquote>{text}</blockquote>"

                # إرسال الاقتباس
                sent_message = await context.bot.send_message(
                    chat_id=channel.channel_id,
                    text=text,
                    parse_mode=parse_mode
                )
                
                # --- منطق الملصق التفاعلي للبوت (الحل الجديد) ---
                # نحن نفتح جلسة جديدة للتعامل مع الملصق لضمان الحساب الصحيح
                sticker_session = db.Session()
                try:
                    db_channel = sticker_session.query(db.Channel).filter_by(id=channel.id).first()
                    
                    # التأكد من تفعيل خاصية الملصق
                    if db_channel.sticker_interval and db_channel.sticker_file_id:
                        # زيادة العداد لأننا نشرنا رسالة (حتى لو كانت من البوت)
                        db_channel.msg_counter += 1
                        sticker_session.commit()
                        
                        # التحقق هل حان وقت النشر؟
                        if db_channel.msg_counter >= db_channel.sticker_interval:
                            try:
                                # إرسال الملصق كرد على الرسالة المنشورة للتو
                                await context.bot.send_sticker(
                                    chat_id=channel.channel_id,
                                    sticker=db_channel.sticker_file_id,
                                    reply_to_message_id=sent_message.message_id
                                )
                                
                                # تصفير العداد (رسالة الملصق نفسها لا تدخل في الحساب لأننا صفرنا بعدها)
                                db_channel.msg_counter = 0
                                sticker_session.commit()
                                logger.info(f"Sticker sent via post_job to {db_channel.title}")
                            except Exception as e:
                                logger.error(f"Error sending sticker: {e}")
                finally:
                    sticker_session.close()
                
                # --- نهاية منطق الملصق ---

                session = db.Session()
                db_channel = session.query(db.Channel).filter_by(id=channel.id).first()
                if db_channel:
                    db_channel.last_post_at = now
                    session.commit()
                session.close()
                
                if force_one:
                    return
                await asyncio.sleep(1) 

        except Exception as e:
            print(f"ERROR in {channel.title}: {e}")

async def finalize_channel_addition(update, context, query, role):
    pending = context.user_data.get('pending_channel')
    if not pending: return
    
    cat = context.user_data.get('selected_category')
    fmt = context.user_data.get('selected_format', 'normal')
    time_conf = context.user_data.get('time_settings', {'type': 'default'})
    time_type = time_conf.get('type', 'default')
    time_value = time_conf.get('value')

    db.add_channel(pending['id'], pending['title'], update.effective_user.id, cat, fmt, time_type, time_value)
    
    context.user_data['pending_channel'] = None
    context.user_data['selected_category'] = None
    context.user_data['time_settings'] = None
    
    time_text = ""
    if time_type == 'fixed':
        time_text = f"⏰ الساعات: {time_value}"
    elif time_type == 'interval':
        time_text = f"⏳ كل: {time_value} دقيقة"
    else:
        time_text = "🚀 فوري/عشوائي"
        
    msg = f"✅ تمت إضافة القناة بنجاح!\n📂 القسم: <b>{cat}</b>\n📝 الشكل: {fmt}\n⏱️ الوقت: {time_text}"
    
    if query:
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
    else:
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))