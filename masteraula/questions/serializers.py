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

from .models import (Discipline, TeachingLevel, LearningObject, Question,
                    Alternative, Document, DocumentQuestion, Header, Year,
                    Source, Topic, LearningObject, Search, DocumentDownload, Synonym, Label, ClassPlan, TeachingYear, Link)

from django.db.models import Prefetch

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
        if type(data) is list:
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

class ModelListSerializer(serializers.ListField):
    
    def __init__(self, queryset, *args, **kwargs):
        super().__init__(args, kwargs)
        self.queryset = queryset

    def to_internal_value(self, data):
        if type(data) is not list:
            raise serializers.ValidationError(_("Expected a list of data"))

        ids_list = list(set(data))
        try:
            ids_list = [int(_id) for _id in ids_list]
        except:
            raise serializers.ValidationError(_("Expected a list valid primary keys"))
        
        qs = self.queryset.filter(id__in=ids_list)
        qs_ids = [obj.id for obj in qs]

        not_present_ids = [str(_id) for _id in qs_ids if _id not in ids_list]

        if not_present_ids:
            raise serializers.ValidationError('{} [{}]'.format(_("Id not presented: "), ', '.join(not_present_ids)))
        return qs

class DisciplineSerializer(serializers.ModelSerializer):
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
    questions_quantity = serializers.SerializerMethodField()

    class Meta:
        model = LearningObject
        fields = (
            'id',
            'owner',
            'source',
            'image',
            'text',
            'tags',
            'object_types',
            'questions_quantity',
        )

        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'source': { 'read_only' : True },
            'image': { 'read_only' : True },
            'text': { 'read_only' : True },
            'object_types': { 'read_only' : True },
        }            
    
    def get_questions_quantity(self, obj):
        try:
            obj._prefetched_objects_cache['questions']
            return len([1 for question in obj.questions.all() if not question.disabled])
        except (AttributeError, KeyError):
            return obj.questions.filter(disabled=False).count()

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

class TopicListSerializer(serializers.ModelSerializer):
    num_questions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'num_questions',
        )

class TopicSerializer(serializers.ModelSerializer):
    childs = serializers.ListSerializer(child=RecursiveField())

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'childs',
        )

class TopicSimplestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
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

class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = (
            'id',
            'text',
            'is_correct'
        )

class LabelSerializer(serializers.ModelSerializer):
    color = serializers.CharField(read_only=False, required=False, allow_null=True)
    num_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Label
        fields = (
             'id',
             'name',
             'color',
             'owner',
             'num_questions'
        )

        extra_kwargs = {
            'owner' : { 'read_only' : True },
            }

    def get_num_questions(self, obj):
        try:
            obj._prefetched_objects_cache['question_set']
            return len(obj.question_set)
        except (AttributeError, KeyError):
            return obj.question_set.count()

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
    topics = TopicSimpleSerializer(read_only=True, many=True)

    labels = serializers.SerializerMethodField('get_labels_owner')
    def get_labels_owner(self, obj):
        try:
            user = self.context.get('request').user
        except:
            user = None
        try:
            obj._prefetched_objects_cache['labels']
            labels = [label for label in obj.labels.all() if label.owner == user]
        except (AttributeError, KeyError):
            labels = Label.objects.filter(owner=user, question=obj)
        serializer = LabelSerializer(labels, many=True)
        return serializer.data

    learning_objects = LearningObjectSerializer(many=True, read_only=True)

    all_topics = serializers.SerializerMethodField('all_topics_serializer')
    def all_topics_serializer(self, question):
        return TopicSimpleSerializer(question.get_all_topics(), many=True).data

    alternatives = AlternativeSerializer(many=True, read_only=False, required=False, allow_null=True)
    tags = TagListSerializer(read_only=False, required=False, allow_null=True) 
    year = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    difficulty = serializers.CharField(read_only=False, required=True)

    learning_objects_ids = ModelListSerializer(write_only=True, allow_null=True, required=False, many=True, queryset=LearningObject.objects.all())
    topics_ids = ModelListSerializer(write_only=True, many=True, queryset=Topic.objects.all())
    disciplines_ids = ModelListSerializer(write_only=True, many=True, queryset=Discipline.objects.all())
    teaching_levels_ids = ModelListSerializer(write_only=True, many=True, queryset=TeachingLevel.objects.all())
    source_id = serializers.PrimaryKeyRelatedField(write_only=True, required=False, allow_null=True, queryset=Source.objects.all())

    documents_quantity  = serializers.SerializerMethodField()
    users_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id',
            'author',
            'authorship',
            'create_date',

            'statement',
            'learning_objects',
            'resolution',
            'difficulty',
            'alternatives',

            'disciplines',
            'teaching_levels',
            'year',
            'source',
            'topics',
            'labels',
            'all_topics',

            'learning_objects_ids',
            'topics_ids',
            'disciplines_ids',
            'teaching_levels_ids',
            'source_id',
            # 'credit_cost',
            'tags',   
            'disabled',
            'documents_quantity',
            'users_quantity'
        )

        depth = 1

    def get_documents_quantity(self, obj):
        documents = Document.objects.filter(questions__id=obj.id, disabled = False).count()
        return documents
    
    def get_users_quantity(self, obj):
        documents = Document.objects.filter(questions__id=obj.id, disabled = False)
        try:
            user = self.context.get('request').user
            users = User.objects.filter(document__id__in=documents).exclude(id=user.id).count()
        except:
            users = None
    
        return users

    def validate_alternatives(self, value):
        if value:
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

    def validate_topics_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one topic id"))
        return list(set(value))

    def validate_teaching_levels_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one teaching level id"))
        return list(set(value))

    # def validate_tags(self, value):
    #     if len(value) < 2:
    #         raise serializers.ValidationError(_("At least two tags"))
    #     return value

    def validate_year(self, value):
        if not value:
            return datetime.date.today().year
            
        if value > datetime.date.today().year:
            raise serializers.ValidationError(_("Year bigger than this year")) 
        return value

    def create(self, validated_data):
        # m2m
        tags = validated_data.pop('tags', None)
        alternatives = validated_data.pop('alternatives', None)

        if not validated_data['resolution'] and not alternatives:
            raise serializers.ValidationError(_("Should contain alternatives or resolution"))

        if 'year' not in validated_data or not validated_data['year']:
            validated_data['year'] =  datetime.date.today().year

        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
            if key.endswith('_id'):
                validated_data[key[:-3]] = validated_data.pop(key)

        question = super().create(validated_data)

        if tags != None:
            tags = [tag for tag in tags if tag.strip() != '']
            question.tags.set(*tags, clear=True)

        if alternatives != None:
            for alt in alternatives:
                Alternative.objects.create(question=question, **alt)

        return Question.objects.get_questions_prefetched().get(id=question.id)

    def update(self, instance, validated_data):
        # m2m
        tags = validated_data.pop('tags', None)
        alternatives = validated_data.pop('alternatives', None)

        if 'resolution' in validated_data:
            if not alternatives and not validated_data['resolution']:
                raise serializers.ValidationError(_("Should contain alternatives or resolution"))

        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
            if key.endswith('_id'):
                validated_data[key[:-3]] = validated_data.pop(key)
        question = super().update(instance, validated_data)

        if tags != None:
            tags = [tag for tag in tags if tag.strip() != '']
            question.tags.set(*tags, clear=True)

        if alternatives != None:
            question.alternatives.all().delete()
            for alt in alternatives:
                Alternative.objects.create(question=question, **alt)
                
        return Question.objects.get_questions_prefetched().get(id=question.id)

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

class QuestionLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label.question_set.through
        fields = (
            'id',
            'question',
            'label',
        )
        extra_kwargs = {
            'label' : { 'read_only' : True }
        }

    def validate_question(self, data):
        if data.disabled:
            raise serializers.ValidationError(_("This question is disabled"))
        return data
    
    def create(self, validated_data):
        label = validated_data['label']
        try:
            return label.question_set.through.get(question_id=validated_data['question'].id)
        except:
            questionLabel = label.add_question(validated_data['question'])
            return questionLabel

class QuestionLabelListDetailSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    label = LabelSerializer(read_only=True)

    class Meta:
        model = Label.question_set.through
       
        fields = (
            'id',
            'question',
            'label',
        )
        extra_kwargs = {
            'label' : { 'read_only' : True }
        }

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

    def validate_question(self, data):
        if data.disabled:
            raise serializers.ValidationError(_("This question is disabled"))
        return data
    
    def create(self, validated_data):
        document = validated_data['document']
        try:
            return document.documentquestion_set.get(question=validated_data['question'])
        except:
            documentQuestion = document.add_question(validated_data['question'])
            return documentQuestion 

class DocumentQuestionDestroySerializer(serializers.ModelSerializer):

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
    questions_quantity = serializers.SerializerMethodField()
    plans_quantity = serializers.SerializerMethodField()


    class Meta:
        model = Document
        fields = (
            'id',
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
            'questions_quantity',
            'plans_quantity'
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True }
        }

    def get_questions_quantity(self, obj):
        try:
            obj._prefetched_objects_cache['questions']
            return len([1 for question in obj.questions.all() if not question.disabled])
        except (AttributeError, KeyError):
            return obj.questions.count()
    
    def get_plans_quantity(self, obj):
        plans = ClassPlan.objects.filter(documents__id=obj.id, disabled=False).count()
        return plans

class DocumentListInfoSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    questions_quantity = serializers.SerializerMethodField()
    questions_topics = serializers.SerializerMethodField('questions_topics_serializer')

    def questions_topics_serializer(self, obj):
        questions = obj.questions.prefetch_related(Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')))
        topic = []
        for q in questions:
            topic += q.get_all_topics()
        topic = list(set(topic))
        return TopicSimpleSerializer(topic, many=True).data

    questions_disciplines = serializers.SerializerMethodField('questions_disciplines_serializer')

    def questions_disciplines_serializer(self, obj):
        questions = obj.questions.prefetch_related('disciplines')
        discipline = []
        for q in questions:
            discipline += q.disciplines.all()
        discipline = list(set(discipline))
        return DisciplineSerializer(discipline, many=True).data

    class Meta:
        model = Document
        fields = (
            'id',
            'name',
            'owner',
            'create_date',
            'questions_quantity',
            'questions_topics',
            'questions_disciplines',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True }
        }

    def get_questions_quantity(self, obj):
        try:
            obj._prefetched_objects_cache['questions']
            return len([1 for question in obj.questions.all() if not question.disabled])
        except (AttributeError, KeyError):
            return obj.questions.filter(disabled=False).count()

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
            'disabled'
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True },
            'documentquestion_set' : { 'read_only' : True}
              }

    def create(self, validated_data):
        document = Document.objects.create(**validated_data)

        return document

    def update(self, instance, validated_data):
        instance.update(**validated_data)
        
        return Document.objects.get_questions_prefetched().get(id=instance.id)

class DocumentCreatesSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionListDetailSerializer(many=True, source='documentquestion_set', read_only=True)
    idQuestion = serializers.IntegerField(required=False, allow_null=True) 
    questions_quantity = serializers.SerializerMethodField()
  
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
            'questions_quantity'
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True },
            'documentquestion_set' : { 'read_only' : True}
              }
    
    def get_questions_quantity(self, obj):
        try:
            obj._prefetched_objects_cache['questions']
            return len([1 for question in obj.questions.all() if not question.disabled])
        except (AttributeError, KeyError):
            return obj.questions.filter(disabled=False).count()


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

class DocumentDownloadSerializer(serializers.ModelSerializer):
    document = ListDocumentQuestionSerializer()
  
    class Meta:
        model = DocumentDownload
        fields = (
            'id',
            'document',
            'download_date',
            'answers',
        )

class DocumentDetailPublicationSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionListDetailSerializer(many=True, source='documentquestion_set', read_only=True)
  
    class Meta:
        model = Document
        fields = (
            'id',
            'name',
            'questions',
        )
        extra_kwargs = {
            'documentquestion_set' : { 'read_only' : True}
        }

class SynonymSerializer(serializers.ModelSerializer):
    topics = TopicSimplestSerializer(read_only=True, many=True)

    class Meta:
        model = Synonym
        fields = (
             'term',
             'topics',
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

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = (
            'id',
            'link',
            'description_url',
        )

class TeachingYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingYear
        fields = (
            'id',
            'name',
        )

class ClassPlanSerializer(serializers.ModelSerializer):
    owner = UserDetailsSerializer(read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    topics = TopicSimpleSerializer(read_only=True, many=True)
    learning_objects = LearningObjectSerializer(many=True, read_only=True)
    documents = DocumentListInfoSerializer(many=True,read_only=True)

    learning_objects_ids = ModelListSerializer(write_only=True, allow_null=True, required=False, many=True, queryset=LearningObject.objects.all())
    topics_ids = ModelListSerializer(write_only=True, many=True, queryset=Topic.objects.all())
    disciplines_ids = ModelListSerializer(write_only=True, many=True, queryset=Discipline.objects.all())
    teaching_levels_ids = ModelListSerializer(write_only=True, many=True, queryset=TeachingLevel.objects.all())
    documents_ids = ModelListSerializer(write_only=True, many=True, queryset=Document.objects.all())
    teaching_years_ids = ModelListSerializer(write_only=True, many=True, queryset=TeachingYear.objects.all())
    links = LinkSerializer(many=True)

    class Meta:
        model = ClassPlan
        fields = (
            'id',
            'owner',
            'create_date',
            'name',

            'disciplines',
            'teaching_levels',
            'topics',
            'learning_objects',
            'documents', 
            'links',
            'teaching_years',

            'learning_objects_ids',
            'topics_ids',
            'disciplines_ids',
            'teaching_levels_ids',
            'documents_ids',
            'teaching_years_ids',

            'duration',
            'comment',
            'description',
            'pdf',
        )

        extra_kwargs = {
            'name' : { 'required' : True},
            'disciplines' : { 'required' : True},
            'teaching_levels' : { 'required' : True}
        }
        depth = 1

    def validate_disciplines_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one discipline id"))
        return list(set(value))

    def validate_topics_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one topic id"))
        return list(set(value))

    def validate_teaching_levels_ids(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(_("At least one teaching level id"))
        return list(set(value))
    
    def validate_duration(self, value):
        if value == 0:
            value = None
        return value
           
    def validate_links(self, value):
        if len(value) > 0:
            for lin in value:
                for i, (k,v) in enumerate(lin.items()):
                    if k =="link" and "://" not in v:
                        lin[k] =  "https://" + v
        return value
        
    def create(self, validated_data):
        links = validated_data.pop('links', None)
        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
        
        plan = super().create(validated_data)

        if links != None:
            for lin in links:
                Link.objects.create(plan=plan, **lin)

        return ClassPlan.objects.get(id=plan.id)
    
    def update(self, instance, validated_data):
        learning_objects_ids = validated_data.pop('learning_objects_ids', None)
        documents_ids = validated_data.pop('documents_ids', None)
        teaching_years_ids = validated_data.pop('teaching_years_ids', None)

        links = validated_data.pop('links', None)
        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
        
        plan = super().update(instance, validated_data)

        if links != None:
            plan.links.all().delete()
            for lin in links:
                Link.objects.create(plan=plan, **lin)

        plan.learning_objects.clear()
        if learning_objects_ids != None:
            for l in learning_objects_ids:
                plan.learning_objects.add(l)

        plan.documents.clear()
        if documents_ids != None:
            for d in documents_ids:
                plan.documents.add(d)
        
        plan.teaching_years.clear()
        if teaching_years_ids != None:
            for t in teaching_years_ids:
                plan.teaching_years.add(t)

        return ClassPlan.objects.get(id=plan.id)
