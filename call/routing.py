# call/routing.py
from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path(r'ws/call/<username>/', consumers.CallConsumer.as_asgi()),
    path(r'ws/call/<username>/<not_user>/', consumers.CallConsumer.as_asgi()),
    path(r'ws/call/<username>/<not_user>/', consumers.CallConsumer.as_asgi()),
]