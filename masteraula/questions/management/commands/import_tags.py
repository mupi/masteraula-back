# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question

import csv
import os

class Command(BaseCommand):
    help = 'Import question tags from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+')

    def handle(self, *args, **options):
        for filename in options['filename']:

            questions = []
            with open(filename, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                # adding only the essential
                for row in reader:
                    if row[1].strip() != '':
                        r = []
                        r.append(row[0])
                        r.append(row[1])
                        questions.append(r)
                
                # separate the tags
                for question in questions:
                    tags = question[1].split(',')
                    tags = [t.strip() for t in tags]
                    question[1] = tags

                # check if the question has tags already and update
                updated = []
                not_updated = []
                question_ids = [ q[0] for q in questions ]
                
                for question in questions:
                    q = Question.objects.get(id=question[0])
                    if q.tags.count() > 0:
                        not_updated.append(q.id)
                    else:
                        for t in question[1]:
                            q.tags.add(t)
                            updated.append(q.id)
                        q.save()
                print("Atualizadas ")
                print(updated)
                print("Não atualizadas ")
                print(not_updated)
