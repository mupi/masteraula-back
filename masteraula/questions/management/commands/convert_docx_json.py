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
        owner = "".join(re.findall(reg, text.replace("\n", ""), flags=0))
        obj.pop(0)
        jsdata = []
        count = 0
        null = None

        for o in obj:

            reg = r"Texto:(.*?)Imagem:"
            obj_text = "".join(re.findall(reg, o.replace("\n", ""), flags=0))
            reg = r"Imagem:(.*?)Tags:"
            obj_img = "".join(re.findall(reg, o.replace("\n", ""), flags=0))

            reg = r"Tags:(.*?)Fonte:"
            obj_tags = re.findall(reg, o.replace("\n", ""), flags=0)
            reg = r"Fonte:(.*?)Questão:"
            obj_source = "".join(re.findall(reg, o.replace("\n", ""), flags=0))

            learning_object = LearningObject.objects.create(owner_id=1, source=obj_source, text=obj_text)

            if "sim" in obj_img.lower():
                count = count + 1
                name = [filename for filename in os.listdir(img_dir) if filename.startswith("image" + str(count))]

                learning_object.image.save("image" + str(count), File(open(img_dir + "/" + "".join(name), 'rb')))

            for tag in obj_tags:
                learning_object.tags.add("".join(tag))
                learning_object.save()

            question = re.split('Questão:', text)
            question.pop(0)

            for item in question:
                reg = r"Enunciado:(.*?)Resolução:"
                statement = "".join(re.findall(reg, item.replace("\n", ""), flags=0))
                reg = r"Resolução:(.*?)Tags:"
                resolution = "".join(re.findall(reg, item.replace("\n", ""), flags=0))
                reg = r"Tags:(.*?)Alternativas:"
                tags = "".join(re.findall(reg, item.replace("\n", ""), flags=0)).split(',')
                reg = r"Alternativas:(.*?)Resposta:"
                alternatives = "".join(re.findall(reg, item.replace("\n", ""), flags=0)).strip().split(',')

                if len(alternatives) < 0:
                    alternatives = null

                answer = "".join(re.split('Resposta:', item.replace("\n", ""))[-1])

                jsdata.append({"id": null,
                               "author": 1,
                               "statement": statement,
                               "difficulty": "M",
                               "resolution": resolution,
                               "year": datetime.datetime.now().year,
                               "disciplines": discipline.id,
                               "teaching_levels": 4,
                               "souce": owner,
                               "tags": tags,
                               "alternatives": alternatives,
                               "resposta": answer,
                               "learning_object": learning_object.id,
                               "object_source": null
                               })

        with open('question.json', 'w', encoding='utf-8') as outfile:
            json.dump(jsdata, outfile, ensure_ascii=False, indent=2)
