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
import simple_funcs as sf
import telebot
from telebot import types

# [BUILT-INS]
token = os.environ.get("TG_TOKEN")
secret = os.environ.get('SQL_ROOT_PASSWORD')
bot = telebot.TeleBot(token)


def sql_connect():
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

    @staticmethod
    def send(quo, chat):
        keyboard = types.InlineKeyboardMarkup()
        link = types.InlineKeyboardButton(text='📖' if quo[3] is not None else '🎬', 
                                          callback_data='link', url=quo[4])
        keyboard.add(link)
        quote = (f'<i>{quo[1]}\n</i>\n<b>{quo[2]}</b>\n#{quo[3]}' if quo[3] is not None else 
                 f'<i>{quo[1]}\n</i>\n<b>{quo[2]} ({quo[5]})</b>')
        bot.send_message(chat, text=quote, parse_mode='HTML', reply_markup=keyboard)

    @staticmethod
    def stop(chat_id):
        """Moves chat to 'stopped' list, so he won't receive scheduled quotes"""
        with sql.cursor() as cur:
            cur.execute(f"SELECT stopped FROM users WHERE id = '{chat_id}'")
            if cur.fetchone()[0] != 0:
                bot.send_message(chat_id,
                                 '<b>⚠ Рассылка цитат уже приостановлена для вас!\n</b> \nЧтобы возобновить напишите /resume',
                                 parse_mode='HTML')
                return

            cur.execute(f"UPDATE users SET stopped = 1 WHERE id = '{chat_id}'")
            bot.send_message(chat_id,
                             '<b>❌ Рассылка цитат приостановлена!\n</b> \nЧтобы возобновить напишите /resume',
                             parse_mode='HTML')

    @staticmethod
    def resume(chat_id):
        """Removes user from 'stopped' list"""
        with sql.cursor() as cur:
            cur.execute(f"SELECT stopped FROM users WHERE id = '{chat_id}'")
            if cur.fetchone()[0] != 1:
                bot.send_message(chat_id, '<b>⚠ Вы еще не приостанавливали рассылку!</b>',
                                 parse_mode='HTML')
                return
            cur.execute(f"UPDATE users SET stopped = 0 WHERE id = '{chat_id}'")
            bot.send_message(chat_id, '<b>✔ Рассылка цитат возобновлена!</b>',
                             parse_mode='HTML')

    def check(self, user: str, check=True) -> tuple:
        """Checks for quote available for {user}"""
        with sql.cursor() as cur:
            cur.execute(f"SELECT used_quotes FROM quotes_query WHERE user_id = '{user}'")
            used_quotes = cur.fetchone()[0]
            used_quotes = '' if not used_quotes else used_quotes
            if len(used_quotes) >= 251:
                # removes used quotes from DB if there is no more available quotes for user
                cur.execute(f"UPDATE quotes_query SET used_quotes = null WHERE user_id = '{user}'")
            while True:
                number = str(random.randint(1, self.est_quotes))
                result = cur.execute(f"SELECT * FROM quotes WHERE id = {number};")
                if result == 0:
                    print(f"Quote not found for {user}, last number is {number}")
                if check:
                    if number in used_quotes.split():
                        continue
                    cur.execute(
                        f"UPDATE quotes_query SET used_quotes = '{used_quotes + number + ' '}' WHERE user_id = '{user}'")
                cur.execute(f"SELECT * FROM quotes WHERE id = {number};")
                quote = cur.fetchone()
                if not quote:
                    print(f"Quote not found for {user}, last number is {number}")
                return quote

    def random(self, user: str, checking=False):
        """ Sends random quote for user.
            If checking == False, it does not check for the presence of id in the database.
        """
        quote = self.check(user, checking)
        self.send(quote, user)

    def randoms(self, group: int):
        """Sends random quotes for users"""
        start_time = time.time()
        counter = 0
        users = read_users(group)
        print("=================================")
        for user in users:
            try:
                self.random(user[0], True)
                print(f"Latency #{counter}: {str(time.time() - start_time)[:4]} seconds")
            except telebot.apihelper.ApiTelegramException as user_e:
                print(f"Bad ID ({user[0]}):", user_e)
            except Exception:
                traceback.print_exc()
            finally:
                counter += 1

    def add(self, message, full: bool = True, info=None, isfilm: bool = False):
        """Adds a quote from user to file, for further verification."""
        global callback_cancel
        if callback_cancel.get(message.chat.id):
            if full:
                callback_cancel[message.chat.id] = False
            return

        if isfilm:
            if full and (message.text.count('%') != 2 or len(message.text) < 15):
                bot.send_message(message.chat.id,
                                 '⚠ <b>Неправильный формат!</b>\nОтправьте цитату в таком виде:\n\n'
                                 '<i>текст_цитаты%фильм%год</i>\n\n'
                                 '<i>Хьюстон, у нас проблема.%Апполон 13%1995</i>',
                                 parse_mode='HTML', reply_markup=cancel_button)
                return bot.register_next_step_handler(message, self.add, full=full, info=info, isfilm=isfilm)
            if not full and info is not None:
                message.text += '%' + info
            file = 'quotes/f_to_add.txt'
        else:
            if full and (message.text.count('%') != 2 or len(message.text) < 25):
                bot.send_message(message.chat.id,
                                 '⚠ <b>Неправильный формат!</b>\nОтправьте цитату в таком виде:\n\n'
                                 '<i>текст_цитаты%книга%автор</i>\n\n'
                                 '<i>Что хочешь помнить, то всегда помнишь.%Вино из одуванчиков%Рэй Брэдбери</i>',
                                 parse_mode='HTML', reply_markup=cancel_button)
                return bot.register_next_step_handler(message, self.add, full=full, info=info, isfilm=isfilm)
            if not full and info is not None:
                message.text += '%' + info
            file = 'quotes/to_add.txt'
        with open(file, 'a', encoding='utf-8') as verification:
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
sql_connect()
quotes = Quote()
schedule.every().day.at('14:00').do(quotes.randoms, group=1)
schedule.every().day.at('12:00').do(quotes.randoms, group=2)
schedule.every().day.at('20:00').do(quotes.randoms, group=2)
schedule.every(20).minutes.do(sql_connect)


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
        return cur.fetchall()


def add_many_quotes(message, isfilm: bool = False):
    global callback_cancel
    if callback_cancel.get(message.chat.id):
        callback_cancel[message.chat.id] = False
        return
    if message.text.count('%') != 1 or len(message.text) < 6:
        if isfilm:
            bot.send_message(message.chat.id,
                         '⚠ <b>Неправильный формат! Попробуйте еще раз.</b>\n\n'
                         '<i>фильм%год</i>\n\n'
                         '<i>Апполон 13%1995</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
            return bot.register_next_step_handler(message, add_many_quotes, isfilm=True)
        bot.send_message(message.chat.id,
                         '⚠ <b>Неправильный формат! Попробуйте еще раз.</b>\n\n'
                         '<i>книга%автор</i>\n\n'
                         '<i>Вино из одуванчиков%Рэй Брэдбери</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        return bot.register_next_step_handler(message, add_many_quotes)
    bot.send_message(message.chat.id,
                     '📚 Теперь отправляйте текст ваших цитат! (по одной на сообщение)\n\n'
                     '<i>А когда закончите, нажмите отменить 😉</i>\n\n',
                     parse_mode='HTML', reply_markup=cancel_button)

    def tmp(msg, data, isfilm=False):
        if callback_cancel.get(data[1], None):
            callback_cancel[data[1]] = False
            return
        bot.register_next_step_handler(msg, quotes.add, full=False, info=data[0], isfilm=isfilm)
        return bot.register_next_step_handler(msg, tmp, isfilm=isfilm, data=data)

    info = [message.text.strip(), message.chat.id]
    tmp(message, info, isfilm)


def send(user: str, message):
    """Sends message requested from admin to user, works either with id or username"""
    try:
        if not user.isdigit():
            users_list = dict(read_users(names=True, stopped=True))
            user = users_list[user]
        bot.send_message(user,
                         f'<b>Сообщение от администрации!</b>\n\n<i>{message}</i>',
                         parse_mode='HTML'
                         )
        print(f'Sent message to {user}:\n{message}')
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
        if cur.execute(f"UPDATE users SET group_number = {group} WHERE id = '{chat_id}';") == 1:
            print(f'{chat_id} changed his group from {before} to {group}.')
        else:
            print(f"Error occurred while changing {chat_id}'s group from {before} to {group}.")


def promo():
    """Sends a little promotional message for all users.txt (except my gf)"""
    users = read_users()
    for user_id in users:
        if user_id[0] == '1103761115':
            continue
        try:
            bot.send_message(user_id[0],
                             text=f'Если тебе нравится наш бот, пожалуйста, не жадничай и поделись им с друзьями! 😉\nЯ буду очень рад!',
                             parse_mode='HTML', disable_notification=True)
        except telebot.apihelper.ApiTelegramException as user_e:
            print(f"Bad USER ({user_id[0]}):", user_e)


schedule.every(2).days.at('16:00').do(promo)


def report(message):
    """Report about problem or idea from user to admin"""
    if message.from_user.id != message.chat.id:
        bot.send_message(message.chat.id, text='<i><b>Данная функция недоступна в групповых чатах!</b></i>',
                         parse_mode='HTML')
        return
    keyboard = types.InlineKeyboardMarkup()
    key_report = types.InlineKeyboardButton(text='❗ Проблема/Ошибка', callback_data='report')
    keyboard.add(key_report)
    key_support = types.InlineKeyboardButton(text='💡 Идея/Предложение', callback_data='support')
    keyboard.add(key_support)
    bot.send_message(message.from_user.id, text='О чем вы хотите <b>сообщить</b>?', parse_mode='HTML',
                     reply_markup=keyboard)


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
@bot.message_handler(commands=['gift', 'promo', 'send', 'reconnect'])
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
    elif message.text.startswith('/reconnect'):
        try:
            sql_connect()
        except Exception as connection_error:
            print("Error while reconnecting to database:", connection_error)
    else:
        print('Wrong code')


# [START]
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     '<b>Привет, я BookBot! 📚\n</b> \n<i>С данного момента, тебе каждый день будут приходить случайные цитаты. '
                     'Для того, чтобы узнать побольше о функционале бота - напиши /help \n</i>'
                     '\nА также, Вы можете попробовать найти цитаты из вашей любимой книги или вашего любимого автора, '
                     'написав /search',
                     parse_mode='HTML')
    with sql.cursor() as cur:
        if cur.execute(f"SELECT id FROM users WHERE id = '{chat_id}'"):
            return
        cur.execute(
            f"INSERT INTO users(username, id) VALUES ('{message.chat.title or message.chat.username}', '{chat_id}');")
        print(message.chat.title or message.chat.username, 'connected to bot.')
    quote = quotes.check(str(chat_id))
    bot.send_message(chat_id, f'Держи свою первую цитату!')
    quotes.send(quote, chat_id)


# user commands handler
@bot.message_handler(commands=['stop', 'resume', 'help', 'report', 'random', 'add', 'quotes', 'search', 'addmany'])
def commands_handler(message):
    command = message.text
    user_id = message.chat.id
    if command.startswith('/stop'):
        quotes.stop(user_id)
    elif command.startswith('/resume'):
        quotes.resume(user_id)
    elif command.startswith('/help'):
        commands = ('<b>Список команд:\n'
                    '</b>\n/random<i> - случайная цитата в любое время суток\n'
                    '</i>\n/stop<i> - приостановить рассылку\n'
                    '</i>\n/resume<i> - возобновить рассылку\n'
                    '</i>\n/report<i> - сообщить о проблеме или предложении\n'
                    '</i>\n/add<i> - предложить свою цитату\n'
                    '</i>\n/addmany<i> - предложить несколько цитат из одной книги\n'
                    '</i>\n/quotes<i> - сменить частоту получения цитат\n'
                    '</i>\n/search<i> - найти цитату по книге или автору</i>'

                    )
        bot.send_message(user_id, text=commands, parse_mode='HTML')
    elif command.startswith('/quotes'):
        group = types.InlineKeyboardMarkup()
        group.add(types.InlineKeyboardButton(text='14.00 (UTC+6)', callback_data='1'))
        group.add(types.InlineKeyboardButton(text='12.00 + 20.00 (UTC+6)', callback_data='2'))
        bot.send_message(user_id,
                         '<b>Смена частоты получения цитат:</b>',
                         parse_mode='HTML', reply_markup=group)
    elif command.startswith('/report'):
        report(message)
    elif command.startswith('/random'):
        try:
            quotes.random(str(user_id), False)
        except Exception:
            traceback.print_exc()
    elif command.startswith('/addmany'):
        choose_type = types.InlineKeyboardMarkup([[types.InlineKeyboardButton(text='Фильм 🎬', callback_data="from film"),
                                                   types.InlineKeyboardButton(text='Книга 📖', callback_data="from book")]])
        bot.send_message(user_id, "<i>Выберите, цитаты откуда вы хотите отправить</i>",
                         parse_mode='HTML', reply_markup=choose_type)
    elif command.startswith('/add'):
        choose_type = types.InlineKeyboardMarkup([[types.InlineKeyboardButton(text='Фильм 🎬', callback_data="Quote from film"),
                                                   types.InlineKeyboardButton(text='Книга 📖', callback_data="Quote from book")]])
        bot.send_message(user_id, "<i>Выберите, какую цитату вы хотите отправить</i>",
                         parse_mode='HTML', reply_markup=choose_type)
    elif command.startswith('/search'):
        if len(command.split()) == 1:
            bot.send_message(user_id,
                             '📚 <i>Напишите имя автора или книги после /search через пробел (в одном сообщении).</i>',
                             parse_mode='HTML')
            return
        find = ' '.join([sf.clean(i) for i in command[8:].lower().split()]).strip()
        with open('quotes/authors', 'r', encoding='UTF-8') as authors, open('quotes/books', 'r',
                                                                            encoding='UTF-8') as books:
            authors = authors.read().splitlines()
            books = books.read().splitlines()
            source = 'author'
            if find not in authors:
                if find not in books:
                    bot.send_message(977341432, f'Добавить:\n{command[8:]}/{find}')
                    bot.send_message(user_id,
                                     '☹ <i>К сожалению этой книги или автора у нас нет...\n\n'
                                     'Но вы всегда можете попробовать добавить их через /add !</i>',
                                     parse_mode='HTML')
                    return
                find = command[8:]
                source = 'book'
            
        with sql.cursor() as cur:
            cur.execute(
                f"SELECT * FROM quotes WHERE "
                f"{source} = '{find if source == 'book' else ' '.join([i.capitalize() for i in find.replace(' ', '_', 10).split()])}'")
            q = cur.fetchall()
            if len(q) == 0 and source == 'book':
                cur.execute(f"SELECT * FROM quotes WHERE book = '{find.capitalize()}'")
                q = cur.fetchall()
                if len(q) == 0:
                    cur.execute(f"SELECT * FROM quotes WHERE book = '{' '.join(word.capitalize() for word in find.split())}'")
                    q = cur.fetchall()
                    if len(q) == 0: 
                        bot.send_message(user_id,
                                         '⚠ <i>Перепроверьте название книги, что-то написано не так!</i>', parse_mode='HTML')
            else:
                quotes.send(q[random.randrange(len(q))], user_id)
    else:
        print('Wrong code')


@bot.message_handler()
def idk(message):
    bot.send_message(message.chat.id,
                     '<i>Прости, я не понимаю чего ты хочешь 😰</i>\n\n'
                     'Попробуй написать /help !',
                     parse_mode='HTML')


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
        bot.answer_callback_query(call.id)

    elif call.data == "from film":
        bot.send_message(call.message.chat.id,
                         '🎬 Отправьте фильм и год в таком формате:\n\n'
                         '<i>фильм%год</i>\n\n'
                         '<i>Апполон 13%1995</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(call.message, add_many_quotes, isfilm=True)
        
    elif call.data == "from book":
        bot.send_message(call.message.chat.id,
                         '📚 Отправьте автора цитат и книгу в таком формате:\n\n'
                         '<i>книга%автор</i>\n\n'
                         '<i>Вино из одуванчиков%Рэй Брэдбери</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(call.message, add_many_quotes)
        
    elif call.data == "Quote from film":
        bot.send_message(call.message.chat.id,
                         '🎬 Отправьте цитату в таком виде:\n\n'
                         '<i>текст_цитаты%фильм%год</i>\n\n'
                         '<i>Хьюстон, у нас проблема.%Апполон 13%1995</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(call.message, quotes.add, isfilm=True)
        
    elif call.data == "Quote from book":
        bot.send_message(call.message.chat.id,
                         '📚 Отправьте цитату в таком виде:\n\n'
                         '<i>текст_цитаты%книга%автор</i>\n\n'
                         '<i>Что хочешь помнить, то всегда помнишь.%Вино из одуванчиков%Рэй Брэдбери</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(call.message, quotes.add)
        
    elif call.data == 'cancel':
        global callback_cancel
        callback_cancel.update({call.message.chat.id: True})
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Отменено!")


# users0 = read_users()
# for _ in users0:
#     try:
#         print("Announced")
#         bot.send_message(_[0],
#                          '⚠ <b>ВНИМАНИЕ!</b>\n\n'
#                          'Добавлена новая команда!\n'
#                          'Попробуйте найти цитаты по книге или автору - /search !',
#                          parse_mode='HTML')
#     except Exception:
#         continue
# quotes.randoms(0)


# yes = types.InlineKeyboardButton(text='🙂 Да!', callback_data='yes')
# no = types.InlineKeyboardButton(text='☹ Нет!', callback_data='no')
# answer = types.InlineKeyboardMarkup([[yes, no]])

# with sql.cursor() as cur:
#     cur.execute("SELECT id FROM users;")
#     users_qa = cur.fetchall()

# for user in users_qa:
#     bot.send_message(user[0],
#         "⚠ <b>ВНИМАНИЕ!\nПожалуйста, ответьте на вопрос ниже в целях выбора дальнейшего направления развития бота.</b>\n\n"
#         "<i>Хотите ли вы видеть цитаты из фильмов в рассылке?</i>\n\nЕсли у вас есть любимые фильмы, цитаты из которых вы хотели бы получать,"
#         "можете отправить их с помощью /report.", parse_mode="HTML", reply_markup=answer)
#     print(user, '- Succes')


try_count = 0
last_exc = time.time()
while True:
    try:
        if try_count > 0:
            sql_connect()
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        try_count += 1 if time.time() - last_exc < 30 else -try_count
        with open("admin/connection_log.txt", "a") as log:
            log.write("==============================\nConnection ERROR: " + traceback.format_exc())
        last_exc = time.time()
        print("Reconnecting:", try_count)
