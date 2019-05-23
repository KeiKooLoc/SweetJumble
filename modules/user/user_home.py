# -*- coding: utf-8 -*-
import logging
from telegram import ReplyKeyboardMarkup, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, RegexHandler, CallbackQueryHandler, MessageHandler, Filters
from bson import ObjectId

from db import calls_table, order_table, question_table
from ..welcome import cancel, start

from ..help_func import Send
from modules.helper_funcs.pagination import Pagination
from modules.helper_funcs.templates import order_template

from ..keyboards import yes_no_keyboard, user_home_keyboard, main_keyboard

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# USER_HOME, ORDERSs, QUESTIONS, CALL, CANCEL_CALL, CONFIRM_CLEAR_ORDERS_LIST, CONFIRM_CLEAR_QUESTIONS_LIST = range(7)

START, ORDERS, CONFIRM_DELETE_ORDER, CALLS = range(4)


def delete(bot, user_data, chat_id):
    if 'to_delete' in user_data:
        for msg_id in user_data['to_delete']:
            bot.delete_message(chat_id, msg_id)
        user_data['to_delete'] = list()
    else:
        user_data['to_delete'] = list()


# TODO: remember last page when back to orders
#       trash
class UserHome(object):
    def __init__(self):
        self.start_keyboard = ReplyKeyboardMarkup([['Заказы'], ['Вопросы'], ['Заявка на перезвон'], ['Назад']])
        self.orders_keyboard = ReplyKeyboardMarkup([['Показать все'], ['Показать оплаченые'], ['Показать не оплаченые'], ['Назад']])
        self.start_message = '{}, добро пожаловать в Личный Кабинет'

    def start(self, bot, update, user_data):
        delete(bot, user_data, update.effective_chat.id)
        bot.delete_message(update.effective_chat.id, update.message.message_id)

        user_data['to_delete'].append(
            update.message.reply_text(self.start_message.format(update.effective_user.full_name),
                                      reply_markup=self.start_keyboard).message_id)
        return START

    # delete messages
    def orders(self, bot, update, user_data):
        delete(bot, user_data, update.effective_chat.id)
        bot.send_chat_action(update.effective_chat.id, action=ChatAction.TYPING)

        if order_table.find({'user_id': update.effective_user.id}).count() == 0:
            user_data['to_delete'].append(
                update.message.reply_text('Нет заказов', reply_markup=self.start_keyboard))
            return START
        # maybe don't show buttons that got no effect
        if update.message:
            bot.delete_message(update.effective_chat.id, update.effective_message.message_id)
            page = 1
            if update.message.text == 'Показать оплаченые':
                user_data['filter'] = True
                self.orders_keyboard = ReplyKeyboardMarkup([['Показать все'], ['Показать не оплаченые'], ['Назад']])

            elif update.message.text == 'Показать не оплаченые':
                user_data['filter'] = False
                self.orders_keyboard = ReplyKeyboardMarkup([['Показать все'], ['Показать оплаченые'], ['Назад']])

            elif update.message.text == 'Показать все' or update.message.text == 'Заказы':
                user_data['filter'] = 'all'
                self.orders_keyboard = ReplyKeyboardMarkup([['Показать оплаченые'], ['Показать не оплаченые'], ['Назад']])
        else:
            # TODO: correct it. ValueError when back from finish_delete_order
            #       remember last page when back to orders
            try:
                page = int(update.callback_query.data)
            except ValueError:
                page = 1
        data, pages_keyboard, total_pages = \
            Pagination(order_table, status=user_data['filter'], user_id=update.effective_user.id).get(page=page)

        if len(data) == 0:
            user_data['to_delete'].append(
                update.message.reply_text('Нет Заказов', reply_markup=self.start_keyboard)
            )
            return START

        Send(bot, data, update.effective_chat.id, user_data).send_orders_to_user(data)

        if total_pages > 1:
            user_data['to_delete'].append(
                bot.send_message(update.effective_chat.id, 'Current page: {}'.format(str(page)),
                                 reply_markup=pages_keyboard).message_id
            )
        user_data['to_delete'].append(
            bot.send_message(update.effective_chat.id, '\u2060', reply_markup=self.orders_keyboard).message_id
        )
        return ORDERS

    def confirm_delete_order(self, bot, update, user_data):
        delete(bot, user_data, update.effective_chat.id)
        # bot.delete_message(update.effective_chat.id, update.effective_message.message_id)

        order = order_table.find_one({"_id": ObjectId(update.callback_query.data.split('/')[1])})
        if order:
            user_data['to_delete'].append(
                bot.send_message(update.effective_chat.id,
                                 'Все удалённые записи перемещаются в корзину из которой их можно восстановить. '
                                 '\nУдалить запись?', reply_markup=ReplyKeyboardMarkup([['Назад']])).message_id
            )
            # use callback data or user_data?
            user_data['to_delete'].append(
                bot.send_message(update.effective_chat.id, order_template(order, comment=False),
                                 reply_markup=InlineKeyboardMarkup(
                                 [[InlineKeyboardButton('Удалить', callback_data='id/{}'.format(order['_id']))]])).message_id
            )

        else:
            # TODO correct
            pass
        return CONFIRM_DELETE_ORDER

    def finish_delete_order(self, bot, update, user_data):
        move_to_trash = \
            order_table.update_one({'_id': ObjectId(update.callback_query.data.split('/')[1])}, {'$set': {'in_user_trash': True}})
        if move_to_trash.raw_result['n']:
            user_data['to_delete'].append(
                bot.send_message(update.effective_chat.id, 'Заказ удалён успешно').message_id
            )
            bot.answer_callback_query(update.callback_query.id, 'Заказ перенесён в корзину')
            return self.orders(bot, update, user_data)
        else:
            # TODO correct
            user_data['to_delete'].append(
                bot.send_message(chat_id=update.effective_chat.id, text='не удалось удалить заказ, видимо он уже удалён',
                                 reply_markup=self.start_keyboard).message_id)
        return START

    def pay(self, bot, update, user_data):
        pass

    def back(self, bot, update):
        bot.delete_message(update.effective_chat.id, update.message.message_id)
        update.message.reply_text('Sweet Jumble первое и самое крупное агентство персональных стилистов-шопперов в '
                                  'Украине', reply_markup=ReplyKeyboardMarkup(main_keyboard))
        return ConversationHandler.END


user_home_conv = ConversationHandler(
    entry_points=[RegexHandler('^Личный кабинет$', UserHome().start, pass_user_data=True),
                  CommandHandler('home', UserHome().start, pass_user_data=True)],

    states={
        START: [RegexHandler('^Заказы$', UserHome().orders, pass_user_data=True),
                # RegexHandler('^Вопросы$', questions),
                # RegexHandler('^Заявка на перезвон$', user_call, pass_user_data=True),
                RegexHandler('^Назад$', UserHome().back),
                ],

        ORDERS: [CallbackQueryHandler(UserHome().orders, pattern='^[0-9]+$', pass_user_data=True),
                 CallbackQueryHandler(UserHome().confirm_delete_order, pattern=r'delete', pass_user_data=True),
                 # CallbackQueryHandler(UserHome().pay, pattern=r'pay', pass_user_data=True),
                 RegexHandler('^Назад$', UserHome().start, pass_user_data=True),
                 MessageHandler(Filters.text, UserHome().orders, pass_user_data=True)  # TODO: change this line
                                                                                       #          (order_status_filter)
        ],

        CONFIRM_DELETE_ORDER: [CallbackQueryHandler(UserHome().finish_delete_order, pattern=r'id', pass_user_data=True),
                               RegexHandler('^Назад$', UserHome().orders, pass_user_data=True)]

        # CALLS: [RegexHandler('^Удалить заявку$', cancel_call, pass_user_data=True),
        #        RegexHandler('Назад', user_home)],

        # CANCEL_CALL: [RegexHandler('^Назад$', user_call, pass_user_data=True),
        #               RegexHandler('^Да$', cancel_call_success, pass_user_data=True)],

        # QUESTIONS: [  # RegexHandler('^Очистить список$', confirm_clear_question_list),
        #             RegexHandler('^Назад$', user_home)],

    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)

"""
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
    call_me_data = calls_table.find_one({'user_id': update.effective_user.id, 'status': False})
    if not call_me_data:
        update.message.reply_text('У вас нет активных заявок на перезвон',
                                  reply_markup=ReplyKeyboardMarkup(user_home_keyboard, one_time_keyboard=True))
        return USER_HOME

    keyboard = [['Удалить заявку'], ['Назад']]
    data_to_send = 'Мы вам наберём ' + call_template(call_me_data)
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



user_home_conv = ConversationHandler(
    entry_points=[RegexHandler('^Личный кабинет$', UserHome().start),
                  CommandHandler('home', user_home)],

    states={
        USER_HOME: [RegexHandler('^Заказы$', UserHome().orders, pass_user_data=True),
                    RegexHandler('^Вопросы$', questions),
                    RegexHandler('^Заявка на перезвон$', user_call, pass_user_data=True),
                    RegexHandler('^Назад$', start)],

        ORDERS: [CallbackQueryHandler(UserHome().confirm_delete, pass_user_data=True)],

        CONFIRM_DELETE_ORDER: [],

        CALLS: [RegexHandler('^Удалить заявку$', cancel_call, pass_user_data=True),
               RegexHandler('Назад', user_home)],

        CANCEL_CALL: [RegexHandler('^Назад$', user_call, pass_user_data=True),
                      RegexHandler('^Да$', cancel_call_success, pass_user_data=True)],


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
"""
