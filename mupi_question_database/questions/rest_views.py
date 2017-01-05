from rest_framework import generics, response, viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mupi_question_database.users.models import User

from .models import Question, Question_List, Profile, QuestionQuestion_List
from . import permissions as permissions
from . import serializers as serializers

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (permissions.IsOwnerOrReadOnlyUser,)

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'create':
            return serializers.UserSerializer
        return serializers.UserProfileSerializer


    def update(self, request, pk=None):
        user = self.get_object()
        serializer = serializers.UserSerializer(data=request.data)

        if serializer.is_valid():
            if user.check_password(serializer.validated_data['password']):
                user.email = serializer.validated_data['email']
                user.name = serializer.validated_data['name']
                user.save()
                return Response({'status': 'update set'})
            else:
                return Response({'password': 'invalid password'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        user = self.get_object()
        serializer = serializers.UserSerializer(data=request.data, partial = True)

        if serializer.is_valid():
            if user.check_password(serializer.validated_data['password']):
                if 'email' in serializer.validated_data:
                    user.email = serializer.validated_data['email']
                if 'name' in serializer.validated_data:
                    user.name = serializer.validated_data['name']
                user.save()
                return Response({'status': 'update set'})
            else:
                return Response({'password': 'invalid password'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = serializers.PasswordSerializer(data=request.data)
        if serializer.is_valid():
            if user.check_password(serializer.validated_data['previous_password']):
                user.set_password(serializer.data['password'])
                user.save()
                return Response({'status': 'password set'})
            else:
                return Response({'previous_password': 'invalid password'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = serializers.QuestionSerializer
    permission_classes = (permissions.IsOwnerOrReadOnlyQuestion,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @list_route(permission_classes=[IsAuthenticated])
    def user_avaiable_questions(self, request):
        profile = self.request.user.profile
        avaiable_questions = profile.avaiable_questions.all()

        page = self.paginate_queryset(avaiable_questions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recent_users, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def trade_question(self, request, pk=None):
        bought_question = self.get_object()
        buyer_profile = self.request.user.profile
        seller_profile = bought_question.author.profile

        print("asdfdasf")

        avaiable_questions = buyer_profile.avaiable_questions.all()
        if bought_question in avaiable_questions:
            return Response({"error" : "already bought this question"}, status=status.HTTP_400_BAD_REQUEST)

        if buyer_profile.credit_balance < bought_question.credit_cost:
            return Response({"error" : "insuficient founds"}, status=status.HTTP_400_BAD_REQUEST)

        buyer_profile.credit_balance = buyer_profile.credit_balance - bought_question.credit_cost
        buyer_profile.avaiable_questions.add(bought_question)

        seller_profile.credit_balance = seller_profile.credit_balance + bought_question.credit_cost

        buyer_profile.save()
        seller_profile.save()
        return Response({"status" : "success"})

class Question_ListViewSet(viewsets.ModelViewSet):
    queryset = Question_List.objects.all()
    serializer_class = serializers.Question_ListSerializer
    permission_classes = (permissions.IsOwnerOrReadOnlyQuestion_List,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = serializers.Question_List.objects.all()
        else:
            queryset = serializers.Question_List.objects.filter(private=False)
        return queryset

    @detail_route(methods=['post'])
    def clone_list(self, request, pk=None):
        original_list = self.get_object()

        serializer = serializers.Question_ListSerializer(data=request.data)

        serializer.initial_data['questions'] = serializers.QuestionOrderSerializer(
                QuestionQuestion_List.objects.filter(question_list=original_list), many=True, context={'request': request}).data

        if serializer.is_valid():
            print(serializer.validated_data)
            cloned_list = serializer.save(owner=self.request.user, cloned_from=original_list)
            return Response({"status" : "success"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
