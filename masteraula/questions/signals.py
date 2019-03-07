# -*- coding: utf-8 -*-
from taggit.models import Tag
from .models import Question, LearningObject
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Tag)
def save_tag(sender, instance, **kwargs):
    for tag in instance.taggit_taggeditem_items.all():
        if type(tag.content_object) == Question:
            tag.content_object.save()

        if type(tag.content_object) == LearningObject:
            learning_objects = LearningObject.objects.filter(tags= tag)
            for l in learning_objects:
                questions = Question.objects.filter(learning_objects=l)
                for obj in questions:
                    obj.save() 