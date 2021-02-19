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

# built-ins
token = os.environ.get('TG_TOKEN')
mongoDB = os.environ.get('mongoDB')
client = pymongo.MongoClient(f"{mongoDB}")
DB = client["BookBot"]["quotes_queue"]
bot = telebot.TeleBot(token)

# variables
stopped = []
callback_cancel = False


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


# functional
def quote_4_user_checker(user_id: str):
    """Checks for quote available for {user}"""
    while True:
        quote = DB.find({})[random.randint(0, DB.count_documents({}) - 1)]
        if user_id not in quote["Users"]:
            users = quote["Users"] + [user_id]
            required_quote = quote
            DB.update_one({"Quote": quote["Quote"]}, {"$set": {"Users": users}})
            return required_quote


def promo():
    """Sends a little promotional message for all users (except my gf)"""
    with open('users', 'r') as users_r:
        r = users_r.read().replace('\\n', '').splitlines()
    for i in r:
        if i == '1103761115':
            return None
        else:
            bot.send_message(i,
                             text=f'Если тебе нравится наш бот, пожалуйста, не жадничай и поделись им с друзьями! 😉\nЯ буду очень рад!',
                             parse_mode='HTML', disable_notification=True)


def random_quote():
    """Sends random quote for users who aren't in 'stopped' list"""
    with open('users', 'r') as users_r:
        r = users_r.read().replace('\\n', '').splitlines()
    for user_id in r:
        if user_id in stopped:
            return None
        quote = quote_4_user_checker(user_id)
        keyboard = types.InlineKeyboardMarkup()
        key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quote["URL"])
        keyboard.add(key_book)  # добавляем кнопку в клавиатуру
        #   key_like = types.InlineKeyboardButton(text='Нет', callback_data='no')
        #   keyboard.add(key_like)
        bot.send_message(user_id,
                         text=f'<i>{quote["Quote"]}\n</i>\n<b>{quote["Book"]}</b>\n#{quote["Author"]}',
                         parse_mode='HTML', reply_markup=keyboard)


schedule.every().day.at('14:00').do(random_quote)
schedule.every(2).days.at('16:00').do(promo)


# on start
@bot.message_handler(commands=['start'])
def start(message):
    """Welcome message, also sends a demo quote"""
    with open('users', 'r') as users_r:
        r = users_r.read().replace('\\n', '').splitlines()
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


# on stop
@bot.message_handler(commands=['stop'])
def stop(message):
    """Moves user to 'stopped' list, so he won't receive sheduled quotes"""
    if message.from_user.id not in stopped:
        stopped.append(message.from_user.id)
        bot.send_message(message.from_user.id,
                         '<b>❌ Рассылка цитат приостановлена!\n</b> \nЧтобы возобновить напишите /resume',
                         parse_mode='HTML')
    elif message.from_user.id in stopped:
        bot.send_message(message.from_user.id,
                         '<b>⚠ Рассылка цитат уже приостановлена для вас!\n</b> \nЧтобы возобновить напишите /resume',
                         parse_mode='HTML')


# on resume
@bot.message_handler(commands=['resume'])
def resume(message):
    """Removes user from 'stopped' list"""
    if message.from_user.id in stopped:
        stopped.remove(message.from_user.id)
        bot.send_message(message.from_user.id, '<b>✔ Рассылка цитат возобновлена!</b>',
                         parse_mode='HTML')
    elif message.from_user.id not in stopped:
        bot.send_message(message.from_user.id, '<b>⚠ Вы еще не приостанавливали рассылку!</b>',
                         parse_mode='HTML')


# on help
@bot.message_handler(commands=['help'])
def help_command(message):
    """Help with all commands"""
    commands = '<b>Список команд:\n</b>\n/stop<i> - приостановить рассылку\n</i>\n/resume<i> - возобновить рассылку\n</i>\n/report<i> - сообщить о проблеме или предложении</i>'
    bot.send_message(message.from_user.id, text=commands, parse_mode='HTML')


# on report
@bot.message_handler(commands=['report'])
def report(message):
    """Report about problem or idea from user to admin"""
    keyboard = types.InlineKeyboardMarkup()
    key_report = types.InlineKeyboardButton(text='❗ Проблема/Ошибка', callback_data='report')
    keyboard.add(key_report)  # добавляем кнопку в клавиатуру
    key_support = types.InlineKeyboardButton(text='💡 Идея/Предложение', callback_data='support')
    keyboard.add(key_support)
    bot.send_message(message.from_user.id, text=f'О чем вы хотите <b>сообщить</b>?', parse_mode='HTML',
                     reply_markup=keyboard)


# on messages
@bot.message_handler(content_types=['text', 'voice', 'audio'])
def get_text_messages(message):
    """Reacts to audio message. Juat for fun"""
    if message.voice is not None or message.audio is not None:
        bot.send_message(message.from_user.id, 'Ммм... Рай для моих ушей ✨')


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    keyboard = types.InlineKeyboardMarkup()
    key_cancel = types.InlineKeyboardButton(text='Отменить', callback_data='cancel')
    keyboard.add(key_cancel)
    if call.data == "report":
        bot.send_message(call.message.chat.id,
                         '<i>Опишите проблему, Ваше сообщение будет доставлено администрации и принято на рассмотрение!\n</i>',
                         parse_mode='HTML', reply_markup=keyboard)
        print(1)
        bot.register_next_step_handler(call.message, report_send)
        print(2)
        
    elif call.data == "support":
        bot.send_message(call.message.chat.id,
                         '<i>Опишите Вашу идею, сообщение будет доставлено администрации и принято на рассмотрение!\n</i>',
                         parse_mode='HTML', reply_markup=keyboard)
        bot.register_next_step_handler(call.message, support_send)   
        
    elif call.data == 'cancel':
        global callback_cancel
        callback_cancel = True
        bot.send_message(call.message.chat.id,
                         '<b><i>Отменено!</i></b>',
                         parse_mode='HTML')
        
        


def report_send(message):
    global callback_cancel
    if callback_cancel == True:
        callback_cancel = False
        return
    bot.send_message(977341432,
                     f'❗ <b>Поступила жалоба:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.from_user.id,
                     f'✔ <b>Жалоба успешно подана на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')


def support_send(message):
    global callback_cancel
    if callback_cancel == True:
        callback_cancel = False
        return
    bot.send_message(977341432,
                     f'💡 <b>Поступило предложение:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.from_user.id,
                     f'✔ <b>Предложение успешно подано на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')


def polling():
    try:
        bot.polling(none_stop=True, interval=2)
    except Exception as e:
        polling()


# random_quote()
polling()
