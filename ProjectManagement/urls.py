"""ProjectManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main import views as main_views
from accounts import views as user_views
import notifications.urls
from accounts.views import NotificationList, InvitationList

urlpatterns = [
    # path('logout/', main_views.logout.as_view(template_name='accounts/logout.html'), name='logout'),
    path('admin/', admin.site.urls),
    path('', main_views.index, name='home'),
    path('register/', main_views.register, name='register'),
    path('login/', main_views.login_view, name='login'),
    path('logout/', main_views.logout_view, name='logout'),
    path('create_company/', main_views.create_company, name='create_company'),
    path('update_company/<int:company_id>/', main_views.update_company, name='update_company'),
    path('delete_company/<int:company_id>/', main_views.delete_company, name='delete_company'),
    path('add_employees/<int:company_id>/', main_views.add_company_employees, name='add_employees'),
    path('join_company/<int:company_id>/', main_views.join_company, name='join_company'),
    path('reject_company/<int:company_id>/', main_views.reject_company, name='reject_company'),
    path('leave_company/<int:company_id>/', main_views.leave_company, name='leave_company'),
    path('companies/<int:company_id>/', main_views.company_view, name='companies'),
    path('create_project/', main_views.create_project, name='create_project'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('pin/<int:project_id>/', main_views.pin_project),
    path('pin_board/<int:board_id>/', main_views.pin_board),
    path('star_board/<int:board_id>/', main_views.star_board),
    path('delete_project/<int:project_id>/', main_views.delete_project, name='delete_project'),
    path('project/<int:project_id>/', main_views.project_view, name='project'),
    path('board/<int:board_id>/', main_views.board_view, name='board'),
    path('leave_project/<int:project_id>/', main_views.leave_project, name='leave_project'),
    path('update_project/<int:project_id>/', main_views.update_project, name='update_project'),
    path('update_status/<int:project_id>/', main_views.update_status, name='update_status'),
    path('add_member/<int:project_id>/', main_views.add_project_member, name='add_member'),
    path('add_staff/<int:project_id>/', main_views.add_project_staff, name='add_project_staff'),
    path('accept_invitation/<int:project_id>/', main_views.accept_invitation, name='accept_invitation'),
    path('decline_invitation/<int:project_id>/', main_views.decline_invitation, name='decline_invitation'),
    path('remove/<int:project_id>/<int:user_id>/', main_views.remove_member, name='remove_member'),
    path('remove_employee/<int:company_id>/<int:user_id>/', main_views.remove_employee, name='remove_employee'),
    path('remove_staff/<int:project_id>/<int:user_id>/', main_views.remove_staff, name='remove_staff'),
    path('create_announcement/<int:project_id>/', main_views.create_announcement, name='create_announcement'),
    path('delete_announcement/<int:message_id>/', main_views.delete_announcement, name='delete_announcement'),
    path('notifications/', include(notifications.urls, namespace='notifications')),
    path('mark-notification-read/<int:notification_id>/', user_views.mark_notification_read, name='mark_notification_read'),
    path('delete-all-notifications/', user_views.delete_all_notifications, name='delete_all_notifications'),
    path('get-unread-count/', user_views.get_unread_count, name='get_unread_count'),
    path('get-invitation-count/', user_views.get_invitation_count, name='get_invitation_count'),
    path('api/notifications/', NotificationList.as_view(), name='notification-list'),
    path('api/invitations/', InvitationList.as_view(), name='invitation_list'),
    path('create_board/<int:project_id>/', main_views.create_board, name='create_board'),
    path('update_board/<int:board_id>/', main_views.update_board, name='update_board'),
    path('delete_board/<int:board_id>/', main_views.delete_board, name='delete_board'),
    path('create_task/<int:board_id>/', main_views.create_task, name='create_task'),
    path('get-board-users-count/<int:board_id>/', main_views.get_board_users_count, name='get_board_users_count'),
    path('get-project-stats/<int:project_id>/', main_views.get_project_stats, name='get_project_stats'),
    path('add-users-to-task/<int:task_id>/', main_views.add_task_user, name='add-task-user'),
    path('add-staff-to-task/<int:task_id>/', main_views.add_task_follower, name='add-task-staff'),
    path('remove-task-staff/<int:task_id>/<int:user_id>', main_views.remove_task_staff, name='remove_task_staff'),
    path('remove-task-user/<int:task_id>/<int:user_id>', main_views.remove_task_user, name='remove_task_user'),
    path('update-task-status/', main_views.update_task_status, name='update-task-status'),
    path('update-task-priority/', main_views.update_task_priority, name='update-task-priority'),
    path('send_message/<int:task_id>/', main_views.send_message, name='send_message'),
    path('check_new_messages/<int:task_id>/', main_views.check_new_messages, name='check_new_messages'),
    path('delete_post/<int:post_id>/', main_views.delete_post, name='delete_post'),
    path('delete_task/<int:task_id>/', main_views.delete_task, name='delete_task'),
    path('my_tasks/', main_views.my_tasks, name='my_tasks'),
    path('profile/', user_views.profile, name='profile'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
