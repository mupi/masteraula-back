from django.contrib import admin

from .models import Question, Answer, Question_List, QuestionQuestion_List, Profile

admin.site.register(Question)
admin.site.register(Question_List)
admin.site.register(QuestionQuestion_List)
admin.site.register(Answer)
admin.site.register(Profile)
