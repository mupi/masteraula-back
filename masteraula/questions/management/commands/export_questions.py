from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Alternative, TeachingLevel, Discipline
from django.apps import apps
import csv
import sys
import re


"""
 Prints CSV of fields of a model.
"""

class Command(BaseCommand):
    help = ("Output the specified model as CSV: ./manage.py export_questions > questions.csv")
    args = '[Question]'

    fields = ['ID', 'Autor','Origem','Ano','Grau de dificuldade','Disciplinas','Nível de ensino','Enunciado','Resolução','Alternativa Correta','Alternativa A','Alternativa B','Alternativa C','Alternativa D','Alternativa E']
    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    writer.writerow(fields)
    
    def handle(self, *app_labels, **options):
        
        question = Question.objects.all()
       
        for q in question:
            
            difficulty = None
            disc = None
            teaching_level = None 
            resp = None 
            alternative = None
            
            answer = Alternative.objects.filter(question=q)
            disciplines = Discipline.objects.filter(question=q)
            teaching_levels = TeachingLevel.objects.filter(question=q)
            statement = remove_tags(rename_image_tags(q.statement))
            
            if q.difficulty == 'M':
                difficulty = "Médio"
            
            if q.difficulty == 'E':
               difficulty = "Fácil"
            
            if q.difficulty == 'H':
               difficulty = "Difícil"
                        
            for d in disciplines:
                disc = d.name      
                
            for t in teaching_levels:
                teaching_level = t.name

            for a in answer:      
                if a.is_correct:
                    resp = remove_tags(rename_image_tags(a.text))

            fields = [q.id, q.author, q.source, q.year, difficulty, disc, teaching_level, statement, q.resolution, resp]

            for a in answer:
                alternative = remove_tags(rename_image_tags(a.text))
                fields += [alternative]
                
            writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
            writer.writerow(fields)

def rename_image_tags(text):
    TAG_RE = re.compile("<img(.)*?src=\"(.*?)\"(.)*?>")
    return TAG_RE.sub('[IMAGEM]', text)

def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)
               
        