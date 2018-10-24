from django.core.management.base import BaseCommand, CommandError
from masteraula.questions.models import Question
# from masteraula.questions.search_indexes import QuestionIndex, TagIndex
import re
import requests
import json

from threading import Thread

class Command(BaseCommand):
    help = 'check all the images and output the id with broken images'

    question_broken_images = []
    thread_numbers = 25
    
    def handle(self, *args, **options):

        questions = Question.objects.filter(id__gte=0).order_by('id')

        def threaded_function(arg):
            for question in questions:
                if question.id % self.thread_numbers == arg:
                    for alternative in question.alternatives.all():                                    
                        results = re.findall('(<img(.)*?src=\"(.*?)\"(.)*?>)', alternative.text)
                        
                        for result in results:
                            print('Testing... ' + result[2])
                            try:
                                r = requests.head(result[2])
                                if not r.ok:
                                    self.question_broken_images.append((question.id, result[2]))
                                    print('Error')
                                else:
                                    print('Ok')
                            except:
                                self.question_broken_images.append((question.id, result[2]))
                                print('Error')

        threads = []
        for i in range(self.thread_numbers):
            threads.append(Thread(target = threaded_function, args = [i]))
            threads[i].start()

        for i in range(self.thread_numbers):
            threads[i].join()

        print(json.dumps(self.question_broken_images))
        print("Finish")
