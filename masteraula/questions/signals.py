# -*- coding: utf-8 -*-
from taggit.models import Tag, TaggedItemBase
from .models import Question, LearningObject, Topic, Label, Activity, ClassPlanPublication

from ..users.models import User
from django.db.models.signals import post_save, m2m_changed, post_delete, pre_save

from django.dispatch import receiver
from .search_indexes import QuestionIndex, LearningObjectIndex, ActivityIndex, ClassPlanPublicationIndex, TopicIndex
from .tasks import update_question_index, update_learning_object_index, update_questions_topic, update_activities_topic, update_activity_index, update_class_plan_topic, update_class_plan_index

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

@receiver(post_save, sender=User)
def update_label(sender, instance, created, **kwargs):
    if created:
        label = Label.objects.filter(owner=instance, name="Favoritos")
        if not label:
            question = Question.objects.filter(disabled=False).first()
            label1 = Label.objects.create(owner=instance, name="Favoritos", color="#9AEE2E")
            label2 = Label.objects.create(owner=instance, name="Ver Mais Tarde", color="#FC1979")
            question.labels.add(label1, label2)
            question.save()

@receiver(post_save, sender=Question)
def question_post_save(sender, instance, **kwargs):
    update_question_index.apply_async((instance.id,), countdown=5)

@receiver(post_delete, sender=Question)
def question_post_delete(sender, instance, **kwargs):
    QuestionIndex().remove_object(instance)

@receiver(post_save, sender=LearningObject)
def learning_object_post_save(sender, instance, **kwargs):
    update_learning_object_index.apply_async((instance.id,), countdown=5)

@receiver(post_delete, sender=LearningObject)
def learning_object_post_delete(sender, instance, **kwargs):
    LearningObjectIndex().remove_object(instance)

@receiver(post_save, sender=Topic)
def topic_post_save(sender, instance, **kwargs):
    update_questions_topic.apply_async((instance.id,), countdown=5)
    update_activities_topic.apply_async((instance.id,), countdown=5)
    update_class_plan_topic.apply_async((instance.id,), countdown=5)

@receiver(post_save, sender=Topic)
def topic_post_save(sender, instance, **kwargs):
    TopicIndex().update_object(instance)

@receiver(post_delete, sender=Topic)
def topic_post_delete(sender, instance, **kwargs):
   TopicIndex().remove_object(instance)

@receiver(post_save, sender=Activity)
def activity_post_save(sender, instance, **kwargs):
    update_activity_index.apply_async((instance.id,), countdown=5)

@receiver(post_delete, sender=Activity)
def activity_post_delete(sender, instance, **kwargs):
    ActivityIndex().remove_object(instance)

@receiver(post_save, sender=ClassPlanPublication)
def class_plan_post_save(sender, instance, **kwargs):
    update_class_plan_index.apply_async((instance.id,), countdown=5)

@receiver(post_delete, sender=ClassPlanPublication)
def class_plan_post_delete(sender, instance, **kwargs):
    ClassPlanPublicationIndex().remove_object(instance)