# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'cities', views.CityViewSet, base_name='cities-list')
router.register(r'states', views.StateViewSet, base_name='states-list')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(
        regex=r'^resend_confirmation_email$',
        view=views.UserConfirmationEmailView.as_view(),
        name='list'
    ),
    url(r'^rest-auth/facebook/$', views.FacebookLogin.as_view(), name='fb_login'),
    url(r'^rest-auth/google/$', views.GoogleLogin.as_view(), name='google_login'),
    url(r'^rest-auth/connect/facebook$', views.FacebookConnect.as_view(), name='fb_connect'),
    url(r'^rest-auth/connect/google$', views.GoogleConnect.as_view(), name='google_connect'),
]
