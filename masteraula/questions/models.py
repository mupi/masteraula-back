# -*- coding: utf-8 -*-
import datetime
import uuid
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField

from taggit.managers import TaggableManager

from masteraula.users.models import User

from .managers import TopicManager

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

    objects = TopicManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.name)

class Descriptor(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name + " " + self.description[:50]

class QuestionManager(models.Manager):
    # Hardcoded because we know the total depth of the topics tree
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    def get_questions_prefetched(self, topics=True):
        qs = self.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            'learning_objects', 'learning_objects__tags', 'learning_objects__owner', 
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs

    def get_questions_update_index(self, topics=True):
        qs = self.all().select_related('author').prefetch_related(
            'tags', 'alternatives', 'disciplines', 'teaching_levels', 'learning_objects', 'learning_objects__tags', 
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs
    

class Question(models.Model):
    LEVEL_CHOICES = (
        ('', _('None')),
        ('E', _('Easy')),
        ('M', _('Medium')),
        ('H', _('Hard'))
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    authorship = models.CharField(max_length=255, null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    statement = models.TextField()
    learning_objects = models.ManyToManyField('LearningObject', related_name='questions', blank=True)
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
    disabled = models.BooleanField(null=False, blank=True, default=False)
    objects = QuestionManager()

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

class LearningObjectManager(models.Manager):

    def get_objects_update_index(self):
        return self.all().select_related('owner').prefetch_related(
            'tags', Prefetch('questions', queryset=Question.objects.get_questions_update_index(False))
        )

class LearningObject(models.Model):
    TYPE_CHOICES = (
        ('I', _('Image')),
        ('T', _('Text')),
        ('A', _('Audio')),
        ('V', _('Video')),
    )

    def get_upload_file_name(learning_object,filename):
        folder_name = learning_object.folder_name if learning_object.folder_name else 'default'
        return u'masteraula/%s/%s' % (folder_name, filename)

    # name = models.CharField(max_length=100, null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    source = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=get_upload_file_name)
    folder_name = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    object_types = ArrayField(
        models.CharField(max_length=1, choices = TYPE_CHOICES, blank=True)
    )

    tags = TaggableManager(blank=True)

    objects = LearningObjectManager()

    def update(self, **kwargs):
        allowed_attributes = {'owner', 'source', 'image', 'text', 'tags'}
        for name, value in kwargs.items():
            assert name in allowed_attributes
            setattr(self, name, value)
        self.save()

class Alternative(models.Model):
    question = models.ForeignKey(Question, related_name='alternatives', on_delete=models.CASCADE)
    text = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        ordering = ['question', 'pk']

    def __str__(self):
        return self.text[:50]

class DocumentManager(models.Manager):
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    learning_objects_prefetch = Prefetch('learning_objects',
        queryset=LearningObject.objects.all().select_related('owner').prefetch_related('tags')
    )

    questions_prefetch = Prefetch('documentquestion_set__question',
        queryset=Question.objects.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            topics_prefetch, 
            learning_objects_prefetch
        )
    )

    def get_questions_prefetched(self):
        return self.all().select_related('owner').prefetch_related(
            self.questions_prefetch,
        )

    def get_generate_document(self):
        return self.all().prefetch_related(
            Prefetch('documentquestion_set__question',
                queryset=Question.objects.all().prefetch_related(
                    'alternatives', 'learning_objects'
                )
            ),
        )

class Document(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, through='DocumentQuestion', related_name='questions')
    create_date = models.DateTimeField(auto_now_add=True)
    secret = models.BooleanField()
    disabled = models.BooleanField(null=False, blank=True, default=False)
      
    objects = DocumentManager()

    def __str__(self):
        return self.name[:50]
        
    def set_questions(self, document_questions):
        self.documentquestion_set.all().delete()
        for document_question in document_questions:
            self.documentquestion_set.create(**document_question)
        self.update_orders()
        self.save()

    def add_question(self, question):
        last_learning_object = None

        question = Question.objects.prefetch_related('learning_objects').get(id=question.id)
        qs = self.documentquestion_set.all().select_related('question').prefetch_related('question__learning_objects').order_by('order')
        new_order = len(qs)

        for order, document_question in enumerate(qs):
            if (last_learning_object and last_learning_object != [q.id for q in document_question.question.learning_objects.all()]
                    and last_learning_object == [q.id for q in question.learning_objects.all()]):
                new_order = order
                break

            last_learning_object = [q.id for q in document_question.question.learning_objects.all()]
        document_question = self.documentquestion_set.create(question=question, order=new_order)

        return document_question

    def remove_question(self, question):
        self.documentquestion_set.filter(question=question).delete()
        self.update_orders()

    def update_orders(self):
        added_questions = []
        learning_objects_pos = {}
        qs = self.documentquestion_set.all().select_related('question').prefetch_related('question__learning_objects').order_by('order')

        for document_question in qs:
            if len(document_question.question.learning_objects.all()) == 0:
                added_questions.append([document_question])
            else:
                learning_objects_hash = '-'.join(str(lo.id) for lo in document_question.question.learning_objects.all())
                if learning_objects_hash in learning_objects_pos:
                    added_questions[learning_objects_pos[learning_objects_hash]].append(document_question)
                else:
                    learning_objects_pos[learning_objects_hash] = len(added_questions)
                    added_questions.append([document_question])
                    
        order = 0
        for question_list in added_questions:
            for question in question_list:
                question.order = order
                question.save()
                order += 1

    def update(self, **kwargs):
        # https://www.dabapps.com/blog/django-models-and-encapsulation/
        allowed_attributes = {'name', 'secret', 'disabled'}
        for name, value in kwargs.items():
            assert name in allowed_attributes
            setattr(self, name, value)
        self.save()

class DocumentQuestionManager(models.Manager):

    topics_prefetch = Prefetch('question__topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    learning_objects_prefetch = Prefetch(
        'question__learning_objects',
        queryset=LearningObject.objects.all().select_related('owner').prefetch_related('tags')
    )

    def get_questions_prefetched(self, topics=True):
        qs = self.all().select_related('question').prefetch_related(
            'question__tags', 'question__disciplines', 'question__teaching_levels', 'question__alternatives',
            self.learning_objects_prefetch
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs

    def create(self, *args, **kwargs):
        documentQuestion = super().create(*args, **kwargs)
        documentQuestions = self.filter(document=documentQuestion.document).filter(order__gte=documentQuestion.order)
        for dq in documentQuestions:
            if dq != documentQuestion:
                dq.order = dq.order + 1
                dq.save()

        return documentQuestion


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

class DocumentDownload(models.Model):
    user = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    download_date = models.DateTimeField(auto_now_add=True)
    answers = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

class DocumentPublication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)