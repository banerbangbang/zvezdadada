import datetime
import os
from database import user_data, referral_data, used_promo_codes, get_referral_count

STATS_FILE = "beautiful_stats.txt"

def update_beautiful_stats():
    """Обновить красивую статистику в файле"""
    
    try:
        print("🔍 Начинаем сбор статистики...")
        
        # ПЕРЕСЧИТЫВАЕМ ВСЕ ДАННЫЕ ЗАНОВО
        total_users = len(user_data)
        print(f"📊 Всего пользователей в user_data: {total_users}")
        
        # Активные пользователи (звёзды > 0)
        active_users = []
        total_stars = 0
        
        for user_id, data in user_data.items():
            stars = data.get('stars', 0)
            total_stars += stars
            if stars > 0:
                active_users.append((user_id, data))
        
        # ИСПРАВЛЕНО: используем round для избежания погрешностей
        total_clicks = int(round(total_stars / 0.1))
        
        # ПРАВИЛЬНЫЙ подсчет рефералов
        print("🔍 Считаем рефералов...")
        total_referrals = 0
        real_referral_stats = []
        
        for user_id, data in user_data.items():
            referral_count = get_referral_count(user_id)  # Используем функцию из database
            total_referrals += referral_count
            
            username = data.get('username', f"User_{user_id}")[:15]
            stars = data.get('stars', 0)
            # ИСПРАВЛЕНО: используем round для избежания погрешностей
            user_clicks = int(round(stars / 0.1))
            real_referral_stats.append((username, referral_count, user_clicks, stars, user_id))
        
        print(f"📊 Всего рефералов: {total_referrals}")
        
        # Сортируем по количеству рефералов (убывание)
        real_referral_stats.sort(key=lambda x: x[1], reverse=True)
        
        stats_text = f"""
╔══════════════════════════════════════════════════════════╗
║                   📊 СТАТИСТИКА БОТА                    ║
╠══════════════════════════════════════════════════════════╣
║ 🕐 Последнее обновление: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
║
║ 📈 ОБЩАЯ СТАТИСТИКА:
║   👥 Всего пользователей: {total_users}
║   🔥 Активных: {len(active_users)}
║   ⭐ Всего звёзд в системе: {total_stars:.1f}
║   🔘 Всего нажатий: {total_clicks}
║   👥 Всего приглашено: {total_referrals}
║
║ 🎪 ТАБЛИЦА 1: АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ (звёзды > 0)
╠══════════════════════════════════════════════════════════╣
"""
        
        # Таблица 1: Активные пользователи (ВСЕ)
        active_users_sorted = []
        for user_id, data in active_users:
            username = data.get('username', f"User_{user_id}")[:20]
            stars = data.get('stars', 0)
            referrals = get_referral_count(user_id)
            used_promos = len(used_promo_codes.get(user_id, []))
            # ИСПРАВЛЕНО: используем round для избежания погрешностей
            user_clicks = int(round(stars / 0.1))
            
            active_users_sorted.append((username, stars, user_clicks, referrals, used_promos, user_id))
        
        # Сортируем по звездам (убывание)
        active_users_sorted.sort(key=lambda x: x[1], reverse=True)
        
        for i, (username, stars, clicks, referrals, used_promos, user_id) in enumerate(active_users_sorted, 1):
            stats_text += f"║ {i:3d}. {username:20} | ⭐ {stars:6.1f} | 🔘 {clicks:4d} | 👥 {referrals:2d} | 🎁 {used_promos:2d}\n"
        
        if not active_users_sorted:
            stats_text += "║           Нет активных пользователей\n"
        
        stats_text += """
╠══════════════════════════════════════════════════════════╣
║ 📊 ТАБЛИЦА 2: ВСЕ ПОЛЬЗОВАТЕЛИ
╠══════════════════════════════════════════════════════════╣
"""
        
        # Таблица 2: Все пользователи (ВСЕ)
        all_users_sorted = []
        for user_id, data in user_data.items():
            username = data.get('username', f"User_{user_id}")[:20]
            stars = data.get('stars', 0)
            # ИСПРАВЛЕНО: используем round для избежания погрешностей
            user_clicks = int(round(stars / 0.1))
            
            all_users_sorted.append((username, stars, user_clicks, user_id))
        
        # Сортируем по user_id (время регистрации)
        all_users_sorted.sort(key=lambda x: x[3])
        
        for i, (username, stars, clicks, user_id) in enumerate(all_users_sorted, 1):
            user_id_short = str(user_id)[:8] + "..." if len(str(user_id)) > 8 else str(user_id)
            stats_text += f"║ {i:4d}. {username:20} | ⭐ {stars:5.1f} | 🔘 {clicks:4d} | ID: {user_id_short}\n"
        
        stats_text += """
╠══════════════════════════════════════════════════════════╣
║ 🎯 ТАБЛИЦА 3: ВСЕ ПОЛЬЗОВАТЕЛИ ПО РЕФЕРАЛАМ
╠══════════════════════════════════════════════════════════╣
"""
        
        # Таблица 3: ВСЕ пользователи по рефералам (не только топ-50)
        for i, (username, ref_count, clicks, stars, user_id) in enumerate(real_referral_stats, 1):
            stats_text += f"║ {i:3d}. {username:15} | 👥 {ref_count:2d} | ⭐ {stars:5.1f} | 🔘 {clicks:4d}\n"
        
        if not real_referral_stats:
            stats_text += "║         Пока нет приглашений\n"
        
        # ИТОГИ
        stats_text += f"""
╠══════════════════════════════════════════════════════════╣
║ 📋 ИТОГИ:
║   👤 Всего пользователей: {total_users}
║   🔥 Активных: {len(active_users)}
║   💰 Всего звёзд: {total_stars:.1f}
║   🔘 Всего кликов: {total_clicks}
║   👥 Всего приглашено: {total_referrals}
║   📊 Всего в реферальной таблице: {len(real_referral_stats)}
╚══════════════════════════════════════════════════════════╝
"""
        
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            f.write(stats_text)
        
        print(f"✅ Статистика сохранена. Пользователей: {total_users}, Рефералов: {total_referrals}")
        return f"✅ Статистика обновлена! Пользователей: {total_users}, Рефералов: {total_referrals}"
    
    except Exception as e:
        print(f"❌ Ошибка статистики: {e}")
        return f"❌ Ошибка обновления статистики: {e}"

def get_beautiful_stats():
    """Получить красивую статистику из файла"""
    if not os.path.exists(STATS_FILE):
        return "Статистика пока не сгенерирована. Используйте /update_stats"
    
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return f.read()

def get_total_stats():
    """Получить общую статистику"""
    total_stars = sum(data.get('stars', 0) for data in user_data.values())
    # ИСПРАВЛЕНО: используем round для избежания погрешностей
    total_clicks = int(round(total_stars / 0.1))
    total_referrals = sum(get_referral_count(user_id) for user_id in user_data.keys())
    
    return {
        'total_users': len(user_data),
        'total_stars': total_stars,
        'total_clicks': total_clicks,
        'total_referrals': total_referrals
    }