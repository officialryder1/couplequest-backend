from django.db.models.signals import post_save
from django.dispatch import receiver
from task.models import Task
from achievement_checker import AchievementChecker

def check_achievements_on_task_completion(sender, instance, created, **kwargs):
    """
    Automatically checks achievements when:
    - A task is marked complete
    - A task is created (for first-task achievements)
    """
    if instance.is_completed or created:
        AchievementChecker.check_all_achievements(instance.couple)