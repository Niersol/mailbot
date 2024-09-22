from pydantic import BaseModel
from typing import Optional



def get_tools():
    tools = [
        {
            "type":'function',
            'function':{
                "name": "get_crypto_price",
                "description": "It takes crypto_name, and currency. Fetches the detail of a specific cryptocurrency. Call this whenever user asks about any detail about any particular cryptocurrency",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "crypto_name": {
                            "type": "string",
                            "description": "The name of the cryptocurrency to fetch the price for."
                        },
                        'currency':{
                            'type':'string',
                            'description':'the code of currency to convert the price'
                        }
                    },
                    "required": ["crypto_name",'currency']
                }
            }
        },
        {
            'type':'function',
            'function':{
                "name": "get_crypto_info",
                "description": "Provides general information about cryptocurrencies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        'currency':{
                            'type':'string',
                            'description':'the code of currency to convert the price'
                        }
                    },
                }
            }
        },
        {
            'type':'function',
            'function':{

                "name": "send_email",
                "description": "Sends an email to a specified email address.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to_email": {
                            "type": "string",
                            "description": "The recipient's email address."
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the email. Generate the subject of the email from body if not specifically given.",
                            "default": ""
                        },
                        "body": {
                            "type": "string",
                            "description": "The body content of the email. The message recieved has command to write the body. The body should be written in professional context even if not provided in professional context. If user doesn't enter name, You Don't need to add Footer mentioning User name. If the recipient name is not added you can extract a part of name that makes sense from email address as a name"
                        }
                    },
                    "required": ["to_email", "body"]
                }
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'get_order_details',
                'description': 'This function returns details of an order. Call this when a user asks about their order. If order ID is not given, ask the user for the order_id.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'order_id': {
                            'type': 'string',
                            'description': 'Order ID to get the order details from the database'
                        }
                    },
                    'required': ['order_id']
                }
            }
        },
        {
            'type':'function',
            'function':{

                "name": "schedule_event",
                "description": "Schedules a Event at a specified date.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        'summary':{
                            'type':"string",
                            'description':'The Title of the event. Rather than taking exact title. make it more readable and professional.'
                        },
                        "start_date_and_time": {
                            "type": "string",
                            "description": "The start date time of the event. take it only if time with date is provided if time is not provided take start date as a parameter leave this parameter. Format should be YYYY-MM-DDTHH:MM:SS.MMMZ example 2008-03-07T17:06:02.000Z"
                        },
                        "end_date_and_time": {
                            "type": "string",
                            "description": "The end date and time of the event. If start date and time is provide but end time is not provided ask specifically about end time. Format should be YYYY-MM-DDTHH:MM:SS.MMMZ example 2008-03-07T17:06:02.000Z"
                        },
                        "participants": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "A list of participants' emails or names.",
                            "default": []
                        },
                        'location':{
                            'type':'string',
                            'description':'Location of the event if mentioned',
                        }
                    },
                    "required": ["summary",'start_date_and_time','end_date_and_time']
                }
            }
        }
    ]
    return tools
