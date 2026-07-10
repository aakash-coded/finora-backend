from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
import decimal
from .models import SavingsGoal
from .serializers import SavingsGoalSerializer
from activities.models import Activity
from notifications.models import Notification

class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        goal = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='goal_created',
            description=f"Created a savings goal '{goal.name}' with target {goal.target_amount}."
        )
        if goal.is_completed:
            self._trigger_completion_alert(goal)

    def perform_update(self, serializer):
        was_completed = serializer.instance.is_completed
        goal = serializer.save()
        
        Activity.objects.create(
            user=self.request.user,
            action_type='goal_updated',
            description=f"Updated savings goal '{goal.name}' (current: {goal.current_amount}/{goal.target_amount})."
        )
        
        # Trigger notification if just completed
        if goal.is_completed and not was_completed:
            self._trigger_completion_alert(goal)

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        Activity.objects.create(
            user=self.request.user,
            action_type='goal_deleted',
            description=f"Deleted savings goal '{name}'."
        )

    @action(detail=True, methods=['post'])
    def add_funds(self, request, pk=None):
        goal = self.get_object()
        amount = request.data.get('amount')
        
        if amount is None:
            return Response({'error': 'Amount is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = float(amount)
        except ValueError:
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

        was_completed = goal.is_completed
        goal.current_amount += decimal.Decimal(str(amount)) if 'decimal' in globals() else amount
        
        # Check completion
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
            
        goal.save()

        Activity.objects.create(
            user=self.request.user,
            action_type='goal_funds_added',
            description=f"Added {amount} to savings goal '{goal.name}'."
        )

        if goal.is_completed and not was_completed:
            self._trigger_completion_alert(goal)

        return Response(SavingsGoalSerializer(goal).data)

    def _trigger_completion_alert(self, goal):
        # Create a notification in the notification center
        Notification.objects.create(
            user=self.request.user,
            type='goal_completed',
            title='Goal Achieved! 🎉',
            message=f"Congratulations! You've reached your savings goal '{goal.name}' of {goal.target_amount}!"
        )
