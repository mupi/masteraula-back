from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,get_username_max_length)
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.core import validators

from drf_haystack.serializers import HaystackSerializer, HaystackSerializerMixin

from rest_auth.registration import serializers as auth_register_serializers
from rest_auth import serializers as auth_serializers

from rest_framework import serializers, exceptions

from .models import User, Profile, City, State

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id' ,'name', 'uf')
        read_only_fields = ('name',)

    def to_internal_value(self, data):
        try:
            city = City.objects.get(id=data)
            return city
        except:
            raise serializers.ValidationError(_('City does not exist 0'))

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ('uf' ,'name',)


class CityEditSerializer(serializers.Field):
    def to_internal_value(self, data):
        try:
            if data and data != 'null':
                return City.objects.get(id=data)
            return None
        except:
            raise serializers.ValidationError(_('City does not exist 1'))

    def to_representation(self, data):
        try:
            if data:
                return {'id' : data.id ,'name' : data.name, 'uf' : data.uf.uf}
            return None
        except:
            raise serializers.ValidationError(_('City does not exist 2'))

class UserSerializer(serializers.ModelSerializer):
    city = CityEditSerializer(required=False, allow_null=True)
    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        groups = [group.name for group in obj.groups.all()]
        if obj.is_superuser:
            groups.append('admin')
        print(groups)
        return groups

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'name',
            'email',
            'about',
            'city',
            'profile_pic',
            'groups',
        )
        read_only_fields = ('username', 'email', 'groups'),
        extra_kwargs = {
        "name": {
            "validators":  [
                validators.RegexValidator(
                    regex='^[A-Za-zÀ-ÿ-´\' ]+$',
                    message=_('Name should contain only valid characters'),
                ),
            ],
        },
    }

    def create(self, validated_data):
        city = validated_data.pop('city')
        user = super().create(validated_data)
        user.city = city
        user.save()
        return user

    def update(self, instance, validated_data):
        city = validated_data.pop('city')
        instance = super().update(instance, validated_data)
        instance.city = city
        instance.save()
        return instance

# django-rest-auth custom serializers
class RegisterSerializer(auth_register_serializers.RegisterSerializer):
    name = serializers.CharField(required=True, validators=[
                validators.RegexValidator(
                    regex='^[A-Za-zÀ-ÿ-´\' ]+$',
                    message=_('Name should contain only valid characters'),
                ),
            ])
    city = serializers.IntegerField(required=False)
    
    def validate_city(self, data):
        try:
            City.objects.get(id=data)
            return data
        except:
            raise serializers.ValidationError(_('City does not exist'))

    def custom_signup(self, request, user):
        user.name = self.validated_data.get('name', '')
        if 'city' in self.validated_data:
            city_id = self.validated_data.get('city', '')
            user.city = City.objects.get(id=city_id)

            user.save(update_fields=['name', 'city'])
        else:
            user.save(update_fields=['name'])

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

class ResendConfirmationEmailSerializer(auth_serializers.LoginSerializer):

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
                if email_address.verified:
                    raise serializers.ValidationError(_('Confirmation e-mail already verified.'))
                email_address.send_confirmation(
                    request=self.context.get('request')
                )

        user = User.objects.get(id=user.id)
        attrs['user'] = user
        return attrs

class PasswordChangeSerializer(auth_serializers.PasswordChangeSerializer):

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.old_password_field_enabled,
            self.user,
            not self.user.check_password(value)
        )

        if all(invalid_password_conditions):
            raise serializers.ValidationError(_('Invalid password'))
        return value

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'name',)
        read_only_fields = ('username', 'email')

class JWTSerializer(serializers.Serializer):
    """
    Serializer for JWT authentication.
    """
    token = serializers.CharField()
    user = UserSerializer()
