from django.db import models
from django.conf import settings
from accounts.models import Account

class Category(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='categories'
    ) # null indicates default system categories
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    icon = models.CharField(max_length=50, default='HelpCircle')
    color = models.CharField(max_length=20, default='#64748B')

    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ('user', 'name', 'type')
        ordering = ['name']

    def __str__(self):
        owner = "System" if self.user is None else self.user.username
        return f"{self.name} ({self.get_type_display()}) [{owner}]"


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            # Adjust balance for new transaction
            if self.type == 'income':
                self.account.balance += self.amount
            else:
                self.account.balance -= self.amount
            self.account.save()
        else:
            # Adjust balance for updated transaction
            # Fetch the old database state before save
            orig = Transaction.objects.get(pk=self.pk)
            
            # Revert original values on original account
            old_acct = orig.account
            if orig.type == 'income':
                old_acct.balance -= orig.amount
            else:
                old_acct.balance += orig.amount
            old_acct.save()
            
            # Apply new values to the (possibly new) account
            new_acct = self.account
            if self.type == 'income':
                new_acct.balance += self.amount
            else:
                new_acct.balance -= self.amount
            new_acct.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Adjust balance on deletion
        acct = self.account
        if self.type == 'income':
            acct.balance -= self.amount
        else:
            acct.balance += self.amount
        acct.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.type.upper()}: {self.amount} via {self.account.name} on {self.date}"


class RecurringTransaction(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='recurring_transactions')
    type = models.CharField(max_length=10, choices=Transaction.TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='recurring_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    next_run_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run_date']

    def __str__(self):
        return f"Recurring {self.type.upper()}: {self.amount} ({self.frequency}) next run on {self.next_run_date}"
