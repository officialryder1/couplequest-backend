from django.db import models
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Couple, PairingAttempt, CoupleMessage
from .serializers import CoupleSerializer, CoupleLeaderboardSerializer, CoupleMessageSerializer
from .couple import get_user_couple

from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.decorators import throttle_classes
from rest_framework import generics, permissions
from rest_framework.response import Response
from datetime import timedelta
from core.pusher import pusher_client



import logging
import random


logger = logging.getLogger(__name__)


class CoupleDetailView(generics.RetrieveAPIView):
    queryset = Couple.objects.all()
    serializer_class = CoupleSerializer
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

class CoupleView(generics.ListAPIView):
    queryset = Couple.objects.all()
    serializer_class = CoupleSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])  # Only UserRateThrottle needed for authenticated endpoints
def initiate_pairing(request):
    user = request.user
    couple_name = request.data.get('couple_name', '')
    
    try:
        with transaction.atomic():
            logger.info(f"Initiate pairing requested by {user.id}")
            
            # Check existing couples
            if Couple.objects.filter(
                models.Q(user1=user) | models.Q(user2=user),
                is_active=True
            ).exists():
                logger.warning(f"User {user.id} already in couple")
                return Response(...)
            
            # Generate code
            
            
            
            # Create couple record
            couple = Couple.objects.create(
                user1=user,
                initiated_by=user,
                is_active=False,
                name=couple_name or f"{user.username}'s Couple"
            )

            code = couple.generate_pairing_code()
            logger.info(f"Generated code {code} for {user.id}")

            
            logger.info(f"Couple {couple.id} created successfully")
            return Response({
                "pairing_code": code,
                "expires_at": couple.pairing_code_expires.isoformat(),
                "couple_id": str(couple.id),
                "message": "Share this code with your partner"
            })
            
    except Exception as e:
        logger.error(f"Pairing initiation failed: {str(e)}", exc_info=True)
        return Response(
            {"error": "Pairing failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle, UserRateThrottle]) # 10 attempts per hour from same IP
def confirm_pairing(request):
    """
    Confirm pairing using code
    """
    user = request.user
    pairing_code = request.data.get('pairing_code')
    ip = request.META.get('REMOTE_ADDR')

    # Track attempts
    attempt = PairingAttempt.objects.create(
        user=user,
        ip_address=ip,
        code_attempt=pairing_code or ''
    )

    if not pairing_code:
        return Response(
            {"error": "Pairing code is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check for too many recent attempts
    recent_failures = PairingAttempt.objects.filter(
        ip_address=ip,
        was_successful=False,
        attempted_at__gte=timezone.now() - timedelta(hours=1)
    ).count()

    if recent_failures >= 5:
        return Response(
            {"error": "Too many pairing attempts. Please try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        couple = Couple.objects.get(
            pairing_code=pairing_code,
            is_active=False,
            pairing_code_expires__gt=timezone.now()

        )

        if not couple.is_code_valid():
            raise Couple.DoesNotExist
        
    except Couple.DoesNotExist:
        attempt.save()
        return Response(
            {'error': "Invalid or expired pairing code"}
        )
    
    # Prevent self-pairing
    if couple.user1 == user:
        return Response(
            {'error': "Cannot pair with yourself"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user is already paired
    if Couple.objects.filter(
        models.Q(user1=user) | models.Q(user2=user),
        is_active=True
    ).exists():
        return Response(
            {"error": "You're already in a couple"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    with transaction.atomic():
        couple.activate_pairing(user)
        couple.pairing_code = None
        couple.pairing_code_expires = None
        couple.save()
        attempt.was_successful = True
        attempt.save()

        pusher_client.trigger(
            f'couple-{couple.id}',
            'pairing-completed',
            {
                "message": "Pairing completed!",
                "couple_id": str(couple.id),
                "partner": user.username
            }

        )


    return Response({
        "success": True,
        "couple": CoupleSerializer(couple).data,
        'couple_id': str(couple.id),
        "message": "Pairing successful"
    })

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @throttle_classes([UserRateThrottle, AnonRateThrottle])
# def check_pairing_status(request):
#     """Check if user is in a couple"""
#     user = request.user
#     couple = Couple.objects.filter(
#         models.Q(user1=user) | models.Q(user2=user),
#         is_active=True
#     ).first()
    
#     return Response({
#         "is_paired": couple is not None,
#         "couple": CoupleSerializer(couple).data if couple else None
#     })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_pairing_status(request):
    """
    Check the current user's pairing status
    Returns:
    - is_paired: boolean
    - couple_id: UUID if paired
    - partner_username: string if paired
    - pending_invite: boolean if has pending invite
    - code_expires_at: datetime if pending
    """

    user = request.user

    # Check active couple
    active_couple = Couple.objects.filter(
        (Q(user1=user) | Q(user2=user)),
        is_active=True
    ).first()

    # Check pending invite (where user is user2)
    pending_invite = Couple.objects.filter(
        user2=user,
        is_active=False,
        pairing_code_expires__gt=timezone.now()
    ).first()

    # Check pending code (where user initiated)
    pending_code = Couple.objects.filter(
        user1=user,
        is_active=False,
        pairing_code_expires__gt=timezone.now()
    ).first()

    response_data = {
        'is_paired': active_couple is not None,
        'couple_id': str(active_couple.id) if active_couple else None,
        'partner_username': (
            active_couple.user1.username if active_couple and active_couple.user2 == user
            else active_couple.user2.username if active_couple
            else None
        ),
        'pending_invite': pending_invite is not None,
        'pending_code': pending_code is not None,
        'code_expires_at': (
            pending_code.pairing_code_expires.isoformat() 
            if pending_code 
            else None
        )
    }
    
    return Response(response_data)

@api_view(['GET'])
def leaderboard(request):
    couples = Couple.objects.filter(is_active=True).order_by('-combined_points')[:20]
    serializer = CoupleLeaderboardSerializer(couples, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_message_history(request):
    couple = get_user_couple(request.user)
    if not couple:
        return Response(
            {'error': 'You need to be in an active couple to view messages'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    messages = CoupleMessage.objects.filter(couple=couple).order_by('-timestamp')[:50]
    serializer = CoupleMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_as_read(request):
    couple = get_user_couple(request.user)
    if not couple:
        return Response(
            {'error': 'You need to be in an active couple to mark messages'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Mark all unread messages from partner as read
    partner = couple.user1 if request.user == couple.user2 else couple.user2
    CoupleMessage.objects.filter(
        sender=partner,
        is_read=False
    ).update(is_read=True)
    
    return Response({'status': 'success'})