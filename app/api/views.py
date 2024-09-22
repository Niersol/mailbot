import uuid
import json
import base64
import openai
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from .serializers import ConversationSerializer, MessageSerializer
from django.contrib.contenttypes.models import ContentType
from .models import Conversation, Message
from django.http import JsonResponse
from django.db.models import Sum
from rest_framework import generics, permissions
from .models import Product, Collection, Cart, Order
from .serializers import ProductSerializer, CollectionSerializer, CartSerializer, OrderSerializer
from .functions import *
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render,redirect,get_object_or_404
from .function_definitions import *


client = OpenAI(
    api_key=settings.OPENAI_APIKEY
)
def get_assistant_response(messages):
    tools = get_tools()
    model_content_type = ContentType.objects.get(app_label='mailbot', model='finetunningmodel')
    Model = model_content_type.model_class()
    selected_model = Model.objects.filter(selected=True)
    response = client.chat.completions.create(
        model=selected_model[0].output_model,
        messages=messages,
        tools=tools
    )
    return response.choices[0].message

def get_messages(conversation):
    list = []
    messages = Message.objects.filter(conversation = conversation).order_by('created_at')
    for message in messages:
        list.append({'role':message.role,'content':message.content})
    return list

def handleToolCall(tool_call,request):
    tool_call_name = tool_call.function.name
    tool_call_id = tool_call.id
    arguments = json.loads(tool_call.function.arguments)
    if tool_call_name == 'get_crypto_price':
         
        content = get_crypto_price(arguments)
    elif tool_call_name == "get_crypto_info":
        content  = get_crypto_info(arguments)
    elif tool_call_name == 'send_email':
        content = send_email(arguments)
    elif tool_call_name == 'schedule_event':
        content = create_calendar_event(arguments)
    elif tool_call_name == 'get_order_details':
        content = get_order_details(arguments)
    else:
        content = 'Unknown tool call'    
    return {
        'role':'tool',
        'content':content,
        'tool_call_id':tool_call_id
    }

class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        # conversation_id = request.session.get('conversation_id','')
        conversation = Conversation.objects.filter(user=user)
        messages = conversation.messages.all() 
        return Response({

        })

    def post(self, request):
        user = request.user
        start_new = request.data.get('start_new', False)
        messages = []
        print(request.session.session_key)
        print(request.session.get('conversation_id'))
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

        Message.objects.create(conversation=conversation, role='user', content=user_message)
        try:
            assistant_response = get_assistant_response(messages)
            print(assistant_response)
        except Exception as e:
            return Response({'response': f"couldn't generate msg {e}"})
        print(assistant_response.content)
        if assistant_response.tool_calls:
            messages.append(assistant_response)
            tool_call_list = assistant_response.tool_calls
            for tool_call in tool_call_list:
                response = handleToolCall(tool_call,request)
                messages.append(response)
            reply = get_assistant_response(messages)   
            reply = reply.content
            print(reply)
        else:
            reply = assistant_response.content
        try:
            Message.objects.create(conversation=conversation, role='assistant', content=reply)
        except:
            return Response({'response': "couldn't save  assistant msg"})     
        return Response({'response': reply}, status=status.HTTP_201_CREATED)



class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class CollectionListView(generics.ListCreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.AllowAny]

class CollectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.AllowAny]

class CartListView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrderListView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        cart = Cart.objects.get(id=self.request.data['cart_id'])
        serializer.save(user=self.request.user, cart=cart, total_price=cart.items.aggregate(Sum('price'))['price__sum'])

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

from .models import Image
from .serializers import ImageSerializer

class ImageListView(generics.ListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()

class ImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
