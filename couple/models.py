from django.db import models
from django.contrib.auth import get_user_model
from userProfile.models import CustomUser as User
import random
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class Couple(models.Model):
    user1 = models.ForeignKey(User, related_name='couple_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='couple_user2', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, default="New Couple")
    combined_points = models.IntegerField(default=0)
    pairing_code = models.CharField(max_length=6, editable=False, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    initiated_by = models.ForeignKey(User, related_name='initiated_couples', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pairing_code_expires = models.DateTimeField(null=True, blank=True)

    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(auto_now_add=True)
    
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user1', 'user2'],  # Fixed: using tuple
                name='unique_couple',
                condition=models.Q(user2__isnull=False)
            )
        ]

    def clean(self):
        # Prevent self-pairing
        if self.user1 == self.user2:
            raise ValueError("A user cannot pair with themselves.")
        
        # Check if users are already in a couple
        if self.is_active:
            existing = Couple.objects.filter(
                models.Q(user1=self.user1) | 
                models.Q(user2=self.user1) |
                models.Q(user1=self.user2) | 
                models.Q(user2=self.user2),
                is_active=True
            ).exclude(id=self.id)
            if existing.exists():
                raise ValueError("One or both users are already in a couple.")
    
    def update_combined_points(self):
        """Calculate combined points from both users"""
        self.combined_points = (
        self.user1.userprofile.xp + 
        (self.user2.userprofile.xp if self.user2 else 0)
        )
        self.save()
        

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.user1.username}'s Couple"
        super().save(*args, **kwargs)

    def activate_pairing(self, confirming_user):
        """Complete the pairing process"""
        if self.user2 is None:
            self.user2 = confirming_user
        self.is_active = True
        self.pairing_code = None
        self.pairing_code_expires = None
        self.save()

    
    def generate_pairing_code(self):
        """Generate a unique pairing code."""
        while True:
            code = str(random.randint(100000, 999999))
            if not Couple.objects.filter(pairing_code=code).exists():
                self.pairing_code = code
                self.pairing_code_expires = timezone.now() + timedelta(minutes=15)
                self.save()
                return code
    
    def is_code_valid(self):
        """Check if code is still valid"""
        return (
            self.pairing_code and 
            self.pairing_code_expires and 
            timezone.now() < self.pairing_code_expires
        )

    def update_streak(self):
        today = timezone.now().date()
        if self.last_activity_date == today - timedelta(days=1):
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        elif self.last_activity_date != today:
            self.current_streak = 1
        
        self.last_activity_date = today
        self.save()
        
        # Notify clients
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'couple_{self.id}',
            {
                'type': 'couple_update',
                'payload': {
                    'type': 'streak_updated',
                    'payload': self.current_streak
                }
            }
        )
        
        return self.current_streak

    def get_streak_bonus(self):
        if self.current_streak >= 7:
            return 0.5  # 50% bonus after 7 days
        elif self.current_streak >= 3:
            return 0.2  # 20% bonus after 3 days
        return 0
    
    def __str__(self):
        return f"{self.user1} & {self.user2 if self.user2 else '...'}"
    
    @property
    def users(self):
        """Helper property to get both users"""
        return [self.user1, self.user2]
    

class PairingAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField()
    code_attempt = models.CharField(max_length=6)
    attempted_at = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)


class CoupleMessage(models.Model):
    couple = models.ForeignKey(Couple, on_delete= models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Message from {self.sender.username} to {self.couple}'

    def mark_as_read(self):
        self.is_read = True
        self.save()