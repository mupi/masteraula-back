import warnings

from taggit.models import Tag
from .models import Question, Activity
from django.conf import settings


class RelatedQuestions():

    def similar_questions(self, question, activity=False):
        list_question = []
        questions = Question.objects.filter(topics__in=question.get_all_topics()).order_by('?')
        disciplines = Question.objects.filter(disciplines__in=question.disciplines.all()).exclude(id__in=questions).order_by('?')

        if activity == False:
            questions = questions.exclude(id=question.id)
            disciplines = disciplines.exclude(id=question.id)

        if not questions:
            questions = disciplines[:8]

        else:
            if len(questions) >= 8:
                questions = questions[:8]

            else:
                questions = questions[:len(questions)]
                questions += disciplines[:8]

        # Get activities similar
        activities = Activity.objects.filter(topics__in=question.get_all_topics()).order_by('?')
        print("TEste aqui", len(activities))
        disciplines_act = Activity.objects.filter(disciplines__in=question.disciplines.all()).exclude(id__in=activities).order_by('?')
        list_activity = []

        if activity == True:
            activities = activities.exclude(id=question.id)
            disciplines_act = disciplines_act.exclude(id=question.id)
        
        if not activities:
            activities = disciplines_act[:8]

        else:
            if len(activities) >= 8:
                activities = activities[:8]

            else:
                activities = activities[:len(activities)]
                activities += disciplines_act[:8]

        for item in activities[:4]:
            list_activity.append(item.id)

        if len(activities) < 4:
            questions = questions[:(8 - len(activities))]
        else:
            questions = questions[:4]

        for item in questions:
            list_question.append(item.id)

        return list_question, list_activity
