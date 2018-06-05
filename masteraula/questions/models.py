# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _

from taggit.managers import TaggableManager

from masteraula.users.models import User

class Subject(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name


class EducationLevel(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name

class LearningObject(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    image = models.ImageField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    tags = TaggableManager()

    def __str__(self):
        return self.name


class Describer(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name + " " + description[:50]


class Question(models.Model):
    LEVEL_CHOICES = (
        ('', 'Nenhuma opção'),
        ('E', _('Easy')),
        ('M', _('Medium')),
        ('H', _('Hard'))
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

    statement = models.TextField()
    learning_object = models.ForeignKey(LearningObject, null=True, blank=True)
    resolution = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=1, choices = LEVEL_CHOICES, null=True, blank=True)

    subjects = models.ManyToManyField(Subject, blank=True)
    education_level = models.ForeignKey(EducationLevel, blank=True, null=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)

    credit_cost = models.PositiveIntegerField(null=False, blank=True, default=0)

    tags = TaggableManager()

    def __str__(self):
        return self.question_statement[:75]


class Alternative(models.Model):
    question = models.ForeignKey(Question, related_name='alternatives', on_delete=models.CASCADE)
    answer_text = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        ordering = ['question', 'pk']

    def __str__(self):
        return self.answer_text[:50]

class Document(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, through='DocumentQuestion', related_name='questions')
    create_date = models.DateTimeField(auto_now_add=True)
    secret = models.BooleanField()

    def __str__(self):
        return self.name[:50]


class DocumentQuestion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(null=False, blank=False)

    class Meta:
        ordering = ['document', 'order']

    def __str__(self):
        return self.question_list_header[:50]


class DocumentHeader(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=200)
    subject_name = models.CharField(max_length=50)
    professor_name = models.CharField(max_length=200)
    student_indicator = models.BooleanField()
    class_indicator = models.BooleanField()
    score_indicator = models.BooleanField()
    date_indicator = models.BooleanField()
