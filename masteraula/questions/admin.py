from import_export.admin import ExportMixin
from django.contrib import admin
from import_export import resources, widgets
from import_export.fields import Field
from import_export.formats import base_formats

from .models import (Discipline, TeachingLevel, LearningObject, Descriptor, Question,
                     Alternative, Document, DocumentQuestion, Header, Year, Source, Topic, Search,
                     DocumentDownload)

class SearchResource(resources.ModelResource):
    
    class Meta:
        model = Search
        fields = ('id','user', 'term', 'disciplines', 'teaching_levels', 'difficulty', 'source', 'year', 'date_search')
        widgets = {
                'date_search': {'format': '%d/%m/%Y'},
                }

    def dehydrate_disciplines(self,search):
        itens = search.disciplines.all()
        list_disciplines = []
        for i in itens:
            list_disciplines.append(i.name)

        return(', '.join(list_disciplines))

    def dehydrate_teaching_levels(self,search):
        itens = search.teaching_levels.all()
        list_levels = []
        for i in itens:
            list_levels.append(i.name)

        return(', '.join(list_levels))

class DocumentResource(resources.ModelResource):
    question_counter = Field(column_name='question_counter')
    
    class Meta:
        model = DocumentDownload
        fields = ('id','user', 'user__name', 'document', 'download_date', 'answers')
        export_order = fields
        widgets = {
                'download_date': {'format': '%d/%m/%Y'},
                }
                

    def dehydrate_document(self, documentDownload):
        return documentDownload.document.name

    def dehydrate_question_counter(self, documentDownload):
        return '{}'.format(documentDownload.document.questions.count())


class LearningObjectQuestionsInline(admin.TabularInline):
    model = Question.learning_objects.through
    raw_id_fields = ('question',)

class DocumentQuestionsInline(admin.TabularInline):
    model = Document.questions.through
    raw_id_fields = ('question',)

class AlternativesInline(admin.TabularInline):
    model = Alternative

class TopicsInline(admin.TabularInline):
    model = Topic

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

class YearModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ['id', 'name',]
    list_per_page = 100

class SourceModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ['id', 'name',]
    list_per_page = 100

class TopicModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('parent', )
    list_display = ('id', 'name',)
    search_fields = ['id', 'name',]
    list_per_page = 100

    inlines = [TopicsInline,]

class LearningObjectModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', )
    search_fields = ['id', 'name', 'source', 'tags__name']
    list_display = ('id', 'source', 'image', 'text', 'tag_list')
    search_fields = ['id','source', 'text']
    list_per_page = 100

    inlines = [LearningObjectQuestionsInline,]

    def get_queryset(self, request):
        return super(LearningObjectModelAdmin, self).get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

class QuestionModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'learning_objects', 'topics')
    list_display = ('id', 'statement', 'year', 'source', 'tag_list','disabled',)
    search_fields = ['id', 'year', 'source', 'statement', 'tags__name']

    inlines = [AlternativesInline, ]

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
    list_display = ('id', 'owner_id', 'owner_name', 'owner_email', 'name', 'create_date', 'secret', 'disabled',)
    search_fields = ['id', 'owner__id', 'owner__name', 'owner__email', 'name', 'create_date']

    inlines = [DocumentQuestionsInline, ]

    list_per_page = 100

    def owner_name(self, obj):
        return obj.owner.name

    def owner_email(self, obj):
        return obj.owner.email

class HeaderModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner',)
    list_display = ('id', 'name', 'institution_name', 'professor_name',)
    search_fields = ['id', 'name']

    list_per_page = 100

class SearchModelAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SearchResource
    raw_id_fields = ('user',)
    list_display = ('id', 'user_id', 'user', 'term', 'date_search')
    search_fields = ['id', 'user__name', 'term', 'date_search']
    list_per_page = 100

    def get_export_formats(self):
        
        formats = (
                base_formats.CSV,
                base_formats.XLS,
                base_formats.ODS,
                base_formats.JSON,
                base_formats.HTML,
        )
        return [f for f in formats if f().can_export()]

class DocumentDownloadModelAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = DocumentResource
    raw_id_fields = ('user',)
    list_display = ('id', 'user_id', 'user', 'document')
    search_fields = ['id', 'user__name', 'user__id', 'document__name']
    list_per_page = 100

    def get_export_formats(self):
        
        formats = (
                base_formats.CSV,
                base_formats.XLS,
                base_formats.ODS,
                base_formats.JSON,
                base_formats.HTML,
        )
        return [f for f in formats if f().can_export()]

admin.site.register(Discipline, DisciplineModelAdmin)
admin.site.register(Descriptor, DescriptorModelAdmin)
admin.site.register(TeachingLevel, TeachingLeveltModelAdmin)
admin.site.register(Year, YearModelAdmin)
admin.site.register(Source, SourceModelAdmin)
admin.site.register(Topic, TopicModelAdmin)
admin.site.register(LearningObject, LearningObjectModelAdmin)
admin.site.register(Alternative, AlternativeModelAdmin)
admin.site.register(Question, QuestionModelAdmin)
admin.site.register(Document, DocumentModelAdmin)
admin.site.register(Header, HeaderModelAdmin)
admin.site.register(Search, SearchModelAdmin)
admin.site.register(DocumentDownload, DocumentDownloadModelAdmin)