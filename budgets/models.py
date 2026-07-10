from django.db import models
from django.conf import settings
from transactions.models import Category

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount_limit = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField()  # 1 to 12
    year = models.IntegerField()

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')
        ordering = ['-year', '-month', 'category__name']

    def __str__(self):
        return f"{self.user.username} budget for {self.category.name}: {self.amount_limit} ({self.month}/{self.year})"
