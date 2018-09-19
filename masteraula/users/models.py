# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core import validators


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

@python_2_unicode_compatible
class User(AbstractUser):

    name = models.CharField(blank=False, max_length=255,
            validators=[
                validators.RegexValidator(
                    regex='^[A-Za-zÀ-ÿ ]+$',
                    message='Name should contain only valid characters',
                ),
            ],)
    email = models.EmailField(blank=False, null=False)
    about = models.TextField(blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.username

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