from django.contrib import admin
from .models import Reward, Achievement, CoupleAchievement

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    """
    Admin interface for the Reward model.
    This allows management of rewards through the Django admin panel.
    """
    list_display = ('name', 'cost', 'is_unlocked')
    search_fields = ('name',)
    ordering = ('-cost',)

    def has_add_permission(self, request):
        return True
    
admin.site.register(Achievement)
admin.site.register(CoupleAchievement)
