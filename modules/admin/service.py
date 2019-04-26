# -*- coding: utf-8 -*-
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, RegexHandler, Filters

from db import calls_table, order_table, question_table, admin_table, service_table
from ..keyboards import main_keyboard, yes_no_keyboard, admin_home_keyboard
from ..welcome import cancel, admin_home

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ORDERS_ADMIN, CHOOSE_ORDER, EDIT_ORDER, ADD_COMMENT, CHANGE_STATUS, CONFIRM_REMOVE = range(6)

main_order_keyboard = [['Редакторовать'], ['Фильтрация по статусу оплаты'], ['Фильтрация по времени'], ['Назад']]
single_order_keyboard = [['Добавить комментарий'], ['Изменить статус оплаты'], ['Удалить'], ['Назад']]


def orders_admin(bot, update):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    all_orders = order_table.find().sort([['_id', 1]])

    if all_orders.count() == 0:
        update.message.reply_text('Нет Заказов',
                                  reply_markup=ReplyKeyboardMarkup(admin_home_keyboard, one_time_keyboard=True))
        return ConversationHandler.END

    data_to_send = '\n'.join([' От: @' + str(i['username']) +  #  if username?
                              '. Имя: ' + str(i['name']) +
                              '. Телефон: ' + str(i['number']) +
                              '. Услуга: ' + i['category'] + ' - ' + str(i['service']) +
                              '. Оплачена: ' + i['paid'] +
                              '. Время: ' + str(i['timestamp']).split('.')[0] +
                              '. Комментарий: ' + str(i['comment']) for i in all_orders])
    update.message.reply_text(data_to_send, reply_markup=ReplyKeyboardMarkup(main_order_keyboard, one_time_keyboard=True))
    return ORDERS_ADMIN


def choose_order_to_edit(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    keyboard = [[], ['Назад']]
    all_orders = order_table.find().sort([['_id', 1]])

    user_data['orders'] = dict()
    for num, i in enumerate(all_orders):
        user_data['orders'][num + 1] = i
        if len(keyboard[-2]) == 5:
            keyboard.insert(len(keyboard) - 1, [])
        keyboard[-2].append(str(num + 1))

    data_to_send = '\n'.join(['№ ' + str(num) +
                              ' От: @' + str(i['username']) +  # if username?
                              '. Имя: ' + str(i['name']) +
                              '. Телефон: ' + str(i['number']) +
                              '. Услуга: ' + str(i['category']) + ' - ' + str(i['service']) +
                              '. Оплачена: ' + str(i['paid']) +
                              '. Время: ' + str(i['timestamp']).split('.')[0] +
                              '. Комментарий: ' + str(i['comment']) for num, i in user_data['orders'].items()])

    user_data['data_to_send'] = data_to_send
    user_data['keyboard'] = keyboard
    update.message.reply_text(data_to_send + '\nВыберете номер заказа который хотите отредактировать',
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CHOOSE_ORDER


def edit_order(bot, update, user_data):
    try:
        order = user_data['orders'][int(update.message.text)]
    except (ValueError, TypeError, KeyError):
        # Need to correct back to the prev state!
        update.message.reply_text(user_data['data_to_send'] + '\nВыберете номер заказа который хотите отредактировать',
                                  reply_markup=ReplyKeyboardMarkup(user_data['keyboard'], one_time_keyboard=True))
        return CHOOSE_ORDER

    user_data['order'] = order
                                 # if username?
    user_data['order_to_send'] = ' От: @' + str(order['username']) + \
                                 '. Имя: ' + str(order['name']) + \
                                 '. Телефон: ' + str(order['number']) + \
                                 '. Услуга: ' + str(order['category']) + ' - ' + str(order['service']) + \
                                 '. Оплачена: ' + str(order['paid']) + \
                                 '. Время: ' + str(order['timestamp']).split('.')[0] + \
                                 '. Комментарий: ' + str(order['comment'])

    update.message.reply_text(user_data['order_to_send'],
                              reply_markup=ReplyKeyboardMarkup(single_order_keyboard, one_time_keyboard=True))
    return EDIT_ORDER


def add_comment(bot, update, user_data):
    update.message.reply_text(user_data['order_to_send'] + '. Введите комментарий к заказу',
                              reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
    return ADD_COMMENT


def add_comment_success(bot, update, user_data):
    order_table.update_one({'_id': user_data['order']['_id']}, {'$set': {'comment': update.message.text}})

    update.message.reply_text(' От: @' + str(user_data['order']['username']) +
                              '. Имя: ' + str(user_data['order']['name']) +
                              '. Телефон: ' + str(user_data['order']['number']) +
                              '. Услуга: ' + str(user_data['order']['category']) + ' - ' + str(user_data['order']['service']) +
                              '. Оплачена: ' + str(user_data['order']['paid']) +
                              '. Время: ' + str(user_data['order']['timestamp']).split('.')[0] +
                              '. Комментарий: ' + update.message.text +
                              '\nВаш комментарий добавлен',
                              reply_markup=ReplyKeyboardMarkup(single_order_keyboard, one_time_keyboard=True))
    return EDIT_ORDER


# need to use data from db, not from user_data
def change_status(bot, update, user_data):
    update.message.reply_text(user_data['order_to_send'] + '\nИзменить статус оплаты?',
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))
    return CHANGE_STATUS


# need normal back
def change_status_success(bot, update, user_data):
    order_table.update_one({'_id': user_data['order']['_id']}, {'$set': {'paid': 'Да'}})
    order = order_table.find_one({'_id': user_data['order']['_id']})

    update.message.reply_text(' От: @' + str(order['username']) +
                              '. Имя: ' + str(order['name']) +
                              '. Телефон: ' + str(order['number']) +
                              '. Услуга: ' + str(order['category']) + ' - ' + str(order['service']) +
                              '. Оплачена: ' + str(order['paid']) +
                              '. Время: ' + str(order['timestamp']).split('.')[0] +
                              '. Комментарий: ' + str(order['comment']) +
                              '\nCтатус изменён',
                              reply_markup=ReplyKeyboardMarkup(single_order_keyboard, one_time_keyboard=True))

    return EDIT_ORDER


def confirm_remove_order(bot, update, user_data):
    update.message.reply_text(user_data['order_to_send'] + '\nУдалить запись из списка?. '
                                                           'Вы не сможете её вернуть в будущем',
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))
    return CONFIRM_REMOVE


def remove_order_success(bot, update, user_data):
    # Need to correct back to the main state!
    order_table.delete_one({'_id': user_data['order']['_id']})
    update.message.reply_text(user_data['data_to_send'] + '\nЗапись успешно удалена',
                              reply_markup=ReplyKeyboardMarkup(user_data['keyboard'], one_time_keyboard=True))
    return CHOOSE_ORDER


admin_service_conv = ConversationHandler(
        entry_points=[RegexHandler('^Заказы$', orders_admin)],
        states={
            ORDERS_ADMIN: [RegexHandler('^Редакторовать$', choose_order_to_edit, pass_user_data=True),
                           RegexHandler('^Назад$', admin_home)],

            CHOOSE_ORDER: [RegexHandler('^Назад$', orders_admin),
                           MessageHandler(Filters.text, edit_order, pass_user_data=True)],

            EDIT_ORDER: [RegexHandler('^Добавить комментарий$', add_comment, pass_user_data=True),
                         RegexHandler('^Изменить статус оплаты$', change_status, pass_user_data=True),
                         RegexHandler('^Удалить$', confirm_remove_order, pass_user_data=True),
                         RegexHandler('^Назад$', choose_order_to_edit, pass_user_data=True)],

            ADD_COMMENT: [RegexHandler('^Назад$', edit_order),
                          MessageHandler(Filters.text, add_comment_success, pass_user_data=True)],

            CHANGE_STATUS: [RegexHandler('^Да$', change_status_success, pass_user_data=True),
                            RegexHandler('^Назад$', edit_order, pass_user_data=True)],

            CONFIRM_REMOVE: [RegexHandler('^Да$', remove_order_success, pass_user_data=True),
                             RegexHandler('^Назад$', edit_order, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
