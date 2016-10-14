from rest_framework import generics, response

from .serializers import QuestionSerializer, Question_ListSerializer, SimpleQuestion_ListSerializer
from .models import Question, Question_List

from .permissions import IsOwnerOrReadOnly

class QuestionRestListView(generics.ListAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class QuestionRestDetailView(generics.RetrieveAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class Question_ListRestListView(generics.ListAPIView):
    serializer_class = Question_ListSerializer
    queryset = Question_List.objects.all()

class Question_ListRestCreateView(generics.CreateAPIView):
    serializer_class = SimpleQuestion_ListSerializer
    queryset = Question_List.objects.all()

class Question_ListRestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = Question_ListSerializer
    permission_class = IsOwnerOrReadOnly
    queryset = Question_List.objects.all()
