# -*- coding: utf-8 -*-

import telebot
from telebot import types
import schedule
import time
import random
from threading import Thread
from quotes import*


# built-ins
token = '1480667214:AAFuuQu7aF6Cx1wIDIFGwnsdCQDAeDqZU-s'
bot = telebot.TeleBot(token)
stopped = []


class AsyncScheduler(Thread):
    def __init__(self, name):
        Thread.__init__(self)
        self.name = name

    def run(self):
        while True:
            try:
                schedule.run_pending()
                time.sleep(59)
            except:
                self.run()


scheduler = AsyncScheduler('Проверка времени')
scheduler.start()



# functional
def repost():
    users_r = open('users', 'r')
    r = users_r.read().replace('\\n', '')
    r = r.splitlines()
    users_r.close()
    for i in r:
        if i == '1103761115':
            return None
        else:
            bot.send_message(i,
                             text=f'Если тебе нравится наш бот, пожалуйста, не жадничай и поделись им с друзьями! 😉\nЯ буду очень рад!',
                             parse_mode='HTML', disable_notification=True)


def rand_quo():
    users_r = open('users', 'r')
    r = users_r.read().replace('\\n', '')
    r = r.splitlines()
    users_r.close()
    for i in r:
        if i not in stopped:
            number = random.randint(0, len(randoms) - 1)
            keyboard = types.InlineKeyboardMarkup()
            key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=randoms[number][3])
            keyboard.add(key_book)  # добавляем кнопку в клавиатуру
            #   key_like = types.InlineKeyboardButton(text='Нет', callback_data='no')
            #   keyboard.add(key_like)
            bot.send_message(i, text=f'<i>{randoms[number][0]}\n</i>\n<b>{randoms[number][1]}</b>\n#{randoms[number][2]}',
                             parse_mode='HTML', reply_markup=keyboard)
        elif i in stopped:
            return None

# rand_quo()

schedule.every().day.at('14:00').do(rand_quo)
schedule.every(2).days.at('16:00').do(repost)



# on start
@bot.message_handler(commands=['start'])
def start(message):
    users_r = open('users', 'r')
    r = users_r.read().replace('\\n', '')
    r = r.splitlines()
    users_r.close()
    users_w = open('users', 'a')
    user_id = message.from_user.id
    bot.send_message(message.from_user.id,
                     '<b>Привет, я BookBot! 📚\n</b> \n<i>С данного момента, тебе каждый день, утром и вечером будут приходить случайные цитаты. Для того, чтобы узнать побольше о функционале бота - напиши /help \n</i>\nА также, в скором времени появится функция выбора любимых авторов, технология подбора цитат для Вас индивидуально, и много других интересных фишек! 😉',
                     parse_mode='HTML')
    if str(user_id) not in r:
        users_w.write(str(user_id) + '\n')
        print(message.from_user.username)
    users_w.close()


# on stop
@bot.message_handler(commands=['stop'])
def stop(message):
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
    if message.from_user.id in stopped:
        stopped.remove(message.from_user.id)
        bot.send_message(message.from_user.id, '<b>✔ Рассылка цитат возобновлена!</b>',
                         parse_mode='HTML')
    elif message.from_user.id not in stopped:
        bot.send_message(message.from_user.id, '<b>⚠ Вы еще не приостанавливали рассылку!</b>',
                         parse_mode='HTML')


# on help
@bot.message_handler(commands=['help'])
def help(message):
    commands = '<b>Список команд:\n</b>\n/stop<i> - приостановить рассылку\n</i>\n/resume<i> - возобновить рассылку\n</i>\n/report<i> - сообщить о проблеме или предложении</i>'
    bot.send_message(message.from_user.id, text=commands, parse_mode='HTML')


# on report
@bot.message_handler(commands=['report'])
def report(message):
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
    if message.voice is not None or message.audio is not None:
        bot.send_message(message.from_user.id, 'Ммм... Рай для моих ушей')


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    keyboard = types.InlineKeyboardMarkup()
    key_cancel = types.InlineKeyboardButton(text='Отменить', callback_data='cancel')
    keyboard.add(key_cancel)
    if call.data == "report":
        bot.send_message(call.message.chat.id,
                         '<i>Опишите проблему, Ваше сообщение будет доставлено администрации и принято на рассмотрение!\n</i>',
                         parse_mode='HTML', reply_markup=keyboard)
        bot.register_next_step_handler(call.message, report_send)
    elif call.data == "support":
        bot.send_message(call.message.chat.id,
                         '<i>Опишите Вашу идею, сообщение будет доставлено администрации и принято на рассмотрение!\n</i>',
                         parse_mode='HTML', reply_markup=keyboard)
        bot.register_next_step_handler(call.message, support_send)
    elif call.data == 'cancel':
        bot.send_message(call.message.chat.id,
                         '<b><i>Отменено!</i></b>',
                         parse_mode='HTML')

def report_send(message):
    bot.send_message(977341432,
                     f'❗ <b>Поступила жалоба:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.from_user.id, f'✔ <b>Жалоба успешно подана на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')

def support_send(message):
    bot.send_message(977341432,
                     f'💡 <b>Поступило предложение:\n</b>\n<i>{message.text}\n</i>\nот @{message.from_user.username}',
                     parse_mode='HTML')
    bot.send_message(message.from_user.id, f'✔ <b>Предложение успешно подано на рассмотрение!\n</b>\nСпасибо за Вашу помощь!',
                     parse_mode='HTML')




def polling():
    try:
        bot.polling(none_stop=True, interval=2)
    except:
        polling()


polling()
