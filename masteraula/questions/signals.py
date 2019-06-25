# -*- coding: utf-8 -*-
from taggit.models import Tag, TaggedItemBase
from .models import Question, LearningObject, Topic
from ..users.models import User
from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from .search_indexes import QuestionIndex

@receiver(pre_save, sender=User)
def update_username_same_email(sender, instance, **kwargs):
    instance.username = instance.email

@receiver(pre_save, sender=User)
def update_fullname_same_first_second(sender, instance, **kwargs):
    if not instance.name:
        instance.name = instance.get_full_name()
    else:
        names = instance.name.split()
        instance.first_name = names[0]
        instance.last_name = ' '.join(names[1:])

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
    for q in lo.question_set.all():
        QuestionIndex().update_object(instance=q)

@receiver(post_save, sender=Topic)
def topic_post_save(sender, instance, **kwargs):
    topic =  Topic.objects.get(id=instance.id)
    for q in topic.question_set.all():
        QuestionIndex().update_object(instance=q)