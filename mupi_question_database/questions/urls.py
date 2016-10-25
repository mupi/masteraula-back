from django.conf.urls import url

from . import views
from . import rest_views

urlpatterns = [
    url(r'^$', views.QuestionListView.as_view(), name='list'),
    url(r'^(?P<pk>[\d]+)/$',views.QuestionDetailView.as_view(), name='question_detail'),
    url(r'^generate_list$',views.list_generator, name='list_generator'),
    url(r'^check_question/$',views.check_question, name='check_question'),
    url(r'^clear_questions/$',views.clear_questions, name='clear_questions'),

    url(r'^question_list/create$',views.Question_ListCreateView.as_view(), name='question_list_create'),
    url(r'^question_lists/$',views.Question_ListListView.as_view(), name='question_list_list'),
    url(r'^question_lists/own$',views.Question_ListOwnListView.as_view(), name='question_list_own_list'),
    url(r'^question_lists/(?P<pk>[\d]+)/$',views.Question_ListDetailView.as_view(), name='question_list_detail'),
    url(r'^question_lists/(?P<pk>[\d]+)/delete$',views.Question_ListDeleteView.as_view(), name='question_list_delete'),
    url(r'^question_lists/(?P<pk>[\d]+)/clone$',views.Question_ListCloneView.as_view(), name='question_list_clone'),
    url(r'^question_lists/(?P<pk>[\d]+)/edit$',views.Question_ListEditView.as_view(), name='question_list_edit'),
    url(r'^question_lists/(?P<pk>[\d]+)/edit/questions$',views.Question_ListEditListView.as_view(), name='question_list_edit_list'),
    url(r'^question_lists/(?P<pk>[\d]+)/edit/questions/remove$',views.Question_ListRemoveQuestionsView.as_view(), name='question_list_edit_remove_list'),

    url(r'^check_question_edit_add_list/$',views.check_question_edit_add_list, name='check_question_edit_add_list'),
    url(r'^clear_questions_edit_add_list/$',views.clear_questions_edit_add_list, name='clear_questions_edit_add_list'),
    url(r'^check_question_edit_list/$',views.check_question_edit_list, name='check_question_edit_list'),

    # Rest Urls

    url(r'^rest/questions/$', rest_views.QuestionRestListView.as_view()),
    url(r'^rest/questions/(?P<pk>[0-9]+)/$', rest_views.QuestionRestDetailView.as_view()),

    url(r'^rest/question_lists/$', rest_views.Question_ListRestListView.as_view()),
    url(r'^rest/question_list/$', rest_views.Question_ListRestCreateView.as_view()),
    url(r'^rest/question_lists/(?P<pk>[0-9]+)/$', rest_views.Question_ListRestDetailView.as_view()),

]
