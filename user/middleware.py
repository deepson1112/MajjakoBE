import jwt
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

# class JWTAuthenticationMiddleware(MiddlewareMixin):

#     def process_request(self, request):
#         print("hehe")
#         token = request.COOKIES.get('access_token')
#         print(token)
#         if token:
#             try:
#                 validated_token = JWTAuthentication().get_validated_token(token)
#                 user = JWTAuthentication().get_user(validated_token)
#                 request.user = user
#             except AuthenticationFailed:
#                 request.user = None
                
class CustomAuth(JWTAuthentication):
    def authenticate(self, request):

        raw_token = request.COOKIES.get('access_token',None)
        if raw_token is None:
            return None
        try:
            raw_token = raw_token.encode('utf-8')
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception as e:
            raise AuthenticationFailed("Invalid or expired token")
