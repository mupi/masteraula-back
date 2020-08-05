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
                    Source, Topic, LearningObject, Search, DocumentDownload, 
                    Synonym, Label, TeachingYear,
                    FaqQuestion, FaqCategory, DocumentOnline,
                    Result, DocumentQuestionOnline, StudentAnswer,
                    Task, Activity, Bncc, ClassPlanPublication, StationMaterial, 
                    ShareClassPlan)

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

class ModelListValueSerializer(serializers.ListField):
    
    def __init__(self, queryset, *args, **kwargs):
        super().__init__(args, kwargs)
        self.queryset = queryset

    def to_internal_value(self, data):
        if type(data) is not list:
            raise serializers.ValidationError(_("Expected a list of data"))
       
        ids_list = list(set(data))
        try:
            ids_list = [_id for _id in ids_list]
        except:
            raise serializers.ValidationError(_("Expected a list valid primary keys"))
        
        qs = self.queryset.filter(link__in=ids_list)
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
        data = self.context.get('request').data
        
        if tags != None:
            for t in [tag for tag in tags if tag != '']:
                learning_object.tags.add(t)
        
        else:  
            for key, val in data.items():
                if key.startswith('tags'):
                    learning_object.tags.add(val)
        
        type_obj = []
        if 'image' in data:
            type_obj += "I"

        if 'text' in data:
            if data['text'] != "":
                type_obj += "T"

        learning_object.object_types = type_obj
        learning_object.save()
            
        return learning_object

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        learning_object = super().update(instance, validated_data)
        data = self.context.get('request').data

        learning_object.tags.clear()
        if tags != None:
            for t in [tag for tag in tags if tag.strip() != '']:
                learning_object.tags.add(t)
        
        else:
            for key, val in data.items():
                if key.startswith('tags'):
                    learning_object.tags.add(val)

        type_obj = []
        if 'image' in data:
            type_obj += "I"

        if 'text' in data:
            if data['text'] != "":
                type_obj += "T"

        learning_object.object_types = type_obj
        learning_object.save()
        
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

class AlternativeStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = (
            'id',
            'text'
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
    type_question = serializers.SerializerMethodField()

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
            'users_quantity',
            'type_question' 
        )

        depth = 1

    def get_type_question(self, obj):
        if len(obj.alternatives.all()) > 1:
            return ("Objetiva")
        return("Dissertativa")

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

class QuestionStudentSerializer(serializers.ModelSerializer):
    author = UserDetailsSerializer(read_only=True)
    learning_objects = LearningObjectSerializer(many=True, read_only=True)
    alternatives = AlternativeStudentSerializer(many=True, read_only=False, required=False, allow_null=True)
    year = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    type_question = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id',
            'author',
            'authorship',
            'type_question',
            'statement',
            'learning_objects',
            'resolution',
            'alternatives',
            'year',
            'source',
            'disabled'
        )

        depth = 1

    def get_type_question(self, obj):
        if len(obj.alternatives.all()) > 1:
            return ("Objetiva")
        return("Dissertativa")

class QuestionResultSerializer(serializers.ModelSerializer):
    author = UserDetailsSerializer(read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    topics = TopicSimpleSerializer(read_only=True, many=True)

    learning_objects = LearningObjectSerializer(many=True, read_only=True)
    all_topics = serializers.SerializerMethodField('all_topics_serializer')
    def all_topics_serializer(self, question):
        return TopicSimpleSerializer(question.get_all_topics(), many=True).data

    alternatives = AlternativeSerializer(many=True, read_only=False, required=False, allow_null=True)
    tags = TagListSerializer(read_only=False, required=False, allow_null=True) 
    year = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    difficulty = serializers.CharField(read_only=False, required=True)

    documents_quantity  = serializers.SerializerMethodField()
    type_question = serializers.SerializerMethodField()
    users_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id',
            'author',
            'authorship',
            'create_date',
            'type_question',

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
            'all_topics',

            'tags',   
            'disabled',
            'documents_quantity',
            'users_quantity' 
        )

        depth = 1

    def get_type_question(self, obj):
        if len(obj.alternatives.all()) > 1:
            return ("Objetiva")
        return("Dissertativa")

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
    documents_online = serializers.SerializerMethodField()

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
            'plans_quantity',
            'documents_online',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True }
        }
   
    def get_documents_online(self, obj):
        document_count = DocumentOnline.objects.get_documentonline_prefetch().filter(document=obj)
        return len(document_count)

    def get_questions_quantity(self, obj):
        try:
            obj._prefetched_objects_cache['questions']
            return len([1 for question in obj.questions.all() if not question.disabled])
        except (AttributeError, KeyError):
            return obj.questions.count()
    
    def get_plans_quantity(self, obj):
        plans = ClassPlanPublication.objects.filter(documents__id=obj.id, disabled=False).count()
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

class DocumentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = (
            'id',
            'name',
        )

class DocumentDetailSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionListDetailSerializer(many=True, source='documentquestion_set', read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    types_questions = serializers.SerializerMethodField()
    media_questions = serializers.SerializerMethodField()
    application = serializers.SerializerMethodField()
   
    class Meta:
        model = Document
        fields = (
            'id',
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
            'disabled',
            'types_questions',
            'media_questions',
            'application',
        )
        extra_kwargs = {
            'owner' : { 'read_only' : True },
            'create_date' : { 'read_only' : True },
            'secret' : { 'required' : True },
            'documentquestion_set' : { 'read_only' : True}
              }

    def get_types_questions(self, obj):
        questions = obj.documentquestion_set.all()
        dissertation = 0
        objective = 0

        for q in questions:
            if len(q.question.alternatives.all()) > 1:
                objective += 1
            else:
                dissertation += 1

        dic = {'dissertation_quantity': dissertation, 'objective_quantity': objective}
        return dic

    def get_media_questions(self, obj):
        questions = obj.documentquestion_set.all()
        object_count = 0

        for q in questions:
            object_count += len(q.question.learning_objects.all())
        return object_count
    
    def get_application(self, obj):
        questions = obj.documentquestion_set.all()
        count_exame = 0
        count_authoral = 0

        for q in questions:
            if q.question.authorship != None:
                count_authoral += 1
            else:
                count_exame += 1
        dic = { 'exam_quantity': count_exame, 'authoral_quantity':count_authoral}
        return dic
        
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

class TeachingYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingYear
        fields = (
            'id',
            'name',
        )

class FaqQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqQuestion
        fields = (
            'id',
            'faq_question',
            'faq_answer',
        )

class FaqCategorySerializer(serializers.ModelSerializer):
    category_questions = FaqQuestionSerializer(many=True)

    class Meta:
        model = FaqCategory
        fields = (
            'id',
            'name',
            'description_category',
            'category_questions'
        )
    
    def create(self, validated_data):
        category_questions = validated_data.pop('category_questions', None)
                
        question = super().create(validated_data)

        if category_questions != None:
            for cq in category_questions:
                FaqQuestion.objects.create(category=question, **cq)
        
        return FaqCategory.objects.get(id=question.id)
    
    def update(self, instance, validated_data):
        category_questions = validated_data.pop('category_questions', None)
       
        question = super().update(instance, validated_data)

        if category_questions != None:
            question.category_questions.all().delete()
            for cq in category_questions:
                FaqQuestion.objects.create(category=question, **cq)
    
        return FaqCategory.objects.get(id=question.id)

class DocumentQuestionOnlineSerializer(serializers.ModelSerializer):
    question = QuestionResultSerializer(read_only=True)

    class Meta:
        model = DocumentQuestionOnline
        fields = (
            'id',
            'question',
            'score'
        )

class DocumentQuestionStudentSerializer(serializers.ModelSerializer):
    question = QuestionStudentSerializer(read_only=True)

    class Meta:
        model = DocumentQuestionOnline
        fields = (
            'id',
            'question',
        )

class StudentAnswerSerializer(serializers.ModelSerializer):
    student_question = DocumentQuestionOnlineSerializer(required=False)
    review_score = serializers.SerializerMethodField()


    class Meta:
        model = StudentAnswer
        fields = (
            'id',
            'answer_text',
            'answer_alternative',
            'score_answer',
            'student_question',
            'review_score'

        )
    
    def get_review_score(self, obj):
        if obj.answer_alternative != None:
            return True
        if obj.answer_text != None and obj.score_answer != None:
            return True
        return False

class ResultSerializer(serializers.ModelSerializer):
    student_answer = StudentAnswerSerializer(many=True, read_only=True)
    start = serializers.DateTimeField(required=False)
    finish = serializers.DateTimeField(required=False)
    total_score = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = (
            'id',
            'student_name',
            'student_levels',
            'start',
            'finish',
            'student_answer',
            'total_score',
        )
    
    def get_total_score(self, obj):
        count_score = 0
        for t in obj.student_answer.all():
            if t.score_answer:
                count_score = count_score + t.score_answer
        
        return count_score

    def create(self, validated_data):
        student_answer = self.context.get('request').data
        
        result = super().create(validated_data)
        for q in student_answer['student_answer']:
            
            if 'answer_text' in q:
                question = StudentAnswer.objects.create(answer_text=q['answer_text'], score_answer=None, student_question_id=q['student_question'])
           
            else:
                alternative = Alternative.objects.get(id__in=[q['answer_alternative']])
                group_question =  DocumentQuestionOnline.objects.get(id=q['student_question'])
                status_correct = alternative.is_correct
                if status_correct:
                    score_answer = group_question.score
                else:
                    score_answer = 0

                question = StudentAnswer.objects.create(answer_alternative=alternative, score_answer=score_answer, student_question_id=q['student_question'])
            
            result.student_answer.add(question)

        result.save()       
        return Result.objects.get_result_prefetch().get(id=result.id)

    def update(self, instance, validated_data):
        student_answer = self.context.get('request').data
        result = super().update(instance, validated_data)

        for q in student_answer['student_answer']:
            question = StudentAnswer.objects.get(id=q['id'])

            if len(str(q['score_answer'])) > 11:
                raise serializers.ValidationError(_("Maximum number of digits in score is 10!"))
            
            question.score_answer = q['score_answer']
            question.save()

        result.save()
        return Result.objects.get_result_prefetch().get(id=result.id)

class DocumentOnlineListInfoSerializer(serializers.ModelSerializer):
    questions_quantity = serializers.SerializerMethodField()
    questions_topics = serializers.SerializerMethodField('questions_topics_serializer')
    def questions_topics_serializer(self, obj):
        questions = obj.questions_document.prefetch_related(Prefetch('topics', queryset=Topic.objects.select_related(
        'parent', 'discipline', 'parent__parent', 'parent__discipline')))
        topic = []
        for q in questions:
            topic += q.get_all_topics()
        topic = list(set(topic))
        return TopicSimpleSerializer(topic, many=True).data

    questions_disciplines = serializers.SerializerMethodField('questions_disciplines_serializer')
    def questions_disciplines_serializer(self, obj):
        questions = obj.questions_document.prefetch_related('disciplines')
        discipline = []
        for q in questions:
            discipline += q.disciplines.all()
        discipline = list(set(discipline))
        return DisciplineSerializer(discipline, many=True).data

    class Meta:
        model = DocumentOnline
        fields = (
            'link',
            'name',
            'owner',
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
        return obj.questions_document.count()

class DocumentOnlineSerializer(serializers.ModelSerializer):
    owner = UserDetailsSerializer(read_only=True)   
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
    questions_document = DocumentQuestionOnlineSerializer(many=True, source='documentquestiononline_set', required=False, read_only=True)
    document =  DocumentInfoSerializer(read_only= True)
    results =  ResultSerializer(many=True, required=False)
    questions_quantity = serializers.SerializerMethodField()
    types_questions = serializers.SerializerMethodField()
    media_questions = serializers.SerializerMethodField()
    application = serializers.SerializerMethodField()
    document_finish = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    review_score_doc = serializers.SerializerMethodField()
   
    class Meta:
        model = DocumentOnline
        fields = (
            'link',
            'name',
            'document',
            'questions_quantity',
            'owner',
            'create_date',
            'start_date',
            'finish_date',
            'duration',
            'questions_document',
            'results',
            'types_questions',
            'media_questions',
            'application',
            'document_finish',
            'status',
            'review_score_doc'
        )
    def get_review_score_doc(self, obj):
        results = Result.objects.filter(results=obj, student_answer__answer_text__isnull=False, student_answer__score_answer__isnull=True)
        if len(results) > 0:
            return False
        return True

    def get_questions_quantity(self, obj):
        return obj.questions_document.count()
    
    def get_types_questions(self, obj):
        questions = obj.documentquestiononline_set.all()
        dissertation = 0
        objective = 0

        for q in questions:
            if len(q.question.alternatives.all()) > 1:
                objective += 1
            else:
                dissertation += 1

        dic = {'dissertation_quantity': dissertation, 'objective_quantity': objective}
        return dic

    def get_media_questions(self, obj):
        questions = obj.documentquestiononline_set.all()
        object_count = 0

        for q in questions:
            object_count += len(q.question.learning_objects.all())
        return object_count
    
    def get_application(self, obj):
        questions = obj.documentquestiononline_set.all()
        count_exame = 0
        count_authoral = 0

        for q in questions:
            if q.question.source != None:
                count_exame += 1
            else:
                count_authoral += 1
        dic = { 'exam_quantity': count_exame, 'authoral_quantity':count_authoral}
        return dic
      
    def get_document_finish(self, obj):
        count = obj.results.count()
        return count
    
    def get_status(self, obj):
        now = datetime.datetime.now()
        if now > obj.finish_date.replace(tzinfo=None):
            return False
        else:
            return True
    
    def create(self, validated_data):
        questions_documents = self.context.get('request').data
        
        document = super().create(validated_data)

        if len(questions_documents['questions_document'])  > 0:
            count_questions = 0

            for q in questions_documents['questions_document']:
                if len(str(q['score'])) > 11:
                    raise serializers.ValidationError(_("Maximum number of digits in score is 10!"))
                count_questions += 1
                DocumentQuestionOnline.objects.create(document=document, question_id=q['question'], score=q['score'], order=count_questions)
    
        return DocumentOnline.objects.get_documentonline_prefetch().get(link=document.link)

    def update(self, instance, validated_data):
        questions_documents = self.context.get('request').data
        document = super().update(instance, validated_data)
        
        if len(questions_documents['questions_document'])  > 0:        
            for q in questions_documents['questions_document']:
                score = DocumentQuestionOnline.objects.get(id=q['id'])
                score.score = q['score']
                score.save()
    
        return DocumentOnline.objects.get_documentonline_prefetch().get(link=document.link)

class DocumentOnlineStudentSerializer(serializers.ModelSerializer):
    owner = UserDetailsSerializer(read_only=True)   
    questions_document = DocumentQuestionStudentSerializer(many=True, source='documentquestiononline_set', required=False)
    document =  DocumentInfoSerializer(read_only= True)
    types_questions = serializers.SerializerMethodField()
   
    class Meta:
        model = DocumentOnline
        fields = (
            'link',
            'name',
            'document',
            'owner',
            'create_date',
            'start_date',
            'finish_date',
            'duration',
            'questions_document',
            'types_questions',
        )
    
    def get_types_questions(self, obj):
        questions = obj.documentquestiononline_set.all()
        dissertation = 0
        objective = 0

        for q in questions:
            if len(q.question.alternatives.all()) > 1:
                objective += 1
            else:
                dissertation += 1

        dic = {'dissertation_quantity': dissertation, 'objective_quantity': objective}
        return dic

class DocumentOnlineListSerializer(serializers.ModelSerializer):
    owner = UserDetailsSerializer(read_only=True)   
    document =  DocumentInfoSerializer(read_only= True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = DocumentOnline
        fields = (
            'link',
            'name',
            'document',
            'owner',
            'create_date',
            'start_date',
            'finish_date',
            'duration',
            'status',
        )
    
    def get_status(self, obj):
        now = datetime.datetime.now()
        if now > obj.finish_date.replace(tzinfo=None):
            return False
        else:
            return True

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id',
            'description_task',
            'student_expectation',
            'teacher_expectation',
        )

class ActivitySerializer(serializers.ModelSerializer):
    owner = UserDetailsSerializer(read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)
       
    topics = TopicSimpleSerializer(read_only=True, many=True)
    learning_objects = LearningObjectSerializer(many=True, read_only=True)

    all_topics = serializers.SerializerMethodField('all_topics_serializer')
    def all_topics_serializer(self, obj):
        return TopicSimpleSerializer(obj.get_all_topics(), many=True).data

    tasks = TaskSerializer(many=True)

    tags = TagListSerializer(read_only=False, required=False, allow_null=True) 
    difficulty = serializers.CharField(read_only=False, required=True)

    learning_objects_ids = ModelListSerializer(write_only=True, allow_null=True, required=False, many=True, queryset=LearningObject.objects.all())
    topics_ids = ModelListSerializer(write_only=True, many=True, queryset=Topic.objects.all())
    disciplines_ids = ModelListSerializer(write_only=True, many=True, queryset=Discipline.objects.all())
    teaching_levels_ids = ModelListSerializer(write_only=True, many=True, queryset=TeachingLevel.objects.all())


    class Meta:
        model = Activity
        fields = (
            'id',
            'owner',
            'create_date',

            'learning_objects',
            'difficulty',
            'disciplines',
            'teaching_levels',
            'topics',
            'all_topics',

            'learning_objects_ids',
            'topics_ids',
            'disciplines_ids',
            'teaching_levels_ids',

            'tasks',

            'tags',  
            'labels', 
            'disabled',
            'secret',
        )

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

    def validate_year(self, value):
        if not value:
            return datetime.date.today().year
            
        if value > datetime.date.today().year:
            raise serializers.ValidationError(_("Year bigger than this year")) 
        return value

    def create(self, validated_data):
        # m2m
        tags = validated_data.pop('tags', None)
        tasks = validated_data.pop('tasks', None)

        if not tasks:
            raise serializers.ValidationError(_("Should contain at least one task"))

        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
          
        activity = super().create(validated_data)

        if tags != None:
            tags = [tag for tag in tags if tag.strip() != '']
            activity.tags.set(*tags, clear=True)

        if tasks != None:
            for t in tasks:
                Task.objects.create(activity=activity, **t)

        return Activity.objects.get_activities_prefetched().get(id=activity.id)

    def update(self, instance, validated_data):
        # m2m
        tags = validated_data.pop('tags', None)
        tasks = validated_data.pop('tasks', None)

        if not tasks:
            raise serializers.ValidationError(_("Should contain at least one task"))

        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)

        activity = super().update(instance, validated_data)    

        if tags != None:
            tags = [tag for tag in tags if tag.strip() != '']
            activity.tags.set(*tags, clear=True)

        if tasks != None:
            activity.tasks.all().delete()
            for t in tasks:
                Task.objects.create(activity=activity, **t)
                
        return Activity.objects.get_activities_prefetched().get(id=activity.id)

class ActivityLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label.activity_set.through
        fields = (
            'id',
            'activity',
            'label',
        )
        extra_kwargs = {
            'label' : { 'read_only' : True }
        }

    def validate_activity(self, data):
        if data.disabled:
            raise serializers.ValidationError(_("This activity is disabled"))
        return data
    
    def create(self, validated_data):
        label = validated_data['label']
        try:
            return label.activity_set.through.get(activity_id=validated_data['activity'].id)
        except:
            activityLabel = label.add_activity(validated_data['activity'])
            return activityLabel

class ActivityLabelListDetailSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer(read_only=True)
    label = LabelSerializer(read_only=True)

    class Meta:
        model = Label.activity_set.through
       
        fields = (
            'id',
            'activity',
            'label',
        )
        extra_kwargs = {
            'label' : { 'read_only' : True }
        }


class LinkClassPlanSerializer(serializers.ModelSerializer):    
    class Meta:
        model = ShareClassPlan
        fields = (
            'link',
        )  

class BnccSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bncc
        fields = (
            'id',
            'name',
        )

class StationMaterialSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer(required=False, read_only= True)
    document = DocumentListInfoSerializer(required=False, read_only= True)
    document_online = DocumentOnlineListSerializer(required=False, read_only= True)

    activity_ids = serializers.IntegerField(required=False, allow_null=True)
    document_ids = serializers.IntegerField(required=False, allow_null=True)
    document_online_ids = serializers.UUIDField(required=False, allow_null=True)
   
    class Meta:
        model = StationMaterial
        fields = (
            'id',
            'description_station',
            'name_station',
            'document',
            'document_online',
            'activity',

            'document_ids',
            'document_online_ids',
            'activity_ids',
        )
         
class ClassPlanPublicationSerializer(serializers.ModelSerializer):
    owner = UserDetailsSerializer(read_only=True)
    create_date = serializers.DateTimeField(format="%Y/%m/%d", required=False, read_only=True)

    topics = TopicSimpleSerializer(read_only=True, many=True)
    tags = TagListSerializer(read_only=False, required=False, allow_null=True) 
 
    documents = DocumentListInfoSerializer(many=True,read_only=True)
    documents_online = DocumentOnlineListSerializer(many=True, read_only=True)
    activities = ActivitySerializer(many=True, read_only=True)

    topics_ids = ModelListSerializer(write_only=True, many=True, queryset=Topic.objects.all())
    disciplines_ids = ModelListSerializer(write_only=True, many=True, queryset=Discipline.objects.all())
    teaching_levels_ids = ModelListSerializer(write_only=True, many=True, queryset=TeachingLevel.objects.all())
    bncc_ids = ModelListSerializer(write_only=True, many=True, queryset=Bncc.objects.all())
    teaching_years_ids = ModelListSerializer(write_only=True, many=True, queryset=TeachingYear.objects.all())

    documents_ids = ModelListSerializer(write_only=True, many=True, queryset=Document.objects.all())
    documents_online_ids = ModelListValueSerializer(write_only=True, many=True, queryset=DocumentOnline.objects.all())
    activities_ids = ModelListSerializer(write_only=True, many=True, queryset=Activity.objects.all())

    stations = StationMaterialSerializer(many=True)

    class Meta:
        model = ClassPlanPublication
        fields = (
            'id',
            'owner',
            'create_date',
            'name',

            'disciplines',
            'teaching_levels',
            'topics',
            'tags',
            'bncc',
            'teaching_years',

            'documents', 
            'documents_online',
            'activities',          

            'duration', 
            'phases',
            'content',
            'guidelines',

            'disabled',
            'plan_type',
            'stations',

            'topics_ids',
            'disciplines_ids',
            'teaching_levels_ids',
            'documents_ids',
            'documents_online_ids',
            'activities_ids',
            'teaching_years_ids',
            'bncc_ids',           
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
           
    def create(self, validated_data):
        stations = validated_data.pop('stations', None)
        tags = validated_data.pop('tags', None)

        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
        
        plan = super().create(validated_data)

        if tags != None:
            for t in [tag for tag in tags if tag != '']:
                plan.tags.add(t)
        
        if stations != None:
            for st in stations:
                es = StationMaterial.objects.create(plan=plan, name_station= st['name_station'], description_station=st['description_station'] )
                                
                if 'document_ids' in st:
                    es.document_id = st['document_ids']
                if 'document_online_ids' in st:
                    es.document_online_id = st['document_online_ids']
                if 'activity_ids' in st:
                    es.activity_id = st['activity_ids']
                es.save()
    
        return ClassPlanPublication.objects.get(id=plan.id)
    
    def update(self, instance, validated_data):
        documents_ids = validated_data.pop('documents_ids', None)
        documents_online_ids = validated_data.pop('documents_online_ids', None)
        activities_ids = validated_data.pop('activities_ids', None)
        tags = validated_data.pop('tags', None)
        stations = validated_data.pop('stations', None)
        bncc_ids = validated_data.pop('bncc_ids', None)

        for key in list(validated_data.keys()):
            if key.endswith('_ids'):
                validated_data[key[:-4]] = validated_data.pop(key)
        
        plan = super().update(instance, validated_data)

        if stations != None:
            plan.stations.all().delete()
            for st in stations:
                es = StationMaterial.objects.create(plan=plan, name_station= st['name_station'], description_station=st['description_station'] )
                                
                if 'document_ids' in st:
                    es.document_id = st['document_ids']
                if 'document_online_ids' in st:
                    es.document_online_id = st['document_online_ids']
                if 'activity_ids' in st:
                    es.activity_id = st['activity_ids']
                es.save()

        plan.documents.clear()
        if documents_ids != None:
            for d in documents_ids:
                plan.documents.add(d)
        
        plan.documents_online.clear()
        if documents_online_ids != None:
            for do in documents_online_ids:
                plan.documents_online.add(do)
        
        plan.activities.clear()
        if activities_ids != None:
            for d in activities_ids:
                plan.activities.add(d)
        
        if tags != None:
            tags = [tag for tag in tags if tag.strip() != '']
            plan.tags.set(*tags, clear=True)
        
        plan.bncc.clear()
        if bncc_ids != None:
            for b in bncc_ids:
                plan.bncc.add(b)
        
        return ClassPlanPublication.objects.get(id=plan.id)

class ListClassPlanActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassPlanPublication
        fields = (
            'id',
            'name',   
        )

class ShareClassPlanSerializer(serializers.ModelSerializer):
        documents_online = DocumentOnlineListSerializer(many=True, read_only=True)
        activities = ActivitySerializer(many=True, read_only=True)
        stations = StationMaterialSerializer(many=True)

        class Meta:
            model = ClassPlanPublication
            fields = (
                'name',
                'documents_online',
                'activities',          

                'guidelines',

                'disabled',
                'plan_type',
                'stations',  
            )
            depth = 1