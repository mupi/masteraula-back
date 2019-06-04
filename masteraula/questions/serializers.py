from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,get_username_max_length)
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from drf_haystack.serializers import HaystackSerializer, HaystackSerializerMixin

from rest_auth.registration import serializers as auth_register_serializers
from rest_auth import serializers as auth_serializers

from rest_framework import serializers, exceptions

from rest_framework_recursive.fields import RecursiveField

from taggit.models import Tag

from masteraula.users.models import User, Profile
from masteraula.users.serializers import UserDetailsSerializer

from .models import (Discipline, TeachingLevel, LearningObject, Descriptor, Question,
                     Alternative, Document, DocumentQuestion, Header, Year, Source, Topic, LearningObject, Search)

import unicodedata
import ast
import datetime

# from .search_indexes import QuestionIndex, TagIndex

class TagListSerializer(serializers.Field):
    '''
    TagListSerializer para tratar o App taggit, ja que nao possui suporte para
    rest_framework
    '''
    def to_internal_value(self, data):
        if  type(data) is list:
            return data
        try:
            taglist = ast.literal_eval(data)
            return taglist
        except BaseException as e:
            raise serializers.ValidationError(_("Expected a list of data"))

    def to_representation(self, obj):
        if type(obj) is not list:
            return [{'name' : tag.name} for tag in obj.all()]
        return obj

class DisciplineSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = (
            'id',
            'name',
            'slug',
        )

class TeachingLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingLevel
        fields = (
            'id',
            'name',
            'slug',
        )

class YearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = (
            'id',
            'name'
        )

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = (
            'id',
            'name'
        )

class LearningObjectSerializer(serializers.ModelSerializer):
    tags = TagListSerializer(read_only=False, required=False) 

    class Meta:
        model = LearningObject
        fields = (
            'id',
            'owner',
            'source',
            'image',
            'text',
            'tags',
        )

        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'source': { 'read_only' : True },
            'image': { 'read_only' : True },
            'text': { 'read_only' : True },
        }            

    def create(self, validated_data):
        tags = validated_data.pop('tags', None)
        learning_object = super().create(validated_data)

        if tags != None:
            for t in [tag for tag in tags if tag != '']:
                learning_object.tags.add(t)
        
        return learning_object

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)

        learning_object = super().update(instance, validated_data)

        if tags != None:
            learning_object.tags.clear()
            for t in [tag for tag in tags if tag.strip() != '']:
                learning_object.tags.add(t)

        return learning_object

class TopicSerializer(serializers.ModelSerializer):
    childs = serializers.ListSerializer(child=RecursiveField())

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'childs',
        )
        
class TopicSimpleSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'parent',
        )

    def get_parent(self, obj):
        if obj.parent is not None:
            return TopicSimpleSerializer(obj.parent).data
        else:
            return None

class DescriptorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descriptor
        fields = (
            'id',
            'name',
            'description'
        )

class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = (
            'id',
            'text',
            'is_correct'
        )

class ListDocumentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = (
            'id',
            'name',   
        )
       
class QuestionSerializer(serializers.ModelSerializer):
    author = UserDetailsSerializer(read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    learning_objects =  LearningObjectSerializer(many=True, read_only=True)
    topics = TopicSimpleSerializer(read_only=True, many=True)

    all_topics = serializers.SerializerMethodField('all_topics_serializer')
    def all_topics_serializer(self, question):
        return TopicSimpleSerializer(question.get_all_topics(), many=True).data

    alternatives = AlternativeSerializer(many=True, read_only=False)
    tags = TagListSerializer(read_only=False) 
    year = serializers.IntegerField(read_only=False, default=datetime.date.today().year)
    topics_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True, queryset=Topic.objects.all())
    disciplines_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True, queryset=Discipline.objects.all())
    teaching_levels_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True, queryset=TeachingLevel.objects.all())

    class Meta:
        model = Question
        fields = (
            'id',
            'author',
            'create_date',

            'statement',
            'learning_objects',
            'resolution',
            'difficulty',
            'alternatives',

            'disciplines',
            'descriptors',
            'teaching_levels',
            'year',
            'source',
            'topics',
            'all_topics',

            'topics_ids',
            'disciplines_ids',
            'teaching_levels_ids',

            # 'credit_cost',
            
            'tags',   
        )

        depth = 1

    def validate_alternatives(self, value):
        if len(value) < 3:
            raise serializers.ValidationError(_("At least 3 alternatives"))
        number_of_corrects = 0
        for alternative in value:
            if 'is_correct' in alternative and alternative['is_correct']:
                number_of_corrects += 1
        if number_of_corrects != 1:
            raise serializers.ValidationError(_("Should contan at least 1 correct alternative"))
        return value

    def validate_disciplines_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one discipline id"))
        return list(set(value))

    def validate_teaching_levels_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one teaching level id"))
        return list(set(value))

    def validate_tags(self, value):
        print(value)
        if len(value) < 2:
            raise serializers.ValidationError(_("At least two tags"))
        return value

    def validate_year(self, value):
        if value > datetime.date.today().year:
            raise serializers.ValidationError(_("Year bigger than this year")) 
        return value

    def create(self, validated_data):
        # m2m
        tags = validated_data.pop('tags', None)
        topics = validated_data.pop('topics_ids', None)
        alternatives = validated_data.pop('alternatives', None)
        disciplines = validated_data.pop('disciplines_ids', None)
        teaching_levels = validated_data.pop('teaching_levels_ids', None)

        question = super().create(validated_data)
        if not question.year:
            question.year = datetime.date.today().year

        if tags != None:
            for t in [tag for tag in tags if tag.strip() != '']:
                question.tags.add(t)

        if topics != None:
            for t in topics:
                question.topics.add(t)

        if alternatives != None:
            for alt in alternatives:
                Alternative.objects.create(question=question, **alt)

        for discipline in disciplines:
            question.disciplines.add(discipline)

        for teaching_level in teaching_levels:
            question.teaching_levels.add(teaching_level)

        question.save()
        
        return question

    def update(self, instance, validated_data):
        # m2m
        tags = validated_data.pop('tags', None)
        topics = validated_data.pop('topics_ids', None)
        alternatives = validated_data.pop('alternatives', None)
        disciplines = validated_data.pop('disciplines_ids', None)
        teaching_levels = validated_data.pop('teaching_levels_ids', None)

        question = super().update(instance, validated_data)
        if not question.year:
            question.year = datetime.date.today().year

        if tags != None:
            question.tags.clear()
            for t in [tag for tag in tags if tag.strip() != '']:
                question.tags.add(t)

        if topics != None:
            question.topics.clear()
            for t in topics:
                question.topics.add(t)

        if alternatives != None:
            question.alternatives.all().delete()
            for alt in alternatives:
                Alternative.objects.create(question=question, **alt)

        if alternatives != None:
            question.disciplines.clear()
            for discipline in disciplines:
                question.disciplines.add(discipline)

        if teaching_levels != None:
            question.teaching_levels.clear()
            for teaching_level in teaching_levels:
                question.teaching_levels.add(teaching_level)

        question.save()

        return question

class QuestionTagEditSerializer(serializers.ModelSerializer):
    topics_ids = serializers.PrimaryKeyRelatedField(write_only=True, many=True, queryset=Topic.objects.all())
    tags = TagListSerializer(read_only=False) 

    class Meta:
        model = Question
        fields = (
            'id',
            'difficulty',
            'topics_ids',

            'tags',   
        )

        extra_kwargs = {
            'difficulty' : { 'read_only' : False, 'required' : True},
        }
        depth = 1

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        topics = validated_data.pop('topics_ids', None)

        question = super().update(instance, validated_data)

        if tags != None:
            question.tags.clear()
            for t in [tag for tag in tags if tag.strip() != '']:
                question.tags.add(t)

        if topics != None:
            question.topics.clear()
            for t in topics:
                question.topics.add(t)
        question.save()

        return question

# class QuestionSearchSerializer(HaystackSerializerMixin, QuestionSerializer):
# 
#    class Meta(QuestionSerializer.Meta):
#       search_fields = ('text',)

class DocumentQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DocumentQuestion
        fields = (
            'id',
            'question',
            'document',
            'order',
        )
        extra_kwargs = {
            'document' : { 'read_only' : True },
            'order' : { 'required' : False }
        }
    
    def create(self, validated_data):
        document = validated_data['document']
        try:
            return document.documentquestion_set.get(question=validated_data['question'])
        except:
            documentQuestion = document.add_question(validated_data['question'])
            return documentQuestion 

class DocumentQuestionListDetailSerializer(serializers.ModelSerializer):
    
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = DocumentQuestion
       
        fields = (
            'id',
            'question',
            'document',
            'order',
        )
        extra_kwargs = {
            'document' : { 'read_only' : True },
            'order' : { 'required' : False }
        }

 
        
class DocumentListSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionSerializer(many=True, source='documentquestion_set', read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)

    class Meta:
        model = Document
        fields = (
            'id',
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True }
        }

class DocumentDetailSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionListDetailSerializer(many=True, source='documentquestion_set', read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
  

    class Meta:
        model = Document
        fields = (
            'id',
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True },
            'documentquestion_set' : { 'read_only' : True}
              }

    # def validate_questions(self, value):
    #     documentQuestions = sorted(value, key=lambda k: k['order'])
    #     documentQuestions = [{'question' : dc['question'], 'order' : order} for order, dc in enumerate(documentQuestions)]
    #     return documentQuestions

    def create(self, validated_data):
        # documentQuestions = validated_data.pop('documentquestion_set')
        document = Document.objects.create(**validated_data)

        # document.set_questions(documentQuestions)

        return document

    def update(self, instance, validated_data):
        # if 'documentquestion_set' in validated_data:
        #     documentquestion_set = validated_data.pop('documentquestion_set')
            # instance.set_questions(documentquestion_set)

        instance.update(**validated_data)
        
        return instance

class DocumentCreatesSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionListDetailSerializer(many=True, source='documentquestion_set', read_only=True)
    idQuestion = serializers.IntegerField(required=False, allow_null=True) 
  
    class Meta:
        model = Document
        fields = (
            'id',
            'idQuestion',
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True },
            'documentquestion_set' : { 'read_only' : True}
              }

    def validate_questions(self, value):
        documentQuestions = sorted(value, key=lambda k: k['order'])
        documentQuestions = [{'question' : dc['question'], 'order' : order} for order, dc in enumerate(documentQuestions)]
        return documentQuestions

    def create(self, validated_data):
        idQuestion = validated_data.pop('idQuestion') if 'idQuestion' in validated_data else None
        document = Document.objects.create(**validated_data)

        if idQuestion:
            try:
                question = Question.objects.get(id=idQuestion)
                document.add_question(question)
            except:
                pass

        return document

class HeaderSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Header
        fields = (
            'id',
            'name',
            'owner',
            'institution_name',
            'discipline_name',
            'professor_name',
            'student_indicator',
            'class_indicator',
            'score_indicator',
            'date_indicator',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            }

    def create(self, validated_data):
        header = Header.objects.create(**validated_data)
        return header

    def update(self, instance, validated_data):
        instance.update(**validated_data)
        return instance

class HeaderListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Header
        fields = (
            'id',
            'name',
        )

class SearchSerializer(serializers.ModelSerializer):
    user = UserDetailsSerializer(read_only=True)
    difficulty = serializers.CharField()
    date_search = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    
    class Meta:
        model = Search
        fields = (
            'id',
            'term',
            'user',
            'disciplines',
            'teaching_levels',
            'difficulty',
            'source',
            'year',
            'date_search',
        )
        