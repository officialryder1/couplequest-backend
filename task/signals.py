from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task
from django.utils import timezone
from datetime import timedelta

@receiver(post_save, sender=Task)
def award_xp_on_task_completed(sender, instance, created, **kwargs):
    if instance.is_completed and not instance.completed_at:
        # Grants XP to both users in the couple
        couple = instance.couple
        for user in [couple.user1, couple.user2]:
            profile = user.userProfile
            profile.xp += instance.points
            profile.calculate_level() #Recalculate level
            profile.update_streak() #Update streak
        instance.completed_at = timezone.now()
        instance.save()


def update_user_stats(user, xp_earned):
    """Update XP, level, and streaks for a user"""
    profile = user.userprofile
    
    # Update XP and level
    profile.xp += xp_earned
    profile.level = calculate_level(profile.xp)
    
    # Update streak
    today = timezone.now().date()
    if profile.last_active == today - timedelta(days=1):
        profile.streak += 1
    elif profile.last_active != today:
        profile.streak = 1  # Reset streak if broken
    
    profile.last_active = today
    profile.save()

def calculate_level(xp):
    """Calculate level based on XP (customize formula as needed)"""
    return int((xp / 100) ** 0.6) + 1  # Slower progression at higher level