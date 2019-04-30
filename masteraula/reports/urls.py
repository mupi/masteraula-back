from django.conf import settings
from django.conf.urls import url, include

from . import views
from . import statements_views
from . import alternatives_views
from . import objects_views

urlpatterns = [
    url(r'^$', views.ReportsView.as_view(), name='reports_home'),
    url(r'^uncategorized_questions/$', views.UncategorizedTagsView.as_view(), name='uncategorized_questions'),
    url(r'^number_documents/$', views.NumberDocumentsView.as_view(), name='number_documents'),

    url(r'^statements_with_div/$', statements_views.StatementsWithDivView.as_view(), name='statements_with_div'),
    url(r'^statements_with_texto_associado/$', statements_views.StatementsWithTextoAssociado.as_view(), name='statements_with_texto_associado'),
    url(r'^statements_with_br/$', statements_views.StatementsWithBrInsideP.as_view(), name='statements_with_br'),
    url(r'^statements_with_p_inside_p/$', statements_views.StatementsWithPInsideP.as_view(), name='statements_with_p_inside_p'),
    url(r'^statements_with_empty_p/$', statements_views.StatementsWithEmptyP.as_view(), name='statements_with_empty_p'),
    url(r'^statements_with_strong_em/$', statements_views.StatementsWithBoldItalic.as_view(), name='statements_with_strong_em'),
    url(r'^statements_with_sup_sub/$', statements_views.StatementsWithSupSub.as_view(), name='statements_with_sup_sub'),
    url(r'^statements_with_line_height/$', statements_views.StatementsWithLineHeight.as_view(), name='statements_with_line_height'),
    url(r'^statements_all/$', statements_views.StatementsAllFilter.as_view(), name='statements_all'),

    url(r'^has_learning_object/$', views.StatementLearningObject.as_view(), name='has_learning_object'),
    url(r'^objects_without_source/$', views.ObjectsWithoutSource.as_view(), name='objects_without_source'),

    url(r'^objects_with_div/$', objects_views.ObjectsWithDivView.as_view(), name='objects_with_div'),
    url(r'^objects_with_texto_associado/$', objects_views.ObjectsWithTextoAssociado.as_view(), name='objects_with_texto_associado'),
    url(r'^objects_with_br/$', objects_views.ObjectsWithBrInsideP.as_view(), name='objects_with_br'),
    url(r'^objects_with_p_inside_p/$', objects_views.ObjectsWithPInsideP.as_view(), name='objects_with_p_inside_p'),
    url(r'^objects_with_empty_p/$', objects_views.ObjectsWithEmptyP.as_view(), name='objects_with_empty_p'),
    url(r'^objects_with_strong_em/$', objects_views.ObjectsWithBoldItalic.as_view(), name='objects_with_strong_em'),
    url(r'^objects_with_sup_sub/$', objects_views.ObjectsWithSupSub.as_view(), name='objects_with_sup_sub'),
    url(r'^objects_with_line_height/$', objects_views.ObjectsWithLineHeight.as_view(), name='objects_with_line_height'),
    url(r'^objects_all/$', objects_views.ObjectsAllFilter.as_view(), name='objects_all'),

    # url(r'^objects_with_div/$', objects_views.ObjectsWithDivView.as_view(), name='objects_with_div'),
    # url(r'^objects_with_texto_associado/$', objects_views.ObjectsWithTextoAssociado.as_view(), name='objects_with_texto_associado'),
    # url(r'^objects_with_br/$', objects_views.ObjectsWithBrInsideP.as_view(), name='objects_with_br'),
    # url(r'^objects_with_p_inside_p/$', objects_views.ObjectsWithPInsideP.as_view(), name='objects_with_p_inside_p'),
    # url(r'^objects_with_empty_p/$', objects_views.ObjectsWithEmptyP.as_view(), name='objects_with_empty_p'),
    # url(r'^objects_with_strong_em/$', objects_views.ObjectsWithBoldItalic.as_view(), name='objects_with_strong_em'),
    # url(r'^objects_with_sup_sub/$', objects_views.ObjectsWithSupSub.as_view(), name='objects_with_sup_sub'),
    # url(r'^objects_with_line_height/$', objects_views.ObjectsWithLineHeight.as_view(), name='objects_with_line_height'),
    url(r'^alternatives_all/$', alternatives_views.AlternativesAllFilter.as_view(), name='alternatives_all'),

    url(r'^statement_update/$', views.StatemensUpdateView.as_view(), name='update_with_div'),
    url(r'^learning_object_update/$', views.LearningObjectUpdateView.as_view(), name='update_learning_object'),
    url(r'^alternative_update/$', views.AlternativeUpdateView.as_view(), name='alternative_update'),
]