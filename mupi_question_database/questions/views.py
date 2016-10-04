from django.views.generic import DetailView, ListView, RedirectView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Question


class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question

    slug_field = 'pk'
    slug_url_kwarg = 'pk'


class QuestionListView(LoginRequiredMixin, ListView):
    model = Question

    slug_field = 'pk'
    slug_url_kwarg = 'pk'

class QuestionCheckAnswerView(LoginRequiredMixin, DetailView):
    template_name = 'questions/question_checkAnswer.html'
    model = Question

    slug_field = 'pk'
    slug_url_kwarg = 'pk'
