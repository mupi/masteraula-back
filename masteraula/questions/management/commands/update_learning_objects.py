# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline, LearningObject
from masteraula.users.models import User
from django.core.files import File

import re
import csv
import os
import urllib
import time

class Command(BaseCommand):
    help = 'Update the csv questions and repeated ones. A csv-files folder with the files is mandatory'

    def add_arguments(self, parser):
        parser.add_argument('same_object', nargs='+')

    def getImgTags(self, text):
        pattern = "(<img[\\\/ \w \d]*?src=\"(.|\n)+?\"[\\\/ \w \d]*?>)"
        return re.findall(pattern, text)

    def getUrls(self, text):
        pattern = "src=\"((.|\n)+?)\"[\\\/ \w \d]*?"
        return re.findall(pattern, text)

    def getImageNames(self, text):
        pattern = ".+\/(.+?)\/(.+?)(jpg|png)"
        return re.findall(pattern, text)

    def writeBackup(self, id, statement):
        self.backup.write(str(id))
        self.backup.write('\n' + statement + '\n')

    def handle(self, *args, **options):
        # Mantém um backup das statements para se algo der errado
        self.backup = open('bkp' + str(int(round(time.time() * 1000))) + '.txt', 'w')

        questions_with_objects = []
        questions_with_same_objects = []
        saved_questions = []
        errors = []

        # Todos os objetos de aprendizagem
        for filename in os.listdir('json-files/'):
            all_files = open('json-files/' + filename, 'r') 
            for line in all_files: 
                questions_with_objects.append(int(line)) 
                

        # Questões repetidas para objetos de aprendizagem
        for same_object_file in options['same_object']:
            print(same_object_file)
            with open(same_object_file) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    questions_with_same_objects.append((int(row[0]),int(row[1])))

        author = User.objects.get(name='mupi')

        questions_with_same_objects.sort()
        for question_same in questions_with_same_objects:
            learning_objects = []
            first = True
            print(question_same)
            for question_id in range(question_same[0], question_same[1] + 1):
                print(question_id)
                try:
                    question = Question.objects.get(id=question_id)

                    for res in self.getImgTags(question.statement):
                        # Já existe um objeto de aprendizado para a questão
                        if not first and learning_objects:
                            for learning_object in learning_objects:
                                question.learning_objects.add(learning_object)
                                
                        # Não existe, logo temos que baixar (ou tentar) a imagem e criar um objeto de aprendizagem
                        else:
                            for url in self.getUrls(res[0]):
                                for name in self.getImageNames(url[0]):
                                    folder_name = name[0]
                                    image_name = name[1] + name[2]
                                    complete_path = 'imagens/' + folder_name + '/' + image_name
                                    print(url[0])
                                    if not os.path.exists('imagens/' + folder_name):
                                        os.mkdir('imagens/' + folder_name)
                                    if not os.path.isfile(complete_path):
                                        urllib.request.urlretrieve(url[0], complete_path)

                                    learning_object = LearningObject.objects.create(owner=author, folder_name=folder_name)
                                    learning_object.image.save(image_name, File(open(complete_path, 'rb')))
                                    question.learning_objects.add(learning_object)

                                    learning_objects.append(learning_object)

                        self.writeBackup(question.id, question.statement)
                        question.statement = question.statement.replace(res[0], '') 
                    question.save()
                except Exception as e:
                    print(e)
                    errors.append(question_id)

                first = False
                saved_questions.append(question_id)                    
        
        # Faz agora com as questões únicas (objetos de aprendizado exclusivos das questões)
        print("Equal done")
        questions_with_objects.sort()
        for question_id in questions_with_objects:
            print(question_id)
            # Já foi tratado anteriormente pela primeira parte do algoritmo
            if question_id in saved_questions:
                continue
            try:
                question = Question.objects.get(id=question_id)

                # Sempre vamos criar objetos de aprendizagem aqui
                for res in self.getImgTags(question.statement):
                    for url in self.getUrls(res[0]):
                        for name in self.getImageNames(url[0]):
                            folder_name = name[0]
                            image_name = name[1] + name[2]
                            complete_path = 'imagens/' + folder_name + '/' + image_name
                            print(url[0])
                            if not os.path.exists('imagens/' + folder_name):
                                os.mkdir('imagens/' + folder_name)
                            if not os.path.isfile(complete_path):
                                urllib.request.urlretrieve(url[0], complete_path)

                            learning_object = LearningObject.objects.create(owner=author, folder_name=folder_name)
                            learning_object.image.save(image_name, File(open(complete_path, 'rb')))
                            question.learning_objects.add(learning_object)

                    self.writeBackup(question.id, question.statement)
                    question.statement = question.statement.replace(res[0], '')
                question.save()
            except Exception as e:
                print(e)
                errors.append(question_id)
        self.backup.close()
        print(errors)