
from django.urls import path

from . import chatconsumer

websocket_urlpatterns = [
   
    path('ws/chat/', chatconsumer.ChatConsumer),
    
]