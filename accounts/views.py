from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from notifications.models import Notification
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.


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


def get_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user)
    notification_list = []
    for notification in notifications:
        notification_list.append({
            'message': notification.verb,
        })
    return JsonResponse(notification_list, safe=False)


def get_unread_count(request):
    count = Notification.objects.filter(recipient=request.user, unread=True).count()
    return JsonResponse({'count': count})


class NotificationList(APIView):

    def get(self, request, format=None):
        notifications = Notification.objects.filter(recipient=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)