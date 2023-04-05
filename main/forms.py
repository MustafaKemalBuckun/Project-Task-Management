from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = {
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2'
        }


class LoginForm(forms.Form):
    username = forms.CharField(required = True)
    password = forms.CharField(required = True, widget=forms.PasswordInput)