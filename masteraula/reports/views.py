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

from masteraula.questions.models import Question, Discipline, Document, LearningObject, User

from .serializers import QuestionStatementEditSerializer, LearningObjectEditSerializer

from bs4 import BeautifulSoup as bs

import json
import re

class SuperuserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class DisciplineReportsBaseView(SuperuserMixin, TemplateView):
    login_url = '/admin/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = Discipline.objects.all()
        context['header'] =  self.header if hasattr(self, 'header') else 'Relatório'
        return context

def process_tags_br(text):
    program = re.compile('(<[\/\s]*?br[\s]*?>)')

    while(program.search(text)):
        text = program.sub('<br/>', text)
    return text

def process_tags_div(all_ids, all_texts, force_stay=False, get_status=False):
    program = re.compile('<div[^<]*>(.*?)<\/div>')             
    program2 = re.compile('<div[^<]*>') 

    clean = []
    clean2 = []
    texts = []
    ids = []
    status = []

    for _id, text in zip(all_ids, all_texts):
        has = False
        clean_text = text

        while(program.search(clean_text)):
            has = True
            clean_text = program.sub('<p>\\1</p>', clean_text)
        if has or force_stay:
            ids.append(_id)
            texts.append(text)
            clean.append(clean_text)
            status.append('Removed <div>' if has else '')
    
    for text in clean:
        while(program2.search(text)):
            text = program2.sub('', text)
        clean2.append(text)

    if get_status:
        return (ids, texts, clean2, status)
    return ids, texts, clean2

def process_tags_br_inside_p(all_ids, all_texts, force_stay=False, get_status=False):
    program = re.compile('(<p((?!</p>)[\s\S])*>((?!</p>)[\s\S])*)(<[\/\s]*?br[\/\s]*?>)([\s\S]*?<\/p>)')
    clean = []
    texts = []
    ids = []
    status = []

    for _id, text in zip(all_ids, all_texts):
        has = False
        clean_text = text

        while(program.search(clean_text)):
            clean_text = program.sub('\\1 </p><p> \\5', clean_text)
            has = True
        if has or force_stay:
            ids.append(_id)
            texts.append(text)
            clean.append(clean_text)
            status.append('Removed <br> inside <p>' if has else '')
    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def process_tags_texto_associado_inside_p(all_ids, all_texts, force_stay=False, get_status=False):
    program = re.compile('<p[^<]*texto_associado_questao[^<]*>([\s\S]*?)<\/p>')
    clean = []
    texts = []
    ids = []
    status = []

    for _id, text in zip(all_ids, all_texts):
        has = False
        clean_text = text

        while(program.search(clean_text)):
            has = True
            if program.search(clean_text).groups()[0].strip() != '':
                clean_text = program.sub('<p>\\1</p>', clean_text)
            else:
                clean_text = program.sub('', clean_text)
        if has or force_stay:
            ids.append(_id)
            texts.append(text)
            clean.append(clean_text)
            status.append('Replace texto_associado_questao' if has else '')
    if get_status:
        return ids, texts, clean, status
    return ids, texts, clean

def prepare_texts_data(ids, texts, clean, all_status=None):
    data = []
    if all_status is None:
        all_status = [None] * len(ids)
    for _id, text, clean_text, status in zip(ids, texts, clean, all_status):
        soup = bs(text, "html.parser")
        text = soup.prettify()

        soup = bs(clean_text, "html.parser")
        clean_text = soup.prettify()

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

class StatementsAllFilter(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Todas as detecções'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        if disciplines and questions.count() > 0:
            ids, texts = zip(*[(q.id, process_tags_br(q.statement)) for q in questions])
        else:
            return super().render_to_response(context)
        
        ids1, _, _ = process_tags_div(ids, texts)
        ids2, _, _ = process_tags_br_inside_p(ids, texts)
        ids3, _, _ = process_tags_texto_associado_inside_p(ids, texts)

        ids = list(set(ids1 + ids2 + ids3))
        
        if not ids:
            return super().render_to_response(context)

        questions = Question.objects.filter(id__in=ids).order_by('id')
        if questions.count() > 0:
            ids, texts = zip(*[(q.id, process_tags_br(q.statement)) for q in questions])

        _, _, clean, status1 = process_tags_div(ids, texts, True, True)
        _, _, clean, status2 = process_tags_br_inside_p(ids, clean, True, True)
        _, _, clean, status3 = process_tags_texto_associado_inside_p(ids, clean, True, True)
        context['data'] = prepare_texts_data(ids, texts, clean, list(zip(status1, status2, status3)))

        return super().render_to_response(context)

class StatemensWithDivView(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com <div>'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='<div').order_by('id')
        if disciplines and questions.count() > 0:
            ids, texts = zip(*[(q.id, process_tags_br(q.statement)) for q in questions])
        else:
            return super().render_to_response(context)
        
        ids, texts, clean = process_tags_div(ids, texts)
        context['data'] = prepare_texts_data(ids, texts, clean)

        return super().render_to_response(context)


class StatemensWithTextoAssociado(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com texto associado'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='texto_associado_questao').order_by('id')
        if disciplines and questions.count() > 0:
            ids, texts = zip(*[(q.id, process_tags_br(q.statement)) for q in questions])
        else:
            return super().render_to_response(context)

        ids, texts, clean = process_tags_texto_associado_inside_p(ids, texts)
        context['data'] = prepare_texts_data(ids, texts, clean)
        context['header'] = 'Questões com texto associado'

        return super().render_to_response(context)


class StatemensWithBrInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tag <br> dentro de <p>'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='br').order_by('id')
        if disciplines and questions.count() > 0:
            ids, texts = zip(*[(q.id, process_tags_br(q.statement)) for q in questions])
        else:
            return super().render_to_response(context)

        ids, texts, clean = process_tags_br_inside_p(ids, texts)
        context['data'] = prepare_texts_data(ids, texts, clean)

        return super().render_to_response(context)


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


class ObjectsWithBrInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com <br> dentro de <p>'
    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='br') \
                    .filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects and learning_objects.count() > 0:
            ids, texts = zip(*[(lo.id, process_tags_br(lo.text)) for lo in learning_objects])
        else:
            return super().render_to_response(context)

        ids, texts, clean = process_tags_br_inside_p(ids, texts)
        context['data'] = prepare_texts_data(ids, texts, clean)

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