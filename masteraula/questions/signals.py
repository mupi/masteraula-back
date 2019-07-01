# -*- coding: utf-8 -*-
from taggit.models import Tag, TaggedItemBase
from .models import Question, LearningObject, Topic
from django.db.models.signals import post_save, m2m_changed, post_delete
from django.dispatch import receiver
from .search_indexes import QuestionIndex, LearningObjectIndex

@receiver(m2m_changed, sender=Question.tags.through)
def m2m_tags_changed(sender, instance, action, reverse, **kwargs):
    if action == 'post_add' or action == 'post_remove':
        if type(instance) == Question:
            q = Question.objects.get(id=instance.id)
            QuestionIndex().update_object(instance=q)

        elif type(instance) == LearningObject:
            lo =  LearningObject.objects.get(id=instance.id)
            for q in lo.question_set.all():
                QuestionIndex().update_object(instance=q)

@receiver(m2m_changed, sender=Question.learning_objects.through)
def m2m_learning_object_changed(sender, instance, action, reverse, **kwargs):
    if action == 'post_add' or action == 'post_remove':
        q = Question.objects.get(id=instance.id)
        QuestionIndex().update_object(instance=q)

@receiver(m2m_changed, sender=Question.topics.through)
def m2m_topic_changed(sender, instance, action, reverse, **kwargs):
    if action == 'post_add' or action == 'post_remove':
        q = Question.objects.get(id=instance.id)
        QuestionIndex().update_object(instance=q)

@receiver(post_save, sender=Question)
def question_post_save(sender, instance, **kwargs):
    q =  Question.objects.get(id=instance.id)
    QuestionIndex().update_object(instance=q)

@receiver(post_save, sender=LearningObject)
def learning_object_post_save(sender, instance, **kwargs):
    lo =  LearningObject.objects.get(id=instance.id)
    LearningObjectIndex().update_object(instance=lo)
    for q in lo.question_set.all():
        QuestionIndex().update_object(instance=q)

@receiver(post_delete, sender=LearningObject)
def learning_object_post_delete(sender, instance, **kwargs):
    LearningObjectIndex().remove_object(instance)

@receiver(post_save, sender=Topic)
def topic_post_save(sender, instance, **kwargs):
    topic =  Topic.objects.get(id=instance.id)
    for q in topic.question_set.all():
        QuestionIndex().update_object(instance=q)