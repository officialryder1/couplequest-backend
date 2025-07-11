from rest_framework import serializers
from .models import Couple, CoupleMessage
from userProfile.serializers import UserSerializer

class CoupleSerializer(serializers.ModelSerializer):
    user1 = serializers.StringRelatedField()
    user2 = serializers.StringRelatedField(allow_null=True)
    user1_name = serializers.CharField(source='user1.username')
    user2_name = serializers.CharField(source='user2.username')
    
    class Meta:
        model = Couple
        fields = ['id', 'user1', 'user2', 'is_active', 'created_at', 'name', 'combined_points', 'current_streak', 'longest_streak', 'user1_name', 'user2_name']
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        """Ensure clean JSON serialization"""
        data = super().to_representation(instance)
        # Remove any None values that might cause issues
        return {k: v for k, v in data.items() if v is not None}
    

class CoupleLeaderboardSerializer(serializers.ModelSerializer):
    user1_name = serializers.CharField(source='user1.username')
    user2_name = serializers.CharField(source='user2.username', allow_null=True)
    
    class Meta:
        model = Couple
        fields = ['name', 'user1_name', 'user2_name', 'combined_points']

class CoupleMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = CoupleMessage
        fields = ['id', 'content', 'sender', 'sender_username', 'timestamp', 'is_read']
        read_only_fields = ['sender', 'timestamp', 'is_read']