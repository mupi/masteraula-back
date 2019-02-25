# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.http import require_http_methods

from masteraula.questions.models import Question, Discipline
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
            disciplines_names = [d.name for d in Discipline.objects.filter(id__in=disciplines)]
            filename =  '_'.join(disciplines_names)
            questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        else:
            filname = 'all'
            questions = Question.objects.all().order_by('id')
        
        data = ''
        for question in questions:
            if question.tags.count() == 0:
                data = data + '%d, https://masteraula.com.br/#/edit-question/%d\n' % (question.id, question.id)
    
        response = HttpResponse(
            data, 'text/csv'
        )
        response['Content-Disposition'] = 'attachment, filename="%s.csv"' % filename
        return response