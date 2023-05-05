from ckeditor.fields import RichTextFormField
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField
from main.models import Project, Company, ProjectStaff, Message

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
        self.fields['company'] = ModelChoiceField(queryset=companies, required=False)

    def is_valid(self):
        return super(ProjectForm, self).is_valid()


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = {
            'owner',
        }
        widgets = {
            'description': RichTextFormField(config_name="default"),
        }


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = {
            'owner',
            'date_created',
            'company',
            'users',
        }


class AddStaff(forms.ModelForm):
    class Meta:
        model = ProjectStaff
        exclude = {
            'project',
        }

    def __init__(self, project_users, *args, **kwargs):
        super(AddStaff, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = project_users


class CreateAnnouncement(forms.ModelForm):
    class Meta:
        model = Message
        exclude = {
            'owner',
            'project',
        }


class UpdateAnnouncement(forms.ModelForm):
    class Meta:
        model = Message
        exclude = {
            'owner',
            'project',
        }
