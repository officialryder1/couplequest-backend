from rest_framework import serializers
from .models import Reward, CoupleAchievement, Achievement


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = '__all__'

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'


class CoupleAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoupleAchievement
        fields = '__all__'