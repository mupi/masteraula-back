from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,get_username_max_length)
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.base import AuthProcess

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.core import validators
from django.contrib.auth import get_user_model

from drf_haystack.serializers import HaystackSerializer, HaystackSerializerMixin

from rest_auth.registration import serializers as auth_register_serializers
from rest_auth.registration.serializers import SocialLoginSerializer, SocialAccountSerializer
from rest_auth import serializers as auth_serializers

from rest_framework import serializers, exceptions

from requests.exceptions import HTTPError

from django.db.models import Count

from .models import User, Profile, City, State, School, Subscription
from masteraula.questions.models import Discipline, Question, Document, ClassPlan, DocumentDownload, LearningObject, Topic

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

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

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

class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = (
            'id',
            'name',
        )
    
    def to_internal_value(self, data):
        try:
            if data and data != 'null':
                return Discipline.objects.get(id=data)
            return None
        except:
            raise serializers.ValidationError(_('Id not found'))

class UserSerializer(serializers.ModelSerializer):
    city = CityEditSerializer(required=False, allow_null=True)
    schools = SchoolSerializer(many = True, required=False, read_only=True)
    disciplines = DisciplineSerializer(many = True, required = False)
    groups = serializers.SerializerMethodField()
    socialaccounts = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    
    def get_groups(self, obj):
        groups = [group.name for group in obj.groups.all()]
        if obj.is_superuser:
            groups.append('admin')
        return groups

    def get_socialaccounts(self, obj):
        return SocialAccountSerializer(SocialAccount.objects.filter(user=obj), many=True).data

    def get_subscription(self, obj):
        return obj.premium()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'name',
            'email',
            'about',
            'city',
            'schools',
            'disciplines',
            'profile_pic',
            'groups',
            'socialaccounts',
            'subscription',
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
        disciplines = validated_data.pop('disciplines')
        instance = super().update(instance, validated_data)
        instance.city = city
        instance.disciplines = disciplines
        instance.save()
        return instance

class SubscriptionSerializer(serializers.ModelSerializer):      
    user = UserSerializer(many = True, read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'id',
            'user',
            'start_date',
            'expiration_date',
            'note',
        )

# django-rest-auth custom serializers
class RegisterSerializer(auth_register_serializers.RegisterSerializer):
    name = serializers.CharField(required=True, validators=[
                validators.RegexValidator(
                    regex='^[A-Za-zÀ-ÿ-´\' ]+$',
                    message=_('Name should contain only valid characters'),
                ),
            ])
    city = serializers.IntegerField(required=False)
    terms_use = serializers.BooleanField(required=True)
    
    def validate_terms_use(self, data):
        if data:
            return data
       
        msg = _('Terms use not accept')
        raise exceptions.ValidationError(msg)
        
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


class SocialOnlyLoginSerializer(SocialLoginSerializer):
    def validate(self, attrs):
        view = self.context.get('view')
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                _("View is not defined, pass it as a context variable")
            )

        adapter_class = getattr(view, 'adapter_class', None)
        if not adapter_class:
            raise serializers.ValidationError(_("Define adapter_class in view"))

        adapter = adapter_class(request)
        app = adapter.get_provider().get_app(request)

        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token

        # Case 1: We received the access_token
        if attrs.get('access_token'):
            access_token = attrs.get('access_token')

        # Case 2: We received the authorization code
        elif attrs.get('code'):
            self.callback_url = getattr(view, 'callback_url', None)
            self.client_class = getattr(view, 'client_class', None)

            if not self.callback_url:
                raise serializers.ValidationError(
                    _("Define callback_url in view")
                )
            if not self.client_class:
                raise serializers.ValidationError(
                    _("Define client_class in view")
                )

            code = attrs.get('code')

            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope
            )
            token = client.get_access_token(code)
            access_token = token['access_token']

        else:
            raise serializers.ValidationError(
                _("Incorrect input. access_token or code is required."))

        social_token = adapter.parse_token({'access_token': access_token})
        social_token.app = app

        try:
            login = self.get_social_login(adapter, app, social_token, access_token)
            complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))

        if not login.is_existing:
            raise serializers.ValidationError(_("Não há usuários associados a esta rede social"))

        attrs['user'] = login.account.user

        return attrs

class TopicListSerializer(serializers.ModelSerializer):
    num_questions = serializers.IntegerField(read_only=True)
    per_questions = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'num_questions',
            'per_questions'
        )
    
    def get_per_questions(self, obj):
        qtde_questions = Question.objects.filter(disabled=False).count()
        per_questions = (obj.num_questions * 100) / qtde_questions
        return round(per_questions, 2)

class DashboardSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    documents_questions = serializers.SerializerMethodField()
    downloads = serializers.SerializerMethodField()
    plans = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    total_objects = serializers.SerializerMethodField()
    total_topics = serializers.SerializerMethodField()
    topics_questions = serializers.SerializerMethodField('topics_questions_serializer')

    def topics_questions_serializer(self, obj):
        topics = Topic.objects.all().annotate(num_questions=Count('question')).order_by('-num_questions')
        return TopicListSerializer(topics[:10], many=True).data
    
    class Meta:
        model = User
        fields = (
            'questions',
            'documents', 
            'documents_questions', 
            'downloads', 'plans', 
            'total_questions', 
            'total_objects', 
            'total_topics', 
            'topics_questions'
            )
    
    def get_questions(self, obj):
        question = Question.objects.filter(author=obj, disabled=False).count()
        return question

    def get_documents(self, obj):
        documents = Document.objects.filter(owner=obj, disabled=False).count()
        return documents

    def get_documents_questions(self, obj):
        documents = Document.objects.filter(owner=obj).prefetch_related('questions')
        dup_questions = []

        for doc in documents:
            for q in doc.questions.all():
                if q.id not in dup_questions:
                    dup_questions.append(q.id)

        questions = Question.objects.filter(id__in=dup_questions).count()
        return questions

    def get_downloads(self, obj):
        downloads = DocumentDownload.objects.filter(user=obj).count()
        return downloads

    def get_plans(self, obj):
        plans = ClassPlan.objects.filter(owner=obj).count()
        return plans

    def get_total_questions(self, obj):
        questions = Question.objects.filter(disabled=False).count()
        return questions

    def get_total_objects(self, obj):
        objects = LearningObject.objects.all().count()
        return objects

    def get_total_topics(self, obj):
        topics = Topic.objects.all().count()
        return topics