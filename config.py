import os 
import random

# Базовые настройки
BOT_TOKEN = None
CHANNEL_ID = -1003270368878
MIN_STARS_FOR_WITHDRAW = 500
ADMIN_IDS = [5408585719]  # Можно добавить больше админов через запятую

# Реферальная система
INITIAL_REFERRALS_NEEDED = 3
REFERRAL_TYPES = {
    "quest": {
        "name": "Для задания '3 друга'",
        "reward": 100,
        "target": 3,
        "description": "Пригласите 3 друзей по этой ссылке для получения 100 звезд"
    },
    "security": {
        "name": "Для проверки безопасности", 
        "description": "Приглашайте друзей для проверки что вы не бот"
    }
}

# Каналы для рекламы (ИСПРАВЛЕНО: убраны дубликаты)
ADVERTISEMENT_CHANNELS = [
    "https://t.me/reklamacanals",
    "https://t.me/razmeshenie_reklamy"
]

def get_random_referral_stage():
    """Получить случайное число от 1 до 3 (раньше было до 4)"""
    return random.randint(1, 3)  # ИЗМЕНЕНИЕ: было (1, 4)

# Мини-игры (без изменений)
MINI_GAMES = {
    "dice": {
        "name": "🎲 Кости",
        "min_bet": 5,
        "max_bet": 50,
        "description": "Брось кости! Выиграй x2 или проиграй",
        "win_multiplier": 2
    },
    "coin": {
        "name": "🪙 Монетка", 
        "min_bet": 3,
        "max_bet": 50,
        "description": "Выбери орла или решку! Угадай и забери x2!",
        "win_multiplier": 2
    },
    "slots": {
        "name": "🎰 Слоты",
        "min_bet": 10,
        "max_bet": 50,
        "description": "Крути слоты! 3 одинаковых = ДЖЕКПОТ x5!",
        "win_multiplier": 5
    },
    "number": {
        "name": "🔢 Угадай число",
        "min_bet": 5,
        "max_bet": 50,
        "description": "Угадай число от 1 до 5! Выигрыш x3!",
        "win_multiplier": 3
    }
}

WIN_PROBABILITY = 0.25

# Промокоды (ИСПРАВЛЕНО: GIFT35 был 600, теперь 35)
PROMO_CODES = {
    "STAR20": 20, "BONUS30": 30, "GIFT20": 20, "MEGA45": 45, "SUPER50": 50,
    "FREE25": 25, "LUCKY35": 35, "WIN40": 40, "BONUS25": 25, "STAR30": 30,
    "GIFT35": 35, "MEGA50": 50, "SUPER40": 40, "GOLD45": 45, "SILVER30": 30,
    "VIP55": 55, "PREMIUM60": 60, "EXTRA35": 35, "PLUS40": 40, "MAX50": 50,
    "ULTRA45": 45, "PRO55": 55, "ELITE60": 60, "TOP50": 50, "BEST45": 45,
    "SPECIAL40": 40, "EXCLUSIVE55": 55
}

# Квесты (без изменений)
QUESTS = {
    "invite_3_friends": {
        "name": "👥 Пригласи 3 друзей",
        "reward": 100,
        "target": 3,
        "description": "Пригласи 3 друзей по специальной ссылке для задания"
    }
}