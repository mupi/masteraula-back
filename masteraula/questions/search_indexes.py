from django.utils import timezone
from django.utils.text import slugify

from taggit.models import Tag

from haystack import indexes
from haystack.inputs import Clean
from haystack.query import SearchQuerySet, SQ, AutoQuery

from .models import Question, LearningObject, Synonym, Topic
from masteraula.questions.templatetags.search_helpers import stripaccents, prepare_document, stripaccents_str

from functools import reduce

import re
import unicodedata

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, boost=0.01)
    
    topics = indexes.CharField(boost=1000)
    tags = indexes.CharField(boost=100)
    statement = indexes.CharField()

    topics_ids = indexes.MultiValueField()
    disciplines = indexes.MultiValueField()
    teaching_levels = indexes.MultiValueField()

    year = indexes.CharField(model_attr='year', null=True)
    source = indexes.CharField(model_attr='source', null=True)
    difficulty = indexes.CharField()
    author = indexes.IntegerField()
    authorship = indexes.CharField()
    disabled = indexes.BooleanField(model_attr='disabled')

    def get_model(self):
        return Question
    
    def index_queryset(self, using=None):
        return Question.objects.get_questions_update_index().filter(disabled=False)

    def prepare_statement(self, obj):
        return prepare_document(obj.statement)

    def prepare_topics(self, obj):
        topics = obj.get_all_topics()
        res = [ topic.name for topic in topics ]

        for topic in topics:
            res += [ synonym.term for synonym in topic.synonym_set.all() ]

        return ' '.join(stripaccents(t) for t in res)
    
    def prepare_topics_ids(self, obj):
        return [ topic.pk for topic in obj.get_all_topics() ]

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

    @staticmethod
    def filter_question_search(text, query_params):
        disciplines = query_params.getlist('disciplines', None)
        teaching_levels = query_params.getlist('teaching_levels', None)
        difficulties = query_params.getlist('difficulties', None)
        years = query_params.getlist('years', None)
        sources = query_params.getlist('sources', None)
        author = query_params.get('author', None)
        topics = query_params.getlist('topics', None)

        params = {'disabled' : 'false'}
        if disciplines:
            params['disciplines__id__in'] = disciplines
        if teaching_levels:
            params['teaching_levels__in'] = teaching_levels
        if difficulties:
            difficulties_texts = []
            if 'E' in difficulties:
                difficulties_texts.append('Facil')
            if 'M' in difficulties:
                difficulties_texts.append('Medio')
            if 'H' in difficulties:
                difficulties_texts.append('Dificil')
            params['difficulty__in'] = difficulties_texts
        if years:
            params['year__in'] = years
        if sources:
            params['source__in'] = sources
        if author:
            params['author__id'] = author
        if topics:
            params['topics_ids__in'] = topics
    
        # The following queries are to apply the weights of haystack boost
        queries = [SQ(tags=Clean(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        query = queries.pop()
        for item in queries:
            query |= item
        queries = [SQ(topics=Clean(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item
        queries = [SQ(statement=Clean(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item

        search_queryset = SearchQuerySet().models(Question).filter_and(**params)
        search_queryset = search_queryset.filter(SQ(content=Clean(text)) | (
            SQ(content=Clean(text)) & query
        ))

        return search_queryset

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

class SynonymIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    term = indexes.CharField(model_attr='term')
    topics = indexes.MultiValueField()
    term_auto = indexes.EdgeNgramField(model_attr='term')

    def get_model(self):
        return Synonym

    def index_queryset(self, using=None):
        return Synonym.objects.get_topics_prefetched()

    def prepare_topics(self, obj):
        return [ topic.name for topic in obj.topics.all() ]
    
    def prepare_term_auto(self, obj):
        return stripaccents_str(obj)

class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    term_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Topic

    def prepare_term_auto(self, obj):
        return stripaccents_str(obj)