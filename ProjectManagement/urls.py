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
from accounts.views import NotificationList

urlpatterns = [
    # path('logout/', main_views.logout.as_view(template_name='accounts/logout.html'), name='logout'),
    path('admin/', admin.site.urls),
    path('', main_views.index, name='home'),
    path('register/', main_views.register, name='register'),
    path('login/', main_views.login_view, name='login'),
    path('logout/', main_views.logout_view, name='logout'),
    path('create_project/', main_views.create_project, name='create_project'),
    path('create_company/', main_views.create_company, name='create_company'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('pin/<int:project_id>/', main_views.pin_project),
    path('delete_project/<int:project_id>/', main_views.delete_project, name='delete_project'),
    path('project/<int:project_id>/', main_views.project_view, name='project'),
    path('leave_project/<int:project_id>/', main_views.leave_project, name='leave_project'),
    path('update_project/<int:project_id>/', main_views.update_project, name='update_project'),
    path('update_status/<int:project_id>/', main_views.update_status, name='update_status'),
    path('add_member/<int:project_id>/', main_views.add_project_member, name='add_member'),
    path('add_staff/<int:project_id>/', main_views.add_project_staff, name='add_project_staff'),
    path('accept_invitation/<int:project_id>/', main_views.accept_invitation, name='accept_invitation'),
    path('decline_invitation/<int:project_id>/', main_views.decline_invitation, name='decline_invitation'),
    path('remove/<int:project_id>/<int:user_id>/', main_views.remove_member, name='remove_member'),
    path('remove_staff/<int:project_id>/<int:user_id>/', main_views.remove_staff, name='remove_staff'),
    path('create_announcement/<int:project_id>/', main_views.create_announcement, name='create_announcement'),
    path('delete_announcement/<int:message_id>/', main_views.delete_announcement, name='delete_announcement'),
    path('notifications/', include(notifications.urls, namespace='notifications')),
    path('mark-notification-read/<int:notification_id>/', user_views.mark_notification_read, name='mark_notification_read'),
    path('delete-all-notifications/', user_views.delete_all_notifications, name='delete_all_notifications'),
    path('get-unread-count/', user_views.get_unread_count, name='get_unread_count'),
    path('get-notifications/', user_views.get_notifications, name='get_notifications'),
    path('api/notifications/', NotificationList.as_view(), name='notification-list'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
