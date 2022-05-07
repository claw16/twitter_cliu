from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        # HOMEWORK: make fields more straightforward, i.e. actor verb action on target
        fields = (
            'id',
            'actor_content_type',
            'actor_object_id',
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'timestamp',
            'unread',
        )
    # example: Ann (actor) liked (verb) your tweet1 (action_object) on Twitter (target)
