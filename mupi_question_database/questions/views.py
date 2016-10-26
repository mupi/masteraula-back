from django.views.generic import DetailView, ListView, RedirectView, UpdateView, TemplateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models import Q
from django.urls import reverse


from docx import *
from docx.shared import Inches

import json
import datetime
import io

from .models import Question, Question_List

class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = "questions/question_detail.html"
    context_object_name = "question"

class QuestionListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = "questions/question_list.html"
    context_object_name = "question_list"
    paginate_by = 10



class Question_ListDetailView(LoginRequiredMixin, DetailView):
    model = Question_List
    template_name = "questions/question_list_detail.html"
    context_object_name = "question_list"

class Question_ListDeleteView(LoginRequiredMixin, DeleteView):
    model = Question_List
    context_object_name = "question_list"
    success_url = "/questions/question_lists"

class Question_ListCreateView(LoginRequiredMixin, CreateView):
    model = Question_List
    fields = ['question_list_header', 'private']
    template_name = "questions/question_list_create.html"

    def get_context_data(self, *args, **kwargs):
        context = super(Question_ListCreateView, self).get_context_data(**kwargs)
        if not 'checked_questions' in self.request.session or not self.request.session['checked_questions']:
            checked_questions = []
        else:
            checked_questions = self.request.session['checked_questions']

        context['checked_questions'] = Question.objects.filter(pk__in=checked_questions)
        return context

    def form_valid(self, form):
        new_list = form.save(commit=False)
        new_list.owner = self.request.user

        if not 'checked_questions' in self.request.session or not self.request.session['checked_questions']:
            checked_questions = []
        else:
            checked_questions = self.request.session['checked_questions']
        new_list.save()

        questions = Question.objects.filter(pk__in=checked_questions)
        for question in questions:
            new_list.questions.add(question)
        new_list.save()

        self.request.session['checked_questions'] = []
        return HttpResponseRedirect(reverse('questions:question_list_detail', args=(str(new_list.pk),)))

class Question_ListEditView(LoginRequiredMixin, UpdateView):
    model = Question_List
    fields = ['question_list_header', 'private']
    template_name = "questions/question_list_edit.html"

    def form_valid(self, form):
        new_list = form.save(commit=False)

        if 'checked_edit_add_questions' in self.request.session and self.request.session['checked_edit_add_questions']:
            checked_questions = self.request.session['checked_edit_add_questions']
            questions = Question.objects.filter(pk__in=checked_questions)

            for question in questions:
                new_list.questions.add(question)
            new_list.save()

            self.request.session['checked_edit_add_questions'] = []

        return HttpResponseRedirect(reverse('questions:question_list_detail', args=(str(new_list.pk),)))

    def get_context_data(self, *args, **kwargs):
        context = super(Question_ListEditView, self).get_context_data(**kwargs)

        # Faz tambem a verificacao para mostrar somente dados referentes a atualizacao
        # da mesma lista e os dados que estao no request
        if not 'checked_edit_add_questions' in self.request.session or not self.request.session['checked_edit_add_questions']:
            checked_questions = []
            self.request.session['question_list_edit_id'] = None
            self.request.session['checked_edit_add_questions'] = []
            self.request.session['checked_edit_questions'] = []
        elif self.request.session['question_list_edit_id'] == self.kwargs['pk']:
            checked_questions = Question.objects.filter(pk__in=self.request.session['checked_edit_add_questions'])
            context['checked_edit_add_questions'] = checked_questions

        return context

class Question_ListRemoveQuestionsView(LoginRequiredMixin, UpdateView):
    model = Question_List
    fields = []

    def form_valid(self, form):
        new_list = form.save(commit=False)

        if 'checked_edit_questions' in self.request.session and self.request.session['checked_edit_questions']:
            checked_questions = self.request.session['checked_edit_questions']
            questions = new_list.questions.filter(pk__in=checked_questions)

            for question in questions:
                new_list.questions.remove(question)
            new_list.save()

            self.request.session['checked_edit_questions'] = []

        return HttpResponseRedirect(reverse('questions:question_list_edit', args=(str(new_list.pk),)))

class Question_ListEditListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = "questions/question_list_edit_list.html"
    context_object_name = "question_list"
    paginate_by = 10

    def get_context_data(self, *args, **kwargs):
        context = super(Question_ListEditListView, self).get_context_data(**kwargs)

        # Verifica se a session esta armazenando dados de edicao da lista de
        # questoes que esta sendo atualizada no momento, evitando dados mortos
        # na session
        if not self.request.session['question_list_edit_id'] or self.request.session['question_list_edit_id'] != self.kwargs['pk']:
            self.request.session['checked_edit_add_questions'] = []
        self.request.session['question_list_edit_id'] = self.kwargs['pk']

        list_exclude_questions = Question_List.objects.get(id=self.kwargs['pk']).questions.all()

        context['question_list'] = Question.objects.exclude(pk__in=list_exclude_questions)
        # Armazena para fazer a verificaçao acima
        context['pk_slug'] = self.kwargs['pk']

        return context

class Question_ListListView(LoginRequiredMixin, ListView):
    model = Question_List
    template_name = "questions/question_list_list.html"
    context_object_name = "question_list_list"
    success_url = "/questions"

    def get_context_data(self, *args, **kwargs):
        context = super(Question_ListListView, self).get_context_data(**kwargs)

        context['question_list_list'] = Question_List.objects.filter(Q(private=False) | Q(owner=self.request.user.id))
        return context

class Question_ListOwnListView(LoginRequiredMixin, ListView):
    model = Question_List
    template_name = "questions/question_list_own_list.html"
    context_object_name = "question_list_list"
    success_url = "/questions"

    def get_context_data(self, *args, **kwargs):
        context = super(Question_ListOwnListView, self).get_context_data(**kwargs)

        context['question_list_list'] = Question_List.objects.filter(owner=self.request.user.id)
        return context

class Question_ListCloneView(LoginRequiredMixin, CreateView):
    model = Question_List
    fields = ['question_list_header', 'private']
    template_name = "questions/question_list_clone.html"
    context_object_name = "question_list"

    def get_context_data(self, *args, **kwargs):
        context = super(Question_ListCloneView, self).get_context_data(**kwargs)

        context['cloned_from_list'] = Question_List.objects.get(id=self.kwargs['pk'])
        return context


    def form_valid(self, form):
        cloned_from_list = self.get_context_data()['cloned_from_list']
        new_list = form.save(commit=False)
        new_list.owner = self.request.user

        if not cloned_from_list or not cloned_from_list.questions.all:
            questions = []
        else:
            questions = cloned_from_list.questions.all()
        new_list.cloned_from = cloned_from_list
        new_list.save()

        for question in questions:
            new_list.questions.add(question)
        new_list.save()

        self.request.session['cloned_from_list'] = None
        return HttpResponseRedirect(reverse('questions:question_list_detail', args=(str(new_list.pk),)))

def list_generator(request):
    if (request.method == 'GET'):
        if not 'generate_list_questions' in request.session or not request.session['generate_list_questions']:
            raise Http404("Cant generate a null list.")
        list_questions = Question.objects.filter(pk__in=request.session['generate_list_questions'])
        if not list_questions:
            raise Http404("Cant generate an empty list doccument.")

        document = Document()
        docx_title="Test_List.docx"
        document.add_paragraph(
            "Lista gerada em {:s} as {:s}.".format(
                datetime.date.today().strftime('%d/%m/%Y'),
                datetime.datetime.today().strftime('%X')
            )
        )

        questionCounter = 1
        for question in list_questions:
            document.add_heading('Question ' + str(questionCounter), level=2)
            p = document.add_paragraph('(')
            p.add_run(question.question_header).bold = True
            p.add_run(')'+question.question_text)
            itemChar = 'a'
            for answer in question.answers.all():
                document.add_paragraph(itemChar + ') ' + answer.answer_text)
                itemChar = chr(ord(itemChar) + 1)
            questionCounter = questionCounter + 1
            p = document.add_paragraph()

        document.add_page_break()

        document.save(docx_title)
        data = open(docx_title, "rb").read()

        response = HttpResponse(
            data, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = 'attachment; filename=' + docx_title
        return response

    if (request.method != 'POST'):
        return HttpResponse(
            json.dumps({"status" : "error"}),
            content_type="application/json"
        )
    questionsId = request.POST.getlist('questionsId[]')

    if questionsId == None or len(questionsId) == 0:
        return HttpResponse(
            json.dumps({"status" : "error"}),
            content_type="application/json"
        )
    request.session['generate_list_questions'] = questionsId
    return HttpResponse(
        json.dumps({'status' : 'ready'}),
        content_type="application/json"
    )


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
    raise Http404("Method GET not allowed in check_question!")

def clear_questions(request):
    if (request.method == 'POST'):

        request.session['checked_questions'] = []

        return HttpResponse(
            json.dumps({"status" : "success"}),
            content_type="application/json"
        )
    raise Http404("Method GET not allowed in check_question!")


def check_question_edit_list(request):
    if (request.method == 'POST'):
        questionPk = request.POST.get('questionPK')
        checked = request.POST.get('checked')

        if not 'checked_edit_questions' in request.session or not request.session['checked_edit_questions']:
            checked_questions = []
        else:
            checked_questions = request.session['checked_edit_questions']

        if checked == 'true':
            checked_questions.append(int(questionPk))
        else:
            checked_questions = [item for item in checked_questions if item != int(questionPk)]

        request.session['checked_edit_questions'] = checked_questions

        return HttpResponse(
            json.dumps({"status" : "success"}),
            content_type="application/json"
        )
    raise Http404("Method GET not allowed in check_question!")


def check_question_edit_add_list(request):
    if (request.method == 'POST'):
        questionPk = request.POST.get('questionPK')
        checked = request.POST.get('checked')

        if not 'checked_edit_add_questions' in request.session or not request.session['checked_edit_add_questions']:
            checked_questions = []
        else:
            checked_questions = request.session['checked_edit_add_questions']

        if checked == 'true':
            checked_questions.append(int(questionPk))
        else:
            checked_questions = [item for item in checked_questions if item != int(questionPk)]

        request.session['checked_edit_add_questions'] = checked_questions

        return HttpResponse(
            json.dumps({"status" : "success"}),
            content_type="application/json"
        )
    raise Http404("Method GET not allowed in check_question!")

def clear_questions_edit_add_list(request):
    if (request.method == 'POST'):

        request.session['checked_edit_add_questions'] = []

        return HttpResponse(
            json.dumps({"status" : "success"}),
            content_type="application/json"
        )
    raise Http404("Method GET not allowed in check_question!")

class QuestionCreate(CreateView):
    model = Question
    fields = ['question_header','question_text','resolution','level','author','tags']

