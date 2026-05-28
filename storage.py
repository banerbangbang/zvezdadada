import os
import time
import json
import threading
from typing import Dict, Any
from functools import lru_cache

DATA_FILE = "user_data.json"
_auto_save_timer = None

# Глобальные переменные для данных (инициализируются в database.py)
user_data = {}
referral_data = {}
user_stages = {}
used_promo_codes = {}
user_quests = {}
games_stats = {}
banned_users = {}

def init_storage(database_module):
    """Инициализировать ссылки на данные из database.py (вызвать один раз при старте)"""
    global user_data, referral_data, user_stages, used_promo_codes, user_quests, games_stats, banned_users
    user_data = database_module.user_data
    referral_data = database_module.referral_data
    user_stages = database_module.user_stages
    used_promo_codes = database_module.used_promo_codes
    user_quests = database_module.user_quests
    games_stats = database_module.games_stats
    banned_users = database_module.banned_users
    print("✅ Storage инициализирован")

def save_data():
    """Сохранить все данные в файл (БЕЗ циклических импортов)"""
    try:
        data = {
            "user_data": user_data,
            "referral_data": referral_data, 
            "user_stages": user_stages,
            "used_promo_codes": used_promo_codes,
            "user_quests": user_quests,
            "games_stats": games_stats,
            "banned_users": banned_users
        }
        
        # Используем временный файл для безопасного сохранения
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Заменяем старый файл новым
        if os.path.exists(DATA_FILE):
            os.replace(temp_file, DATA_FILE)
        else:
            os.rename(temp_file, DATA_FILE)
            
        print(f"✅ Данные сохранены в {DATA_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")
        # Удаляем временный файл при ошибке
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def load_data():
    """Загрузить данные из файла"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Очищаем текущие данные перед загрузкой
            user_data.clear()
            referral_data.clear()
            user_stages.clear()
            used_promo_codes.clear()
            user_quests.clear()
            games_stats.clear()
            banned_users.clear()
            
            # Загружаем новые данные
            user_data.update({int(k): v for k, v in data.get("user_data", {}).items()})
            referral_data.update({int(k): v for k, v in data.get("referral_data", {}).items()})
            user_stages.update({int(k): v for k, v in data.get("user_stages", {}).items()})
            used_promo_codes.update({int(k): v for k, v in data.get("used_promo_codes", {}).items()})
            user_quests.update({int(k): v for k, v in data.get("user_quests", {}).items()})
            games_stats.update({int(k): v for k, v in data.get("games_stats", {}).items()})
            banned_users.update(data.get("banned_users", {}))
            
            print(f"✅ Данные загружены из {DATA_FILE}")
            return True
        else:
            print("ℹ️ Файл данных не найден, создаем новую БД")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return False

def auto_save():
    """Автоматическое сохранение данных (неблокирующее)"""
    def _save_async():
        save_data()
    
    # Запускаем в отдельном потоке чтобы не блокировать бота
    thread = threading.Thread(target=_save_async, daemon=True)
    thread.start()

# Оптимизированный кэш
class FastCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key, max_age=60):
        if key in self._cache:
            if time.time() - self._timestamps[key] < max_age:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key, value):
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def clear(self):
        self._cache.clear()
        self._timestamps.clear()

# Глобальный кэш
fast_cache = FastCache()

# Кэширование топ пользователей
@lru_cache(maxsize=1)
def get_cached_top_users(exclude_user_id):
    from database import get_top_users
    return get_top_users(limit=10, exclude_user_id=exclude_user_id)

# Очистка кэша при изменении данных
def clear_top_cache():
    get_cached_top_users.cache_clear()
