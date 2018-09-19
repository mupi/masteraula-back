# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(
        regex=r'^resend_confirmation_email$',
        view=views.UserConfirmationEmailView.as_view(),
        name='list'
    ),
]
