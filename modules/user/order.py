# -*- coding: utf-8 -*-
import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters
import datetime

from db import order_table, service_table
from ..welcome import cancel, start
from ..help_func import send_notification_to_admins
from ..keyboards import yes_no_keyboard, main_keyboard

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SERVICES, SERVICE, DO_ORDER, ORDER_CONFIRM = range(4)


# Help function
def make_service_keyboard(category):
    return [[i['name']] for i in service_table.find({'category': category})] + [['Назад']]
#


def services(bot, update, user_data):
    if update.message.text != 'Назад':
        user_data['category'] = update.message.text
    update.message.reply_text('Выберете услугу которую хотите заказать или о которой хотите узнать больше',
                              reply_markup=ReplyKeyboardMarkup(make_service_keyboard(user_data['category']),
                                                               one_time_keyboard=True))
    return SERVICES


def service(bot, update, user_data):
    msg = update.message.text
    if msg != 'Назад':
        user_data['service'] = update.message.text
    service_info = service_table.find_one({'name': user_data['service']})
    update.message.reply_text('{}. '
                              'Цена: {} '
                              'Продолжительность: {} '
                              '{}'.format(service_info['name'],
                                          service_info['price'],
                                          service_info['duration'],
                                          service_info['description']),
                              reply_markup=ReplyKeyboardMarkup([['Заказать'], ['Назад']], one_time_keyboard=True))
    return SERVICE


def do_order(bot, update, user_data):
    # Check that the user has already ordered the service
    if order_table.find_one({'username': update.message.chat.username, 'service': user_data['service'], 'paid': 'Нет'}):
        update.message.reply_text('Вы уже заказали {}. '
                                  'Ваш заказ отправлен на обработку. Наш специалист свяжется с вами в ближайшее время '
                                  'Вы можете просмотреть список заказов нажав на кнопку Личный кабинет.'.format(
                                    user_data['service']),
                                  reply_markup=ReplyKeyboardMarkup(make_service_keyboard(user_data['category']),
                                                                   one_time_keyboard=True))
        return SERVICES

    update.message.reply_text('Отправьте сообщение в формате имя телефон. '
                              'К примеру Юра 0635271986',
                              reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
    return DO_ORDER


def order_confirm(bot, update, user_data):
    msg = update.message.text
    order_data = msg.split(' ')

    # CHECK USER MESSAGE
    error_msg = 'Ошибка ввода. {info}. Отправьте сообщение в формате имя телефон. ' \
                'К примеру: Юра 0635271986'
    order_template = ['Юра', '0635271986']

    # Check that message consist of 4 parts
    if len(order_data) != len(order_template):
        update.message.reply_text(error_msg.format(info='Ваше сообщение состоит не из %s частей') % len(order_template))
        return DO_ORDER

    # Check that each part of message less then 30 characters
    for i in order_data:
        if len(list(i)) > 30:
            update.message.reply_text(error_msg.format(info='Слишком длинное сообщение'))
            return DO_ORDER

    # How can I check phone number??
    # check that number contains only ints
    try:
        for num in list(order_data[-1]):  # phone number on last index in message
            int(num)
    except ValueError:
        update.message.reply_text(error_msg.format(info='Телефонный номер должен состоять только из цифр'))
        return DO_ORDER
    if len(order_data[-1]) < 5:
        update.message.reply_text(error_msg.format(info='Cлишком короткий телефонный номер '))
        return DO_ORDER

    update.message.reply_text('Заказуваемая Улсуга: {}. Заказ на {}. Отправить запрос?'.format(user_data['service'], msg),
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))
    user_data['name'] = order_data[0]
    user_data['number'] = order_data[1]
    return ORDER_CONFIRM


def order_confirm_true(bot, update, user_data):
    order_table.insert_one(
        {
            'username': update.message.chat.username,
            'name': user_data['name'],
            'number': user_data['number'],
            'service': user_data['service'],
            'category': user_data['category'],
            'paid': 'Нет',
            'comment': 0,
            'timestamp': datetime.datetime.now()
        })
    send_notification_to_admins(bot, 'Пользователь @{} заказал услугу!'.format(update.message.chat.username))
    update.message.reply_text('Ваш заказ отправлен на обработку. Наш специалист свяжется с вами в ближайшее время '
                              'Вы можете просмотреть список заказов нажав на кнопку Личный кабинет.',
                              reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


order_conv = ConversationHandler(
    entry_points=[RegexHandler('^Услуги стилистов$', services, pass_user_data=True),
                  RegexHandler('^Школа шоппера$', services, pass_user_data=True),
                  CommandHandler('order', services)],

    # do better SERVICES state
    states={
        SERVICES: [RegexHandler('^Назад$', start),
                   RegexHandler('^КОНСУЛЬТАЦИЯ СТИЛИСТА$', service, pass_user_data=True),
                   RegexHandler('^АНАЛИЗ ГАРДЕРОБА$', service, pass_user_data=True),
                   RegexHandler('^ШОППИНГ СО СТИЛИСТОМ$', service, pass_user_data=True),
                   RegexHandler('^САМ СЕБЕ ШОППЕР$', service, pass_user_data=True),
                   RegexHandler('^ДЛЯ НАЧИНАЮЩИХ$', service, pass_user_data=True),
                   RegexHandler('^ДЛЯ ПРОФЕССИОНАЛА$', service, pass_user_data=True),
                   RegexHandler('^VIP ОБУЧЕНИЕ$', service, pass_user_data=True)
                   ],

        SERVICE: [RegexHandler('^Назад$', services, pass_user_data=True),
                  RegexHandler('^Заказать$', do_order, pass_user_data=True)],

        DO_ORDER: [RegexHandler('^Назад$', service, pass_user_data=True),
                   MessageHandler(Filters.text, order_confirm, pass_user_data=True)],

        ORDER_CONFIRM: [RegexHandler('^Назад$', do_order, pass_user_data=True),
                        RegexHandler('^Да$', order_confirm_true, pass_user_data=True)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)
