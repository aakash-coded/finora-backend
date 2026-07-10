from rest_framework import serializers
from .models import Activity

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'action_type', 'description', 'timestamp')
        read_only_fields = ('id', 'action_type', 'description', 'timestamp')
