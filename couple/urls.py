from django.urls import path
from .views import CoupleDetailView, initiate_pairing, check_pairing_status, confirm_pairing, leaderboard, CoupleView, get_message_history, mark_messages_as_read

urlpatterns = [
    path('', CoupleView.as_view(), name="couple-list"),
    path('<int:pk>/', CoupleDetailView.as_view(), name='couple-detail'),
    path('pairing/initiate/', initiate_pairing, name='initiate-pairing'),
    path('pairing/confirm/', confirm_pairing, name='confirm-pairing'),
    path('pairing/status/', check_pairing_status, name='pairing-status'),

    path('leaderboard/', leaderboard, name='couple-leaderboard'),

    path('messages/', get_message_history, name='message-history'),
    path('messages/read/', mark_messages_as_read, name='mark-messages-read'),
]