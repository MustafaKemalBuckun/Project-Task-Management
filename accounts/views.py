from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from notifications.models import Notification
from django.core import serializers

from main.forms import UserUpdateForm
from main.models import Invitation
from .serializers import NotificationSerializer, InvitationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.


def profile(request):
    current_user = request.user
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=current_user)
        if user_form.is_valid():
            user_form.save()
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=current_user)
    return render(request, 'accounts/profile.html', {'user_form': user_form,})


def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.mark_as_read()
    unread_count = Notification.objects.filter(recipient=request.user, unread=True).count()
    return JsonResponse({'unread_count': unread_count})


def delete_all_notifications(request):
    if request.method == 'POST':
        notifications = Notification.objects.filter(recipient=request.user)
        notifications.delete()
        print("success")
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


def get_unread_count(request):
    count = Notification.objects.filter(recipient=request.user, unread=True).count()
    return JsonResponse({'count': count})


class NotificationList(APIView):

    def get(self, request, format=None):
        notifications = Notification.objects.filter(recipient=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class InvitationList(APIView):

    def get(self, request, format=None):
        invitations = Invitation.objects.filter(invited=request.user)
        serializer = InvitationSerializer(invitations, many=True)
        return Response(serializer.data)


def get_invitation_count(request):
    invitation_count = Invitation.objects.filter(invited=request.user).count()
    return JsonResponse({'count': invitation_count})
