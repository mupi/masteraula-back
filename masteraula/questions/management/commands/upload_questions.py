from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline, LearningObject
from django.core.files import File

from .check_duplicates import check_duplicates

import json
import os
import re
import csv

class Command(BaseCommand):
    help = 'populate data from json-questions directory (data extracted from enem estuda)'

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('img_dir')
        parser.add_argument('discipline')

    def handle(self, *args, **options):
        img_dir = options['img_dir']
        discipline = options['discipline']

        for filename in os.listdir('json-questions/'):
            if not filename.endswith('.json'):
                continue

            print ('Salvando questoes do arquivo ' + filename)
            errors = []
            errors_list = []
            alternatives = []
            no_alternatives = []
            two_alternatives = []
            more_alternatives = []

            question_with_objects = []

            success = []
        
            with open('json-questions/' + filename) as data_file:
                data = json.load(data_file)

                # duplicate_ids = []
                duplicate_ids = check_duplicates(data, discipline)

                for index, question_data in enumerate(data):
                    if question_data['id_enem'] in duplicate_ids:
                        print("Questão {} provavelmente duplicada".format(question_data['id_enem']))
                        continue
                    try:
                        statement = ""
                        statement_image = ""
                        object_text = ""
                        image = ""
                        check = False
                        count = 0
                        count_obj = 0

                        #Check if statement p1 has image  
                        for data in question_data["statement_p1"]:

                            if check_exists(data, img_dir) == False:
                                print("Não existe imagem no Enunciado P1 " + question_data["id_enem"])
                                check = True                                           
                        
                        #Check if statement p2 has image  
                        for data in question_data["statement_p2"]:
                                   
                            if check_exists(data, img_dir) == False:
                                print("Não existe imagem no Enunciado P2 " + question_data["id_enem"])
                                check = True                                                           

                        #Check if alternatives has images  
                        for data in question_data["alternatives"]:

                            if check_exists(data, img_dir) == False:
                                print("Não existe imagem nas alternativas " + question_data["id_enem"])
                                check = True                                        
                        
                        #Check if object_text has images  
                        for data in question_data["object_text"]:
                               
                            if check_exists(data, img_dir) == False:
                                print("Não existe imagem no objeto texto " + question_data["id_enem"])
                                check = True   
                        
                        #Check if object_image has images 
                        if "<img" in question_data["object_image"]:
                            object_image = question_data["object_image"].replace("\"", "").split("/")[-1]
                            if "?" in object_image:
                                object_image = object_image.split("?")[0] 
                            exists = os.path.isfile(img_dir + '/' + object_image)

                            if exists == False:
                                print("Não existe imagem no objeto imagem " + question_data["id_enem"])
                                check = True  

                        if check:
                            errors.append([question_data["id_enem"]])
                            check = False  
                            continue
                                
                        else:
                            pass

                        # verify if the question has one and just one right answer
                        right_answer = False
                    
                        if "alternatives" in question_data:
                            if len(question_data["alternatives"])  == 0:
                                print('Question ' + str(index + 1) + ' dont have alternatives')
                                no_alternatives.append(question_data['id_enem'])
                                continue
                            elif len(question_data["alternatives"])  == 2:
                                print('Question ' + str(index + 1) + ' have only 2 alternatives')
                                two_alternatives.append(question_data['id_enem'])
                                continue
                            elif len(question_data["alternatives"]) > 5:
                                print('Question ' + str(index + 1) + ' has lots of alternatives')
                                more_alternatives.append(question_data['id_enem'])
                                continue
                            else:
                                alternatives.append(len(question_data["alternatives"]))
                                for i, answer_data in enumerate(question_data["alternatives"]):
                                
                                    if i == int(question_data["resposta"]): 
                                        right_answer = True
                                        answer_correct = answer_data
                                
                                if not right_answer:
                                    print('Question ' + str(index + 1) + ' dont have right answer')
                        
                        if  len(question_data["object_text"]) > 0 or len(question_data["object_image"]) > 0:
                            question_with_objects.append(question_data['id_enem'])
                            continue
                       
                        try:
                            discipline = Discipline.objects.get(name=discipline)
                        except Discipline.DoesNotExist:
                            raise CommandError('Disciplina "%s" nao existe' % discipline)
                                            
                        if question_data["difficulty"]: 
                            if question_data["difficulty"] == "Fácil":
                                difficulty = "E"
                            if question_data["difficulty"] == "Médio":
                                difficulty = "M"
                            if question_data["difficulty"] == "Difícil":
                                difficulty = "H"
                        else:
                            difficulty = ''

                        teaching_level = 4
                        
                        if question_data["statement_p1"]:
                            for data in question_data["statement_p1"]:
                                data = clean_div(data)
                                statement = statement + data

                        if question_data["statement_p2"]:
                            for data in question_data["statement_p2"]:
                                data = clean_div(data)
                                statement = statement + data

                        
                        # continue
                                        
                        question = Question.objects.create(statement = statement,
                                                            year=question_data["year"],
                                                            source=question_data["source"],
                                                            resolution= "",
                                                            difficulty=difficulty,
                                                            author_id=1)
                                
                        question.disciplines.add(discipline)
                        question.teaching_levels.add(teaching_level)                      

                        for tag in question_data["tags"]:
                            if len(tag) < 100:
                                question.tags.add(tag)
                                question.save()

                        print ("Questao " + question_data["id_enem"] + " Salva")

                        # if  len(question_data["object_text"]) > 0:
                        #     learning_object = LearningObject.objects.create(owner_id=1, text=object_text)
                            
                        #     if "object_source" in question_data:
                        #         learning_object.source = question_data["object_source"]
                        #     len_object = sum('<img' in s for s in question_data["object_text"]) 
                            
                        #     for obj in question_data["object_text"]:
                        #         img = find_img(obj)
                        #         if len(img) > 0:
                        #             for text in img:
                        #                 data = find_src(text)
                        #                 for i in data:
                        #                     image = name_image(i).split("/")[-1]

                        #                     if count_obj > 0:
                        #                         new_name = str(learning_object.id) + '_' + str(count_obj) + '.' + image.split('.')[-1]
                        #                         count_obj = count_obj + 1           
                        #                     else:
                        #                         count_obj = count_obj + 1
                        #                         new_name = str(learning_object.id) + '.' + image.split('.')[-1]

                        #                     os.rename(img_dir + '/' + image, 'img_upload' + '/' + new_name)
                                           
                        #                     if len_object == 1 and len(question_data["object_image"]) == 0:
                        #                         object_image = image
                        #                         learning_object.folder_name = question_data["source"] + "-" + question_data["year"]
                        #                         learning_object.image.save(new_name, File(open(img_dir + '/' +  new_name, 'rb'))) 
                        #                         obj = obj.replace(text, ' ')   

                        #                     if len_object > 1 or question_data["object_image"] != "":
                        #                         obj = obj.replace(text, '<img src="https://s3.us-east-2.amazonaws.com/masteraula/images/question_images/new_questions/' + new_name + '"> ')
                        #         obj = clean_div(obj)
                        #         object_text = object_text + obj
                        #         learning_object.text = object_text
                        #         learning_object.save()
                                                           
                        #     question.learning_objects.add(learning_object.id)
                        #     print ("Objeto texto da questão Salvo")
                       
                        # if  len(question_data["object_image"]) > 0:
                        #     object_image = question_data["object_image"].replace("\"", "").split("/")[-1]
                        #     if "?" in object_image:
                        #         object_image = object_image.split("?")[0]
                        #     print ("Objeto imagem da questão Salvo")
                            
                        #     learning_object = LearningObject.objects.create(owner_id=1, folder_name=question_data["source"] + "-" + question_data["year"])
                        #     rename = str(learning_object.id) + '.' + object_image.split(".")[-1]
                        #     learning_object.image.save(rename, File(open(img_dir + '/' + object_image, 'rb')))
                        #     question.learning_objects.add(learning_object.id)
                        #     if "object_source" in question_data:
                        #         learning_object.source = question_data["object_source"]
                        #     os.remove(img_dir + '/' + object_image)

                        #Rename Image Statement
                        img = find_img(question.statement)
                        if len(img) > 0:
                            for text in img:
                                data = find_src(text)
                                for i in data:
                                    image = name_image(i).split("/")[-1]

                                    if count > 0:
                                        new_name = str(question.id) + '_' + str(count) + '.' + image.split('.')[-1]
                                        count = count + 1           
                                    else:
                                        count = count + 1
                                        new_name = str(question.id) + '.' + image.split('.')[-1]

                                    os.rename(img_dir + '/' + image, 'img_upload' + '/' + new_name)
                                    question.statement = question.statement.replace(text, '<img src="https://s3.us-east-2.amazonaws.com/masteraula/images/question_images/new_questions/' + new_name + '"> ')
                                    question.save()    
                        
                        #Create alternatives and rename Image 
                        if "alternatives" in question_data and len(question_data["alternatives"]) > 0:
                            for answer_data in question_data["alternatives"]:
                                answer_data = clean_div(answer_data)
                                if answer_correct == answer_data:
                                    is_correct = True
                                else:
                                    is_correct = False
                                
                                img = find_img(answer_data)
                                if len(img) > 0:
                                    for text in img:
                                        data = find_src(text)
                                        for i in data:
                                            image = name_image(i).split("/")[-1]

                                            if count > 0:
                                                new_name = str(question.id) + '_' + str(count) + '.' + image.split('.')[-1]
                                                count = count + 1           
                                            else:
                                                count = count + 1
                                                new_name = str(question.id) + '.' + image.split('.')[-1]

                                            os.rename(img_dir + '/' + image, 'img_upload' + '/' + new_name)
                                            answer_data = answer_data.replace(text, '<img src="https://s3.us-east-2.amazonaws.com/masteraula/images/question_images/new_questions/' + new_name + '"> ')
                                answer = Alternative.objects.create(text=answer_data,
                                                                    is_correct=is_correct,
                                                                    question_id=question.id)
                                                                    
                        success.append(question_data['id_enem'])

                    except Exception as e:
                        print('ERROR adding question Enem ' + question_data["id_enem"])
                        print(e)
                        errors_list.append([question_data["id_enem"]]) 
                        continue

        errors_lists = [('no_alternatives', no_alternatives),
            ('two_alternatives', two_alternatives),
            ('question_with_objects', question_with_objects),
            ('errors', errors),
            ('errors_list', errors_list),
        ]

        for erro_name, error_list in errors_lists:
            if error_list:
                with open('error_{}.csv'.format(erro_name), mode='w') as error_file:
                    error_file = csv.writer(error_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    error_file.writerows(error_list)

        print('Foram adicionadas {} questoes: {}'.format(len(success), success))

def clean_div(text):
    div = re.findall(r'<div.*?>', text)
    if len(div) > 0:
        for i in div:
            text = text.replace(i, "")
    text = text.replace("</div>", "")
    return text

def find_src(text):
    if "latex" in text:
        text = re.findall(r'src=".*?"', text)
        return text
    text = re.findall(r'src=".*?" ', text)
    return text

def find_img(text):
    text = re.findall(r'<img.*?>', text)
    return text

def name_image(text):
    image = text.replace("\"", "").split("/")[-1]

    if "?" in text:
        image = text.split("?")[0]
    image = image.strip()
    return image

def check_exists(data, img_dir):
    data = find_src(data)
    if len(data) > 0:
        for i in data:
            image = name_image(i).split("/")[-1]
        exists = os.path.exists(img_dir + '/' + image)
        return exists