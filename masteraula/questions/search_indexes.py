from django.utils import timezone
from django.utils.text import slugify

from taggit.models import Tag

from haystack import indexes

from .models import Question
from masteraula.questions.templatetags.search_helpers import stripaccents

import re
import unicodedata

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True, boost=0.1)

    topics = indexes.CharField(boost=100)
    tags = indexes.CharField(boost=50)
    learning_objects_tags = indexes.CharField(boost=30)

    disciplines = indexes.MultiValueField()
    teaching_levels = indexes.MultiValueField()
    year = indexes.CharField(model_attr='year')
    source = indexes.CharField(model_attr='source')
    difficulty = indexes.CharField()

    def get_model(self):
        return Question
    
    def prepare_topics(self, obj):
        return ' '.join([ topic.name for topic in obj.topics.only('name') ])

    def prepare_tags(self, obj):
        return ' '.join([ tag.name for tag in obj.tags.only('name') ])

    def prepare_learning_objects_tags(self, obj):
        return ' '.join([ tag.name for lo in obj.learning_objects.all() for tag in lo.tags.only('name') ])

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