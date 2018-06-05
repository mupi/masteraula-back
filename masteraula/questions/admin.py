from django.contrib import admin

from .models import Subject


# class SubjectModelAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name',)

#     search_fields = ['name',]

#     list_per_page = 50

# class AlternativeModelAdmin(admin.ModelAdmin):
#     raw_id_fields = ('question', )

#     list_display = ('id', 'question', 'answer_text', 'is_correct')

#     search_fields = ['id', 'answer_text', 'question__statement', 'question__id' ]

#     list_per_page = 100

# class Question_ListModelAdmin(admin.ModelAdmin):
#     raw_id_fields = ('owner', )

#     list_display = ('id', 'header', 'owner',)

#     search_fields = ['id', 'header', 'owner__name' ]

#     list_per_page = 100

# class QuestionQuestion_ListModelAdmin(admin.ModelAdmin):
#     raw_id_fields = ('question', 'question_list' )

#     list_display = ('id', 'question_list', 'question', 'order')

#     search_fields = ['id', 'question_list__id', 'question_list__name', 'question_list__owner' ]

#     list_per_page = 100

# class QuestionsInline(admin.TabularInline):
#     model = Profile.avaiable_questions.through
#     raw_id_fields = ('question',)

# class ProfileModelAdmin(admin.ModelAdmin):
#     raw_id_fields = ('user',)

#     list_display = ('id', 'user', 'credit_balance',)

#     search_fields = ['id', 'user__name', ]

#     inlines = [QuestionsInline,]
#     exclude = ('avaiable_questions',)

#     list_per_page = 100

# admin.site.register(Subject, SubjectModelAdmin)
# admin.site.register(Question,QuestionModelAdmin)
# admin.site.register(Document, Question_ListModelAdmin)
# admin.site.register(DocumentQuestion, QuestionQuestion_ListModelAdmin)
# admin.site.register(Alternative, AlternativeModelAdmin)
# admin.site.register(Profile, ProfileModelAdmin)
