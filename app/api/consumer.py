import json
import uuid
import openai
from openai import OpenAI
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import User
from .models import Conversation, Message
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from asgiref.sync import async_to_sync
import uuid  # For generating unique conversation IDs

client = OpenAI(
    api_key=settings.OPENAI_APIKEY
)
class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_id = None

    def connect(self):
        
        self.conversation_id = str(uuid.uuid4())  # Generates a unique ID

        # Step 2: Accept the WebSocket connection
        self.accept()

        # Step 3: Add this connection to the conversation group using the unique conversation_id
        async_to_sync(self.channel_layer.group_add)(
            self.conversation_id,
            self.channel_name
        )

        # Optionally, send the generated conversation_id back to the client
        self.send(text_data=json.dumps({
            'conversation_id': self.conversation_id,
            'message': 'Connection established. New conversation started.'
        }))

    def disconnect(self, code):
        # Remove the connection from the group when the WebSocket disconnects
        async_to_sync(self.channel_layer.group_discard)(
            self.conversation_id,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        # Handle incoming messages
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Forward the message to GPT or the agent handling logic
        self.send_gpt_response(message)




    def send_gpt_response(self, message):
        messages=[
                {'role':'system',  "content": "You are a helpful  AI assistant. Your job is to generate ideal responses."},
            ]
        messages.append({'role':'user','content':message})
        gpt_response = self.get_bot_response(messages)
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_id,
            {
                'type': 'chat_message',
                'message': gpt_response
            }
        )

    def notify_agent(self, message):
        # Notify the agent that GPT couldn't answer
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_id,
            {
                'type': 'chat_message',
                'message': "An agent will assist you shortly."
            }
        )

    def chat_message(self, event):
        # Send message back to the client
        self.send(text_data=json.dumps(event))

    def get_bot_response(self, messages):
        # Placeholder logic for bot response (integrate with GPT-4 here)
        model_content_type = ContentType.objects.get(app_label='mailbot', model='finetunningmodel')
        Model = model_content_type.model_class()
        selected_model = Model.objects.filter(selected=True)
        response = client.chat.completions.create(
            model=selected_model[0].output_model,
            messages=messages,
        )
        return response.choices[0].message.content
# class ChatConsumer(WebsocketConsumer):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.conversation_id = None

#     def connect(self):
#         self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
#         self.accept()
#         async_to_sync(self.channel_layer.group_add)(
#             self.conversation_id,
#             self.channel_name
#         )

#     def disconnect(self, code):
#         async_to_sync(self.channel_layer.group_discard)(
#             self.conversation_id,
#             self.channel_name
#         )

#     def receive(self, text_data=None, bytes_data=None):

#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']
#         async_to_sync(self.channel_layer.group_send)(
#             self.conversation_id,
#             {
#                 'type':'chat_message',
#                 'message':message
#             }
#         )

#     def chat_message(self,event):
#         self.send(text_data=json.dumps(event))

# class ChatConsumer(WebsocketConsumer):
#     def connect(self):
#         self.user = self.scope["user"]
#         self.conversation_id = None

#         print(self.scope["user"])
#         if self.user is not None and self.user.is_authenticated:
#             self.accept()  # Accept the connection
#         else:
#             self.close()   # Close connection if user is not authenticated
#     def disconnect(self, close_code):
#         # Clean up when the connection closes (if needed)
#         pass

#     def receive(self, text_data):
#         data = json.loads(text_data)
#         messages=[
#                 {'role':'system',  "content": "You are a helpful mailbot AI assistant. Your job is to generate ideal gmail responses. The format of the email doesn't matter, provide answer in plain text without subject."},
#             ]
#         message = data['message']
        
#         action = data.get('action', None)

#         if action == 'clear':
#             # Start a new conversation if 'clear' action is received
#             self.start_new_conversation()
#         elif not self.conversation_id:
#             # Start a new conversation on first message if no conversation exists
#             self.start_new_conversation()
#         # Save user message
#         self.save_message('user', message)
#         messages.append({'role':'user','content':message})
#         # Example bot response logic (replace with GPT integration)
#         response_message = self.get_bot_response(messages)

#         # Save bot response message
#         self.save_message('assistant', response_message)

#         # Send bot response back to client
#         self.send(text_data=json.dumps({
#             'message': response_message
#         }))

#     def start_new_conversation(self):
#         if self.user.is_authenticated:
#             print("user is authenticated")
#             user_instance = self.user._wrapped if hasattr(self.user, '_wrapped') else self.user

#             # Create a new conversation for the user
#             conversation = Conversation.objects.create(user=user_instance)
#             self.conversation_id = conversation.id
#         else:
#             print('closed')
#             # Handle the case where the user is not authenticated
#             self.close()

#     def save_message(self, role, content):
#         # Save a new message to the conversation
#         conversation = Conversation.objects.get(id=self.conversation_id)
#         all_messages = Message.objects.filter(conversation=conversation)
#         print(all_messages.values())
#         Message.objects.create(conversation=conversation, role=role, content=content)

    # def get_bot_response(self, messages):
    #     # Placeholder logic for bot response (integrate with GPT-4 here)
    #     model_content_type = ContentType.objects.get(app_label='mailbot', model='finetunningmodel')
    #     Model = model_content_type.model_class()
    #     selected_model = Model.objects.filter(selected=True)
    #     response = client.chat.completions.create(
    #         model=selected_model[0].output_model,
    #         messages=messages,
    #     )
    #     return response.choices[0].message.content
