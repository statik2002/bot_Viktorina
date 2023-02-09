import logging
import os
import random

import telegram
from functools import partial
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from utils import load_questions

logger = logging.getLogger(__file__)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        #fr'Hi {user.mention_markdown_v2()}\!',
        'Здравствуйте',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def messages(
        update: Update,
        context: CallbackContext,
        questions) -> None:

    if update.message.text == 'Новый вопрос':
        question = questions[random.randrange(len(questions))]
        update.message.reply_text(question['question'])


def main() -> None:
    load_dotenv()
    telegram_token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']

    questions = load_questions('questions/1vs1200.txt')

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    bot = telegram.Bot(token=telegram_token)
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счёт']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=chat_id,
                     text="Привет я бот для викторин!",
                     reply_markup=reply_markup)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            partial(messages, questions=questions)
        )
    )

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
