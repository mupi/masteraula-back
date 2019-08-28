from taggit.models import Tag
from .models import Question

from django.db import connection

from django.conf import settings
import spacy
import warnings

class RelatedQuestions(): 
   
    def similar_questions(self, question):
        en = [ discipline for discipline in question.disciplines.all() if discipline.name == 'Inglês' ]

        # if settings.RUNNING_DEVSERVER:
        #     if len(en) > 0:
        #         nlp = spacy.load('en_core_web_md')
        #     else:
        #         nlp = spacy.load('pt_core_news_sm')
        #         warnings.filterwarnings("ignore")
        
        # if not settings.RUNNING_DEVSERVER:
        if len(en) > 0:
            nlp =  settings.LANGUAGE_MODELS_EN
        else:
            nlp =  settings.LANGUAGE_MODELS_PT   

        topics = []
        print(len(connection.queries))
        questions = Question.objects.filter(topics__in=question.topics.all()).exclude(id=question.id)
        print(len(connection.queries))
        disciplines = Question.objects.filter(disciplines__in=question.disciplines.all()).exclude(id=question.id).order_by('?')
        print(len(connection.queries))

        if not questions.count():
            related_questions = list(disciplines[:4])
           
        else:
            tags = []

            for tag in question.tags.all():
                tags.append(tag.name)
            print(len(connection.queries))

            text = ' '.join(tags)
            tokens = nlp(text.lower())

            similar_questions = []
            
            for question in questions:
                for tag in question.tags.all():
                    for token in tokens:
                        
                        if nlp(tag.name.lower()).similarity(token) > 0.7:
                            if not question.id in similar_questions:
                                similar_questions.append(question.id)
            print(len(connection.queries))

            related_questions = questions.filter(id__in=similar_questions)
            print(len(connection.queries))

            ids = [i.id for i in related_questions]
            print(len(connection.queries))
            print(len(related_questions))

            if len(related_questions) > 4: 
                related_questions = list(related_questions.order_by('?')[:4])
                
            if len(related_questions) < 4: 
                qtd = 4 - len(related_questions)
                questions = questions.exclude(id__in=ids).order_by('?')[:qtd]
                related_questions =  list(related_questions) + list(questions)

                if len(related_questions) < 4:
                    qtd = 4 - len(related_questions)
                    disciplines = disciplines.exclude(id__in=ids)[:qtd]
                    related_questions  = list(related_questions) + list(disciplines)
       
        itens = []
        for item in related_questions:
            itens.append(item.id)
        print(len(connection.queries))

        return(itens) 
            

        