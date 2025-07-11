from django.conf import settings
from pusher import Pusher

pusher_client =Pusher(
    app_id = settings.PUSHER_APP_ID,
    key = settings.PUSHER_KEY,
    secret = settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)

def trigger_pusher(channel, event, data):
    try:
        pusher_client.trigger(channel, event, data)
    except Exception as e:
        print(f"Pusher trigger failed: {str(e)}")