from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline, LearningObject
from django.core.files import File

import docx2txt
import json
import os
import re
import datetime
from bs4 import BeautifulSoup
from subprocess import call

class Command(BaseCommand):
    help = 'populate data from docx (teachers)'

    # Example: python manage.py convert_docx_json teste_prof.docx Português

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('discipline')
        parser.add_argument('id')

    def handle(self, *args, **options):
        filename = options['filename']
        discipline = options['discipline']
        id_question = options['id']

        try:
            discipline = Discipline.objects.get(name=discipline)
        except Discipline.DoesNotExist:
            raise CommandError('Disciplina "%s" nao existe' % discipline)

        call(['pandoc', '-o', 'output.html', filename])
        call(['python3', 'extract_images.py', filename])

        file_html = open('output.html', 'r', encoding='utf-8')

        text = file_html.read()
        obj = re.split('<p>Objeto:', text)

        reg = r"<p>Nome:(.*?)</p>"
        owner = "".join(re.findall(reg, text, flags=0)).strip()

        obj.pop(0)
        jsdata = []
        count = 0
        null = None

        for o in obj:
            o = "Objeto:" + o
            object_types = []
            reg = r"Objeto:(.*?)Tags:"
            obj_text = "".join(re.findall(reg, o.replace("\n", ""), flags=0)).strip()

            reg = r"<img(.*?)/>"
            obj_img = "".join(re.findall(reg, o, flags=0))

            obj_text = BeautifulSoup(obj_text, 'html.parser')
            obj_text = obj_text.prettify()

            reg = r"Tags:(.*?)Fonte:"
            obj_tags = re.findall(reg, o.replace("\n", "").replace("<p>", "").replace("</p>", ""), flags=0)
            reg = r"Fonte:(.*?)Questão:"
            obj_source = "".join(re.findall(reg, o.replace("\n", "").replace("<p>", "").replace("</p>", ""), flags=0))

            if len(obj_text) < 2 or len(obj_img) < 2:
                id_object = null

            else:
                learning_object = LearningObject.objects.create(
                    owner_id=1, source=obj_source, object_types=object_types)
                id_object = learning_object.id

                if len(obj_text) > 2:
                    learning_object.text = obj_text
                    learning_object.save()
                    object_types.append('T')

                if len(obj_img) > 2:
                    object_types.append('I')
                    count = count + 1
                    name = [filename for filename in os.listdir(
                        "images") if filename.startswith(filename + "-image" + str(count))]

                    learning_object.image.save(filename + "-image" + str(count),
                                               File(open(filename + "-image" + str(count), 'rb')))
                    os.remove(filename + "-image" + str(count))

                for tag in obj_tags:
                    learning_object.tags.add("".join(tag))
                    learning_object.save()

            question = re.split('Questão:', o)
            question.pop(0)

            for item in question:
                reg = r"<p>Enunciado:(.*?)Resolução:"
                statement = "".join(re.findall(reg, item.replace("\n", ""), flags=0))
                
             
                reg = r"Resolução:(.*?)Tags:"
                resolution = "".join(re.findall(reg, item.replace("\n", ""), flags=0))
                reg = r"Tags:(.*?)Alternativas:"
                tags = "".join(re.findall(reg, item.replace("\n", "").replace(
                    "<p>", "").replace("</p>", ""), flags=0)).split(',')
                reg = r"Alternativas:(.*?)Resposta:"
                alternatives = "".join(re.findall(reg, item.replace("\n", "").replace(
                    "<p>", "").replace("</p>", ""), flags=0)).strip().split('()')

                reg = r"Vestibular:(.*?)Ano:"
                source = "".join(re.findall(reg, item.replace("\n", "").replace(
                    "<p>", "").replace("</p>", ""), flags=0)).strip()
                reg = r"Ano:(.*?)Resposta:"
                year = "".join(re.findall(reg, item.replace("\n", "").replace(
                    "<p>", "").replace("</p>", ""), flags=0)).strip()
                answer = "".join(re.split('Resposta:', item.replace("\n", ""))[-1])
                answer = "".join(re.findall(r"[0-9]", answer))

                if len(year) < 2:
                    year = datetime.datetime.now().year

                if len(alternatives) < 2:
                    alternatives = ""
                
                if len(statement) <2:
                    continue

                if len(alternatives) < 2 and len(resolution) < 2:
                    continue

                id_question = id_question + 1

                jsdata.append({"id": id_question,
                               "author": 1,
                               "authorship": owner,
                               "statement": statement,
                               "difficulty": "M",
                               "resolution": resolution,
                               "year": int(year),
                               "disciplines": discipline.id,
                               "teaching_levels": 4,
                               "souce": source,
                               "tags": tags,
                               "alternatives": alternatives,
                               "resposta": answer,
                               "learning_object": id_object,
                               "object_source": obj_source,
                               "object_types": object_types
                               })

        with open('questions.json', 'w', encoding='utf-8') as outfile:
            json.dump(jsdata, outfile, ensure_ascii=False, indent=2)
