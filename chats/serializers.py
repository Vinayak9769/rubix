from rest_framework import serializers
from .models import ChatRoom, Message
from auths.models import CustomUser

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat_room', 'sender', 'sender_name', 'content', 'timestamp']
        read_only_fields = ['timestamp']

from rest_framework import serializers
from .models import ChatRoom

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'created_at']

