#mobile OTP verification
import pyotp
from datetime import datetime, timedelta
from dvls import settings
import requests
from rest_framework.serializers import ValidationError
from rest_framework.response import Response

def send_message(message, phone_number, schedule=False):
    """
    This function sends message request to the message server
    """
    message_server = settings.MESSAGE_SERVER
 
    payload = {
        "message": message,
        "message_to": phone_number,
        "message_from_service": 1,
        "schedule":schedule
        }
    
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(message_server, json=payload, headers=headers)

    return response

def generate_otp():
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, interval=300)
    otp = totp.now()
    return otp, secret 

def verify_otp(otp, secret):
    totp = pyotp.TOTP(secret, interval=300)
    return totp.verify(otp)

def sparrow_sms(to, text):
    response = requests.post(
            "http://api.sparrowsms.com/v2/sms/",
            data={'token' : settings.SPARROW_SMS_TOKEN,
                  'from'  : 'TheAlert',
                  'to'    : to,
                  'text'  : text})

    # status_code = r.status_code
    # response = r.text
    response_json = response.json()
    return response_json

from django.core.exceptions import ValidationError
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

# def mobile_message(phone_number, nation, message):
#     if not phone_number or not nation:
#         raise ValidationError({
#             'message': 'Phone number and nation are required.',
#             'default_message': {'phone_number': 'Missing phone number', 'nation': 'Missing nation'}
#         })
#
#     try:
#         if nation == "NP":
#             otp_response = sparrow_sms(phone_number, message)
#             if otp_response.get('response_code') != 200:
#                 raise ValidationError({
#                     'message': 'Failed to send OTP for Nepal.',
#                     'default_message': {'response_code': otp_response.get('response_code', 'Unknown')}
#                 })
#
#         elif nation == "US":
#             if len(phone_number) < 10:
#                 raise ValidationError({
#                     'message': 'Invalid phone number for the US.',
#                     'default_message': {'phone_number': phone_number}
#                 })
#
#             area_code = phone_number[:3]
#             main_number = phone_number[3:]
#             formatted_phone_number = f"({area_code}) {main_number}"
#
#             otp_response = send_message(message, formatted_phone_number)
#             if otp_response.status_code != 200:
#                 raise ValidationError({
#                     'message': 'Failed to send OTP for the US.',
#                     'default_message': {'response_code': otp_response.status_code, 'details': otp_response.text}
#                 })
#
#         else:
#             raise ValidationError({
#                 'message': f'Unsupported nation code: {nation}',
#                 'default_message': {'nation': nation}
#             })
#
#     except ValidationError as ve:
#         logger.error(f"Validation error: {ve}")
#         raise ve
#
#     except Exception as e:
#         logger.error(f"Unexpected error while sending OTP: {e}")
#         raise ValidationError({
#             'message': 'An unexpected error occurred while sending OTP.',
#             'default_message': {'error': str(e)}
#         })
#
#     return Response({"message": "OTP sent successfully"})
#
# def mobile_message(phone_number, nation, message):
#     if not phone_number or not nation:
#         raise ValidationError({
#             'message': 'Phone number and nation are required.',
#             'default_message': {'phone_number': 'Missing phone number', 'nation': 'Missing nation'}
#         })
#
#     try:
#         if nation == "NP":
#             otp_response = sparrow_sms(phone_number, message)
#             response_code = otp_response.get('response_code')
#             if response_code != 200:
#                 # Map Sparrow SMS error codes to user-friendly messages
#                 sparrow_error_mapping = {
#                     1000: "A required field is missing.",
#                     1001: "Invalid IP Address.",
#                     1002: "Invalid Token.",
#                     1003: "Account is inactive.",
#                     1004: "Account is inactive.",
#                     1005: "Account has expired.",
#                     1006: "Account has expired.",
#                     1007: "Invalid Receiver. Please check the phone number.",
#                     1008: "Invalid Sender.",
#                     1010: "Text cannot be empty.",
#                     1011: "No valid receiver found.",
#                     1012: "No credits available. Please top up your account.",
#                     1013: "Insufficient credits to send the message.",
#                 }
#
#                 error_message = sparrow_error_mapping.get(response_code, "An unknown error occurred.")
#                 raise ValidationError({
#                     'message': f"Failed to send OTP: {error_message}",
#                     'default_message': {
#                         'response_code': response_code,
#                         'response': otp_response.get('response', 'No details provided')
#                     }
#                 })
#
#         elif nation == "US":
#             if len(phone_number) < 10:
#                 raise ValidationError({
#                     'message': 'Invalid phone number for the US.',
#                     'default_message': {'phone_number': phone_number}
#                 })
#
#             area_code = phone_number[:3]
#             main_number = phone_number[3:]
#             formatted_phone_number = f"({area_code}) {main_number}"
#
#             otp_response = send_message(message, formatted_phone_number)
#             if otp_response.status_code != 200:
#                 raise ValidationError({
#                     'message': 'Failed to send OTP for the US.',
#                     'default_message': {'response_code': otp_response.status_code, 'details': otp_response.text}
#                 })
#
#         else:
#             raise ValidationError({
#                 'message': f'Unsupported nation code: {nation}',
#                 'default_message': {'nation': nation}
#             })
#
#     except ValidationError as ve:
#         logger.error(f"Validation error: {ve}")
#         raise ve
#
#     except Exception as e:
#         logger.error(f"Unexpected error while sending OTP: {e}")
#         raise ValidationError({
#             'message': 'An unexpected error occurred while sending OTP.',
#             'default_message': {'error': str(e)}
#         })
#
#     return Response({"message": "OTP sent successfully"})

from django.core.exceptions import ValidationError
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def mobile_message(phone_number, nation, message):
    if not phone_number or not nation:
        raise ValidationError({
            'phone_number': 'Phone number is required.',
            'nation': 'Nation is required.'
        })

    try:
        if nation == "NP":
            otp_response = sparrow_sms(phone_number, message)
            response_code = otp_response.get('response_code')
            if response_code != 200:
                sparrow_error_mapping = {
                    1000: "A required field is missing.",
                    1001: "Invalid IP Address.",
                    1002: "Invalid Token.",
                    1003: "Account is inactive.",
                    1005: "Account has expired.",
                    1007: "Invalid Receiver.",
                    1008: "Invalid Sender.",
                    1010: "Text cannot be empty.",
                    1011: "Invalid Mobile Number.",
                    1012: "Please try again after some time.",
                    1013: "Insufficient credits.",
                }
                error_message = sparrow_error_mapping.get(response_code, "An unknown error occurred.")
                raise ValidationError({'otp': f"Failed to send OTP: {error_message}"})

        elif nation == "US":
            if len(phone_number) < 10:
                raise ValidationError({'phone_number': 'Invalid phone number for the US.'})

            area_code = phone_number[:3]
            main_number = phone_number[3:]
            formatted_phone_number = f"({area_code}) {main_number}"

            otp_response = send_message(message, formatted_phone_number)
            if otp_response.status_code != 200:
                raise ValidationError({'otp': 'Failed to send OTP for the US.'})

        else:
            raise ValidationError({'nation': f'Unsupported nation code: {nation}'})

    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        raise ve

    except Exception as e:
        logger.error(f"Unexpected error while sending OTP: {e}")
        raise ValidationError({'error': 'An unexpected error occurred while sending OTP.'})

    return Response({"message": "OTP sent successfully"})

