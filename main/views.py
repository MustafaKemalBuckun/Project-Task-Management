from django.db.models import Q, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from accounts.models import User
from .forms import UserRegisterForm, ProjectForm
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Project, Company

# Create your views here.


def index(request):
    user = request.user
    projects = Project.objects.filter(Q(users=user) | Q(owner=user)).annotate(task_count=Count('task'))
    if not user.is_anonymous:
        context = {
            'user': user,
            'user_projects': projects,
            'user_companies': Company.objects.filter(Q(owner=user) | Q(employees=user)),
        }
        return render(request, 'home/index.html', context)
    else:
        return redirect('login')


def register(request):
    if request.method == 'POST':
        registerform = UserRegisterForm(request.POST)
        if registerform.is_valid():
            registerform.save()
            username = registerform.cleaned_data.get('username')
            messages.success(request, f'{username} kullanıcısı için hesap başarıyla oluşturuldu! Giriş yapabilirsiniz.')
            return redirect('login')
    else:
        registerform = UserRegisterForm()
    return render(request, 'accounts/register.html', {'registerform': registerform})


def login_view(request):
    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            print("test")
            username = loginform.cleaned_data.get("username")
            password = loginform.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        loginform = LoginForm()
    return render(request, 'accounts/login.html', {'loginform': loginform})


def logout_view(request):
    logout(request)
    return redirect('login')


def base_context(request):   # used for base.html
    user = request.user
    user_projects = Project.objects.filter(users=user)
    context = {
        'user': user,
        'user_projects': user_projects
    }
    return context


def create_project(request):
    user = request.user
    companies = Company.objects.filter(Q(owner=user) | Q(employees=user)).distinct()
    if request.method == 'POST':
        projectform = ProjectForm(companies, request.POST)
        if projectform.is_valid():
            print("validated.")
            project = projectform.save(commit=False)
            project.owner = user
            project.save()
        else:
            print("not valid.")
    else:
        projectform = ProjectForm(companies)
    return render(request, 'project/create_project.html', {'projectform': projectform})
