# -*- coding: utf-8 -*-
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from .keyboards import main_keyboard, admin_home_keyboard
from db import users_table

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHOOSING = 0


"""
class WelcomeBot(object):
    @staticmethod
    def start(bot, update):
        update.message.reply_text(
            'Sweet Jumble первое и самое крупное агентство персональных стилистов-шопперов в Украине',
            reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
        return CHOOSING

    @staticmethod
    def contacts(bot, update):
        update.message.reply_text('instagram https://www.instagram.com/rostdikoy/ '
                                  'twitter https://twitter.com/Sweet_Jumble '
                                  'facebook https://www.facebook.com/SweetJumble.ua '
                                  'pinterest https://www.pinterest.com/sjumble/ '
                                  'youtube   https://www.youtube.com/user/sweetjumble '
                                  'школа шоппера facebook https://www.facebook.com/shoppers.school/ '
                                  'звоните: '
                                  '+38 063 038 30 00 '
                                  '+38 096 38 00 300 '
                                  '+38 044 22 777 88 '
                                  'пишите: '
                                  'УСЛУГИ СТИЛИСТОВ '
                                  'shopper@sweetjumble.ua '
                                  'ШКОЛА ШОППЕРА '
                                  'school@sweetjumble.ua',
                                  reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
        return CHOOSING

    @staticmethod
    def about(bot, update):
        update.message.reply_text('Sweet Jumble (англ. любимый беспорядок) — это агентство профессиональных шопперов. '
                                  'Мы помогаем решать проблемы с гардеробом, умеем быстро и экономно выбирать покупки '
                                  'во время шоппинга. «Порядок рождается из беспорядка!» — '
                                  'так звучит философия нашего агентства.'
                                  'Об основателе РОСТ DИКОЙ Рост Дикой входит в тройку топ-стилистов Украины. VIP-шоппер. '
                                  'Владелец крупнейшего в Украине агентства шопперов Sweet Jumble '
                                  '(более 120 стилистов-шопперов). Основатель «Школы шоппера» (обучение профессиональному '
                                  'шоппингу и личному стилю) в 12 городах Украины, более 2000 учеников. Член жюри и '
                                  'ведущий международных конкурсов молодых дизайнеров. Амбассадор профессии «шоппер» и '
                                  'основатель тренда «Шоппинг со стилистом». Автор курсов и тренингов по стилю и шоппингу. '
                                  'Стилист на 5 телеканалах.',
                                  reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
        return CHOOSING
"""


def start(bot, update):
    if not users_table.find_one({'id': update.effective_user.id}):
        users_table.insert_one({'id': update.effective_user.id,
                                'chat_id': update.message.chat.id,
                                'username': update.effective_user.username,
                                'full_name': update.effective_user.full_name,
                                'name': update.effective_user.name
                                })
    else:
        users_table.update_one({'id': update.effective_user.id},
                               {
                                   '$set':
                                       {'id': update.effective_user.id,
                                        'chat_id': update.message.chat.id,
                                        'username': update.effective_user.username,
                                        'full_name': update.effective_user.full_name,
                                        'name': update.effective_user.name
                                        }
                               })
    update.message.reply_text('Sweet Jumble первое и самое крупное агентство персональных стилистов-шопперов в Украине',
                              reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))

    return ConversationHandler.END


def admin_home(bot, update):
    update.message.reply_text('Привет, {}. Добро пожаловать в админку'.format(update.effective_user.full_name),
                              reply_markup=ReplyKeyboardMarkup(admin_home_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


def contacts(bot, update):
    update.message.reply_text('instagram https://www.instagram.com/rostdikoy/'
                              '\ntwitter https://twitter.com/Sweet_Jumble'
                              '\nfacebook https://www.facebook.com/SweetJumble.ua'
                              '\npinterest https://www.pinterest.com/sjumble/ '
                              '\nyoutube https://www.youtube.com/user/sweetjumble '
                              '\nшкола шоппера facebook https://www.facebook.com/shoppers.school/ '
                              '\nзвоните: '
                              '\n+38 063 038 30 00 '
                              '\n+38 096 38 00 300 '
                              '\n+38 044 22 777 88 '
                              '\nпишите: '
                              '\nУСЛУГИ СТИЛИСТОВ '
                              '\nshopper@sweetjumble.ua '
                              '\nШКОЛА ШОППЕРА '
                              '\nschool@sweetjumble.ua',
                              reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


def about(bot, update):
    update.message.reply_text('Sweet Jumble (англ. любимый беспорядок) — это агентство профессиональных шопперов. '
                              'Мы помогаем решать проблемы с гардеробом, умеем быстро и экономно выбирать покупки '
                              'во время шоппинга. «Порядок рождается из беспорядка!» — '
                              'так звучит философия нашего агентства.'
                              'Об основателе РОСТ DИКОЙ Рост Дикой входит в тройку топ-стилистов Украины. VIP-шоппер. '
                              'Владелец крупнейшего в Украине агентства шопперов Sweet Jumble '
                              '(более 120 стилистов-шопперов). Основатель «Школы шоппера» (обучение профессиональному '
                              'шоппингу и личному стилю) в 12 городах Украины, более 2000 учеников. Член жюри и '
                              'ведущий международных конкурсов молодых дизайнеров. Амбассадор профессии «шоппер» и '
                              'основатель тренда «Шоппинг со стилистом». Автор курсов и тренингов по стилю и шоппингу. '
                              'Стилист на 5 телеканалах.',
                              reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


def cancel(bot, update):
    update.message.reply_text('cancel conversation',
                              reply_markup=ReplyKeyboardRemove()  # main_keyboard
                              )
    return ConversationHandler.END

