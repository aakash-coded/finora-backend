from django.db import models
from django.conf import settings

class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('cash', 'Cash Wallet'),
        ('bank', 'Bank Account'),
        ('credit_card', 'Credit Card'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - {self.balance}"
