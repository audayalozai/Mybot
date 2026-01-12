from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import random

# إعداد قاعدة البيانات
engine = create_engine('sqlite:///bot_database.db', echo=False)
Base = declarative_base()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# --- تعريف الجداول ---

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, unique=True, nullable=False)
    title = Column(String, nullable=False)
    added_by = Column(Integer, nullable=True)
    category = Column(String, default="اقتباسات عامة")
    msg_format = Column(String, default="normal") 
    time_type = Column(String, default="default") 
    time_value = Column(String, nullable=True) 
    last_post_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # --- خصائص الملصق التفاعلي ---
    sticker_file_id = Column(String, nullable=True)
    sticker_interval = Column(Integer, nullable=True)
    msg_counter = Column(Integer, default=0)
    sticker_sender_id = Column(Integer, nullable=True)

class BotSettings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(String)

class FileContent(Base):
    __tablename__ = 'files_content'
    id = Column(Integer, primary_key=True)
    category = Column(String)
    content = Column(Text)

# إنشاء الجداول
Base.metadata.create_all(engine)

# --- دوال مساعدة ---

def is_admin(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    session.close()
    return user.is_admin if user else False

def add_channel(ch_id, title, added_by, cat, fmt, t_type='default', t_val=None):
    session = Session()
    try:
        new_ch = Channel(channel_id=ch_id, title=title, added_by=added_by, 
                         category=cat, msg_format=fmt, time_type=t_type, time_value=t_val)
        session.add(new_ch)
        session.commit()
    finally:
        session.close()

def remove_channel_db(ch_id):
    session = Session()
    try:
        ch = session.query(Channel).filter_by(channel_id=ch_id).first()
        if ch:
            session.delete(ch)
            session.commit()
    except:
        pass
    finally:
        session.close()

def add_file_content(category, content_list):
    session = Session()
    count = 0
    try:
        for text in content_list:
            new_content = FileContent(category=category, content=text)
            session.add(new_content)
            count += 1
        session.commit()
    except Exception as e:
        print(f"Error adding content: {e}")
        session.rollback()
    finally:
        session.close()
    return count

def get_next_content(category):
    session = Session()
    try:
        content = session.query(FileContent).filter_by(category=category).order_by(FileContent.id).all()
        if content:
            selected = random.choice(content)
            return selected.content
        return None
    finally:
        session.close()

def get_stats():
    session = Session()
    try:
        users_count = session.query(User).count()
        channels_count = session.query(Channel).count()
        posts_count = session.query(FileContent).count()
        return (f"📊 <b>إحصائيات البوت:</b>\n"
                f"👥 المستخدمين: {users_count}\n"
                f"📢 القنوات: {channels_count}\n"
                f"📝 الرسائل المخزنة: {posts_count}")
    finally:
        session.close()