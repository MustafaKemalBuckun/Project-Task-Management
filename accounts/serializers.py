from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.username')

    class Meta:
        model = Notification
        fields = ('id', 'actor', 'verb', 'description', 'unread', 'timestamp', 'timesince')
