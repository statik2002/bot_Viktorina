import logging
import os
import random
import re

import redis
import telegram
from functools import partial
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, \
    RegexHandler

from utils import load_questions

logger = logging.getLogger(__file__)

NEW_QUESTION, ANSWER, SURRENDER = range(3)

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

    if update.message.text == 'Новый вопрос':
        question = questions[random.randrange(len(questions))]
        redis_client.set(str(update.message.from_user.id), question['question'], 6000)
        redis_client.set(question['question'], question['answer'], 6000)
        update.message.reply_text(question['question'])
        return ANSWER
    else:
        return ANSWER


def handle_solution_attempt(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:
    user = update.message.from_user.id
    question = redis_client.get(str(update.message.from_user.id))
    answer = re.split(r'\.|\(', redis_client.get(question))

    if update.message.text == 'Сдаться':
        print(update.message.text)
        return SURRENDER
    if update.message.text.lower() != answer[0].lower():
        update.message.reply_text(f'Неправильно… Попробуешь ещё раз?', reply_markup=reply_markup)
        return ANSWER

    else:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»')
        return NEW_QUESTION


def handle_surrender(
        update: Update,
        context: CallbackContext,
        questions,
        redis_client) -> None:
    print('Все пропало')
    user = update.message.from_user.id
    question = redis_client.get(str(update.message.from_user.id))
    answer = re.split(r'\.|\(', redis_client.get(question))
    update.message.reply_text(f'Правильный ответ: {answer}', reply_markup=reply_markup)
    return NEW_QUESTION


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=telegram.ReplyKeyboardRemove())

    return ConversationHandler.END


def main() -> None:
    load_dotenv()
    telegram_token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)

    questions = load_questions('questions/1vs1200.txt')

    redis_client = redis.StrictRedis(
        host='localhost',
        port=6379,
        password='',
        charset="utf-8",
        decode_responses=True
    )

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NEW_QUESTION: [
                MessageHandler(Filters.text & ~Filters.command,
                               partial(handle_new_question_request, questions=questions, redis_client=redis_client),
                               )
            ],

            ANSWER: [
                MessageHandler(Filters.text & ~Filters.command,
                               partial(handle_solution_attempt, questions=questions, redis_client=redis_client),
                               )
            ],
            SURRENDER: [
                MessageHandler(Filters.text & ~Filters.command,
                               partial(handle_surrender, questions=questions, redis_client=redis_client),
                               )
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # dispatcher.add_handler(CommandHandler("start", start))
    # dispatcher.add_handler(CommandHandler("help", help_command))

    # dispatcher.add_handler(
    #    MessageHandler(
    #        Filters.text & ~Filters.command,
    #        partial(messages, questions=questions, redis_client=redis_client)
    #    )
    # )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
