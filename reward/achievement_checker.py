from django.db import transaction
from .models import Achievement, CoupleAchievement

class AchievementChecker:
    @classmethod
    def check_all_achievements(cls, couple):
        """
        Checks all possible achievements for a couple
        Returns list of newly unlocked achievements
        """
        unlocked = []
        
        for achievement in Achievement.objects.all():
            # Skip if already unlocked
            if CoupleAchievement.objects.filter(
                couple=couple, 
                achievement=achievement
            ).exists():
                continue
                
            # Check unlock conditions
            if achievement.check_unlock_conditions(couple):
                unlocked.append(achievement)
                cls._grant_achievement(couple, achievement)
        
        return unlocked
    
    @classmethod
    @transaction.atomic
    def _grant_achievement(cls, couple, achievement):
        """Helper method to grant an achievement"""
        CoupleAchievement.objects.create(
            couple=couple,
            achievement=achievement
        )
        # Award XP to both users
        couple.user1.userprofile.xp += achievement.xp_reward
        couple.user2.userprofile.xp += achievement.xp_reward
        couple.user1.userprofile.save()
        couple.user2.userprofile.save()