# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from .models import *

from import_export.admin import ExportMixin
from import_export import resources, widgets
from import_export.fields import Field
from import_export.formats import base_formats

from django.db.models import Q, Count

from masteraula.questions.models import Question, Document, ClassPlan, DocumentDownload

class SchoolInline(admin.TabularInline):
    model = User.schools.through

@admin.register(School)
class SchoolModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    search_fields = ['id', 'name',]
    
    inlines = [SchoolInline, ]
    

class MyUserAdminResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id','name', 'username', 'email', 'about', 'city', 'schools', 'disciplines', 'date_joined')
        export_order = fields
        widgets = {
                'date_joined': {'format': '%d/%m/%Y'},
                }

    def dehydrate_city(self,user):
        if user.city:
            return user.city.name

    def dehydrate_disciplines(self,user):
        itens = user.disciplines.all()
        list_disciplines = []
        for i in itens:
            list_disciplines.append(i.name)

        return(', '.join(list_disciplines))

    def dehydrate_schools(self,user):
        itens = user.schools.all()
        list_schools = []
        for i in itens:
            list_schools.append(i.name)

        return(', '.join(list_schools))

class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

class MyUserCreationForm(UserCreationForm):

    error_message = UserCreationForm.error_messages.update({
        'duplicate_username': 'This username has already been taken.'
    })

    class Meta(UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_('This username has already been taken'))


@admin.register(User)
class MyUserAdmin(ExportMixin, AuthUserAdmin):
    resource_class =  MyUserAdminResource
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    raw_id_fields = ('city', 'schools')
    fieldsets = (
            ('User Profile', {'fields': ('name', 'city', 'schools', 'disciplines',)}),
    ) + AuthUserAdmin.fieldsets
    list_display = ('id', 'username', 'name', 'questions', 'documents', 'downloads', 'plans', 'is_superuser', 'date_joined')
    search_fields = ['id', 'name', 'email', 'schools__name', 'date_joined']
   
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _document_count=Count("document",  distinct=True, filter=Q(document__disabled=False)),
            _question_count=Count("question",  distinct=True, filter=Q(question__disabled=False)),
            _download_count=Count("documentdownload", distinct=True),
            _plan_count=Count("classplan", distinct=True),
        )
        return queryset

    def questions(self, obj):
        return obj._question_count

    def documents(self, obj):
        return obj._document_count

    # def documents_questions(self, obj):
    #     documents = Document.objects.filter(owner=obj).prefetch_related('questions')
    #     dup_questions = []

    #     for doc in documents:
    #         dup_questions += doc.questions.all()
    #     dup_questions = list(set(dup_questions))
                
    #     questions = Question.objects.filter(id__in=dup_questions).count()
    #     return str(questions)

    def downloads(self, obj):
        return obj._download_count

    def plans(self, obj):
        return obj._plan_count

    def export_formats(self):      
        formats = (
                base_formats.CSV,
                base_formats.XLS,
                base_formats.ODS,
                base_formats.JSON,
                base_formats.HTML,
        )
        return [f for f in formats if f().can_export()]

@admin.register(Subscription)
class SubscriptionModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'start_date', 'expiration_date')
    search_fields = ['id', 'user',]
    raw_id_fields = ('user',)