import json
import sqlite3
import os

print("🔍 Поиск файла с данными...")

# Показываем все JSON файлы
files = os.listdir('.')
json_files = [f for f in files if f.endswith('.json') and f != 'force_import.py']
print(f"Найдены JSON файлы: {json_files}")

if not json_files:
    print("❌ Нет JSON файлов!")
    exit()

# Берем первый JSON файл
json_file = json_files[0]
print(f"✅ Использую файл: {json_file}")

# Удаляем старую БД если есть
if os.path.exists('bot_database.db'):
    os.remove('bot_database.db')
    print("🗑️ Старая БД удалена")

# Создаем новую БД
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Создаем таблицы
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

cursor.execute('''
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referral_id INTEGER UNIQUE,
    type TEXT DEFAULT 'quest',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Читаем JSON
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Импортируем пользователей
users_count = 0
for user_id_str, user_info in data.get("user_data", {}).items():
    try:
        user_id = int(user_id_str)
        stars = user_info.get("stars", 0)
        username = user_info.get("username", f"User_{user_id}")[:50]
        security_target = user_info.get("security_target", 3)
        security_progress = user_info.get("security_progress", 0)
        
        cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, stars, username, security_target, security_progress)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, stars, username, security_target, security_progress))
        users_count += 1
        print(f"  + {username}: {stars}⭐")
    except Exception as e:
        print(f"  ❌ Ошибка с {user_id_str}: {e}")

# Импортируем рефералов
ref_count = 0
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
                    INSERT OR IGNORE INTO referrals (referrer_id, referral_id, type)
                    VALUES (?, ?, ?)
                    ''', (referrer_id, int(referral_id), ref_type))
                    ref_count += 1
                except:
                    pass
    except:
        pass

conn.commit()
conn.close()

print(f"\n✅ ИМПОРТ ЗАВЕРШЕН:")
print(f"   • Пользователей: {users_count}")
print(f"   • Рефералов: {ref_count}")
print(f"   • Файл: {json_file}")