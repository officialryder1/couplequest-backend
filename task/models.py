from django.db import models
from couple.models import Couple
from userProfile.models import CustomUser as User
from django.utils import timezone


class Task(models.Model):
    CATEGORY_CHOICES = [
        ('ROMANCE', 'Romance'),
        ('CHORES', 'Chores'),
        ('FITNESS', 'Fitness'),
        ('ADVENTURE', 'Adventure'),
        ('OTHER', 'Other'),
    ]

    couple = models.ForeignKey(Couple, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points = models.IntegerField(default=10)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='OTHER')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks'
    )
    due_date = models.DateField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=20, 
        blank=True,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly')
        ]
    )
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='completed_tasks'
    )

    def complete(self, user):
        """Mark task as completed with validation"""
        if self.is_completed:
            raise ValueError("Task already completed")
        
        self.is_completed = True
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save()
        return self

    def __str__(self):
        return f"Task: {self.title} | Points: {self.points} | Completed: {self.is_completed}"