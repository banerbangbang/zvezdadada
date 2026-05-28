from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("⭐ Получить звёзды"), KeyboardButton("👤 Профиль")],
        [KeyboardButton("💎 Вывод звёзд"), KeyboardButton("📜 Правила")],
        [KeyboardButton("🎮 Мини-игры"), KeyboardButton("🎁 Промокоды")],
        [KeyboardButton("🎯 Задания"), KeyboardButton("📎 Реферальная ссылка")],
        [KeyboardButton("🏆 Топ пользователей"), KeyboardButton("📝 Отзывы")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def subscribe_keyboard():
    keyboard = [
        [KeyboardButton("📢 Подписаться на канал")],
        [KeyboardButton("✅ Проверить подписку")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def games_keyboard():
    keyboard = [
        [KeyboardButton("🎲 Кости"), KeyboardButton("🪙 Монетка")],
        [KeyboardButton("🎰 Слоты"), KeyboardButton("🔢 Угадай число")],
        [KeyboardButton("📊 Статистика игр"), KeyboardButton("⬅️ В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def play_again_keyboard():
    keyboard = [
        [KeyboardButton("🔄 Играть еще"), KeyboardButton("⬅️ В игры")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def coin_choice_keyboard():
    keyboard = [
        [KeyboardButton("🦅 Орел"), KeyboardButton("👑 Решка")],
        [KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def number_choice_keyboard():
    keyboard = [
        [KeyboardButton("1️⃣"), KeyboardButton("2️⃣"), KeyboardButton("3️⃣")],
        [KeyboardButton("4️⃣"), KeyboardButton("5️⃣")],
        [KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def referral_inline_keyboard(user_id):
    """Inline клавиатура ТОЛЬКО для задания (всегда показывается)"""
    keyboard = [
        [InlineKeyboardButton("🔗 Ссылка для задания (3 друга = 100⭐)", callback_data=f"ref_quest_{user_id}")],
        [InlineKeyboardButton("📢 Каналы для рекламы", url="https://t.me/reklamacanals")]
    ]
    return InlineKeyboardMarkup(keyboard)

def referral_with_security_inline_keyboard(user_id):
    """Inline клавиатура с ОБЕИМИ ссылками (только при 500+ звезд)"""
    keyboard = [
        [InlineKeyboardButton("🔗 Ссылка для задания (3 друга = 100⭐)", callback_data=f"ref_quest_{user_id}")],
        [InlineKeyboardButton("🔐 Ссылка для проверки безопасности", callback_data=f"ref_security_{user_id}")],
        [InlineKeyboardButton("📢 Каналы для рекламы", url="https://t.me/reklamacanals")]
    ]
    return InlineKeyboardMarkup(keyboard)

def withdrawal_inline_keyboard(user_id):
    """Inline клавиатура для вывода (с поддержкой)"""
    keyboard = [
        [InlineKeyboardButton("👤 Техподдержка", url="https://t.me/soobnieadmin_bot")],
        [InlineKeyboardButton("📢 Каналы для рекламы", url="https://t.me/reklamacanals")]
    ]
    return InlineKeyboardMarkup(keyboard)

def security_inline_keyboard(user_id):
    """Inline клавиатура только для проверки безопасности"""
    keyboard = [
        [InlineKeyboardButton("🔐 Получить ссылку для проверки", callback_data=f"ref_security_{user_id}")],
        [InlineKeyboardButton("📢 Каналы для рекламы", url="https://t.me/reklamacanals")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ДОБАВЛЕНА НЕДОСТАЮЩАЯ ФУНКЦИЯ
def quest_inline_keyboard(user_id):
    """Inline клавиатура для заданий"""
    keyboard = [
        [InlineKeyboardButton("🔗 Ссылка для задания (3 друга = 100⭐)", callback_data=f"ref_quest_{user_id}")],
        [InlineKeyboardButton("📢 Каналы для рекламы", url="https://t.me/reklamacanals")]
    ]
    return InlineKeyboardMarkup(keyboard)