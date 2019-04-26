# -*- coding: utf-8 -*-
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters

from db import calls_table, order_table, question_table, admin_table, service_table
from ..keyboards import yes_no_keyboard, main_keyboard, admin_home_keyboard
from ..welcome import cancel


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CALLS = range(1)

call_me_keyboard = [['Показать все'], ['Показать ещё не набраных'], ['Показать набраных'],
                    ['Фильтрация по времени звонка']]


def calls(bot, update):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    calls = calls_table.find({}).sort([['_id', 1]])
    if calls.count() == 0:
        update.message.reply_text('Нет заявок',
                                  reply_markup=ReplyKeyboardMarkup(admin_home_keyboard, one_time_keyboard=True))
    else:
        update.message.reply_text('Считается что юзеру позвонили через 30 мин после заданого в заявке времени. '
                                  'До того юзер не сможет оформить новую заявку'.format())

    return CALLS


recall_admin_conv = ConversationHandler(
    entry_points=[RegexHandler('^Перезвонить$', calls)],
    states={
        CALLS: []
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)