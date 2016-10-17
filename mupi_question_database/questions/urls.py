from django.conf.urls import url

from . import views
from . import rest_views

urlpatterns = [
    url(r'^$', views.QuestionListView.as_view(), name='list'),
    url(r'^(?P<pk>[\d]+)/$',views.QuestionDetailView.as_view(), name='question_detail'),
    # url(r'^question_selectedList$',views.SelectedQuetionsView.as_view(), name='question_selectedList'),
    url(r'^generate_list$',views.list_generator, name='list_generator'),
    url(r'^check_question/$',views.check_question, name='check_question'),
    url(r'^clear_questions/$',views.clear_questions, name='clear_questions'),

    url(r'^create_question_list/$',views.Question_ListCreateView.as_view(), name='save_question_list'),
    url(r'^question_lists/$',views.Question_ListListView.as_view(), name='question_listlist'),
    url(r'^question_lists/(?P<pk>[\d]+)/$',views.Question_ListDeleteView.as_view(), name='question_listdetaildelete'),

    # Rest Urls

    url(r'^rest/questions/$', rest_views.QuestionRestListView.as_view()),
    url(r'^rest/questions/(?P<pk>[0-9]+)/$', rest_views.QuestionRestDetailView.as_view()),

    url(r'^rest/question_lists/$', rest_views.Question_ListRestListView.as_view()),
    url(r'^rest/question_list/$', rest_views.Question_ListRestCreateView.as_view()),
    url(r'^rest/question_lists/(?P<pk>[0-9]+)/$', rest_views.Question_ListRestDetailView.as_view()),

]
