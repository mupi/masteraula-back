# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from django.views.decorators.http import require_http_methods

from masteraula.questions.models import Question, Discipline, Document, User

from django.views import View

class ReportsView(LoginRequiredMixin, View):
    login_url = '/admin/login/'
    template_name = 'reports/base.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/admin/login/?next=%s' % request.path)
        return render(request, self.template_name)


class UncategorizedTagsView(LoginRequiredMixin, View):
    login_url = '/admin/login/'
    template_name = 'reports/uncategorized_questions.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/admin/login/?next=%s' % request.path)
        disciplines = Discipline.objects.all()

        return render(request, self.template_name, {'disciplines' : disciplines})

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/admin/login/?next=%s' % request.path)

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

class NumberDocumentsView(LoginRequiredMixin, View):
    login_url = '/admin/login/'
    template_name = 'reports/number_documents.html'
    

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/admin/login/?next=%s' % request.path)

        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):      
        if not request.user.is_superuser:
            return redirect('/admin/login/?next=%s' % request.path)
        
        data = ''            
        data = 'Usuário,' + 'Provas Ativas, '+ 'Provas Criadas,' + '\n'  
            
        if request.POST['id_users'] != '':
            users = request.POST['id_users']

        else:
            user_id = User.objects.all()
            users = [i.id for i in user_id]  
        
        if type(users) is not list:
            for user in users.split(","):
                documents = Document.objects.filter(owner_id = user).count()
                documents_active = Document.objects.filter(owner_id = user, disabled = False).count()
                data = data + str(user) + ',' + str(documents_active) + ',' + str(documents) + '\n'    
        
        else:
            for user in users:
                documents = Document.objects.filter(owner_id = user).count()
                documents_active = Document.objects.filter(owner_id = user, disabled = False).count()
                data = data + str(user) + ',' + str(documents_active) + ',' + str(documents) + '\n'
    
        response = HttpResponse(data)

        response['Content-Disposition'] = 'attachment; filename="relatorio_provas.csv"'
        return response

