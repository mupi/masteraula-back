from django.contrib import admin

from .models import (Discipline, TeachingLevel, LearningObject, Descriptor, Question,
                     Alternative, Document, DocumentQuestion)

class QuestionsInline(admin.TabularInline):
    model = Document.questions.through
    raw_id_fields = ('question',)


class AlternativesInline(admin.TabularInline):
    model = Alternative



class DisciplineModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ['id', 'name',]
    list_per_page = 100

class DescriptorModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ['id', 'name',]
    list_per_page = 100

class TeachingLeveltModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ['id', 'name']
    list_per_page = 100

class LearningObjectModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', )
    # list_display = ('id', 'name', 'image', 'text', 'tag_list')
    # search_fields = ['id', 'name',]
    list_display = ('id', 'source', 'image', 'text', 'tag_list')
    search_fields = ['id',]
    list_per_page = 100

    def get_queryset(self, request):
        return super(LearningObjectModelAdmin, self).get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

class QuestionModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'learning_objects', 'disciplines')
    list_display = ('id', 'statement', 'year', 'source', 'tag_list')
    search_fields = ['id', 'year', 'source', 'statement']

    inlines = [AlternativesInline,]

    list_per_page = 100

    def get_queryset(self, request):
        return super(QuestionModelAdmin, self).get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())
    
class AlternativeModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('question', )
    list_display = ('id', 'question', 'text', 'is_correct',)
    search_fields = ['id', 'text', 'question__statement', 'question__id']

    list_per_page = 100

class DocumentModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner',)
    list_display = ('id', 'name', 'create_date', 'secret',)
    search_fields = ['id', 'name']

    inlines = [QuestionsInline, ]

    list_per_page = 100


admin.site.register(Discipline, DisciplineModelAdmin)
admin.site.register(Descriptor, DescriptorModelAdmin)
admin.site.register(TeachingLevel, TeachingLeveltModelAdmin)
admin.site.register(LearningObject, LearningObjectModelAdmin)
admin.site.register(Alternative, AlternativeModelAdmin)
admin.site.register(Question, QuestionModelAdmin)
admin.site.register(Document, DocumentModelAdmin)