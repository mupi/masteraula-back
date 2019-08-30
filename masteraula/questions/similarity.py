import spacy
import warnings

from taggit.models import Tag
from .models import Question
from django.conf import settings

class RelatedQuestions(): 
   
    def similar_questions(self, question):
        questions = Question.objects.filter(topics__in=question.get_all_topics()).exclude(id=question.id).order_by('?')
        disciplines = Question.objects.filter(disciplines__in=question.disciplines.all()).exclude(id=question.id).order_by('?')
       
        if not questions.count():
            questions = disciplines[:4]
           
        else:
            if len(questions) >= 4: 
                questions = questions[:4]
                
            else:
                questions = questions[:len(questions)]
                questions += disciplines[:(4 - len(questions))]

        itens = []
        for item in questions:
            itens.append(item.id)

        return itens
            

        