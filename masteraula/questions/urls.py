from django.conf import settings
from django.conf.urls import url, include
from rest_framework import renderers
from rest_framework.routers import DefaultRouter, SimpleRouter

from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token
from rest_framework_swagger.views import get_swagger_view

from . import views

# Create a router and register our viewsets with it.
router = SimpleRouter()
if settings.DEBUG: 
    router = DefaultRouter()

router.register(r'questions/search', views.QuestionSearchView, base_name='questions-search')
router.register(r'questions', views.QuestionViewSet, base_name='questions')
router.register(r'disciplines', views.DisciplineViewSet, base_name='disciplines')
router.register(r'teaching_levels', views.TeachingLevelViewSet, base_name='teaching_levels')
router.register(r'years', views.YearViewSet, base_name='years')
router.register(r'sources', views.SourceViewSet, base_name='sources')
router.register(r'topics', views.TopicViewSet, base_name='topics')
router.register(r'labels', views.LabelViewSet, base_name='labels')
router.register(r'documents', views.DocumentViewSet, base_name='documents')
router.register(r'document_publication', views.DocumentPublicationViewSet, base_name='document_publication')
router.register(r'headers', views.HeaderViewSet, base_name='headers')
router.register(r'learning_object/search', views.LearningObjectSearchView, base_name='learning_object-search')
router.register(r'learning_object', views.LearningObjectViewSet, base_name='learning_object')
router.register(r'document_download', views.DocumentDownloadViewSet, base_name='document_download')
router.register(r'synonym_topic', views.SynonymViewSet, base_name='synonym_topic')
router.register(r'synonym_autocomplete', views.AutocompleteSearchViewSet, base_name='synonym_autocomplete')
router.register(r'class_plans', views.ClassPlanViewSet, base_name="class_plans")
router.register(r'links', views.LinkViewSet, base_name="links")
router.register(r'teaching_years', views.TeachingYearViewSet, base_name="teaching_years")
router.register(r'stations', views.StationViewSet, base_name="stations")
router.register(r'faq_categories', views.FaqCategoryViewSet, base_name="faq_categories")
router.register(r'document_online', views.DocumentOnlineViewSet, base_name="document_online")

urlpatterns = [
    url(r'^', include(router.urls)),
]

if settings.DEBUG: 
    schema_view = get_swagger_view(title='Mupi Question API')
    urlpatterns += [
        url(r'^docs/$', schema_view),
    ]
