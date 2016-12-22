from rest_framework import generics, response, viewsets

from mupi_question_database.users.models import User

from .serializers import QuestionSerializer, Question_ListSerializer, SimpleQuestion_ListSerializer, ProfileSerializer, UserSerializer
from .models import Question, Question_List, Profile

from .permissions import IsOwnerOrReadOnlyQuestion_List

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class Question_ListViewSet(viewsets.ModelViewSet):
    queryset = Question_List.objects.all()
    serializer_class = Question_ListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
