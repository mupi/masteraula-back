from __future__ import absolute_import, unicode_literals
from whoosh.index import LockError
from celery import shared_task

from .search_indexes import QuestionIndex, LearningObjectIndex, ActivityIndex, ClassPlanPublicationIndex
from .models import Question, LearningObject, Activity, ClassPlanPublication
from django.db import connection

def update_or_remove_question(question):
    if question.disabled:
        QuestionIndex().remove_object(instance=question)
    else:
        QuestionIndex().update_object(instance=question)

@shared_task(name="update_question_index", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_question_index(question):
    try:
        question = Question.objects.get_questions_update_index().get(id=question)
    except:
        return
    update_or_remove_question(question)
    
@shared_task(name="update_learning_object_index", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_learning_object_index(learningObject):
    try:
        lo = LearningObject.objects.get_objects_update_index().get(id=learningObject)
    except:
        return
    LearningObjectIndex().update_object(instance=lo)
    for question in lo.questions.all():
        update_or_remove_question(question)
    
    for activity in lo.activities.all():
        update_or_remove_activity(activity)

@shared_task(name="update_questions_topic", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_questions_topic(topic):
    questions = Question.objects.get_questions_update_index().filter(topics__id=topic)
    for question in questions:
        update_or_remove_question(question)

def update_or_remove_activity(activity):
    if activity.disabled:
        ActivityIndex().remove_object(instance=activity)
    else:
        ActivityIndex().update_object(instance=activity)

@shared_task(name="update_activity_index", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_activity_index(activity):
    try:
        activity = Activity.objects.get_activities_update_index().get(id=activity)
    except:
        return
    update_or_remove_activity(activity)

@shared_task(name="update_activities_topic", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_activities_topic(topic):
    activities = Activity.objects.get_activities_update_index().filter(topics__id=topic)
    for activity in activities:
        update_or_remove_activity(activity)
    
def update_or_remove_class_plan(class_plan):
    if class_plan.disabled:
        ClassPlanPublicationIndex().remove_object(instance=class_plan)
    else:
       ClassPlanPublicationIndex().update_object(instance=class_plan)

@shared_task(name="update_class_plan_index", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_class_plan_index(class_plan):
    try:
        class_plan = ClassPlanPublication.objects.get_class_plans_update_index().get(id=class_plan)
        
    except:
        return
    update_or_remove_class_plan(class_plan)

@shared_task(name="update_class_plan_topic", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_class_plan_topic(topic):
    class_plans = ClassPlanPublication.objects.get_class_plans_update_index().filter(topics__id=topic)
    for class_plan in class_plans:
        update_or_remove_class_plan(class_plan) 