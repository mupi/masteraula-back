# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views import defaults as default_views
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from allauth.account.views import ConfirmEmailView
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from masteraula.users.views import null_view
from masteraula.users.views import FacebookLogin, GoogleLogin


urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, admin.site.urls),
    url(r'^rest-auth/facebook/$', FacebookLogin.as_view(), name='fb_login'),
    url(r'^rest-auth/google/$', GoogleLogin.as_view(), name='google_login'),

    # Your stuff: custom urls includes go here
    url(r'', include('masteraula.questions.urls', namespace='masteraula.questions')),
    url(r'', include('masteraula.users.urls', namespace='masteraula.users')),
    url(r'^reports/', include('masteraula.reports.urls', namespace='reports')),

    # Workaround to deal with some urls https://github.com/Tivix/django-rest-auth/issues/292
    url(r'^auth/registration/account-email-verification-sent/', null_view, name='account_email_verification_sent'),
    url(r'^auth/registration/account-confirm-email/', null_view, name='account_confirm_email'),
    url(r'^auth/registration/password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', null_view, name='password_reset_confirm'),
    
    url(r'^auth/', include('rest_auth.urls')),
    url(r'^auth/refresh-login', refresh_jwt_token),
    url(r'^auth/registration/', include('rest_auth.registration.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', default_views.bad_request, kwargs={'exception': Exception('Bad Request!')}),
        url(r'^403/$', default_views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        url(r'^404/$', default_views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        url(r'^500/$', default_views.server_error),
        url(r'^search/', include('haystack.urls')),
    ]
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
