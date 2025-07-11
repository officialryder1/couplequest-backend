import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Couple, CoupleMessage
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import sync_to_async


class CoupleConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.accept()

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        

        # Get the couple group name
        self.couple = await self.get_user_couple()
        if not self.couple:
            await self.close()
            return
        
        # join couple group
        await self.channel_layer.group_add(
            self.couple_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave coupe group
        if hasattr(self, 'couple_group_name'):
            await self.channel_layer.group_discard(
                self.couple_group_name,
                self.channel_name
            )

    @database_sync_to_async
    def get_user_couple(self):
        return Couple.objects.filter(
            (Q(user1=self.user) | Q(user2=self.user)),
            is_active=True
        ).first()
    
    async def receive(self, text_data):
        # Handle incoming messages (if needed)
        pass

    async def couple_update(self, event):
        # Send updates to the client
        await self.send(text_data=json.dumps(event))



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.accept()

        self.couple_id = self.scope['url_route']['kwargs']['couple_id']
        self.room_group_name = f'chat_{self.couple_id}'
        
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_content = data.get('message')
            
            if not message_content:
                return

            # Save message to database
            message = await self.save_message(
                user=self.scope["user"],
                content=message_content
            )
            
            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message.content,
                    "sender": message.sender.username,
                    "timestamp": message.timestamp.isoformat(),
                    "message_id": message.id
                }
            )
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def save_message(self, user, content):
        from .models import Couple
        couple = Couple.objects.get(id=self.couple_id)
        return CoupleMessage.objects.create(
            couple=couple,
            sender=user,
            content=content
        )