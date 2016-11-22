from django import forms
from rolepermissions.shortcuts import assign_role

class SignupForm(forms.Form):

    def signup(self, request, user):
        assign_role(user, 'student')
