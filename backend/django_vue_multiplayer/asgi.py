import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from app import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_vue_multiplayer.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    'websocket': URLRouter([
        path('ws/game/', consumers.GameConsumer.as_asgi()),
    ]),
})
