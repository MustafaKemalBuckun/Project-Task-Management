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
    project = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = '__all__'

    def get_project(self, invitation):
        project = {
            'id': invitation.project.id,
            'name': invitation.project.name,
        }
        if invitation.project.company:
            project['company'] = {
                'id': invitation.project.company.id,
                'name': invitation.project.company.name,
            }
        return project
