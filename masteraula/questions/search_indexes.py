from django.utils import timezone
from django.utils.text import slugify

from taggit.models import Tag

from haystack import indexes

from .models import Question
from masteraula.questions.templatetags.search_helpers import stripaccents

import re
import unicodedata

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True)
    author = indexes.CharField(model_attr='author')
    create_date = indexes.DateTimeField(model_attr='create_date')
    
    statement = indexes.CharField(model_attr='statement')
    learning_objects = indexes.MultiValueField(indexed=True)
    resolution = indexes.CharField(model_attr='resolution')
    difficulty = indexes.CharField(model_attr='difficulty', null=True)

    disciplines = indexes.MultiValueField(indexed=True)
    descriptors = indexes.MultiValueField(indexed=True)
    teaching_levels = indexes.MultiValueField(indexed=True)
    
    year = indexes.CharField(model_attr='year', null=True)
    source = indexes.CharField(model_attr='source', null=True)

    tags = indexes.MultiValueField(indexed=True)

    def get_model(self):
        return Question

    # def index_queryset(self, using=None):
    #     """Used when the entire index for model is updated."""
    #     return self.get_model().objects.filter(create_date__lte=timezone.now())

    def prepare_statement(self, obj):
        cleaner = re.compile('<.*?>')
        return re.sub(cleaner, '', obj.statement)

    def prepare_learning_objects(self, obj):
        cleaner = re.compile('<.*?>')
        for learning_objects in obj.learning_objects.all():
            if learning_objects.text is not None:
                return [re.sub(cleaner, '', learning_objects.text)]      

    def prepare_difficulty(self, obj):
        if obj.difficulty == 'E':
            return 'Facil'
        elif obj.difficulty == 'M':
            return 'Medio'
        elif obj.difficulty == 'H':
            return 'Dificil'
        return ''

    def prepare_tags(self, obj):
        return [ tag.name for tag in obj.tags.all() ]

    def prepare_tags_slugs(self, obj):
        return [ tag.slug for tag in obj.tags.all() ]

    def prepare_disciplines(self, obj):
        return [ discipline.pk for discipline in obj.disciplines.all() ]

    def prepare_teaching_levels(self, obj):
        return [ teaching_level.pk for teaching_level in obj.teaching_levels.all() ]

class TagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True)
    name = indexes.CharField(model_attr='name')
    slug = indexes.CharField(model_attr='slug')
    tags_auto = indexes.EdgeNgramField(model_attr='slug')

    def get_model(self):
        return Tag
