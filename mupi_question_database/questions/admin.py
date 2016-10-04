from django.contrib import admin

from .models import Question, Answer, Question_List

admin.site.register(Question)
admin.site.register(Question_List)
admin.site.register(Answer)
