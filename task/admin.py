from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for the Task model.
    This allows management of tasks through the Django admin panel.
    """
    list_display = ('title', 'description')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    list_filter = ('created_at',)