from django.contrib.messages import get_messages
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from notifications.models import Notification

from accounts.models import User
from .forms import UserRegisterForm, ProjectForm, CompanyForm, ProjectUpdateForm, AddStaff, CreateAnnouncement, \
    UpdateAnnouncement, CreateBoard
from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Project, Company, PinnedProjects, Board, Task, ProjectStaff, Invitation, Message, Post


# Create your views here.


def index(request):
    user = request.user
    if not user.is_anonymous:
        # notification = Notification.objects.create(actor=user, recipient=user, description='Welcome!', verb='welcome')
        # notification.save()
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
    context = {}
    if not request.user.is_anonymous:
        user_projects = Project.objects.filter(users=request.user)
        user_invitations = Invitation.objects.filter(invited=request.user)
        unread_count = Notification.objects.filter(recipient=request.user, unread=True).count()
        notifications = Notification.objects.filter(recipient=request.user)
        context = {
            'user': request.user,
            'user_projects': user_projects,
            'user_invitations': user_invitations,
            'unread_count': unread_count,
            'notifications': notifications,
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
    active_tasks = Task.objects.filter(project=project, board__in=boards, status='Aktif').count()
    pending_tasks = Task.objects.filter(project=project, board__in=boards, status='Beklemede').count()
    inactive_tasks = Task.objects.filter(project=project, board__in=boards, status='İnaktif').count()
    completed_tasks = Task.objects.filter(project=project, board__in=boards, status='Tamamlandı').count()
    projectform = ProjectUpdateForm(instance=project)
    staff_form = AddStaff(project_users)
    announcement_form = CreateAnnouncement()
    announcements = Message.objects.filter(project=project)
    message = get_messages(request)
    sort_algorithm = Case(
        When(id=project.owner.id, then=Value(0)),
        When(id__in=project_staff.values('id'), then=Value(1)),
        default=Value(2),
        output_field=IntegerField()
    )
    all_users = project.users.order_by(sort_algorithm)
    board_form = CreateBoard()
    context = {
        'project_members': project_users,
        'messages': message,
        'project': project,
        'boards': boards,
        'tasks': tasks,
        'active_tasks': active_tasks,
        'pending_tasks': pending_tasks,
        'inactive_tasks': inactive_tasks,
        'completed_tasks': completed_tasks,
        'current_user': user,
        'projectform': projectform,
        'staff_form': staff_form,
        'board_form': board_form,
        'project_staff': project_staff,
        'all_users': all_users,
        'announcement_form': announcement_form,
        'announcements': announcements,
    }

    return render(request, 'projects/project.html', context)


def leave_project(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    if ProjectStaff.objects.get(user=user) is not None:
        ProjectStaff.objects.get(user=user).delete()
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
        notification = Notification.objects.create(actor=project.owner, recipient=user, verb='Yeni bir davetiniz var.', description='davet')
        notification.save()
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
            notification = Notification.objects.create(actor=project.owner, recipient=s.user,
                                                       verb=project.name + ' projesinde yetkilendirildiniz.',
                                                       description='yetki')
            notification.save()
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
    notification = Notification.objects.create(actor=user, recipient=project.owner, verb=', davetinizi kabul etti!', description='accepted')
    notification.save()
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
    if ProjectStaff.objects.get(user=user) is not None:
        ProjectStaff.objects.get(user=user).delete()
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


def create_announcement(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    if request.method == 'POST':
        announcement_form = CreateAnnouncement(request.POST)
        if announcement_form.is_valid():
            announcement = announcement_form.save(commit=False)
            announcement.owner = user
            announcement.project = project
            announcement.save()
            for user in project.users.exclude(id=announcement.owner.id):
                notification = Notification.objects.create(actor=project.owner,
                                                           recipient=user,
                                                           verb=', ' + project.name
                                                                + ' projesinde bir duyuru yayınladı.',
                                                           description='duyuru')
                notification.save()
            return redirect('project', project_id)


def update_status(request, project_id: int):
    if request.method == 'POST':
        user = request.user
        project = Project.objects.get(id=project_id)
        if user == project.owner and project.status == 'Aktif':
            project.status = 'İnaktif'
            project.save()
            return redirect('project', project_id)
        elif user == project.owner and project.status == 'İnaktif':
            project.status = 'Aktif'
            project.save()
            return redirect('project', project_id)
        return redirect('home')


def delete_announcement(request, message_id: int):
    announcement = Message.objects.get(id=message_id)
    project_id = announcement.project.id
    announcement.delete()
    return redirect('project', project_id)


def create_board(request, project_id: int):
    # user = request.user
    project = Project.objects.get(id=project_id)
    if request.method == 'POST':
        board_form = CreateBoard(request.POST)
        if board_form.is_valid():
            board = board_form.save(commit=False)
            board.project = project
            board_form.save()
            return redirect('project', project_id)


def get_board_users_count(request, board_id):
    board = Board.objects.get(id=board_id)
    count = board.users.count()
    return JsonResponse({'count': count})


def get_project_stats(request, project_id):
    project = Project.objects.get(id=project_id)
    board_count = Board.objects.filter(project=project).count()
    task_count = Task.objects.filter(project=project).count()
    post_count = Post.objects.filter(project=project).count()
    staff_count = ProjectStaff.objects.filter(project=project).count()
    user_count = project.users.count()
    return JsonResponse({'board_count': board_count, 'task_count': task_count, 'post_count': post_count,
                         'staff_count': staff_count, 'user_count': user_count})
