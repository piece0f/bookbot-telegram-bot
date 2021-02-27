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

# [BUILT-INS]
token = os.environ.get('TG_TOKEN')
mongoDB = os.environ.get('mongoDB')
client = pymongo.MongoClient(f"{mongoDB}")
quotes = client["BookBot"]["quotes_queue"]
with open("stop_list", "r") as f:
    stopped = f.read().splitlines()
bot = telebot.TeleBot(token)

# [VARIABLES]
with open('users', 'r') as f:
    f = f.read().splitlines()
    callback_cancel = {user: False for user in f}
cancel_button = types.InlineKeyboardMarkup()
key_cancel = types.InlineKeyboardButton(text='Отменить', callback_data='cancel')
cancel_button.add(key_cancel)


# Async thread (time scheduler)
class AsyncScheduler(Thread):
    def __init__(self, name):
        Thread.__init__(self)
        self.name = name

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(59)


scheduler = AsyncScheduler('Проверка времени')
scheduler.start()


# [FUNCTIONAL]
# on stop
def stop(message):
    """Moves user to 'stopped' list, so he won't receive scheduled quotes"""
    global stopped
    if str(message.from_user.id) not in stopped:
        with open("stop_list", "a") as stopped_tmp:
            stopped_tmp.write(f"{message.from_user.id}\n")
            stopped_tmp.close()
        stopped.append(str(message.from_user.id))
        bot.send_message(message.from_user.id,
                         '<b>❌ Рассылка цитат приостановлена!\n</b> \nЧтобы возобновить напишите /resume',
                         parse_mode='HTML')
    else:
        bot.send_message(message.from_user.id,
                         '<b>⚠ Рассылка цитат уже приостановлена для вас!\n</b> \nЧтобы возобновить напишите /resume',
                         parse_mode='HTML')


# on resume
def resume(message):
    """Removes user from 'stopped' list"""
    global stopped
    if str(message.from_user.id) in stopped:
        with open('stop_list', 'r') as stopped_tmp:
            stopped_raw = stopped_tmp.readlines()
            stopped_raw.remove(str(message.from_user.id) + '\n')
        with open("stop_list", "w") as tmp:
            tmp.write(''.join(stopped_raw))
            tmp.close()
        stopped.remove(str(message.from_user.id))
        bot.send_message(message.from_user.id, '<b>✔ Рассылка цитат возобновлена!</b>',
                         parse_mode='HTML')
    else:
        bot.send_message(message.from_user.id, '<b>⚠ Вы еще не приостанавливали рассылку!</b>',
                         parse_mode='HTML')


# on help
def help_command(message):
    """Help with all commands"""
    commands = ('<b>Список команд:\n'
                '</b>\n/random<i> - случайная цитата в любое время суток\n'
                '</i>\n/stop<i> - приостановить рассылку\n'
                '</i>\n/resume<i> - возобновить рассылку\n'
                '</i>\n/report<i> - сообщить о проблеме или предложении\n'
                '</i>\n/add<i> - предложить свою цитату</i>'
                )
    bot.send_message(message.from_user.id, text=commands, parse_mode='HTML')


# on report
def report(message):
    """Report about problem or idea from user to admin"""
    keyboard = types.InlineKeyboardMarkup()
    key_report = types.InlineKeyboardButton(text='❗ Проблема/Ошибка', callback_data='report')
    keyboard.add(key_report)  # добавляем кнопку в клавиатуру
    key_support = types.InlineKeyboardButton(text='💡 Идея/Предложение', callback_data='support')
    keyboard.add(key_support)
    bot.send_message(message.from_user.id, text=f'О чем вы хотите <b>сообщить</b>?', parse_mode='HTML',
                     reply_markup=keyboard)


def quote_4_user_checker(user_id: str, check=True):
    """Checks for quote available for {user}"""
    if quotes.count_documents({"Users": user_id}) >= 68:
        # removes user id from DB if there is no more available quotes for user
        quotes.update_many({"Users": user_id}, {"$pull": {"Users": user_id}})
    while True:
        quote = quotes.find({})[random.randint(0, quotes.count_documents({}) - 1)]
        if not check:
            # if check for available is not required return random quote
            return quote
        if user_id in quote["Users"]:
            continue
        required_quote = quote
        quotes.update_one({"Quote": quote["Quote"]}, {"$push": {"Users": user_id}})
        return required_quote


def promo():
    """Sends a little promotional message for all users (except my gf)"""
    with open('users', 'r') as users_r:
        r = users_r.read().splitlines()
    for user_id in r:
        if user_id == '1103761115':
            continue
        bot.send_message(user_id,
                         text=f'Если тебе нравится наш бот, пожалуйста, не жадничай и поделись им с друзьями! 😉\nЯ буду очень рад!',
                         parse_mode='HTML', disable_notification=True)


def random_q(user, checking=False):
    """ Sends random quote for user.
        If checking == False, it does not check for the presence of id in the database.
    """
    quote = quote_4_user_checker(user, check=checking)
    keyboard = types.InlineKeyboardMarkup()
    key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quote["URL"])
    keyboard.add(key_book)
    #   key_like = types.InlineKeyboardButton(text='Нет', callback_data='no')
    #   keyboard.add(key_like)
    bot.send_message(user,
                     text=f'<i>{quote["Quote"]}\n</i>\n<b>{quote["Book"]}</b>\n#{quote["Author"]}',
                     parse_mode='HTML', reply_markup=keyboard)


def random_quotes():
    """Sends random quote for users who aren't in 'stopped' list"""
    with open('users', 'r') as users_r:
        r = users_r.read().splitlines()
    for user_id in r:
        if user_id in stopped:
            continue
        try:
            random_q(user_id, True)
        except:
            continue


def add_quote(message):
    """Adds a quote from user to file, for further verification."""
    global callback_cancel
    if callback_cancel[message.from_user.id]:
        callback_cancel[message.from_user.id] = False
        return
    if message.text.count('%') != 2:
        global cancel_button
        bot.send_message(message.from_user.id,
                         '⚠ <b>Неправильный формат!</b>\nОтправьте цитату в таком виде:\n\n'
                         '<i>текст_цитаты%книга%автор</i>\n\n'
                         '<i>Что хочешь помнить, то всегда помнишь.%Вино из одуванчиков%Рэй Брэдбери</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        return bot.register_next_step_handler(message, add_quote)
    with open('quotes_4_add.txt', 'a', encoding='utf-8') as verification:
        verification.write(message.text + '%\n')
    bot.send_message(message.from_user.id,
                     '✔ <i>Спасибо за помощь в развитии бота! Ваша цитата была отправлена на проверку'
                     ' и будет добавлена в течении 48 часов!</i>',
                     parse_mode='HTML')
    print(f'{message.from_user.id} (@{message.from_user.username}) запросил добавление цитаты!')
    pass


# problem handler
def report_send(message):
    global callback_cancel
    if callback_cancel[message.from_user.id]:
        callback_cancel[message.from_user.id] = False
        return
    bot.send_message(977341432,
                     f'❗ <b>Поступила жалоба:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.from_user.id,
                     f'✔ <b>Жалоба успешно подана на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')


# idea handler
def support_send(message):
    global callback_cancel
    if callback_cancel[message.from_user.id]:
        callback_cancel[message.from_user.id] = False
        return
    bot.send_message(977341432,
                     f'💡 <b>Поступило предложение:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.from_user.id,
                     f'✔ <b>Предложение успешно подано на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')


schedule.every().day.at('14:00').do(random_quotes)
schedule.every(2).days.at('16:00').do(promo)


# [ADMIN]
@bot.message_handler(commands=['quote', 'promo'])
def admin(message):
    """Admin message handler, answers on admin requests"""
    print('Admin command execution...')
    if message.from_user.id != 977341432:
        print('False: Non-admin request')
        return
    if message.text == '/quote':
        random_quotes()
        print("Succeed")
    elif message.text == '/promo':
        promo()
        print("Succeed")
    else:
        print('Wrong code')


# [START]
@bot.message_handler(commands=['start'])
def start(message):
    """Welcome message, also sends a demo quote"""
    with open('users', 'r') as users_r:
        r = users_r.read().splitlines()
    with open('users', 'a') as users_w:
        user_id = message.from_user.id
        bot.send_message(user_id,
                         '<b>Привет, я BookBot! 📚\n</b> \n<i>С данного момента, тебе каждый день будут приходить случайные цитаты. Для того, чтобы узнать побольше о функционале бота - напиши /help \n</i>\nА также, в скором времени появится функция выбора любимых авторов, технология подбора цитат для Вас индивидуально, и много других интересных фишек! 😉',
                         parse_mode='HTML')
        if str(user_id) in r:
            return
        users_w.write(str(user_id) + '\n')
        print(message.from_user.username)
        quote = quote_4_user_checker(user_id)
        keyboard = types.InlineKeyboardMarkup()
        key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quote["URL"])
        keyboard.add(key_book)
        bot.send_message(user_id,
                         text=f'Держи свою первую цитату!\n\n<i>{quote["Quote"]}\n</i>\n<b>{quote["Book"]}</b>\n#{quote["Author"]}',
                         parse_mode='HTML')


# user commands handler
@bot.message_handler(commands=['stop', 'resume', 'help', 'report', 'random', 'add'])
def commands_handler(message):
    command = message.text
    if command == '/stop':
        stop(message)
    elif command == '/resume':
        resume(message)
    elif command == '/help':
        help_command(message)
    elif command == '/report':
        report(message)
    elif command == '/random':
        try:
            random_q(message.from_user.id, False)
        except:
            pass
    elif command == '/add':
        global cancel_button
        bot.send_message(message.from_user.id,
                         '📚 Отправьте цитату в таком виде:\n\n'
                         '<i>текст_цитаты%книга%автор</i>\n\n'
                         '<i>Что хочешь помнить, то всегда помнишь.%Вино из одуванчиков%Рэй Брэдбери</i>',
                         parse_mode='HTML', reply_markup=cancel_button)
        bot.register_next_step_handler(message, add_quote)
    else:
        print('Wrong code')


# on audio
@bot.message_handler(content_types=['voice', 'audio'])
def get_audio_messages(message):
    """Reacts to audio message. Just for fun"""
    if message.voice is not None or message.audio is not None:
        bot.send_message(message.from_user.id, 'Ммм... Рай для моих ушей ✨')


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

    elif call.data == 'cancel':
        global callback_cancel
        callback_cancel[call.message.from_user.id] = True
        bot.send_message(call.message.chat.id,
                         '<b><i>Отменено!</i></b>',
                         parse_mode='HTML')


def polling():
    try:
        bot.polling(none_stop=True, interval=1)
    # noinspection PyBroadException
    except Exception:
        polling()

        
# with open('users', 'r') as f:
#     users = f.read().splitlines()
# for i in users:
#     try:
#         bot.send_message(i,
#                          '⚠ <b>ВНИМАНИЕ!</b>\n\n'
#                          'Добавлена новая команда!\n'
#                          'Добавляйте свои любимые цитаты с помощью /add!',
#                          parse_mode='HTML')
#     except:
#         continue

# random_quotes()
polling()
