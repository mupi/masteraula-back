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

def check_duplicates(json_questions, discipline):
    duplicates = []

    json_questions_stm = []

    for question in json_questions:
        statement = '{} {}'.format(' '.join(question['statement_p1']), ' '.join(question['statement_p2']))
        json_questions_stm.append((only_key_words(statement),
                                    question['id_enem'],
                                    statement))
    print('prepared all new questions')
    
    all_questions = []
    all_questions_dict = {}
    for question in Question.objects.filter(disciplines__name__in=[discipline]):
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
            scores.append([choices[1], all_questions_dict[choices[0]], question_stm[3], question_stm[2]])
        else:
            scores.append([-1, '', question_stm[3], question_stm[2]])

    scores.sort()
    
    for i, score in enumerate(scores):
        if score[0] < 0:
            print('\nQuestao {}'.format(i + 1))
            print('questao muito simples')
            print('questao comparada: {} {}'.format(score[3], score[2]))
            duplicates.append(score[3])
        elif score[0] >= 65:
            print('\nQuestao {}'.format(i + 1))
            print('score: {}'.format(score[0]))
            print('questao banco:{} {}'.format(score[1], Question.objects.get(id=score[1]).statement))
            print('questao comparada: {} {}'.format(score[3], score[2]))
            duplicates.append(score[3])

    return duplicates

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

        duplicates = check_duplicates(json_questions, DISCIPLINE)

        with open('duplicates.json', 'w') as f:
            f.write(json.dumps(duplicates))

        print('Ok')