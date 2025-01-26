from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import ChatRoom, Message
from channels.db import database_sync_to_async
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
from auths.models import CustomUser

class GeneralChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.hackathon_id = self.scope['url_route']['kwargs']['hackathon_id']
        self.room_name = f"hackathon_{self.hackathon_id}_general"
        self.chatroom = await self.get_or_create_chatroom(self.room_name)

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        messages = await self.get_message_history(self.chatroom)
        await self.send(text_data=json.dumps({'history': messages[::-1]}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']

        if user.is_authenticated:
            await self.save_message(user, self.chatroom, message)

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user.full_name if user.is_authenticated else "Anonymous",
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        await self.send(text_data=json.dumps({'message': message, 'user': user}))

    @sync_to_async
    def get_or_create_chatroom(self, room_name):
        return ChatRoom.objects.get_or_create(name=room_name)[0]

    @sync_to_async
    def save_message(self, user, chatroom, content):
        Message.objects.create(sender=user, room=chatroom, content=content)

    @sync_to_async
    def get_message_history(self, chatroom):
        messages = chatroom.messages.all().order_by('-timestamp')[:50]
        return [
            {'user': msg.sender.full_name, 'message': msg.content, 'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            for msg in messages
        ]


class TeamChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.team_id = self.scope['url_route']['kwargs']['team_id']
        self.room_name = f"team_{self.team_id}"
        self.chatroom = await self.get_or_create_chatroom(self.room_name)

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        messages = await self.get_message_history(self.chatroom)
        await self.send(text_data=json.dumps({'history': messages[::-1]}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']

        if user.is_authenticated:
            await self.save_message(user, self.chatroom, message)

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user.username if user.is_authenticated else "Anonymous",
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        await self.send(text_data=json.dumps({'message': message, 'user': user}))

    @sync_to_async
    def get_or_create_chatroom(self, room_name):
        return ChatRoom.objects.get_or_create(name=room_name)[0]

    @sync_to_async
    def save_message(self, user, chatroom, content):
        Message.objects.create(sender=user, room=chatroom, content=content)

    @sync_to_async
    def get_message_history(self, chatroom):
        messages = chatroom.messages.all().order_by('-timestamp')[:50]
        return [
            {'user': msg.sender.username, 'message': msg.content, 'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            for msg in messages
        ]


class DMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user1_id = self.scope['url_route']['kwargs']['user1_id']
        self.user2_id = self.scope['url_route']['kwargs']['user2_id']
        self.room_name = f"dm_{min(self.user1_id, self.user2_id)}_{max(self.user1_id, self.user2_id)}"
        self.chatroom = await self.get_or_create_chatroom(self.room_name)

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        messages = await self.get_message_history(self.chatroom)
        await self.send(text_data=json.dumps({'history': messages[::-1]}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']

        if user.is_authenticated:
            await self.save_message(user, self.chatroom, message)

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user.username if user.is_authenticated else "Anonymous",
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        await self.send(text_data=json.dumps({'message': message, 'user': user}))

    @sync_to_async
    def get_or_create_chatroom(self, room_name):
        return ChatRoom.objects.get_or_create(name=room_name)[0]

    @sync_to_async
    def save_message(self, user, chatroom, content):
        Message.objects.create(sender=user, room=chatroom, content=content)

    @sync_to_async
    def get_message_history(self, chatroom):
        messages = chatroom.messages.all().order_by('-timestamp')[:50]
        return [
            {'user': msg.sender.username, 'message': msg.content, 'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            for msg in messages
        ]




load_dotenv()
genai.configure(api_key=os.getenv('API_KEY'))

config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain"
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=config,
    system_instruction="""
    Classify requests into exactly one of these categories:
    - Frontend
    - Backend
    - Full Stack
    - UI/UX
    - AI/ML

    Respond only with the category name. Example response:
    Frontend
    """
)


class TeamFinderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user_input = text_data_json.get('message')
        current_user = self.scope["user"]

        if user_input:
            chat_session = model.start_chat()
            response = chat_session.send_message(user_input)
            response_text = response.text
            skill_category = self.parse_skill(response_text)
            teammates = await database_sync_to_async(self.filter_by_skill)(current_user, skill_category)

            await self.send(text_data=json.dumps({
                'skill_category': skill_category,
                'teammates': self.format_teammates(teammates)
            }))

    def parse_skill(self, response_text):
        response_text = response_text.lower()
        categories = ["frontend", "backend", "full stack", "ui/ux", "ai/ml"]

        for category in categories:
            if category in response_text:
                return category.capitalize()
        return "Other"

    def format_teammates(self, users):
        return [{
            'id': user['id'],
            'name': user['full_name'],
            'skills': user['skills'].split(',') if user['skills'] else [],
            'github_score': user['github_score'],
            'profile': f"http://localhost:5173/user/{user['id']}"
        } for user in users]

    def filter_by_skill(self, current_user, skill_category):
        return list(CustomUser.objects.exclude(id=current_user.id)
            .filter(skills__icontains=skill_category)
            .values('id', 'full_name', 'skills', 'github_score'))