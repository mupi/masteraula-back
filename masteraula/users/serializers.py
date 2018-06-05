from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,get_username_max_length)
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from drf_haystack.serializers import HaystackSerializer, HaystackSerializerMixin

from rest_auth.registration import serializers as auth_register_serializers
from rest_auth import serializers as auth_serializers

from rest_framework import serializers, exceptions

from .models import User, Profile

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'name',
            'email'
        )
        extra_kwargs = {'username': {'required' : True}}

# django-rest-auth custom serializers
class RegisterSerializer(auth_register_serializers.RegisterSerializer):

    def save(self, request):
        user = super().save(request)

        # Adiciona um profile para o respectivo usuario
        Profile.objects.create(user=user)
        return user

class LoginSerializer(auth_serializers.LoginSerializer):

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            # Authentication through email
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
                user = self._validate_email(email, password)

            # Authentication through username
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
                user = self._validate_username(username, password)

            # Authentication through either username or email
            else:
                user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise exceptions.ValidationError(msg)

        # If required, is the email verified?
        if not user.is_superuser and 'rest_auth.registration' in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise serializers.ValidationError(_('E-mail is not verified.'))

        user = User.objects.get(id=user.id)
        attrs['user'] = user
        return attrs

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'name')
        read_only_fields = ('username', 'email')


class JWTSerializer(serializers.Serializer):
    """
    Serializer for JWT authentication.
    """
    token = serializers.CharField()
    user = UserSerializer()
