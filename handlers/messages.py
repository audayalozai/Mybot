import asyncio
from telegram import Update
from telegram.ext import ContextTypes, filters
import database as db
import config
from keyboards import get_back_keyboard, get_categories_keyboard
from utils import is_user_admin_in_channel, finalize_channel_addition

async def broadcast_task(context, text):
    success_count = 0
    session = db.Session()
    users = session.query(db.User).all()
    channels = session.query(db.Channel).all()
    session.close()

    for u in users:
        try:
            await context.bot.send_message(chat_id=u.user_id, text=text)
            success_count += 1
            await asyncio.sleep(0.05) 
        except Exception:
            pass
            
    for c in channels:
        try:
            await context.bot.send_message(chat_id=c.channel_id, text=text)
            success_count += 1
        except Exception:
            pass
    
    print(f"Broadcast finished. Sent to {success_count} chats.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    # --- تعريف المتغيرات الأساسية في البداية (لإصلاح مشكلة الـ role) ---
    user_id = update.effective_user.id
    text = update.message.text
    document = update.message.document
    
    if user_id == config.DEVELOPER_ID: role = "dev"
    elif db.is_admin(user_id): role = "admin"
    else: role = "user"
    
    forward_from = None
    if hasattr(update.message, 'forward_from_chat'):
        forward_from = update.message.forward_from_chat

    # --- منطق إعداد الملصق التفاعلي (الآن يمكنه استخدام role) ---
    if context.user_data.get('action') == 'waiting_sticker':
        # التأكد من وجود الملصق
        if not update.message.sticker:
            await update.message.reply_text("❌ يرجى إرسال ملصق صحيح فقط.")
            return
        
        context.user_data['temp_sticker_id'] = update.message.sticker.file_id
        context.user_data['action'] = 'waiting_sticker_interval'
        await update.message.reply_text("✅ تم حفظ الملصق.\n\nالآن أرسل الرقم: (بعد كل كم رسالة يتم النشر؟)\nمثلاً: 10", reply_markup=get_back_keyboard(role))
        return

    if context.user_data.get('action') == 'waiting_sticker_interval':
        try:
            interval = int(text.strip())
            if interval < 1: raise ValueError
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح أكبر من صفر.", reply_markup=get_back_keyboard(role))
            return
        
        context.user_data['temp_sticker_interval'] = interval
        context.user_data['action'] = 'waiting_sticker_sender'
        await update.message.reply_text("✅ تم حفظ العدد.\n\nالآن أرسل آيدي الشخص الذي سيرسل الملصق (لأن ينشر كأنه شخص وليس بوت).\nأو اكتب 0 ليرسله البوت نفسه.", reply_markup=get_back_keyboard(role))
        return

    if context.user_data.get('action') == 'waiting_sticker_sender':
        sender_id = None
        try:
            val = int(text.strip())
            if val != 0:
                sender_id = val
        except:
            sender_id = None 

        ch_id = context.user_data.get('editing_channel_id')
        if not ch_id:
            context.user_data['action'] = None
            return

        session = db.Session()
        try:
            ch = session.query(db.Channel).filter_by(id=ch_id).first()
            if ch:
                ch.sticker_file_id = context.user_data.get('temp_sticker_id')
                ch.sticker_interval = context.user_data.get('temp_sticker_interval')
                ch.sticker_sender_id = sender_id
                ch.msg_counter = 0
                session.commit()
                
                sender_txt = "البوت" if not sender_id else f"الشخص: {sender_id}"
                msg = f"✅ تم تفعيل الملصق التفاعلي بنجاح!\n\n⭐ الملصق: تم التعيين\n🔢 العدد: كل {ch.sticker_interval} رسالة\n👤 المرسل: {sender_txt}"
            else:
                msg = "❌ حدث خطأ."
        except Exception as e:
            session.rollback()
            print(f"Error saving sticker settings: {e}")
            msg = "❌ حدث خطأ أثناء الحفظ."
        finally:
            session.close()
        
        context.user_data.pop('temp_sticker_id', None)
        context.user_data.pop('temp_sticker_interval', None)
        context.user_data['action'] = None
        
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
        return

    # --- إضافة/حذف مشرف ---
    if context.user_data.get('action') == 'add_admin':
        target = text.strip().replace("@", "")
        session = db.Session()
        try:
            user = session.query(db.User).filter((db.User.username == target) | (db.User.user_id == str(target))).first()
            if user:
                user.is_admin = True
                session.commit()
                msg = f"✅ تم رفع @{user.username} مشرفاً بنجاح."
            else:
                msg = "❌ المستخدم غير موجود في قاعدة بيانات البوت."
        except Exception as e:
            session.rollback()
            msg = "❌ حدث خطأ."
        finally:
            session.close()
        
        context.user_data['action'] = None
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
        return

    if context.user_data.get('action') == 'del_admin':
        target = text.strip().replace("@", "")
        session = db.Session()
        try:
            user = session.query(db.User).filter((db.User.username == target) | (db.User.user_id == str(target))).first()
            if user and user.user_id != config.DEVELOPER_ID:
                user.is_admin = False
                session.commit()
                msg = f"✅ تم إزالة صلاحية المشرف من @{user.username}."
            else:
                msg = "❌ حدث خطأ أو تحاول حذف المطور."
        except Exception as e:
            session.rollback()
            msg = "❌ حدث خطأ."
        finally:
            session.close()
            
        context.user_data['action'] = None
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
        return

    # رفع الملفات
    if document and context.user_data.get('upload_category'):
        category = context.user_data['upload_category']
        if document.mime_type == "text/plain":
            file = await document.get_file()
            content_bytes = await file.download_as_bytearray()
            content_text = content_bytes.decode('utf-8').splitlines()
            content_list = [line for line in content_text if line.strip()]
            
            count = db.add_file_content(category, content_list)
            msg = f"✅ تمت إضافة <b>{count}</b> اقتباس لقسم <b>{category}</b> بنجاح."
            context.user_data['upload_category'] = None
        else:
            msg = "❌ يرجى رفع ملف بصيغة .txt فقط."
        
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
        return

    # إضافة قناة
    if context.user_data.get('step') == 'waiting_channel':
        channel_id = None
        title = ""
        
        if forward_from:
            channel_id = forward_from.id
            title = forward_from.title
        elif text and (text.startswith("@") or text.startswith("-100")):
            try:
                chat = await context.bot.get_chat(text)
                channel_id = chat.id
                title = chat.title
            except:
                msg = "❌ تعذر الوصول للقناة. تأكد من المعرف وأن البوت مشرف."
                await update.message.reply_text(msg, reply_markup=get_back_keyboard(role))
                return
        else:
            return

        is_bot_admin = await is_user_admin_in_channel(context.bot, user_id, channel_id)
        
        if not is_bot_admin:
            msg = f"⛔️ <b>تنبيه:</b> أنا لست مشرفاً في القناة [<b>{title}</b>].\n\nيرجى رفعي مشرفاً ثم إعادة المحاولة."
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
            return

        context.user_data['pending_channel'] = {'id': channel_id, 'title': title}
        context.user_data['step'] = None
        msg = f"✅ تم التحقق من القناة: <b>{title}</b>\n\nالآن اختر نوع الاقتباسات لهذه القناة:"
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_categories_keyboard())
        return

    # --- إعدادات الوقت ---
    if context.user_data.get('action') == 'set_fixed_time':
        time_input = text.strip()
        
        if context.user_data.get('mode') == 'edit':
            ch_id = context.user_data.get('editing_channel_id')
            session = db.Session()
            try:
                ch = session.query(db.Channel).filter_by(id=ch_id).first()
                if ch:
                    ch.time_type = 'fixed'
                    ch.time_value = time_input
                    session.commit()
                    msg = f"✅ تم تحديث وقت القناة <b>{ch.title}</b>\n🕒 الساعات: {time_input}"
                else:
                    msg = "❌ خطأ في العثور على القناة."
            except Exception as e:
                session.rollback()
                print(f"Error updating fixed time: {e}")
                msg = "❌ حدث خطأ أثناء التحديث."
            finally:
                session.close()
                context.user_data['action'] = None
                context.user_data['mode'] = None
                await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
        else:
            try:
                context.user_data['time_settings'] = {'type': 'fixed', 'value': time_input}
                await finalize_channel_addition(update, context, None, role)
            except Exception as e:
                print(f"Error adding fixed time: {e}")
                await update.message.reply_text("❌ حدث خطأ أثناء حفظ الإعدادات.", reply_markup=get_back_keyboard(role))
        return

    if context.user_data.get('action') == 'set_interval':
        try:
            val = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح للدقائق.", reply_markup=get_back_keyboard(role))
            return
            
        if context.user_data.get('mode') == 'edit':
            ch_id = context.user_data.get('editing_channel_id')
            session = db.Session()
            try:
                ch = session.query(db.Channel).filter_by(id=ch_id).first()
                if ch:
                    ch.time_type = 'interval'
                    ch.time_value = str(val)
                    session.commit()
                    msg = f"✅ تم تحديث وقت القناة <b>{ch.title}</b>\n⏳ كل: {val} دقيقة"
                else:
                    msg = "❌ خطأ في العثور على القناة."
            except Exception as e:
                session.rollback()
                print(f"Error updating interval: {e}")
                msg = "❌ حدث خطأ أثناء التحديث."
            finally:
                session.close()
                context.user_data['action'] = None
                context.user_data['mode'] = None
                await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_back_keyboard(role))
        else:
            try:
                context.user_data['time_settings'] = {'type': 'interval', 'value': str(val)}
                await finalize_channel_addition(update, context, None, role)
            except Exception as e:
                print(f"Error adding interval: {e}")
                await update.message.reply_text("❌ حدث خطأ أثناء حفظ الإعدادات.", reply_markup=get_back_keyboard(role))
        return

    # إذاعة
    if context.user_data.get('action') == 'waiting_broadcast':
        msg_to_send = update.message.text or update.message.caption
        if not msg_to_send: return
        
        await update.message.reply_text("⏳ جاري إرسال الإذاعة، سيتم إعلامك عند الانتهاء...")
        asyncio.create_task(broadcast_task(context, msg_to_send))
        context.user_data['action'] = None
        return

    # تفعيل المجموعات
    if text == "تفعيل":
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        if chat_type in ['group', 'supergroup']:
            is_bot_admin = await is_user_admin_in_channel(context.bot, user_id, chat_id)
            if not is_bot_admin:
                await update.message.reply_text("يجب أن أكون مشرفاً في المجموعة للتفعيل.")
                return
            
            db.add_channel(chat_id, update.effective_chat.title, user_id, "اقتباسات عامة", "normal")
            await update.message.reply_text("✅ تم تفعيل البوت في المجموعة بنجاح!")