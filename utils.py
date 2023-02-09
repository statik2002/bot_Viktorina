from pprint import pprint


def load_questions(file_path):
    with open('questions/1vs1200.txt', 'r', encoding='koi8-r') as quesion_file:
        raw = quesion_file.read().split('\n\n\n')

    questions = []

    for line in raw[1:10]:

        splited_line = line.split('\n\n')
        question = {}
        for lll in splited_line:
            element = lll.split('\n')
            if element[0] == 'Ответ:':
                question['answer'] = element[1]
            if element[0] == 'Источник:':
                question['source'] = element[1]
            if element[0] == 'Автор:':
                question['author'] = element[1]
            if 'Вопрос' in element[0]:
                question['question'] = ''.join(element[1:])

        questions.append(question)

    return questions
    # pprint(questions[0]['question'])


