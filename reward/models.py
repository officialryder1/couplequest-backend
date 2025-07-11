from django.db import models
from couple.models import Couple
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from task.models import Task

User = get_user_model()


class Reward(models.Model):
    Couple = models.ForeignKey(Couple, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    cost = models.IntegerField(default=20)
    is_unlocked = models.BooleanField(default=False)

    def __str__(self):
        return f"Reward {self.name} Costs {self.cost}"

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10)
    xp_reward = models.PositiveIntegerField(default=10)

    # RuLE CONFIGURATION  (stored as json)
    unlock_rules = JSONField(default=dict, blank=True, help_text="""
    JSON structure defining unlock condition. Examples:
    - First task: {"task_count": 1}
    - 3-day streak: {"streak_days": 3}
    - Complete 5 hard task: {"hard_task": 5}                         
    """)

    def __str__(self):
        return self.name
    
    def check_unlock_conditions(self, couple):
        """
        Checks if a couple meet this achievement's unlock conditions
        """
        from django.db.models import Q, Count

        # First task completion
        if self.unlock_rules.get('task_count') == 1:
            return Task.objects.filter(couple=couple, is_completed=True).exists()

        # Specific number of tasks
        if task_count := self.unlock_rules.get('task_count'):
            return Task.objects.filter(couple=couple, is_completed=True).count() >= task_count
        
        # Streak achievements
        if streak_days := self.unlock_rules.get('streak_days'):
            return couple.current_streak >= streak_days
        
        # Category-specific tasks
        if category_count := self.unlock_rules.get('category_tasks'):
            category = self.unlock_rules.get('category')
            return Task.objects.filter(
                couple=couple, 
                is_completed=True,
                category=category
            ).count() >= category_count
        
        # Difficulty-specific tasks
        if difficulty_count := self.unlock_rules.get('difficulty_tasks'):
            difficulty = self.unlock_rules.get('difficulty')
            return Task.objects.filter(
                couple=couple,
                is_completed=True,
                difficulty=difficulty
            ).count() >= difficulty_count

class CoupleAchievement(models.Model):
    """Tracks which achievements a couple has unlocked."""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("couple", "achievement")  # Prevent duplicates

    def __str__(self):
        return f"{self.couple} unlocked {self.achievement}"