import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from openai import OpenAI
from .serializers import ConversationSerializer, MessageSerializer
from django.contrib.contenttypes.models import ContentType
from .models import Conversation, Message
from django.http import JsonResponse

client = OpenAI(
    api_key=settings.OPENAI_APIKEY
)
def get_assistant_response(messages):
    model_content_type = ContentType.objects.get(app_label='mailbot', model='finetunningmodel')
    Model = model_content_type.model_class()
    selected_model = Model.objects.filter(selected=True)
    response = client.chat.completions.create(
        model=selected_model[0].output_model,
        messages=messages
    )
    return response.choices[0].message.content

def get_messages(conversation):
    list = []
    messages = Message.objects.filter(conversation = conversation).order_by('created_at')
    for message in messages:
        list.append({'role':message.role,'content':message.content})
    return list

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        print(user.username)
        # conversation_id = request.session.get('conversation_id')
        # conversation = Conversation.objects.filter(id=uuid.UUID(conversation_id), user=user).first() if conversation_id else None
        # messages = conversation.messages.all() if conversation else []

        # serializer = MessageSerializer(messages, many=True)
        return Response('ok')

    def post(self, request):
        user = request.user
        start_new = request.data.get('start_new', False)
        messages = []
        if start_new or 'conversation_id' not in request.session:
            # Create a new conversation
            conversation = Conversation.objects.create(user=user)
            request.session['conversation_id'] = str(conversation.id)
        else:
            # Get the existing conversation
            conversation_id = request.session.get('conversation_id')
            print(conversation_id)
            conversation = get_object_or_404(Conversation, id=uuid.UUID(conversation_id), user=user)
            messages = get_messages(conversation)

        user_message = request.data.get('message')
        print(messages)
        messages.append({'role':'user','content':user_message})
        # Save the user's message
        Message.objects.create(conversation=conversation, role='user', content=user_message)

        # Call the Chat Completion API to get the assistant's response
        assistant_response = get_assistant_response(messages)
        Message.objects.create(conversation=conversation, role='assistant', content=assistant_response)
        
        print(assistant_response)
        return Response({'response': assistant_response}, status=status.HTTP_201_CREATED)
