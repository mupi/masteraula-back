# -*- coding: utf-8 -*-
from django.http import HttpResponse

from drf_haystack.filters import HaystackAutocompleteFilter
from drf_haystack.viewsets import HaystackViewSet

from rest_framework import (generics, response, viewsets, status, mixins, 
                    exceptions, pagination, permissions)
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
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

class QuestionSearchView(HaystackViewSet):   
    index_models = [Question]
    pagination_class = QuestionPagination
    serializer_class = serializers.QuestionSearchSerializer
    permission_classes = (permissions.IsAuthenticated, QuestionPermission, )
     
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
    serializer_class = serializers.QuestionSerializer
    pagination_class = QuestionPagination
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, QuestionPermission )

    def get_queryset(self):
        queryset = Question.objects.all().order_by('id')
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
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, LearningObjectPermission, )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = (DocumentsPermission, )

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

# class UserViewSet(mixins.CreateModelMixin,
#                     mixins.ListModelMixin,
#                     mixins.RetrieveModelMixin,
#                     viewsets.GenericViewSet):
#     """
# list:

# List all the users with basic information (without profile info)
# <hr>

# create:

# WARNING - You may consider using django-rest-auth registration method instead

# Create a new User with some required fields

# ##Parameters
# * Only the name is not required. All the others are.
# * Email has to be a valid email.
# * Username has to be a new one (can't repeat)

# <hr>

# retrieve:

# Get the id's related user.
# <hr>
#     """
#     queryset = User.objects.all()
#     permission_classes = (permissions.UserPermission,)
#     serializer_class = serializers.UserSerializer

#     # @list_route(methods=['delete'], permission_classes=[IsAuthenticated])
#     # def current_destroy(self, request, pk=None):
#     #     """
#     #     Delete the current authenticated user
#     #     """
#     #     user = request.user
#     #     user.is_active = False
#     #     user.save()
#     #     return Response({'status': 'deleted'})

#     def list (self, request):
#         user = self.request.user
#         if not user.is_superuser:
#             self.serializer_class = serializers.UserBasicSerializer
#         return super().list(request)

#     def retrieve(self, request, pk=None):
#         user = self.request.user
#         if not user.is_superuser:
#             self.serializer_class = serializers.UserBasicSerializer
#         return super().retrieve(request, pk)

#     @list_route(methods=['patch'], permission_classes=[IsAuthenticated], serializer_class=serializers.UserUpdateSerializer)
#     def current_update(self, request):
#         """
#         WARNING - You may consider using django-rest-auth patch method instead

#         Update all the fields, checking the password before saving the new changes.

#         All the fields will be updated. All the fields are required.
#         """
#         user = request.user
#         serializer = serializers.UserUpdateSerializer(data=request.data)

#         if serializer.is_valid():
#             if user.check_password(serializer.validated_data['password']):
#                 user.email = serializer.validated_data['email']
#                 user.name = serializer.validated_data['name']
#                 user.save()
#                 return Response({'status': 'update set'})
#             else:
#                 return Response({'password': 'invalid password'},
#                                 status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response(serializer.errors,
#                             status=status.HTTP_400_BAD_REQUEST)

#     @list_route(methods=['put'], permission_classes=[IsAuthenticated], serializer_class=serializers.UserUpdateSerializer)
#     def current_partial_update(self, request):
#         """
#         WARNING - You may consider using django-rest-auth put method instead

#         Update only the fields that are in the request, checking the password.
#         """
#         user = request.user
#         serializer = serializers.UserUpdateSerializer(data=request.data, partial = True)

#         if serializer.is_valid():
#             if 'password' not in serializer.validated_data:
#                 return Response({'password': 'password field is required'},
#                                 status=status.HTTP_400_BAD_REQUEST)

#             if user.check_password(serializer.validated_data['password']):
#                 if 'email' in serializer.validated_data:
#                     user.email = serializer.validated_data['email']
#                 if 'name' in serializer.validated_data:
#                     user.name = serializer.validated_data['name']
#                 user.save()
#                 return Response({'status': 'update set'})
#             else:
#                 return Response({'password': 'invalid password'},
#                                 status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response(serializer.errors,
#                             status=status.HTTP_400_BAD_REQUEST)

#     @list_route(methods=['get'], permission_classes=[IsAuthenticated])
#     def current(self, request):
#         """
#         WARNING - You may consider using django-rest-auth get method instead

#         Show current authenticated user
#         """
#         user = request.user
#         serializer = serializers.UserProfileSerializer(user, context={'request': request})
#         return Response(serializer.data)

#     @list_route(methods=['post'], permission_classes=[IsAuthenticated], serializer_class=serializers.PasswordSerializer)
#     def set_password(self, request):
#         """
#         WARNING - You may consider using django-rest-auth password change method instead

#         API View that change the password of the current user in request.
#         """
#         user = request.user
#         serializer = serializers.PasswordSerializer(data=request.data)
#         if serializer.is_valid():
#             if user.check_password(serializer.validated_data['previous_password']):
#                 user.set_password(serializer.data['password'])
#                 user.save()
#                 return Response({'status': 'password set'})
#             else:
#                 return Response({'previous_password': 'invalid password'},
#                                 status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response(serializer.errors,
#                             status=status.HTTP_400_BAD_REQUEST)

# class QuestionViewSet(viewsets.ModelViewSet):
#     """
# list:

# List all the questions
# <hr>

# create:

# Create a new question

# ###Parameters

# ###resolution
# Resolution is a string that saves the author opinion and/or how to solve it.

# ####level
# A string containing one of the following options: "E" (easy), "M" ('medium'), "H" (hard) or null

# ####tags
# An array containing strings representing the tags.

# E.g.:
# ```"tags" : ["enem", "química orgânica"]```

# ####Answers
# An array containing objects that has two parameters: 'answer_text' containing the answer text
# and 'is_correct' that if the answer is correct or not.
# The anwer must have one and only one correct answer.

# Correct E.g.:

# ```
# "answers" : [
#     {
#         "answer_text" : "Sim",
#         "is_correct" : true
#     },
#     {
#         "answer_text" : "Não",
#         "is_correct" : false
#     }
# ]```

# Wrong E.g.:

# ```
# "answers" : [
#     {
#         "answer_text" : "Errado",
#         "is_correct" : false
#     },
#     {
#         "answer_text" : "Não",
#         "is_correct" : false
#     }
# ]```
# <hr>

# retrieve:

# Get the id's related question.
# <hr>

# delete:

# Delete the id's related question.
# <hr>

# update:

# Update all the fields. All the fields are required.

# The question will only be updated if the current authenticated user is the author.
# <hr>

# partial_update:

# Update only the fields that are in the request.

# The question will only be updated if the current authenticated user is the author.
# <hr>

# delete:

# WARNING: Deleting questions may impact questions_lists(the orders will be affected causing a huge problem)
# The question will only be deleted if the current authenticated user is the author.
# <hr>
#     """
#     queryset = Question.objects.all()
#     serializer_class = serializers.QuestionSerializer
#     permission_classes = (permissions.QuestionPermission,)
#     pagination_class = QuestionPagination

#     def perform_create(self, serializer):
#         serializer.save(author=self.request.user)

#     def retrieve(self, request, pk=None):
#         user = self.request.user
#         question = self.get_object()
#         # if (user.is_anonymous() or question not in user.profile.avaiable_questions.all()) and not user.is_superuser:
#         #     self.serializer_class = serializers.QuestionBasicSerializer
#         return super().retrieve(request, pk)

#     def list(self, request):
#         user = self.request.user
#         # if not user.is_superuser:
#         #     self.serializer_class = serializers.QuestionBasicSerializer
#         return super().list(request)

#     @list_route(permission_classes=[IsAuthenticated])
#     def user_avaiable_questions(self, request):
#         """
#         List all the purcharsed questions of the current authenticated user.
#         """
#         user = self.request.user
#         avaiable_questions = user.profile.avaiable_questions.all()

#         page = self.paginate_queryset(avaiable_questions)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(recent_users, many=True)
#         return Response(serializer.data)

#     @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
#     def trade_question(self, request, pk=None):
#         """
#         Trade the question, if the current authenticated user has founds and hasn't already
#         bought the question
#         """
#         bought_question = self.get_object()
#         buyer_profile = self.request.user.profile
#         seller_profile = bought_question.author.profile

#         avaiable_questions = buyer_profile.avaiable_questions.all()
#         if bought_question in avaiable_questions:
#             return Response({"error" : "already bought this question"}, status=status.HTTP_400_BAD_REQUEST)

#         if buyer_profile.credit_balance < bought_question.credit_cost:
#             return Response({"error" : "insuficient founds"}, status=status.HTTP_400_BAD_REQUEST)

#         buyer_profile.credit_balance = buyer_profile.credit_balance - bought_question.credit_cost
#         buyer_profile.avaiable_questions.add(bought_question)

#         seller_profile.credit_balance = seller_profile.credit_balance + bought_question.credit_cost

#         buyer_profile.save()
#         seller_profile.save()
#         return Response({"status" : "success"})



# class Question_ListViewSet(viewsets.ModelViewSet):
#     """
# list:

# List all the question_lists, excluding the private (unless the request user is the owner)

# create:

# Create a new question_list

# ##Parameters
# ###questions:
# An array containing objects that has two parameters: 'question' containing the question URL and
# 'order', the order that the question will appear in the list.

# The question list order starts at 1 and should respect the ascending order so if the list has
# 3 questions it's necessary that the array has three questions containing 1, 2 and 3 order.

# Correct E.g.:

# ```
# "questions" : [
#     {
#         "question" : 1,
#         "order" : 2
#     },
#     {
#         "question" : 4,
#         "order" : 1
#     }
# ]```

# Wrong E.g. 1 (duplicated order):

# ```
# "questions" : [
#     {
#         "question" : 1,
#         "order" : 1
#     },
#     {
#         "question" : 4,
#         "order" : 1
#     }
# ]```

# Wrong E.g. 2 (Invalid order):

# ```
# "questions" : [
#     {
#         "question" : 1,
#         "order" : 2
#     },
#     {
#         "question" : 4,
#         "order" : 3
#     }
# ]```

# Wrong E.g. 3 (duplicate question):

# ```
# "questions" : [
#     {
#         "question" : 1,
#         "order" : 2
#     },
#     {
#         "question" : 1,
#         "order" : 1
#     }
# ]```

# retrieve:

# Get the id's related question_list

# update:

# Update all the fields. All the fields are required.

# The question will only be updated if the current authenticated user is the owner.

# partial_update:

# Update only the fields that are in the request.

# The question will only be updated if the current authenticated user is the owner.

# destroy:

# Delete the id's related question_list.

# The question_list will only be deleted if the current authenticated user is the owner.
#     """
#     serializer_class = serializers.Question_ListSerializer
#     permission_classes = (permissions.Question_ListPermission,)

#     def get_serializer_class(self):
#         if self.action == 'retrieve':
#             return serializers.Question_ListDetailSerializer
#         if self.action == 'list' or self.action == 'user_list_questions':
#             return serializers.Question_ListBasicSerializer
#         return serializers.Question_ListSerializer

#     def create(self, request):
#         user_serializer = serializers.UserSerializer(self.request.user, context={'request': request})
#         request.data['owner'] = user_serializer.data['id']
#         return super().create(request)

#     def update(self, request, pk=None):
#         user_serializer = serializers.UserSerializer(self.request.user, context={'request': request})
#         request.data['owner'] = user_serializer.data['id']
#         return super().update(request, pk)

#     def partial_update(self, request, pk=None):
#         user_serializer = serializers.UserSerializer(self.request.user, context={'request': request})
#         request.data['owner'] = user_serializer.data['id']
#         return super().update(request, pk)

#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)

#     def get_queryset(self):
#         if self.request.user.is_superuser:
#             queryset = serializers.Question_List.objects.all()
#         else:
#             queryset = serializers.Question_List.objects.filter(secret=False)
#         return queryset

#     @list_route(permission_classes=[IsAuthenticated])
#     def user_list_questions(self, request):
#         """
#         List all the question lists of the current authenticated user.
#         """
#         user = self.request.user
#         avaiable_lists = user.question_list_set.all()
#         # self.pagination_class = None

#         # page = self.paginate_queryset(avaiable_lists)
#         # if page is not None:
#         serializer = serializers.Question_ListBasicSerializer(avaiable_lists, many=True)
#         return Response(serializer.data)

#         # serializer = self.get_serializer(recent_users, many=True)
#         # return Response(serializer.data)

#     @detail_route(methods=['post'])
#     def clone_list(self, request, pk=None):
#         """
#         Clone the list, copying all the questions and giving a new name and setting private or not.
#         """
#         original_list = self.get_object()

#         user_serializer = serializers.UserSerializer(self.request.user, context={'request': request})
#         request.data['owner'] = user_serializer.data['url']
#         serializer = self.get_serializer(data=request.data)

#         serializer.initial_data['questions'] = serializers.QuestionOrderSerializer(
#                 QuestionQuestion_List.objects.filter(question_list=original_list), many=True, context={'request': request}).data

#         serializer.is_valid(raise_exception=True)

#         serializer.save(owner=self.request.user, cloned_from=original_list)
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# class TagListView(mixins.ListModelMixin, viewsets.GenericViewSet):
#     queryset = Question.tags.most_common()
#     pagination_class = None
#     serializer_class = serializers.TagSerializer

# class SubjectListView(mixins.ListModelMixin, viewsets.GenericViewSet):
#     queryset = Subject.objects.all()
#     pagination_class = None
#     serializer_class = serializers.SubjectSerializer

# class QuestionSearchView(mixins.ListModelMixin, viewsets.ViewSetMixin, HaystackGenericAPIView):
#     """
# list:

# List questions. It can be used filters passed in the queryset.

# E.g.s:

# + admin's Questions: [http://localhost:8000/rest/search/question/?author=admin](http://localhost:8000/rest/search/question/?author=admin)
# + Questions with 'enem' and 'Facil' tags: [http://localhost:8000/rest/search/question/?tags=enem&level=Facil](http://localhost:8000/rest/search/question/?tags=enem&level=Facil)
# + Questions with 'enem' and 'erro' tags: [http://localhost:8000/rest/search/question/?tags=enem&tags=erro](http://localhost:8000/rest/search/question/?tags=enem&tags=erro)
# + Questions with 'D'águas de lindóia' tag: [http://localhost:8000/rest/search/question/?tags=daguas-de-lindoia](http://localhost:8000/rest/search/question/?tags=daguas-de-lindoia)
# + Questions containing 'Quantas' word: [http://localhost:8000/rest/search/question/?text__content=Quantas](http://localhost:8000/rest/search/question/?text__content=Quantas)
#     """
#     index_models = [Question]
#     pagination_class = QuestionPagination

#     serializer_class = serializers.QuestionSearchSerializer

# class TagSearchView(mixins.ListModelMixin, viewsets.ViewSetMixin, HaystackGenericAPIView):
#     """
# list:

# List tags. Useful with autocomplete. Need at least 2 characters to work.

# E.g.s:
# Tags starting with 'bio': [http://localhost:8000/rest/search/tag/?q=bio](http://localhost:8000/rest/search/tag/?q=bio)
#     """
#     index_models = [Tag]
#     pagination_class = None
#     serializer_class = serializers.TagSearchSerializer
#     filter_backends = [HaystackAutocompleteFilter]
