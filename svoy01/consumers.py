from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from .models import Messages, Chat


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # c = Chat.objects.filter(owner=self.scope['user'])
        # print(c[1].name, c[1])
        # print(self.scope['user'])

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = self.scope['user']

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': str(username),
            }
        )
        if message:
            Messages.objects.create(author=self.scope['user'],
                                    text=message,
                                    room_name=self.room_name,
                                    chat_id=Chat.objects.filter(name=self.room_name,
                                                                owner=self.scope['user']).get().pk)

    def chat_message(self, event):
        message = event['message']
        username = event['username']

        self.send(text_data=json.dumps({
            'event': "Send",
            'message': message,
            'username': username
        }))
