# chat/consumers.py
import json
import time
from datetime import datetime

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.core.cache import cache


class ChatConsumer(WebsocketConsumer):
    session = ''
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.session = self.scope['session'].get('username', 'default_value')
        print("heree......")
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        session = text_data_json["session"]
        all_messages = cache.get(f'{self.room_name}-chat-messages', {})
        all_messages.update({time.time(): [self.session, message, datetime.now()]})
        cache.set(f'{self.room_name}-chat-messages', all_messages, 86400)

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": '\n'+message, "session": session}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        session = event["session"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "session": session}))

