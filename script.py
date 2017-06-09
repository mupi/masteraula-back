from mupi_question_database.questions.models import Question, Answer, Subject
from mupi_question_database.questions.search_indexes import QuestionIndex, TagIndex
import json
import os

for filename in os.listdir('json-questions/'):
    if not filename.endswith('.json'):
        continue

    print ('Salvando questoes do arquivo ' + filename)

    with open('json-questions/' + filename) as data_file:
        data = json.load(data_file)

        erradas = []
        certas = []
        counter = 0
        # for question_data in data["questions"]:
        for question_data in data:
            counter = counter + 1
            try:
                # verify if the question has one and just one right answer
                right_answer = False
                message = ''
                if "answers" in question_data and len(question_data["answers"]) > 0:
                    for answer_data in question_data["answers"]:
                        if answer_data['is_correct'] and not right_answer:
                            right_answer = True
                        elif answer_data['is_correct'] and right_answer:
                            message = ('Question ' + str(counter) + ' has two right answer')
                    if not right_answer:
                        print('Question ' + str(counter) + ' dont have right answer')
                        continue
                    if message != '':
                        print(message)
                        continue

                subject_id = question_data["discipline"]
                subject = Subject.objects.get(subject_name=subject_id)

                # question = Question.objects.create(question_statement=question_data["statement"],
                #                                     level=question_data["level"],
                #                                     resolution=question_data["resolution"],
                #                                     year=question_data["year"],
                #                                     source=question_data["source"],
                #                                     education_level=question_data["education_level"],
                #                                     author_id=1)

                resolution = question_data["resolution"] if "resolution" in question_data else ''

                question = Question.objects.create(question_statement=question_data["question_statement"],
                                                    level='',
                                                    resolution=resolution,
                                                    year=question_data["year"],
                                                    source=question_data["source"],
                                                    education_level=question_data["education_level"],
                                                    author_id=1)

                if "answers" in question_data and len(question_data["answers"]) > 0:
                    for answer_data in question_data["answers"]:
                        answer = Answer.objects.create(answer_text=answer_data["answer_text"],
                                                            is_correct=answer_data["is_correct"],
                                                            question_id=question.id)

                # for subject_id in question_data["subjects"]:
                #     subject = Subject.objects.get(pk=subject_id)
                #     question.subjects.add(subject)
                question.subjects.add(subject)

                for tag in question_data["tags"]:
                    if len(tag) < 100:
                        question.tags.add(tag)
                        question.save()
                for tag in question.tags.all():
                    TagIndex().update_object(tag)

                QuestionIndex().update_object(question)
                certas.append(question_data)
                print ("Questao " + str(counter) + " Salva")
            except:
                print ("Erro na questao " + str(counter))
                erradas.append(question_data)
    # if len(erradas) > 0:
    #     with open('json-questions/errors/' + filename, 'w+') as outfile:
    #         json.dump(erradas, outfile)
    # if len(certas) > 0:
    #     with open('json-questions/corrects/' + filename, 'w+') as outfile:
    #         json.dump(certas, outfile)

    print('Questoes salvas do arquivo ' + filename)
print('Feito')
