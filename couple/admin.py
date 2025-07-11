from django.contrib import admin
from .models import Couple, PairingAttempt, CoupleMessage

@admin.register(Couple)
class CoupleAdmin(admin.ModelAdmin):
    """
    Admin interface for the Couple model.
    This allows management of couples through the Django admin panel.
    """
    list_display = ('user1', 'user2', 'created_at', 'updated_at')
    search_fields = ('user1__email', 'user2__email')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return True
    
@admin.register(PairingAttempt)
class PairingAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'user', 'was_successful', 'attempted_at')
    list_filter = ('was_successful',)
    search_fields = ('ip_address', 'user__username')

admin.site.register(CoupleMessage)
