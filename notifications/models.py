from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('budget_exceeded', 'Budget Exceeded'),
        ('recurring_transaction', 'Recurring Transaction Alert'),
        ('goal_completed', 'Savings Goal Completed'),
        ('upcoming_bill', 'Upcoming Bill Reminder'),
        ('info', 'Information'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username} (Read: {self.is_read})"
