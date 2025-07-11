from rest_framework import generics, permissions
from .models import Task
from .serializers import TaskSerializer, TaskCreateSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .signals import update_user_stats
from django.db import transaction
from couple.models import Couple
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from reward import achievement_checker
from reward.serializers import AchievementSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from couple.couple import get_user_couple
from core.pusher import pusher_client


def calculate_level(xp):
    """Calculate level based on XP"""
    return int((xp / 100) ** 0.6) + 1

class TaskPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    # pagination_class = TaskPagination
    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filter_backends = ["is_completed"]
    # ordering_fields = ['created_at', 'due_date', 'points']
    # ordering = ['-created_at']

    def perform_create(self, serializer):
        # Automatically set the task's creator
        serializer.save(created_by=self.request.user)

    
@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def complete_task(request, task_id):
    """
    Mark a task as completed and update user/couple stats
    ---
    parameters:
      - name: task_id
        required: true
        type: integer
    responses:
      200:
        description: Task successfully completed
      400:
        description: Invalid request
      403:
        description: Unauthorized access
      404:
        description: Task not found
    """
    try:
        # Get task with related couple data in single query
        task = Task.objects.select_related('couple').get(id=task_id)
        user = request.user

        # Verify authorization
        if user not in [task.couple.user1, task.couple.user2]:
            return Response(
                {'error': 'Unauthorized to complete this task'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already completed
        if task.is_completed:
            return Response(
                {'error': 'Task already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Complete the task
        task.complete(user)
        pusher_client.trigger(
            f'couple-{task.couple.id}',
            "task-updated",
            {
                "task": TaskSerializer(task).data,
                "message": f"{user.username} completed a task!"
            }
        )

       

        # Check for achievements
        new_achievements = achievement_checker.AchievementChecker.check_all_achievements(task.couple)

        for achievement in new_achievements:
            pusher_client.trigger(
                f"couple-{task.couple.id}",
                "achievement-unlocked",
                {
                    "achievement": AchievementSerializer(achievement).data,
                    "message": "🎉 Achievement unlocked!"
                }
            )

        
        # Update streak and calculate bonus
        streak = task.couple.update_streak()
        streak_bonus = task.couple.get_streak_bonus()
        bonus_points = int(task.points * streak_bonus)

        # Update user stats
        user_profile = user.userprofile
        user_profile.xp += task.points
        user_profile.level = calculate_level(user_profile.xp)
        user_profile.save()

        # Update couple points if paired
        couple = Couple.objects.filter(
            (Q(user1=user) | Q(user2=user)) & Q(is_active=True)
        ).first()

        if couple:
            couple.combined_points = (
                couple.user1.userprofile.xp + 
                (couple.user2.userprofile.xp if couple.user2 else 0)
            )
            couple.save()

        return Response(TaskSerializer(task).data)

    except Task.DoesNotExist:
        return Response(
            {'error': 'Task not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        transaction.set_rollback(True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_task(request):
    serializer = TaskCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Get user's active couple
        couple = Couple.objects.filter(
            (Q(user1=request.user) | Q(user2=request.user)) & 
            Q(is_active=True)
        ).first()
        
        if not couple:
            return Response(
                {'error': 'You need to be in an active couple to create tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task = serializer.save(
            couple=couple,
            created_by=request.user
        )

        pusher_client.trigger(
            f"couple-{couple.id}",
            "task_created",
            {
                "task": TaskSerializer(task).data,
                "message": f"{request.user.username} created a new task"
            }
        )
        
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_tasks(request):
    status = request.query_params.get('status', None)
    page = request.query_params.get('page', 1)
    
    couple = get_user_couple(request.user)
    if not couple:
        return Response({'error': 'No active couple'}, status=400)
    
    tasks = Task.objects.filter(couple=couple)
    
    # Filter by status
    if status == 'done':
        tasks = tasks.filter(is_completed=True)
    elif status == 'undone':
        tasks = tasks.filter(is_completed=False)
    
    # Paginate results
    paginator = TaskPagination()
    result_page = paginator.paginate_queryset(tasks, request)
    serializer = TaskSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)