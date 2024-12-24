from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
import base64
import requests
import json

from dvls.settings import BASE_DIR, sender_email, access_token_url, client_id, client_secret


def get_access_token():
    url = access_token_url
    payload = {'grant_type': 'client_credentials', 'client_id': client_id,
               'scope': 'https://graph.microsoft.com/.default', 'client_secret': client_secret}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        access = json.loads(response.text)['access_token']
        return access
    else:
        # Raise an exception or handle the error appropriately
        raise Exception(f"Failed to get access token. Status code: {response.status_code}, Response: {response.text}")


def send_mail_using_graph(receiver_email, subject, message_text, sender_email='no-reply@majjakodeals.com', attachments=None):
    access_token = get_access_token()
    if attachments == None:
        message = {
            'Message': {
                'Subject': subject,
                'Body': {
                    'ContentType': 'HTML',
                    'Content': message_text
                },
                'ToRecipients': [{
                    'EmailAddress': {
                        'Address': receiver_email
                    }
                }]
            },
            'SaveToSentItems': 'true'
        }
    else:
        pdf_file_path = str(BASE_DIR) + '/' + attachments
        # print(pdf_file_path)
        with open(pdf_file_path, 'rb') as file:
            pdf_content = file.read()
        base64_encoded_pdf = base64.b64encode(pdf_content).decode('utf-8')
        message = {
            'Message': {
                'Subject': subject,
                'Body': {
                    'ContentType': 'HTML',
                    'Content': message_text
                },
                'ToRecipients': [{
                    'EmailAddress': {
                        'Address': receiver_email
                    }
                }],
                "attachments": [
                    {
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        "name": "attachment.pdf",
                        "contentType": "application/pdf",
                        "contentBytes": base64_encoded_pdf
                    }
                ]
            },
            'SaveToSentItems': 'true'
        }

    endpoint = f'https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail'
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.post(endpoint, headers=headers, json=message)
    if response.status_code != 202:
        raise Exception('Failed to send email: ',
                        response.status_code, response.text)


def send_verification_email(request, user, mail_subject, email_template):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    message = render_to_string(email_template, {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),

    })
    to_email = user.email

    send_mail_using_graph(receiver_email=to_email, subject=mail_subject,message_text=message)



def send_notification(mail_subject, mail_template, context):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    if (isinstance(context['to_email'], str)):
        to_email = []
        to_email.append(context['to_email'])
    else:
        to_email = context['to_email']
    send_mail_using_graph(receiver_email=context['to_email'], subject=mail_subject,message_text=message)
    
    # mail = EmailMessage(mail_subject, message, from_email, to=to_email)
    # mail.content_subtype = "html"
    # mail.send()
