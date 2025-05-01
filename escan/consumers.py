from channels.db import database_sync_to_async
from .models import Thread, Message
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.thread = await database_sync_to_async(Thread.objects.get)(id=self.thread_id)
        self.room_group_name = f'inbox_{self.thread.id}'

        # Join room group (this group will include both the user and admin)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        sender = self.scope['user']

        # Get the receiver (admin or user based on the sender)
        receiver = await self.get_receiver()

        # Save the message to the database
        message = await database_sync_to_async(self.save_message)(sender, receiver, message_content)

        # Send the message to both the sender and receiver (both user and admin)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message.content,
                'sender': message.sender.username,
                'receiver': message.receiver.username,  # Send receiver's username to the frontend
                'sender_image_url': message.sender.image_url.url if message.sender.image_url else None,
                'receiver_image_url': message.receiver.image_url.url if message.receiver.image_url else None,
                'timestamp': message.timestamp.isoformat()
            }
        )

    async def chat_message(self, event):
        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'receiver': event['receiver'],
            'sender_image_url': event['sender_image_url'],  # Send sender image URL
            'receiver_image_url': event['receiver_image_url'],  # Send receiver image URL
            'timestamp': event['timestamp'],
        }))

    # Async method to get the receiver
    @database_sync_to_async
    def get_receiver(self):
        # Determine the receiver based on the current user and thread
        if self.scope['user'] == self.thread.user:
            return self.thread.admin
        else:
            return self.thread.user

    def save_message(self, sender, receiver, content):
        # Create the message with both sender and receiver
        message = Message.objects.create(
            thread=self.thread,
            sender=sender,
            receiver=receiver,
            content=content
        )
        return message


# from channels.db import database_sync_to_async
# from .models import Thread, Message
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class InboxConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.thread_id = self.scope['url_route']['kwargs']['thread_id']
#         self.thread = await database_sync_to_async(Thread.objects.get)(id=self.thread_id)
#         self.room_group_name = f'inbox_{self.thread.id}'

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message_content = text_data_json['message']
#         sender = self.scope['user']

#         # Get the receiver based on the thread and current user
#         receiver = await self.get_receiver()

#         # Save the message to the database
#         message = await database_sync_to_async(self.save_message)(sender, receiver, message_content)

#         # Safely get image URLs (stored as strings from Supabase)
#         sender_image = message.sender.image_url if message.sender.image_url else ''
#         receiver_image = message.receiver.image_url if message.receiver.image_url else ''

#         # Send the message to group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message.content,
#                 'sender': message.sender.username,
#                 'receiver': message.receiver.username,
#                 'sender_image_url': sender_image,
#                 'receiver_image_url': receiver_image,
#                 'timestamp': message.timestamp.isoformat()
#             }
#         )

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             'message': event['message'],
#             'sender': event['sender'],
#             'receiver': event['receiver'],
#             'sender_image_url': event['sender_image_url'],
#             'receiver_image_url': event['receiver_image_url'],
#             'timestamp': event['timestamp'],
#         }))

#     @database_sync_to_async
#     def get_receiver(self):
#         return self.thread.admin if self.scope['user'] == self.thread.user else self.thread.user

#     def save_message(self, sender, receiver, content):
#         return Message.objects.create(
#             thread=self.thread,
#             sender=sender,
#             receiver=receiver,
#             content=content
#         )


# your_app/consumers.py

# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import Thread, Message

# class InboxConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.thread_id = self.scope['url_route']['kwargs']['thread_id']
#         self.thread = await database_sync_to_async(Thread.objects.get)(id=self.thread_id)
#         self.room_group_name = f'inbox_{self.thread.id}'

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         # Accept WebSocket connection
#         await self.accept()

#         # Send unread message count and messages initially
#         await self.send_unread_messages()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message_content = text_data_json['message']
#         sender = self.scope['user']

#         # Get the receiver
#         receiver = await self.get_receiver()

#         # Save the message to the database
#         message = await database_sync_to_async(self.save_message)(sender, receiver, message_content)

#         # Send the message to both the sender and receiver (both user and admin)
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message.content,
#                 'sender': message.sender.username,
#                 'receiver': message.receiver.username,
#                 'timestamp': message.timestamp.isoformat(),
#                 'thread_id': self.thread.id,
#                 'sender_image_url': message.sender.image_url,
#                 'is_read': message.is_read
#             }
#         )

#         # After sending the message, send the updated unread message count and messages
#         await self.send_unread_messages()

#     async def chat_message(self, event):
#         # Send the message to WebSocket
#         await self.send(text_data=json.dumps({
#             'type': 'new_message',
#             'message': event['message'],
#             'sender': event['sender'],
#             'receiver': event['receiver'],
#             'timestamp': event['timestamp'],
#             'thread_id': event['thread_id'],
#             'sender_image_url': event['sender_image_url'],
#             'is_read': event['is_read']
#         }))

#     async def send_unread_messages(self):
#         unread_messages = await database_sync_to_async(self.get_unread_messages)()
#         unread_count = len(unread_messages)

#         # Send unread message data to WebSocket
#         await self.send(text_data=json.dumps({
#             'type': 'unread_messages',
#             'unread_count': unread_count,
#             'unread_messages': unread_messages
#         }))

#     @database_sync_to_async
#     def get_receiver(self):
#         # Determine the receiver based on the current user and thread
#         if self.scope['user'] == self.thread.user:
#             return self.thread.admin
#         else:
#             return self.thread.user

#     @database_sync_to_async
#     def save_message(self, sender, receiver, content):
#         # Create and save the message
#         message = Message.objects.create(
#             thread=self.thread,
#             sender=sender,
#             receiver=receiver,
#             content=content
#         )
#         return message

#     @database_sync_to_async
#     def get_unread_messages(self):
#         # Get unread messages for the thread
#         return Message.objects.filter(thread=self.thread, is_read=False).values('id', 'sender__username', 'content', 'timestamp', 'is_read', 'sender__image_url', 'thread__id')

