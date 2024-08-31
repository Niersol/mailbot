from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from openai import OpenAI
from django.conf import settings
from datetime import datetime
from django.utils import timezone
import json
from django.template.loader import render_to_string
from .models import *
import tempfile
import os
from .functions import *


client = OpenAI(
    api_key=settings.OPENAI_APIKEY
)
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
                file = client.files.create(
                    file=file_to_upload,
                    purpose="fine-tune"
                )

            response = client.fine_tuning.jobs.create(
                training_file=file.id,
                model=base_model
            )
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

class FineTunningListView(View):
    def get(self,request):
        try:
            response = client.fine_tuning.jobs.list()
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
    def get(self,request, job_id):
        # Replace this with your actual query to fetch the job details
        job = client.fine_tuning.jobs.retrieve(job_id)
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
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_product_availability",
                    "description": "Check if a specific item is available in stock. Use this when a customer asks about the availability of a product.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {
                                "type": "string",
                                "description": "The name of the item, such as 'slim-fit dress shirt'.",
                            },
                            "color": {
                                "type": "string",
                                "description": "The color of the item.",
                            },
                            "size": {
                                "type": "string",
                                "description": "The size of the item.",
                            },
                        },
                        "required": ["item_name", "color", "size"],
                        "additionalProperties": False,
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order_status",
                    "description": "Retrieve the status of a customer's order. Use this function when a customer wants to know the status of their order.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The customer's order ID.",
                            },
                        },
                        "required": ["order_id"],
                        "additionalProperties": False,
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_return",
                    "description": "Initiate a return process for a customer's order. Call this when a customer wants to return an item.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The customer's order ID.",
                            },
                            "reason": {
                                "type": "string",
                                "description": "The reason for the return.",
                            },
                        },
                        "required": ["order_id", "reason"],
                        "additionalProperties": False,
                    },
                }
            }
        ]
        messages=[
                {'role':'system',  "content": "You are a helpful mailbot AI assistant. Your job is to generate ideal gmail responses. The format of the email doesn't matter, provide answer in plain text without subject."},
            ]

        def get(self,request):
            return render(request,'playground/index.html')
        
        def post(self,request):
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            selected_model = FineTunningModel.objects.filter(selected=True)
            if prompt == '':
                return JsonResponse({'status':'failed','msg':'no email was submitted'})
            self.messages.append({'role':'user',  "content": prompt})
            if not selected_model:
                return JsonResponse({'status':'failed','msg':'no model is selected'})
            response = client.chat.completions.create(
                model=selected_model[0].output_model,
                messages=self.messages,
                tools=self.tools
            )
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
                response = client.chat.completions.create(
                    model=selected_model[0].output_model,
                    messages=self.messages,
                )
                print(response.choices[0])
            return JsonResponse({'status':'success','msg':response.choices[0].message.content})
