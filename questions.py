import random


def load_questions(file_path):
    with open('questions/1vs1200.txt', 'r', encoding='koi8-r') as questions_file:
        raw = questions_file.read().split('\n\n\n')

    questions = []

    for line in raw[1:10]:
        divided_block = line.split('\n\n')
        question = {}
        for block_line in divided_block:
            element = block_line.split('\n')
            if element[0] == 'Ответ:':
                question['answer'] = ' '.join(element[1:])
            if element[0] == 'Источник:':
                question['source'] = element[1]
            if element[0] == 'Автор:':
                question['author'] = element[1]
            if 'Вопрос' in element[0]:
                question['question'] = ' '.join(element[1:])
            if element[0] == 'Комментарий:':
                question['comment'] = ' '.join(element[1:])
            if element[0] == 'Зачет:':
                question['answer2'] = element[1]

        questions.append(question)

    return questions


def select_and_save_question(questions, redis_client, user_id):
    question = questions[random.randrange(len(questions))]
    redis_client.set(str(user_id), question['question'], 6000)
    redis_client.set(question['question'], question['answer'], 6000)

    return question['question']


def get_answer(user_id, redis_client):
    question = redis_client.get(str(user_id))

    return ''.join(redis_client.get(question))
