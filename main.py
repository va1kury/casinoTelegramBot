import telebot
import config
import sqlite3
import threading
from telebot import types


bot = telebot.TeleBot(config.token)
db = sqlite3.connect("database.db", check_same_thread=False)
sql = db.cursor()
lock = threading.Lock()


#initialize database
sql.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT, name TEXT, link TEXT, balance BIGINT, deposit BIGINT, cashout BIGINT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS game1 (id BIGINT)""")
db.commit()


def update_database_user_info(message):
    userid = message.from_user.id
    userlink = message.from_user.username
    username = message.from_user.first_name

    sql.execute(f"SELECT id FROM users WHERE id = {userid}")
    if sql.fetchone() is None: #если пользователя нет в бд - добавляем его
        sql.execute(f"INSERT INTO users VALUES ({userid}, '{username}', '@{userlink}', '0', '0', '0')")
        db.commit()
    else: #или обновляем данные о пользователе
        sql.execute(f"SELECT name FROM users WHERE id = {userid}")
        if sql.fetchone()[0] != username:
            sql.execute(f"UPDATE users SET name = '{username}' WHERE id = {userid}")
            db.commit()
        sql.execute(f"SELECT link FROM users WHERE id = {userid}")
        if sql.fetchone()[0] != userlink:
            sql.execute(f"UPDATE users SET link = '@{userlink}' WHERE id = {userid}")
            db.commit()


@bot.message_handler(commands=["start"])
def start_option(message):
    userid = message.from_user.id
    userlink = message.from_user.username
    username = message.from_user.first_name

    update_database_user_info(message)

    bot.send_message(message.chat.id,
                     f"Привет, {username}! Этот бот позволяет сыграть в раличные игры с другими пользователями.",
                     parse_mode="Markdown")


@bot.message_handler(commands=["game1"])
def game1_start(message):
    bot.send_message(message.chat.id, "Поиск оппонента...")

    # проверка, есть уже пользователь в списке ищущих игру, если нет - добавляем
    sql.execute(f"SELECT id FROM game1 WHERE id = {message.from_user.id}")
    if sql.fetchone() is None:
        db.execute(f"INSERT INTO game1 VALUES ({message.from_user.id})")
        db.commit()

    game1_looking_for_opponent(message)


def game1_looking_for_opponent(message):
    for i in db.execute(f"SELECT id FROM game1 WHERE id = {message.from_user.id}"):
        print(i)


@bot.message_handler(commands=["profile"])
def profile_status(message):
    balance = db.execute(f"SELECT balance FROM users WHERE id = {message.from_user.id}").fetchone()[0]
    deposit = db.execute(f"SELECT deposit FROM users WHERE id = {message.from_user.id}").fetchone()[0]
    cashout = db.execute(f"SELECT cashout FROM users WHERE id = {message.from_user.id}").fetchone()[0]
    rmk = types.InlineKeyboardMarkup()
    item_deposit = types.InlineKeyboardButton(text="Пополнить баланс 🚀", callback_data="balance_deposit")
    item_cashout = types.InlineKeyboardButton(text="Вывести 💎", callback_data="balance_cashout")
    rmk.add(item_deposit, item_cashout)
    bot.send_message(message.chat.id,
                     f"♦️ | Твой профиль\n\n💸 | Баланс: {balance}\n👑 | Депозит: {deposit}\n🎁 | Выведено: {cashout}",
                     reply_markup=rmk,
                     parse_mode="Markdown")

def profile_deposit_step_1(message):
    try:
        #Обновление баланса пользователя в БД после команды "пополнить баланс" и ввода суммы
        user_id = message.chat.id
        old_user_balance = db.execute(f"SELECT balance FROM users WHERE id = {user_id}").fetchone()[0]
        new_user_balance = old_user_balance + int(message.text)
        old_user_deposit = db.execute(f"SELECT deposit FROM users WHERE id = {user_id}").fetchone()[0]
        new_user_deposit = old_user_deposit + int(message.text)
        db.execute(f"UPDATE users SET balance = {new_user_balance} WHERE id = {user_id}")
        db.execute(f"UPDATE users SET deposit = {new_user_deposit} WHERE id = {user_id}")
        db.commit()
    except:
        bot.send_message(message.chat.id, "Ошибка2!")


@bot.callback_query_handler(lambda call: call.data == "balance_deposit" or call.data == "balance_cashout")
def profile_change_balance(call):
    try:
        if call.data == "balance_deposit":
            msg = bot.send_message(call.message.chat.id, f"*Введите сумму, которую хотите пополнить:*", parse_mode="Markdown")
            bot.register_next_step_handler(msg, profile_deposit_step_1)
        elif call.data == "balance_cashout":
            pass
    except:
        bot.send_message(call.message.chat.id, "Ошибка1!")


@bot.message_handler(commands=["cashout"])
def cashout(message):
    pass


bot.infinity_polling(none_stop=True, interval=0)