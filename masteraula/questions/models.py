# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _

from taggit.managers import TaggableManager

from masteraula.users.models import User

class DocumentQuestionManager(models.Manager):
    def create(self, *args, **kwargs):
        documentQuestion = super().create(*args, **kwargs)
        documentQuestions = super().filter(document=documentQuestion.document).filter(order__gte=documentQuestion.order)
        for dq in documentQuestions:
            if dq != documentQuestion:
                dq.order = dq.order + 1
                dq.save()

        return documentQuestion

class Discipline(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.name

class TeachingLevel(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.name

class Year(models.Model):
    name = models.PositiveIntegerField()

    def __str__(self):
        return str(self.name)

class Source(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return str(self.name)

class Topic(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, null=False, blank=False)
    parent = models.ForeignKey('Topic', related_name='childs', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.name)

class LearningObject(models.Model):
    def get_upload_file_name(learning_object,filename):
        folder_name = learning_object.folder_name if learning_object.folder_name else 'default'
        return u'masteraula/%s/%s' % (folder_name, filename)

    # name = models.CharField(max_length=100, null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    source = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=get_upload_file_name)
    folder_name = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    tags = TaggableManager(blank=True)

    def update(self, **kwargs):
        allowed_attributes = {'owner', 'source', 'image', 'text', 'tags'}
        for name, value in kwargs.items():
            assert name in allowed_attributes
            setattr(self, name, value)
        self.save()

class Descriptor(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name + " " + self.description[:50]


class Question(models.Model):
    LEVEL_CHOICES = (
        ('', _('None')),
        ('E', _('Easy')),
        ('M', _('Medium')),
        ('H', _('Hard'))
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

    statement = models.TextField()
    learning_objects = models.ManyToManyField(LearningObject, blank=True)
    resolution = models.TextField(null=True, blank=True)
    difficulty = models.CharField(max_length=1, choices = LEVEL_CHOICES, null=True, blank=True)

    disciplines = models.ManyToManyField(Discipline, blank=True)
    descriptors = models.ManyToManyField(Descriptor, blank=True)
    teaching_levels = models.ManyToManyField(TeachingLevel, blank=True)
    topics = models.ManyToManyField(Topic, blank=True)

    year = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)

    credit_cost = models.PositiveIntegerField(null=False, blank=True, default=0)

    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.statement[:75]

    def get_all_topics(self):
        topics = []
        new_topics = [t for t in self.topics.all()]
        while new_topics:
            parents_id = [t.parent for t in new_topics if t.parent]
            topics = topics + new_topics
            new_topics = parents_id
        return list(set(topics))

class Alternative(models.Model):
    question = models.ForeignKey(Question, related_name='alternatives', on_delete=models.CASCADE)
    text = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        ordering = ['question', 'pk']

    def __str__(self):
        return self.text[:50]

class Document(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, through='DocumentQuestion', related_name='questions')
    create_date = models.DateTimeField(auto_now_add=True)
    secret = models.BooleanField()
      
    def __str__(self):
        return self.name[:50]
        
    def set_questions(self, document_questions):
        self.documentquestion_set.all().delete()
        for document_question in document_questions:
            self.documentquestion_set.create(**document_question)
        self.update_orders()
        self.save()

    def add_question(self, question):
        order = 0
        new_order = self.documentquestion_set.count()
        last_learning_object = None
        for order, documentQuestion in enumerate(self.documentquestion_set.all().order_by('order')):
            if (last_learning_object and last_learning_object != [q for q  in documentQuestion.question.learning_objects.values()]
                    and last_learning_object == [q for q in question.learning_objects.values()]):
                new_order = order
                break

            last_learning_object = [q for q  in documentQuestion.question.learning_objects.values()]
        documentQuestion = self.documentquestion_set.create(question=question, order=new_order)
        self.save()
        return documentQuestion

    def remove_question(self, question):
        self.documentquestion_set.filter(question=question).delete()
        self.save()
        self.update_orders()

    def update_orders(self):
        added_questions = []
        documentQuestions = self.documentquestion_set.all().order_by('order')

        order = 0
        for i, documentQuestion in enumerate(documentQuestions):
            # Added questions
            if i in added_questions:
                continue
            
            documentQuestion.set_order(order)
            order = order + 1

            # unify the questions with same learning object
            learning_objects = [q for q  in documentQuestion.question.learning_objects.values()]
            if learning_objects:
                for j in range(i, len(documentQuestions)):
                    if j in added_questions:
                        continue
                    if learning_objects == [q for q  in documentQuestions[j].question.learning_objects.values()]:
                        added_questions.append(j)
                        documentQuestions[j].set_order(order)
                        order = order + 1

    def update(self, **kwargs):
        # https://www.dabapps.com/blog/django-models-and-encapsulation/
        allowed_attributes = {'name', 'secret'}
        for name, value in kwargs.items():
            assert name in allowed_attributes
            setattr(self, name, value)
        self.save()

class DocumentQuestion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(null=False, blank=False)

    objects = DocumentQuestionManager()

    class Meta:
        ordering = ['document', 'order']

    def set_order(self, order):
        self.order = order
        self.save()

class Header(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE) 
    institution_name = models.CharField(max_length=200, blank=True, null=True)
    discipline_name = models.CharField(max_length=50, blank=True, null=True)
    professor_name = models.CharField(max_length=200, blank=True, null=True)
    student_indicator = models.BooleanField(default=False, blank=True)
    class_indicator = models.BooleanField(default=False, blank=True)
    score_indicator = models.BooleanField(default=False, blank=True)
    date_indicator = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.name[:50]

    def update(self, **kwargs):
        allowed_attributes = {'name', 'institution_name', 'discipline_name', 'professor_name', 'student_indicator', 'class_indicator',
        'score_indicator', 'date_indicator'}
        for name, value in kwargs.items():
            assert name in allowed_attributes
            setattr(self, name, value)
        self.save()

class Search(models.Model):
   
    term = models.CharField(max_length=100, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE) 

    disciplines = models.ManyToManyField(Discipline, blank=True)
    teaching_levels = models.ManyToManyField(TeachingLevel, blank=True)
    difficulty = models.CharField(max_length=20, null=True, blank=True)
    source = models.CharField(max_length=150, null=True, blank=True)
    year = models.CharField(max_length=100, null=True, blank=True)
    date_search = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Search"
        verbose_name_plural = "Searches"