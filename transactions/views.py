from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Category, Tag, Transaction, RecurringTransaction
from .serializers import CategorySerializer, TagSerializer, TransactionSerializer, RecurringTransactionSerializer
from activities.models import Activity

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Self-healing: if no system categories exist, create default ones
        if not Category.objects.filter(user=None).exists():
            default_categories = [
                # Expenses
                {'name': 'Housing', 'type': 'expense', 'icon': 'Home', 'color': '#EF4444'},
                {'name': 'Groceries', 'type': 'expense', 'icon': 'ShoppingCart', 'color': '#F59E0B'},
                {'name': 'Utilities', 'type': 'expense', 'icon': 'Zap', 'color': '#3B82F6'},
                {'name': 'Transportation', 'type': 'expense', 'icon': 'Car', 'color': '#10B981'},
                {'name': 'Entertainment', 'type': 'expense', 'icon': 'Film', 'color': '#8B5CF6'},
                {'name': 'Dining Out', 'type': 'expense', 'icon': 'Utensils', 'color': '#EC4899'},
                {'name': 'Insurance', 'type': 'expense', 'icon': 'Shield', 'color': '#6366F1'},
                {'name': 'Healthcare', 'type': 'expense', 'icon': 'HeartPulse', 'color': '#14B8A6'},
                # Incomes
                {'name': 'Salary', 'type': 'income', 'icon': 'Briefcase', 'color': '#22C55E'},
                {'name': 'Investments', 'type': 'income', 'icon': 'TrendingUp', 'color': '#06B6D4'},
                {'name': 'Freelance/Side Hussle', 'type': 'income', 'icon': 'Laptop', 'color': '#84CC16'},
                {'name': 'Gifts', 'type': 'income', 'icon': 'Gift', 'color': '#E11D48'},
            ]
            for cat in default_categories:
                Category.objects.create(user=None, **cat)

        return Category.objects.filter(Q(user=None) | Q(user=self.request.user))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Advanced Filtering
        search_query = self.request.query_params.get('search')
        tx_type = self.request.query_params.get('type')
        account_id = self.request.query_params.get('account')
        category_id = self.request.query_params.get('category')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        tags = self.request.query_params.getlist('tags')

        if search_query:
            queryset = queryset.filter(
                Q(notes__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(account__name__icontains=search_query)
            )

        if tx_type:
            queryset = queryset.filter(type=tx_type)

        if account_id:
            queryset = queryset.filter(account_id=account_id)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)

        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()

        return queryset

    def perform_create(self, serializer):
        transaction = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='transaction_created',
            description=f"Logged a new {transaction.type} of {transaction.amount} under category '{transaction.category.name if transaction.category else 'Uncategorized'}' to account '{transaction.account.name}'."
        )

    def perform_update(self, serializer):
        transaction = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='transaction_updated',
            description=f"Updated transaction '{transaction.id}' ({transaction.type} of {transaction.amount})."
        )

    def perform_destroy(self, instance):
        amount = instance.amount
        tx_type = instance.type
        acct_name = instance.account.name
        instance.delete()
        Activity.objects.create(
            user=self.request.user,
            action_type='transaction_deleted',
            description=f"Deleted {tx_type} transaction of {amount} from account '{acct_name}'."
        )


class RecurringTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        rec = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='recurring_created',
            description=f"Set up recurring {rec.type} of {rec.amount} ({rec.frequency}) starting {rec.start_date}."
        )

    def perform_update(self, serializer):
        rec = serializer.save()
        Activity.objects.create(
            user=self.request.user,
            action_type='recurring_updated',
            description=f"Updated recurring transaction '{rec.id}' ({rec.type} of {rec.amount})."
        )

    def perform_destroy(self, instance):
        amount = instance.amount
        tx_type = instance.type
        instance.delete()
        Activity.objects.create(
            user=self.request.user,
            action_type='recurring_deleted',
            description=f"Deleted recurring {tx_type} of {amount}."
        )
