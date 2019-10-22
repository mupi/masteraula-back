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
    list_display = ('id', 'username', 'name', 'is_superuser', 'date_joined')
    search_fields = ['id', 'name', 'email', 'disciplines__name', 'schools__name', 'date_joined']
    
    def get_export_formats(self):
        
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