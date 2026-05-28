import datetime
import os

STATS_FILE = "bot_stats.txt"

def log_user_action(user_id, username, action, details=""):
    """Логировать действия пользователей"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] UserID: {user_id} | Name: {username} | Action: {action}"
    if details:
        log_entry += f" | Details: {details}"
    log_entry += "\n"
    
    with open(STATS_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def log_referral(inviter_id, inviter_name, referral_id, referral_name):
    """Логировать приглашения"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] 🎯 REFERRAL | Inviter: {inviter_name} ({inviter_id}) -> New user: {referral_name} ({referral_id})\n"
    
    with open(STATS_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def get_stats():
    """Получить статистику из файла"""
    if not os.path.exists(STATS_FILE):
        return "Статистика пока пуста"
    
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return f.read()