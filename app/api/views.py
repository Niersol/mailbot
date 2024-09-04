import uuid
import json
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
from django.db.models import Sum
from rest_framework import generics, permissions
from .models import Product, Collection, Cart, Order
from .serializers import ProductSerializer, CollectionSerializer, CartSerializer, OrderSerializer
from .functions import *
tools = [
    {
        'type':'function',
        'function':{
            'name': 'inquiry_about_collection',
            'description':'Call this function when some one inquires about Collection of Products. Such as, what to wear in winter? or Products to wear in Summer?',
            "parameters":{
                'type':'object',
                'properties':{
                    'collection_name':{
                        'type':'string',
                        'description':'The name of the collection, such as Formal Collection, Winter Collection, Summer Collection'
                    }
                },
                'required':['collection_name'],
                'additionalProperties':False,
            },
        }
    },
]
client = OpenAI(
    api_key=settings.OPENAI_APIKEY
)
def get_assistant_response(messages):
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

def handleToolCall(tool_call):
    tool_call_name = tool_call.function.name
    tool_call_id = tool_call.id
    arguments = json.loads(tool_call.function.arguments)
    if tool_call_name == 'inquiry_about_collection':
        return inquiry_about_collection(arguments)

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # conversation_id = request.session.get('conversation_id')
        # conversation = Conversation.objects.filter(id=uuid.UUID(conversation_id), user=user).first() if conversation_id else None
        # messages = conversation.messages.all() if conversation else []

        # serializer = MessageSerializer(messages, many=True)
        return Response('ok')

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
        # Save the user's message
        Message.objects.create(conversation=conversation, role='user', content=user_message)
        data = ''
        # Call the Chat Completion API to get the assistant's response
        assistant_response = get_assistant_response(messages)
        if assistant_response.tool_calls:
            messages.append(assistant_response)
            tool_call_list = assistant_response.tool_calls
            for tool_call in tool_call_list:
                response = handleToolCall(tool_call)
                if(type(response)==list or response.role == 'raw'):
                    data = response
                else:
                    messages.append(response)
            reply = get_assistant_response(messages)
        else:
            reply = assistant_response.content
        Message.objects.create(conversation=conversation, role='assistant', content=reply)
        
        print(assistant_response)
        return Response({'response': reply,'data':data}, status=status.HTTP_201_CREATED)



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
