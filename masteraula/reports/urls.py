from django.conf import settings
from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^$', views.ReportsView.as_view(), name='reports_home'),
    url(r'^uncategorized_questions/$', views.UncategorizedTagsView.as_view(), name='uncategorized_questions'),
    url(r'^number_documents/$', views.NumberDocumentsView.as_view(), name='number_documents'),
]