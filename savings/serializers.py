from rest_framework import serializers
from .models import SavingsGoal

class SavingsGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsGoal
        fields = ('id', 'name', 'target_amount', 'current_amount', 'target_date', 'is_completed', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Mark as completed if current >= target
        if validated_data.get('current_amount', 0.0) >= validated_data.get('target_amount', 0.0):
            validated_data['is_completed'] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        curr = validated_data.get('current_amount', instance.current_amount)
        targ = validated_data.get('target_amount', instance.target_amount)
        if curr >= targ:
            validated_data['is_completed'] = True
        else:
            validated_data['is_completed'] = False
        return super().update(instance, validated_data)
