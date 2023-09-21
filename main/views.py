from datetime import timezone, datetime

from django.contrib.messages import get_messages
from django.db.models import Q, Count, Case, When, Value, IntegerField, F, BooleanField, ExpressionWrapper
from django.db.models.functions import NullIf
from django.http import JsonResponse
from django.shortcuts import render, redirect
from notifications.models import Notification

from accounts.models import User
from .forms import UserRegisterForm, ProjectForm, CompanyForm, ProjectUpdateForm, AddStaff, CreateAnnouncement, \
    CreateBoard, CreateTask, UpdateBoard, CompanyUpdateForm
from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from .models import Project, Company, PinnedProjects, Board, Task, ProjectStaff, Invitation, Message, Post, PinnedBoards


# Create your views here.


def index(request):
    user = request.user
    if not user.is_anonymous:
        pinned_projects = PinnedProjects.objects.filter(user=user).order_by('pinned_at').values_list('project_id',
                                                                                                     flat=True)
        projects = Project.objects.filter(Q(users=user) | Q(owner=user)).annotate(
            task_count=Count('task'),
            is_pinned=Case(
                When(id__in=pinned_projects, then=True),
                default=False,
                output_field=BooleanField()
            ),
            completed_tasks=Count('task', filter=Q(task__status='Tamamlandı')),
            percentage=ExpressionWrapper(
                F('completed_tasks') * 100 / NullIf(F('task_count'), 0),
                output_field=IntegerField(),
            )
        ).order_by('-is_pinned')
        user_companies = Company.objects.filter(Q(owner=user) | Q(employees=user)).distinct()
        user_invitations = Invitation.objects.filter(invited=user)
        context = {
            'user': user,
            'user_projects': projects,
            'user_companies': user_companies,
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
        user_projects = Project.objects.filter(Q(users=request.user) | Q(owner=request.user)).distinct()
        user_invitations = Invitation.objects.filter(invited=request.user)
        unread_count = Notification.objects.filter(recipient=request.user, unread=True).count()
        notifications = Notification.objects.filter(recipient=request.user)
        user_companies = Company.objects.filter(Q(owner=request.user) | Q(employees=request.user)).distinct()
        context = {
            'user': request.user,
            'user_projects': user_projects,
            'user_invitations': user_invitations,
            'unread_count': unread_count,
            'notifications': notifications,
            'user_companies': user_companies,
        }
    return context


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
            return redirect('home')
        else:
            print("not valid.")
    else:
        companyform = CompanyForm()
    return render(request, 'companies/create_company.html', {'companyform': companyform})


def update_company(request, company_id: int):
    company = Company.objects.get(id=company_id)
    company_employees = company.employees.all()
    if request.method == 'POST':
        companyform = CompanyUpdateForm(request.POST, request.FILES, instance=company)
        if companyform.is_valid():
            c = companyform.save(commit=False)
            c.employees.set(company_employees)
            c.save()
        else:
            print("fail.")
    return redirect('companies', company_id)


def delete_company(request, company_id: int):
    company = Company.objects.get(id=company_id)
    company.delete()
    return redirect('home')


def leave_company(request, company_id: int):
    user = request.user
    company = Company.objects.get(id=company_id)
    company.employees.remove(user)
    return redirect('home')


def company_view(request, company_id: int):
    user = request.user
    company = Company.objects.get(id=company_id)
    company_employees = company.employees.exclude(Q(id=company.owner.id))
    projects = Project.objects.filter(company=company).annotate(task_count=Count('task'))
    companyform = CompanyUpdateForm(instance=company)
    sort_algorithm = Case(
        When(id=company.owner.id, then=Value(0)),
        When(id__in=company_employees.values('id'), then=Value(1)),
        default=Value(2),
        output_field=IntegerField()
    )
    percentages = []
    for project in projects:
        total_tasks = project.task_set.count()
        print(total_tasks)
        completed_tasks = project.task_set.filter(status='Tamamlandı').count()
        if total_tasks > 0:
            progress = int((completed_tasks / total_tasks) * 100)
        else:
            progress = 0
        percentages.append(progress)
    context = {
        'company_employees': company_employees,
        'company': company,
        'current_user': user,
        'projects': projects,
        'projects_data': zip(projects, percentages),
        'companyform': companyform,
        'percentages': percentages,
    }
    return render(request, 'companies/company.html', context)


def add_company_employees(request, company_id: int):
    company = Company.objects.get(id=company_id)
    if request.method == "POST":
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Kullanıcı bulunamadı.'})
        if company.employees.filter(username=username).exists():
            return JsonResponse({'status': 'warning', 'message': 'Bu kullanıcı zaten bu şirketin çalışanı.'})
        invitation = Invitation.objects.filter(inviter=company.owner, invited=user, company=company)
        if invitation:
            return JsonResponse({'status': 'warning', 'message': 'Bu kullanıcıya zaten davet gönderilmiş.'})
        invite = Invitation.objects.create(inviter=company.owner, invited=user, company=company)
        notification = Notification.objects.create(actor=company.owner, recipient=user, verb='Yeni bir şirket davetiniz var.',
                                                   description='davet')
        notification.save()
        invite.save()
        return JsonResponse({'status': 'success', 'message': 'Kullanıcıya davet gönderildi!'})
    else:
        return redirect('company', company_id)


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


def pin_project(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    pinned = PinnedProjects.objects.filter(project=project, user=user)
    if pinned:
        PinnedProjects.objects.get(project=project, user=user).delete()
    else:
        project.pinnedprojects_set.create(project=project, user=user)

    return index(request)


def pin_board(request, board_id):
    board = Board.objects.get(id=board_id)
    project = board.project.id
    pinned = Board.objects.filter(id=board.id, is_pinned=True)
    print(pinned)
    if pinned:
        board.is_pinned = False
        board.save()
    else:
        board.is_pinned = True
        board.save()
        print(board.is_pinned)

    return project_view(request, project)


def star_board(request, board_id):
    board = Board.objects.get(id=board_id)
    project = board.project.id
    pinned = PinnedBoards.objects.filter(board=board, user=request.user)
    if pinned:
        PinnedBoards.objects.get(board=board, user=request.user).delete()
    else:
        board.pinnedboards_set.create(board=board, user=request.user)

    return project_view(request, project)


def delete_project(request, project_id: int):
    project = Project.objects.get(id=project_id)
    project.delete()
    return redirect('home')


def project_view(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    project_staff = User.objects.filter(projectstaff__project=project)
    project_users = project.users.exclude(Q(id=project.owner.id) | Q(projectstaff__project=project))
    boards = Board.objects.filter(project=project).order_by('pinnedboards__pinned_at', F('is_pinned').desc()).distinct()
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
    board_form = CreateBoard(all_users)
    pinned_boards = PinnedBoards.objects.filter(user=user).values_list('board_id', flat=True)

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
        'pinned_boards': pinned_boards,
    }

    return render(request, 'projects/project.html', context)


def leave_project(request, project_id: int):
    user = request.user
    project = Project.objects.get(id=project_id)
    if user in ProjectStaff.objects.filter(user=user):
        ProjectStaff.objects.get(user=user).delete()
    boards = project.board_set.all()
    tasks = Task.objects.filter(board__in=boards)
    for board in boards:
        board.users.remove(user)
    for task in tasks:
        task.assigned_to.remove(user)
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


def join_company(request, company_id):
    company = Company.objects.get(id=company_id)
    company.employees.add(request.user)
    company.save()
    inv = Invitation.objects.get(inviter=company.owner, invited=request.user, company=company)
    notification = Notification.objects.create(actor=request.user, recipient=company.owner, verb=', davetinizi kabul etti!',
                                               description='accepted')
    notification.save()
    inv.delete()
    return redirect('companies', company_id)


def reject_company(request, company_id):
    company = Company.objects.get(id=company_id)
    inv = Invitation.objects.get(inviter=company.owner, invited=request.user, company=company)
    inv.delete()
    return redirect('home')


def remove_member(request, project_id: int, user_id: int):
    user = User.objects.get(id=user_id)
    project = Project.objects.get(id=project_id)
    if ProjectStaff.objects.get(user=user) is not None:
        ProjectStaff.objects.get(user=user).delete()
    project.users.remove(user)

    print('we here')
    return redirect('project', project_id)


def remove_employee(request, company_id, user_id):
    user = User.objects.get(id=user_id)
    company = Company.objects.get(id=company_id)
    company.employees.remove(user)
    return redirect('companies', company_id)


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
    all_users = project.users
    if request.method == 'POST':
        board_form = CreateBoard(all_users, request.POST)
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


def board_view(request, board_id):
    board = Board.objects.get(id=board_id)
    project = board.project
    project_users = project.users
    tasks = Task.objects.filter(board=board)
    task_form = CreateTask(project_users)
    waiting_tasks = Task.objects.filter(project=project, board=board, status='Beklemede')
    done_tasks = Task.objects.filter(project=project, board=board, status='Tamamlandı')
    inactive_tasks = Task.objects.filter(project=project, board=board, status='İnaktif')
    active_tasks = Task.objects.filter(project=project, board=board, status='Aktif')
    board_form = UpdateBoard(project_users, instance=board)
    time = datetime.now(timezone.utc)
    project_staff = User.objects.filter(projectstaff__project=project)
    all_status = [status[0] for status in Task.STATUS_CHOICES]
    priorities = [priority[0] for priority in Task.PRIORITY_CHOICES]
    task_groups = {
        'Aktif': active_tasks,
        'İnaktif': inactive_tasks,
        'Beklemede': waiting_tasks,
        'Tamamlandı': done_tasks,
    }
    context = {
        'task_groups': task_groups,
        'time': time,
        'board': board,
        'board_form': board_form,
        'tasks': tasks,
        'task_form': task_form,
        'waiting_tasks': waiting_tasks,
        'done_tasks': done_tasks,
        'inactive_tasks': inactive_tasks,
        'active_tasks': active_tasks,
        'current_user': request.user,
        'project_staff': project_staff,
        'all_status': all_status,
        'priorities': priorities,
    }
    return render(request, 'projects/board.html', context)


def update_board(request, board_id):
    board = Board.objects.get(id=board_id)
    already_users = list(board.users.all())
    users = board.project.users.all()
    if request.method == 'POST':
        board_form = UpdateBoard(users, request.POST, instance=board)
        if board_form.is_valid():
            b = board_form.save(commit=False)
            b.users.set(board_form.cleaned_data['users'])
            b.save()
            new_users = b.users.exclude(id__in=[user.id for user in already_users])
            print(new_users)
            for user in board.users.all():
                notification = Notification.objects.create(
                    actor=request.user,
                    recipient=user,
                    verb=request.user.username + ', "' + board.project.name + '" projesindeki "'
                         + board.title + '" panosunu güncelledi.',
                    description='pano güncelleme'
                )
                notification.save()
            if new_users is not None:
                for user in new_users:
                    print(user.username)
                    notification = Notification.objects.create(
                        actor=board.project.owner,
                        recipient=user,
                        verb=board.project.name + ' projesinde '
                        + board.title + ' panosuna eklendiniz.',
                        description='panoya kullanıcı ekleme'
                    )
                    notification.save()
            else:
                print('hmmm')
        else:
            print(board_form.errors)
        return redirect('board', board.id)


def delete_board(request, board_id):
    board = Board.objects.get(id=board_id)
    board.delete()
    return redirect('project', board.project.id)


def create_task(request, board_id):
    board = Board.objects.get(id=board_id)
    project = board.project
    user = request.user
    project_users = project.users
    if request.method == 'POST':
        task_form = CreateTask(project_users, request.POST)
        if task_form.is_valid():
            task = task_form.save(commit=False)
            task.project = project
            task.board = board
            task.save()
            task_form.save_m2m()
            if task.assigned_to.all() is not None:
                for assignee in task.assigned_to.all():
                    print(assignee.username)
                    notify = Notification.objects.create(
                        actor=request.user,
                        recipient=assignee,
                        verb='"' + board.title + '" panosunda, ' + '(' + task.project.name + ') ' +
                             user.username + ' tarafından "' + task.title + '" görevine eklendiniz.'
                    )
                    notify.save()
            return redirect('board', board_id)
        else:
            print(task_form.errors)


def add_task_user(request, task_id):
    task = Task.objects.get(id=task_id)
    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = User.objects.get(id=user_id)
        task.assigned_to.add(user)
        task.save()
        notify = Notification.objects.create(
            actor=request.user,
            recipient=user,
            verb='"' + task.board.title + '" panosunda, ' + '(' + task.project.name + ') ' +
            request.user.username + ' tarafından "' + task.title + '" görevine eklendiniz.'
        )
        notify.save()
        return redirect('board', task.board.id)


def add_task_follower(request, task_id):
    task = Task.objects.get(id=task_id)
    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = User.objects.get(id=user_id)
        task.followers.add(user)
        task.save()
        notify = Notification.objects.create(
            actor=request.user,
            recipient=user,
            verb='"' + task.board.title + '" panosunda, ' + '(' + task.project.name + ') ' +
            request.user.username + ' tarafından "' + task.title + '" görevine takipçi olarak eklendiniz.'
        )
        notify.save()
        return redirect('board', task.board.id)


def remove_task_user(request, task_id, user_id):
    task = Task.objects.get(id=task_id)
    user = User.objects.get(id=user_id)
    task.assigned_to.remove(user)
    task.save()
    return redirect('board', task.board.id)


def remove_task_staff(request, task_id, user_id):
    task = Task.objects.get(id=task_id)
    user = User.objects.get(id=user_id)
    task.followers.remove(user)
    task.save()
    return redirect('board', task.board.id)


def update_task_status(request):
    task_id = request.POST.get('task_id')
    new_status = request.POST.get('status')

    task = Task.objects.get(id=task_id)
    task.status = new_status
    task.save()

    response_data = {
        'success': True,
        'message': 'Task status updated successfully.',
    }
    return JsonResponse(response_data)


def update_task_priority(request):
    task_id = request.POST.get('task_id')
    new_priority = request.POST.get('priority')

    task = Task.objects.get(id=task_id)
    task.priority = new_priority
    task.save()

    response_data = {
        'success': True,
        'message': 'Task priority updated successfully.',
    }
    return JsonResponse(response_data)


def send_message(request, task_id):
    task = Task.objects.get(id=task_id)
    if request.method == 'POST':
        message = request.POST.get('message')
        file = request.FILES.get('file')

        post = Post.objects.create(content=message, author=request.user, project=task.project, files=file, board=task.board, task=task)
        post.save()
        assignees = User.objects.filter(id__in=task.assigned_to.values_list('id', flat=True)).exclude(
            id=request.user.id)
        for assignee in assignees:
            notify = Notification.objects.create(
                actor=request.user,
                recipient=assignee,
                verb='"' + request.user.username + '", ' + '"' + task.title + '"' +
                     'görevinde yeni bir gönderi oluşturdu.'
            )
            notify.save()
        response_data = {
            'success': True
        }
        return JsonResponse(response_data)

    else:
        response_data = {
            'success': False,
            'error': 'Invalid request method.'
        }
        return JsonResponse(response_data)


def check_new_messages(request, task_id):
    task = Task.objects.get(id=task_id)
    messages = Post.objects.filter(task=task).order_by('-date_created')
    data = {
        'messages': []
    }
    user = User.objects.get(id=request.user.id)

    for message in messages:

        is_current_user = message.author == request.user
        current_user_photo = user.photo.url if is_current_user and user.photo else None
        author_photo = message.author.photo.url if not is_current_user and message.author.photo else None
        message_data = {
            'is_current_user': is_current_user,
            'content': message.content,
            'date_created': message.date_created,
            'current_user_photo': current_user_photo,
            'author_id': message.author.id,
            'author_photo': author_photo,
            'author_username': message.author.username,
            'id': message.id
        }
        data['messages'].append(message_data)

    return JsonResponse(data)


def delete_post(request, post_id):
    post = Post.objects.get(id=post_id)
    post.delete()
    return redirect('board', post.board.id)


def delete_task(request, task_id):
    task = Task.objects.get(id=task_id)
    task.delete()
    return redirect('board', task.board.id)


def my_tasks(request):
    projects = Project.objects.filter(Q(users=request.user) | Q(owner=request.user)).distinct()
    tasks = Task.objects.filter(Q(assigned_to=request.user) | Q(followers=request.user)).distinct()
    time = datetime.now(timezone.utc)
    context = {
        'projects': projects,
        'tasks': tasks,
        'current_user': request.user,
        'time': time,
    }
    return render(request, 'home/tasks.html', context)
