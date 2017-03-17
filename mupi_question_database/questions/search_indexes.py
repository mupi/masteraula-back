from django.utils import timezone

from taggit.models import Tag

from haystack import indexes

from .models import Question

import re
import unicodedata

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True)
    author = indexes.CharField(model_attr='author')
    create_date = indexes.DateTimeField(model_attr='create_date')
    level = indexes.CharField(model_attr='level', null=True)
    question_statement = indexes.CharField(model_attr='question_statement')
    subjects = indexes.MultiValueField()
    tags = indexes.MultiValueField()
    education_level = indexes.CharField(model_attr='education_level', null=True)
    year = indexes.CharField(model_attr='year', null=True)
    source = indexes.CharField(model_attr='source', null=True)

    def get_model(self):
        return Question

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(create_date__lte=timezone.now())


    def prepare_question_statement(self, obj):
        cleaner = re.compile('<.*?>')
        return re.sub(cleaner, '', obj.question_statement)

    def prepare_level(self, obj):
        if obj.level == 'E':
            return 'Facil'
        elif obj.level == 'M':
            return 'Medio'
        elif obj.level == 'H':
            return 'Dificil'
        return ''

    def prepare_tags(self, obj):
        return [tag.slug for tag in obj.tags.all()]

    def prepare_subjects(self, obj):
        return [ unicodedata.normalize('NFKD', subject.subject_name).encode('ASCII', 'ignore')
                    for subject in obj.subjects.all()]

class TagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True)
    name = indexes.CharField(model_attr='name')
    slug = indexes.CharField(model_attr='slug')
    tags_auto = indexes.EdgeNgramField(model_attr='slug')

    def get_model(self):
        return Tag
