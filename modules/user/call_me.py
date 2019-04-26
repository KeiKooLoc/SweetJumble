# -*- coding: utf-8 -*-
import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters

from db import calls_table
from ..welcome import cancel, start
from ..keyboards import main_keyboard, yes_no_keyboard
from ..help_func import send_notification_to_admins


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CALL_ME, CALL_ME_CONFIRM = range(2)


def call_me(bot, update, user_data):
    # Check that user already got the call me note
    # TODO: check that date are in 30 min interval
    msg_in_db = calls_table.find_one({'user_id': update.effective_user.id, 'have_called': 0})
    if msg_in_db:
        # Need correct back to the prev state!
        update.message.reply_text('Вы уже оставляли заявку {}. '
                                  'Вы можете отменить заявку в Личном кабинете /home'.format(
                                    msg_in_db['date']['month'] + '-' + msg_in_db['date']['day'] + ' ' +
                                    msg_in_db['date']['hour'] + '-' + msg_in_db['date']['min'] + ' ' +
                                    msg_in_db['name'] + ' ' + msg_in_db['number']),
                                  reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
        return ConversationHandler.END

    update.message.reply_text('Наше рабочее время Пн-Пт с 9:00 до 20:00. '
                              'Отправьте сообщение в формате месяц-день час-минута имя телефон. '
                              'К примеру: 04-15 17-45 Юра 0635271986',
                              reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
    return CALL_ME


def call_me_confirm(bot, update, user_data):
    msg = update.message.text
    call_me_data = msg.split(' ')

    # VALIDATE USER MESSAGE
    # TODO: check that date are not past
    error_msg = 'Ошибка ввода. {info}. Отправьте сообщение в формате месяц-день час-минута имя телефон. ' \
                'К примеру: 04-15 17-45 Юра 0635271986'
    template = ['04-15', '17-45', 'Юра', '0635271986']

    # Check that message consist of 4 parts
    if len(call_me_data) != len(template):
        update.message.reply_text(error_msg.format(info='Ваше сообщение состоит не из %s частей') % len(template))
        return CALL_ME

    # Check that each part of message less then 30 characters
    for i in call_me_data:
        if len(list(i)) > 30:
            update.message.reply_text(error_msg.format(info='Слишком длинное сообщение'))
            return CALL_ME

    # How can I check phone number??
    # check phone number(contains only ints and len)
    try:
        for num in list(call_me_data[-1]):
            int(num)
    except ValueError:
        update.message.reply_text(error_msg.format(info='Телефонный номер должен состоять только из цифр '))
        return CALL_ME

    if len(call_me_data[-1]) < 5:
        update.message.reply_text(error_msg.format(info='Cлишком короткий телефонный номер '))
        return CALL_ME

    # не дать возможность отправить сообщение с прошлой датой или прошлым временем
    # Check that date and time in message are correct
    try:
        month = int(call_me_data[0].split('-')[0])
        day = int(call_me_data[0].split('-')[1])
        hour = int(call_me_data[1].split('-')[0])
        min = int(call_me_data[1].split('-')[1])
    except (ValueError, IndexError):
        update.message.reply_text(error_msg.format(info='Формат даты или времени не верный '))
        return CALL_ME

    if not 1 <= month <= 12:  # month < 1 or month > 12:
        update.message.reply_text(error_msg.format(info='Слишком большое или маленькое число в месяце'))
        return CALL_ME
    if not 1 <= day <= 31:  # day < 1 or day > 31:
        update.message.reply_text(error_msg.format(info='Слишком большое или маленькое число в дне'))
        return CALL_ME
    if not 9 <= hour <= 20:  # hour < 9 or hour > 20:
        update.message.reply_text(error_msg.format(info='Наше рабочее время с 9:00 до 20:00'))
        return CALL_ME
    if not 0 <= min < 60:   # min < 0 or min > 59:
        update.message.reply_text(error_msg.format(info='Минутная стрелка часов никогда не показывала на такое время)'))
        return CALL_ME

    update.message.reply_text('{}, всё верно?'.format(msg),
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))

    user_data['month'] = str(month) if len(str(month)) == 2 else '0' + str(month)
    user_data['day'] = str(day) if len(str(day)) == 2 else '0' + str(day)
    user_data['hour'] = str(hour) if len(str(hour)) == 2 else '0' + str(hour)
    user_data['min'] = str(min) if len(str(min)) == 2 else '0' + str(min)
    user_data['name'] = call_me_data[2]
    user_data['number'] = call_me_data[3]
    return CALL_ME_CONFIRM


def call_me_confirm_true(bot, update, user_data):
    msg_in_db = calls_table.find_one({'username': update.message.chat.username, 'have_called': 0})
    if msg_in_db:
        calls_table.update_one(
            {
                'username': update.message.chat.username,
                'have_called': 0
            },
            {
                '$set': {
                            'date.month': user_data['month'],
                            'date.day': user_data['day'],
                            'date.hour': user_data['hour'],
                            'date.min': user_data['min'],
                            'name': user_data['name'],
                            'number': user_data['number']
                        }
            })
        # Send notification to admins
        send_notification_to_admins(bot, 'Пользователь @{} изменил запрос на перезвонить.'.format(
                update.message.chat.username))

    else:
        calls_table.insert_one(
            {
                'user_id': update.effective_user.id,
                'date': {
                            'month': user_data['month'],
                            'day': user_data['day'],
                            'hour': user_data['hour'],
                            'min': user_data['min']
                        },
                'name': user_data['name'],
                'number': user_data['number'],
                'have_called': 0
            })
        # Send notification to admins
        send_notification_to_admins(bot, 'Новый запрос на перезвонить.'
                                         'От: @{}'.format(update.message.chat.username))

    # yura, Мы перезвоним 4:26, в 18:0 на номер 0635271987
    update.message.reply_text('{}, Мы перезвоним {}, в {} на номер {}'.format(user_data['name'],
                                                                              user_data['month'] + ':' + user_data['day'],
                                                                              user_data['hour'] + ':' + user_data['min'],
                                                                              user_data['number']),
                              reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))

    return ConversationHandler.END


call_me_conv = ConversationHandler(
    entry_points=[RegexHandler('^Перезвоните мне$', call_me, pass_user_data=True),
                  CommandHandler('call_me', call_me, pass_user_data=True)],

    states={
            CALL_ME: [RegexHandler('^Назад$', start),
                      MessageHandler(Filters.text, call_me_confirm, pass_user_data=True)],

            CALL_ME_CONFIRM: [RegexHandler('^Да$', call_me_confirm_true, pass_user_data=True),
                              RegexHandler('^Назад$', call_me, pass_user_data=True)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)
