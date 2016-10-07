from django.views.generic import DetailView, ListView, RedirectView, UpdateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
import json

from .models import Question


class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = "questions/question_detail.html"
    context_object_name = "question"

class QuestionListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = "questions/question_list.html"
    context_object_name = "question_list"
    paginate_by = 10

class QuestionCheckAnswerView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = 'questions/question_checkAnswer.html'

def check_question(request):
    if (request.method == 'POST'):
        questionPk = request.POST.get('questionPK')
        checked = request.POST.get('checked')

        if not 'checked_questions' in request.session or not request.session['checked_questions']:
            checked_questions = []
        else:
            checked_questions = request.session['checked_questions']

        if checked == 'true':
            checked_questions.append(int(questionPk))
        else:
            checked_questions = [item for item in checked_questions if item != int(questionPk)]

        request.session['checked_questions'] = checked_questions

        return HttpResponse(
            json.dumps({"status" : "success"}),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"nothing to see": "this isn't happening"}),
            content_type="application/json"
        )

class SelectedQuetionsView(LoginRequiredMixin, TemplateView):
    template_name = "questions/question_selectedList.html"

    def get_context_data(self, *args, **kwargs):
        context = super(SelectedQuetionsView, self).get_context_data(**kwargs)
        if not 'checked_questions' in self.request.session or not self.request.session['checked_questions']:
            checked_questions = []
        else:
            checked_questions = self.request.session['checked_questions']

        context['checked_questions'] = Question.objects.filter(pk__in=checked_questions)
        return context
