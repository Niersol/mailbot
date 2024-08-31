import re
from time import sleep
import datetime
from celery import shared_task
from email.utils import parsedate_to_datetime
from django.utils import timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .models import Credentials as creds, GmailMessage, RawMessage, Payload, Header, EmailAddress, Part, ScriptControl
from google.auth.transport.requests import Request

def get_credentials():
    cred = creds.objects.get(id=1)
    scopes_list = cred.scopes.split(',')  # Convert the comma-separated string back to a list
    credentials = Credentials(
        token=cred.token,
        token_uri=cred.token_uri,
        refresh_token=cred.refresh_token,
        scopes=scopes_list,
        client_id=cred.client_id,
        client_secret=cred.client_secret
    )
    return credentials

def extract_email_and_name(header_value):
    match = re.search(r'(.*) <(.+?)>', header_value)
    if match:
        name, email = match.groups()
        return name.strip(), email
    return header_value, header_value  # If no match, return header as both name and email

def fetch_and_store_emails(service):
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])

    for message in messages:
        try:
            # Check if the message already exists in the database
            if GmailMessage.objects.filter(message_id=message['id']).exists():
                print(f"Message ID {message['id']} already exists. Skipping...")
                continue

            # Fetch the message details
            msg = service.users().messages().get(userId='me', id=message['id']).execute()

            # Extract message metadata
            message_id = msg['id']
            thread_id = msg['threadId']
            label_ids = ','.join(msg.get('labelIds', []))
            snippet = msg.get('snippet', '')
            history_id = msg['historyId']
            internal_date = timezone.make_aware(
                datetime.datetime.fromtimestamp(int(msg['internalDate']) / 1000),
                timezone=timezone.get_current_timezone()
            )
            size_estimate = msg.get('sizeEstimate', 0)

            # Extract the 'From' header
            from_header = next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'From')
            sender_name, sender_email = extract_email_and_name(from_header)

            # Extract the 'To' header (receiver's information)
            to_header = next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'To')
            receiver_name, receiver_email = extract_email_and_name(to_header)

            # Extract the 'Date' header
            date_header = next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'Date')
            received_date = parsedate_to_datetime(date_header)
            subject_header = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'), '')

            # Handle the EmailAddress model for both sender and receiver
            sender_address, created = EmailAddress.objects.get_or_create(email=sender_email)
            receiver_address, created = EmailAddress.objects.get_or_create(email=receiver_email)

            # Create GmailMessage instance
            gmail_message = GmailMessage.objects.create(
                address=sender_address,
                message_id=message_id,
                thread_id=thread_id,
                label_ids=label_ids,
                snippet=snippet,
                history_id=history_id,
                internal_date=internal_date,
                size_estimate=size_estimate,
                sender_name=sender_name,
                received_date=received_date,
                subject=subject_header,
                receiver_name=receiver_name,
                receiver_email=receiver_email
            )

            # Store Headers
            headers = msg['payload'].get('headers', [])
            for header in headers:
                Header.objects.create(
                    gmail_message=gmail_message,
                    name=header['name'],
                    value=header['value']
                )

            # Store Payload
            payload = msg['payload']
            payload_instance = Payload.objects.create(
                gmail_message=gmail_message,
                mime_type=payload.get('mimeType', ''),
                body_data=payload.get('body', {}).get('data', '')
            )

            # Store Parts if they exist
            if 'parts' in payload:
                for part in payload['parts']:
                    Part.objects.create(
                        payload=payload_instance,
                        part_id=part.get('partId', ''),
                        mime_type=part.get('mimeType', ''),
                        filename=part.get('filename', ''),
                        body_data=part.get('body', {}).get('data', ''),
                        attachment_id=part.get('body', {}).get('attachmentId', '')
                    )

            # Store Raw Message
            RawMessage.objects.create(
                gmail_message=gmail_message,
                raw_data=msg.get('raw', '')
            )

            print(f"Message ID {message['id']} stored successfully.")

        except Exception as e:
            print(f"An error occurred while processing message ID {message['id']}: {e}")

@shared_task
def main():
    script = ScriptControl.objects.get(id=1)
    if script.is_running:
        try:
            credentials = get_credentials()
            service = build('gmail', 'v1', credentials=credentials)
            fetch_and_store_emails(service)
            
            # Refresh the credentials
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            # Ensure scopes are correctly stored
            cred = creds.objects.get(id=1)
            cred.token = credentials.token
            cred.refresh_token = credentials.refresh_token
            cred.client_id = credentials.client_id
            cred.client_secret = credentials.client_secret
            cred.token_uri = credentials.token_uri
            cred.scopes = ','.join(credentials.scopes)  # Store scopes as a string
            cred.save()

        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("script is off")
