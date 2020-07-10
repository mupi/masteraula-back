from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question, Label
from masteraula.users.models import User

from django.apps import apps

"""
 Add default question.
"""

class Command(BaseCommand):
    help = ("./manage.py add_label")
    
    def handle(self, *app_labels, **options):
        users = User.objects.all()
        question = Question.objects.filter(disabled=False).first()

        for u in users: 
            label1 = Label.objects.filter(owner=u, name="Favoritos")
            label2 = Label.objects.filter(owner=u, name="Ver Mais Tarde")

            if not label1:
                label1 = Label.objects.create(owner=u, name="Favoritos", color="#9AEE2E")
                question.labels.add(label1)
            
            if not label2:
                label2 = Label.objects.create(owner=u, name="Ver Mais Tarde", color="#FC1979")
                question.labels.add(label2)

            print("Criando a label para o usuário :" + str(u.id))
            question.save()
        
        print("Etiquetas criadas. Fim!")
