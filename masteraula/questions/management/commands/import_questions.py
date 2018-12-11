# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline, LearningObject
from masteraula.users.models import User
from django.core.files import File

import csv
import os

class Command(BaseCommand):
    help = 'Import question from CSV file it is different from export_questions. If you run it twice, the questions will be duplicate'


    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+')
        parser.add_argument('img_dir')


    def handle(self, *args, **options):
        img_dir = options['img_dir']

        for filename in options['filename']:
            print('Adding images from ' + filename)
            file_added_images = []
            file_existed_images = []
            file_failed_images = []
            file_learning_objects = {}
            line = 0

            csvfile = None
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

                    # ignore first occurence (titles)
                    if first:
                        first = False
                        continue
                    #   0      1      2      3    45678    9        10         11      12     13    14      15      16
                    # AUTOR | OBJ? | OBJ | ENUM | ABCDE | RESP | RESOLUCAO | SOURCE | YEAR | DISC | DIF | ENSINO | TAGS
                    
                    author = User.objects.get(name=row[0])

                    learning_object = None
                    if row[2]:
                        if row[2] in file_learning_objects:
                            learning_object = file_learning_objects[row[2]]
                        else:
                            if row[1].upper() == 'S':
                                learning_object = LearningObject.objects.create(owner=author, folder_name=filename.split('.')[0])
                                learning_object.image.save(row[2], File(open(img_dir + '/' + row[2], 'rb')))
                            else:
                                learning_object = LearningObject.objects.create(owner=author, text=row[2])
                            file_learning_objects[row[2]] = learning_object

                    statement = row[3]
                    alternatives_text = []
                    for i in range(4,9):
                        if row[i]:
                            if (i == ord(row[9].upper()) - ord('A') + 4):
                                alternatives_text.append((row[i], True))    # Right alternative
                            else:
                                alternatives_text.append((row[i], False))   # Wrong alternative
                    
                    resolution = row[10] if row[10] else ''
                    source = row[11] if row[11] else ''
                    year = int(row[12]) if row[12] else ''
                    
                    disciplines = [discipline_id.strip() for discipline_id in row[13].split(',')]
                    disciplines = [int(discipline_id.split(' ')[0]) for discipline_id in disciplines]
                    disciplines = [d for d in Discipline.objects.filter(id__in=disciplines)]

                    difficulty = row[14].upper() if row[14] else 'M'

                    teaching_levels = [teaching_level_id.strip() for teaching_level_id in row[15].split(',')]
                    teaching_levels = [int(teaching_level_id.split(' ')[0]) for teaching_level_id in teaching_levels]
                    teaching_levels = [d for d in TeachingLevel.objects.filter(id__in=teaching_levels)]

                    tags = [tag.strip() for tag in row[16].split(',')]

                    question = Question.objects.create(author=author,
                                                        statement=statement,
                                                        resolution=resolution,
                                                        difficulty=difficulty,
                                                        year=year,
                                                        source=source)

                    if learning_object:
                        question.learning_objects.add(learning_object)

                    for alternative in alternatives_text:
                        Alternative.objects.create(question=question,text=alternative[0], is_correct=alternative[1])
                    
                    for discipline in disciplines:
                        question.disciplines.add(discipline)

                    for teaching_level in teaching_levels:
                        question.teaching_levels.add(teaching_level)

                    for tag in tags:
                        question.tags.add(tag)

                    question.save()
                    file_added_images.append(question.id)
                    print('Success adding question with id ' + str(question.id) + ' in line ' + str(line))
                except Exception as e:
                    print('ERROR adding question in line ' + str(line))
                    print(e)
                    file_failed_images.append(line)
                    continue
            print('Total added images from ' + filename + ': ' + str(len(file_added_images)))
            print(file_added_images)
            print('Total failed images from ' + filename + ': ' + str(len(file_failed_images)))
            print(file_failed_images)
