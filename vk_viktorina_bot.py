import os
import random
import logging

import telegram
import vk_api as vk
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from error_processing import TelegramLogsHandler

logger = logging.getLogger(__name__)


def answer_message(event, vk_api, keyboard):

    session_id = event.user_id

    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard(),
    )


def main():
    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['CHAT_ID']

    bot = telegram.Bot(token=telegram_token)

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(TelegramLogsHandler(bot, chat_id))

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            answer_message(event, vk_api, keyboard)


if __name__ == "__main__":
    main()
