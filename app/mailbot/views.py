import os
import json
import tempfile
import openai
import requests
from openai import OpenAI
from datetime import datetime
from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from google_auth_oauthlib.flow import Flow
from api.models import Credentials as creds
from .functions import *
from .models import *
CLIENT_SECRETS_FILE = 'client_secret_18918845091-50aqcb5shf2l427gujdncbi61pt3316h.apps.googleusercontent.com.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/calendar']
def initialize_client():
    try:
        # api_key = APIKey.objects.get(pk=1)
        # if api_key:
            client = OpenAI(
                api_key=settings.OPENAI_APIKEY
            )
            return client
    except ObjectDoesNotExist:
        return None

def credentials_to_dict(credentials):
    return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

def authorize(request):
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = request.build_absolute_uri('oauth2callback')
    print(flow.redirect_uri)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='false'
    )

    request.session['state'] = state
    print(authorization_url)
    return redirect(authorization_url)

def clear_credentials(request):
    if 'credentials' in request.session:
        del request.session['credentials']
        try:
            creds.objects.get(id=1).delete()
        except:
            print("no obj found")
    return redirect('authorize')

def oauth2callback(request):
    state = request.session['state']

    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = request.build_absolute_uri("http://127.0.0.1:8000/dashboard/authorize/oauth2callback")
    print(flow.redirect_uri)
    authorization_response = request.build_absolute_uri()

    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    scopes_str = ','.join(credentials.scopes)  # Convert the list of scopes to a comma-separated string
    try:
        cred = creds.objects.get(id=1)
        cred.token = credentials.token
        cred.refresh_token = credentials.refresh_token
        cred.client_id = credentials.client_id
        cred.client_secret = credentials.client_secret
        cred.token_uri = credentials.token_uri
        cred.scopes = scopes_str
        cred.save()

    except ObjectDoesNotExist:
        cred = creds.objects.create(
            id=1,
            token=credentials.token,
            refresh_token = credentials.refresh_token,
            token_uri = credentials.token_uri,
            client_id=credentials.client_id,
            client_secret = credentials.client_secret,
            scopes = scopes_str
        )
    return redirect('models-list')

def active_users_list(request):
    users = User.objects.filter(is_active=True).exclude(is_staff=True, is_superuser=True)
    
    user_data = [{'id': user.pk, 'username': user.username} for user in users]
    
    return JsonResponse({'active_users': user_data})

def user_conversations(request, user_id):
    model_content_type = ContentType.objects.get(app_label='api', model='conversation')
    Conversation = model_content_type.model_class()

    user = get_object_or_404(User, pk=user_id, is_active=True, is_staff=False, is_superuser=False)
    
    # Get all conversations for the user
    conversations = Conversation.objects.filter(user=user).prefetch_related('messages')
    
    # Prepare the data to be returned as JSON
    conversation_data = []
    for conversation in conversations:
        messages = [{'role': message.role, 'content': message.content, 'created_at': message.created_at} for message in conversation.messages.all()]
        conversation_data.append({
            'conversation_id': conversation.id,
            'created_at': conversation.created_at,
            'messages': messages
        })

    return JsonResponse({'user': {'id': user.pk, 'username': user.username}, 'conversations': conversation_data})


def format_record(record):
    """Format a single record to match the desired JSON Lines format."""
    
    # Create the message structure
    messages = [
        {"role": 'system', "content": record['system']},
        {"role": 'user', "content": record['user']},
        {"role": 'assistant', "content": record['assistant']}
    ]
    
    return {"messages": messages}

def fine_tune(request):
    if request.method == 'POST':
        client = initialize_client()
        if not client:
            request.session['error'] = 'API key is wrong or Does not Exist.'
            return redirect(reverse('api-key'))
        model_name = request.POST.get('model_name','')
        base_model = request.POST.get('base_model','')
        prompts = FineTuneExample.objects.all()
        if len(prompts) < 10:
            return JsonResponse({'status': 'failed', 'err': 'There should be at least 10 prompts'})

        data = [format_record(record) for record in prompts.values()]
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            for record in data:
                temp_file.write(json.dumps(record) + '\n')

            temp_file_name = temp_file.name
        try:
            # Upload the temporary file
            with open(temp_file_name, 'rb') as file_to_upload:
                try:
                    file = client.files.create(
                        file=file_to_upload,
                        purpose="fine-tune"
                    )
                except openai.AuthenticationError:
                    request.session['error'] = 'API key is wrong or Does not Exist.'
                    return redirect(reverse('api-key'))
            try:
                response = client.fine_tuning.jobs.create(
                    training_file=file.id,
                    model=base_model
                )
            except openai.AuthenticationError:
                request.session['error'] = 'API key is wrong or Does not Exist.'
                return redirect(reverse('api-key'))
            
            created_at_datetime = datetime.fromtimestamp(response.created_at)
            created_at_datetime = timezone.make_aware(created_at_datetime)
            FineTunningModel.objects.create(model_id=response.id,created_at=created_at_datetime,model_name=model_name)
            return JsonResponse({'status': 'success'})
        finally:
            # Ensure the temporary file is deleted after use
            os.remove(temp_file_name)

def select_model(request,job_id):
    action = request.POST.get('action','')
    output_model = request.POST.get('output_model','')
    all_fine_tune_models = FineTunningModel.objects.update(selected=False)
    if action == 'select':
        fine_tune_model = FineTunningModel.objects.get(model_id=job_id)
        fine_tune_model.selected = True
        fine_tune_model.output_model = output_model
        fine_tune_model.save()
    return JsonResponse({
        'status':'success'
    })

class ApiKey(View):
    def get(self,request):
        context = {
            'api_key':''
        }
        try:
            api_key = APIKey.objects.get(id=1)
            context['api_key'] = api_key.api_key
        except Exception:
            pass
        
        context['error'] = request.session.pop('error',None)
        return render(request,'api_key/index.html',context=context)
    def post(self,request):
        api_key = request.POST.get('api_key')
        if api_key:
            # Save the API key to the database
            APIKey.objects.update_or_create(
                id=1,
                defaults={'api_key': api_key}
            )
            # Redirect to the page where the OpenAI client is used
            return redirect(reverse('models-list'))  # Change to the relevant view
        return render(request, 'api_key/index.html', {'error': 'API Key is required'})
    
class FineTunningListView(View):
    client = initialize_client()
    def get(self,request):
        if not self.client:
            request.session['error'] = 'API key is wrong or Does not Exist.'
            return  redirect(reverse('api-key'))
        try:
            try:
                response = self.client.fine_tuning.jobs.list()
            except openai.AuthenticationError:
                request.session['error'] = 'API key is wrong or Does not Exist.'
                return redirect(reverse('api-key'))
            jobs = []
            for job in response:

                # Convert created_at timestamp to a datetime object
                created_at_datetime = datetime.fromtimestamp(job.created_at)
                created_at_datetime = timezone.make_aware(created_at_datetime)
                model,created = FineTunningModel.objects.get_or_create(model_id=job.id,
                            defaults={'created_at': created_at_datetime}  # Use defaults to set 'created_at' only if created
                )
                # Convert datetime object to a formatted string
                job_dict = job.to_dict()  # Convert job object to a dictionary
                job_dict['model_name'] = model.model_name
                job_dict['selected'] = model.selected
                job_dict['created_at'] = created_at_datetime.strftime('%d-%m-%y %H:%M')
                jobs.append(job_dict)
        except Exception as e:
            jobs = []
            print(f"An error occurred: {e}")
        return render(request,'fine_tunning/index.html', {'jobs': jobs})
    

class FineTunnigDetailView(View):
    client = initialize_client()
    def get(self,request, job_id):
        if not self.client:
            request.session['error'] = 'API key is wrong or Does not Exist.'
            return redirect(reverse('api-key'))
        # Replace this with your actual query to fetch the job details
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
        except openai.AuthenticationError:
            request.session['error'] = 'API key is wrong or Does not Exist.'
            return redirect(reverse('api-key'))
        fine_tune_model = FineTunningModel.objects.get(model_id=job_id)
        created_at_datetime = datetime.fromtimestamp(job.created_at)
        job_dict = job.to_dict()  # Convert job object to a dictionary
        job_dict['selected'] = fine_tune_model.selected
        job_dict['created_at'] = created_at_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        return JsonResponse({
            'job':job_dict
        })
    
class FineTuneExampleListView(View):
    LIST_OF_BASE_MODELS = [
        'babbage-002',
        'davinci-002',
        'gpt-3.5-turbo-0125',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-1106',
        'gpt-4o-2024-08-06',
        'gpt-4o-mini-2024-07-18',
    ]
    def get(self,request):
        examples = FineTuneExample.objects.all()
        examples_data = [{
            'id':example.pk,
            'user':example.user,
            'system':example.system,
            'assistant':example.assistant
        } for example in examples]
        return render(request,'fine_tunning/components/create_model.html',context={"base_models":self.LIST_OF_BASE_MODELS,"saved_prompts":examples_data})

    def post(self,request):
        user = request.POST.get('user','')
        system = request.POST.get('system','')
        assistant = request.POST.get('assistant','')
        example = FineTuneExample.objects.create(user=user,system=system,assistant=assistant)
        example_data = {
            'id':example.pk,
            'user':example.user,
            'assistant':example.assistant,
            'system':example.system
        }
        return JsonResponse({
            'status':'success',
            'example':example_data
        })
    
class PlayGroundView(View):
        messages=[
                {'role':'system',  "content": "You are a helpful mailbot AI assistant. Your job is to generate ideal gmail responses. The format of the email doesn't matter, provide answer in plain text without subject."},
            ]
        client = initialize_client()
        def get(self,request):
            model_content_type = ContentType.objects.get(app_label='api', model='conversation')
            Conversation = model_content_type.model_class()

            user =request.user
            
            # Get all conversations for the user
            if user.is_authenticated:
                conversations = Conversation.objects.filter(user=user).prefetch_related('messages')
            else:
                # Handle the case where the user is not authenticated
                conversations = None
            
            # Prepare the data to be returned as JSON
            conversation_data = []
            for conversation in conversations:
                messages = [{'role': message.role, 'content': message.content, 'created_at': message.created_at} for message in conversation.messages.all()]
                conversation_data.append({
                    'conversation_id': conversation.pk,
                    'created_at': conversation.created_at,
                    'messages': messages
                })

            return JsonResponse({'user': { 'username': user.username}, 'conversations': conversation_data})
        
        def post(self,request):
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            selected_model = FineTunningModel.objects.filter(selected=True)
            if prompt == '':
                return JsonResponse({'status':'failed','msg':'no email was submitted'})
            self.messages.append({'role':'user',  "content": prompt})
            if not selected_model:
                return JsonResponse({'status':'failed','msg':'no model is selected'})
            try:
                response = self.client.chat.completions.create(
                    model=selected_model[0].output_model,
                    messages=self.messages,
                )
            except openai.AuthenticationError:
                request.session['error'] = 'API key is wrong or Does not Exist.'
                return redirect(reverse('api-key'))
            print(response.choices[0].message)
            self.messages.append(response.choices[0].message)
            if response.choices[0].message.tool_calls:
                print(response.choices[0].message.tool_calls)
                tool_call = response.choices[0].message.tool_calls[0]
                tool_call_name = response.choices[0].message.tool_calls[0].function.name
                tool_call_id = response.choices[0].message.tool_calls[0].id
                print(tool_call,tool_call_name)
                arguments = json.loads(tool_call.function.arguments)
                if tool_call_name == 'check_product_availability':
                    item_name = arguments['item_name']
                    color = arguments['color']
                    size = arguments['size']
                    availability = check_product_availability(item_name,color,size)
                    function_call_result_message = {
                        "role": "tool",
                        "content": json.dumps({
                            "item_name": item_name,
                            "color": color,
                            'size':size,
                            'availability':availability
                        }),
                        "tool_call_id": tool_call_id
                    }

                # print(arguments)
                # order_id = arguments['order_id']
                # print(order_id)
                # delivery_date = get_delivery_date(order_id)
                self.messages.append(function_call_result_message)
                try:
                    response = self.client.chat.completions.create(
                        model=selected_model[0].output_model,
                        messages=self.messages,
                    )
                except openai.APIConnectionError:
                    request.session['error'] = 'API key is wrong or Does not Exist.'
                    return redirect(reverse('api-key'))
                print(response.choices[0])
            return JsonResponse({'status':'success','msg':response.choices[0].message.content})

class ChatLogView(View):

    def get(self,request):
        return render(request,'chat_logs/index.html')