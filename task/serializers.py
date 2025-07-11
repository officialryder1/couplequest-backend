from rest_framework import serializers
from .models import Task
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class TaskCreateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'points', 'category',
            'assigned_to', 'due_date', 'is_recurring', 'recurrence_pattern'
        ]
        extra_kwargs = {
            'created_by': {'read_only': True},
            'couple': {'read_only': True},
            'recurrence_pattern': {'required': False}
        }

    def validate(self, data):
        if data.get('is_recurring') and not data.get('recurrence_pattern'):
            raise serializers.ValidationError(
                "Recurrence pattern is required for recurring tasks"
            )
        return data