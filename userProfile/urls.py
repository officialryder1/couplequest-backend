from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, RegisterView, user_stats, register, pusher_auth, current_user

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('register-userprofile/', RegisterView.as_view(), name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', current_user, name='current_user'),
    
    path('stats/', user_stats, name='user-stats'),
    path('pusher/auth/', pusher_auth, name='pusher_auth'),

]