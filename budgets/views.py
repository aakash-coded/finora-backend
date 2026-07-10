from rest_framework import viewsets, permissions
from .models import Budget
from .serializers import BudgetSerializer
from activities.models import Activity

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        budget = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='budget_created',
            description=f"Created a budget limit of {budget.amount_limit} for category '{budget.category.name}' for {budget.month}/{budget.year}."
        )

    def perform_update(self, serializer):
        budget = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='budget_updated',
            description=f"Updated budget for '{budget.category.name}' ({budget.month}/{budget.year}) to {budget.amount_limit}."
        )

    def perform_destroy(self, instance):
        name = instance.category.name
        period = f"{instance.month}/{instance.year}"
        instance.delete()
        Activity.objects.create(
            user=self.request.user,
            action_type='budget_deleted',
            description=f"Deleted budget for '{name}' for {period}."
        )
