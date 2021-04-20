# -*- coding: utf-8 -*-
"""
BookBot is telegram bot, based on telegram API and MongoDB.
His objective is to send interesting quotes from books to users.txt.
"""

import os
import random
import time
import traceback
from threading import Thread

import pymysql
import schedule
import telebot
from telebot import types

# [BUILT-INS]
token = os.environ.get("TG_TOKEN")
secret = os.environ.get('SQL_ROOT_PASSWORD')
bot = telebot.TeleBot(token)


def init_sql():
    global sql
    try:
        sql.close()
    except:  # In case connection isn't opened yet.
        pass
    sql = pymysql.connect(host='localhost', user='root', password=secret, database='bookbot', autocommit=True)
    sql.cursor().execute("SELECT * FROM wake_up;")
    sql.cursor().close()


# [VARIABLES]
cancel_button = types.InlineKeyboardMarkup()
key_cancel = types.InlineKeyboardButton(text='Отменить', callback_data='cancel')
cancel_button.add(key_cancel)
callback_cancel = {}


# [CLASSES]
# Async thread (time scheduler)
class AsyncScheduler(Thread):
    def __init__(self, name):
        Thread.__init__(self)
        self.name = name

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(59)


class Quote:
    """Class for quotes and everything about them"""

    def __init__(self):
        with sql.cursor() as cur:
            cur.execute("SELECT count(id) FROM quotes;")
            self.est_quotes = int(cur.fetchone()[0])
            cur.close()

    def stop(self, chat_id):
        """Moves chat to 'stopped' list, so he won't receive scheduled quotes"""
        with sql.cursor() as cur:
            cur.execute(f"SELECT stopped FROM users WHERE id = '{chat_id}'")
            if cur.fetchone()[0] == 0:
                cur.execute(f"UPDATE users SET stopped = 1 WHERE id = '{chat_id}'")
                bot.send_message(chat_id,
                                 '<b>❌ Рассылка цитат приостановлена!\n</b> \nЧтобы возобновить напишите /resume',
                                 parse_mode='HTML')
            else:
                bot.send_message(chat_id,
                                 '<b>⚠ Рассылка цитат уже приостановлена для вас!\n</b> \nЧтобы возобновить напишите /resume',
                                 parse_mode='HTML')
            cur.close()

    def resume(self, chat_id):
        """Removes user from 'stopped' list"""
        with sql.cursor() as cur:
            cur.execute(f"SELECT stopped FROM users WHERE id = '{chat_id}'")
            if cur.fetchone()[0] == 1:
                cur.execute(f"UPDATE users SET stopped = 0 WHERE id = '{chat_id}'")
                bot.send_message(chat_id, '<b>✔ Рассылка цитат возобновлена!</b>',
                                 parse_mode='HTML')
            else:
                bot.send_message(chat_id, '<b>⚠ Вы еще не приостанавливали рассылку!</b>',
                                 parse_mode='HTML')
            cur.close()

    def check(self, user: str, check=True) -> tuple:
        """Checks for quote available for {user}"""
        with sql.cursor() as cur:
            cur.execute(f"SELECT used_quotes FROM quotes_query WHERE user_id = '{user}'")
            used_q = cur.fetchone()[0] or ' '
            if len(used_q) >= 255:
                # removes user id from DB if there is no more available quotes for user
                cur.execute(f"UPDATE quotes_query SET used_quotes = null WHERE user_id = '{user}'")
            if used_q == ' ':
                used_q = ''
            while True:
                number = str(random.randint(1, self.est_quotes))
                if check and number in used_q.split():
                    continue
                cur.execute(f"SELECT * FROM quotes WHERE id = {number};")
                quote = cur.fetchone()
                cur.execute(f"UPDATE quotes_query SET used_quotes = '{used_q + number + ' '}' WHERE user_id = '{user}'")
                cur.close()
                return quote

    def random(self, user: str, checking=False):
        """ Sends random quote for user.
            If checking == False, it does not check for the presence of id in the database.
        """
        quo = self.check(user, check=checking)
        keyboard = types.InlineKeyboardMarkup()
        key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quo[4])
        keyboard.add(key_book)
        bot.send_message(user,
                         text=f'<i>{quo[1]}\n</i>\n<b>{quo[2]}</b>\n#{quo[3]}',
                         parse_mode='HTML', reply_markup=keyboard)

    def randoms(self, group: int):
        """Sends random quote for users.txt who aren't in 'stopped' list"""
        start_time = time.time()
        counter = 0
        r = read_users(group)
        print("=================================")
        for user in r:
            try:
                self.random(user[0], True)
                print(f"Latency #{counter}: {str(time.time() - start_time)[:4]} seconds")
            except telebot.apihelper.ApiTelegramException as user_e:
                print(f"Bad ID ({user[0]}):", user_e)
            except Exception:
                traceback.print_exc()
            finally:
                counter += 1

    def add(self, message):
        """Adds a quote from user to file, for further verification."""
        global callback_cancel
        if callback_cancel.get(message.chat.id):
            callback_cancel[message.chat.id] = False
            return
        if message.text.count('%') != 2:
            global cancel_button
            bot.send_message(message.chat.id,
                             '⚠ <b>Неправильный формат!</b>\nОтправьте цитату в таком виде:\n\n'
                             '<i>текст_цитаты%книга%автор</i>\n\n'
                             '<i>Что хочешь помнить, то всегда помнишь.%Вино из одуванчиков%Рэй Брэдбери</i>',
                             parse_mode='HTML', reply_markup=cancel_button)
            return bot.register_next_step_handler(message, self.add)
        with open('admin/quotes_4_add.txt', 'a', encoding='utf-8') as verification:
            verification.write(message.text + '%\n')
        bot.send_message(message.chat.id,
                         '✔ <i>Спасибо за помощь в развитии бота! Ваша цитата была отправлена на проверку'
                         ' и будет добавлена в течении 48 часов!</i>',
                         parse_mode='HTML')
        print(f'{message.chat.id} (@{message.from_user.username or message.chat.title}) запросил добавление цитаты!')


class UserInGroup(Exception):
    def __init__(self, text='user is already in group.'):
        self.txt = text


# [INITIALIZING]
scheduler = AsyncScheduler("Time check")
try:
    scheduler.start()
except Exception as e:
    traceback.print_exc()
init_sql()
quotes = Quote()
schedule.every().day.at('14:00').do(quotes.randoms, group=1)
schedule.every().day.at('12:00').do(quotes.randoms, group=2)
schedule.every().day.at('20:00').do(quotes.randoms, group=2)
schedule.every(20).minutes.do(init_sql)


# [FUNCTIONAL]
def read_users(group=-1, names=False, stopped=False) -> tuple[tuple]:
    """Reading users from db"""
    with sql.cursor() as cur:
        if stopped:
            command = f"SELECT {'username, ' if names else ''}id FROM users" \
                      f"{f' WHERE group_number = {group}' if group != -1 else ''};"
        else:
            command = f"SELECT {'username, ' if names else ''}id FROM users WHERE stopped = 0" \
                      f"{f' AND group_number = {group}' if group != -1 else ''};"
        cur.execute(command)
        r = cur.fetchall()
        cur.close()
    return r


def help_command(chat_id):
    """Help with all commands"""
    commands = ('<b>Список команд:\n'
                '</b>\n/random<i> - случайная цитата в любое время суток\n'
                '</i>\n/stop<i> - приостановить рассылку\n'
                '</i>\n/resume<i> - возобновить рассылку\n'
                '</i>\n/report<i> - сообщить о проблеме или предложении\n'
                '</i>\n/add<i> - предложить свою цитату\n'
                '</i>\n/quotes<i> - сменить частоту получения цитат</i>'
                )
    bot.send_message(chat_id, text=commands, parse_mode='HTML')


def report(message):
    """Report about problem or idea from user to admin"""
    if message.from_user.id != message.chat.id:
        bot.send_message(message.chat.id, text='<i><b>Данная функция недоступна в групповых чатах!</b></i>',
                         parse_mode='HTML')
        return
    keyboard = types.InlineKeyboardMarkup()
    key_report = types.InlineKeyboardButton(text='❗ Проблема/Ошибка', callback_data='report')
    keyboard.add(key_report)  # добавляем кнопку в клавиатуру
    key_support = types.InlineKeyboardButton(text='💡 Идея/Предложение', callback_data='support')
    keyboard.add(key_support)
    bot.send_message(message.from_user.id, text='О чем вы хотите <b>сообщить</b>?', parse_mode='HTML',
                     reply_markup=keyboard)


def send(user: str, message):
    """Sends message requested from admin to user, works either with id or """
    try:
        user_id = user
        if not user.isdigit():
            users_list = dict(read_users(names=True, stopped=True))
            user_id = users_list[user]
        bot.send_message(user_id,
                         f'<b>Сообщение от администрации!</b>\n\n<i>{message}</i>',
                         parse_mode='HTML'
                         )
        print(f'Sent message to {user_id}:\n{message}')
    except telebot.apihelper.ApiTelegramException as user_e:
        print(f"Bad USER ({user}):", user_e)
    except Exception as other_e:
        print(other_e)


def change_group(chat_id, group: int):
    """Changes user's time for quote"""
    with sql.cursor() as cur:
        cur.execute(f"SELECT group_number FROM users WHERE id = '{chat_id}';")
        before = cur.fetchone()[0]
        if group == before:
            raise UserInGroup()
        result = cur.execute(f"UPDATE users SET group_number = {group} WHERE id = '{chat_id}';")
        if result == 1:
            print(f'{chat_id} changed his group from {before} to {group}.')
        else:
            print(f"Error occurred while changing {chat_id}'s group from {before} to {group}.")
        cur.close()


def promo():
    """Sends a little promotional message for all users.txt (except my gf)"""
    r = read_users()
    for user_id in r:
        if user_id[0] == '1103761115':
            continue
        try:
            bot.send_message(user_id[0],
                             text=f'Если тебе нравится наш бот, пожалуйста, не жадничай и поделись им с друзьями! 😉\nЯ буду очень рад!',
                             parse_mode='HTML', disable_notification=True)
        except telebot.apihelper.ApiTelegramException as user_e:
            print(f"Bad USER ({user_id[0]}):", user_e)


schedule.every(2).days.at('16:00').do(promo)


# problem handler
def report_send(message):
    global callback_cancel
    if callback_cancel.get(message.chat.id):
        callback_cancel[message.chat.id] = False
        return
    bot.send_message(977341432,
                     f'❗ <b>Поступила жалоба:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.chat.id,
                     f'✔ <b>Жалоба успешно подана на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')


# idea handler
def support_send(message):
    global callback_cancel
    if callback_cancel.get(message.chat.id):
        callback_cancel[message.chat.id] = False
        return
    bot.send_message(977341432,
                     f'💡 <b>Поступило предложение:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.chat.id,
                     f'✔ <b>Предложение успешно подано на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')


# [ADMIN]
@bot.message_handler(commands=['gift', 'promo', 'send'])
def admin(message):
    """Admin message handler, answers on admin requests"""
    print('Admin command execution...')
    if message.chat.id != 977341432:
        print('False: Non-admin request')
        return
    if message.text.startswith('/gift'):
        quotes.randoms(int(message.text[-1]))
        print("Succeed")
    elif message.text.startswith('/promo'):
        promo()
        print("Succeed")
    elif message.text.startswith('/send'):
        command = message.text.split()[1:]
        send(command[0], ' '.join(command[1:]))
        print("Succeed")
    else:
        print('Wrong code')


# [START]
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     '<b>Привет, я BookBot! 📚\n</b> \n<i>С данного момента, тебе каждый день будут приходить случайные цитаты. Для того, чтобы узнать побольше о функционале бота - напиши /help \n</i>\nА также, в скором времени появится функция выбора любимых авторов, технология подбора цитат для Вас индивидуально, и много других интересных фишек! 😉',
                     parse_mode='HTML')
    with sql.cursor() as cur:
        check = cur.execute(f"SELECT id FROM users WHERE id = '{chat_id}'")
        if check:
            return
        cur.execute(
            f'INSERT INTO users(username, id) VALUES ("{message.chat.username or message.chat.title}", "{chat_id}");')
        print(message.chat.username or message.chat.title, 'connected to bot.')
        cur.close()
    quote = quotes.check(str(chat_id))
    keyboard = types.InlineKeyboardMarkup()
    key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quote[4])
    keyboard.add(key_book)
    bot.send_message(chat_id,
                     text=f'Держи свою первую цитату!\n\n<i>{quote[1]}\n</i>\n<b>{quote[2]}</b>\n#{quote[3]}',
                     parse_mode='HTML', reply_markup=keyboard)


# user commands handler
@bot.message_handler(commands=['stop', 'resume', 'help', 'report', 'random', 'add', 'quotes'])
def commands_handler(message):
    command = message.text
    if command.startswith('/stop'):
        quotes.stop(message.chat.id)
    elif command.startswith('/resume'):
        quotes.resume(message.chat.id)
    elif command.startswith('/help'):
        help_command(message.chat.id)
    elif command.startswith('/quotes'):
        group = types.InlineKeyboardMarkup()
        group.add(types.InlineKeyboardButton(text='14.00 (UTC+6)', callback_data='1'))
        group.add(types.InlineKeyboardButton(text='12.00 + 20.00 (UTC+6)', callback_data='2'))
        bot.send_message(message.chat.id,
                         '<b>Смена частоты получения цитат:</b>',
                         parse_mode='HTML', reply_markup=group)
    elif command.startswith('/report'):
        report(message)
    elif command.startswith('/random'):
        try:
            quotes.random(str(message.chat.id), False)
        except Exception:
            pass
    elif command.startswith('/add'):
        bot.send_message(message.chat.id,
                         '📚 Отправьте цитату в таком виде:\n\n'
                         '<i>текст_цитаты%книга%автор</i>\n\n'
                         '<i>Что хочешь помнить, то всегда помнишь.%Вино из одуванчиков%Рэй Брэдбери</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(message, quotes.add)
    else:
        print('Wrong code')


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global cancel_button
    if call.data == "report":
        bot.send_message(call.message.chat.id,
                         '<i>Опишите проблему, Ваше сообщение будет доставлено администрации и принято на рассмотрение!\n</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(call.message, report_send)

    elif call.data == "support":
        bot.send_message(call.message.chat.id,
                         '<i>Опишите Вашу идею, сообщение будет доставлено администрации и принято на рассмотрение!\n</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(call.message, support_send)

    elif call.data in '12':
        try:
            change_group(str(call.message.chat.id), int(call.data))
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id,
                             '✔ <b>Вы успешно сменили частоту получения цитат!</b>',
                             parse_mode='HTML')
        except UserInGroup:
            bot.send_message(call.message.chat.id,
                             '⚠ <b>Вы уже находитесь в этой группе!</b>',
                             parse_mode='HTML')
        except Exception as other_e:
            print(other_e)
    elif call.data == 'cancel':
        global callback_cancel
        callback_cancel.update({call.message.chat.id: True})
        bot.send_message(call.message.chat.id,
                         '<b><i>Отменено!</i></b>',
                         parse_mode='HTML')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


# users0 = read_users(0)
# for _ in users0:
#     try:
#         bot.send_message(_,
#                          '⚠ <b>ВНИМАНИЕ!</b>\n\n'
#                          'Добавлена новая команда!\n'
#                          'Чтобы получать 2 цитаты в день, напишите /quotes 2! Подробнее о команде в /help',
#                          parse_mode='HTML')
#     except Exception:
#         continue
# quotes.randoms(0)

try_count = 1
last_exc = time.time()
while True:
    try:
        init_sql()
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        try_count += 1 if time.time() - last_exc < 15 else -try_count
        with open("admin/connection_log.txt", "a") as dump:
            dump.write("==============================\nConnection ERROR: " + traceback.format_exc())
        last_exc = time.time()

        print("Reconnecting:", try_count)
