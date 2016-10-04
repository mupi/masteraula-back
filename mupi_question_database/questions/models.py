import datetime

from django.db import models
from mupi_question_database.users.models import User

from taggit.managers import TaggableManager

class Question(models.Model):
    LEVEL_CHOICES = (
        ("E", "EASY"),
        ("M", "MEDIUM"),
        ("H", "HARD")
    )

    question_text = models.CharField(max_length=200)
    question_header = models.CharField(max_length=50)
    resolution = models.CharField(max_length=50, null=True, blank=True)
    level = models.CharField(max_length=1, choices = LEVEL_CHOICES, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    create_date = models.DateTimeField()

    tags = TaggableManager()

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return u'QuestionId%d %s' % (self.pk ,self.question_text)


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=100)
    is_correct = models.BooleanField()

    class Meta:
        ordering = ['question', 'pk']

    def __str__(self):
        return u'QuestionId: %d AnswerId: %d' % (self.question.pk, self.pk)


class Question_List(models.Model):
    question_list_header = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)
    create_date = models.DateTimeField()

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return u'ListId: %d Header: %d' % (self.pk, self.question_list_header)
