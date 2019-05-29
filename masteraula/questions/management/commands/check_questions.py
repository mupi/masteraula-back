from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Discipline

from masteraula.questions.templatetags.search_helpers import only_key_words
from fuzzywuzzy import fuzz, process

import re
import requests
import json

from threading import Thread

import csv
import os

def check_alternatives(json_questions):
    no_alternatives = []
    two_alternatives = []
    more_alternatives = []
    
    for question_data in json_questions:
        id_enem = question_data['id_enem']

        if "alternatives" in question_data:
            alternatives = question_data["alternatives"]
            if len(alternatives)  == 0:
                no_alternatives.append(id_enem)
                continue
            elif len(alternatives)  == 2:
                two_alternatives.append(id_enem)
                continue
            elif len(alternatives) > 5:
                more_alternatives.append(id_enem)
                continue
        else:
            no_alternatives.append(id_enem)

    return no_alternatives, two_alternatives, more_alternatives

def has_learning_objects(json_questions):
    question_with_objects = []

    for question_data in json_questions:
        if  len(question_data["object_text"]) > 0 or len(question_data["object_image"]) > 0:
            question_with_objects.append(question_data['id_enem'])

    return question_with_objects

def has_years(json_questions):
    questions_without_year = []

    for question_data in json_questions:
        if 'year' not in question_data:
            questions_without_year.append(question_data['id_enem'])

    return questions_without_year

def check_duplicates(json_questions, discipline):

    class KeywordQuestionStatement():
        def __init__(self, question_id, statement):
            self.statement = statement
            self.question_id = question_id
            self.keywords = only_key_words(statement)

        def __lt__(self, other):
            return len(self.keywords) < len(other.keywords)

    class Score():
        def __init__(self, id_enem, statement, question_id=None, score = -1):
            self.question_id = question_id
            self.id_enem = id_enem
            self.statement = statement
            self.score = score

        def __lt__(self, other):
            return self.score < other.score

    duplicates = []
    too_simple_questions = []

    new_questions = []
    for question_data in json_questions:
        statement = '{} {}'.format(' '.join(question_data['statement_p1']), ' '.join(question_data['statement_p2']))
        new_question = KeywordQuestionStatement(
            question_id = question_data['id_enem'],
            statement = statement
        )
        new_questions.append(new_question)
    print('prepared all new questions')
    
    db_questions = []
    for question in Question.objects.filter(disciplines__in=[discipline]):
        db_question = KeywordQuestionStatement(
            question_id = question.pk,
            statement = question.statement
        )
        db_questions.append(db_question)
    print('prepared all questions')

    db_questions.sort()
    new_questions.sort()

    all_questions_keywords = [q.keywords for q in db_questions]
    scores = []

    for i, new_question in enumerate(new_questions):
        print('Questao {}'.format(i + 1))
        if new_question.keywords:
            choices = process.extractOne(new_question.keywords, all_questions_keywords, scorer=fuzz.token_sort_ratio)
            for db_question in db_questions:
                if db_question.keywords == choices[0]:
                    break

            score = Score(new_question.question_id, new_question.statement, db_question.question_id, choices[1])
        else:
            score = Score(new_question.question_id, new_question.statement)
        scores.append(score)

    scores.sort()
    
    for i, score in enumerate(scores):
        if score.score < 0:
            print('\nQuestao {}'.format(i + 1))
            print('questao muito simples')
            print('questao comparada: {} {}'.format(score.id_enem, score.statement))
            too_simple_questions.append(score.id_enem)
        elif score.score >= 65:
            print('\nQuestao {}'.format(i + 1))
            print('score: {}'.format(score.score))
            print('questao banco:{} {}'.format(score.question_id, Question.objects.get(id=score.question_id).statement))
            print('questao comparada: {} {}'.format(score.id_enem, score.statement))
            duplicates.append(score.id_enem)

    return too_simple_questions, duplicates

def check_valid_questions(json_questions, discipline=None, output=False):
    
    print('Total questions {}'.format(len(json_questions)))

    no_years = has_years(json_questions)
    print('Questions without year: {}'.format(len(no_years)))

    no_alternatives, two_alternatives, more_alternatives = check_alternatives(json_questions)
    print('Questions without alternatives: {}'.format(len(no_alternatives)))
    print('Questions with 2  alternatives: {}'.format(len(two_alternatives)))
    print('Questions with more than 5 alternatives: {}'.format(len(more_alternatives)))

    question_with_objects = has_learning_objects(json_questions)
    print('Questions with objects : {}'.format(len(question_with_objects)))

    invalid_questions = list(set(no_years + no_alternatives + two_alternatives + more_alternatives + question_with_objects))

    too_simple_questions, duplicates = [], []
    if discipline:
        valid_json_questions = [json_question for json_question in json_questions if json_question['id_enem'] not in invalid_questions]
        too_simple_questions, duplicates = check_duplicates(valid_json_questions, discipline)
        print('Very simple questions: {}'.format(len(too_simple_questions)))
        print('Possible duplicate quetions: {}'.format(len(duplicates)))

    invalid_questions = list(set(invalid_questions + too_simple_questions + duplicates))
    print('Total invalid: {}'.format(len(invalid_questions)))
    print('Total valid : {}'.format(len(json_questions) - len(invalid_questions)))


    if output:
        with open('json-questions/reports/no_years.json', 'w') as f:
            json.dump(no_years, f, indent = 2)

        with open('json-questions/reports/no_alternatives.json', 'w') as f:
            json.dump(no_alternatives, f, indent = 2)
        with open('json-questions/reports/two_alternatives.json', 'w') as f:
            json.dump(two_alternatives, f, indent = 2)
        with open('json-questions/reports/more_alternatives.json', 'w') as f:
            json.dump(more_alternatives, f, indent = 2)

        with open('json-questions/reports/question_with_objects.json', 'w') as f:
            json.dump(question_with_objects, f, indent = 2)

        with open('json-questions/reports/duplicates.json', 'w') as f:
            json.dump(duplicates, f, indent = 2)
        with open('json-questions/reports/too_simple_questions.json', 'w') as f:
            json.dump(too_simple_questions, f, indent = 2)

    return [json_question for json_question in json_questions if json_question['id_enem'] not in invalid_questions]


class Command(BaseCommand):
    help = 'Check if there is a duplicate question from the file'

    def add_arguments(self, parser):
        parser.add_argument('folder')
        parser.add_argument('--export', action='store_true',)
        parser.add_argument('--duplicates', action='append', type=str)

    def handle(self, *args, **kwargs):
        folder = kwargs['folder']
        discipline = kwargs['duplicates']
        export = kwargs['export']

        if discipline:
            discipline = Discipline.objects.get(name__in=discipline)

        json_questions = []
        for filename in os.listdir(folder):
            if not filename.endswith('.json'):
                continue
            with open('{}/{}'.format(folder, filename), 'r') as f:
                json_questions += json.loads(f.read().replace(' ', ''))

        check_valid_questions(json_questions, discipline, export)