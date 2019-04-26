# -*- coding: utf-8 -*-
import logging
from telegram.ext import Updater, CommandHandler, RegexHandler
from config import conf

from modules.welcome import start, admin_home, about, contacts

from modules.user.call_me import call_me_conv
from modules.user.question import ask_conv
from modules.user.order import order_conv
from modules.user.user_home import user_home_conv

from modules.admin.answer import admin_answer_conv
from modules.admin.service import admin_service_conv

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
from threading import Thread
import os
import sys

def stop_and_restart():
    updater.stop()
    os.execl(sys.executable, sys.executable, *sys.argv)

def restart(bot, update):
    update.message.reply_text('Bot is restarting...')
    Thread(target=stop_and_restart).start()
"""


# TODO: 1) relationships in db and information about users
#       2) validate USER MESSAGE IN SEPARATE FUNCTION
#       3) notifications
#       4) admins chat_ids and admin decorators
#       5) run async decorators??
#       6) use of user_data.clear()
#       7) modules!
#       8) saving usernames in database, send notifications and so on, what if no username??
#       9) saving and clearing data between states
#       10) users ban list
#       11) change recall system


def errors(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)  # context.error or error


def main():
    updater = Updater(conf['BOT_TOKEN'])  # use_context=True ?
    dp = updater.dispatcher

    start_handler = CommandHandler('start', start)
    admin_handler = CommandHandler('admin', admin_home)  # Check that user admin()

    about_handler = CommandHandler('about', about)
    rex_about_handler = RegexHandler('^О компании$', about)
    contact_handler = CommandHandler('contact', contacts)
    rex_contact_handler = RegexHandler('^Контакты$', contacts)

    dp.add_handler(about_handler)
    dp.add_handler(rex_about_handler)
    dp.add_handler(contact_handler)
    dp.add_handler(rex_contact_handler)

    # USER
    dp.add_handler(start_handler)

    dp.add_handler(call_me_conv)
    dp.add_handler(ask_conv)
    dp.add_handler(order_conv)
    dp.add_handler(user_home_conv)

    # ADMIN
    dp.add_handler(admin_handler)

    dp.add_handler(admin_answer_conv)
    dp.add_handler(admin_service_conv)
    #

    dp.add_error_handler(errors)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
