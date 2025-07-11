from django.shortcuts import get_object_or_404
from .models import Couple
from django.db.models import Q

def get_user_couple(user):
    """Safely get the active couple for a user"""
    return Couple.objects.filter(
        (Q(user1=user) | Q(user2=user)),
        is_active=True
    ).first()