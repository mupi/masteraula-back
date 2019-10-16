# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_auth.registration.views import SocialLoginView, SocialConnectView

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User, City, State, School, Subscribe
from .serializers import CitySerializer, StateSerializer, SchoolSerializer,ResendConfirmationEmailSerializer, SocialOnlyLoginSerializer, SubscribeSerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    serializer_class = CitySerializer
    queryset = City.objects.all()

    def get_queryset(self):
        queryset = City.objects.all()
        if 'uf' not in self.request.query_params:
            return None
        uf = self.request.query_params['uf']
        queryset = queryset.filter(uf=uf)
        return queryset

class StateViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    serializer_class = StateSerializer
    queryset = State.objects.all()
    
class SchoolViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = SchoolSerializer
    queryset = School.objects.all()

class SubscribeViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = SubscribeSerializer
    queryset = Subscribe.objects.all()

class UserConfirmationEmailView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResendConfirmationEmailSerializer

    def post(self, request, *args, **kwargs):
        self.serializer = self.get_serializer(data=request.data,
                                                context={'request': request})
        self.serializer.is_valid(raise_exception=True)            
        return Response({"status": "Confirmation e-mail was sent with success"}, status=status.HTTP_200_OK)

class FacebookSignup(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter

class GoogleSignup(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter

    serializer_class = SocialOnlyLoginSerializer

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    serializer_class = SocialOnlyLoginSerializer

class FacebookConnect(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter

class GoogleConnect(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

@api_view()
def null_view(request):
    return Response(status=status.HTTP_400_BAD_REQUEST)