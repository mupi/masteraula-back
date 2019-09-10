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

class SchoolInline(admin.TabularInline):
    model = School

class SchoolModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city')
    search_fields = ['id', 'name',]
    list_per_page = 100

    inlines = [SchoolInline,]

class MyUserAdminResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id','name', 'username', 'email', 'about', 'city', 'school', 'disciplines', 'date_joined')
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

    def dehydrate_school(self,user):
        itens = user.school.all()
        list_school = []
        for i in itens:
            list_school.append(i.name)

        return(', '.join(list_disciplines))

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
    raw_id_fields = ('city', 'school')
    fieldsets = (
            ('User Profile', {'fields': ('name', 'city', 'school', 'disciplines',)}),
    ) + AuthUserAdmin.fieldsets
    list_display = ('id', 'username', 'name', 'is_superuser', 'date_joined')
    search_fields = ['id', 'name', 'email', 'disciplines__name', 'school__name', 'date_joined']
    
    def get_export_formats(self):
        
        formats = (
                base_formats.CSV,
                base_formats.XLS,
                base_formats.ODS,
                base_formats.JSON,
                base_formats.HTML,
        )
        return [f for f in formats if f().can_export()]

admin.site.register(School, )