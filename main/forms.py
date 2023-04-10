from ckeditor.fields import RichTextFormField
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField

from main.models import Project

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
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput)


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        exclude = {
            'owner',
            'date_created',
        }
        widgets = {
            'description': RichTextFormField(config_name="default"),
        }

    def __init__(self, companies, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields['company'] = ModelChoiceField(queryset=companies)
