# -*- coding: utf-8 -*-
import logging
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, RegexHandler

from db import calls_table, order_table, question_table
from ..welcome import cancel, start
from ..help_func import send_notification_to_admins
from ..keyboards import yes_no_keyboard, user_home_keyboard

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_HOME, ORDERS, QUESTIONS, CALL, CANCEL_CALL, CONFIRM_CLEAR_ORDERS_LIST, CONFIRM_CLEAR_QUESTIONS_LIST = range(7)


def user_home(bot, update):
    update.message.reply_text('Это ваш личный кабинет где вы можете просмотреть овтеты на ваши вопросы или ваши заказы',
                              reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
    return USER_HOME


def orders(bot, update):
    orders_data = order_table.find({'username': update.message.chat.username}).sort([['_id', 1]])
    if orders_data.count() == 0:
        update.message.reply_text('У вас ещё не было заказов',
                                  reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
        return USER_HOME
    data_to_send = '\n'.join(['Заказ на: ' + i['name'] +
                              '. Номер: ' + i['number'] +
                              '. Услуга: ' + i['category'] + ' - ' + i['service'] +
                              '. Оплачено: ' + i['paid'] +
                              '. Дата оформления: ' + str(i['timestamp']).split('.')[0] for i in orders_data])
    update.message.reply_text(data_to_send,
                              reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
    return USER_HOME


def questions(bot, update):
    questions_data = question_table.find({'username': update.message.chat.username}).sort([['_id', 1]])
    if questions_data.count() == 0:
        update.message.reply_text('Вы не задавали ещё ни одного вопроса',
                                  reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
        return USER_HOME
    data_to_send = '\n'.join(['Вопрос: ' + i['question'] +
                              '. Ответ: ' + str(i['answer']) +
                              '. Дата: ' + str(i['timestamp']).split('.')[0] for i in questions_data])
    update.message.reply_text(data_to_send,
                              reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
    return USER_HOME


def user_call(bot, update, user_data):
    call_me_data = calls_table.find_one({'username': update.message.chat.username, 'have_called': 0})
    if not call_me_data:
        update.message.reply_text('У вас нет активных заявок на перезвон',
                                  reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
        return USER_HOME

    keyboard = [['Удалить заявку'], ['Назад']]
    data_to_send = 'Мы вам наберём ' + str(call_me_data['date']['month']) + ':' + str(call_me_data['date']['day']) + \
                   '\nВ ' + str(call_me_data['date']['hour']) + ':' + str(call_me_data['date']['min']) + \
                   '\nНа номер: ' + call_me_data['number']
    user_data['data_to_send'] = data_to_send
    user_data['_id'] = call_me_data['_id']
    update.message.reply_text(data_to_send,
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CALL


def cancel_call(bot, update, user_data):
    update.message.reply_text(user_data['data_to_send'] + '\nОтменить заявку?',
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))
    return CANCEL_CALL


def cancel_call_success(bot, update, user_data):
    calls_table.delete_one({'_id': user_data['_id']})
    send_notification_to_admins(bot, '@{} Удалили заявку о перезвоне'.format(update.message.chat.username))
    update.message.reply_text('Заявка на перезвон удалена. Вы можете оформить новую в любое время',
                              reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
    return USER_HOME


"""
def confirm_clear_order_list(bot, update):
    keyboard = [['Да', 'Назад']]
    update.message.reply_text(data['user']['orders'] + '      Удалить все записи?',
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CONFIRM_CLEAR_ORDERS_LIST


def questions(bot, update):
    keyboard = [['Очистить список'], ['Назад']]
    # question_table.find({'username':})
    update.message.reply_text(data['user']['questions'],
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return QUESTIONS


def confirm_clear_question_list(bot, update):
    keyboard = [['Да', 'Назад']]
    update.message.reply_text(data['user']['questions'] + '      Удалить все записи?',
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CONFIRM_CLEAR_QUESTIONS_LIST


def clear_list_confirm_true(bot, update):
    update.message.reply_text('Записи удалены',
                              reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
    return USER_HOME

"""


user_home_conv = ConversationHandler(
    entry_points=[RegexHandler('^Личный кабинет$', user_home),
                  CommandHandler('home', user_home)],

    states={
        USER_HOME: [RegexHandler('^Заказы$', orders),
                    RegexHandler('^Вопросы$', questions),
                    RegexHandler('^Заявка на перезвон$', user_call, pass_user_data=True),
                    RegexHandler('^Назад$', start)],

        CALL: [RegexHandler('^Удалить заявку$', cancel_call, pass_user_data=True),
               RegexHandler('Назад', user_home)],

        CANCEL_CALL: [RegexHandler('^Назад$', user_call, pass_user_data=True),
                      RegexHandler('^Да$', cancel_call_success, pass_user_data=True)],

        ORDERS: [  # RegexHandler('^Очистить список$', confirm_clear_order_list),
                 RegexHandler('^Назад$', user_home)],

        # CONFIRM_CLEAR_ORDERS_LIST: [RegexHandler('^Да$', clear_list_confirm_true),
        #                            RegexHandler('^Назад$', orders)],

        QUESTIONS: [  # RegexHandler('^Очистить список$', confirm_clear_question_list),
                    RegexHandler('^Назад$', user_home)],

        # CONFIRM_CLEAR_QUESTIONS_LIST: [RegexHandler('^Да$', clear_list_confirm_true),
        #                                RegexHandler('^Назад$', questions)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)
