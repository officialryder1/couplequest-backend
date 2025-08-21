from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserProfileSerializer, UserSerializer
from .models import UserProfile
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import permission_classes, throttle_classes
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.throttling import UserRateThrottle

User = get_user_model()

class LoginView(TokenObtainPairView):
    """
    Custom login view that uses a custom serializer for token generation.
    """
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    """
    View to register a new user.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


# class UserProfileView(generics.RetrieveUpdateAPIView):
#     """
#     View to retrieve and update the user's profile.
#     """
#     serializer_class = UserProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
def user_stats(request):
    profile = request.user.userprofile
    return Response({
        'xp': profile.xp,
        'level': profile.level,
        'streak': profile.streak
    })

@api_view(['POST'])
def register(request):
    """
    Register a new user with proper password hashing
    """
    serializer = UserSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Hash password before saving
            validated_data = serializer.validated_data
            validated_data['password'] = make_password(validated_data['password'])
            
            user = User.objects.create(**validated_data)
            
            return Response({
                'status': 'success',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            # Catch any unexpected errors
            return Response({
                'status': 'error',
                'message': f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # If serializer is invalid
    return Response({
        'status': 'error',
        'message': 'Registration failed. Please check the provided details.',
        'errors': serializer.errors  # <-- still keep field-specific errors
    }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@login_required
def pusher_auth(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            socket_id = data['socket_id']
            channel_name = data['channel_name']
            
            # SECURITY CHECK: User can only access their own channel
            expected_prefix = f'private-user-{request.user.id}'
            if not channel_name.startswith(expected_prefix):
                return JsonResponse(
                    {'error': 'Channel access denied'}, 
                    status=403
                )
            
            # Initialize Pusher (match your existing config)
            from pusher import Pusher
            pusher = Pusher(
                app_id=settings.PUSHER_APP_ID,
                key=settings.PUSHER_KEY,
                secret=settings.PUSHER_SECRET,
                cluster=settings.PUSHER_CLUSTER
            )
            
            # Generate the auth response
            auth = pusher.authenticate(
                channel=channel_name,
                socket_id=socket_id
            )
            
            return JsonResponse(auth)
            
        except Exception as e:
            return JsonResponse(
                {'error': f'Authentication failed: {str(e)}'},
                status=400
            )
    
    return JsonResponse(
        {'error': 'Invalid request method'},
        status=405
    )


from .serializers import UserDetailSerializer
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UserRateThrottle])
def current_user(request):

    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data)