# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.conf import settings

import datetime
from dateutil import relativedelta


#populated by fixture
class State (models.Model):
    uf = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50)
    uf_code = models.CharField(max_length=5)

#populated by fixture
class City (models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=80)
    uf = models.ForeignKey(State, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.uf.uf + " " + self.name
    def __str__(self):
        return self.uf.uf + " " + self.name

class School (models.Model):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class User(AbstractUser):

    def validate_image(fileobj):
        max_size = 1024 * 1024
        if fileobj.size > max_size:
            raise ValidationError(_('Max file size is 1MB'))
            

    name = models.CharField(blank=False, max_length=255,
            validators=[
                validators.RegexValidator(
                    regex='^[A-Za-zÀ-ÿ-´\' ]+$',
                    message=_('Name should contain only valid characters'),
                ),
            ],)
    email = models.EmailField(blank=False, null=False)
    about = models.TextField(blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    schools = models.ManyToManyField(School, blank=True, related_name="teachers")
    disciplines = models.ManyToManyField('questions.Discipline', related_name="users_discipline")
    profile_pic = models.ImageField(null=True, upload_to='profile_pics', validators=[validate_image])

    def __str__(self):
        return self.username

    def premium(self):
        return self.subscription_set.filter(expiration_date__gt=datetime.datetime.now()).count() > 0

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credit_avaiable = models.PositiveIntegerField(null=False, blank=True, default=0)
    credit_spent = models.PositiveIntegerField(null=False, blank=True, default=0)
    question_transactions = models.ManyToManyField('QuestionTransaction', blank=True)

    def __str__(self):
        return u'Profile de %s' % (self.user.username)

from masteraula.questions.models import Question

class QuestionTransaction(models.Model):
    user = models.ForeignKey('Profile', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

def next_month():
    return datetime.datetime.now() + relativedelta.relativedelta(months=1)

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(default=next_month)
    note = models.TextField(null=True, blank=True)

class Contact(models.Model):
    name = models.CharField(blank=False, null=False, max_length=255,
            validators=[
                validators.RegexValidator(
                    regex='^[A-Za-zÀ-ÿ-´\' ]+$',
                    message=_('Name should contain only valid characters'),
                ),
            ],)
    email = models.EmailField(blank=False, null=False) 
    phone = models.CharField(max_length=15, null=True, blank=True)
    message = models.TextField(null=False, blank=False)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def email_contact(self, obj):
        plaintext = get_template('contact/faq_message.txt')
        if not 'phone' in obj:
            phone = ""
        else:
            phone = obj['phone']

        context_message = { 'name': obj['name'], 'email': obj['email'], 'phone': phone, 'message': obj['message']}

        sub = '[Masteraula - FAQ] Mensagem enviada por ' + obj['name']
        subject, from_email, to = sub, settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL
        text_content = plaintext.render(context_message)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.send()  
    