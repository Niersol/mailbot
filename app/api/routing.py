from django.urls import path
from . import consumer

websocket_urlpatterns = [
    path('ws/chat/', consumer.ChatConsumer.as_asgi()),
]
