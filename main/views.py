from django.contrib.messages import get_messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from accounts.models import User
from .forms import UserRegisterForm, ProjectForm, CompanyForm, ProjectUpdateForm, AddStaff
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Project, Company, PinnedProjects, Board, Task, ProjectStaff, Invitation


# Create your views here.


def index(request):
    user = request.user
    if not user.is_anonymous:
        projects = Project.objects.filter(Q(users=user) | Q(owner=user)).annotate(task_count=Count('task'))
        pinned_projects = PinnedProjects.objects.filter(user=user).order_by('pinned_at')
        print(pinned_projects.values_list('project_id'))
        unpinned_projects = Project.objects.filter(Q(users=user) | Q(owner=user)).annotate(
            task_count=Count('task')).exclude(pinnedprojects__in=pinned_projects)
        print(unpinned_projects)
        percentages = []
        user_companies = Company.objects.filter(Q(owner=user) | Q(employees=user))

        user_invitations = Invitation.objects.filter(invited=user)
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
            'user_companies': user_companies,
            'unpinned_project_data': zip(unpinned_projects, percentages),
            'pinned_project_data': zip(pinned_projects, percentages),
            'pinned_projects': pinned_projects,
            'user_invitations': user_invitations,
        }

        return render(request, 'home/index.html', context)
    else:
        return redirect('login')


def register(request):
    if request.method == 'POST':
        registerform = UserRegisterForm(request.POST)
        if registerform.is_valid():
            registerform.save()
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
    user_invitations = Invitation.objects.filter(invited=user)
    context = {
        'user': user,
        'user_projects': user_projects,
        'user_invitations': user_invitations,
    }
    return context


def create_project(request):
    user = request.user
    companies = Company.objects.filter(owner=user)
    if request.method == 'POST':
        projectform = ProjectForm(companies, request.POST)
        if projectform.is_valid():
            project = projectform.save(commit=False)
            project.owner = user
            project.save()
            project.users.add(user)
            project.save()
            staff = ProjectStaff.objects.create(user=user, project=project)
            staff.save()
        return redirect('home')
    else:
        projectform = ProjectForm(companies)
    return render(request, 'projects/create_project.html', {'projectform': projectform})


def create_company(request):
    user = request.user
    if request.method == 'POST':
        companyform = CompanyForm(request.POST, request.FILES)
        if companyform.is_valid():
            print("validated.")
            company = companyform.save(commit=False)
            company.owner = user
            company.save()
            company.employees.add(user)
            company.save()
        else:
            print("not valid.")
    else:
        companyform = CompanyForm()
    return render(request, 'companies/create_company.html', {'companyform': companyform})


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


def project_view(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    project_staff = User.objects.filter(projectstaff__project=project)
    project_users = project.users.exclude(Q(id=project.owner.id) | Q(projectstaff__project=project))
    boards = Board.objects.filter(project=project)
    tasks = Task.objects.filter(project=project, board__in=boards)
    projectform = ProjectUpdateForm(instance=project)
    staff_form = AddStaff(project_users)
    message = get_messages(request)
    print(project_staff.values_list('username'))
    print(project_users.values_list('username'))
    context = {
        'messages': message,
        'project': project,
        'boards': boards,
        'tasks': tasks,
        'user': user,
        'projectform': projectform,
        'staff_form': staff_form,
        'project_staff': project_staff,
    }

    return render(request, 'projects/project.html', context)


def leave_project(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    project.users.remove(user)
    return redirect('home')


def update_project(request, project_id: int):
    project = Project.objects.get(id=project_id)
    project_users = project.users.all()
    project_staff = project.projectstaff_set.all()
    if request.method == 'POST':
        projectform = ProjectUpdateForm(request.POST, instance=project)
        if projectform.is_valid():
            p = projectform.save(commit=False)
            p.users.set(project_users)
            p.projectstaff_set.set(project_staff)
            p.save()
        else:
            print('fail.')
        return redirect('project', project_id)


def add_project_member(request, project_id: int):
    project = Project.objects.get(id=project_id)
    if request.method == "POST":
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Kullanıcı bulunamadı.'})
        if project.users.filter(username=username).exists():
            return JsonResponse({'status': 'warning', 'message': 'Bu kullanıcı zaten eklenmiş.'})
        invitation = Invitation.objects.filter(inviter=project.owner, invited=user, project=project)
        if invitation:
            return JsonResponse({'status': 'warning', 'message': 'Bu kullanıcıya zaten davet gönderilmiş.'})
        invite = Invitation.objects.create(inviter=project.owner, invited=user, project=project)
        invite.save()
        return JsonResponse({'status': 'success', 'message': 'Kullanıcıya davet gönderildi!'})
    else:
        return redirect('project', project_id)


def add_project_staff(request, project_id: int):
    project = Project.objects.get(id=project_id)
    project_users = project.users.exclude(Q(id=project.owner.id) & Q(projectstaff__user__in=project.users.all()))
    if request.method == "POST":
        staff_form = AddStaff(project_users, request.POST)
        if staff_form.is_valid():
            s = staff_form.save(commit=False)
            s.project = project
            s.save()
            print('not fail.')
        else:
            print('failed.')
        return redirect('project', project_id)


def accept_invitation(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    project.users.add(user)
    project.save()
    invitation = Invitation.objects.get(inviter=project.owner, invited=user, project=project)
    invitation.delete()
    return redirect('project', project_id)


def decline_invitation(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    invitation = Invitation.objects.get(inviter=project.owner, invited=user, project=project)
    invitation.delete()
    return redirect('home')


def remove_member(request, project_id: int, user_id: int):
    user = User.objects.get(id=user_id)
    project = Project.objects.get(id=project_id)
    project.users.remove(user)
    print('we here')
    return redirect('project', project_id)


def remove_staff(request, project_id: int, user_id: int):
    user = User.objects.get(id=user_id)
    project = Project.objects.get(id=project_id)
    project_staff = ProjectStaff.objects.get(user=user, project=project)
    project_staff.delete()
    print('we here')
    return redirect('project', project_id)