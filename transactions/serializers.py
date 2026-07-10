from rest_framework import serializers
from .models import Category, Tag, Transaction, RecurringTransaction
from accounts.models import Account

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'type', 'icon', 'color')
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    tags_details = TagSerializer(source='tags', many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )

    class Meta:
        model = Transaction
        fields = (
            'id', 'account', 'account_name', 'type', 'category', 'category_details',
            'amount', 'date', 'time', 'notes', 'receipt', 'tags_details', 'tag_names',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_account(self, value):
        # Ensure account belongs to user
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Account does not belong to the user.")
        return value

    def validate_category(self, value):
        # Ensure category is system default or belongs to user
        if value and value.user and value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        tag_names = validated_data.pop('tag_names', [])
        
        transaction = Transaction.objects.create(user=user, **validated_data)
        
        # Handle tags
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(user=user, name=name.strip())
            transaction.tags.add(tag)

        return transaction

    def update(self, instance, validated_data):
        user = self.context['request'].user
        tag_names = validated_data.pop('tag_names', None)
        
        # Perform normal update
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tag_names is not None:
            instance.tags.clear()
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(user=user, name=name.strip())
                instance.tags.add(tag)

        return instance


class RecurringTransactionSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = RecurringTransaction
        fields = (
            'id', 'account', 'account_name', 'type', 'category', 'category_details',
            'amount', 'notes', 'frequency', 'is_active', 'start_date', 'next_run_date',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_account(self, value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Account does not belong to the user.")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
