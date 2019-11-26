# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Topic, Synonym, Discipline
from django.core.files import File
from django.shortcuts import get_object_or_404

import csv
import os

class Command(BaseCommand):
    help = 'Import synonyms from cvs. Command ./manage.py insert_synonyms file.csv Discipline'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+')
        parser.add_argument('discipline')
        
    def handle(self, *args, **options):
        discipline = options['discipline']
       
        for filename in options['filename']:
            print('Adding synonyms from ' + filename)
    
            line = 0
            csvfile = None

            try:
                discipline = Discipline.objects.get(name=discipline)
            except Discipline.DoesNotExist:
                raise CommandError('Disciplina "%s" nao existe' % discipline)

            try:
                csvfile = open(filename, 'r')
            except Exception as e:
                print(e)
                continue

            reader = csv.reader(csvfile, delimiter=',')
            first = True
            for row in reader:
                try:
                    line = line + 1

                    if first:
                        first = False
                        continue

                    if row[0]:
                        topic = Topic.objects.filter(name=row[0], discipline=discipline)
                        
                        if row[1] and topic:
                            syns = [syn.strip() for syn in row[1].split(',') if syn.strip() != '']
                            
                            for item in syns:
                                check_syns= Synonym.objects.filter(term__iexact=item.lower())

                                if not check_syns:
                                    syn_create = Synonym.objects.create(term=item)
                                    
                                    for top in topic:
                                        syn_create.topics.add(top)
                                    
                                    syn_create.save()
                                    print('Success adding synonym in line ' + str(line))
                        else:
                            continue

                except Exception as e:
                    print('ERROR adding synonym in line ' + str(line))
                    print(e)
                    continue