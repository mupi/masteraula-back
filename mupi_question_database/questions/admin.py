from django.contrib import admin

from .models import Question, Answer, Question_List, QuestionQuestion_List, Profile, Subject


class QuestionModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('question_parent', )

    list_display = ('id', 'question_statement',)

    search_fields = ['id', 'question_statement',]

    list_per_page = 50

class AnswerModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('question', )

    list_display = ('id', 'question', 'answer_text', 'is_correct')

    search_fields = ['id', 'answer_text', 'question__question_statement', 'question__id' ]

    list_per_page = 100

class Question_ListModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('cloned_from', 'owner' )

    list_display = ('id', 'question_list_header', 'owner', 'secret')

    search_fields = ['id', 'question_list_header', 'owner__name' ]

    list_per_page = 100

class QuestionQuestion_ListModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('question', 'question_list' )

    list_display = ('id', 'question_list', 'question', 'order')

    search_fields = ['id', 'question_list__id', 'question_list__name', 'question_list__owner' ]

    list_per_page = 100

class QuestionsInline(admin.TabularInline):
    model = Profile.avaiable_questions.through
    raw_id_fields = ('question',)

class ProfileModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)

    list_display = ('id', 'user', 'credit_balance',)

    search_fields = ['id', 'user__name', ]

    inlines = [QuestionsInline,]
    exclude = ('avaiable_questions',)

    list_per_page = 100

admin.site.register(Question,QuestionModelAdmin)
admin.site.register(Question_List, Question_ListModelAdmin)
admin.site.register(QuestionQuestion_List, QuestionQuestion_ListModelAdmin)
admin.site.register(Answer, AnswerModelAdmin)
admin.site.register(Profile, ProfileModelAdmin)
admin.site.register(Subject)
