import random
from telegram import Update
from telegram.ext import ContextTypes
from config import MINI_GAMES, WIN_PROBABILITY
from database import get_user_data, update_user_data, update_games_stats, get_games_stats
from keyboards import games_keyboard, play_again_keyboard, main_menu_keyboard, coin_choice_keyboard, number_choice_keyboard
from logger import log_user_action

# Хранилище для текущих игр
user_game_states = {}

async def handle_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    log_user_action(user_id, username, "ENTER_GAMES")
    
    games_text = """
🎮 *МИНИ-ИГРЫ НА ЗВЁЗДЫ* 🎮

*Доступные игры:*

🎲 *Кости* - ставь от 5 до 50 звезд
🪙 *Монетка* - ставь от 3 до 50 звезд  
🎰 *Слоты* - ставь от 10 до 50 звезд
🔢 *Угадай число* - ставь от 5 до 50 звезд

*Выбирай игру и удачи!* 🍀
"""
    
    await update.message.reply_text(
        games_text,
        reply_markup=games_keyboard(),
        parse_mode='Markdown'
    )

async def handle_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if context.args:
        try:
            bet = int(context.args[0])
            game_config = MINI_GAMES["dice"]
            
            # Проверяем ставку
            if bet < game_config["min_bet"]:
                await update.message.reply_text(
                    f"❌ Минимальная ставка: {game_config['min_bet']} звезд",
                    reply_markup=games_keyboard()
                )
                return
            if bet > game_config["max_bet"]:
                await update.message.reply_text(
                    f"❌ Максимальная ставка: {game_config['max_bet']} звезд",
                    reply_markup=games_keyboard()
                )
                return
            
            # Проверяем баланс
            user_data = get_user_data(user_id)
            if user_data['stars'] < bet:
                await update.message.reply_text(
                    "❌ Недостаточно звезд для ставки!",
                    reply_markup=games_keyboard()
                )
                return
            
            # Играем!
            if random.random() < WIN_PROBABILITY:
                # ВЫИГРЫШ
                win_amount = bet * game_config["win_multiplier"]
                update_user_data(user_id, username, win_amount - bet)
                update_games_stats(user_id, bet, win_amount)
                
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                
                result_text = f"""
🎲 *ИГРА В КОСТИ* 🎲

🎯 *Ваша ставка:* {bet}⭐
🎲 *Бросок:* {dice1} + {dice2} = {dice1 + dice2}

🎉 *ВЫ ВЫИГРАЛИ!* 🎉
💫 *Выигрыш:* +{win_amount} звезд!

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐
"""
                log_user_action(user_id, username, "DICE_WIN", f"Bet: {bet}, Win: {win_amount}")
                
            else:
                # ПРОИГРЫШ
                update_user_data(user_id, username, -bet)
                update_games_stats(user_id, bet, 0)
                
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                
                result_text = f"""
🎲 *ИГРА В КОСТИ* 🎲

🎯 *Ваша ставка:* {bet}⭐
🎲 *Бросок:* {dice1} + {dice2} = {dice1 + dice2}

😔 *ВЫ ПРОИГРАЛИ*
💸 *Проигрыш:* -{bet} звезд

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐

*Попробуйте еще раз!* 🍀
"""
                log_user_action(user_id, username, "DICE_LOSE", f"Bet: {bet}, Lose")
            
            await update.message.reply_text(
                result_text,
                reply_markup=play_again_keyboard(),
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверная ставка! Используйте числа.",
                reply_markup=games_keyboard()
            )
    else:
        # Показываем правила игры
        game_config = MINI_GAMES["dice"]
        await update.message.reply_text(
            f"🎲 *ИГРА В КОСТИ*\n\n"
            f"🎯 *Правила:* {game_config['description']}\n\n"
            f"💰 *Ставки:* от {game_config['min_bet']} до {game_config['max_bet']} звезд\n"
            f"🎁 *Выигрыш:* x{game_config['win_multiplier']} от ставки\n"
            f"📊 *Шанс выигрыша:* 25%\n\n"
            f"*Чтобы играть, напишите:*\n"
            f"`/dice СТАВКА`\n\n"
            f"*Пример:* `/dice 10`",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )

async def handle_coin_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if context.args:
        try:
            bet = int(context.args[0])
            game_config = MINI_GAMES["coin"]
            
            # Проверки ставки
            if bet < game_config["min_bet"] or bet > game_config["max_bet"]:
                await update.message.reply_text(
                    f"❌ Ставка должна быть от {game_config['min_bet']} до {game_config['max_bet']} звезд",
                    reply_markup=games_keyboard()
                )
                return
            
            user_data = get_user_data(user_id)
            if user_data['stars'] < bet:
                await update.message.reply_text(
                    "❌ Недостаточно звезд!",
                    reply_markup=games_keyboard()
                )
                return
            
            # Сохраняем ставку для выбора
            user_game_states[user_id] = {"game": "coin", "bet": bet}
            
            await update.message.reply_text(
                f"🪙 *ИГРА В МОНЕТКУ*\n\n"
                f"🎯 *Ваша ставка:* {bet}⭐\n\n"
                f"*Выбери сторону монетки:*",
                reply_markup=coin_choice_keyboard(),
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверная ставка! Используйте числа.",
                reply_markup=games_keyboard()
            )
    else:
        game_config = MINI_GAMES["coin"]
        await update.message.reply_text(
            f"🪙 *ИГРА В МОНЕТКУ*\n\n"
            f"🎯 *Правила:* {game_config['description']}\n\n"
            f"💰 *Ставки:* от {game_config['min_bet']} до {game_config['max_bet']} звезд\n"
            f"🎁 *Выигрыш:* x{game_config['win_multiplier']} от ставки\n"
            f"📊 *Шанс выигрыша:* 25%\n\n"
            f"*Чтобы играть, напишите:*\n"
            f"`/coin СТАВКА`\n\n"
            f"*Пример:* `/coin 10`",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )

async def handle_coin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if user_id not in user_game_states or user_game_states[user_id]["game"] != "coin":
        await update.message.reply_text(
            "❌ Сначала сделайте ставку командой `/coin СТАВКА`",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    user_choice = update.message.text
    bet = user_game_states[user_id]["bet"]
    
    # Определяем выбор пользователя
    if "Орел" in user_choice:
        player_choice = "ОРЁЛ"
        player_emoji = "🦅"
    else:
        player_choice = "РЕШКА" 
        player_emoji = "👑"
    
    # Генерируем результат
    coin_result = random.choice(["ОРЁЛ", "РЕШКА"])
    coin_emoji = "🦅" if coin_result == "ОРЁЛ" else "👑"
    
    # Проверяем выигрыш
    if player_choice == coin_result:
        # ВЫИГРЫШ
        game_config = MINI_GAMES["coin"]
        win_amount = bet * game_config["win_multiplier"]
        update_user_data(user_id, username, win_amount - bet)
        update_games_stats(user_id, bet, win_amount)
        
        result_text = f"""
🪙 *ИГРА В МОНЕТКУ* 🪙

🎯 *Ваша ставка:* {bet}⭐
🤔 *Ваш выбор:* {player_choice} {player_emoji}
🎲 *Результат:* {coin_result} {coin_emoji}

🎉 *ВЫ ВЫИГРАЛИ!* 🎉
💫 *Выигрыш:* +{win_amount} звезд!

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐
"""
        log_user_action(user_id, username, "COIN_WIN", f"Bet: {bet}, Win: {win_amount}")
    else:
        # ПРОИГРЫШ
        update_user_data(user_id, username, -bet)
        update_games_stats(user_id, bet, 0)
        
        result_text = f"""
🪙 *ИГРА В МОНЕТКУ* 🪙

🎯 *Ваша ставка:* {bet}⭐
🤔 *Ваш выбор:* {player_choice} {player_emoji}
🎲 *Результат:* {coin_result} {coin_emoji}

😔 *ВЫ ПРОИГРАЛИ*
💸 *Проигрыш:* -{bet} звезд

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐

*Попробуйте еще раз!* 🍀
"""
        log_user_action(user_id, username, "COIN_LOSE", f"Bet: {bet}, Lose")
    
    # Удаляем состояние игры
    del user_game_states[user_id]
    
    await update.message.reply_text(
        result_text,
        reply_markup=play_again_keyboard(),
        parse_mode='Markdown'
    )

async def handle_slots_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if context.args:
        try:
            bet = int(context.args[0])
            game_config = MINI_GAMES["slots"]
            
            if bet < game_config["min_bet"] or bet > game_config["max_bet"]:
                await update.message.reply_text(
                    f"❌ Ставка должна быть от {game_config['min_bet']} до {game_config['max_bet']} звезд",
                    reply_markup=games_keyboard()
                )
                return
            
            user_data = get_user_data(user_id)
            if user_data['stars'] < bet:
                await update.message.reply_text(
                    "❌ Недостаточно звезд!",
                    reply_markup=games_keyboard()
                )
                return
            
            # Генерируем слоты
            symbols = ["🍒", "🍋", "🍊", "⭐", "🔔", "💎"]
            slot1 = random.choice(symbols)
            slot2 = random.choice(symbols)
            slot3 = random.choice(symbols)
            
            # Проверяем выигрыш (3 одинаковых символа)
            if slot1 == slot2 == slot3:
                win_amount = bet * game_config["win_multiplier"]
                update_user_data(user_id, username, win_amount - bet)
                update_games_stats(user_id, bet, win_amount)
                
                result_text = f"""
🎰 *ИГРА В СЛОТЫ* 🎰

🎯 *Ваша ставка:* {bet}⭐
🎰 *Результат:* [{slot1}] [{slot2}] [{slot3}]

🎉 *ДЖЕКПОТ! 3 ОДИНАКОВЫХ!* 🎉
💫 *Выигрыш:* +{win_amount} звезд!

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐
"""
                log_user_action(user_id, username, "SLOTS_WIN", f"Bet: {bet}, Win: {win_amount}")
            else:
                update_user_data(user_id, username, -bet)
                update_games_stats(user_id, bet, 0)
                
                result_text = f"""
🎰 *ИГРА В СЛОТЫ* 🎰

🎯 *Ваша ставка:* {bet}⭐
🎰 *Результат:* [{slot1}] [{slot2}] [{slot3}]

😔 *ПРОИГРЫШ*
💸 *Проигрыш:* -{bet} звезд

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐

*Крутите еще!* 🍀
"""
                log_user_action(user_id, username, "SLOTS_LOSE", f"Bet: {bet}, Lose")
            
            await update.message.reply_text(
                result_text,
                reply_markup=play_again_keyboard(),
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверная ставка! Используйте числа.",
                reply_markup=games_keyboard()
            )
    else:
        game_config = MINI_GAMES["slots"]
        await update.message.reply_text(
            f"🎰 *ИГРА В СЛОТЫ*\n\n"
            f"🎯 *Правила:* {game_config['description']}\n\n"
            f"💰 *Ставки:* от {game_config['min_bet']} до {game_config['max_bet']} звезд\n"
            f"🎁 *Выигрыш:* x{game_config['win_multiplier']} от ставки (только 3 одинаковых символа!)\n"
            f"📊 *Шанс выигрыша:* 25%\n\n"
            f"*Чтобы играть, напишите:*\n"
            f"`/slots СТАВКА`\n\n"
            f"*Пример:* `/slots 20`",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )

async def handle_number_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if context.args:
        try:
            bet = int(context.args[0])
            game_config = MINI_GAMES["number"]
            
            if bet < game_config["min_bet"] or bet > game_config["max_bet"]:
                await update.message.reply_text(
                    f"❌ Ставка должна быть от {game_config['min_bet']} до {game_config['max_bet']} звезд",
                    reply_markup=games_keyboard()
                )
                return
            
            user_data = get_user_data(user_id)
            if user_data['stars'] < bet:
                await update.message.reply_text(
                    "❌ Недостаточно звезд!",
                    reply_markup=games_keyboard()
                )
                return
            
            # Сохраняем ставку для выбора числа
            user_game_states[user_id] = {"game": "number", "bet": bet}
            
            await update.message.reply_text(
                f"🔢 *УГАДАЙ ЧИСЛО*\n\n"
                f"🎯 *Ваша ставка:* {bet}⭐\n\n"
                f"*Выбери число от 1 до 5:*",
                reply_markup=number_choice_keyboard(),
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверная ставка! Используйте числа.",
                reply_markup=games_keyboard()
            )
    else:
        game_config = MINI_GAMES["number"]
        await update.message.reply_text(
            f"🔢 *УГАДАЙ ЧИСЛО*\n\n"
            f"🎯 *Правила:* {game_config['description']}\n\n"
            f"💰 *Ставки:* от {game_config['min_bet']} до {game_config['max_bet']} звезд\n"
            f"🎁 *Выигрыш:* x{game_config['win_multiplier']} от ставки\n"
            f"📊 *Шанс выигрыша:* 25%\n\n"
            f"*Чтобы играть, напишите:*\n"
            f"`/number СТАВКА`\n\n"
            f"*Пример:* `/number 15`",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )

async def handle_number_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name
    
    if user_id not in user_game_states or user_game_states[user_id]["game"] != "number":
        await update.message.reply_text(
            "❌ Сначала сделайте ставку командой `/number СТАВКА`",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    user_choice_text = update.message.text
    bet = user_game_states[user_id]["bet"]
    
    # Определяем выбор пользователя
    number_map = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5}
    player_choice = number_map.get(user_choice_text, 0)
    
    if player_choice == 0:
        await update.message.reply_text(
            "❌ Неверный выбор! Выбери число от 1 до 5.",
            reply_markup=number_choice_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Генерируем случайное число
    random_number = random.randint(1, 5)
    
    # Проверяем выигрыш
    if player_choice == random_number:
        # ВЫИГРЫШ
        game_config = MINI_GAMES["number"]
        win_amount = bet * game_config["win_multiplier"]
        update_user_data(user_id, username, win_amount - bet)
        update_games_stats(user_id, bet, win_amount)
        
        result_text = f"""
🔢 *УГАДАЙ ЧИСЛО* 🔢

🎯 *Ваша ставка:* {bet}⭐
🤔 *Ваш выбор:* {player_choice}
🎲 *Загаданное число:* {random_number} 🎯

🎉 *ВЫ УГАДАЛИ!* 🎉
💫 *Выигрыш:* +{win_amount} звезд!

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐
"""
        log_user_action(user_id, username, "NUMBER_WIN", f"Bet: {bet}, Win: {win_amount}")
    else:
        # ПРОИГРЫШ
        update_user_data(user_id, username, -bet)
        update_games_stats(user_id, bet, 0)
        
        result_text = f"""
🔢 *УГАДАЙ ЧИСЛО* 🔢

🎯 *Ваша ставка:* {bet}⭐
🤔 *Ваш выбор:* {player_choice}
🎲 *Загаданное число:* {random_number} ❌

😔 *НЕ УГАДАЛИ*
💸 *Проигрыш:* -{bet} звезд

💰 *Баланс:* {get_user_data(user_id)['stars']:.1f}⭐

*Попробуйте снова!* 🍀
"""
        log_user_action(user_id, username, "NUMBER_LOSE", f"Bet: {bet}, Lose")
    
    # Удаляем состояние игры
    del user_game_states[user_id]
    
    await update.message.reply_text(
        result_text,
        reply_markup=play_again_keyboard(),
        parse_mode='Markdown'
    )

async def handle_games_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = get_games_stats(user_id)
    
    if stats["games_played"] == 0:
        await update.message.reply_text(
            "📊 *Вы еще не играли в мини-игры!*\n\n"
            "🎮 Попробуйте одну из игр и здесь появится ваша статистика!",
            reply_markup=games_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    profit = stats["total_win"] - stats["total_bet"]
    profit_text = "📈" if profit >= 0 else "📉"
    
    stats_text = f"""
📊 *ВАША СТАТИСТИКА В ИГРАХ* 📊

🎮 *Игр сыграно:* {stats['games_played']}
💰 *Всего поставлено:* {stats['total_bet']}⭐
🎁 *Всего выиграно:* {stats['total_win']}⭐
{profit_text} *Чистая прибыль:* {profit}⭐

"""
    if stats["games_played"] > 0:
        win_rate = (stats["total_win"] / stats["total_bet"]) * 100
        stats_text += f"📈 *Процент возврата:* {win_rate:.1f}%"
    
    await update.message.reply_text(
        stats_text,
        reply_markup=games_keyboard(),
        parse_mode='Markdown'
    )