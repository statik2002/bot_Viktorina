import logging
import os
import random
import re

import redis
import telegram
from functools import partial
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from error_processing import TelegramLogsHandler
from load_questions import load_questions
from questions import select_and_save_question, get_answer

logger = logging.getLogger(__file__)

NEW_QUESTION, ATTEMPT = range(2)

custom_keyboard = [['Новый вопрос', 'Сдаться'],
                   ['Мой счёт']]
reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user

    update.message.reply_text(
        # fr'Hi {user.mention_markdown_v2()}\!',
        'Привет! Это мега квиз!',
        reply_markup=reply_markup,
    )

    return NEW_QUESTION


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def handle_new_question_request(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:

    question = select_and_save_question(questions, redis_client, update.message.from_user.id)

    update.message.reply_text(question, reply_markup=reply_markup)

    return ATTEMPT


def handle_solution_attempt(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:
    user = update.message.from_user.id
    question = redis_client.get(str(update.message.from_user.id))

    if redis_client.get(question).lower().find(update.message.text.lower()) == -1:
        update.message.reply_text(f'Неправильно… Попробуешь ещё раз?', reply_markup=reply_markup)
        return ATTEMPT

    else:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»', reply_markup=reply_markup)
        return NEW_QUESTION


def handle_surrender(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:

    answer = get_answer(update, redis_client)
    update.message.reply_text(f'Правильный ответ: {answer}', reply_markup=reply_markup)

    question = select_and_save_question(questions, redis_client, update.message.from_user.id)
    update.message.reply_text(question)

    return ATTEMPT


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled quiz.", user.first_name)
    update.message.reply_text('Пока пока!',
                              reply_markup=telegram.ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(update, context):
    logger.error(msg='Ошибка при работе скрипта: ', exc_info=context.error)


def main() -> None:
    load_dotenv()
    telegram_token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']

    service_bot = telegram.Bot(token=telegram_token)
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(TelegramLogsHandler(service_bot, chat_id))

    questions = load_questions('questions/1vs1200.txt')

    redis_client = redis.StrictRedis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD'],
        charset="utf-8",
        decode_responses=True
    )

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    partial_new_question = partial(handle_new_question_request, questions=questions, redis_client=redis_client)
    partial_solution_attempt = partial(handle_solution_attempt, questions=questions, redis_client=redis_client)
    partial_surrender = partial(handle_surrender, questions=questions, redis_client=redis_client)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NEW_QUESTION: [
                MessageHandler(Filters.regex('^Новый вопрос$'), partial_new_question)
            ],

            ATTEMPT: [
                MessageHandler(Filters.regex('^Сдаться$'), partial_surrender),
                MessageHandler(Filters.text & ~Filters.command, partial_solution_attempt)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
