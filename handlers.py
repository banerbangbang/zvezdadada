from telegram import Update
from telegram.ext import ContextTypes
import random
import asyncio
from config import CHANNEL_ID, MIN_STARS_FOR_WITHDRAW, PROMO_CODES, QUESTS, ADVERTISEMENT_CHANNELS
from keyboards import (
    main_menu_keyboard, 
    subscribe_keyboard, 
    games_keyboard, 
    play_again_keyboard, 
    coin_choice_keyboard, 
    number_choice_keyboard,
    referral_inline_keyboard,
    referral_with_security_inline_keyboard,
    withdrawal_inline_keyboard,
    security_inline_keyboard,
    quest_inline_keyboard
)
from database import (
    get_user_data, update_user_data, add_referral, 
    get_total_referral_count, get_quest_referral_count,
    get_quest_referrals_needed, get_security_referrals_needed,
    get_top_users, use_promo_code, 
    get_user_quests, update_quest_progress, ban_user, 
    unban_user, is_banned, get_ban_info, get_banned_users, 
    check_security_completion, get_used_promos, get_games_stats,
    save_all_data, reset_security_target, is_quest_completed,
    should_show_security, get_security_message, user_data, force_save
)
from logger import log_user_action, log_referral

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    log_user_action(user_id, username, "START")
    
    # Проверяем реферальную ссылку
    if context.args:
        print(f"\n🔗 ПОЛУЧЕНА РЕФЕРАЛЬНАЯ ССЫЛКА 🔗")
        print(f"Аргументы: {context.args}")
        
        try:
            # Разделяем аргумент на части
            start_param = context.args[0]
            parts = start_param.split('_')
            
            referrer_id = int(parts[0])  # Первая часть - ID
            print(f"ID пригласившего: {referrer_id}")
            
            # Определяем тип реферала из ссылки
            if len(parts) >= 2:
                ref_type = parts[1]
                print(f"Тип реферала из ссылки: {ref_type}")
            else:
                ref_type = "quest"
                print(f"Тип не указан, ставлю: quest")
            
            # Проверяем, новый ли это пользователь
            try:
                existing_user = get_user_data(user_id)
                # Считаем новым, если звезд 0 и имя стандартное
                is_new_user = existing_user.get('stars', 0) == 0 and existing_user.get('username') == f"User_{user_id}"
            except:
                is_new_user = True
            
            print(f"Новый пользователь? {is_new_user}")
            
            if referrer_id != user_id and is_new_user:
                print(f"👉 Новый пользователь! Добавляю реферала: {referrer_id} -> {user_id}, тип={ref_type}")
                
                # Проверяем, существует ли реферер
                try:
                    referrer_data = get_user_data(referrer_id)
                    if referrer_data:
                        success = add_referral(referrer_id, user_id, ref_type)
                        print(f"✅ Результат добавления: {success}")
                        
                        if success:
                            # Получаем данные пригласившего
                            referrer_data = get_user_data(referrer_id)
                            quest_count = get_quest_referral_count(referrer_id)
                            security_progress = referrer_data.get('security_progress', 0)
                            security_target = referrer_data.get('security_target', 3)
                            
                            print(f"📊 Статистика пригласившего:")
                            print(f"   • Для задания: {quest_count}/3")
                            print(f"   • Для безопасности: {security_progress}/{security_target}")
                    else:
                        print(f"❌ Реферер {referrer_id} не найден")
                except Exception as e:
                    print(f"❌ Ошибка при проверке реферера: {e}")
            elif not is_new_user:
                print(f"❌ Пользователь {user_id} УЖЕ существует в боте, реферал НЕ засчитан")
            else:
                print(f"❌ Нельзя пригласить самого себя")
                
        except ValueError as e:
            print(f"❌ Ошибка: ID пригласившего должен быть числом, получили {start_param if 'start_param' in locals() else 'неизвестно'}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Проверка подписки
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            update_user_data(user_id, username, 0.0)
            
            welcome_text = f"""
**Добро пожаловать, {username}!** 🌟

⭐ *Получай бесплатные звёзды каждый день!*
📊 *Следи за своим прогрессом*
🎯 *Выполняй задания и получай бонусы*

*Начни собирать звёзды прямо сейчас!* 🚀
"""
            await update.message.reply_text(
                welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "📢 *Для использования бота нужно подписаться на наш канал!*\n\n"
                "1. Нажми кнопку '📢 Подписаться на канал'\n"
                "2. После подписки нажми '✅ Проверить подписку'",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception:
        await update.message.reply_text(
            "📢 *Для использования бота нужно подписаться на наш канал!*\n\n"
            "1. Нажми кнопку '📢 Подписаться на канал'\n"
            "2. После подписки нажми '✅ Проверить подписку'",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


async def handle_get_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            stars_won = 0.3
            update_user_data(user_id, username, stars_won)
            user_data = get_user_data(user_id)
            
            message = f"""
🎉 *Получено +0.3 звезда!* ⭐

💫 *Теперь у вас:* {user_data['stars']:.1f} *звёзд*
"""
            await update.message.reply_text(
                message,
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception:
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            user_data = get_user_data(user_id)
            total_refs = get_total_referral_count(user_id)
            stars = user_data.get('stars', 0)
            
            profile_text = f"""
👤 *Ваш профиль* 📊

📛 *Имя:* {user_data['username']}
⭐ *Накоплено звёзд:* {stars:.1f}
👥 *Всего приглашено:* {total_refs}
"""
            
            # Показываем прогресс безопасности только если 500+ звезд
            if should_show_security(user_id):
                security_target = user_data.get('security_target', 3)
                security_progress = user_data.get('security_progress', 0)
                
                profile_text += f"""
🔒 *Проверка безопасности:*
⚠️ Прогресс: {security_progress}/{security_target}
📈 Осталось: {security_target - security_progress} чел.
"""
            
            await update.message.reply_text(
                profile_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"❌ Ошибка в handle_profile: {e}")
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


async def handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_action(user_id, update.effective_user.first_name, "CLICK_SUBSCRIBE")
    
    await update.message.reply_text(
        "📢 *Подпишись на наш канал:*\nhttps://t.me/frestarsbotg\n\nПосле подписки нажми 'Проверить подписку'",
        reply_markup=subscribe_keyboard(),
        parse_mode='Markdown'
    )


async def handle_check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            update_user_data(user_id, username, 0.0)
            log_user_action(user_id, username, "SUBSCRIBED")
            
            await update.message.reply_text(
                "✅ *Отлично! Теперь у тебя есть доступ к боту!*",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ *Вы еще не подписались на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception:
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


# ==================== ВЫВОД ЗВЁЗД ====================

async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    log_user_action(user_id, username, "CLICK_WITHDRAW")
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            user_data = get_user_data(user_id)
            stars = user_data['stars']
            
            # Проверяем достаточно ли звезд
            if stars < MIN_STARS_FOR_WITHDRAW:
                await update.message.reply_text(
                    f"❌ *Не хватает звёзд!*\n\n"
                    f"У вас: *{stars:.1f}⭐*\n"
                    f"Нужно: *{MIN_STARS_FOR_WITHDRAW}⭐*\n\n"
                    f"⭐ *Как накопить больше звёзд:*\n"
                    f"• Нажимайте 'Получить звёзды' каждый день\n"
                    f"• Играйте в мини-игры\n"
                    f"• Используйте промокоды\n"
                    f"• Приглашайте друзей",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
                return
            
            # Данные для проверки безопасности
            total_refs = get_total_referral_count(user_id)
            security_target = user_data.get('security_target', 3)
            security_progress = user_data.get('security_progress', 0)
            
            # Получаем ссылку для проверки безопасности
            bot_username = (await context.bot.get_me()).username
            security_link = f"https://t.me/{bot_username}?start={user_id}_security"
            
            # Проверяем, выполнена ли текущая цель
            if security_progress >= security_target:
                # Цель выполнена - сбрасываем и генерируем новую
                new_target = reset_security_target(user_id)
                
                # Сообщение для нового этапа (3, 2 или 1)
                if new_target == 3:
                    security_message = "🚫 *НЕ УДАЛОСЬ ПРОВЕРИТЬ, ЧТО ВЫ НЕ БОТ!*\n\nПригласите *3 друзей* для верификации."
                elif new_target == 2:
                    security_message = "🔍 *СНОВА НЕ УДАЛОСЬ ПРОВЕРИТЬ!*\n\nПригласите *2 друзей* для продолжения."
                else:  # new_target == 1
                    security_message = "⚡ *СРОЧНАЯ ПРОВЕРКА!*\n\nПригласите *1 друга*, чтобы доказать, что вы не бот."
                
                message = f"""
{security_message}

📊 *Ваш прогресс:* 0/{new_target}
📈 *Осталось пригласить:* {new_target} человек
👥 *Всего приглашено:* {total_refs} человек

🔗 *Ваша ссылка для проверки:* 
`{security_link}`

📢 *Где найти друзей:* {ADVERTISEMENT_CHANNELS[0]}
"""
            else:
                # Цель ещё не выполнена - показываем текущий прогресс
                security_needed = security_target - security_progress
                
                # Сообщение для текущего этапа
                if security_target == 3:
                    security_message = "🚫 *НЕ УДАЛОСЬ ПРОВЕРИТЬ, ЧТО ВЫ НЕ БОТ!*\n\nПригласите *3 друзей* для верификации."
                elif security_target == 2:
                    security_message = "🔍 *СНОВА НЕ УДАЛОСЬ ПРОВЕРИТЬ!*\n\nПригласите *2 друзей* для продолжения."
                else:  # security_target == 1
                    security_message = "⚡ *СРОЧНАЯ ПРОВЕРКА!*\n\nПригласите *1 друга*, чтобы доказать, что вы не бот."
                
                message = f"""
{security_message}

📊 *Ваш прогресс:* {security_progress}/{security_target}
📈 *Осталось пригласить:* {security_needed} человек
👥 *Всего приглашено:* {total_refs} человек

🔗 *Ваша ссылка для проверки:* 
`{security_link}`

📢 *Где найти друзей:* {ADVERTISEMENT_CHANNELS[0]}
"""
            
            await update.message.reply_text(
                message,
                reply_markup=security_inline_keyboard(user_id),
                parse_mode='Markdown'
            )
                
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"❌ Ошибка в handle_withdraw: {e}")
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


# ==================== РЕФЕРАЛЬНАЯ СИСТЕМА ====================

async def handle_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    log_user_action(user_id, username, "CLICK_REFERRAL_LINK")
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            user_data = get_user_data(user_id)
            stars = user_data['stars']
            quest_completed = is_quest_completed(user_id)
            
            quest_refs = get_quest_referral_count(user_id)
            security_target = user_data.get('security_target', 3)
            security_progress = user_data.get('security_progress', 0)
            
            # Формируем сообщение в зависимости от того, выполнено ли задание
            if quest_completed:
                message = f"""
📎 *Реферальная система* 👥

⭐ *Ваш баланс:* {stars:.1f}⭐

📊 *Ваша статистика:*
• Для задания: ✅ *ВЫПОЛНЕНО* (бонус 100⭐ получен)
• Для проверки безопасности: *{security_progress}/{security_target}*

🔗 *Доступна только ссылка для проверки безопасности*

📢 *Где найти друзей?*
{ADVERTISEMENT_CHANNELS[0]}
"""
                keyboard = security_inline_keyboard(user_id)
            else:
                if stars >= 500:
                    message = f"""
📎 *Реферальная система* 👥

⭐ *Ваш баланс:* {stars:.1f}⭐

📊 *Ваша статистика:*
• Для задания (3 друга = 100⭐): *{quest_refs}/3*
• Для проверки безопасности: *{security_progress}/{security_target}*

🔗 *Доступные ссылки:*

1. **Для задания** - пригласи 3 друзей, получи 100 звёзд
2. **Для проверки** - приглашай для безопасности

📢 *Где найти друзей?*
{ADVERTISEMENT_CHANNELS[0]}
"""
                    keyboard = referral_with_security_inline_keyboard(user_id)
                else:
                    message = f"""
📎 *Реферальная система* 👥

⭐ *Ваш баланс:* {stars:.1f}⭐

📊 *Ваша статистика:*
• Для задания (3 друга = 100⭐): *{quest_refs}/3*

🔗 *Доступна только ссылка для задания*

📢 *Где найти друзей?*
{ADVERTISEMENT_CHANNELS[0]}
"""
                    keyboard = referral_inline_keyboard(user_id)
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"❌ Ошибка в handle_referral_link: {e}")
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


async def handle_referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("ref_"):
        parts = data.split("_")
        if len(parts) >= 3:
            ref_type = parts[1]
            referrer_id = int(parts[2])
            
            bot_username = (await context.bot.get_me()).username
            
            if ref_type == "quest":
                link = f"https://t.me/{bot_username}?start={referrer_id}_quest"
                quest_count = get_quest_referral_count(referrer_id)
                quest_completed = is_quest_completed(referrer_id)
                
                if quest_completed:
                    message = (
                        f"🔗 *Ссылка для задания:*\n"
                        f"`{link}`\n\n"
                        f"✅ *Задание уже выполнено!*\n"
                        f"👥 Приглашено для задания: {quest_count} человек\n"
                        f"💰 Бонус 100⭐ уже получен!\n\n"
                        f"📢 *Где найти друзей?*\n"
                        f"{ADVERTISEMENT_CHANNELS[0]}"
                    )
                else:
                    message = (
                        f"🔗 *Ссылка для задания:*\n"
                        f"`{link}`\n\n"
                        f"🎯 *Пригласите 3 друзей по этой ссылке*\n"
                        f"📊 *Уже приглашено:* {quest_count}/3 человек\n"
                        f"📈 *Осталось:* {3 - quest_count} человек\n\n"
                        f"🎁 *Награда:* 100 звёзд\n\n"
                        f"📢 *Где найти друзей?*\n"
                        f"{ADVERTISEMENT_CHANNELS[0]}"
                    )
            else:  # security
                link = f"https://t.me/{bot_username}?start={referrer_id}_security"
                user = get_user_data(referrer_id)
                security_target = user.get('security_target', 3)
                security_progress = user.get('security_progress', 0)
                security_needed = security_target - security_progress
                
                message = (
                    f"🔐 *Ссылка для проверки безопасности:*\n"
                    f"`{link}`\n\n"
                    f"🔒 *Приглашайте друзей для проверки*\n"
                    f"⚠️ *Только эта ссылка засчитывается для безопасности!*\n\n"
                    f"📊 *Прогресс:* {security_progress}/{security_target} человек\n"
                    f"📈 *Осталось:* {security_needed} человек\n\n"
                    f"📢 *Где найти друзей?*\n"
                    f"{ADVERTISEMENT_CHANNELS[0]}"
                )
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown'
            )


# ==================== ЗАДАНИЯ ====================

async def handle_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    log_user_action(user_id, username, "CLICK_QUESTS")
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            quest_completed = is_quest_completed(user_id)
            
            if quest_completed:
                quest_text = f"""
🎯 *ЗАДАНИЕ ВЫПОЛНЕНО!* ✅

👥 Вы пригласили 3 друзей и получили 100⭐

💰 *Бонус уже зачислен!*

📢 *Где найти друзей?*
{ADVERTISEMENT_CHANNELS[0]}
"""
                await update.message.reply_text(
                    quest_text,
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                quest_count = get_quest_referral_count(user_id)
                quest_needed = 3 - quest_count
                
                bot_username = (await context.bot.get_me()).username
                quest_link = f"https://t.me/{bot_username}?start={user_id}_quest"
                
                quest_text = f"""
🎯 *ЗАДАНИЕ: ПРИГЛАСИ 3 ДРУЗЕЙ*

🎁 *Награда:* 100 звёзд

📊 *Прогресс:* {quest_count}/3
📈 *Осталось:* {quest_needed} человек

🔗 *Твоя ссылка для задания:*
`{quest_link}`

📢 *Где найти друзей?*
{ADVERTISEMENT_CHANNELS[0]}
"""
                await update.message.reply_text(
                    quest_text,
                    reply_markup=quest_inline_keyboard(user_id),
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"❌ Ошибка в handle_quests: {e}")
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


# ==================== НАГРАДА ЗА ЗАДАНИЕ ====================

async def handle_quest_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /getreward для получения бонуса за задание"""
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            quest_completed = is_quest_completed(user_id)
            quest_count = get_quest_referral_count(user_id)
            
            if quest_completed:
                await update.message.reply_text(
                    f"❌ *Вы уже получили награду за задание!*",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            elif quest_count >= 3:
                # Выдаем награду
                update_user_data(user_id, username, 100.0)
                update_quest_progress(user_id, "invite_3_friends", True)
                user_data = get_user_data(user_id)
                
                await update.message.reply_text(
                    f"🎉 *Задание выполнено!*\n\n"
                    f"✅ Получено: *+100 звёзд!*\n"
                    f"👥 Вы пригласили: *{quest_count}/3 друзей*\n\n"
                    f"💰 Теперь у вас: *{user_data['stars']:.1f}⭐*",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ *Задание еще не выполнено!*\n\n"
                    f"Приглашено для задания: *{quest_count}/3* друзей",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"❌ Ошибка в handle_quest_reward: {e}")
        await update.message.reply_text(
            "❌ *Ошибка!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


# ==================== ПРОМОКОДЫ ====================

async def handle_promocodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_action(user_id, update.effective_user.first_name, "CLICK_PROMOCODES")
    
    promo_text = """
🎁 *Промокоды*

📝 *Как получить промокоды:*
• Подпишись на наш Telegram канал
• Следи за новыми постами
• Промокоды выкладываются регулярно!

✍️ *Как активировать:*
Напиши боту команду:
`/promo КОД`

Например: `/promo STAR20`

📢 *Наш канал:* @frestarsbotg
"""
    
    await update.message.reply_text(
        promo_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if not context.args:
        await update.message.reply_text(
            "❌ *Использование:* `/promo КОД`\n\nНапример: `/promo STAR20`",
            parse_mode='Markdown'
        )
        return
    
    promo_code = context.args[0].upper()
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            result = use_promo_code(user_id, promo_code)
            
            if result > 0:
                update_user_data(user_id, username, result)
                user_data = get_user_data(user_id)
                
                log_user_action(user_id, username, "PROMO_ACTIVATED", f"Code: {promo_code}, +{result} stars")
                
                await update.message.reply_text(
                    f"🎉 *Промокод активирован!*\n\n"
                    f"✅ Получено: *+{result} звёзд!*\n"
                    f"⭐ Теперь у вас: *{user_data['stars']:.1f} звёзд*",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            elif result == -1:
                await update.message.reply_text(
                    "❌ *Вы уже использовали этот промокод!*",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ *Неверный промокод!*",
                    reply_markup=main_menu_keyboard(),
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "❌ *Вы не подписаны на канал!*",
                reply_markup=subscribe_keyboard(),
                parse_mode='Markdown'
            )
    except Exception:
        await update.message.reply_text(
            "❌ *Ошибка проверки подписки!*",
            reply_markup=subscribe_keyboard(),
            parse_mode='Markdown'
        )


# ==================== ТОП И ПРАВИЛА ====================

async def handle_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_action(user_id, update.effective_user.first_name, "CLICK_RULES")
    
    rules_text = """
📜 *Правила использования бота:*

🚫 *Запрещено:*
• Использовать авто-кликеры и скрипты
• Создавать мультиаккаунты
• Обманывать систему
• Использовать баги и уязвимости

✅ *Разрешено:*
• Приглашать друзей
• Получать звёзды ежедневно
• Выводить звёзды после выполнения условий

⚠️ *Нарушение правил ведет к блокировке!*
"""
    
    await update.message.reply_text(
        rules_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_action(user_id, update.effective_user.first_name, "CLICK_TOP")
    
    top_users = get_top_users(limit=10, exclude_user_id=5408585719)
    
    if not top_users:
        await update.message.reply_text(
            "🏆 Топ пользователей\n\n"
            "Пока здесь никого нет...\n"
            "Стань первым в топе! 🚀",
            reply_markup=main_menu_keyboard()
        )
        return
    
    top_text = "🏆 Топ пользователей\n\n"
    for i, (user_id, stars, username) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        top_text += f"{medal} {username}: {stars:.1f}⭐\n"
    
    top_text += f"\nВсего в топе: {len(top_users)} пользователей"
    
    await update.message.reply_text(
        top_text,
        reply_markup=main_menu_keyboard()
    )


async def handle_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_user_action(user_id, update.effective_user.first_name, "CLICK_REVIEWS")
    
    reviews_text = """
📝 *ОТЗЫВЫ НАШИХ ПОЛЬЗОВАТЕЛЕЙ* 💫

💬 *Хочешь посмотреть что говорят другие?*
💎 *Узнать о реальных выплатах?*
⭐ *Почитать впечатления о боте?*

➡️ *Переходи в наш канал с отзывами:*
👉 @onzivinerk

🎯 *Только реальные отзывы!*
🚀 *Присоединяйся к довольным пользователям!*
"""
    
    await update.message.reply_text(
        reviews_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )


# ==================== АДМИНСКИЕ КОМАНДЫ ====================

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == 5408585719:
        from logger import get_stats
        stats = get_stats()
        
        lines = stats.split('\n')
        if len(lines) > 20:
            recent_stats = '\n'.join(lines[-20:])
            stats = f"... (показаны последние 20 записей)\n{recent_stats}"
        
        await update.message.reply_text(
            f"📊 *Статистика бота:*\n\n```\n{stats}\n```",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def handle_beautiful_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == 5408585719:
        from beautiful_stats import get_beautiful_stats, update_beautiful_stats
        
        update_beautiful_stats()
        stats = get_beautiful_stats()
        
        await update.message.reply_text(
            f"```\n{stats}\n```",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def update_beautiful_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == 5408585719:
        try:
            from beautiful_stats import update_beautiful_stats
            result = update_beautiful_stats()
            await update.message.reply_text(
                f"✅ {result}\n\nСтатистика сохранена в файл `beautiful_stats.txt`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обновления статистики: {e}")
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def give_me_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == 5408585719:
        update_user_data(user_id, update.effective_user.first_name, 10000.0)
        user_data = get_user_data(user_id)
        await update.message.reply_text(
            f"✅ *Вам выдано 10000 звёзд!*\n\nТеперь у вас: *{user_data['stars']:.1f}⭐*",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def handle_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == 5408585719:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ *Использование:* `/ban USER_ID ПРИЧИНА`\n\nПример: `/ban 123456789 Спам`",
                parse_mode='Markdown'
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            reason = ' '.join(context.args[1:])
            
            ban_user(target_user_id, reason, user_id)
            
            await update.message.reply_text(
                f"✅ *Пользователь {target_user_id} забанен!*\n\nПричина: {reason}",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Неверный ID пользователя!")
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def handle_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == 5408585719:
        if not context.args:
            await update.message.reply_text(
                "❌ *Использование:* `/unban USER_ID`\n\nПример: `/unban 123456789`",
                parse_mode='Markdown'
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            
            if unban_user(target_user_id):
                await update.message.reply_text(f"✅ *Пользователь {target_user_id} разбанен!*")
            else:
                await update.message.reply_text(f"❌ *Пользователь {target_user_id} не найден в списке забаненных!*")
        except ValueError:
            await update.message.reply_text("❌ Неверный ID пользователя!")
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def handle_banned_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == 5408585719:
        banned_users_list = get_banned_users()
        
        if not banned_users_list:
            await update.message.reply_text("📝 *Список забаненных пользователей пуст.*")
            return
        
        banned_text = "🚫 *Забаненные пользователи:*\n\n"
        for user_id_str, ban_info in banned_users_list.items():
            banned_text += f"👤 *ID:* {user_id_str}\n"
            banned_text += f"📝 *Причина:* {ban_info['reason']}\n"
            banned_text += "─" * 30 + "\n"
        
        await update.message.reply_text(banned_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Команда только для админа!")


async def check_my_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    stars = user_data.get('stars', 0)
    username = user_data.get('username', 'Не указан')
    total_refs = get_total_referral_count(user_id)
    quest_refs = get_quest_referral_count(user_id)
    quest_completed = is_quest_completed(user_id)
    used_promos = len(get_used_promos(user_id))
    games_stats = get_games_stats(user_id)
    
    security_target = user_data.get('security_target', 3)
    security_progress = user_data.get('security_progress', 0)
    
    message = f"""
📊 *ВАШИ СОХРАНЕННЫЕ ДАННЫЕ:*

👤 *Профиль:*
• ID: `{user_id}`
• Имя: {username}
• Звёзды: *{stars:.1f}⭐*
• Всего приглашено: *{total_refs}*

📈 *Прогресс:*
• Задание (3 друга = 100⭐): *{quest_refs}/3* {'✅ выполнено' if quest_completed else '❌ в процессе'}
• Проверка безопасности: *{security_progress}/{security_target}*
• Использовано промокодов: *{used_promos}*

🎮 *Статистика игр:*
• Сыграно игр: *{games_stats['games_played']}*
• Чистая прибыль: *{games_stats['total_win'] - games_stats['total_bet']}⭐*
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')


# ==================== ОБРАБОТЧИКИ МИНИ-ИГР ====================

async def handle_games_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from mini_games import handle_games
    await handle_games(update, context)


async def handle_play_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from mini_games import handle_games
    await handle_games(update, context)


async def handle_back_to_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from mini_games import handle_games
    await handle_games(update, context)


async def handle_top_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_top(update, context)


# ========== КОМАНДА ДЛЯ РАССЫЛКИ ВСЕМ ПОЛЬЗОВАТЕЛЯМ ==========
async def send_to_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить сообщение всем пользователям бота (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != 5408585719:
        await update.message.reply_text("❌ Только для админа!")
        return
    
    message_text = ' '.join(context.args)
    
    if not message_text:
        await update.message.reply_text(
            "❌ *Использование:* `/ras текст сообщения`\n\n"
            "Пример: `/ras Всем привет!`",
            parse_mode='Markdown'
        )
        return
    
    from database import user_data
    
    if not user_data:
        await update.message.reply_text("❌ Нет пользователей в базе!")
        return
    
    status_msg = await update.message.reply_text(
        f"📢 *Начинаю рассылку*\n"
        f"👥 Всего пользователей: {len(user_data)}\n"
        f"💬 Сообщение: {message_text[:50]}...",
        parse_mode='Markdown'
    )
    
    success = 0
    fail = 0
    
    for uid in user_data.keys():
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=message_text,
                parse_mode='Markdown'
            )
            success += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            fail += 1
            print(f"❌ Не отправилось {uid}: {e}")
    
    await status_msg.edit_text(
        f"✅ *Рассылка завершена!*\n\n"
        f"📤 Отправлено: {success}\n"
        f"❌ Ошибок: {fail}\n"
        f"👥 Всего: {len(user_data)}",
        parse_mode='Markdown'
    )

# ========== КОМАНДА ДЛЯ СБОРА ПОЛЬЗОВАТЕЛЕЙ ИЗ КАНАЛА ==========
async def collect_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Собрать всех пользователей из канала (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != 5408585719:
        await update.message.reply_text("❌ Только для админа!")
        return
    
    await update.message.reply_text("📢 *Начинаю сбор пользователей из канала @frestarsbotg...*\n⏳ Может занять минуту.", parse_mode='Markdown')
    
    from telethon import TelegramClient
    import json
    
    api_id = 36873949
    api_hash = '999a8a42fcc1df357ab9b8d85d37121c'
    phone = '+79229486709'
    
    client = TelegramClient('session_collector', api_id, api_hash)
    
    try:
        await client.start(phone)
        channel = await client.get_entity('@frestarsbotg')
        
        users = []
        async for user in client.iter_participants(channel):
            if not user.bot:
                users.append(user.id)
        
        with open('channel_users.json', 'w') as f:
            json.dump(users, f)
        
        await update.message.reply_text(
            f"✅ *Готово!*\n\n👥 Собрано: {len(users)} пользователей\n💾 Сохранено в `channel_users.json`",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()
# ================================================================
