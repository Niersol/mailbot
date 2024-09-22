import json
import requests
import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from openai import OpenAI
from django.db.models import Q
from django.conf import settings
from .models import *
from .models import Credentials as creds
from google.oauth2.credentials import Credentials

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'




def get_credentials():
    try:
        cred = creds.objects.get(id=1)
        scopes_list = cred.scopes.split(',')
        
        # Ensure all fields are present and valid
        if not cred.token or not cred.refresh_token or not cred.client_id or not cred.client_secret:
            print("Missing critical credential fields")
            return None

        credentials = Credentials(
            token=cred.token,
            token_uri=cred.token_uri,
            refresh_token=cred.refresh_token,
            scopes=scopes_list,
            client_id=cred.client_id,
            client_secret=cred.client_secret
        )
        
        # Check if the credentials are expired and can be refreshed
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())

        return credentials

    except creds.DoesNotExist:
        print("Credentials not found in the database")
        return None


def get_crypto_price(args):
    url = "https://api.livecoinwatch.com/coins/single"
    name = args.get('crypto_name','BTC')
    currency = args.get('currency','USD')


    payload = json.dumps({
    "currency": currency,
    "code": name,
    "meta": True
    })
    headers = {
    'content-type': 'application/json',
    'x-api-key': '5e4197c6-0ea2-4e39-a2b1-342ba5c7aa38'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    return response.text

def get_crypto_info(args):
    url = "https://api.livecoinwatch.com/coins/single"
    currency = args.get('currency',"USD")
    payload = json.dumps({
        "currency": currency,
        "sort": "rank",
        "order": "ascending",
        "offset": 0,
        "limit": 50,
        "meta": True
    })
    headers = {
    'content-type': 'application/json',
    'x-api-key': '5e4197c6-0ea2-4e39-a2b1-342ba5c7aa38'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    return response.text


def send_email(args):
    recipient_address = args.get('to_email','')
    body = args.get('body','')
    subject = args.get('subject','')
    creds = get_credentials()
    print(creds)
    # Create a new email message
    message = MIMEMultipart()
    message['to'] = recipient_address
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Encode the message to base64url
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)

        # Create the message body
        message_body = {
            'raw': raw_message
        }

        # Send the email
        sent_message = service.users().messages().send(userId='me', body=message_body).execute()

        return json.dumps({'status': "success"})

    except HttpError as error:
        print(f'An error occurred: {error}')
        return json.dumps({'status': "failure", 'error': str(error)})
    


def create_calendar_event(event_details):
    """
    Schedules a calendar event using Google Calendar API with support for both date and datetime formats.

    Args:
        event_details (dict): A dictionary containing:
            - 'summary': Title of the event
            - 'start_date': Event start date in 'YYYY-MM-DD' format (if time is not provided)
            - 'end_date': Event end date in 'YYYY-MM-DD' format (if time is not provided)
            - 'start_datetime': Event start datetime in 'YYYY-MM-DDTHH:MM:SS' format
            - 'end_datetime': Event end datetime in 'YYYY-MM-DDTHH:MM:SS' format
            - 'participants': List of participants' emails or names
            - 'location': Location of the event

    Returns:
        dict: Google API's response of the created event or error message.
    """
    
    try:
        credentials = get_credentials()
        service = build('calendar', 'v3', credentials=credentials)
        print("inside schedule event")
        # Prepare the event object based on the provided details
        if 'start_date_and_time' in event_details and 'end_date_and_time' in event_details:
            # Use datetime fields if provided
            event = {
                'summary': event_details['summary'],
                'start': {
                    'dateTime': event_details['start_date_and_time'],
                    'timeZone': 'Asia/Karachi',
                },
                'end': {
                    'dateTime': event_details['end_date_and_time'],
                    "timeZone": "Asia/Karachi"
                },
                'location': event_details.get('location', ''),
                'attendees': [{'email': email} for email in event_details.get('participants', [])]
            }

        # Insert the event into the user's primary calendar
        created_event = service.events().insert(calendarId='primary', body=event).execute()

        print(f"Event created: {created_event.get('htmlLink')}")
        return json.dumps({'status': 'success', 'event_link': created_event.get('htmlLink')})

    except Exception as error:
        print(f"An error occurred: {error}")
        return json.dumps({'status': 'failure', 'error': str(error)})
    

def get_order_details(args):
    order_id = args['order_id']
    order = Order.objects.get(id=order_id)
    items = [{
        'item_name':item.product.name,
        'item_quantity':item.quantity,
        'item_price':str(item.price)
    } for item in order.cart.items.all()]
    price = str(order.total_price)
    return json.dumps({
        'order_id':order.pk,
        'Total price':price,
        'user':order.user.username,
        'items':items,
        'status':order.status
    })