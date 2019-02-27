from django.conf import settings
from django.conf.urls import url, include
from rest_framework import renderers
from rest_framework.routers import DefaultRouter

from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token
from rest_framework_swagger.views import get_swagger_view

from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'questions/search', views.QuestionSearchView, base_name='questions-search')
router.register(r'questions', views.QuestionViewSet, base_name='questions')
router.register(r'disciplines', views.DisciplineViewSet, base_name='disciplines')
router.register(r'teaching_levels', views.TeachingLevelViewSet, base_name='teaching_levels')
router.register(r'years', views.YearViewSet, base_name='years')
router.register(r'sources', views.SourceViewSet, base_name='sources')
router.register(r'topics', views.TopicViewSet, base_name='topics')
router.register(r'documents', views.DocumentViewSet, base_name='documents')
router.register(r'headers', views.HeaderViewSet, base_name='headers')
router.register(r'learning_object', views.LearningObjectViewSet, base_name='learning_object')
router.register(r'search', views.SearchViewSet, base_name='search')

# router.register(r'users', rest_views.UserViewSet, base_name='users')
# router.register(r'question_lists', rest_views.Question_ListViewSet, base_name='question_lists')

# router.register(r'search/question', rest_views.QuestionSearchView, base_name='questions_search')
# router.register(r'search/tag', rest_views.TagSearchView, base_name='tags_search')
# router.register(r'tags', rest_views.TagListView, base_name='tags')
# router.register(r'subjects', rest_views.SubjectListView, base_name='subjects')

schema_view = get_swagger_view(title='Mupi Question API')

urlpatterns = [
    # url(r'^$', views.QuestionSearchView.as_view(), name='list'),
    # url(r'^search/$', views.QuestionSearchView.as_view() ,name='question_search'),
    #
    # url(r'^search_tag_ajax/$', views.QuestionTagSearchView.as_view()  ,name='question_search_tag_ajax'),
    # 
    # url(r'^(?P<pk>[\d]+)/$',views.QuestionDetailView.as_view(), name='question_detail'),
    # url(r'^generate_list$',views.list_generator, name='list_generator'),
    # url(r'^generate_answer_list$',views.answer_list_generator, name='answer_list_generator'),
    # url(r'^check_question/$',views.check_question, name='check_question'),
    # url(r'^clear_questions/$',views.clear_questions, name='clear_questions'),
    # url(r'^create_question/$',views.QuestionCreate.as_view(success_url='/questions/create_question'), name='question_form'),
    #
    # url(r'^question_list/create$',views.Question_ListCreateView.as_view(), name='question_list_create'),
    # url(r'^question_lists/$',views.Question_ListListView.as_view(), name='question_list_list'),
    # url(r'^question_lists/own$',views.Question_ListOwnListView.as_view(), name='question_list_own_list'),
    # url(r'^question_lists/(?P<pk>[\d]+)/$',views.Question_ListDetailView.as_view(), name='question_list_detail'),
    # url(r'^question_lists/(?P<pk>[\d]+)/delete$',views.Question_ListDeleteView.as_view(), name='question_list_delete'),
    # url(r'^question_lists/(?P<pk>[\d]+)/clone$',views.Question_ListCloneView.as_view(), name='question_list_clone'),
    # url(r'^question_lists/(?P<pk>[\d]+)/edit$',views.Question_ListEditView.as_view(), name='question_list_edit'),
    # url(r'^question_lists/(?P<pk>[\d]+)/edit/questions$',views.QuestionEditSearchView.as_view(), name='question_list_edit_list'),
    # url(r'^question_lists/(?P<pk>[\d]+)/edit/questions/search$',views.QuestionEditSearchView.as_view(), name='question_search_edit_list'),
    # url(r'^question_lists/(?P<pk>[\d]+)/edit/questions/remove$',views.Question_ListRemoveQuestionsView.as_view(), name='question_list_edit_remove_list'),
    #
    # url(r'^check_question_edit_add_list/$',views.check_question_edit_add_list, name='check_question_edit_add_list'),
    # url(r'^clear_questions_edit_add_list/$',views.clear_questions_edit_add_list, name='clear_questions_edit_add_list'),
    # url(r'^check_question_edit_list/$',views.check_question_edit_list, name='check_question_edit_list'),
    #
    # url(r'^get_tags/$', views.autocomplete, name='get_tags'),
    

    # Rest Urls

    url(r'^', include(router.urls)),
    url(r'^docs/$', schema_view),
    # url(r'^api-token-auth/', obtain_jwt_token),
    # url(r'^api-token-verify/', verify_jwt_token),
    # url(r'^auth/', include('rest_auth.urls')),
    # url(r'^auth/registration/', include('rest_auth.registration.urls')),
]


if settings.DEBUG:
    urlpatterns += [
        url(r'^docs/$', schema_view),
    ]
