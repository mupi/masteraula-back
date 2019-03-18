# -*- coding: utf-8 -*-
from django.http import HttpResponse

from drf_haystack.filters import HaystackAutocompleteFilter
from drf_haystack.viewsets import HaystackViewSet

from rest_framework import generics, response, viewsets, status, mixins, viewsets
from rest_framework.decorators import detail_route, list_route
#from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import viewsets, exceptions, pagination
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from taggit.models import Tag

from masteraula.users.models import User
from masteraula.questions.templatetags.search_helpers import stripaccents

from .models import (Question, Document, Discipline, TeachingLevel, DocumentQuestion, Header,
                    Year, Source, Topic, LearningObject, Search)
from .templatetags.search_helpers import stripaccents
from .docx_parsers import Question_Parser
from .docx_generator import Docx_Generator
from . import permissions as permissions
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

class QuestionSearchView(HaystackViewSet):   
    index_models = [Question]
    pagination_class = QuestionPagination
    serializer_class = serializers.QuestionSearchSerializer
    permission_classes = (permissions.QuestionPermission, )
     
    def get_queryset(self, *args, **kwargs):
        disciplines = self.request.query_params.getlist('disciplines', None)
        teaching_levels = self.request.query_params.getlist('teaching_levels', None)
        difficulties = self.request.query_params.getlist('difficulties', None)
        years = self.request.query_params.getlist('years', None)
        sources = self.request.query_params.getlist('sources', None)
        
        self.request.query_params._mutable = True
        for key in self.request.query_params:
            if key == 'text' or key=='page':
                self.request.query_params.setlist(key, [stripaccents(qp_value) for qp_value in self.request.query_params.getlist(key)])
            else:
                self.request.query_params.setlist(key, [])
        self.request.query_params._mutable = False

        queryset = super().get_queryset()

        if disciplines is not None and disciplines:
            queryset = queryset.filter(disciplines__id__in=disciplines)
        if teaching_levels is not None and teaching_levels:
            queryset = queryset.filter(teaching_levels__in=teaching_levels)
        if difficulties is not None and difficulties:
            difficulties_texts = []
            if 'E' in difficulties:
                difficulties_texts.append('Facil')
            if 'M' in difficulties:
                difficulties_texts.append('Medio')
            if 'H' in difficulties:
                difficulties_texts.append('Dificil')
            queryset = queryset.filter(difficulty__in=difficulties_texts)
        if years is not None and years:
            queryset = queryset.filter(year__in=years)
        if sources is not None and sources:
            # query = reduce(operator.or_, (Q(source__contains = source) for source in sources))
            # queryset = queryset.filter(query)
            queryset = queryset.filter(source__in=sources)   
        
        #Salvar os dados de busca
        obj = Search.objects.create(user=self.request.user, term=self.request.query_params['text'])
        
        if disciplines is not None:
            obj.disciplines = disciplines
        if teaching_levels is not None:
            obj.teaching_levels = teaching_levels
        if difficulties is not None:
            difficulties_text = []

            for d in difficulties:
                if 'E' in d:
                    difficulties_text.append('Easy')     
                if 'M' in d:
                    difficulties_text.append('Medium')
                if 'H' in d:
                    difficulties_text.append('Hard')
           
            dif = ', '.join(difficulties_text)
            obj.difficulty = dif

        if sources is not None:
            s = ', '.join(sources)
            obj.source = s
        if years is not None:
            y = ', '.join(years)
            obj.year = y
  
        obj.save()
        return queryset
    
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = serializers.QuestionSerializer
    pagination_class = QuestionPagination
    permission_classes = (permissions.QuestionPermission, )

    def get_queryset(self):
        queryset = Question.objects.all()
        disciplines = self.request.query_params.getlist('disciplines', None)
        teaching_levels = self.request.query_params.getlist('teaching_levels', None)
        difficulties = self.request.query_params.getlist('difficulties', None)
        years = self.request.query_params.getlist('years', None)
        sources = self.request.query_params.getlist('sources', None)

        if disciplines is not None and disciplines:
            queryset = queryset.filter(disciplines__in=disciplines).distinct()
        if teaching_levels is not None and teaching_levels:
            queryset = queryset.filter(teaching_levels__in=teaching_levels).distinct()
        if difficulties is not None and difficulties:
            queryset = queryset.filter(difficulty__in=difficulties).distinct()
        if years is not None and years:
            queryset = queryset.filter(year__in=years).distinct()
        if sources is not None and sources:
            query = reduce(operator.or_, (Q(source__contains = source) for source in sources))
            queryset = queryset.filter(query)
            
        return queryset
    
    def retrieve(self, request, pk=None):
        question = get_object_or_404(self.get_queryset(), pk=pk)
        serializer_question = self.serializer_class(question)

        documents_questions = DocumentQuestion.objects.filter(question__id=pk)
        documents = [dq.document for dq in documents_questions if dq.document.owner==request.user]
        documents = sorted(documents, key=lambda doc: doc.create_date)
        serializer_documents = serializers.ListDocumentQuestionSerializer(documents, many = True)

        return_data = serializer_question.data
        return_data['documents'] = serializer_documents.data
        
        return Response(return_data)   

class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Discipline.objects.all().order_by('name')
    serializer_class = serializers.DisciplineSerialzier
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
    serializer_class = serializers.TopicSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        if self.request.query_params:
            disciplines = self.request.query_params.getlist('disciplines', None)
            queryset = Topic.objects.filter(parent=None).filter(discipline__in=disciplines).distinct()

        else:
            queryset = Topic.objects.all()
        return queryset

class LearningObjectViewSet(viewsets.ModelViewSet):
    queryset = LearningObject.objects.all()
    serializer_class = serializers.LearningObjectSerializer
    pagination_class = LearningObjectPagination
    permission_classes = (permissions.LearningObjectPermission, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.DocumentsPermission, )

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = Document.objects.all() 
            return queryset
        else:
            queryset = Document.objects.filter(owner=self.request.user)
            return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.DocumentListSerializer
        if self.action == 'create':
            return serializers.DocumentCreatesSerializer
        return serializers.DocumentDetailSerializer
       

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @detail_route(methods=['post'])
    def copy_document(self, request, pk=None):
        obj = self.get_object()
        questions = obj.questions.all()
                                       
        obj.pk = None
        obj.name = obj.name + ' (Cópia)'
        obj.save()

        for count, q in enumerate(questions):
            dq = DocumentQuestion.objects.create(document=obj, question=q, order=count) 
       
        serializer = serializers.DocumentCreatesSerializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @detail_route(methods=['post'])
    def add_question(self, request, pk=None):
        document = self.get_object()
        serializer = serializers.DocumentQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_question = serializer.save(document=document)
        list_document = serializers.DocumentQuestionListDetailSerializer(document_question)
        headers = self.get_success_headers(list_document.data)
        
        return Response(list_document.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @detail_route(methods=['post'])
    def remove_question(self, request, pk=None):
        document = self.get_object()
        request.data['order'] = 0
        serializer = serializers.DocumentQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']
        document.remove_question(question)

        return Response(status = status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get'])
    def my_documents(self, request):
        order_field = request.query_params.get('order_field', None)
        order_type = request.query_params.get('order', None)
        
        if order_field == 'date':
            if order_type == 'desc':
                queryset = Document.objects.filter(owner=self.request.user).order_by('-create_date')
            else:
                queryset = Document.objects.filter(owner=self.request.user).order_by('create_date')

        elif order_field == 'name':
            if order_type =='desc':
                queryset = Document.objects.filter(owner=self.request.user).order_by('-name')
            else:
                queryset = Document.objects.filter(owner=self.request.user).order_by('name')

        elif order_field =='question_number':
            if order_type =='desc':
                queryset = Document.objects.filter(owner=self.request.user).annotate(num_questions = Count('questions')).order_by('-num_questions')
            else:
                queryset = Document.objects.filter(owner=self.request.user).annotate(num_questions = Count('questions')).order_by('num_questions')

        else:
            queryset = Document.objects.filter(owner=self.request.user).order_by('-create_date')

        self.pagination_class = DocumentPagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.DocumentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.DocumentListSerializer(queryset, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # @detail_route(methods=['get'])
    # def get_list(self, request, pk=None):
    #     """
    #     Generate a docx file containing all the list.
    #     """
    #     document = self.get_object()
    #     document_name = document.name
    #     docx_name = pk + document_name + '.docx'

    #     data = open(docx_name, "rb").read()

    #     response = HttpResponse(
    #         data, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    #     )
    #     response['Content-Disposition'] = 'attachment; filename="' + document_name + '.docx"'
    #     # Apaga o arquivo temporario criado
    #     os.remove(docx_name)
    #     return response

    @detail_route(methods=['get'])
    def generate_list(self, request, pk=None):
        """
        Generate a docx file containing all the list.
        """
        document = self.get_object()
        document_generator = Docx_Generator()
        flags = request.query_params

        if not document.questions:
            raise exceptions.ValidationError('Can not generate an empty list')
        
        document_generator.write_title(document)
        
        if 'header' in flags:
            header = Header.objects.get(pk=int(flags['header']))
            document_generator.write_header(header)

        document_generator.write_questions([dq.question for dq in document.documentquestion_set.all().order_by('order')])

        if 'answers' in flags and flags['answers'] == 'True':
            document_generator.write_answers([dq.question for dq in document.documentquestion_set.all().order_by('order')])
        
        docx_name = document_generator.close()
        data = open(docx_name + '.docx', "rb").read()

        response = HttpResponse(
            data, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = 'attachment; filename="' + docx_name + '.docx"'
        os.remove(docx_name + '.docx')
        return response

        # flags = request.query_params
        # resolution = False
        # # question_parents = []
        # all_questions = []

        # if not questions:
        #     raise exceptions.ValidationError('Can not generate an empty list')

        # if 'resolution' in flags and flags['resolution'] == 'True':
        #     resolution = True

        # # Nome aleatorio para nao causar problemas
        # docx_name = pk + str(current_milli_time()) + '.docx'
        # parser = Question_Parser(docx_name)
        # parser.parse_heading(document)

        # for q in questions:
        # #     if q.question_parent != None:
        # #         if q.question_parent not in question_parents:
        # #             question_parents.append(q.question_parent)
        # #             all_questions.append(q.question_parent)
        #     all_questions.append(q)

        # parser.parse_list_questions(all_questions, resolution)

        # if 'answers' in flags and flags['answers'] == 'True':
        #     parser.parse_alternatives_list_questions(all_questions)

        # parser.end_parser()

class HeaderViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.HeaderSerializer
    pagination_class = HeaderPagination
    permission_classes = (permissions.HeaderPermission,)

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
        