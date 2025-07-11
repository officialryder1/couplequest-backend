from rest_framework import generics, permissions
from .models import Reward, Achievement, CoupleAchievement
from .serializers import RewardSerializer, AchievementSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from couple.models import Couple
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.db import transaction
from django.db import models
from .achievement_checker import AchievementChecker
from couple.couple import get_user_couple

class RewardListView(generics.ListAPIView):
    """
    View to list all rewards.
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

@api_view(['POST'])
def redeem_reward(request, reward_id):
    reward = Reward.objects.get(id=reward_id)
    profile = request.user.userprofile
    if profile.xp >= reward.cost:
        profile.xp -= reward.cost
        profile.save()
        reward.is_unlocked = True
        reward.save()
        return Response({'success': f'Reward "{reward.name}" unlocked!'})
    return Response({'error': 'Not enough XP!'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reward_achievement(request):
    """
    Grants an achievement to a couple.
    Required POST data:
    - achievement_id: ID of the achievement to grant
    - couple_id: ID of the couple receiving the achievement
    """
    achievement_id = request.data.get('achievement_id')
    couple_id = request.data.get('couple_id')

    # Validate required fields
    if not achievement_id or not couple_id:
        return Response(
            {'error': 'Both achievement_id and couple_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    

    try:
        # Verify the requesting user is part of the couple
        couple = Couple.objects.get(
            id=couple_id,
            is_active=True,
            user1=request.user
        )
        
        achievement = Achievement.objects.get(id=achievement_id)
        
        # Check if already unlocked
        if CoupleAchievement.objects.filter(couple=couple, achievement=achievement).exists():
            return Response(
                {'error': 'This couple already has this achievement'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the achievement unlock
        couple_achievement = CoupleAchievement.objects.create(
            couple=couple,
            achievement=achievement
        )

        # Update couple XP (sum for both users)
        couple.user1.profile.xp += achievement.xp_reward
        couple.user2.profile.xp += achievement.xp_reward
        couple.user1.profile.save()
        couple.user2.profile.save()

        return Response({
            'success': True,
            'achievement': AchievementSerializer(achievement).data,
            'unlocked_at': couple_achievement.unlocked_at,
            'xp_added': achievement.xp_reward * 2  # XP for both users
        }, status=status.HTTP_201_CREATED)

    except Couple.DoesNotExist:
        return Response(
            {'error': 'Couple not found or you are not a member'},
            status=status.HTTP_403_FORBIDDEN
        )
    except Achievement.DoesNotExist:
        return Response(
            {'error': 'Achievement not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_achievements(request):
    couple = get_user_couple(request.user)  # Assuming user is in a couple
    
    unlocked = CoupleAchievement.objects.filter(
        couple=couple
    ).select_related('achievement')
    
    locked = Achievement.objects.exclude(
        id__in=unlocked.values_list('achievement_id', flat=True)
    )
    
    return Response({
        'unlocked': [
            {
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'xp_reward': ua.achievement.xp_reward,
                'unlocked_at': ua.unlocked_at
            }
            for ua in unlocked
        ],
        'locked': [
            {
                'id': ach.id,
                'name': ach.name,
                'description': ach.description,
                'icon': ach.icon,
                'xp_reward': ach.xp_reward
            }
            for ach in locked
        ]
    })

@api_view(['GET'])
def check_new_achievements(request):
    couple = get_user_couple(request.user)

    if not couple:
        return Response(
            {'error': 'You need to be in an active couple to check achievements'},
            status=status.HTTP_403_FORBIDDEN
        )
    new_achievements = AchievementChecker.check_all_achievements(couple)
    
    return Response(AchievementSerializer(new_achievements, many=True).data)