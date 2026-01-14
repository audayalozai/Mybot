from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_dev_keyboard():
    keyboard = [
        # القسم الأول: المحتوى والإدارة
        [InlineKeyboardButton("📂 إدارة الملفات", callback_data="manage_files")],
        [InlineKeyboardButton("🔧 إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("➕ إضافة قناة نشر", callback_data="add_channel_prompt")],
        
        # القسم الثاني: العرض والتنفيذ
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats")],
        [InlineKeyboardButton("🚀 نشر الآن (منشور واحد)", callback_data="post_now")],
        [InlineKeyboardButton("🔊 إرسال إذاعة", callback_data="broadcast_menu")],
        
        # القسم الثالث: الإعدادات المتقدمة
        [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="manage_admins")],
        [InlineKeyboardButton("⚙️ تفعيل/ايقاف النشر", callback_data="toggle_posting")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        # القسم الأول: المحتوى والإدارة
        [InlineKeyboardButton("📂 إدارة الملفات", callback_data="manage_files")],
        [InlineKeyboardButton("🔧 إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("➕ إضافة قناة نشر", callback_data="add_channel_prompt")],
        
        # القسم الثاني: العرض والتنفيذ
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats")],
        [InlineKeyboardButton("🚀 نشر الآن (منشور واحد)", callback_data="post_now")],
        [InlineKeyboardButton("🔊 إرسال إذاعة", callback_data="broadcast_menu")],
        
        # القسم الثالث: الإعدادات
        [InlineKeyboardButton("⚙️ تفعيل/ايقاف النشر", callback_data="toggle_posting")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة/مجموعة", callback_data="add_channel_prompt")],
        [InlineKeyboardButton("🔧 إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(role):
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"back_{role}")]]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard():
    keyboard = [
        [InlineKeyboardButton("❤️ حب", callback_data="cat_حب")],
        [InlineKeyboardButton("أذكار-آيات", callback_data="cat_عيد ميلاد")],
        [InlineKeyboardButton("💭 اقتباسات عامة", callback_data="cat_اقتباسات عامة")],
        [InlineKeyboardButton("📜 ابيات شعرية", callback_data="cat_ابيات شعرية")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_format_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 رسالة عادية", callback_data="fmt_normal")],
        [InlineKeyboardButton("💎 رسالة بشكل إقتباس", callback_data="fmt_blockquote")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_time_keyboard():
    keyboard = [
        [InlineKeyboardButton("⏰ ساعات محددة", callback_data="time_fixed")],
        [InlineKeyboardButton("⏳ فارق زمني (دقائق)", callback_data="time_interval")],
        [InlineKeyboardButton("🚫 افتراضي (عشوائي/فوري)", callback_data="time_default")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_files_keyboard():
    keyboard = [
        [InlineKeyboardButton("❤️ حب", callback_data="upload_حب")],
        [InlineKeyboardButton("أذكار-آيات", callback_data="upload_عيد ميلاد")],
        [InlineKeyboardButton("💭 اقتباسات عامة", callback_data="upload_اقتباسات عامة")],
        [InlineKeyboardButton("📜 ابيات شعرية", callback_data="upload_ابيات شعرية")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard_edit(context):
    ch_id = context.user_data.get('editing_channel_id')
    keyboard = [
        [InlineKeyboardButton("❤️ حب", callback_data="set_edit_cat_حب")],
        [InlineKeyboardButton("أذكار-آيات", callback_data="set_edit_cat_عيد ميلاد")],
        [InlineKeyboardButton("💭 اقتباسات عامة", callback_data="set_edit_cat_اقتباسات عامة")],
        [InlineKeyboardButton("📜 ابيات شعرية", callback_data="set_edit_cat_ابيات شعرية")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"edit_channel_{ch_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_format_keyboard_edit(context):
    ch_id = context.user_data.get('editing_channel_id')
    keyboard = [
        [InlineKeyboardButton("📝 رسالة عادية", callback_data="set_edit_fmt_normal")],
        [InlineKeyboardButton("💎 Blockquote", callback_data="set_edit_fmt_blockquote")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"edit_channel_{ch_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
