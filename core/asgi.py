"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack
from core import routing
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(  # Wrap with SessionMiddleware first
        AuthMiddlewareStack(  # Then add AuthMiddleware
            URLRouter(
                routing.websocket_urlpatterns
            )
        )
    ),
})
