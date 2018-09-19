# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User, City, State
from .serializers import CitySerializer, StateSerializer, ResendConfirmationEmailSerializer



class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = 'username'
    slug_url_kwarg = 'username'


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse('users:detail',
                       kwargs={'username': self.request.user.username})


class UserUpdateView(LoginRequiredMixin, UpdateView):

    fields = ['name', ]

    # we already imported User in the view code above, remember?
    model = User

    # send the user back to their own page after a successful update
    def get_success_url(self):
        return reverse('users:detail',
                       kwargs={'username': self.request.user.username})

    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)


class UserListView(LoginRequiredMixin, ListView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = 'username'
    slug_url_kwarg = 'username'

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
    
class UserConfirmationEmailView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResendConfirmationEmailSerializer

    def post(self, request, *args, **kwargs):
        self.serializer = self.get_serializer(data=request.data,
                                                context={'request': request})
        self.serializer.is_valid(raise_exception=True)            
        return Response({"status": "Confirmation e-mail was sent with success"}, status=status.HTTP_200_OK)

@api_view()
def null_view(request):
    return Response(status=status.HTTP_400_BAD_REQUEST)