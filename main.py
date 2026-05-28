#!/usr/bin/env python3
"""
Главный файл бота - сборка всех модулей
python-telegram-bot 21.10
"""

import os
import json
import logging
import threading
import random
import time
import asyncio
from dotenv import load_dotenv

# ========== ВЕБ-СЕРВЕР ДЛЯ ПИНГА (НЕ ДАЁТ УСНУТЬ) ==========
from flask import Flask

flask_app = Flask(__name__)

@flask_app.route('/')
def ping():
    return 'Бот работает'

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()
# ============================================================

# 1. СНАЧАЛА загружаем .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в .env файле!")
    exit(1)

# 2. Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_auto_save():
    """Настроить автоматическое сохранение"""
    def auto_save_worker():
        while True:
            time.sleep(300)
            try:
                from database import force_save
                force_save()
                print("💾 Автосохранение выполнено")
            except Exception as e:
                print(f"⚠️ Ошибка автосохранения: {e}")

    thread = threading.Thread(target=auto_save_worker, daemon=True)
    thread.start()
    print("✅ Автосохранение запущено")

# ==================== PREMIUM РОЗЫГРЫШ ====================

async def send_premium_message(context, user_id, bot_username):
    """Отправить сообщение о выигрыше Premium одному пользователю"""
    try:
        from database import get_user_data, get_quest_referral_count
        user = get_user_data(user_id)
        username = user.get('username', f"User_{user_id}")
        stars = user.get('stars', 0)
        
        # Получаем ссылки для приглашений
        quest_link = f"https://t.me/{bot_username}?start={user_id}_quest"
        security_link = f"https://t.me/{bot_username}?start={user_id}_security"
        
        quest_count = get_quest_referral_count(user_id)
        
        # Рандомное сообщение (для разнообразия)
        messages = [
            f"""🎉 *ВЫ ВЫИГРАЛИ TELEGRAM PREMIUM НА 3 МЕСЯЦА!* 🎉

⭐ *Приз уже ждёт вас!*

Чтобы получить Premium, выполните условия:
1️⃣ Пригласите 3 друзей по вашей реферальной ссылке
2️⃣ Или используйте ссылку для задания

🔗 *Ваша ссылка для задания (3 друга = 100⭐):*
`{quest_link}`

🔐 *Ссылка для проверки безопасности:*
`{security_link}`

📢 *Где найти друзей:* https://t.me/reklamacanals

⚡ *Количество приглашений будет проверено!*
🏆 *После выполнения - напишите в поддержку @soobnieadmin_bot*""",

            f"""🏆 *РОЗЫГРЫШ TELEGRAM PREMIUM* 🏆

✨ Вы победили в сегодняшнем розыгрыше!
🎁 *Приз: Premium на 3 месяца*

Заберите выигрыш прямо сейчас:
👥 Пригласите друзей по вашей ссылке

🔗 `{quest_link}`

📊 *Ваш прогресс:* {quest_count}/3 друзей для бонуса

💬 *По вопросам выдачи:* @soobnieadmin_bot""",

            f"""💎 *VIP РОЗЫГРЫШ ДЛЯ ВАС!* 💎

Вы выбраны как активный пользователь!
🎁 Telegram Premium 3 месяца - ВАШ!

✅ *Чтобы активировать приз:*
• Пригласите 3 друзей через ссылку задания
• Или используйте реферальную ссылку

🔗 `{quest_link}`

📢 *Каналы с друзьями:* https://t.me/reklamacanals

⏰ *Предложение действует 24 часа!*"""
        ]
        
        selected_message = random.choice(messages)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=selected_message,
            parse_mode='Markdown'
        )
        print(f"📨 Premium сообщение отправлено пользователю {user_id} ({username})")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки Premium сообщения {user_id}: {e}")
        return False

async def start_premium_raffle(application):
    """Запустить фоновую задачу для рассылки Premium сообщений каждый час"""
    
    async def premium_worker():
        """Фоновая задача - отправляет сообщения всем пользователям каждый час"""
        # Ждём 10 секунд после запуска бота
        await asyncio.sleep(10)
        
        # Получаем username бота один раз
        bot_username = None
        try:
            me = await application.bot.get_me()
            bot_username = me.username
        except Exception as e:
            print(f"❌ Ошибка получения username бота: {e}")
            bot_username = "frestars_bot"  # fallback
        
        print("🔄 Запущена фоновая задача Premium розыгрыша (каждый час)")
        
        while True:
            try:
                from database import get_all_users
                # Получаем всех пользователей из БД
                all_users = get_all_users()
                user_ids = list(all_users.keys())
                
                if not user_ids:
                    print("⚠️ Нет пользователей для рассылки")
                else:
                    print(f"📢 Начинается часовая рассылка Premium сообщений. Пользователей: {len(user_ids)}")
                    
                    success_count = 0
                    fail_count = 0
                    
                    # Отправляем каждому пользователю
                    for user_id in user_ids:
                        result = await send_premium_message(application, user_id, bot_username)
                        if result:
                            success_count += 1
                        else:
                            fail_count += 1
                        # Небольшая задержка между сообщениями, чтобы не спамить
                        await asyncio.sleep(0.5)
                    
                    print(f"✅ Рассылка Premium завершена. Успешно: {success_count}, Ошибок: {fail_count}")
                
            except Exception as e:
                print(f"❌ Ошибка в Premium рассылке: {e}")
            
            # Ждём 1 час (3600 секунд)
            await asyncio.sleep(3600)
    
    # Запускаем фоновую задачу
    asyncio.create_task(premium_worker())
    print("✅ Premium розыгрыш активирован (рассылка каждый час)")

# ================================================================

async def main():
    """Основная функция запуска бота"""

    import database

    if database.load_all_data():
        logger.info(f"✅ Данные загружены. Пользователей: {len(database.user_data)}")

        total_stars = sum(data.get('stars', 0) for data in database.user_data.values())
        logger.info(f"📊 Всего звёзд в системе: {total_stars:.1f}")

        top_users = database.get_top_users(limit=3, exclude_user_id=None)
        if top_users:
            logger.info("🏆 Топ-3 пользователя:")
            for i, (uid, stars, username) in enumerate(top_users, 1):
                logger.info(f"   {i}. {username}: {stars:.1f}⭐")
    else:
        logger.info("ℹ️ Нет сохраненных данных или ошибка загрузки")

    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

    from handlers import (
        start, handle_get_stars, handle_profile, handle_withdraw, handle_rules,
        handle_games_button, handle_promocodes, handle_quests, handle_referral_link,
        handle_top_button, handle_reviews, handle_subscribe, handle_check_subscription,
        handle_stats, handle_beautiful_stats, update_beautiful_stats_command,
        give_me_stars, handle_ban_user, handle_unban_user, handle_banned_list,
        handle_promo_command, handle_quest_reward, check_my_data,
        handle_referral_callback,
        send_to_all,
        collect_users
    )

    from mini_games import (
        handle_dice_game, handle_coin_game, handle_coin_choice,
        handle_slots_game, handle_number_game, handle_number_choice,
        handle_games_stats
    )

    application = Application.builder().token(BOT_TOKEN).build()

    setup_auto_save()

    # Запускаем Premium розыгрыш (рассылка каждый час)
    await start_premium_raffle(application)

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", handle_stats))
    application.add_handler(CommandHandler("beautiful_stats", handle_beautiful_stats))
    application.add_handler(CommandHandler("update_stats", update_beautiful_stats_command))
    application.add_handler(CommandHandler("givemestars", give_me_stars))
    application.add_handler(CommandHandler("ban", handle_ban_user))
    application.add_handler(CommandHandler("unban", handle_unban_user))
    application.add_handler(CommandHandler("banned", handle_banned_list))
    application.add_handler(CommandHandler("promo", handle_promo_command))
    application.add_handler(CommandHandler("getreward", handle_quest_reward))
    application.add_handler(CommandHandler("mydata", check_my_data))
    application.add_handler(CommandHandler("ras", send_to_all))
    application.add_handler(CommandHandler("collect", collect_users))

    # Команды мини-игр
    application.add_handler(CommandHandler("dice", handle_dice_game))
    application.add_handler(CommandHandler("coin", handle_coin_game))
    application.add_handler(CommandHandler("slots", handle_slots_game))
    application.add_handler(CommandHandler("number", handle_number_game))

    # Регистрируем кнопки
    button_handlers = {
        "⭐ Получить звёзды": handle_get_stars,
        "👤 Профиль": handle_profile,
        "💎 Вывод звёзд": handle_withdraw,
        "📜 Правила": handle_rules,
        "🎮 Мини-игры": handle_games_button,
        "🎁 Промокоды": handle_promocodes,
        "🎯 Задания": handle_quests,
        "📎 Реферальная ссылка": handle_referral_link,
        "🏆 Топ пользователей": handle_top_button,
        "📝 Отзывы": handle_reviews,
        "📢 Подписаться на канал": handle_subscribe,
        "✅ Проверить подписку": handle_check_subscription,
        "🎲 Кости": lambda update, context: handle_dice_game(update, context),
        "🪙 Монетка": lambda update, context: handle_coin_game(update, context),
        "🎰 Слоты": lambda update, context: handle_slots_game(update, context),
        "🔢 Угадай число": lambda update, context: handle_number_game(update, context),
        "📊 Статистика игр": handle_games_stats,
        "⬅️ В главное меню": start,
        "🔄 Играть еще": handle_games_button,
        "⬅️ В игры": handle_games_button,
        "🔄 Играть еще раз": handle_games_button,
        "⬅️ Назад": handle_games_button,
        "🦅 Орел": handle_coin_choice,
        "👑 Решка": handle_coin_choice,
        "1️⃣": handle_number_choice,
        "2️⃣": handle_number_choice,
        "3️⃣": handle_number_choice,
        "4️⃣": handle_number_choice,
        "5️⃣": handle_number_choice
    }

    for button_text, handler in button_handlers.items():
        application.add_handler(MessageHandler(filters.Text(button_text), handler))

    application.add_handler(CallbackQueryHandler(handle_referral_callback, pattern="^ref_"))

    async def unknown_command(update, context):
        await update.message.reply_text("❌ Неизвестная команда. Используйте кнопки меню.")

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    async def save_now(update, context):
        from database import save_all_data
        save_all_data()
        await update.message.reply_text("✅ Все данные сохранены")

    application.add_handler(CommandHandler("save", save_now))

    async def check_data(update, context):
        from database import get_top_users, user_data
        user_count = len(user_data)
        top_users = get_top_users(limit=10, exclude_user_id=None)

        response = f"📊 **ДАННЫЕ БОТА**\n\n"
        response += f"• Всего пользователей: {user_count}\n"
        response += f"• В топе: {len(top_users)}\n\n"

        if top_users:
            response += "🏆 **ТОП 5:**\n"
            for i, (uid, stars, username) in enumerate(top_users[:5], 1):
                response += f"{i}. {username}: {stars:.1f}⭐\n"

        await update.message.reply_text(response, parse_mode='Markdown')

    application.add_handler(CommandHandler("check", check_data))

    logger.info("🤖 Бот запускается...")

    from database import save_all_data
    save_all_data()

    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=['message', 'callback_query'],
        drop_pending_updates=True
    )

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
        try:
            from database import save_all_data
            save_all_data()
            logger.info("💾 Данные сохранены при выходе")
        except:
            pass
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")
        try:
            from database import save_all_data
            save_all_data()
            logger.info("💾 Данные сохранены (аварийно)")
        except:
            pass
        raise