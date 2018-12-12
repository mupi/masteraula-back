from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline
# from masteraula.questions.search_indexes import QuestionIndex, TagIndex
import json
import os

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_questions')

    def handle(self, *args, **options):
        with open(options['json_questions']) as data_file:
            data = json.load(data_file)

            questions_ids = []
            questions_statements = {}

            for question_data in data:
                questions_ids.append(question_data['pk'])
                questions_statements[question_data['pk']] = question_data['fields']['statement']
            
            for question in Question.objects.filter(id__in=questions_ids):
                try:
                    print(question.id)
                    if question.statement != questions_statements[question.id]:
                        question.statement = questions_statements[question.id]
                        question.save()
                except Exception as e:
                    print(e)
