# -*- coding: utf-8 -*-
import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters
import datetime

from db import question_table
from ..keyboards import main_keyboard, yes_no_keyboard
from ..welcome import cancel, start

from ..help_func import send_notification_to_admins

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ASK, ASK_CONFIRM = range(2)


def ask(bot, update):
    # Check if user already got not answered questions
    if question_table.find({'username': update.message.chat.username, 'answer': 0}).count() > 9:
        update.message.reply_text('Вы уже задавали несколько вопросов на которые ещё не дали ответы. '
                                  'У вас будет возможность задать новый вопрос после того как мы ответим на предыдущие',
                                  reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
        return ConversationHandler.END

    update.message.reply_text('Доброго времени суток. Задайте любой вопрос по стилю и мы ответим вам в ближайшее время.'
                              ' Ответ вы сможете посмотреть нажав на кнопку Личный кабинет '
                              'Вам прийдёт уведомление об ответе',
                              reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
    return ASK


def ask_confirm(bot, update, user_data):
    msg = update.message.text
    update.message.reply_text('Ваш вопрос: {} Отправить?'.format(msg),
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))
    user_data['question'] = update.message.text

    return ASK_CONFIRM


def ask_confirm_true(bot, update, user_data):
    question_table.insert_one(
        {
            'username': update.message.chat.username,
            'question': user_data['question'],
            'answer': 0,
            'timestamp': datetime.datetime.now()
        })
    send_notification_to_admins(bot, 'Новый вопрос. @{}'.format(update.message.chat.username))
    update.message.reply_text('Ваш вопроc отправлен на обработку, Вы сможете посмотреть вопрос и ответ на него нажав '
                              'на кнопку Личный кабинет. Вам прийдёт уведомление об ответе.',
                              reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


ask_conv = ConversationHandler(
    entry_points=[RegexHandler('^Задать вопрос$', ask),
                  CommandHandler('ask', ask)],

    states={
            ASK: [RegexHandler('^Назад$', start),
                  MessageHandler(Filters.text, ask_confirm, pass_user_data=True)],

            ASK_CONFIRM: [RegexHandler('^Да$', ask_confirm_true, pass_user_data=True),
                          RegexHandler('^Назад$', ask)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)
