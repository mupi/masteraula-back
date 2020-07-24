# -*- coding: utf-8 -*-
import os
import time
import datetime
import operator

from functools import reduce

from rest_framework import (generics, response, viewsets, status, mixins, exceptions, pagination, permissions)
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.response import Response

from django.http import HttpResponse, FileResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .models import (TermsUse,)

from . import serializers as serializers

class TermsUseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TermsUse.objects.all().order_by('id')
    serializer_class = serializers.TermsUseSerializer
    pagination_class = None