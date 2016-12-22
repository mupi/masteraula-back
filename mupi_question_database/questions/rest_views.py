from rest_framework import generics, response

from .serializers import QuestionSerializer, Question_ListSerializer, SimpleQuestion_ListSerializer, ProfileSerializer
from .models import Question, Question_List, Profile

from .permissions import IsOwnerOrReadOnlyQuestion_List

class ProfileRestListView(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class QuestionRestListView(generics.ListAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class QuestionRestDetailView(generics.RetrieveAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer



class Question_ListRestListView(generics.ListAPIView):
    serializer_class = Question_ListSerializer
    queryset = Question_List.objects.all()
    queryset = Question_List.objects.filter(private=False)

class Question_ListRestCreateView(generics.CreateAPIView):
    serializer_class = SimpleQuestion_ListSerializer
    queryset = Question_List.objects.all()

class Question_ListRestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = Question_ListSerializer
    permission_classes = [IsOwnerOrReadOnlyQuestion_List,]
    queryset = Question_List.objects.all()
