from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline, LearningObject
from django.core.files import File
import json
import os
import re
import csv

class Command(BaseCommand):
    help = 'populate data from json-questions directory (data extracted from enem estuda)'

    def add_arguments(self, parser):
        parser.add_argument('file_name', nargs='+')
        parser.add_argument('img_dir')

    def handle(self, *args, **options):
        img_dir = options['img_dir']

        for filename in os.listdir('json-questions/'):
            if not filename.endswith('.json'):
                continue

            print ('Salvando questoes do arquivo ' + filename)
            errors = []
            errors_list = []
        
            with open('json-questions/' + filename) as data_file:
                data = json.load(data_file)
                discipline = filename.split(".")[0]
                for index, question_data in enumerate(data):
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
                            exists = check_exists(data, img_dir)

                            if exists == False:
                                print("Não existe imagem no Enunciado P1 " + question_data["id_enem"])
                                check = True                                           
                        
                        #Check if statement p2 has image  
                        for data in question_data["statement_p2"]:
                            exists = check_exists(data, img_dir)
                                   
                            if exists == False:
                                print("Não existe imagem no Enunciado P2 " + question_data["id_enem"])
                                check = True                                                           

                        #Check if alternatives has images  
                        for data in question_data["alternatives"]:
                            exists = check_exists(data, img_dir)

                            if exists == False:
                                print("Não existe imagem nas alternativas " + question_data["id_enem"])
                                check = True                                        
                        
                        #Check if object_text has images  
                        for data in question_data["object_text"]:
                            exists = check_exists(data, img_dir)
                               
                            if exists == False:
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
                        message = ''
                        
                        if "alternatives" in question_data and len(question_data["alternatives"]) > 0:
                            for i, answer_data in enumerate(question_data["alternatives"]):
                            
                                if i == int(question_data["resposta"]): 
                                    right_answer = True
                                    answer_correct = answer_data
                            
                            if not right_answer:
                                print('Question ' + str(index + 1) + ' dont have right answer')
                                continue
                            if message != '':
                                print(message)
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
                    
                        if  len(question_data["object_text"]) > 0:
                            learning_object = LearningObject.objects.create(owner_id=1, text=object_text)
                            
                            if "object_source" in question_data:
                                learning_object.source = question_data["object_source"]
                            len_object = sum('<img' in s for s in question_data["object_text"]) 
                            
                            for obj in question_data["object_text"]:
                                img = find_img(obj)
                                if len(img) > 0:
                                    for text in img:
                                        data = find_src(text)
                                        for i in data:
                                            image = name_image(i).split("/")[-1]

                                            if count_obj > 0:
                                                new_name = str(learning_object.id) + '_' + str(count_obj) + '.' + image.split('.')[-1]
                                                count_obj = count_obj + 1           
                                            else:
                                                count_obj = count_obj + 1
                                                new_name = str(learning_object.id) + '.' + image.split('.')[-1]

                                            os.rename(img_dir + '/' + image, img_dir + '/' + new_name)
                                           
                                            if len_object == 1 and len(question_data["object_image"]) == 0:
                                                object_image = image
                                                learning_object.folder_name = question_data["source"] + "-" + question_data["year"]
                                                learning_object.image.save(new_name, File(open(img_dir + '/' +  new_name, 'rb'))) 
                                                obj = obj.replace(text, ' ')   

                                            if len_object > 1 or question_data["object_image"] != "":
                                                obj = obj.replace(text, '<img src="https://s3.us-east-2.amazonaws.com/masteraula/images/question_images/new_questions/' + new_name + '"> ')
                                obj = clean_div(obj)
                                object_text = object_text + obj
                                learning_object.text = object_text
                                learning_object.save()
                                                           
                            question.learning_objects.add(learning_object.id)
                            print ("Objeto texto da questão Salvo")
                       
                        if  len(question_data["object_image"]) > 0:
                            object_image = question_data["object_image"].replace("\"", "").split("/")[-1]
                            if "?" in object_image:
                                object_image = object_image.split("?")[0]
                            print ("Objeto imagem da questão Salvo")
                            
                            learning_object = LearningObject.objects.create(owner_id=1, folder_name=question_data["source"] + "-" + question_data["year"])
                            rename = str(learning_object.id) + '.' + object_image.split(".")[-1]
                            learning_object.image.save(rename, File(open(img_dir + '/' + object_image, 'rb')))
                            question.learning_objects.add(learning_object.id)
                            if "object_source" in question_data:
                                learning_object.source = question_data["object_source"]
                            os.remove(img_dir + '/' + object_image)

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

                                    os.rename(img_dir + '/' + image, img_dir + '/' + new_name)
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

                                            os.rename(img_dir + '/' + image, img_dir + '/' + new_name)
                                            answer_data = answer_data.replace(text, '<img src="https://s3.us-east-2.amazonaws.com/masteraula/images/question_images/new_questions/' + new_name + '"> ')
                                answer = Alternative.objects.create(text=answer_data,
                                                                    is_correct=is_correct,
                                                                    question_id=question.id)

                    except Exception as e:
                        print('ERROR adding question Enem ' + question_data["id_enem"])
                        print(e)
                        errors_list.append([question_data["id_enem"]]) 
                        continue

        with open('errors_imagens.csv', mode='w') as errors_imagens:
            errors_imagens = csv.writer(errors_imagens, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            errors_imagens.writerows(errors)

        with open('errors_questions.csv', mode='w') as errors_questions:
                            errors_questions = csv.writer(errors_questions, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                            errors_questions.writerows(errors_list)

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