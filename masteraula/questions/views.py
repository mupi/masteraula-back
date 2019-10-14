# -*- coding: utf-8 -*-
from django.http import HttpResponse, FileResponse, HttpResponseBadRequest
from haystack.query import SearchQuerySet, SQ, AutoQuery

from rest_framework import (generics, response, viewsets, status, mixins, 
                    exceptions, pagination, permissions)

from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.response import Response

from django.db.models import Count, Q, Case, When
from django.shortcuts import get_object_or_404
from django.core.exceptions import FieldError

from taggit.models import Tag

from masteraula.users.models import User
from masteraula.questions.templatetags.search_helpers import stripaccents

from .models import (Question, Document, Discipline, TeachingLevel, DocumentQuestion, Header,
                    Year, Source, Topic, LearningObject, Search, DocumentDownload, DocumentPublication)

from .templatetags.search_helpers import stripaccents
from .docx_parsers import Question_Parser
from .docx_generator import Docx_Generator
from .docx_generator_aws import DocxGeneratorAWS
from .similarity import RelatedQuestions
from .permissions import QuestionPermission, LearningObjectPermission, DocumentsPermission, HeaderPermission
from . import serializers as serializers

import os
import time
import operator
from functools import reduce

current_milli_time = lambda: int(round(time.time() * 1000))

class DocumentPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10
    max_page_size = 80

class QuestionPagination(pagination.PageNumberPagination):
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

class QuestionSearchView(viewsets.ReadOnlyModelViewSet):   
    pagination_class = QuestionPagination
    serializer_class = serializers.QuestionSerializer
    permission_classes = (permissions.IsAuthenticated, QuestionPermission, )
     
    def paginate_queryset(self, search_queryset):
        search_queryset = search_queryset.load_all()

        page = super().paginate_queryset(search_queryset)
        questions_ids = [res.object.id for res in page]

        queryset = Question.objects.get_questions_prefetched().filter(disabled=False, id__in=questions_ids).order_by('id')
        order = Case(*[When(id=id, then=pos) for pos, id in enumerate(questions_ids)])
        queryset = queryset.order_by(order)

        return queryset

    def get_queryset(self):
        text = self.request.GET.get('text', None)
        if not text:
            raise FieldError("Invalid search text")
        text = stripaccents(text)
        text = ' '.join([value for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3])
        if not text:
            raise FieldError("Invalid search text")

        disciplines = self.request.query_params.getlist('disciplines', None)
        teaching_levels = self.request.query_params.getlist('teaching_levels', None)
        difficulties = self.request.query_params.getlist('difficulties', None)
        years = self.request.query_params.getlist('years', None)
        sources = self.request.query_params.getlist('sources', None)
        author = self.request.query_params.get('author', None)
        authorship = self.request.query_params.get('authorship', None)

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
        if authorship:
            params['authorship__in'] = authorship

        # The following queries are to apply the weights of haystack boost
        queries = [SQ(tags=AutoQuery(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        query = queries.pop()
        for item in queries:
            query |= item
        queries = [SQ(topics=AutoQuery(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item
        queries = [SQ(statement=AutoQuery(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item

        search_queryset = SearchQuerySet().models(Question).filter_and(**params)
        search_queryset = search_queryset.filter(SQ(content=AutoQuery(text)) | (
            SQ(content=AutoQuery(text)) & query
        ))

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
    permission_classes = (permissions.IsAuthenticated, QuestionPermission )

    def get_queryset(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return Question.objects.all()
        queryset = Question.objects.get_questions_prefetched()
        if self.action == 'list':
            queryset = queryset.filter(disabled=False).order_by('id')

        disciplines = self.request.query_params.getlist('disciplines', None)
        teaching_levels = self.request.query_params.getlist('teaching_levels', None)
        difficulties = self.request.query_params.getlist('difficulties', None)
        years = self.request.query_params.getlist('years', None)
        sources = self.request.query_params.getlist('sources', None)
        author = self.request.query_params.get('author', None)
       
        if disciplines:
            queryset = queryset.filter(disciplines__in=disciplines).distinct()
        if teaching_levels:
            queryset = queryset.filter(teaching_levels__in=teaching_levels).distinct()
        if difficulties:
            queryset = queryset.filter(difficulty__in=difficulties).distinct()
        if years:
            queryset = queryset.filter(year__in=years).distinct()
        if sources:
            query = reduce(operator.or_, (Q(source__contains = source) for source in sources))
            queryset = queryset.filter(query)
        if author:
            queryset = queryset.filter(author__id=author).order_by('-create_date')

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
        serializer_question = self.serializer_class(question)

        documents = Document.objects.filter(questions__id=pk, owner=request.user).order_by('create_date')
        serializer_documents = serializers.ListDocumentQuestionSerializer(documents, many = True)

        return_data = serializer_question.data
        return_data['documents'] = serializer_documents.data

        related_questions = RelatedQuestions().similar_questions(question)
        order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(related_questions)])

        questions_object = Question.objects.get_questions_prefetched().filter(id__in=related_questions).order_by(order)
        serializer_questions = serializers.QuestionSerializer(questions_object, many=True)

        return_data['related_questions'] = serializer_questions.data
    
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

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.get_parents_tree()
    serializer_class = serializers.TopicSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        if self.request.query_params:
            disciplines = self.request.query_params.getlist('disciplines', None)
            return Topic.objects.get_parents_tree(disciplines)
        return self.queryset

class LearningObjectSearchView(viewsets.ReadOnlyModelViewSet):
    pagination_class = LearningObjectPagination
    serializer_class = serializers.LearningObjectSerializer
    permission_classes = (permissions.IsAuthenticated, LearningObjectPermission, )

    def gen_queryset(self, search_qs, page_start):
        search_qs = search_qs.load_all()
        queryset = [None] * len(search_qs)
        count = 0
        results = search_qs[page_start:page_start+16]
        for i in range(page_start, min(page_start + 16, len(queryset))):
            if len(results) == 0:
                break
            res = results.pop(0)
            queryset[i] = res.object
            count += 1
            
        return queryset[:count]
    
    def get_queryset(self):
        page = self.request.GET.get('page', None)
        text = self.request.GET.get('text', None)
        is_image = self.request.GET.get('is_image', None)
        is_text = self.request.GET.get('is_text', None)

        try:
            page_no = int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            raise FieldError("Not a valid number for page.")

        if page_no < 1:
            raise FieldError("Pages should be 1 or greater.")

        if not text:
            raise FieldError("Invalid search text")

        text = stripaccents(text)
        text = ' '.join([value for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3])
        
        if not text:
            raise FieldError("Invalid search text")

        params = {}
        if is_image:
            params['is_image'] = True
        if is_text:
            params['is_text'] = True

        start_offset = (page_no - 1) * 16

        # The following queries are to apply the weights of haystack boost
        queries = [SQ(tags=AutoQuery(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        query = queries.pop()
        for item in queries:
            query |= item
        queries = [SQ(source=AutoQuery(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item
        queries = [SQ(text_object=AutoQuery(value)) for value in text.split(' ') if value.strip() != '' and len(value.strip()) >= 3]
        for item in queries:
            query |= item

        search_queryset = SearchQuerySet().models(LearningObject).filter(**params).filter(SQ(content=AutoQuery(text)) | (
            SQ(content=AutoQuery(text)) & query
        ))

        return self.gen_queryset(search_queryset, start_offset)

class LearningObjectViewSet(viewsets.ModelViewSet):
    queryset = LearningObject.objects.all()
    serializer_class = serializers.LearningObjectSerializer
    pagination_class = LearningObjectPagination
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, LearningObjectPermission, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, pk=None):
        learning_object = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_learningobject = self.serializer_class(learning_object)

        questions_object = Question.objects.filter(learning_objects__id=pk).filter(disabled=False).order_by('-create_date')
        serializer_questions = serializers.QuestionSerializer(questions_object, many = True)

        return_data = serializer_learningobject.data
        return_data['questions'] = serializer_questions.data
        
        return Response(return_data)

    def get_queryset(self):
        queryset = LearningObject.objects.all().order_by('id')
        is_image = self.request.query_params.get('is_image', None)
        is_text = self.request.query_params.get('is_text', None)
       
        if is_image:
            queryset = queryset.filter(image__isnull=False).exclude(image='')

        if is_text:
            queryset = queryset.filter(text__isnull=False).exclude(text='')
            
        return queryset.filter()

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = (DocumentsPermission, )

    def get_queryset(self):
        queryset = Document.objects.get_questions_prefetched().filter(owner=self.request.user, disabled=False)
        if (self.action=='generate_list'):
            queryset = Document.objects.get_generate_document().filter(owner=self.request.user, disabled=False)
        if self.action == 'add_question' or self.action == 'remove_question' or self.action == 'update' or self.action == 'partial_update':
            queryset = Document.objects.filter(owner=self.request.user, disabled=False)
        if self.action == 'copy_document':
            queryset = Document.objects.get_questions_prefetched() \
                .filter(Q(documentpublication__isnull=False)|Q(owner=self.request.user)).filter(disabled=False).distinct()
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
       
        serializer = serializers.DocumentCreatesSerializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @detail_route(methods=['post'])
    def add_question(self, request, pk=None):
        document = self.get_object()
        serializer = serializers.DocumentQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_question = serializer.save(document=document)

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

    @detail_route(methods=['get'])
    def generate_list(self, request, pk=None):
        """
        Generate a docx file containing all the list.
        """
        document = self.get_object()
        document_generator = DocxGeneratorAWS()

        try:
            flags = request.query_params
            answers = 'answers' in flags and flags['answers'] == 'True'
            document_generator.generate_document(document, answers)

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
        