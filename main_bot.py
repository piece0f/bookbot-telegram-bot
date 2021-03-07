# -*- coding: utf-8 -*-
"""
BookBot is telegram bot, based on telegram API and MongoDB.
His objective is to send interesting quotes from books to users0.
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
with open('users0', 'r') as f:
    f = f.read().splitlines()
    callback_cancel = {int(user): False for user in f}
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


class UserInGroup(Exception):
    def __init__(self, text='user is already in group.'):
        self.txt = text


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
                '</i>\n/add<i> - предложить свою цитату\n'
                '</i>\n/quotes<i> - сменить частоту получения цитат (1 - 14.00, 2 - 12.00 + 20.00)</i>'
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


# messages from admin
def send(user_id, message):
    """Sends message requested from admin to user"""
    try:
        bot.send_message(user_id,
                         '<b>Сообщение от администрации!</b>\n\n' + message,
                         parse_mode='HTML'
                         )
        print(f'Sent message to {user_id}:\n{message}')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Bad ID ({user_id}):", e)
    except Exception as e:
        print(e)


# changes user's time for quote
def change_group(user_id, group):
    before = 0
    for i in range(1, 3):
        with open(f'users{i}', 'r') as file_read:
            group_list = file_read.readlines()
            if user_id + '\n' in group_list and i == group:
                raise UserInGroup()
        if user_id + '\n' in group_list:
            group_list.remove(user_id + '\n')
            before = i
            with open(f'users{i}', 'w') as file_write:
                file_write.write(''.join(group_list))
        elif i == group:
            group_list.append(user_id + '\n')
            with open(f'users{i}', 'w') as file_write:
                file_write.write(''.join(group_list))
    print(f'{user_id} changed his group from {before} to {group}.')


def quote_4_user_checker(user_id: str, check=True):
    """Checks for quote available for {user}"""
    est_quotes = quotes.estimated_document_count()
    if quotes.count_documents({"Users": user_id}) >= est_quotes - 1:
        # removes user id from DB if there is no more available quotes for user
        quotes.update_many({"Users": user_id}, {"$pull": {"Users": user_id}})
    all_quotes = quotes.find({})
    while True:
        quote = all_quotes[random.randint(0, est_quotes - 1)]
        if not check:
            # if check for available is not required return random quote
            return quote
        if user_id in quote["Users"]:
            continue
        required_quote = quote
        quotes.update_one({"Quote": quote["Quote"]}, {"$push": {"Users": user_id}})
        return required_quote


def promo():
    """Sends a little promotional message for all users0 (except my gf)"""
    with open('users0', 'r') as users_r:
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


def random_quotes(group: int):
    """Sends random quote for users0 who aren't in 'stopped' list"""
    start_time = time.time()
    counter = 0
    with open(f'users{group}', 'r') as users_r:
        r = users_r.read().splitlines()
    for user_id in r:
        if user_id in stopped:
            continue
        try:
            random_q(user_id, True)
            print(f"Latency #{counter}: {str(time.time() - start_time)[:4]} seconds")
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Bad ID ({user_id}):", e)
        except Exception as e:
            print(e)
        finally:
            counter += 1


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
    return


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


schedule.every().day.at('14:00').do(random_quotes, group=1)
schedule.every().day.at('12:00').do(random_quotes, group=2)
schedule.every().day.at('20:00').do(random_quotes, group=2)

schedule.every(2).days.at('16:00').do(promo)


# [ADMIN]
@bot.message_handler(commands=['quote', 'promo', 'send'])
def admin(message):
    """Admin message handler, answers on admin requests"""
    print('Admin command execution...')
    if message.from_user.id != 977341432:
        print('False: Non-admin request')
        return
    if message.text.startswith('/quote'):
        random_quotes(0)
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
    with open('users0', 'r') as users_r:
        r = users_r.read().splitlines()
    user_id = message.from_user.id
    bot.send_message(user_id,
                     '<b>Привет, я BookBot! 📚\n</b> \n<i>С данного момента, тебе каждый день будут приходить случайные цитаты. Для того, чтобы узнать побольше о функционале бота - напиши /help \n</i>\nА также, в скором времени появится функция выбора любимых авторов, технология подбора цитат для Вас индивидуально, и много других интересных фишек! 😉',
                     parse_mode='HTML')
    if str(user_id) in r:
        return
    with open('users0', 'a') as users_w, open('users1', 'a') as users_w2:
        users_w.write(str(user_id) + '\n')
        users_w2.write(str(user_id) + '\n')
        print(message.from_user.username, 'connected to bot.')
    quote = quote_4_user_checker(user_id)
    keyboard = types.InlineKeyboardMarkup()
    key_book = types.InlineKeyboardButton(text='📖', callback_data='book', url=quote["URL"])
    keyboard.add(key_book)
    bot.send_message(user_id,
                     text=f'Держи свою первую цитату!\n\n<i>{quote["Quote"]}\n</i>\n<b>{quote["Book"]}</b>\n#{quote["Author"]}',
                     parse_mode='HTML')
    callback_cancel.update({int(message.from_user.id): False})


# user commands handler
@bot.message_handler(commands=['stop', 'resume', 'help', 'report', 'random', 'add', 'quotes'])
def commands_handler(message):
    command = message.text
    if command == '/stop':
        stop(message)
    elif command == '/resume':
        resume(message)
    elif command == '/help':
        help_command(message)
    elif command.startswith('/quotes'):
        if len(command.split()) == 1:
            bot.send_message(message.from_user.id,
                             '<b>Смена частоты получения цитат:</b>\n\n'
                             '<i>/quotes N\n'
                             'N - число от 1 до 2 (1 - 14.00, 2 - 12.00 + 20.00)</i>',
                             parse_mode='HTML')
            return
        try:
            queried_group = int(command[-1])
            if queried_group not in (1, 2):
                raise ValueError(f'wrong group number - {queried_group}')
            change_group(str(message.from_user.id), queried_group)
            bot.send_message(message.from_user.id,
                             '✔ <b>Вы успешно сменили группу!</b>',
                             parse_mode='HTML')
        except ValueError:
            bot.send_message(message.from_user.id,
                             '⚠ <b>Неправильный формат!</b>\n\n<i>Группа должна быть числом от 1 до 2!</i>',
                             parse_mode='HTML')
        except UserInGroup:
            bot.send_message(message.from_user.id,
                             '⚠ <b>Вы уже находитесь в этой группе!</b>',
                             parse_mode='HTML')
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
        callback_cancel[call.message.chat.id] = True
        bot.send_message(call.message.chat.id,
                         '<b><i>Отменено!</i></b>',
                         parse_mode='HTML')


def polling():
    try:
        bot.polling(none_stop=True, interval=1)
    # noinspection PyBroadException
    except Exception:
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

# random_quotes(1)

polling()
