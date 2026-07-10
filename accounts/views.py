from rest_framework import viewsets, permissions
from .models import Account
from .serializers import AccountSerializer
from activities.models import Activity

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        account = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='account_created',
            description=f"Created a new account '{account.name}' with initial balance {account.balance}."
        )

    def perform_update(self, serializer):
        account = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='account_updated',
            description=f"Updated details for account '{account.name}'."
        )

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        Activity.objects.create(
            user=self.request.user,
            action_type='account_deleted',
            description=f"Deleted account '{name}'."
        )
