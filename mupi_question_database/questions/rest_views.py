from rest_framework import generics, response, viewsets, status
from rest_framework.response import Response

from mupi_question_database.users.models import User

from .models import Question, Question_List, Profile
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


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = serializers.QuestionSerializer
    permission_classes = (permissions.IsOwnerOrReadOnlyQuestion,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class Question_ListViewSet(viewsets.ModelViewSet):
    queryset = Question_List.objects.all()
    serializer_class = serializers.Question_ListSerializer
    permission_classes = (permissions.IsOwnerOrReadOnlyQuestion_List,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def list(self, request):
        if request.user.is_superuser:
            queryset = Question_List.objects.all()
            serializer = zQuestion_ListSerializer(queryset, many=True)
        else:
            queryset = Question_List.objects.filter(private=False)
            serializer = Question_ListSerializer(queryset, many=True)
        return Response(serializer.data)
