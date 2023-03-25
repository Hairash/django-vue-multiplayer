from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from app import consumers

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/game/', consumers.GameConsumer.as_asgi()),
    ]),
})
