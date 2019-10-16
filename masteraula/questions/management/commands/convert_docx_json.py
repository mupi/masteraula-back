from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline, LearningObject
from django.core.files import File

import docx2txt
import json
import os
import re
import datetime


class Command(BaseCommand):
    help = 'populate data from docx (teachers)'

    #Example: python manage.py convert_docx_json teste_prof.docx img_dir Português

    def add_arguments(self, parser):
        parser.add_argument('filename')
        parser.add_argument('img_dir')
        parser.add_argument('discipline')

    def handle(self, *args, **options):
        filename = options['filename']
        img_dir = options['img_dir']
        discipline = options['discipline']

        try:
            discipline = Discipline.objects.get(name=discipline)
        except Discipline.DoesNotExist:
            raise CommandError('Disciplina "%s" nao existe' % discipline)

        text = docx2txt.process(filename, img_dir)
        obj = re.split('Objeto:', text)
       
        reg = r"Nome:(.*?)Objeto:"
        owner = "".join(re.findall(reg, text.replace("\n", ""), flags=0)).strip()
        obj.pop(0)
        jsdata = []
        count = 0
        null = None

        for o in obj:
            reg = r"Texto:(.*?)Imagem:"
            obj_text = "".join(re.findall(reg, o.replace("\n", ""), flags=0)).strip()
            reg = r"Imagem:(.*?)Tags:"
            obj_img = "".join(re.findall(reg, o.replace("\n", ""), flags=0))

            reg = r"Tags:(.*?)Fonte:"
            obj_tags = re.findall(reg, o.replace("\n", ""), flags=0)
            reg = r"Fonte:(.*?)Questão:"
            obj_source = "".join(re.findall(reg, o.replace("\n", ""), flags=0))
            
            if len(obj_text) > 0 or "sim" in obj_img.lower():
                learning_object = LearningObject.objects.create(owner_id=1, source=obj_source, text=obj_text)
                id_object = learning_object.id
            else:
                id_object = null

            if "sim" in obj_img.lower():
                count = count + 1
                name = [filename for filename in os.listdir(img_dir) if filename.startswith("image" + str(count))]

                learning_object.image.save("img_" + owner + str(count), File(open(img_dir + "/" + "".join(name), 'rb')))
                os.remove(img_dir + '/' + "".join(name))
            if len(obj_tags) > 1:    
                for tag in obj_tags:
                    learning_object.tags.add("".join(tag))
                    learning_object.save()

            question = re.split('Questão:', o)
            question.pop(0)

            for item in question:
                reg = r"Enunciado:(.*?)Resolução:"
                statement = "".join(re.findall(reg, item.replace("\n", ""), flags=0))
                reg = r"Resolução:(.*?)Tags:"
                resolution = "".join(re.findall(reg, item.replace("\n", ""), flags=0))
                reg = r"Tags:(.*?)Alternativas:"
                tags = "".join(re.findall(reg, item.replace("\n", ""), flags=0)).split(',')
                reg = r"Alternativas:(.*?)Resposta:"
                alternatives = "".join(re.findall(reg, item.replace("\n", ""), flags=0)).strip().split('.,')

                if len(alternatives) < 2:
                    alternatives = ""
                   
                answer = "".join(re.split('Resposta:', item.replace("\n", ""))[-1])
                answer = "".join(re.findall(r"[0-9]", answer))

                jsdata.append({"id": null,
                                "author": 1,
                                "authorship": owner,
                                "statement": statement,
                                "difficulty": "M",
                                "resolution": resolution,
                                "year": datetime.datetime.now().year,
                                "disciplines": discipline.id,
                                "teaching_levels": 4,
                                "souce": "",
                                "tags": tags,
                                "alternatives": alternatives,
                                "resposta": answer,
                                "learning_object": id_object,
                                "object_source": null
                                })   

        with open('questions.json', 'w', encoding='utf-8') as outfile:
            json.dump(jsdata, outfile, ensure_ascii=False, indent=2)
