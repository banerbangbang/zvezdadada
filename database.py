import sqlite3
import json
import os
import random
import threading
import time
from datetime import datetime

# Имя файла базы данных
DB_FILE = "bot_database.db"
JSON_FILE = "user_data(2).json"

# --- СООБЩЕНИЯ ДЛЯ ПРОВЕРКИ БЕЗОПАСНОСТИ ---
SECURITY_MESSAGES = {
    3: [
        "🚫 *НЕ УДАЛОСЬ ПРОВЕРИТЬ, ЧТО ВЫ НЕ БОТ!*\n\nПригласите *3 друзей* для верификации.",
        "🤖 *ОБНАРУЖЕНА ПОДОЗРИТЕЛЬНАЯ АКТИВНОСТЬ!*\n\nПригласите *3 реальных пользователей*.",
        "⚠️ *ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ!*\n\nПригласите *3 друзей* по ссылке ниже."
    ],
    2: [
        "🔍 *СНОВА НЕ УДАЛОСЬ ПРОВЕРИТЬ!*\n\nПригласите *2 друзей* для продолжения.",
        "🛡️ *ЗАЩИТА ОТ НАКРУТКИ!*\n\nПригласите *2 человека*.",
        "🎭 *ПРОВЕРКА НЕ ПРОЙДЕНА!*\n\nПригласите *2 друзей*."
    ],
    1: [
        "📢 *ОПЯТЬ ПРОВАЛ!*\n\nПригласите *1 друга*.",
        "🔒 *ПОСЛЕДНЯЯ ПОПЫТКА!*\n\nПригласите *1 пользователя*.",
        "⚡ *СРОЧНАЯ ПРОВЕРКА!*\n\nПригласите *1 друга*."
    ]
}

# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================

def init_database():
    """Создает все таблицы, если их нет"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        stars REAL DEFAULT 0,
        username TEXT,
        security_target INTEGER DEFAULT 3,
        security_progress INTEGER DEFAULT 0,
        registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица рефералов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referral_id INTEGER UNIQUE,
        type TEXT DEFAULT 'quest',
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица использованных промокодов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS used_promocodes (
        user_id INTEGER,
        promo_code TEXT,
        used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, promo_code)
    )
    ''')
    
    # Таблица выполненных заданий
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_quests (
        user_id INTEGER,
        quest_id TEXT,
        completed BOOLEAN DEFAULT 1,
        completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, quest_id)
    )
    ''')
    
    # Таблица статистики игр
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games_stats (
        user_id INTEGER PRIMARY KEY,
        games_played INTEGER DEFAULT 0,
        total_bet INTEGER DEFAULT 0,
        total_win INTEGER DEFAULT 0
    )
    ''')
    
    # Таблица забаненных пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_by INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # СОЗДАЕМ ИНДЕКСЫ для ускорения запросов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_type ON referrals(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_stars ON users(stars DESC)')
    
    conn.commit()
    conn.close()
    
    # Проверяем, нужно ли перенести данные из JSON
    check_and_migrate()

def check_and_migrate():
    """Переносит данные ТОЛЬКО если база пустая и JSON существует"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        if os.path.exists(JSON_FILE):
            print(f"🔄 База пустая, переносим данные из {JSON_FILE}...")
            migrate_from_json()
        else:
            print(f"ℹ️ Файл {JSON_FILE} не найден, создаем новую БД")
    else:
        print(f"✅ В БД уже есть {count} пользователей, пропускаем миграцию")

def migrate_from_json():
    """Переносит данные из JSON в SQLite"""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Переносим пользователей
        users_count = 0
        for user_id_str, user_info in data.get("user_data", {}).items():
            try:
                user_id = int(user_id_str)
                stars = user_info.get("stars", 0)
                username = user_info.get("username", f"User_{user_id}")
                security_target = user_info.get("security_target", 3)
                security_progress = user_info.get("security_progress", 0)
                
                cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, stars, username, security_target, security_progress)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, stars, username[:50], security_target, security_progress))
                users_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при переносе пользователя {user_id_str}: {e}")
        
        # Переносим рефералов
        referrals_count = 0
        for referrer_id_str, referrals in data.get("referral_data", {}).items():
            try:
                referrer_id = int(referrer_id_str)
                for ref in referrals:
                    if isinstance(ref, dict):
                        referral_id = ref.get("id")
                        ref_type = ref.get("type", "quest")
                    else:
                        referral_id = ref
                        ref_type = "quest"
                    
                    if referral_id:
                        try:
                            cursor.execute('''
                            INSERT OR IGNORE INTO referrals (referrer_id, referral_id, type, date)
                            VALUES (?, ?, ?, ?)
                            ''', (referrer_id, int(referral_id), ref_type, datetime.now().isoformat()))
                            referrals_count += 1
                        except Exception as e:
                            print(f"⚠️ Ошибка при добавлении реферала: {e}")
            except Exception as e:
                print(f"⚠️ Ошибка при обработке рефералов для {referrer_id_str}: {e}")
        
        # Переносим промокоды
        promos_count = 0
        for user_id_str, promos in data.get("used_promo_codes", {}).items():
            try:
                user_id = int(user_id_str)
                for promo in promos:
                    cursor.execute('''
                    INSERT OR IGNORE INTO used_promocodes (user_id, promo_code)
                    VALUES (?, ?)
                    ''', (user_id, promo))
                    promos_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при переносе промокодов для {user_id_str}: {e}")
        
        # Переносим задания
        quests_count = 0
        for user_id_str, quests in data.get("user_quests", {}).items():
            try:
                user_id = int(user_id_str)
                for quest_id, completed in quests.items():
                    if completed:
                        cursor.execute('''
                        INSERT OR IGNORE INTO user_quests (user_id, quest_id)
                        VALUES (?, ?)
                        ''', (user_id, quest_id))
                        quests_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при переносе заданий для {user_id_str}: {e}")
        
        # Переносим статистику игр
        games_count = 0
        for user_id_str, stats in data.get("games_stats", {}).items():
            try:
                user_id = int(user_id_str)
                games_played = stats.get("games_played", 0)
                total_bet = stats.get("total_bet", 0)
                total_win = stats.get("total_win", 0)
                
                cursor.execute('''
                INSERT OR REPLACE INTO games_stats (user_id, games_played, total_bet, total_win)
                VALUES (?, ?, ?, ?)
                ''', (user_id, games_played, total_bet, total_win))
                games_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при переносе статистики игр для {user_id_str}: {e}")
        
        # Переносим баны
        bans_count = 0
        for user_id_str, ban_info in data.get("banned_users", {}).items():
            try:
                user_id = int(user_id_str)
                reason = ban_info.get("reason", "")
                banned_by = ban_info.get("banned_by", 0)
                
                cursor.execute('''
                INSERT OR IGNORE INTO banned_users (user_id, reason, banned_by, date)
                VALUES (?, ?, ?, ?)
                ''', (user_id, reason, banned_by, datetime.now().isoformat()))
                bans_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при переносе банов для {user_id_str}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Миграция завершена:")
        print(f"   • Пользователей: {users_count}")
        print(f"   • Рефералов: {referrals_count}")
        print(f"   • Промокодов: {promos_count}")
        print(f"   • Заданий: {quests_count}")
        print(f"   • Статистики игр: {games_count}")
        print(f"   • Банов: {bans_count}")
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")

# ==================== АВТОСОХРАНЕНИЕ ====================

def auto_save_worker():
    """Фоновый поток для автоматического сохранения"""
    while True:
        time.sleep(300)  # Каждые 5 минут
        try:
            force_save()
            print("💾 Автосохранение выполнено")
        except Exception as e:
            print(f"⚠️ Ошибка автосохранения: {e}")

def force_save():
    """Принудительное сохранение всех изменений"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        return False

# Запускаем автосохранение в фоне
threading.Thread(target=auto_save_worker, daemon=True).start()

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

def get_user_data(user_id):
    """Получить данные пользователя"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT user_id, stars, username, security_target, security_progress
    FROM users WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    
    if row is None:
        # Создаем нового пользователя
        cursor.execute('''
        INSERT INTO users (user_id, username, stars, security_target, security_progress)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, f"User_{user_id}", 0.0, 3, 0))
        conn.commit()
        
        cursor.execute('''
        SELECT user_id, stars, username, security_target, security_progress
        FROM users WHERE user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
    
    conn.close()
    
    return {
        "user_id": row[0],
        "stars": row[1],
        "username": row[2],
        "security_target": row[3],
        "security_progress": row[4]
    }

def update_user_data(user_id, username, stars_change=0.0):
    """Обновить данные пользователя"""
    user_id = int(user_id)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT stars FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        current_stars = 0.0
    else:
        current_stars = row[0]
    
    new_stars = max(0, current_stars + stars_change)
    
    cursor.execute('''
    UPDATE users SET stars = ?, username = ? WHERE user_id = ?
    ''', (new_stars, username[:50], user_id))
    
    conn.commit()
    conn.close()
    
    return get_user_data(user_id)

# ==================== РЕФЕРАЛЫ ====================

def add_referral(referrer_id, referral_id, ref_type="quest"):
    """Добавить реферала"""
    referrer_id = int(referrer_id)
    referral_id = int(referral_id)

    if referrer_id == referral_id:
        print(f"❌ Нельзя пригласить самого себя")
        return False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем, существует ли реферал уже
    cursor.execute('SELECT id FROM referrals WHERE referral_id = ?', (referral_id,))
    if cursor.fetchone():
        print(f"❌ Реферал {referral_id} уже существует")
        conn.close()
        return False
    
    # Проверяем, существует ли пользователь-реферер
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (referrer_id,))
    if not cursor.fetchone():
        print(f"❌ Реферер {referrer_id} не найден в БД")
        conn.close()
        return False

    try:
        # Добавляем реферала
        cursor.execute('''
        INSERT INTO referrals (referrer_id, referral_id, type, date)
        VALUES (?, ?, ?, ?)
        ''', (referrer_id, referral_id, ref_type, datetime.now().isoformat()))
        
        print(f"✅ Реферал добавлен: {referrer_id} -> {referral_id}, тип={ref_type}")
        
        # Обновляем прогресс безопасности
        cursor.execute('''
        SELECT security_target, security_progress FROM users WHERE user_id = ?
        ''', (referrer_id,))
        row = cursor.fetchone()
        
        if row:
            target = row[0]
            progress = row[1]
            
            if ref_type == "security":
                if progress < target:
                    cursor.execute('''
                    UPDATE users SET security_progress = security_progress + 1
                    WHERE user_id = ?
                    ''', (referrer_id,))
                    print(f"🔐 Прогресс безопасности: {progress + 1}/{target}")
            
            elif ref_type == "quest":
                # Считаем количество рефералов для задания
                cursor.execute('''
                SELECT COUNT(*) FROM referrals 
                WHERE referrer_id = ? AND type = 'quest'
                ''', (referrer_id,))
                quest_count = cursor.fetchone()[0]
                
                # Проверяем, выполнено ли уже задание
                cursor.execute('''
                SELECT completed FROM user_quests 
                WHERE user_id = ? AND quest_id = 'invite_3_friends'
                ''', (referrer_id,))
                quest_completed = cursor.fetchone()
                
                if quest_count >= 3 and not quest_completed:
                    # Начисляем 100 звезд
                    cursor.execute('''
                    UPDATE users SET stars = stars + 100 WHERE user_id = ?
                    ''', (referrer_id,))
                    
                    # Отмечаем задание как выполненное
                    cursor.execute('''
                    INSERT OR IGNORE INTO user_quests (user_id, quest_id, completed)
                    VALUES (?, 'invite_3_friends', 1)
                    ''', (referrer_id,))
                    
                    print(f"🎉 Бонус: 100 звезд за 3 друзей!")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка добавления реферала: {e}")
        conn.close()
        return False

def get_referral_count(user_id, ref_type=None):
    """Получить количество рефералов"""
    user_id = int(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if ref_type:
        cursor.execute('''
        SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND type = ?
        ''', (user_id, ref_type))
    else:
        cursor.execute('''
        SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
        ''', (user_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_quest_referral_count(user_id):
    return get_referral_count(user_id, "quest")

def get_security_referral_count(user_id):
    return get_referral_count(user_id, "security")

def get_total_referral_count(user_id):
    return get_referral_count(user_id)

# ==================== ЗАДАНИЯ ====================

def check_quest_completion(user_id):
    quest_count = get_quest_referral_count(user_id)
    return quest_count >= 3

def get_quest_referrals_needed(user_id):
    if check_quest_completion(user_id):
        return 0
    count = get_quest_referral_count(user_id)
    return max(0, 3 - count)

def is_quest_completed(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT completed FROM user_quests 
    WHERE user_id = ? AND quest_id = 'invite_3_friends'
    ''', (int(user_id),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def update_quest_progress(user_id, quest_id, completed=True):
    user_id = int(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if completed:
        cursor.execute('''
        INSERT OR REPLACE INTO user_quests (user_id, quest_id, completed)
        VALUES (?, ?, 1)
        ''', (user_id, quest_id))
    else:
        cursor.execute('''
        DELETE FROM user_quests WHERE user_id = ? AND quest_id = ?
        ''', (user_id, quest_id))
    
    conn.commit()
    conn.close()

def get_user_quests(user_id):
    user_id = int(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT quest_id, completed FROM user_quests WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    quests = {}
    for quest_id, completed in rows:
        quests[quest_id] = bool(completed)
    return quests

# ==================== БЕЗОПАСНОСТЬ ====================

def get_security_message(needed_count):
    messages = SECURITY_MESSAGES.get(needed_count, SECURITY_MESSAGES[3])
    return random.choice(messages)

def get_total_security_needed(user_id):
    user = get_user_data(user_id)
    return user.get('security_target', 3)

def get_security_referrals_needed(user_id):
    user = get_user_data(user_id)
    target = user.get('security_target', 3)
    progress = user.get('security_progress', 0)
    return max(0, target - progress)

def check_security_completion(user_id):
    user = get_user_data(user_id)
    target = user.get('security_target', 3)
    progress = user.get('security_progress', 0)
    return progress >= target

def reset_security_target(user_id):
    """Сбросить цель безопасности на новое случайное значение (1, 2 или 3)"""
    user = get_user_data(user_id)
    old_target = user.get('security_target', 3)
    
    possible_targets = [1, 2, 3]
    if old_target in possible_targets:
        possible_targets.remove(old_target)
    new_target = random.choice(possible_targets)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users SET security_target = ?, security_progress = 0
    WHERE user_id = ?
    ''', (new_target, user_id))
    conn.commit()
    conn.close()
    
    print(f"🔄 Сброс безопасности: {old_target} -> {new_target}")
    return new_target

def should_show_security(user_id):
    user = get_user_data(user_id)
    return user.get('stars', 0) >= 500

# ==================== ПРОМОКОДЫ ====================

def use_promo_code(user_id, code):
    from config import PROMO_CODES
    user_id = int(user_id)
    code = code.upper()
    
    if code not in PROMO_CODES:
        return 0
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM used_promocodes WHERE user_id = ? AND promo_code = ?
    ''', (user_id, code))
    
    if cursor.fetchone():
        conn.close()
        return -1
    
    cursor.execute('''
    INSERT INTO used_promocodes (user_id, promo_code)
    VALUES (?, ?)
    ''', (user_id, code))
    
    conn.commit()
    conn.close()
    return PROMO_CODES[code]

def get_used_promos(user_id):
    user_id = int(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT promo_code FROM used_promocodes WHERE user_id = ?', (user_id,))
    promos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return promos

# ==================== ТОП ПОЛЬЗОВАТЕЛЕЙ ====================

def get_top_users(limit=10, exclude_user_id=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if exclude_user_id:
        cursor.execute('''
        SELECT user_id, stars, username FROM users
        WHERE user_id != ?
        ORDER BY stars DESC
        LIMIT ?
        ''', (exclude_user_id, limit))
    else:
        cursor.execute('''
        SELECT user_id, stars, username FROM users
        ORDER BY stars DESC
        LIMIT ?
        ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results

# ==================== СТАТИСТИКА ИГР ====================

def update_games_stats(user_id, bet, win):
    user_id = int(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO games_stats (user_id, games_played, total_bet, total_win)
    VALUES (?, 1, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        games_played = games_played + 1,
        total_bet = total_bet + excluded.total_bet,
        total_win = total_win + excluded.total_win
    ''', (user_id, bet, win))
    
    conn.commit()
    conn.close()

def get_games_stats(user_id):
    user_id = int(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT games_played, total_bet, total_win FROM games_stats WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"games_played": row[0], "total_bet": row[1], "total_win": row[2]}
    return {"games_played": 0, "total_bet": 0, "total_win": 0}

# ==================== БАНЫ ====================

def ban_user(user_id, reason, admin_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, date)
    VALUES (?, ?, ?, ?)
    ''', (user_id, reason, admin_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def is_banned(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM banned_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_ban_info(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT reason, banned_by, date FROM banned_users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"reason": row[0], "banned_by": row[1], "date": row[2]}
    return None

def get_banned_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, reason, banned_by, date FROM banned_users')
    rows = cursor.fetchall()
    conn.close()
    
    banned = {}
    for row in rows:
        banned[str(row[0])] = {"reason": row[1], "banned_by": row[2], "date": row[3]}
    return banned

# ==================== ПОЛУЧЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ====================

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, stars, username, security_target, security_progress FROM users')
    rows = cursor.fetchall()
    conn.close()
    
    users = {}
    for row in rows:
        users[row[0]] = {
            "user_id": row[0],
            "stars": row[1],
            "username": row[2],
            "security_target": row[3],
            "security_progress": row[4]
        }
    return users

def get_all_referrals():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id, referral_id, type, date FROM referrals ORDER BY referrer_id')
    rows = cursor.fetchall()
    conn.close()
    
    referrals = {}
    for row in rows:
        referrer_id = row[0]
        if referrer_id not in referrals:
            referrals[referrer_id] = []
        referrals[referrer_id].append({
            "id": row[1],
            "type": row[2],
            "date": row[3]
        })
    return referrals

def get_referral_data():
    return get_all_referrals()

# ==================== ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ ====================

def load_all_data():
    """Загрузить все данные в глобальные переменные (для совместимости)"""
    global user_data, referral_data, used_promo_codes, user_quests, games_stats, banned_users
    user_data = get_all_users()
    referral_data = get_all_referrals()
    banned_users = get_banned_users()
    
    # Загружаем использованные промокоды
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, promo_code FROM used_promocodes')
    used_promo_codes = {}
    for user_id, promo in cursor.fetchall():
        if user_id not in used_promo_codes:
            used_promo_codes[user_id] = []
        used_promo_codes[user_id].append(promo)
    
    # Загружаем задания
    cursor.execute('SELECT user_id, quest_id FROM user_quests WHERE completed = 1')
    user_quests = {}
    for user_id, quest_id in cursor.fetchall():
        if user_id not in user_quests:
            user_quests[user_id] = {}
        user_quests[user_id][quest_id] = True
    
    # Загружаем статистику игр
    cursor.execute('SELECT user_id, games_played, total_bet, total_win FROM games_stats')
    games_stats = {}
    for user_id, played, bet, win in cursor.fetchall():
        games_stats[user_id] = {
            "games_played": played,
            "total_bet": bet,
            "total_win": win
        }
    
    conn.close()
    
    print(f"✅ Данные загружены из SQLite. Пользователей: {len(user_data)}")
    return True

def save_all_data():
    """Принудительно сохранить все изменения в БД"""
    return force_save()

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================

# Инициализируем базу данных
init_database()

# Для совместимости со старым кодом
user_data = get_all_users()
referral_data = get_all_referrals()
used_promo_codes = {}
user_quests = {}
games_stats = {}
banned_users = get_banned_users()