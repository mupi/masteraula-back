# -*- coding: utf-8 -*-
import datetime
import uuid
import operator
import magic

from django.db import models
from django.db.models import Prefetch, Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError

from functools import reduce

from taggit.managers import TaggableManager

from masteraula.users.models import User

from .managers import TopicManager

class Discipline(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-name']

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

class Label(models.Model):
    COLORS_CHOICES = (
        ('', _('None')),
        ('#FFFF33', _('Yellow')),
        ('#A849F7', _('Purple')),
        ('#F9442E', _('Red')),
        ('#BABEBF', _('Grey')),
        ('#050505', _('Black')),
        ('#FC1979', _('Pink')),
        ('#FC7320', _('Orange')),
        ('#82C2FB', _('Blue')),
        ('#9AEE2E', _('Light Green')),
        ('#569505', _('Dark Green'))
    )

    name = models.CharField(max_length=50, null=False, blank=False)
    color = models.CharField(max_length=7, choices = COLORS_CHOICES, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)

    def add_question(self, question):
        self.question_set.add(question)
        return Label.question_set.through.objects.get(question=question, label=self)

    def remove_question(self, question):
        self.question_set.remove(question.id)
    
    def add_activity(self, activity):
        self.activity_set.add(activity)
        return Label.activity_set.through.objects.get(activity=activity, label=self)

    def remove_activity(self, activity):
        self.activity_set.remove(activity.id)

class SynonymManager(models.Manager):
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    def get_topics_prefetched(self, topics=True):
        qs = self.all().prefetch_related(self.topics_prefetch)
        return qs

class Synonym(models.Model):
    term =  models.CharField(max_length=100, null=False, blank=False)
    topics = models.ManyToManyField(Topic)

    objects = SynonymManager()

    def __str__(self):
        return str(self.term)

class Descriptor(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name + " " + self.description[:50]

class QuestionManager(models.Manager):
    # Hardcoded because we know the total depth of the topics tree
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.prefetch_related('synonym_set').select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    labels_prefetch = Prefetch('labels', queryset=Label.objects.prefetch_related('question_set').select_related(
        'owner'
    ))

    def get_questions_prefetched(self, topics=True):
        from django.apps import apps

        LearningObject = apps.get_model('questions', 'LearningObject')
        learning_object_prefetch = Prefetch('learning_objects', queryset=LearningObject.objects.select_related('owner').prefetch_related(
            'tags', 'questions'
        ))

        qs = self.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            self.labels_prefetch, learning_object_prefetch
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs

    def get_questions_update_index(self, topics=True):
        qs = self.all().select_related('author').prefetch_related(
            'tags', 'alternatives', 'disciplines', 'teaching_levels', 'learning_objects', 'learning_objects__tags', 'labels',
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs

    def filter_questions_request(self, query_params):
        queryset = self.get_questions_prefetched()
        
        disciplines = query_params.getlist('disciplines', None)
        teaching_levels = query_params.getlist('teaching_levels', None)
        difficulties = query_params.getlist('difficulties', None)
        years = query_params.getlist('years', None)
        sources = query_params.getlist('sources', None)
        author = query_params.get('author', None)
        topics = query_params.getlist('topics', None)
        labels = query_params.getlist('labels', None)
       
        if disciplines:
            queryset = queryset.filter(disciplines__in=disciplines)
        if teaching_levels:
            queryset = queryset.filter(teaching_levels__in=teaching_levels)
        if difficulties:
            queryset = queryset.filter(difficulty__in=difficulties)
        if years:
            queryset = queryset.filter(year__in=years)
        if sources:
            query = reduce(operator.or_, (Q(source__contains = source) for source in sources))
            queryset = queryset.filter(query)
        if author:
            queryset = queryset.filter(author__id=author)
        if topics:
            for topic in topics:
                queryset = queryset.filter(topics__id=topic)
        if labels:
            queryset = queryset.filter(labels__in=labels)
        
        if not author:
            queryset = queryset.filter(secret=False)
        
        queryset = queryset.distinct()
        return queryset

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
    labels = models.ManyToManyField(Label, blank=True)

    year = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)

    credit_cost = models.PositiveIntegerField(null=False, blank=True, default=0)

    tags = TaggableManager(blank=True)
    disabled = models.BooleanField(null=False, blank=True, default=False)
    secret = models.BooleanField(null=False, blank=True, default=False)

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
    disabled = models.BooleanField(null=False, blank=True, default=False)

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
        queryset=LearningObject.objects.all().select_related('owner').prefetch_related('tags', 'questions')
    )

    labels_prefetch = Prefetch('labels', queryset=Label.objects.prefetch_related('question_set').select_related(
        'owner'
    ))

    questions_prefetch = Prefetch('documentquestion_set__question',
        queryset=Question.objects.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            topics_prefetch, 
            learning_objects_prefetch,
            labels_prefetch
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

class DocumentLimitExceedException(Exception):
    pass

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
        if self.questions.count() >= 30:
            raise DocumentLimitExceedException('Documentos não pode ter mais de 30 questões.')
        if not self.owner.premium() and self.questions.count() >= 10:
            raise DocumentLimitExceedException('Documentos não pode ter mais de 10 questões. Para aumentar o número de questões, atualize seu plano gratuito para Premium.')
        
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
    term = models.TextField(null=False, blank=False)
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

class TeachingYear(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return str(self.name)

class Station(models.Model):
    description_station = models.TextField(null=False, blank=False)

    learning_object = models.ForeignKey(LearningObject, related_name='station_obj', null=True, blank=True)
    document = models.ForeignKey(Document, related_name='station_doc', null=True, blank=True)
    question = models.ForeignKey(Question, related_name='station_question', null=True, blank=True)

    plan = models.ForeignKey('ClassPlan', related_name='stations', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.description_station)

class ClassPlan(models.Model):

    TYPE_PLAN = (
            ('T', _('Traditional')),
            ('S', _('Station')),
        )

    def validate_pdf(fileobj):
        max_size = 2*(1024 * 1024)
        if fileobj.size > max_size:
            raise ValidationError(_('Max file size is 2MB'))

        filetype = magic.from_buffer(fileobj.read())
        if not "PDF" in filetype:
            raise ValidationError("File is not PDF.")


    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200)

    disciplines = models.ManyToManyField(Discipline, blank=True)
    teaching_levels = models.ManyToManyField(TeachingLevel, blank=True)
    topics = models.ManyToManyField(Topic, blank=True)
    learning_objects = models.ManyToManyField('LearningObject', related_name='plans_obj', blank=True)
    documents = models.ManyToManyField(Document, related_name='plans_doc', blank=True)
    teaching_years = models.ManyToManyField(TeachingYear, blank=True)

    duration = models.PositiveIntegerField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    pdf = models.FileField(null=True, blank=True, upload_to='documents_pdf', validators=[validate_pdf])
    disabled = models.BooleanField(null=False, blank=True, default=False)
    plan_type = models.CharField(max_length=1, choices = TYPE_PLAN, null=True, blank=True)

    def __str__(self):
        return str(self.name)

class Link(models.Model):
    link = models.TextField(max_length=2083, null=False, blank=False)
    description_url = models.TextField(null=True, blank=True)
    plan = models.ForeignKey(ClassPlan, related_name='links', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.link)

class FaqCategory(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    description_category = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.description_category)

    class Meta:
        verbose_name = "Faq Category"
        verbose_name_plural = "FAQ categories"

class FaqQuestion(models.Model):
    faq_question = models.TextField()
    faq_answer = models.TextField()
    category = models.ForeignKey(FaqCategory, related_name='category_questions', on_delete=models.CASCADE, null=True, blank=True)

class StudentAnswer(models.Model):
    answer_alternative =  models.ForeignKey(Alternative, on_delete=models.CASCADE, null=True, blank=True)
    answer_text = models.TextField(null=True, blank=True)
    score_answer = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    student_answer = models.ForeignKey('Result', related_name='student_answer', on_delete=models.CASCADE, null=True, blank=True)
    student_question = models.ForeignKey('DocumentQuestionOnline', related_name='student_question', on_delete=models.CASCADE)

    class Meta:   
        ordering = ['student_question']


class ResultManager(models.Manager):
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    learning_objects_prefetch = Prefetch('learning_objects',
        queryset=LearningObject.objects.all().select_related('owner').prefetch_related('tags', 'questions')
    )

    labels_prefetch = Prefetch('labels', queryset=Label.objects.prefetch_related('question_set').select_related(
        'owner'
    ))

    student_question_prefetch = Prefetch('student_question__question',
        queryset=Question.objects.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            topics_prefetch, 
            learning_objects_prefetch,
            labels_prefetch
        )
    )

    student_answer_prefetch = Prefetch('student_answer', queryset=StudentAnswer.objects.all().prefetch_related('answer_alternative', student_question_prefetch))

    def get_result_prefetch(self):
        qs = self.all().select_related('results').prefetch_related(self.student_answer_prefetch)
        return qs

class Result(models.Model):
    results = models.ForeignKey('DocumentOnline', related_name='results', on_delete=models.CASCADE, verbose_name="document")
    student_name = models.CharField(max_length=200)
    student_levels = models.CharField(max_length=200)
    start = models.DateTimeField()
    finish = models.DateTimeField()

    objects = ResultManager()

class DocumentOnlineManager(models.Manager):

    topics_prefetch = Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    learning_objects_prefetch = Prefetch('learning_objects',
        queryset=LearningObject.objects.all().select_related('owner').prefetch_related('tags', 'questions')
    )

    labels_prefetch = Prefetch('labels', queryset=Label.objects.prefetch_related('question_set').select_related(
        'owner'
    ))

    questions_prefetch = Prefetch('documentquestiononline_set__question',
        queryset=Question.objects.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            topics_prefetch, 
            learning_objects_prefetch,
            labels_prefetch
        )
    )

    student_question_prefetch = Prefetch('student_question__question',
        queryset=Question.objects.all().select_related('author').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'alternatives',
            topics_prefetch, 
            learning_objects_prefetch,
            labels_prefetch
        )
    )

    student_answer_prefetch = Prefetch('student_answer', queryset=StudentAnswer.objects.all().prefetch_related('answer_alternative', student_question_prefetch))
  
    results_prefetch = Prefetch('results',
        queryset=Result.objects.all().prefetch_related(student_answer_prefetch)
    )

    def get_documentonline_prefetch(self):
        qs = self.all().select_related('owner', 'document').prefetch_related(self.questions_prefetch, self.results_prefetch)
        return qs
       
class DocumentOnline(models.Model):
    link = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, related_name='document_document_online', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    finish_date = models.DateTimeField()
    duration = models.PositiveIntegerField(null=True, blank=True)
    questions_document = models.ManyToManyField(Question, through='DocumentQuestionOnline', related_name='questions_document')
    disabled = models.BooleanField(null=False, blank=True, default=False)

    objects = DocumentOnlineManager()

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Document Online"
        verbose_name_plural = "Documents Online"

class DocumentQuestionOnlineManager(models.Manager):
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
    
class DocumentQuestionOnline(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    document = models.ForeignKey(DocumentOnline, on_delete=models.CASCADE)
    score = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    order = models.PositiveIntegerField(null=True, blank=True)

    objects = DocumentQuestionOnlineManager()

    def __str__(self):
        return str(self.pk)
    
    class Meta:
        verbose_name = "Document Question Online"
        verbose_name_plural = "Document Question Online"
   
        ordering = ['order']

class ActivityManager(models.Manager):
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.prefetch_related('synonym_set').select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    labels_prefetch = Prefetch('labels', queryset=Label.objects.prefetch_related('question_set').select_related(
        'owner'
    ))

    def get_activities_prefetched(self, topics=True):
        learning_object_prefetch = Prefetch('learning_objects', queryset=LearningObject.objects.select_related('owner').prefetch_related(
            'tags', 'questions'
        ))

        qs = self.all().select_related('owner').prefetch_related(
            'tags', 'disciplines', 'teaching_levels', 'tasks',
            self.labels_prefetch, learning_object_prefetch
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs

    def get_activities_update_index(self, topics=True):
        qs = self.all().select_related('owner').prefetch_related(
            'tags', 'tasks', 'disciplines', 'teaching_levels', 'learning_objects', 'learning_objects__tags', 'labels',
        )
        if topics:
            qs = qs.prefetch_related(self.topics_prefetch)
        return qs
    
    def filter_activities_request(self, query_params):
        queryset = self.get_activities_prefetched()
        
        disciplines = query_params.getlist('disciplines', None)
        teaching_levels = query_params.getlist('teaching_levels', None)
        difficulties = query_params.getlist('difficulties', None)
        owner = query_params.get('author', None)
        topics = query_params.getlist('topics', None)
        years = query_params.get('years', None)
        
        if disciplines:
            queryset = queryset.filter(disciplines__in=disciplines)
        if teaching_levels:
            queryset = queryset.filter(teaching_levels__in=teaching_levels)
        if difficulties:
            queryset = queryset.filter(difficulty__in=difficulties)
        if owner:
            queryset = queryset.filter(owner__id=owner)
        if topics:
            for topic in topics:
                queryset = queryset.filter(topics__id=topic)
        if years:
            queryset = queryset.filter(create_date__year=int(years))
        
        if not owner:
            queryset = queryset.filter(secret=False)
        queryset = queryset.distinct()
        return queryset

class Activity(models.Model):
    LEVEL_CHOICES = (
        ('', _('None')),
        ('E', _('Easy')),
        ('M', _('Medium')),
        ('H', _('Hard'))
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    learning_objects = models.ManyToManyField(LearningObject, related_name='activities', blank=True)
    difficulty = models.CharField(max_length=1, choices = LEVEL_CHOICES, null=True, blank=True)
    disciplines = models.ManyToManyField(Discipline, blank=True)
    teaching_levels = models.ManyToManyField(TeachingLevel, blank=True)
    topics = models.ManyToManyField(Topic, blank=True)
    tags = TaggableManager(blank=True)
    labels = models.ManyToManyField(Label, blank=True)

    disabled = models.BooleanField(null=False, blank=True, default=False)
    secret = models.BooleanField(null=False, blank=True, default=False)

    objects = ActivityManager()

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
    
    def __str__(self):
        return str(self.id)

    def get_all_topics(self):
        topics = []
        new_topics = [t for t in self.topics.all()]
        while new_topics:
            parents_id = [t.parent for t in new_topics if t.parent]
            topics = topics + new_topics
            new_topics = parents_id
        return list(set(topics))

class Task(models.Model):
    description_task = models.TextField()
    student_expectation = models.TextField()
    teacher_expectation = models.TextField(null=True, blank=True)
   
    activity = models.ForeignKey(Activity, related_name='tasks', on_delete=models.CASCADE)

class Bncc(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    
    class Meta:
        verbose_name = "Bncc"
        verbose_name_plural = "BNCC"

    def __str__(self):
        return str(self.name)

class StationMaterial(models.Model):
    name_station = models.CharField(max_length=100, null=False, blank=False)
    description_station = models.TextField(null=False, blank=False)

    document = models.ForeignKey(Document, related_name='plan_station_doc', null=True, blank=True)
    document_online = models.ForeignKey(DocumentOnline, related_name='plan_station_doc_online', null=True, blank=True)
    activity = models.ForeignKey(Activity, related_name='plan_station_activity', null=True, blank=True)

    plan = models.ForeignKey('ClassPlanPublication', related_name='stations', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.description_station)

class ClassPlanPublication(models.Manager):
    topics_prefetch = Prefetch('topics', queryset=Topic.objects.prefetch_related('synonym_set').select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')
    )

    documents_prefetch = Prefetch(
        'documents',
        queryset=Document.objects.all().select_related('owner').prefetch_related('questions')
    )

    documents_online_prefetch = Prefetch(
        'documents_online',
        queryset=DocumentOnline.objects.all().select_related('owner').prefetch_related('questions_document')
    )

    stations_prefetch = Prefetch(
        'stations',
        queryset=StationMaterial.objects.all().select_related('plan').prefetch_related('activity', 'document', 'document_online')
    )

    activities_prefetch = Prefetch(
        'activities',
        queryset=Activity.objects.all().select_related('owner').prefetch_related('tags', 'disciplines', 'teaching_levels', 'tasks', 'learning_objects')
    )

    def get_classplan_prefetched(self):
        qs = self.all().select_related('owner').prefetch_related(
            'disciplines', 'teaching_levels', 'tags', 'bncc', 'teaching_years', self.topics_prefetch, self.documents_prefetch, self.stations_prefetch, self.documents_online_prefetch, self.activities_prefetch
        )
        return qs
    
    def get_class_plans_update_index(self, topics=True):
        qs = self.all().select_related('owner').prefetch_related(
            'disciplines', 'teaching_levels', 'tags', 'bncc', 'teaching_years', self.topics_prefetch, self.documents_prefetch, self.stations_prefetch, self.documents_online_prefetch, self.activities_prefetch
        )
        return qs
    
    def filter_class_plans_request(self, query_params):
        queryset = self.get_classplan_prefetched()
        
        disciplines = query_params.getlist('disciplines', None)
        teaching_levels = query_params.getlist('teaching_levels', None)
        owner = query_params.get('author', None)
        topics = query_params.getlist('topics', None)
        years = query_params.get('years', None)
        
        if disciplines:
            queryset = queryset.filter(disciplines__in=disciplines)
        if teaching_levels:
            queryset = queryset.filter(teaching_levels__in=teaching_levels)
        if owner:
            queryset = queryset.filter(owner__id=owner)
        if topics:
            for topic in topics:
                queryset = queryset.filter(topics__id=topic)
        if years:
            queryset = queryset.filter(create_date__year=int(years))
        if not owner:
            queryset = queryset.filter(secret=False)
        
        queryset = queryset.distinct()
        return queryset
   

class ClassPlanPublication(models.Model):
    TYPE_PLAN = (
            ('T', _('Traditional')),
            ('S', _('Station')),
        )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200)

    disciplines = models.ManyToManyField(Discipline, blank=True)
    teaching_levels = models.ManyToManyField(TeachingLevel, blank=True)
    topics = models.ManyToManyField(Topic, blank=True)
    tags = TaggableManager(blank=True)
    bncc = models.ManyToManyField(Bncc, blank=True)
    teaching_years = models.ManyToManyField(TeachingYear, blank=True)
    
    documents = models.ManyToManyField(Document, related_name='class_plans_doc', blank=True)
    documents_online = models.ManyToManyField(DocumentOnline, related_name='class_plans_doc_online', blank=True)
    activities = models.ManyToManyField(Activity, related_name='class_plans_act', blank=True)
    
    duration = models.PositiveIntegerField(null=True, blank=True)
    phases = models.TextField()
    content = models.TextField(null=True, blank=True)
    guidelines = models.TextField(null=True, blank=True)

    disabled = models.BooleanField(null=False, blank=True, default=False)
    plan_type = models.CharField(max_length=1, choices = TYPE_PLAN, null=True, blank=True)
    secret = models.BooleanField(null=False, blank=True, default=False)

    objects = ClassPlanPublication()

    def __str__(self):
        return str(self.name)
    
    # class Meta:
    #     ordering = ['id']
    
    def get_all_topics(self):
        topics = []
        new_topics = [t for t in self.topics.all()]
        while new_topics:
            parents_id = [t.parent for t in new_topics if t.parent]
            topics = topics + new_topics
            new_topics = parents_id
        return list(set(topics))

class ShareClassPlan(models.Model):
    link = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_plan = models.ForeignKey(ClassPlanPublication, related_name= "link_class_plan", on_delete=models.CASCADE)
    share_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.link)

    class Meta:   
        ordering = ['link']