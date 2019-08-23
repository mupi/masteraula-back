from django.utils import timezone
from django.utils.text import slugify

from taggit.models import Tag

from haystack import indexes

from .models import Question, LearningObject
from masteraula.questions.templatetags.search_helpers import stripaccents, prepare_document

import re
import unicodedata

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, boost=0.01)
    
    topics = indexes.CharField(boost=1000)
    tags = indexes.CharField(boost=100)
    statement = indexes.CharField()

    disciplines = indexes.MultiValueField()
    teaching_levels = indexes.MultiValueField()
    year = indexes.CharField(model_attr='year', null=True)
    source = indexes.CharField(model_attr='source', null=True)
    difficulty = indexes.CharField()
    author = indexes.IntegerField()
    disabled = indexes.BooleanField(model_attr='disabled')

    def get_model(self):
        return Question
    
    def index_queryset(self, using=None):
        return Question.objects.get_questions_update_index().filter(disabled=False)

    def prepare_statement(self, obj):

        return prepare_document(obj.statement)

    def prepare_topics(self, obj):
        return ' '.join([ stripaccents(topic.name) for topic in obj.get_all_topics() ])

    def prepare_tags(self, obj):
        return ' '.join([ stripaccents(tag.name) for tag in obj.tags.all() ])

    def prepare_difficulty(self, obj):
        if obj.difficulty == 'E':
            return 'Facil'
        elif obj.difficulty == 'M':
            return 'Medio'
        elif obj.difficulty == 'H':
            return 'Dificil'
        return ''

    def prepare_disciplines(self, obj):
        return [ discipline.pk for discipline in obj.disciplines.all() ]

    def prepare_teaching_levels(self, obj):
        return [ teaching_level.pk for teaching_level in obj.teaching_levels.all() ]

    def prepare_author(self, obj):
        return obj.author_id 

class LearningObjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, boost=0.01)
    source = indexes.CharField()
    text_object = indexes.CharField(model_attr='text', null=True)
    tags = indexes.CharField(boost=1000)
    is_image = indexes.BooleanField()
    is_text = indexes.BooleanField()

    def get_model(self):
        return LearningObject

    def index_queryset(self, using=None):
        return LearningObject.objects.get_objects_update_index()

    def prepare_source(self, obj):
        return prepare_document(obj.source)
    
    def prepare_text_object(self, obj):
        return prepare_document(obj.text)

    def prepare_is_text(self, obj):
        return obj.text != None and obj.text != ''

    def prepare_is_image(self, obj):
        return obj.image != None and obj.image != ''
    
    def prepare_tags(self, obj):
        return ' '.join([ stripaccents(tag.name) for tag in obj.tags.all() ])

