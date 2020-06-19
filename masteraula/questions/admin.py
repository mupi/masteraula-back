from import_export.admin import ExportMixin, ImportMixin
from django.contrib import admin
from import_export import resources, widgets
from import_export.fields import Field
from import_export.formats import base_formats

from .models import (Discipline, TeachingLevel, LearningObject, Descriptor, Question,
                     Alternative, Document, DocumentQuestion, Header, Year, Source, Topic, Search,
                     DocumentDownload, DocumentPublication, Synonym, Label, Link, TeachingYear, ClassPlan, Station, FaqCategory, FaqQuestion, DocumentOnline, Result, DocumentQuestionOnline, StudentAnswer)

class SearchResource(resources.ModelResource):
    
    class Meta:
        model = Search
        fields = ('id','user', 'user__name', 'term', 'disciplines', 'teaching_levels', 'difficulty', 'source', 'year', 'date_search')
        export_order = fields
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

class QuestionResource(resources.ModelResource):
    class Meta:
        model = Question
        exclude = ('tags', 'learning_objects')

    def after_import_row(self, row, row_result, **kwargs):
            instance = self._meta.model.objects.get(pk=row_result.object_id)
            
            if 'tags' in row:
                for item in row['tags']:
                    instance.tags.add(item)

            if 'alternatives' in row:
                is_correct = False
                for i, item in enumerate(row['alternatives']):
                    is_correct = False

                    if int(row['resposta']) == (i + 1):
                        is_correct = True
                    Alternative.objects.create(text=item, is_correct=is_correct, question_id=instance.id)
            
            if 'learning_object' in row:
                if not isinstance(row['learning_object'], int):
                    learning_object = LearningObject.objects.create(owner_id=1, text=row['learning_object'])
                                
                    if row['object_source']:
                        learning_object.source = row["object_source"]
                    instance.learning_objects.add(learning_object.id)

                else:
                    instance.learning_objects.add(row['learning_object'])
                
class LearningObjectQuestionsInline(admin.TabularInline):
    model = Question.learning_objects.through
    show_change_link = True
    raw_id_fields = ('question',)
    extra = 1

class QuestionLearningObjectInline(admin.TabularInline):
    model = LearningObject.questions.through
    show_change_link = True
    raw_id_fields = ('learningobject',)
    extra = 1

class DocumentQuestionsInline(admin.TabularInline):
    model = Document.questions.through
    raw_id_fields = ('question',)

class AlternativesInline(admin.TabularInline):
    model = Alternative
    show_change_link = True
    extra = 1

class FaqQuestionInline(admin.TabularInline):
    model = FaqQuestion
    show_change_link = True
    extra = 1

class TopicQuestionInline(admin.StackedInline):
    model = Topic.question_set.through
    raw_id_fields=('question',)

    extra = 1

class TopicsInline(admin.StackedInline):
    model = Question.topics.through
    raw_id_fields=('topic',)

    extra = 1

class ClassPlanLearningObjectInline(admin.TabularInline):
    model = LearningObject.plans_obj.through
    show_change_link = True
    raw_id_fields = ('learningobject',)
    extra = 1

class ClassPlanDocumentInline(admin.TabularInline):
    model = Document.plans_doc.through
    show_change_link = True
    raw_id_fields = ('document',)
    extra = 1

class ClassPlanTopicsInline(admin.StackedInline):
    model = ClassPlan.topics.through
    raw_id_fields=('topic',)

    extra = 1

class ClassPlanLinksInline(admin.TabularInline):
    model = Link
    extra = 1

class ClassPlanStationsInline(admin.TabularInline):
    model = Station
    raw_id_fields = ('document', 'question', 'learning_object',)
    extra = 1

class TopicChildsInline(admin.StackedInline):
    model = Topic
    show_change_link = True
    exclude = ('discipline', 'name')
    extra = 1

class LabelQuestionInline(admin.StackedInline):
    model = Label.question_set.through
    raw_id_fields=('question',)

    extra = 1

class LabelInline(admin.TabularInline):
    model = Question.labels.through
    raw_id_fields=('label',)

    extra = 1

class SynonymInline(admin.TabularInline):
    model = Synonym.topics.through
    raw_id_fields=('topic',)

    extra = 1

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

    inlines = [TopicChildsInline, TopicQuestionInline, ]
    list_per_page = 100

class LabelModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', )
    list_display = ('id', 'owner_id', 'name', 'num_questions')
    search_fields = ['id', 'name',]

    inlines = [LabelQuestionInline, ]
    list_per_page = 100

    def num_questions(self, obj):
        return Question.objects.filter(labels=obj).count()

class SynonymModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'term',)
    search_fields = ['id', 'term',]
    list_per_page = 100
    exclude = ('topics',)

    inlines = [SynonymInline,]

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

class QuestionModelAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = QuestionResource
    raw_id_fields = ('author', )
    list_display = ('id', 'statement', 'year', 'source', 'tag_list', 'disabled',)
    exclude = ('topics', 'learning_objects')
    search_fields = ('id', 'year', 'source', 'statement', 'tags__name')

    inlines = [QuestionLearningObjectInline, AlternativesInline, TopicsInline, LabelInline]

    list_per_page = 100


    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())
    
    def get_import_formats(self):
        return [base_formats.JSON]
    
class AlternativeModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('question', )
    list_display = ('id', 'question', 'text', 'is_correct',)
    search_fields = ['id', 'text', 'question__statement', 'question__id']

    list_per_page = 100

class DocumentModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner',)
    list_display = ('id', 'owner_id', 'owner_name', 'owner_email', 'name', 'num_questions', 'create_date', 'secret', 'disabled',)
    search_fields = ['id', 'owner__id', 'owner__name', 'owner__email', 'name', 'create_date']

    inlines = [DocumentQuestionsInline, ]

    list_per_page = 100

    def owner_name(self, obj):
        return obj.owner.name

    def owner_email(self, obj):
        return obj.owner.email
    
    def num_questions(self, obj):
        return obj.questions.count()

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
    list_display = ('id', 'user_id', 'user', 'document', 'download_date')
    search_fields = ['id', 'user__name', 'user__id',  'user__email', 'document__name', 'download_date']
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

class DocumentPublicationModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'document')
    list_display = ('id', 'document__name', 'user__name', 'create_date',)
    search_fields = ['id', 'document__name', 'user__name', 'create_date']

    list_per_page = 100

    def user__name(self, obj):
        if obj.user:
            return obj.user.name
        return ""

    def document__name(self, obj):
        return obj.document.name

class TeachingYearModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ['id', 'name',]
    list_per_page = 100

class LinkModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('plan', )
    list_display = ('id', 'link',)
    search_fields = ['id',]
    list_per_page = 100

class StationModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('plan','document', 'question', 'learning_object',)
    list_display = ('id', 'description_station',)
    search_fields = ['id',]
    list_per_page = 100

class ClassPlanModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', )
    list_display = ('id', 'name', 'create_date', 'duration', 'disabled')
    search_fields = ('id', 'name', 'description')
    exclude = ('topics', 'learning_objects', 'links', 'documents')

    inlines = [ClassPlanStationsInline, ClassPlanDocumentInline, ClassPlanLearningObjectInline, ClassPlanLinksInline, ClassPlanTopicsInline]

    list_per_page = 100

class FaqCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description_category')
    search_fields = ['id',]
    list_per_page = 100

    inlines = [FaqQuestionInline, ]

class DocumentQuestionOnlineInline(admin.TabularInline):
    model = DocumentOnline.questions_document.through
    show_change_link = True
    raw_id_fields = ('question', )
    extra = 1

class DocumentOnlineModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('owner', 'document',)
    list_display = ('link', 'owner', 'name', 'create_date')
    list_per_page = 100

    inlines = [DocumentQuestionOnlineInline, ]

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    show_change_link = True
    raw_id_fields = ('student_question', 'answer_alternative', )

    extra = 1

class ResultModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('results', )
    list_display = ('id', 'student_name', 'student_levels', 'results', )
    list_per_page = 100

    inlines = [StudentAnswerInline, ]

class DocumentQuestionOnlineModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('question', 'document')
    list_display = ('id', 'document', 'score')
    list_per_page = 100

admin.site.register(Discipline, DisciplineModelAdmin)
admin.site.register(Descriptor, DescriptorModelAdmin)
admin.site.register(TeachingLevel, TeachingLeveltModelAdmin)
admin.site.register(Year, YearModelAdmin)
admin.site.register(Source, SourceModelAdmin)
admin.site.register(Topic, TopicModelAdmin)
admin.site.register(Label, LabelModelAdmin)
admin.site.register(LearningObject, LearningObjectModelAdmin)
admin.site.register(Alternative, AlternativeModelAdmin)
admin.site.register(Question, QuestionModelAdmin)
admin.site.register(Document, DocumentModelAdmin)
admin.site.register(Header, HeaderModelAdmin)
admin.site.register(Search, SearchModelAdmin)
admin.site.register(DocumentDownload, DocumentDownloadModelAdmin)
admin.site.register(DocumentPublication, DocumentPublicationModelAdmin)
admin.site.register(Synonym, SynonymModelAdmin)
admin.site.register(TeachingYear, TeachingYearModelAdmin)
admin.site.register(ClassPlan, ClassPlanModelAdmin)
admin.site.register(Link, LinkModelAdmin)
admin.site.register(Station, StationModelAdmin)
admin.site.register(FaqCategory, FaqCategoryModelAdmin)
admin.site.register(DocumentOnline, DocumentOnlineModelAdmin)
admin.site.register(Result, ResultModelAdmin)
# admin.site.register(DocumentQuestionOnline, DocumentQuestionOnlineModelAdmin)