from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer,UserSerializer 
from .models import Conversation, Message

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id','username','password','email','first_name','last_name']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'updated_at', 'messages']