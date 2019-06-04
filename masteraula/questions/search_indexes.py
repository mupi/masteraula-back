from django.utils import timezone
from django.utils.text import slugify

from taggit.models import Tag

from haystack import indexes

from .models import Question
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

    def get_model(self):
        return Question

    def prepare_statement(self, obj):
        return prepare_document(obj.statement)

    def prepare_topics(self, obj):
        return ' '.join([ stripaccents(topic.name) for topic in obj.topics.only('name') ])

    def prepare_tags(self, obj):
        return ' '.join([ stripaccents(tag.name) for tag in obj.tags.only('name') ])

    def prepare_difficulty(self, obj):
        if obj.difficulty == 'E':
            return 'Facil'
        elif obj.difficulty == 'M':
            return 'Medio'
        elif obj.difficulty == 'H':
            return 'Dificil'
        return ''

    def prepare_disciplines(self, obj):
        return [ discipline.pk for discipline in obj.disciplines.only('pk') ]

    def prepare_teaching_levels(self, obj):
        return [ teaching_level.pk for teaching_level in obj.teaching_levels.only('pk') ]

    def prepare_author(self, obj):
        return obj.author.pk 