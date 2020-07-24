from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,get_username_max_length)
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from rest_auth.registration import serializers as auth_register_serializers
from rest_auth import serializers as auth_serializers

from rest_framework import serializers, exceptions

from .models import (TermsUse,)

import unicodedata
import ast
import datetime

class TermsUseSerializer(serializers.ModelSerializer):
    last_update = serializers.DateTimeField(format="%Y/%m/%d")

    class Meta:
        model = TermsUse
        fields = (
            'id',
            'content',
            'last_update',
        )