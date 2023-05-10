from rest_framework import serializers
from notifications.models import Notification
from main.models import Invitation, Project


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.username')

    class Meta:
        model = Notification
        fields = ('id', 'actor', 'verb', 'description', 'unread', 'timestamp', 'timesince')


class InvitationSerializer(serializers.ModelSerializer):
    inviter = serializers.CharField(source='inviter.username')
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = Invitation
        fields = '__all__'
