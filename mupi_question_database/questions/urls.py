from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.QuestionListView.as_view(), name='list'),
    url(r'^(?P<pk>[\d]+)/$',views.QuestionDetailView.as_view(), name='detail'),
    url(r'^question_selectedList$',views.SelectedQuetionsView.as_view(), name='question_selectedList'),
    url(r'^check_question/$',views.check_question, name='check_question'),
]
