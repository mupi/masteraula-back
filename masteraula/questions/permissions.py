from rest_framework import permissions
from django.db.models import Q

from masteraula.users.models import Subscription
from masteraula.questions.models import DocumentDownload

import datetime

class QuestionPermission(permissions.BasePermission):
    """Só poderá editar a questão se o usuário for autenticado"""
   
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if obj.author == request.user:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True

class LearningObjectPermission(permissions.BasePermission):
    """Só poderá editar o objeto se o usuário for autenticado"""
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        
class DocumentsPermission(permissions.BasePermission):
    """Regras: 
    - Qualquer usuário logado pode criar um documento;
    - Só podem editar um documento o autor desse documento e o super_usuario."""

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action == 'copy_document':
            return True
        if request.user.is_superuser:
           return True
        return obj.owner == request.user

class HeaderPermission(permissions.BasePermission):
    """Regras: 
    - Qualquer usuário logado pode criar um cabeçalho;
    - Só pode editar e visualizar um cabeçalho o autor e o super_usuario."""

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
       
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
           return True
        return obj.owner == request.user

class DocumentDownloadPermission(permissions.BasePermission):
    """3 download por usuário se não for premium"""

    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated:
            return False

        now = datetime.datetime.now()
        premium = Subscription.objects.filter(Q(user=request.user) & Q(expiration_date__gt=now)).count()

        if premium:
            return True
        if DocumentDownload.objects.filter(Q(user=request.user) & Q(download_date__month=now.month)).count() < 3:
            return True
        return False