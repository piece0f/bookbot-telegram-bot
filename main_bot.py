# -*- coding: utf-8 -*-
"""
BookBot is telegram bot, based on telegram API and MongoDB.
His objective is to send interesting quotes from books to users.
"""

import os
import telebot
from telebot import types
import schedule
import time
import random
from threading import Thread
import pymongo
from datetime import datetime

# [BUILT-INS]
token = os.environ.get('TG_TOKEN')
mongoDB = os.environ.get('mongoDB')
client = pymongo.MongoClient(f"{mongoDB}")
bot = telebot.TeleBot(token)

# [VARIABLES]
with open('users0', 'r') as f:
    file = f.read().splitlines()
    callback_cancel = {int(user): False for user in file}
cancel_button = types.InlineKeyboardMarkup()
key_cancel = types.InlineKeyboardButton(text='Отменить', callback_data='cancel')
cancel_button.add(key_cancel)


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
    def __init__(self):
        self.db = client["BookBot"]["quotes_queue"]
        with open("stop_list", "r") as _:
            self.stopped = _.read().splitlines()

    # on stop
    def stop(self, message):
        """Moves user to 'stopped' list, so he won't receive scheduled quotes"""
        if str(message.chat.id) not in self.stopped:
            with open("stop_list", "a") as stopped_tmp:
                stopped_tmp.write(f"{message.chat.id}\n")
            self.stopped.append(str(message.chat.id))
            bot.send_message(message.chat.id,
                             '<b>❌ Рассылка цитат приостановлена!\n</b> \nЧтобы возобновить напишите /resume',
                             parse_mode='HTML')
        else:
            bot.send_message(message.chat.id,
                             '<b>⚠ Рассылка цитат уже приостановлена для вас!\n</b> \nЧтобы возобновить напишите /resume',
                             parse_mode='HTML')

    # on resume
    def resume(self, message):
        """Removes user from 'stopped' list"""
        if str(message.chat.id) in self.stopped:
            with open('stop_list', 'r') as stopped_tmp:
                stopped_raw = stopped_tmp.readlines()
                stopped_raw.remove(str(message.chat.id) + '\n')
            with open("stop_list", "w") as _:
                _.write(''.join(stopped_raw))
            self.stopped.remove(str(message.chat.id))
            bot.send_message(message.chat.id, '<b>✔ Рассылка цитат возобновлена!</b>',
                             parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, '<b>⚠ Вы еще не приостанавливали рассылку!</b>',
                             parse_mode='HTML')

    def check(self, user: str, check=True) -> dict:
        """Checks for quote available for {user}"""
        est_quotes = self.db.estimated_document_count()
        if self.db.count_documents({"Users": user}) >= est_quotes - 1:
            # removes user id from DB if there is no more available quotes for user
            self.db.update_many({"Users": user}, {"$pull": {"Users": user}})
        all_quotes = self.db.find({})
        while True:
            quote = all_quotes[random.randint(0, est_quotes - 1)]
            if not check:
                # if check for available is not required return random quote
                return quote
            if user in quote["Users"]:
                continue
            required_quote = quote
            self.db.update_one({"Quote": quote["Quote"]}, {"$push": {"Users": user}})
            return required_quote

    def random(self, user, checking=False):
        """ Sends random quote for user.
            If checking == False, it does not check for the presence of id in the database.
        """
        quo = self.check(user, check=checking)
        keyboard = types.InlineKeyboardMarkup()
        key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quo["URL"])
        keyboard.add(key_book)
        #   key_like = types.InlineKeyboardButton(text='Нет', callback_data='no')
        #   keyboard.add(key_like)
        bot.send_message(user,
                         text=f'<i>{quo["Quote"]}\n</i>\n<b>{quo["Book"]}</b>\n#{quo["Author"]}',
                         parse_mode='HTML', reply_markup=keyboard)

    def randoms(self, group: int):
        """Sends random quote for users who aren't in 'stopped' list"""
        start_time = time.time()
        counter = 0
        with open(f'users{group}', 'r') as users_r:
            r = users_r.read().splitlines()
        print("=================================")
        for user_id in r:
            if user_id in self.stopped:
                continue
            try:
                self.random(user_id, True)
                print(f"Latency #{counter}: {str(time.time() - start_time)[:4]} seconds")
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Bad ID ({user_id}):", e)
            except Exception as e:
                print(e)
            finally:
                counter += 1

    def add(self, message):
        """Adds a quote from user to file, for further verification."""
        global callback_cancel
        if callback_cancel[message.chat.id]:
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
        with open('quotes_4_add.txt', 'a', encoding='utf-8') as verification:
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
scheduler = AsyncScheduler("Проверка времени")
scheduler.start()
quotes = Quote()
schedule.every().day.at('14:00').do(quotes.randoms, group=1)
schedule.every().day.at('12:00').do(quotes.randoms, group=2)
schedule.every().day.at('20:00').do(quotes.randoms, group=2)


# [FUNCTIONAL]
# on help
def help_command(message):
    """Help with all commands"""
    commands = ('<b>Список команд:\n'
                '</b>\n/random<i> - случайная цитата в любое время суток\n'
                '</i>\n/stop<i> - приостановить рассылку\n'
                '</i>\n/resume<i> - возобновить рассылку\n'
                '</i>\n/report<i> - сообщить о проблеме или предложении\n'
                '</i>\n/add<i> - предложить свою цитату\n'
                '</i>\n/quotes<i> - сменить частоту получения цитат</i>'
                )
    bot.send_message(message.chat.id, text=commands, parse_mode='HTML')


# on report
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


# messages from admin
def send(user: str, message):
    """Sends message requested from admin to user"""
    try:
        user_id = user
        if not user.isdigit():
            with open('users', 'r') as _:
                _ = _.read().splitlines()
                for i in range(len(_)):
                    _[i] = tuple(_[i].split(', '))
                nicknames = dict(_)
            user_id = nicknames[user]
        bot.send_message(user_id,
                         f'<b>Сообщение от администрации!</b>\n\n<i>{message}</i>',
                         parse_mode='HTML'
                         )
        print(f'Sent message to {user_id}:\n{message}')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Bad USER ({user}):", e)
    except Exception as e:
        print(e)


# changes user's time for quote
def change_group(chat_id, group: int):
    before = 0
    for i in range(1, 3):
        with open(f'users{i}', 'r') as file_read:
            group_list = file_read.readlines()
            if chat_id + '\n' in group_list and i == group:
                raise UserInGroup()
        if chat_id + '\n' in group_list:
            group_list.remove(chat_id + '\n')
            before = i
            with open(f'users{i}', 'w') as file_write:
                file_write.write(''.join(group_list))
        elif i == group:
            group_list.append(chat_id + '\n')
            with open(f'users{i}', 'w') as file_write:
                file_write.write(''.join(group_list))
    print(f'{chat_id} changed his group from {before} to {group}.')


def promo():
    """Sends a little promotional message for all users (except my gf)"""
    with open('users', 'r') as _:
        r = _.read().splitlines()
        r = [usr.split(', ')[1] for usr in r]
    for user_id in r:
        if user_id == '1103761115':
            continue
        bot.send_message(user_id,
                         text=f'Если тебе нравится наш бот, пожалуйста, не жадничай и поделись им с друзьями! 😉\nЯ буду очень рад!',
                         parse_mode='HTML', disable_notification=True)


schedule.every(2).days.at('16:00').do(promo)


# problem handler
def report_send(message):
    global callback_cancel
    if callback_cancel[message.chat.id]:
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
    if callback_cancel[message.chat.id]:
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
    """Welcome message, also sends a demo quote"""
    global callback_cancel
    with open('users0', 'r') as _:
        r = _.read().splitlines()
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     '<b>Привет, я BookBot! 📚\n</b> \n<i>С данного момента, тебе каждый день будут приходить случайные цитаты. Для того, чтобы узнать побольше о функционале бота - напиши /help \n</i>\nА также, в скором времени появится функция выбора любимых авторов, технология подбора цитат для Вас индивидуально, и много других интересных фишек! 😉',
                     parse_mode='HTML')
    if str(chat_id) in r:
        return
    with open('users0', 'a') as users_w1, open('users1', 'a') as users_w2, open('users', 'a') as users_w:
        if message.from_user.id == message.chat.id:
            users_w.write(f'{message.from_user.username}, {chat_id}\n')
        users_w1.write(f'{chat_id}\n')
        users_w2.write(f'{chat_id}\n')
        print(message.chat.username or message.chat.title, 'connected to bot.')
    quote = quotes.check(user=chat_id)
    keyboard = types.InlineKeyboardMarkup()
    key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quote["URL"])
    keyboard.add(key_book)
    bot.send_message(chat_id,
                     text=f'Держи свою первую цитату!\n\n<i>{quote["Quote"]}\n</i>\n<b>{quote["Book"]}</b>\n#{quote["Author"]}',
                     parse_mode='HTML')
    callback_cancel.update({int(message.chat.id): False})


# user commands handler
@bot.message_handler(commands=['stop', 'resume', 'help', 'report', 'random', 'add', 'quotes'])
def commands_handler(message):
    command = message.text
    if command.startswith('/stop'):
        quotes.stop(message)
    elif command.startswith('/resume'):
        quotes.resume(message)
    elif command.startswith('/help'):
        help_command(message)
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
            quotes.random(message.chat.id, False)
        except:
            pass
    elif command.startswith('/add'):
        global cancel_button
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
        except Exception as e:
            print(e)
    elif call.data == 'cancel':
        global callback_cancel
        callback_cancel[call.message.chat.id] = True
        bot.send_message(call.message.chat.id,
                         '<b><i>Отменено!</i></b>',
                         parse_mode='HTML')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


def polling():
    try:
        bot.polling(none_stop=True, interval=1)
    # noinspection PyBroadException
    except Exception as e:
        print(datetime.now().time(), '- Connection ERROR:', e)
        polling()


# with open('users0', 'r') as f:
#     users0 = f.read().splitlines()
# for _ in users0:
#     try:
#         bot.send_message(_,
#                          '⚠ <b>ВНИМАНИЕ!</b>\n\n'
#                          'Добавлена новая команда!\n'
#                          'Чтобы получать 2 цитаты в день, напишите /quotes 2! Подробнее о команде в /help',
#                          parse_mode='HTML')
#     except:
#         continue

# quotes.randoms(0)

polling()
