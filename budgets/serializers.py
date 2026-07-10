from rest_framework import serializers
from django.db.models import Sum
from .models import Budget
from transactions.serializers import CategorySerializer
from transactions.models import Transaction

class BudgetSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    current_spend = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = ('id', 'category', 'category_details', 'amount_limit', 'month', 'year', 'current_spend')
        read_only_fields = ('id', 'current_spend')

    def get_current_spend(self, obj):
        total = Transaction.objects.filter(
            user=obj.user,
            category=obj.category,
            type='expense',
            date__month=obj.month,
            date__year=obj.year
        ).aggregate(Sum('amount'))['amount__sum']
        return float(total) if total is not None else 0.0

    def validate_category(self, value):
        if value and value.user and value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category.")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
