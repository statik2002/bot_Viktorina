import argparse
import os
import random
import logging
from textwrap import dedent

import redis
import telegram
import vk_api as vk
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from error_processing import TelegramLogsHandler
from questions import load_questions

logger = logging.getLogger(__name__)


def answer_message(event, vk_api, keyboard, questions, redis_client, user_id):

    question = redis_client.get(str(user_id))
    answer = ''.join(redis_client.get(question))

    if event.text == 'Сдаться':
        new_question = questions[random.randrange(len(questions))]
        redis_client.set(str(user_id), new_question['question'], 6000)
        redis_client.set(
            new_question['question'],
            new_question['answer'],
            6000
        )
        message = dedent(f"""\
                    Правильный ответ: {answer}
                    Следующий вопрос: {new_question['question']}""")

    elif event.text == 'Новый вопрос':
        new_question = questions[random.randrange(len(questions))]
        redis_client.set(str(user_id), new_question['question'], 6000)
        redis_client.set(
            new_question['question'],
            new_question['answer'],
            6000
        )
        message = new_question['question']

    else:
        saved_answer = redis_client.get(str(question))
        if not saved_answer:
            return
        user_answer = event.text
        if saved_answer.lower().find(user_answer.lower()) == -1:
            message = 'Неправильно… Попробуешь ещё раз?',

        else:
            message = dedent("""\
                        Правильно! Поздравляю!
                        Для следующего вопроса нажми «Новый вопрос»""")

    vk_api.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard(),
    )


def main():
    parser = argparse.ArgumentParser(
        description='VK бот викторины',
    )
    parser.add_argument(
        '--path',
        help='путь к файлу с вопросами и ответами',
        default='questions/1vs1200.txt'
    )
    args = parser.parse_args()

    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']

    bot = telegram.Bot(token=telegram_token)

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(TelegramLogsHandler(bot, chat_id))

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    questions = load_questions(args.path)
    redis_client = redis.StrictRedis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD'],
        charset="utf-8",
        decode_responses=True
    )

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            answer_message(
                event,
                vk_api,
                keyboard,
                questions,
                redis_client,
                event.user_id
            )


if __name__ == "__main__":
    main()
