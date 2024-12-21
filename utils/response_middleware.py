# import json
# from django.http import HttpResponse, JsonResponse
# from django.utils.deprecation import MiddlewareMixin
#
# class ResponseUpdateMiddleware(MiddlewareMixin):
#     def process_response(self, request, response):
#         status_code = response.status_code
#         try:
#             if isinstance(response.body, dict):  # Ensure response.body is a dictionary
#                 response.body["message"] = "This is an error"
#                 response.body["error_code"] = status_code
#             else:
#                 response.body = {"message": "This is an error", "error_code": status_code}
#         except:
#
#             return response
#
# from rest_framework.response import Response
# from rest_framework import status
# class SimpleMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         response:Response = self.get_response(request)
#         try:
#             # print(response.data)
#             if response.status_code >= 400:
#                 new_response = {}
#                 new_response['default_message'] = response.data
#                 new_response['message'] = 'An Error Occurred'
#                 if "detail" in new_response['default_message']:
#                     new_response['message'] = new_response['default_message']['detail']
#                 if 'message' in new_response['default_message']:
#                     new_response['message'] = new_response['default_message']['message']
#             return JsonResponse(new_response, status = response.status_code)
#         except Exception as e:
#             return response
#
#         return response

from django.http import JsonResponse
import logging
from django.conf import settings  # To check DEBUG flag

logger = logging.getLogger(__name__)

class EnhancedErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Allow request to proceed to the view
            response = self.get_response(request)
        except Exception as e:
            # Let Django handle the error if DEBUG=True
            if settings.DEBUG:
                raise e

            # Log and return a generic JSON response for production
            logger.error(f"Unhandled exception: {e}")
            return JsonResponse(
                {
                    "message": "An unexpected error occurred. Please try again later.",
                    "default_message": {"error": str(e)},
                    "error_code": 500,
                },
                status=500,
            )

        # Process and format other non-500 errors
        if response.status_code >= 400 and response.status_code < 500:
            return self.format_error_response(response)

        return response

    def format_error_response(self, response):
        try:
            error_response = {
                "default_message": "An unknown error occurred.",
                "message": "Something went wrong. Please try again.",
                "error_code": response.status_code,
            }

            if hasattr(response, "data"):
                error_response["default_message"] = response.data
                if isinstance(response.data, dict):
                    error_response["message"] = self.generate_friendly_error_message(response.data)

            return JsonResponse(error_response, status=response.status_code)

        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return JsonResponse(
                {
                    "default_message": {"error": str(e)},
                    "message": "An unexpected error occurred. Please contact support.",
                    "error_code": 500,
                },
                status=500,
            )

    def generate_friendly_error_message(self, errors):
        """
        Generate user-friendly error messages for all types of errors.
        """
        # Error mappings for general patterns
        error_type_mapping = {
            "required": "field cannot be empty.",
            "null": "field cannot be null.",
            "invalid": "field contains an invalid value.",
            "too short": "field is too short.",
            "too long": "field is too long.",
        }

        # Custom field-specific mappings
        field_custom_messages = {
            "phone_number": {
                "required": "Phone number field cannot be empty.",
                "null": "Phone number is required.",
                "invalid": "Phone number is invalid. Please enter a valid phone number.",
            },
            "email": {
                "invalid": "Email address is not valid. Please provide a valid email.",
            },
        }

        messages = []
        for field, issues in errors.items():
            if isinstance(issues, list):
                for issue in issues:
                    issue_lower = issue.lower()

                    # Check for field-specific custom messages
                    if field in field_custom_messages:
                        for error_type, custom_message in field_custom_messages[field].items():
                            if error_type in issue_lower:
                                messages.append(custom_message)
                                break
                        else:
                            # Fallback to generic mapping if no custom match
                            for error_type, generic_message in error_type_mapping.items():
                                if error_type in issue_lower:
                                    messages.append(f"{field.replace('_', ' ').capitalize()} {generic_message}")
                                    break
                            else:
                                # Final fallback to the raw issue message
                                messages.append(f"{field.replace('_', ' ').capitalize()}: {issue}")
                    else:
                        # General handling for non-custom fields
                        for error_type, generic_message in error_type_mapping.items():
                            if error_type in issue_lower:
                                messages.append(f"{field.replace('_', ' ').capitalize()} {generic_message}")
                                break
                        else:
                            # Final fallback to the raw issue message
                            messages.append(f"{field.replace('_', ' ').capitalize()}: {issue}")

        return " ".join(messages)
