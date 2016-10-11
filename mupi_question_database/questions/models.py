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

    question_header = models.CharField(max_length=50)
    question_text = models.CharField(max_length=1000)
    resolution = models.CharField(max_length=500, null=True, blank=True)
    level = models.CharField(max_length=1, choices = LEVEL_CHOICES, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    create_date = models.DateTimeField(auto_now_add=True)

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
        return u'QuestionId: %d AnswerId: %d Correct: %s' % (
        self.question.pk, self.pk, ("Yes" if self.is_correct else "No"))


class Question_List(models.Model):
    question_list_header = models.CharField("Nome da Lista", max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return u'ListId: %d Header: %s' % (self.pk, self.question_list_header)
