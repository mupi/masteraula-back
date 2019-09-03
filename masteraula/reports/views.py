# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.db.models import Q
from django.shortcuts import redirect, render

from django.views import View
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django.utils.decorators import method_decorator

from django.contrib.auth.mixins import UserPassesTestMixin

from masteraula.questions.models import Question, Discipline, Document, LearningObject, User, Alternative

from .serializers import QuestionStatementEditSerializer, LearningObjectEditSerializer, AlternativeEditSerializer

from bs4 import BeautifulSoup as bs

import json
import re

class SuperuserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

def process_tags_br(text):
    program = re.compile('(<[\/\s]*?br[\s]*?>)')

    while(program.search(text)):
        text = program.sub('<br/>', text)
    return text

def prettify(html_text):

    # Double curly brackets to avoid problems with .format()
    stripped_markup = html_text.replace('{','{{').replace('}','}}')
    stripped_markup = bs(stripped_markup, 'html.parser')

    unformatted_tag_list = []
    unformatted_tag_types = [
        'strong', 'em', 'sup', 'sub', 'b', 'i', 'a', 'img', 'p'
    ]

    for i, tag in enumerate(stripped_markup.find_all(unformatted_tag_types)):
        unformatted_tag_list.append(str(tag))
        tag.replace_with('{' + 'unformatted_tag_list[{0}]'.format(i) + '}')

    return stripped_markup.prettify().format(unformatted_tag_list=unformatted_tag_list)


class DisciplineReportsBaseView(SuperuserMixin, TemplateView):
    login_url = '/admin/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        context['header'] =  self.header if hasattr(self, 'header') else 'Relatório'
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            results = self.queryset(disciplines)
        if disciplines and results:
            ids, texts = results
            texts = [process_tags_br(t) for t in texts]
        else:
            return super().render_to_response(context)
        
        ids, texts, clean = self.report_function(ids, texts)
        context['data'] = prepare_texts_data(ids, texts, clean)
        return super().render_to_response(context)

def prepare_texts_data(ids, texts, clean, all_status=None):
    data = []
    if all_status is None:
        all_status = [None] * len(ids)
    for _id, text, clean_text, status in zip(ids, texts, clean, all_status):
        text = prettify(text)
        clean_text = prettify(clean_text)

        data.append((_id, text, clean_text, status))
    return data
    
class ReportsView(SuperuserMixin, TemplateView):
    login_url = '/admin/login/'
    template_name = 'reports/base.html'

class NumberDocumentsView(SuperuserMixin, TemplateView):
    login_url = '/admin/login/'
    template_name = 'reports/number_documents.html'

    def post(self, request, *args, **kwargs):      
        data = 'Usuário,Provas Ativas,Provas Criadas\n'  

        id_users =  request.POST.get('id_users', None)
        try:
            if id_users:
                users = User.objects.filter(id__in=id_users.split(','))
            else:
                users = User.objects.all()
        except:
            return render(request, self.template_name, {'not_found' : True})

        if users.count() == 0:
            return render(request, self.template_name, {'not_found' : True})

        for user in users:
            documents = Document.objects.filter(owner = user)
            documents_active = documents.filter(disabled = False)
            data = data + str(user) + ',' + str(documents_active.count()) + ',' + str(documents.count()) + '\n'
    
        response = HttpResponse(data, 'text/csv')
        response['Content-Disposition'] = 'attachment; filename="relatorio_provas.csv"'
        return response

    
class UncategorizedTagsView(DisciplineReportsBaseView):
    template_name = 'reports/uncategorized_questions.html'


    def post(self, request, *args, **kwargs):
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        else:
            questions = Question.objects.all().order_by('id')
        
        data = ''
        for question in questions:
            if question.tags.count() == 0:
                data = data + '%d, https://masteraula.com.br/#/edit-question/%d\n' % (question.id, question.id)
    
        response = HttpResponse(
            data, 'text/csv'
        )
        response['Content-Disposition'] = 'attachment; filename="relatorio.csv"'
        return response

class ObjectsWithoutSource(DisciplineReportsBaseView):
    template_name = 'reports/objects_without_source.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            learning_objects = LearningObject.objects.filter(Q(source__isnull=True) | Q(source='')).distinct() \
                    .filter(question__disciplines__in=disciplines).order_by('id')
        else:
            return super().render_to_response(context)
        
        context['data'] = learning_objects

        return super().render_to_response(context)

class StatementLearningObject(DisciplineReportsBaseView):
    template_name = 'reports/has_learning_object.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        else:
            return super().render_to_response(context)
        
        program_list = [
            'Adaptado',
            'Disponível',
            'Acesso',
            'In:',
            'http(s)?://',
            'Adapted',
            '<small>'
        ]
        possible_objects = set()
        for program in program_list:
            for question in questions:
                if re.search(program, question.statement):
                    possible_objects.add(question.id)
            questions = questions.filter(~Q(id__in=list(possible_objects)))

        context['data'] = Question.objects.filter(id__in=list(possible_objects))

        return super().render_to_response(context)


class StatemensUpdateView(SuperuserMixin, View):
    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        data = data=json.loads(body_unicode)

        try:
            question = Question.objects.get(id=data['id'])
        except:
            return HttpResponseBadRequest('Does not exist')

        serializer = QuestionStatementEditSerializer(question, data=data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse( {"success": "true"}, status=200)

        return HttpResponseBadRequest('Invalid data')

class LearningObjectUpdateView(SuperuserMixin, View):
    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        data = data=json.loads(body_unicode)

        try:
            lo = LearningObject.objects.get(id=data['id'])
        except:
            return HttpResponseBadRequest('Does not exist')

        serializer = LearningObjectEditSerializer(lo, data=data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse( {"success": "true"}, status=200)

        return HttpResponseBadRequest('Invalid data')

class AlternativeUpdateView(SuperuserMixin, View):
    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        data = data=json.loads(body_unicode)

        try:
            lo = Alternative.objects.get(id=data['id'])
        except:
            return HttpResponseBadRequest('Does not exist')

        serializer = AlternativeEditSerializer(lo, data=data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse( {"success": "true"}, status=200)

        return HttpResponseBadRequest('Invalid data')