from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    This manager handles user creation and normalization.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    """
    Custom user model that extends the default Django User model.
    This can be used to add additional fields or methods in the future.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, null=True, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak = models.IntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)

    def calculate_level(self):
        # example: Level = sqrt(xp / 100)
        self.level = int((self.xp / 100) ** 0.5) + 1
        self.save()

    def update_streak(self):
        today = timezone.now().date()
        if self.last_active == today - timedelta(days=1):
            self.streak == 1
        elif self.last_active != today:
            self.streak += 1
        
        self.last_active = today
        self.save()

    def __str__(self):
        return f"{self.user.username}'s Profile"