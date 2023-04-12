from django.db.models import Q, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from accounts.models import User
from .forms import UserRegisterForm, ProjectForm
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Project, Company, PinnedProjects


# Create your views here.


def index(request):
    user = request.user
    if not user.is_anonymous:
        projects = Project.objects.filter(Q(users=user) | Q(owner=user)).annotate(
            task_count=Count('task')).order_by('pinnedprojects', 'pinnedprojects__pinned_at')
        pinned_projects = PinnedProjects.objects.filter(user=user).values_list('project_id', flat=True)
        percentages = []
        for project in projects:
            total_tasks = project.task_set.count()
            completed_tasks = project.task_set.filter(status='Tamamlandı').count()
            if total_tasks > 0:
                progress = int((completed_tasks / total_tasks) * 100)
            else:
                progress = 0
            percentages.append(progress)

        context = {
            'user': user,
            'user_projects': projects,
            'user_companies': Company.objects.filter(Q(owner=user) | Q(employees=user)),
            'project_data': zip(projects, percentages),
            'pinned_projects': pinned_projects,
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
            project = projectform.save(commit=False)
            project.owner = user
            project.save()
            project.users.add(user)
            project.save()
        return redirect('home')
    else:
        projectform = ProjectForm(companies)
    return render(request, 'project/create_project.html', {'projectform': projectform})


def pin_project(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    pinned = PinnedProjects.objects.filter(project=project, user=user)
    if pinned:
        PinnedProjects.objects.get(project=project, user=user).delete()
    else:
        project.pinnedprojects_set.create(project=project, user=user)

    return index(request)


def delete_project(request, project_id: int):
    project = Project.objects.get(id=project_id)
    project.delete()
    return redirect('home')
