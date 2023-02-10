# Скрипты ботов викторины для Telegram и VK

## Общее описание
Данные скрипты реализуют викторину. Вопросы загружаются из указанного файла. В процессе викторины бот выбирает
случайный вопрос и задает пользователю. Пользователь пытается ответить на вопрос. Пользователь может нажать 
на кнопку 'Сдаться', тогда бот выводит правильный ответ и задает новый вопрос.

# Установка
Скачать скрипты и вопросы.

Установить виртуальное окружение командой:
```commandline
python3 -m venv env
```

Запускаем виртуальное окружение командой:

Linux, MacOS
```commandline
source env/bin/activate
```

Windows
```commandline
env\Scripts\activate.bat
```

Устанавливаем зависимости командой:
```commandline
pip install -r requirements.txt
```

# Подготовка к запуску
Создайте файл в каталоге со скриптами файл `.env` и впишите туда следующие переменные:

`TELEGRAM_TOKEN=Ваш Telegram токен`

`REDIS_HOST=Хост от Redis` - В случае локального сервера Redis - `localhost`

`REDIS_PORT=Порт в Redis`

`REDIS_PASSWORD=Пароль в Redis`


# Запуск

Для запуска Telegram бота выполните:
```commandline
python tg_viktorina_bot.py
```

Для запуска VK бота выполните:
```commandline
python vk_viktorina_bot.py
```