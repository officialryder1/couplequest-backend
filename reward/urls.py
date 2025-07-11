from django.urls import path
from .views import RewardListView, redeem_reward, reward_achievement, get_achievements, check_new_achievements


urlpatterns = [
    path('', RewardListView.as_view(), name='reward-list'),

    path('redeem/<int:reward_id>/', redeem_reward, name='redeem-reward'),
    path('achievements/reward/', reward_achievement, name='reward-achievement'),
    path('achievements/', get_achievements, name='get-achievements'),
    path('achievements/check/', check_new_achievements, name='check-achievements'),
]