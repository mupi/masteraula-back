from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.QuestionListView.as_view(),
        name='list'
    ),
    # url(
    #     regex=r'^~redirect/$',
    #     view=views.UserRedirectView.as_view(),
    #     name='redirect'
    # ),
    url(
        regex=r'^(?P<pk>[\d]+)/$',
        view=views.QuestionDetailView.as_view(),
        name='detail'
    ),
    # url(
    #     regex=r'^~update/$',
    #     view=views.UserUpdateView.as_view(),
    #     name='update'
    # ),
]
