import time
from functools import lru_cache

# Кэш для частых запросов
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