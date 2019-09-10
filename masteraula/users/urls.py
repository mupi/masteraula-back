# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_auth.registration.views import (
    SocialAccountListView, SocialAccountDisconnectView
)

from . import views

router = SimpleRouter()
if settings.DEBUG: 
    router = DefaultRouter()

router.register(r'cities', views.CityViewSet, base_name='cities-list')
router.register(r'states', views.StateViewSet, base_name='states-list')
router.register(r'school', views.SchoolViewSet, base_name='school')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(
        regex=r'^resend_confirmation_email$',
        view=views.UserConfirmationEmailView.as_view(),
        name='list'
    ),
    url(r'^rest-auth/sign-in/facebook/$', views.FacebookLogin.as_view(), name='fb_login'),
    url(r'^rest-auth/sign-in/google/$', views.GoogleLogin.as_view(), name='google_login'),
    url(r'^rest-auth/sign-up/facebook/$', views.FacebookSignup.as_view(), name='fb_signup'),
    url(r'^rest-auth/sign-up/google/$', views.GoogleSignup.as_view(), name='google_signup'),
    url(r'^rest-auth/connect/facebook/$', views.FacebookConnect.as_view(), name='fb_connect'),
    url(r'^rest-auth/connect/google/$', views.GoogleConnect.as_view(), name='google_connect'),
    url(
        r'^socialaccounts/$',
        SocialAccountListView.as_view(),
        name='social_account_list'
    ),
    url(
        r'^socialaccounts/(?P<pk>\d+)/disconnect/$',
        SocialAccountDisconnectView.as_view(),
        name='social_account_disconnect'
    )
]
