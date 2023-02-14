
def load_questions(file_path):
    with open(file_path, 'r', encoding='koi8-r') as questions_file:
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
