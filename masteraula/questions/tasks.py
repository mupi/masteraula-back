from __future__ import absolute_import, unicode_literals
from whoosh.index import LockError
from celery import shared_task

from .search_indexes import QuestionIndex, LearningObjectIndex
from .models import Question, LearningObject
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

@shared_task(name="update_questions_topic", autoretry_for=(LockError,),
    retry_kwargs={'max_retries': 8}, retry_backoff=True)
def update_questions_topic(topic):
    questions = Question.objects.get_questions_update_index().filter(topics__id=topic)
    for question in questions:
        update_or_remove_question(question)