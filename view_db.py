import sqlite3

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Общая статистика
cursor.execute("SELECT COUNT(*) FROM users")
users = cursor.fetchone()[0]
print(f"📊 Всего пользователей: {users}")

cursor.execute("SELECT COUNT(*) FROM referrals")
refs = cursor.fetchone()[0]
print(f"📎 Всего рефералов: {refs}")

cursor.execute("SELECT SUM(stars) FROM users")
stars = cursor.fetchone()[0]
print(f"⭐ Всего звёзд: {stars:.1f}")

# Топ-10
print("\n🏆 ТОП-10 ПОЛЬЗОВАТЕЛЕЙ:")
cursor.execute("SELECT username, stars FROM users ORDER BY stars DESC LIMIT 10")
for i, (name, stars) in enumerate(cursor.fetchall(), 1):
    print(f"{i}. {name}: {stars:.1f}⭐")

conn.close()