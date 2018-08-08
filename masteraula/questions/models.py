# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _

from taggit.managers import TaggableManager

from masteraula.users.models import User

class Discipline(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name


class TeachingLevel(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name

class LearningObject(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    image = models.ImageField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.name


class Descriptor(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name + " " + self.description[:50]


class Question(models.Model):
    LEVEL_CHOICES = (
        ('', 'Nenhuma opção'),
        ('E', _('Easy')),
        ('M', _('Medium')),
        ('H', _('Hard'))
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateField(auto_now_add=True)

    statement = models.TextField()
    learning_object = models.ForeignKey(LearningObject, null=True, blank=True)
    resolution = models.TextField(null=True, blank=True)
    difficulty = models.CharField(max_length=1, choices = LEVEL_CHOICES, null=True, blank=True)

    disciplines = models.ManyToManyField(Discipline, blank=True)
    descriptors = models.ManyToManyField(Descriptor, blank=True)
    teaching_levels = models.ManyToManyField(TeachingLevel, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)

    credit_cost = models.PositiveIntegerField(null=False, blank=True, default=0)

    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.statement[:75]


class Alternative(models.Model):
    question = models.ForeignKey(Question, related_name='alternatives', on_delete=models.CASCADE)
    text = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        ordering = ['question', 'pk']

    def __str__(self):
        return self.text[:50]

class DocumentHeader(models.Model):
    owner = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    institution_name = models.CharField(max_length=200)
    discipline_name = models.CharField(max_length=50)
    professor_name = models.CharField(max_length=200)
    student_indicator = models.BooleanField()
    class_indicator = models.BooleanField()
    score_indicator = models.BooleanField()
    date_indicator = models.BooleanField()

    def __str__(self):
        if self.owner != None:
            return self.owner.name + " " + self.institution_name + " " + self.discipline_name
        return self.institution_name + " " + self.discipline_name

class Document(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, through='DocumentQuestion', related_name='questions')
    create_date = models.DateField(auto_now_add=True)
    secret = models.BooleanField()
    document_header = models.ForeignKey(DocumentHeader, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name[:50]

    def set_owner(self, owner):
        self.owner = owner
        self.save()

    def set_questions(self, document_questions):
        self.documentquestion_set.all().delete()
        for document_question in document_questions:
            self.documentquestion_set.create(**document_question)
        self.save()

    def add_question(self, question):
        question_qty = self.documentquestion_set.count()
        self.documentquestion_set.create(question=question, order=question_qty)
        self.update_orders()
        self.save()

    def remove_question(self, question):
        self.documentquestion_set.filter(question=question).delete()
        self.save()
        self.update_orders()

    def update_orders(self):
        documentQuestions = self.documentquestion_set.all().order_by('order')
        for order, documentQuestion in enumerate(documentQuestions):
            documentQuestion.set_order(order)

    def update(self, **kwargs):
        # https://www.dabapps.com/blog/django-models-and-encapsulation/
        allowed_attributes = {'name', 'secret', 'document_header'}
        for name, value in kwargs.items():
            assert name in allowed_attributes
            setattr(self, name, value)
        self.save()

class DocumentQuestion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(null=False, blank=False)

        
    class Meta:
        ordering = ['document', 'order']

    def set_order(self, order):
        self.order = order
        self.save()
