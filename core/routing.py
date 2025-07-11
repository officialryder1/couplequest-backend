from couple.consumers import ChatConsumer, CoupleConsumer
from django.urls import re_path, path



websocket_urlpatterns = [
    re_path(r'^ws/chat/$', ChatConsumer.as_asgi()),
    re_path(r'ws/couple/$', CoupleConsumer.as_asgi()),
    path('ws/chat/<int:couple_id>', ChatConsumer.as_asgi()),
]