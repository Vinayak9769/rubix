import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chats.routing
from chats.middleware import JWTAuthMiddlewareStack as TokenAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rubix.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            chats.routing.websocket_urlpatterns
        )
    ),
})
