from rest_framework import generics, response

from .serializers import QuestionSerializer
from .models import Question

class QuestionRestListView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class QuestionRestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
