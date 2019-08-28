import spacy
import warnings

from taggit.models import Tag
from .models import Question
from django.conf import settings

class RelatedQuestions(): 
   
    def similar_questions(self, question):
        en = [ discipline for discipline in question.disciplines.all() if discipline.name == 'Inglês' ]

        if settings.RUNNING_DEVSERVER:
            if len(en) > 0:
                nlp = spacy.load('en_core_web_md')
            else:
                nlp = spacy.load('pt_core_news_sm')
                warnings.filterwarnings("ignore")
        
        if not settings.RUNNING_DEVSERVER:
            if len(en) > 0:
                nlp =  settings.LANGUAGE_MODELS_EN
            else:
                nlp =  settings.LANGUAGE_MODELS_PT   

        topics = []
       
        questions = Question.objects.filter(topics__in=question.topics.all()).exclude(id=question.id)
        disciplines = Question.objects.filter(disciplines__in=question.disciplines.all()).exclude(id=question.id).order_by('?')
       
        if not questions.count():
            related_questions = list(disciplines[:4])
           
        else:
            tags = []

            for tag in question.tags.all():
                tags.append(tag.name)

            text = ' '.join(tags)
            tokens = nlp(text.lower())
            similar_questions = []
            
            for question in questions:
                for tag in question.tags.all():
                    for token in tokens:
                        if nlp(tag.name.lower()).similarity(token) > 0.7:
                            if not question.id in similar_questions:
                                similar_questions.append(question.id)
            
            related_questions = questions.filter(id__in=similar_questions)
            ids = [i.id for i in related_questions]

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
       
        return(itens) 
            

        