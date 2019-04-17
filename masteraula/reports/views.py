# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse

from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.contrib.auth.mixins import UserPassesTestMixin

from django.views.decorators.http import require_http_methods

from masteraula.questions.models import Question, Discipline, Document, User

from django.views import View
from django.views.generic import TemplateView

from bs4 import BeautifulSoup as bs

import re

class SuperuserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class ReportsView(SuperuserMixin, TemplateView):
    login_url = '/admin/login/'
    template_name = 'reports/base.html'


class UncategorizedTagsView(SuperuserMixin, TemplateView):
    login_url = '/admin/login/'
    template_name = 'reports/uncategorized_questions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        return context

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


class StatemensWithDivView(SuperuserMixin, TemplateView):
    template_name = 'reports/statements_with_div.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        return context


    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='<div').order_by('id')
            statements = [(q.id, q.statement) for q in questions]
        else:
            return super().render_to_response(context)
        
        program = re.compile('<div[^<]*>(.*?)<\/div>')             
        program2 = re.compile('<div[^<]*>') 

        clean = []
        removed = []
        clean2 = []
        removed2 = []

        for _, stm in statements:
            curr_removed = []
            while(program.search(stm)):
                curr_removed.append(program.findall(stm))
                stm = program.sub('<p>\\1</p>', stm)
            removed.append(curr_removed)
            clean.append(stm)

        for stm in clean:
            curr_removed = []
            while(program2.search(stm)):
                curr_removed.append(program.findall(stm))
                stm = program2.sub('', stm)
            removed2.append(curr_removed)
            soup = bs(stm, "html.parser")
            clean2.append(soup.prettify())

        data = []
        for i in range(len(clean2)):
            soup = bs(statements[i][1], "html.parser")
            stmt = soup.prettify()
            data.append((statements[i][0], stmt, clean2[i]))
        
        context['data'] = data

        return super().render_to_response(context)

class StatemensUpdateView(SuperuserMixin, View):
    def post(self, request, *args, **kwargs):
        question_id = request.POST.get('questionId', None)
        new_statament = request.POST.get('statement', None)

        if question_id == None or new_statament == None:
            return HttpResponseBadRequest()

        question = Question.objects.get(id=question_id)
        question.statement = new_statament
        question.save()

        return JsonResponse( {"success": "true"}, status=200)