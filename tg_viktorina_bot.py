import argparse
import logging
import os
import random

import redis
import telegram
from functools import partial
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters,
                          CallbackContext, ConversationHandler)

from error_processing import TelegramLogsHandler
from questions import load_questions

logger = logging.getLogger(__file__)

NEW_QUESTION, ATTEMPT = range(2)

custom_keyboard = [['Новый вопрос', 'Сдаться'],
                   ['Мой счёт']]
reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)


def start(update: Update, context: CallbackContext) -> None:

    update.message.reply_text(
        'Привет! Это мега квиз!',
        reply_markup=reply_markup,
    )

    return NEW_QUESTION


def handle_new_question_request(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:

    question = questions[random.randrange(len(questions))]
    redis_client.set(
        str(update.message.from_user.id),
        question['question'],
        6000
    )
    redis_client.set(question['question'], question['answer'], 6000)

    update.message.reply_text(question['question'], reply_markup=reply_markup)

    return ATTEMPT


def handle_solution_attempt(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:

    question = redis_client.get(str(update.message.from_user.id))

    saved_answer = redis_client.get(question)
    user_answer = update.message.text

    if saved_answer.lower().find(user_answer.lower()) == -1:
        update.message.reply_text(
            'Неправильно… Попробуешь ещё раз?',
            reply_markup=reply_markup
        )
        return ATTEMPT

    else:
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего '
            'вопроса нажми «Новый вопрос»',
            reply_markup=reply_markup
        )
        return NEW_QUESTION


def handle_surrender(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:

    question = redis_client.get(str(update.message.from_user.id))
    answer = ''.join(redis_client.get(question))
    update.message.reply_text(
        f'Правильный ответ: {answer}',
        reply_markup=reply_markup
    )

    new_question = questions[random.randrange(len(questions))]
    redis_client.set(
        str(update.message.from_user.id),
        new_question['question'],
        6000
    )
    redis_client.set(new_question['question'], new_question['answer'], 6000)
    update.message.reply_text(new_question['question'])

    return ATTEMPT


def cancel(bot, update):
    user = update.message.from_user
    logger.info("Пользователь %s завершил викторину.", user.first_name)
    update.message.reply_text('Пока пока!',
                              reply_markup=telegram.ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(update, context):
    logger.error(msg='Ошибка при работе скрипта: ', exc_info=context.error)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Telegram бот викторины',
    )
    parser.add_argument(
        '--path',
        help='путь к файлу с вопросами и ответами',
        default='questions/1vs1200.txt'
    )
    args = parser.parse_args()

    load_dotenv()
    telegram_token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']

    service_bot = telegram.Bot(token=telegram_token)
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(TelegramLogsHandler(service_bot, chat_id))

    questions = load_questions(args.path)

    redis_client = redis.StrictRedis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD'],
        charset="utf-8",
        decode_responses=True
    )

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    partial_new_question = partial(
        handle_new_question_request,
        questions=questions,
        redis_client=redis_client
    )
    partial_solution_attempt = partial(
        handle_solution_attempt,
        questions=questions,
        redis_client=redis_client
    )
    partial_surrender = partial(
        handle_surrender,
        questions=questions,
        redis_client=redis_client
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NEW_QUESTION: [
                MessageHandler(
                    Filters.regex('^Новый вопрос$'),
                    partial_new_question
                )
            ],

            ATTEMPT: [
                MessageHandler(
                    Filters.regex('^Сдаться$'),
                    partial_surrender
                ),
                MessageHandler(
                    Filters.text & ~Filters.command,
                    partial_solution_attempt
                )
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
