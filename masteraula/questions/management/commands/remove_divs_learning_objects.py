from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import LearningObject
import re
from bs4 import BeautifulSoup as bs


class Command(BaseCommand):
    help = 'populate data from json-questions directory'

    def handle(self, *args, **options):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='<div').order_by('id')
        statements = [(q.text, q.id) for q in learning_objects]

        program = re.compile('<div[^<]*>(.*?)<\/div>')             
        program2 = re.compile('<div[^<]*>')                

        clean = []
        removed = []
        clean2 = []
        removed2 = []

        for stm, _ in statements:
            curr_removed = []
            while(program.search(stm)):
                curr_removed.append(program.findall(stm))
                stm = program.sub('<p>\\1</p>', stm)
            removed.append(curr_removed)
            clean.append(stm)

        for stm in clean:
            curr_removed = []
            while(program2.search(stm)):
                curr_removed.append(program.findall(stm))
                stm = program2.sub('', stm)
            removed2.append(curr_removed)
            clean2.append(stm)


        html = ''
        for i in range(len(clean2)):
            soup = bs(statements[i][0], "html.parser")
            stmt = soup.prettify()
            soup = bs(clean2[i], "html.parser")
            clean_stmt = soup.prettify()
            html += '<hr><h1>Questao {}</h1>'.format(statements[i][1])
            html += '''<table style='width: 100%'><tr>
            <td>
                <textarea style='width: 100%; height: 300px'>{}</textarea>
            </td>
            <td>
                <textarea style='width: 100%; height: 300px'>{}</textarea>
            </td>
            </tr>
            <tr>
            <td>
                {}
            </td>
            <td>
                {}
            </td>
            </tr></table>'''.format(stmt, clean_stmt, stmt, clean_stmt)

        with open('res1.html', 'w') as f:
            f.write(html)