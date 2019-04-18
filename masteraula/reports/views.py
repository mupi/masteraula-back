# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.contrib.auth.mixins import UserPassesTestMixin

from django.views.decorators.http import require_http_methods

from masteraula.questions.models import Question, Discipline, Document, LearningObject, User

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
        clean2 = []

        for _, stm in statements:
            while(program.search(stm)):
                stm = program.sub('<p>\\1</p>', stm)
            clean.append(stm)

        for stm in clean:
            while(program2.search(stm)):
                stm = program2.sub('', stm)
            soup = bs(stm, "html.parser")
            clean2.append(soup.prettify())

        data = []
        for i in range(len(clean2)):
            soup = bs(statements[i][1], "html.parser")
            stmt = soup.prettify()
            data.append((statements[i][0], stmt, clean2[i]))
        
        context['data'] = data

        return super().render_to_response(context)


class StatemensWithTextoAssociado(SuperuserMixin, TemplateView):
    template_name = 'reports/statements_with_texto_associado.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        return context


    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='texto_associado_questao').order_by('id')
            statements = [(q.id, q.statement) for q in questions]
        else:
            return super().render_to_response(context)
        
        program = re.compile('<p[^<]*texto_associado_questao[^<]*>(.*?)<\/p>')

        clean = []

        for _, stm in statements:
            while(program.search(stm)):
                if program.match(stm).groups()[0] != '':
                    stm = program.sub('<p>\\1</p>', stm)
                else:
                    stm = program.sub('', stm)
            clean.append(stm)

        data = []
        for i in range(len(clean)):
            soup = bs(statements[i][1], "html.parser")
            stmt = soup.prettify()
            soup = bs(clean[i], "html.parser")
            clean_stmt = soup.prettify()
            data.append((statements[i][0], stmt, clean_stmt))
        
        context['data'] = data

        return super().render_to_response(context)


class ObjectsWithoutSource(SuperuserMixin, TemplateView):
    template_name = 'reports/objects_without_source.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        return context


    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            learning_objects = LearningObject.objects.filter(Q(source__isnull=True) | Q(source='')).order_by('id')
            clean = []
            for lo in learning_objects:
                if lo.question_set.filter(disciplines__in=disciplines).count() > 0:
                    clean.append(lo)
        else:
            return super().render_to_response(context)

        data = []
        for lo in clean:
            data.append(lo)
        
        context['data'] = data

        return super().render_to_response(context)


class ObjectsWithBrInsideP(SuperuserMixin, TemplateView):
    template_name = 'reports/objects_with_br.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        return context


    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='br').order_by('id')
            clean = []
            for lo in learning_objects:
                if lo.question_set.filter(disciplines__in=disciplines).count() > 0:
                    clean.append(lo)
        else:
            return super().render_to_response(context)

        program = re.compile('(<p>((?!</p>)[\s\S])*)(<[\/\s]*?br[\/\s]*?>)([\s\S]*?<\/p>)')             
        clean = []
        statements = []

        all_texts = [(q.id, q.text) for q in learning_objects]

        for qid, stmt in all_texts:
            has = False
            stm = stmt

            while(program.search(stm)):
                stm = program.sub('\\1 </p><p> \\4', stm)
                has = True
            if has:
                statements.append((qid, stmt))
                clean.append(stm)

        data = []
        for i in range(len(clean)):
            data.append((statements[i][0], statements[i][1], clean[i]))
        
        context['data'] = data

        return super().render_to_response(context)



class StatemensUpdateView(SuperuserMixin, View):
    def post(self, request, *args, **kwargs):
        pass
        # question_id = request.POST.get('questionId', None)
        # new_statament = request.POST.get('statement', None)

        # if question_id == None or new_statament == None:
        #     return HttpResponseBadRequest()

        # question = Question.objects.get(id=question_id)
        # question.statement = new_statament
        # question.save()

        # return JsonResponse( {"success": "true"}, status=200)

class LearningObjectUpdateView(SuperuserMixin, View):
    def post(self, request, *args, **kwargs):
        pass
        # lo_id = request.POST.get('learningObjectId', None)
        # source = request.POST.get('source', None)
        # is_image = request.POST.get('is_image')
        # new_text = request.POST.get('text', None)

        # if lo_id == None or source == None:
        #     return HttpResponseBadRequest()

        # learning_object = LearningObject.objects.get(id=lo_id)
        # if is_image == 'false':
        #     learning_object.text = new_text
        # learning_object.source = source
        # learning_object.save()

        # return JsonResponse( {"success": "true"}, status=200)