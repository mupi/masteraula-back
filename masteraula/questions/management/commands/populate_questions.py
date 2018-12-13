from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline
# from masteraula.questions.search_indexes import QuestionIndex, TagIndex
import json
import os

class Command(BaseCommand):
    help = 'populate data from json-questions directory'

    def add_arguments(self, parser):
        parser.add_argument('file_name', nargs='+')

    def handle(self, *args, **options):
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
                        if Question.objects.filter(statement = question_data["question_statement"]).count() > 0:
                            print ("Questao " + str(counter) + " Ja existe")
                            continue
                    except:
                        pass

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

                    discipline = question_data["discipline"]
                    try:
                        discipline = Discipline.objects.get(name=discipline)
                    except Discipline.DoesNotExist:
                        raise CommandError('Disciplina "%s" nao existe' % discipline)
                    
                    teaching_level = question_data["education_level"]
                    try:
                        teaching_level = TeachingLevel.objects.get(name=teaching_level)
                    except TeachingLevel.DoesNotExist:
                        raise CommandError('Disciplina "%s" nao existe' % teaching_level)

                    # question = Question.objects.create(question_statement=question_data["statement"],
                    #                                     level=question_data["level"],
                    #                                     resolution=question_data["resolution"],
                    #                                     year=question_data["year"],
                    #                                     source=question_data["source"],
                    #                                     education_level=question_data["education_level"],
                    #                                     author_id=1)

                    resolution = question_data["resolution"] if "resolution" in question_data else ''

                    question = Question.objects.create(statement=question_data["question_statement"],
                                                        resolution=resolution,
                                                        year=question_data["year"],
                                                        source=question_data["source"],
                                                        author_id=1)

                    if "answers" in question_data and len(question_data["answers"]) > 0:
                        for answer_data in question_data["answers"]:
                            answer = Alternative.objects.create(text=answer_data["answer_text"],
                                                                is_correct=answer_data["is_correct"],
                                                                question_id=question.id)

                    # for subject_id in question_data["subjects"]:
                    #     subject = Subject.objects.get(pk=subject_id)
                    #     question.subjects.add(subject)
                    question.disciplines.add(discipline)
                    question.teaching_levels.add(teaching_level)

                    for tag in question_data["tags"]:
                        if len(tag) < 100:
                            question.tags.add(tag)
                            question.save()

                    print ("Questao " + str(counter) + " Salva")

            # if len(erradas) > 0:
            #     with open('json-questions/errors/' + filename, 'w+') as outfile:
            #         json.dump(erradas, outfile)
            # if len(certas) > 0:
            #     with open('json-questions/corrects/' + filename, 'w+') as outfile:
            #         json.dump(certas, outfile)
            print('Questoes salvas do arquivo ' + filename)
        print('Feito')