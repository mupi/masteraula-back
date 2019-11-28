# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Topic, Synonym, Discipline
from django.core.files import File

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
            for i, row in enumerate(reader):
                try:

                    if first:
                        first = False
                        continue

                    if row[0]:
                        topic = Topic.objects.filter(name=row[0], discipline=discipline)
                        
                        if not topic:
                            print('Topic "%s" does not exist' % row[0])
                        
                        if row[1] and topic:
                            syns = [syn.strip() for syn in row[1].split(',') if syn.strip() != '']
                            
                            for item in syns:
                                check_syns= Synonym.objects.filter(term__iexact=item.lower())

                                if not check_syns:
                                    syn_create = Synonym.objects.create(term=item)
                                
                                else:
                                    syn_create = check_syns[0]
                                    
                                for top in topic:
                                    syn_create.topics.add(top)
                                    
                                syn_create.save()
                                    
                        else:
                            continue
                    print('Success adding synonym in line ' + str(i + 1))

                except Exception as e:
                    print('ERROR adding synonym in line ' + str(i + 1))
                    print(e)
                    continue