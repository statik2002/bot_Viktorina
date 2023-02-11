import random


def select_and_save_question(questions, redis_client, user_id):
    question = questions[random.randrange(len(questions))]
    redis_client.set(str(user_id), question['question'], 6000)
    redis_client.set(question['question'], question['answer'], 6000)

    return question['question']


def get_answer(update, redis_client):
    question = redis_client.get(str(update.message.from_user.id))

    return ''.join(redis_client.get(question))
