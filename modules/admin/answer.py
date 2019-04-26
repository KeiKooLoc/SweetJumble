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

QUESTIONS_ADMIN, CHOOSE_QUESTION, GIVE_ANSWER, CONFIRM_ANSWER = range(4)


# QUESTIONS HANDLERS
question_keyboard = [['Ответить'], ['Показать все'], ['Показать без ответа'], ['Назад']]


def questions_admin(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    if update.message.text == 'Показать без ответа':
        questions_data = question_table.find({'answer': 0}).sort([['_id', 1]])
        keyboard = [['Ответить'], ['Показать все'], ['Назад']]
    else:
        questions_data = question_table.find().sort([['_id', 1]])
        keyboard = [['Ответить'], ['Показать без ответа'], ['Назад']]

    if questions_data.count() == 0:
        update.message.reply_text('Нет вопросов',
                                  reply_markup=ReplyKeyboardMarkup(admin_home_keyboard, one_time_keyboard=True))
        return ConversationHandler.END

    data_to_send = '\n'.join([' От: @' + str(i['username']) +
                              '. Время: ' + str(i['timestamp']).split('.')[0] +
                              '. Вопрос: ' + i['question'] +
                              '. Ответ: ' + str(i['answer']) for i in questions_data])
    update.message.reply_text(data_to_send, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return QUESTIONS_ADMIN


def choose_question(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    keyboard = [[], ['Назад']]
    questions_data = question_table.find({'answer': 0}).sort([['_id', 1]])

    # if no question without answer = return back
    if questions_data.count() == 0:
        update.message.reply_text('Вы уже дали ответы на все вопросы',
                                  reply_markup=ReplyKeyboardMarkup(question_keyboard, one_time_keyboard=True))
        return QUESTIONS_ADMIN

    # set button to each question without answer
    for num, i in enumerate(questions_data):
        question_table.update({'_id': i['_id']}, {'$set': {'button': num + 1}})  # update_one({})
        if len(keyboard[-2]) == 5:
            keyboard.insert(len(keyboard) - 1, [])
        keyboard[-2].append(str(num + 1))

    enum_questions = question_table.find({'answer': 0}).sort([['button', 1]])
    data_to_send = '\n'.join([str(i['button']) +
                              '. Вопрос: ' + i['question'] for i in enum_questions])
    user_data['data_to_send'] = data_to_send
    user_data['keyboard'] = keyboard
    update.message.reply_text(data_to_send + '. Выберете номер вопроса на который хотите дать ответ',
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CHOOSE_QUESTION


def give_answer(bot, update, user_data):
    try:
        int(update.message.text)
    except (ValueError, TypeError):
        update.message.reply_text(user_data['data_to_send'] + '. Выберете номер вопроса на который хотите дать ответ',
                                  reply_markup=ReplyKeyboardMarkup(user_data['keyboard'], one_time_keyboard=True))
        return CHOOSE_QUESTION
    q = question_table.find_one({'answer': 0, 'button': int(update.message.text)})
    if q:
        update.message.reply_text(' От: @' + str(q['username']) +
                                  '. Время: ' + str(q['timestamp']).split('.')[0] +
                                  '. Вопрос: ' + str(q['question']) +
                                  '. Ответ: ' + str(q['answer']) + '. Введите ваш ответ',
                                  reply_markup=ReplyKeyboardMarkup([['Назад']], one_time_keyboard=True))
        user_data['q'] = q
        return GIVE_ANSWER
    else:
        update.message.reply_text(user_data['data_to_send'] + '. Выберете номер вопроса на который хотите дать ответ',
                                  reply_markup=ReplyKeyboardMarkup(user_data['keyboard'], one_time_keyboard=True))
        return CHOOSE_QUESTION


def confirm_answer(bot, update, user_data):
    msg = update.message.text
    if msg != 'Назад':
        user_data['answer'] = msg
    update.message.reply_text(' От: @' + str(user_data['q']['username']) +
                              '. Время: ' + str(user_data['q']['timestamp']).split('.')[0] +
                              '. Вопрос: ' + user_data['q']['question'] +
                              '. Ответ: ' + str(msg) + '. Подтвердить отправку ответа?',
                              reply_markup=ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True))
    return CONFIRM_ANSWER


def confirm_answer_true(bot, update, user_data):
    question_table.update_one({'_id': user_data['q']['_id']}, {'$set': {'answer': user_data['answer']}})
    update.message.reply_text('Ваш ответ отправлен и появится в кабинете у юзера и админа. '
                              'Юзеру прийдёт уведомление',
                              reply_markup=ReplyKeyboardMarkup([['Ответить'], ['Показать все'], ['Показать без ответа'],
                                                                ['Назад']], one_time_keyboard=True))
    return QUESTIONS_ADMIN


admin_answer_conv = ConversationHandler(
        entry_points=[RegexHandler('^Вопросы$', questions_admin, pass_user_data=True)],
        states={
            QUESTIONS_ADMIN: [RegexHandler('^Ответить$', choose_question, pass_user_data=True),
                              RegexHandler('^Показать все$', questions_admin, pass_user_data=True),
                              RegexHandler('^Показать без ответа$', questions_admin, pass_user_data=True),
                              RegexHandler('^Назад$', admin_home)],

            CHOOSE_QUESTION: [RegexHandler('^Назад$', questions_admin, pass_user_data=True),
                              MessageHandler(Filters.text, give_answer, pass_user_data=True)],

            GIVE_ANSWER: [RegexHandler('^Назад$', choose_question, pass_user_data=True),
                          MessageHandler(Filters.text, confirm_answer, pass_user_data=True)],

            CONFIRM_ANSWER: [RegexHandler('^Да$', confirm_answer_true, pass_user_data=True),
                             RegexHandler('^Назад$', give_answer, pass_user_data=True)],

        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
