# -*- coding: utf-8 -*-
import os
import time
import datetime
import operator
import csv 

from functools import reduce

from haystack.query import SearchQuerySet, SQ, AutoQuery
from haystack.inputs import Clean

from rest_framework import (generics, response, viewsets, status, mixins, 
                    exceptions, pagination, permissions)
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.response import Response

from django.db.models import Count, Q, Case, When, Subquery, OuterRef, IntegerField, Value, Prefetch, Max
from django.db.models.functions import Coalesce
from django.http import HttpResponse, FileResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from taggit.models import Tag

from masteraula.users.models import User

from .models import (Question, Document, Alternative, Discipline, TeachingLevel, DocumentQuestion, Header, 
                    Year, Source, Topic, LearningObject, Search, DocumentDownload, DocumentPublication, 
                    Synonym, Label, TeachingYear, ClassPlanPublication, StationMaterial, FaqCategory, DocumentOnline, DocumentQuestionOnline, Result, Task, Activity, Bncc,)

from .models import DocumentLimitExceedException

from .templatetags.search_helpers import prepare_document, stripaccents_str
from .docx_parsers import Question_Parser
from .docx_generator import Docx_Generator
from .docx_generator_aws import DocxGeneratorAWS
from .similarity import RelatedQuestions
from .search_indexes import SynonymIndex, TopicIndex, QuestionIndex, ActivityIndex
from .permissions import QuestionPermission, LearningObjectPermission, DocumentsPermission, HeaderPermission, DocumentDownloadPermission, LabelPermission, ClassPlanPermission
from . import serializers as serializers

current_milli_time = lambda: int(round(time.time() * 1000))

class DocumentPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10
    max_page_size = 80

class DocumentOnlinePagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10
    max_page_size = 80

class DocumentCardPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 16
    max_page_size = 64

class QuestionPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 16
    max_page_size = 64

class ActivityPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 16
    max_page_size = 64

class LearningObjectPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 16
    max_page_size = 64

class HeaderPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10
    max_page_size = 50

class TopicPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 54
    max_page_size = 106

class ClassPlanPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10
    max_page_size = 80

class QuestionSearchView(viewsets.ReadOnlyModelViewSet):   
    pagination_class = QuestionPagination
    serializer_class = serializers.QuestionSerializer
    permission_classes = (permissions.IsAuthenticated, QuestionPermission, ) 
     
    def paginate_queryset(self, search_queryset):
        page = super().paginate_queryset(search_queryset)
        questions_ids = [res.pk for res in page]

        queryset = Question.objects.get_questions_prefetched().filter(disabled=False, id__in=questions_ids).order_by('id')
        order = Case(*[When(id=id, then=pos) for pos, id in enumerate(questions_ids)])
        queryset = queryset.order_by(order)

        return queryset

    def get_queryset(self):
        text = self.request.GET.get('text', None)

        if not text:
            raise exceptions.ValidationError("Invalid search text")
        text = prepare_document(text)
        text = ' '.join([value for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3])
        
        if not text:
            raise exceptions.ValidationError("Invalid search text")

        search_queryset = QuestionIndex.filter_question_search(text, self.request.query_params)

        disciplines = self.request.query_params.getlist('disciplines', None)
        teaching_levels = self.request.query_params.getlist('teaching_levels', None)
        sources = self.request.query_params.getlist('sources', None)
        years = self.request.query_params.getlist('years', None)
        difficulties = self.request.query_params.getlist('difficulties', None)

        #Salvar os dados de busca	        
        obj = Search.objects.create(user=self.request.user, term=self.request.query_params['text'])	   
        obj.disciplines = disciplines
        obj.teaching_levels = teaching_levels
        obj.source = ', '.join(sources)
        obj.year = ', '.join(years)
        if difficulties:
            obj.difficulty = ', '.join(difficulties_texts)
        else:
            obj.difficulty = None
        obj.save()
        
        return search_queryset

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.QuestionSerializer
    pagination_class = QuestionPagination
    permission_classes = (permissions.IsAuthenticated, QuestionPermission)

    def get_queryset(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return Question.objects.all()

        queryset = Question.objects.filter_questions_request(self.request.query_params)
        if self.action == 'list':
            queryset = queryset.filter(disabled=False).order_by('id')

        return queryset.order_by('id')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, pk=None):
        question = self.get_object()
        question.disabled = True
        question.save()
        return Response(status = status.HTTP_204_NO_CONTENT)
    
    def retrieve(self, request, pk=None):
        question = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_question = self.serializer_class(question, context=self.get_serializer_context())

        documents = Document.objects.filter(questions__id=pk, owner=request.user, disabled=False).order_by('create_date')
        serializer_documents = serializers.ListDocumentQuestionSerializer(documents, many = True)

        return_data = serializer_question.data
        return_data['documents'] = serializer_documents.data

        related_material = RelatedQuestions().similar_questions(question)
        order_questions = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(related_material[0])])
        order_activities = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(related_material[1])])

        questions_object = Question.objects.get_questions_prefetched().filter(id__in=related_material[0]).order_by(order_questions)
        serializer_questions = serializers.QuestionSerializer(questions_object, many=True, context=self.get_serializer_context())

        activities_object = Activity.objects.get_activities_prefetched().filter(id__in=related_material[1]).order_by(order_activities)
        serializer_activities = serializers.ActivitySerializer(activities_object, many=True, context=self.get_serializer_context())

        return_data['related_questions'] = serializer_questions.data
        return_data['related_activities'] = serializer_activities.data
    
        return Response(return_data)

    @detail_route(methods=['put'], permission_classes=(permissions.IsAuthenticated, permissions.DjangoModelPermissions))
    def tag_question(self, request, pk=None):
        question = get_object_or_404(self.get_queryset(), pk=pk)

        serializer_question = serializers.QuestionTagEditSerializer(question, data=request.data)
        serializer_question.is_valid(raise_exception=True)
        new_question = serializer_question.save()
        serializer_question = self.serializer_class(new_question)

        return Response(serializer_question.data, status=status.HTTP_201_CREATED)

class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Discipline.objects.all().order_by('name')
    serializer_class = serializers.DisciplineSerializer
    pagination_class = None
    
class TeachingLevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeachingLevel.objects.all().order_by('id')
    serializer_class = serializers.TeachingLevelSerializer
    pagination_class = None

class YearViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Year.objects.all().order_by('name')
    serializer_class = serializers.YearSerializer
    pagination_class = None
    
class SourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Source.objects.all().order_by('name')
    serializer_class = serializers.SourceSerializer
    pagination_class = None

class BnccViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bncc.objects.all().order_by('id')
    serializer_class = serializers.BnccSerializer
    pagination_class = None

class SynonymViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Synonym.objects.all()
    serializer_class = serializers.SynonymSerializer
    pagination_class = None

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = serializers.TopicListSerializer
    pagination_class = TopicPagination

    def get_queryset(self, *args, **kwargs):
        order_field = self.request.query_params.get('order_field', None)
        order_type = self.request.query_params.get('order', None)
        disciplines = self.request.query_params.getlist('disciplines', None)
        
        queryset = self.queryset.annotate(num_questions=Count('question'))

        if disciplines:
            queryset = queryset.filter(discipline__in = disciplines)

        if order_type:
            if order_field == 'name':
                if order_type =='desc':
                    queryset = queryset.order_by('-name')
                else:
                    queryset = queryset.order_by('name')

            elif order_field == 'num_questions':
                if order_type == 'desc':
                    queryset = queryset.order_by('-num_questions')
                else:
                    queryset = queryset.order_by('num_questions')
            return queryset
        return queryset.annotate(num_questions=Count('question')).order_by('-num_questions')
      
    @list_route(methods=['get'])
    def related_topics(self, request):
        text = request.query_params.get('text', None)
        topics = request.query_params.getlist('topics', [])
        activities = request.query_params.getlist('activities', None)
       
        if text:
            text = prepare_document(text)
            text = ' '.join([value for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3])
            
            if not text:
                raise exceptions.ValidationError("Invalid search text")

            if activities:
                search_queryset = ActivityIndex.filter_activity_search(text, request.query_params)
                questions_ids = [q.pk for q in search_queryset[:]]
                questions = Activity.objects.prefetch_related(
                    Prefetch('topics', queryset=Topic.objects.only('id', 'name'))
                ).filter(id__in=questions_ids)

            else:
                search_queryset = QuestionIndex.filter_question_search(text, request.query_params)
                questions_ids = [q.pk for q in search_queryset[:]]
                
                questions = Question.objects.prefetch_related(
                    Prefetch('topics', queryset=Topic.objects.only('id', 'name'))
                ).filter(id__in=questions_ids)

            topics_dict = {}
            for question in questions.only('topics__id', 'topics__name'):
                for topic in question.topics.all():
                    if topic.id in topics_dict:
                        topics_dict[topic.id]['num_questions'] += 1
                    else:
                        topics_dict[topic.id] = {'id' : topic.id, 'name' : topic.name, 'num_questions' : 1}

            topics_list = []
            for key in topics_dict:
                if str(key) not in topics:
                    topics_list.append(topics_dict[key])
            queryset = sorted(topics_list, key=lambda x : x['num_questions'], reverse=True)

        else:
            if activities:
                questions = Activity.objects.filter_activities_request(self.request.query_params).filter(disabled=False)
            else:
                questions = Question.objects.filter_questions_request(self.request.query_params).filter(disabled=False)

            questions = questions.filter(topics=OuterRef('pk')).values('topics')
            total_question = questions.annotate(cnt=Count('pk')).values('cnt')
            queryset = Topic.objects.exclude(id__in=topics).annotate(num_questions=Coalesce(Subquery(total_question, output_field=IntegerField()), Value(0)))
            queryset = queryset.order_by('-num_questions').values('name', 'num_questions', 'id')
            queryset = [res for res in queryset[:20] if res['num_questions'] > 0]

        serializer_topics = serializers.TopicListSerializer(queryset[:20], many = True)
        return Response({
            'topics' : serializer_topics.data,
            'more' : len(queryset) > 20
        })

class LearningObjectSearchView(viewsets.ReadOnlyModelViewSet):
    pagination_class = LearningObjectPagination
    serializer_class = serializers.LearningObjectSerializer
    permission_classes = (permissions.IsAuthenticated, LearningObjectPermission, )

    def paginate_queryset(self, search_queryset):
        search_queryset = search_queryset.load_all()

        page = super().paginate_queryset(search_queryset)
        queryset = [res.object for res in page]

        return queryset

    def get_queryset(self):
        page = self.request.GET.get('page', None)
        text = self.request.GET.get('text', None)
        filters = self.request.GET.getlist('filters', None)

        try:
            page_no = int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            raise exceptions.ValidationError("Not a valid number for page.")

        if page_no < 1:
            raise exceptions.ValidationError("Pages should be 1 or greater.")

        if not text:
            raise exceptions.ValidationError("Invalid search text")

        text = prepare_document(text)
        text = ' '.join([value for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3])
        
        if not text:
            raise exceptions.ValidationError("Invalid search text")

        params = {}
        if filters:
            params['object_types'] = filters

        start_offset = (page_no - 1) * 16

        # The following queries are to apply the weights of haystack boost
        queries = [SQ(tags=Clean(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        query = queries.pop()
        for item in queries:
            query |= item
        queries = [SQ(source=Clean(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item
        queries = [SQ(text_object=Clean(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item

        search_queryset = SearchQuerySet().models(LearningObject).filter(**params).filter(SQ(content=Clean(text)) | (
            SQ(content=Clean(text)) & query
        ))

        # return self.gen_queryset(search_queryset, start_offset)
        return search_queryset

class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.LabelSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated, LabelPermission,)

    def get_queryset(self):
        queryset = Label.objects.filter(owner=self.request.user).order_by('name')
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @detail_route(methods=['post'])
    def add_question(self, request, pk=None):
        label = self.get_object()
        serializer = serializers.QuestionLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question_label = serializer.save(label=label)
        question_label.question = Question.objects.get_questions_prefetched().get(id=question_label.question_id)

        list_label = serializers.QuestionLabelListDetailSerializer(question_label)

        headers = self.get_success_headers(list_label.data)
        return Response(list_label.data, status=status.HTTP_201_CREATED, headers=headers)
       
    @detail_route(methods=['post'])
    def remove_question(self, request, pk=None):
        label = self.get_object()

        serializer = serializers.QuestionLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']

        label.remove_question(question)

        return Response(status = status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def add_activity(self, request, pk=None):
        label = self.get_object()
        serializer = serializers.ActivityLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity_label = serializer.save(label=label)
        activity_label.activity = Activity.objects.get_activities_prefetched().get(id=activity_label.activity_id)

        list_label = serializers.ActivityLabelListDetailSerializer(activity_label)

        headers = self.get_success_headers(list_label.data)
        return Response(list_label.data, status=status.HTTP_201_CREATED, headers=headers)
       
    @detail_route(methods=['post'])
    def remove_activity(self, request, pk=None):
        label = self.get_object()

        serializer = serializers.ActivityLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = serializer.validated_data['activity']
        label.remove_activity(activity)

        return Response(status = status.HTTP_204_NO_CONTENT)

class LearningObjectViewSet(viewsets.ModelViewSet):
    queryset = LearningObject.objects.all()
    serializer_class = serializers.LearningObjectSerializer
    pagination_class = LearningObjectPagination
    permission_classes = (permissions.IsAuthenticated, LearningObjectPermission, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, pk=None):
        learning_object = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_learningobject = self.serializer_class(learning_object, context=self.get_serializer_context())

        questions_object = Question.objects.get_questions_prefetched().filter(learning_objects__id=pk).filter(disabled=False).order_by('-create_date').order_by('?')
        activities_object = Activity.objects.get_activities_prefetched().filter(learning_objects__id=pk).filter(disabled=False).order_by('-create_date').order_by('?')

        if len(questions_object) >= 4 and len(activities_object) >= 4:
            questions_object = questions_object[:4]
            activities_object = activities_object[:4]
        else:
            if len(questions_object) < 4:
                activities_object = activities_object[:(8 - len(questions_object))]
            if len(activities_object) < 4:
                questions_object = questions_object[:(8 - len(activities_object))]

        serializer_questions = serializers.QuestionSerializer(questions_object, many = True, context=self.get_serializer_context())
        serializer_activities = serializers.ActivitySerializer(activities_object, many = True, context=self.get_serializer_context())

        return_data = serializer_learningobject.data
        return_data['questions'] = serializer_questions.data
        return_data['activities'] = serializer_activities.data

        return Response(return_data)

    def get_queryset(self):
        queryset = LearningObject.objects.all().order_by('id')
        filters = self.request.query_params.getlist('filters', None)
       
        if filters:
            queryset = queryset.filter(object_types__contains=filters)
            
        return queryset.filter()

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = (DocumentsPermission, )

    def get_queryset(self):
        queryset = Document.objects.get_questions_prefetched().filter(owner=self.request.user, disabled=False)
        if (self.action=='generate_list'):
            queryset = Document.objects.get_generate_document().filter(owner=self.request.user)
        if self.action == 'add_question' or self.action == 'remove_question' or self.action == 'update' or self.action == 'partial_update':
            queryset = Document.objects.filter(owner=self.request.user, disabled=False)
        if self.action == 'copy_document':
            queryset = Document.objects.get_questions_prefetched() \
                .filter(Q(documentpublication__isnull=False)|Q(owner=self.request.user)).filter(disabled=False).distinct()
        if self.action == 'my_documents_cards':
            queryset = Document.objects.filter(owner=self.request.user, disabled=False, questions__isnull=False).distinct()
        if self.action == 'retrieve':
            queryset = Document.objects.get_questions_prefetched().filter(owner=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.DocumentListSerializer
        if self.action == 'create':
            return serializers.DocumentCreatesSerializer
        return serializers.DocumentDetailSerializer   

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, pk=None):
        document = self.get_object()
        document.update(disabled=True)
        return Response(status = status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def copy_document(self, request, pk=None):
        obj = self.get_object()
        questions = [dq.question for dq in obj.documentquestion_set.all().order_by('order')]
                                       
        obj.pk = None
        obj.name = obj.name + ' (Cópia)'
        obj.owner = self.request.user
        obj.save()

        new_questions = []
        for count, q in enumerate(questions):
            if q.disabled == False:
                new_questions.append(DocumentQuestion(document=obj, question=q, order=count))
        DocumentQuestion.objects.bulk_create(new_questions) 

        new_obj = Document.objects.get(pk=obj.id)
        serializer = serializers.DocumentCreatesSerializer(new_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @detail_route(methods=['post'])
    def add_question(self, request, pk=None):
        document = self.get_object()
        serializer = serializers.DocumentQuestionSerializer(data={ **request.data, 'document' : document })
        serializer.is_valid(raise_exception=True)

        try:
            document_question = document.add_question(serializer.validated_data['question'])
        except DocumentLimitExceedException as err:
            raise exceptions.PermissionDenied(str(err))

        document_question = DocumentQuestion.objects.get_questions_prefetched().get(id=document_question.id)
        list_document = serializers.DocumentQuestionListDetailSerializer(document_question)

        headers = self.get_success_headers(list_document.data)
        return Response(list_document.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @detail_route(methods=['post'])
    def remove_question(self, request, pk=None):
        document = self.get_object()
        serializer = serializers.DocumentQuestionDestroySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']
        document.remove_question(question)

        return Response(status = status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get'])
    def my_documents(self, request):
        order_field = request.query_params.get('order_field', None)
        order_type = request.query_params.get('order', None)
        
        queryset = self.get_queryset()
        if order_field == 'date':
            if order_type == 'desc':
                queryset = queryset.order_by('-create_date')
            else:
                queryset = queryset.order_by('create_date')

        elif order_field == 'name':
            if order_type =='desc':
                queryset = queryset.order_by('-name')
            else:
                queryset = queryset.order_by('name')

        elif order_field =='question_number':
            if order_type =='desc':
                queryset = queryset.annotate(num_questions = Count('questions')).order_by('-num_questions')
            else:
                queryset = queryset.annotate(num_questions = Count('questions')).order_by('num_questions')

        else:
            queryset = queryset.order_by('-create_date')

        self.pagination_class = DocumentPagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.DocumentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.DocumentListSerializer(queryset, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['get'])
    def my_documents_cards(self, request):       
        queryset = self.get_queryset().order_by("id")
       
        self.pagination_class = DocumentCardPagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.DocumentListInfoSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.DocumentListInfoSerializer(queryset, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['get'], permission_classes=[permissions.IsAuthenticated, DocumentDownloadPermission, ])
    def generate_list(self, request, pk=None):
        """
        Generate a docx file containing all the list.
        """
        document = self.get_object()
        if document.questions.count() > 30:
            raise exceptions.PermissionDenied('Documento não pode ter mais de 30 questões.')
        document_generator = DocxGeneratorAWS()

        try:
            flags = request.query_params
            answers = 'answers' in flags and flags['answers'] == 'true'
            sources = 'sources' in flags and flags['sources'] == 'true'

            document_generator.generate_document(document, answers, sources)

            DocumentDownload.objects.create(user=self.request.user, 
                                            document=document, 
                                            answers=answers)

            response = FileResponse(
                open(document_generator.docx_name + '.docx', "rb"), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = 'attachment; filename="' + document_generator.docx_name + '.docx"'
        except:
            response = HttpResponseBadRequest()
        finally:
            if os.path.exists(document_generator.docx_name + '.docx'):
                os.remove(document_generator.docx_name + '.docx')
            if os.path.exists(document_generator.docx_name + '.html'):
                os.remove(document_generator.docx_name + '.html')

            return response

class DocumentDownloadViewSet(viewsets.ModelViewSet):
    def get_queryset(self): 
        date = datetime.datetime.now()
        return DocumentDownload.objects.filter(user=self.request.user).filter(download_date__month=date.month)

    def get_serializer_class(self):
        return serializers.DocumentDownloadSerializer
    
    def list(self, request, *args, **kwargs):
        response = super(DocumentDownloadViewSet, self).list(request, *args, **kwargs)
        try:
            total = DocumentDownload.objects.filter(user=self.request.user).count()
            response.data['total_downloads'] = total
        except:
            pass
        return response

class DocumentPublicationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    def get_queryset(self):
        return DocumentPublication.objects.filter(document__disabled=False)

    def get_serializer_class(self):
        return serializers.DocumentDetailPublicationSerializer

    def retrieve(self, request, pk=None):
        publication = self.get_object()
        document = Document.objects.get_questions_prefetched().get(id=publication.document_id)
        document_data = self.get_serializer_class()(document).data

        if not self.request.user.is_authenticated:
            for question in document_data['questions']:
                question['question'].pop('alternatives', None)
    
        return Response(document_data)

    @detail_route(methods=['get'])
    def share(self, request, pk=None):
        """
        Generate a docx file containing all the list.
        """
        publication = self.get_object()
        document = Document.objects.get_questions_prefetched().get(id=publication.document_id)

        return TemplateResponse(request, 'questions/share_publication.html', {'document' : document, 'slug': publication.id }) 

class HeaderViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.HeaderSerializer
    pagination_class = HeaderPagination
    permission_classes = (HeaderPermission,)

    def get_queryset(self):
        queryset = Header.objects.filter(owner=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @list_route(methods=['get'])
    def list_headers(self, request):
        queryset = self.get_queryset().order_by('name')
        serializer = serializers.HeaderListSerializer(queryset, many=True)
        return Response(serializer.data)    
    
    @list_route(methods=['get'])
    def my_headers(self, request):
        order_field = request.query_params.get('order_field', None)
        order_type = request.query_params.get('order', None)
        
        if order_field == 'name':
            if order_type == 'desc':
                queryset = Header.objects.filter(owner=self.request.user).order_by('-name')
            else:
                queryset = Header.objects.filter(owner=self.request.user).order_by('name')

        elif order_field == 'discipline':
            if order_type =='desc':
                queryset = Header.objects.filter(owner=self.request.user).order_by('-discipline_name')
            else:
                queryset = Header.objects.filter(owner=self.request.user).order_by('discipline_name')

        elif order_field =='institution':
            if order_type =='desc':
                queryset = Header.objects.filter(owner=self.request.user).order_by('-institution_name')
            else:
                queryset = Header.objects.filter(owner=self.request.user).order_by('institution_name')

        elif order_field =='teacher':
            if order_type =='desc':
                queryset = Header.objects.filter(owner=self.request.user).order_by('-professor_name')
            else:
                queryset = Header.objects.filter(owner=self.request.user).order_by('professor_name')

        else:
            queryset = Header.objects.filter(owner=self.request.user).order_by('name')

        self.pagination_class = HeaderPagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.HeaderSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.HeaderSerializer(queryset, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AutocompleteSearchViewSet(viewsets.ViewSet):

    index_models = [Synonym, Topic]
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        q = request.GET.get('q', None)
        topics = self.request.query_params.getlist('topics', None)

        if not q or len(q) < 3:
            raise exceptions.ValidationError("'q' parameter required with at least 3 of length")
            
        q = stripaccents_str(q)
        queryset = SearchQuerySet().models(Topic, Synonym).autocomplete(term_auto=q).load_all()

        synonym_qs = []
        topic_qs = []

        for q in queryset[:]:
            if q.model_name == 'synonym':
                synonym_qs.append(q.object)
            else:
                topic_qs.append(q.object)

        synonym_serializer = serializers.SynonymSerializer(synonym_qs, many=True)
        topic_serialzier = serializers.TopicSimplestSerializer(topic_qs, many=True)

        return Response({
            'synonyms': synonym_serializer.data,
            'topics': topic_serialzier.data
        })

class AutocompleteSearchBnccViewSet(viewsets.ViewSet):

    index_models = [Bncc]
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        q = request.GET.get('q', None)
        bncc = self.request.query_params.getlist('bncc', None)

        if not q or len(q) < 3:
            raise exceptions.ValidationError("'q' parameter required with at least 3 of length")
            
        queryset = SearchQuerySet().models(Bncc).autocomplete(term_auto=q).load_all()
        bncc_qs = []

        for q in queryset[:]:
            bncc_qs.append(q.object)
        bncc_serialzier = serializers.BnccSerializer(bncc_qs, many=True)

        return Response(bncc_serialzier.data)

class TeachingYearViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeachingYear.objects.all()
    serializer_class = serializers.TeachingYearSerializer
    pagination_class = None

class ClassPlanPublicationViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ClassPlanPublicationSerializer
    pagination_class = ClassPlanPagination
    # permission_classes = (permissions.IsAuthenticated, ClassPlanPermission, )

    def get_queryset(self):
        # queryset = ClassPlanPublication.objects.get_classplan_prefetched().filter(owner=self.request.user, disabled=False)
        queryset = ClassPlanPublication.objects.filter()
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def destroy(self, request, pk=None):
        plan = self.get_object()
        plan.disabled = True
        plan.save()
        return Response(status = status.HTTP_204_NO_CONTENT)
    
    @list_route(methods=['get'])
    def my_plans(self, request):
        order_field = request.query_params.get('order_field', None)
        order_type = request.query_params.get('order', None)

        queryset = self.get_queryset()
        if order_field == 'create_date':
            if order_type == 'desc':
                queryset = queryset.order_by('-create_date')
            else:
                queryset = queryset.order_by('create_date')

        elif order_field == 'name':
            if order_type =='desc':
                queryset = queryset.order_by('-name')
            else:
                queryset = queryset.order_by('name')
        
        elif order_field == 'duration':
            if order_type =='desc':
                queryset = queryset.order_by('-duration')
            else:
                queryset = queryset.order_by('duration')
        
        elif order_field == 'disciplines':
            if order_type =='desc':
                queryset = queryset.annotate(order_temp=Max("disciplines__name")).order_by("-order_temp") 
            else:
                queryset = queryset.annotate(order_temp=Max("disciplines__name")).order_by("order_temp")

        else:
            queryset = queryset.order_by('-create_date')

        self.pagination_class = ClassPlanPagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.ClassPlanPublicationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.ClassPlanPublicationSerializer(queryset, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    def copy_plan(self, request, pk=None):
        obj = self.get_object()
        class_plan = ClassPlanPublication.objects.filter(id=obj.id).values().first()  
        class_plan.update({'pk': None, 'name': obj.name + ' (Cópia)', 'owner': self.request.user, 'owner_id': self.request.user.id})
        new_class_plan = ClassPlanPublication.objects.create(**class_plan)

        new_class_plan.topics.add(*obj.topics.all())
        new_class_plan.bncc.add(*obj.bncc.all())
        new_class_plan.teaching_levels.add(*obj.teaching_levels.all())
        new_class_plan.teaching_years.add(*obj.teaching_years.all())
        new_class_plan.disciplines.add(*obj.disciplines.all())
        new_class_plan.tags.add(*obj.tags.all())

        for d in obj.documents.all():
            if d.disabled == False:
                doc = Document.objects.filter(id=d.id).values().first()  
                doc.update({'id': None})
                duplicate = Document.objects.create(**doc)
                new_class_plan.documents.add(duplicate)

                new_questions = []
                for count, q in enumerate(obj.documentquestion_set.all().order_by('order')):
                    if q.disabled == False:
                        new_questions.append(DocumentQuestion(document=duplicate, question=q, order=count+1))
                DocumentQuestion.objects.bulk_create(new_questions) 

        for do in obj.documents_online.all():
            doc_online = DocumentOnline.objects.filter(link=do.link).values().first()  
            doc_online.update({'link': None})
            duplicate = DocumentOnline.objects.create(**doc_online)
            new_class_plan.documents_online.add(duplicate)

            new_questions = []
            for count, q in enumerate(obj.documentquestiononline_set.all()):
                if q.disabled == False:
                    new_questions.append(DocumentQuestionOnline(document=duplicate, question=q.question, order=count+1, score=q.score))
            DocumentQuestionOnline.objects.bulk_create(new_questions) 
        
        for a in obj.activities.all():
            if a.disabled == False:
                new_class_plan.activities.add(a)

        new_stations = []
        for st in obj.stations.all():
            document = None
            if st.document:
                doc = Document.objects.filter(id=st.document.id).values().first()  
                doc.update({'id': None})
                doc_duplicate = Document.objects.create(**doc)
                document = doc_duplicate

                new_questions = []
                for count, q in enumerate(st.document.documentquestion_set.all()):
                    if not q.question.disabled:
                        new_questions.append(DocumentQuestion(document=doc_duplicate, question=q.question, order=count+1))
                DocumentQuestion.objects.bulk_create(new_questions) 

            document_online = None
            if st.document_online:
                doc_online = DocumentOnline.objects.filter(link=st.document_online.link).values().first()  
                doc_online.update({'link': None})
                online_duplicate = DocumentOnline.objects.create(**doc_online)
                document_online = online_duplicate

                new_questions = []
                for count, q in enumerate(st.document_online.documentquestiononline_set.all()):
                    if not q.question.disabled:
                        new_questions.append(DocumentQuestionOnline(document=online_duplicate, question=q.question, order=count+1, score=q.score))
                DocumentQuestionOnline.objects.bulk_create(new_questions) 
            
            activity = None
            if st.activity:
                activity = st.activity

            new_stations.append(StationMaterial(name= st.name, description_station=st.description_station, activity=activity, document_online=document_online, document=document, plan=new_class_plan))
        StationMaterial.objects.bulk_create(new_stations)  

        serializer = serializers.ClassPlanPublicationSerializer(new_class_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class FaqCategoryViewSet(viewsets.ModelViewSet):
    queryset = FaqCategory.objects.all()
    serializer_class = serializers.FaqCategorySerializer    
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,) 

class DocumentOnlineViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DocumentOnlineSerializer    
    pagination_class = DocumentOnlinePagination

    def get_queryset(self):
        queryset = DocumentOnline.objects.get_documentonline_prefetch()

        if self.action == 'list':
            queryset = queryset.filter(document=self.request.query_params['id'])
        return queryset.order_by('name')

    def perform_create(self, serializer):
        document = Document.objects.get(id=self.request.query_params['id'])
        serializer.save(owner=self.request.user, document=document)
    
    @list_route(methods=['get'])
    def my_documents_online(self, request):
        order_field = request.query_params.get('order_field', None)
        order_type = request.query_params.get('order', None)
        
        queryset = self.get_queryset().filter(document=self.request.query_params['id'])
        if order_field == 'name':
            if order_type =='desc':
                queryset = queryset.order_by('-name')
            else:
                queryset = queryset.order_by('name')

        elif order_field =='question_number':
            if order_type =='desc':
                queryset = queryset.annotate(num_questions = Count('questions_document')).order_by('-num_questions')
            else:
                queryset = queryset.annotate(num_questions = Count('questions_document')).order_by('num_questions')

        elif order_field =='result':
            if order_type =='desc':
                queryset = queryset.annotate(num_results = Count('results')).order_by('-num_results')
            else:
                queryset = queryset.annotate(num_results = Count('results')).order_by('num_results')

        else:
            queryset = queryset.order_by('name')

        self.pagination_class = DocumentOnlinePagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.DocumentOnlineSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.DocumentOnlineSerializer(queryset, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['get'], permission_classes=(permissions.IsAuthenticatedOrReadOnly,))
    def document_student(self, request, pk=None):
        document = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_document = serializers.DocumentOnlineStudentSerializer(document)

        return Response(serializer_document.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['get'], permission_classes=(permissions.IsAuthenticatedOrReadOnly,))
    def check_document(self, request, pk=None):
        document = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_document = serializers.DocumentOnlineListSerializer(document)

        return Response(serializer_document.data, status=status.HTTP_201_CREATED)
    
    @detail_route(methods=['post'])
    def copy_document(self, request, pk=None):
        obj = self.get_object()
        questions = [dq for dq in obj.questions_document.all()]

        obj.pk = None
        obj.name = obj.name + ' (Cópia)'
        obj.owner = self.request.user
        obj.save()
        
        new_questions = []
        for count, q in enumerate(questions):
            if q.disabled == False:
                dq = DocumentQuestionOnline.objects.get(question=q.id, document=pk)
                new_questions.append(DocumentQuestionOnline(document=obj, question=q, order=count, score=dq.score))
        DocumentQuestionOnline.objects.bulk_create(new_questions) 

        new_obj = DocumentOnline.objects.get(pk=obj.pk)
        serializer = serializers.DocumentOnlineSerializer(new_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['get'], permission_classes=(permissions.IsAuthenticated,))
    def generate_list(self, request, pk=None):
        document_online = self.get_object()
        # Nome aleatorio para nao causar problemas
        file_name =  pk + str(current_milli_time()) 

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + file_name + '.csv"'
        writer = csv.writer(response, delimiter =",", quoting=csv.QUOTE_MINIMAL)
        title = ["Aluno","Série","Data","Duração(min)","Pontuação Total"]

        for i, t in enumerate(document_online.questions_document.all()):
                i = i + 1     
                if len(t.alternatives.all()) == 0: 
                    title.append('Q' + str(i))
                else:
                    question_item = 'a'
                    for al in t.alternatives.all():
                        if al.is_correct:
                            value = question_item
                        question_item = chr(ord(question_item) + 1)
                    title.append('Q' + str(i) + '('+ str(value) + ')')
                title.append('P' + str(i))
        writer.writerow(title)

        for result in document_online.results.all():
            duration = divmod((result.finish - result.start).seconds, 60)
            count_score = 0
            answer = []

            for i, t in enumerate(result.student_answer.all()):
                if t.answer_alternative != None:
                    question_item = 'a'
                    for al in t.student_question.question.alternatives.all():
                        if t.answer_alternative.id == al.id:
                            value = question_item
                        question_item = chr(ord(question_item) + 1)
                    answer.append(value)

                else:
                    answer.append(t.answer_text)
                
                if t.score_answer == None:
                     answer.append(0.00)
                else:
                     answer.append(t.score_answer)
                                            
                if t.score_answer:
                    count_score = count_score + t.score_answer

            data = ([
                result.student_name,
                result.student_levels,
                result.start.strftime("%d/%m/%Y"),
                duration[0],
                count_score       
                ])
            
            for a in answer:
                data.append(a)
            writer.writerow(data)
       
        return response

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all().order_by('-id')
    serializer_class = serializers.ResultSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        document = DocumentOnline.objects.get(link=self.request.query_params['link'])
        serializer.save(finish=datetime.datetime.now(), results= document)

class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ActivitySerializer
    pagination_class = ActivityPagination
    permission_classes = (permissions.IsAuthenticated, QuestionPermission)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return Activity.objects.all()

        queryset = Activity.objects.filter_activities_request(self.request.query_params)
        if self.action == 'list':
            queryset = queryset.filter(disabled=False).order_by('id')
        return queryset.order_by('id')
    
    def retrieve(self, request, pk=None):
        activity = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_activity = self.serializer_class(activity, context=self.get_serializer_context())

        return_data = serializer_activity.data

        related_material = RelatedQuestions().similar_questions(activity, activity=True)
        order_questions = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(related_material[0])])
        order_activities = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(related_material[1])])

        questions_object = Question.objects.get_questions_prefetched().filter(id__in=related_material[0]).order_by(order_questions)
        serializer_questions = serializers.QuestionSerializer(questions_object, many=True, context=self.get_serializer_context())

        activities_object = Activity.objects.get_activities_prefetched().filter(id__in=related_material[1]).order_by(order_activities)
        serializer_activities = serializers.ActivitySerializer(activities_object, many=True, context=self.get_serializer_context())

        return_data['related_questions'] = serializer_questions.data
        return_data['related_activities'] = serializer_activities.data
    
        return Response(return_data)
    
    def destroy(self, request, pk=None):
        activity = self.get_object()
        activity.disabled = True
        activity.save()
        return Response(status = status.HTTP_204_NO_CONTENT)

class ActivitySearchView(viewsets.ReadOnlyModelViewSet):   
    pagination_class = ActivityPagination
    serializer_class = serializers.ActivitySerializer
    permission_classes = (permissions.IsAuthenticated,) 
     
    def paginate_queryset(self, search_queryset):
        page = super().paginate_queryset(search_queryset)
        activities_ids = [res.pk for res in page]

        queryset = Activity.objects.get_activities_prefetched().filter(disabled=False, id__in=activities_ids).order_by('id')
        order = Case(*[When(id=id, then=pos) for pos, id in enumerate(activities_ids)])
        queryset = queryset.order_by(order)

        return queryset

    def get_queryset(self):
        text = self.request.GET.get('text', None)

        if not text:
            raise exceptions.ValidationError("Invalid search text")
        text = prepare_document(text)
        text = ' '.join([value for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3])
        
        if not text:
            raise exceptions.ValidationError("Invalid search text")

        search_queryset = ActivityIndex.filter_activity_search(text, self.request.query_params)

        disciplines = self.request.query_params.getlist('disciplines', None)
        teaching_levels = self.request.query_params.getlist('teaching_levels', None)
        difficulties = self.request.query_params.getlist('difficulties', None)
        
        return search_queryset
