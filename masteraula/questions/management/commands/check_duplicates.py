from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question

from masteraula.questions.templatetags.search_helpers import only_key_words
from fuzzywuzzy import fuzz, process

import re
import requests
import json

from threading import Thread

import csv
import os

class Command(BaseCommand):
    help = 'Check if there is a duplicate question from the file'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        filename = options['filename']
        DISCIPLINE = 'História'

        json_questions = None
        with open(filename, 'r') as f:
            json_questions = json.loads(f.read().replace(' ', ''))

        json_questions_stm = []
        for question in json_questions:
            statement = '{} {}'.format(question['statement_p1'], question['statement_p2'])
            json_questions_stm.append((only_key_words(statement),
                                     question['id_enem'],
                                     statement))
        print('prepared all new questions')
        
        all_questions = []
        all_questions_dict = {}
        for question in Question.objects.filter(disciplines__name__in=[DISCIPLINE]):
            all_questions.append(only_key_words(question.statement))
            all_questions_dict[all_questions[-1]] = question.pk
        print('prepared all questions')

        res = []
        for question_stm in json_questions_stm:
            res.append((len(question_stm[0]), question_stm[0], question_stm[1], question_stm[2]))

        res.sort()
        scores = []
        for i, question_stm in enumerate(res):
            print('Questao {}'.format(i + 1))
            if question_stm[0]:
                choices = process.extractOne(question_stm[1], all_questions, scorer=fuzz.token_sort_ratio)
                choosen = all_questions_dict[choices[0]], choices[1]
                scores.append([i, choosen, question_stm[3]])
            else:
                scores.append([i, '', question_stm[3]])

        
        print(scores)