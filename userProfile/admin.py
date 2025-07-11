from django.contrib import admin
from .models import CustomUser as User, UserProfile

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Admin interface for the CustomUser model.
    This allows management of users through the Django admin panel.
    """
    list_display = ('email', 'username', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('email',)
    
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserProfile model.
    This allows management of user profiles through the Django admin panel.
    """
    list_display = ('user', 'xp', 'level', 'streak', 'last_active')
    search_fields = ('user__email', 'user__username')
    ordering = ('user__email',)