from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.viewsets import ModelViewSet
from django.utils.module_loading import import_string
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from retail_orders.views import StandardResultsSetPagination
from user.models import Notification, User, UserLocation, UserProfile
from user.serializers import AdminSerializer, CompleteUserLocationSerializer, CreateUserLocationSerializer, \
    CustomTokenCreateSerializer, GuestLoginSerializer, LogoutSerializer, NotificationSerializer, UserProfileSerializer, \
    UserUpdateSerializer
# Create your views here.
from typing import Any, Dict, Optional, Type, TypeVar
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.decorators import api_view
from django.db.models import Q

from utils.permissions_override import IsSuperAdmin

from rest_framework.exceptions import ValidationError
from dvls import settings

from allauth.account.views import LogoutView as AllauthLogoutView

from .utils import generate_otp, mobile_message, verify_otp

from datetime import datetime, timedelta
from utils.mail import send_mail_using_graph
from django.template.loader import render_to_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password') 
        try:
            user = User.objects.get(email=email)
            if user.is_active == False:
                return Response({'message': 'Account not activated please check your mail.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if user.guest_user == True:
                return Response({'message': 'No active account found with the given credentials'},
                                status=status.HTTP_404_NOT_FOUND)
            user = authenticate(email=email, password=password)
            if user is None:
                return Response({'message': 'Invalid email or password.'},
                                status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'message': 'No active account found with the given credentials'},
                            status=status.HTTP_404_NOT_FOUND)

        remember_me = request.data.get('remember_me', False)
        # api_settings.ACCESS_TOKEN_LIFETIME = timedelta(seconds=20)

        if remember_me:
            original_refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME
            api_settings.REFRESH_TOKEN_LIFETIME = timedelta(days=30)

        response = super().post(request, *args, **kwargs)

        if remember_me:
            api_settings.REFRESH_TOKEN_LIFETIME = original_refresh_lifetime

        max_age = 30 * 24 * 60 * 60 if remember_me else None
        expires = datetime.utcnow() + timedelta(days=30) if remember_me else None
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='None', secure=True)
        response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite='None', secure=True,
                            max_age=max_age)
        response['Cache-Control'] = 'no-store'
        return response


class CustomRefreshTokenObtainPairView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        raw_token = request.COOKIES.get('refresh_token', None)
        if raw_token == None:
            raise serializers.ValidationError({"message": "The provided refresh token is not valid"})
        try:
            token_class = RefreshToken
            refresh = token_class(raw_token)
            if api_settings.ROTATE_REFRESH_TOKENS:
                if api_settings.BLACKLIST_AFTER_ROTATION:
                    try:
                        refresh.blacklist()
                    except AttributeError:
                        pass

                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()
            data = {"access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                    }
            response = Response(data=data, status=status.HTTP_201_CREATED)
            access_token = response.data['access_token']
            refresh_token = response.data['refresh_token']
            response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='None', secure=True)
            response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite='None', secure=True)
            response['Cache-Control'] = 'no-store'
            return response
        except Exception as e:
            response = Response({"message": "Invalid token" + e}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)
    token_class = RefreshToken

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        refresh = self.token_class(attrs["refresh"])

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data["refresh"] = str(refresh)

        return data


from rest_framework.parsers import MultiPartParser, FormParser


class UserProfileViewSet(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch', 'get']
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class CreateUserLocationView(ModelViewSet):
    queryset = UserLocation.objects.all()
    serializer_class = CreateUserLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return UserLocation.objects.all().filter(user=self.request.user, is_mobile_verified=True)

    def list(self, request, *args, **kwargs):
        a = {"billing_address": "",
             "default_address": ""
             }
        return_data = CompleteUserLocationSerializer(a, context={"request": request})
        return Response(return_data.data)


from rest_framework import status


class GuestLoginViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = GuestLoginSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        guest_serializer = GuestLoginSerializer(data=request.data, context={"request": request})

        if guest_serializer.is_valid():
            guest_serializer.save()
            access_token = guest_serializer.data['access_token']
            refresh_token = guest_serializer.data['refresh_token']
            response = Response(guest_serializer.data, status=status.HTTP_201_CREATED)
            response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='None', secure=True)
            response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite='None', secure=True)
            response['Cache-Control'] = 'no-store'

            return response
        else:
            return Response(guest_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from django.db import transaction


class UserLogout(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = LogoutSerializer

    @transaction.atomic
    def create(self, request):
        raw_token = request.COOKIES.get('refresh_token', None)
        try:
            token = RefreshToken(raw_token.encode('utf-8'))
            token.blacklist()
        except Exception as e:
            pass
        response = Response({"Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        # response.set_cookie(key='access_token', value="", httponly=True, samesite='None', secure=True)
        # response.set_cookie(key='refresh_token', value="", httponly=True, samesite='None', secure=True)

        return response


# class Logout(RetrieveAPIView):
#     permission_classes = [AllowAny]
#     serializer_class = LogoutSerializer

#     def get(self, request, *args, **kwargs):
#         try:
#             token = RefreshToken(raw_token.encode('utf-8'))
#             token.blacklist()
#         except Exception as e:
#             pass
#         response = Response({"Logout successful"}, status=status.HTTP_200_OK)
#         response.delete_cookie("access_token")
#         response.delete_cookie("refresh_token")
#         return response


#     @transaction.atomic
#     def create(self, request):
#         raw_token = request.COOKIES.get('refresh_token',None)
#         try:
#             token = RefreshToken(raw_token.encode('utf-8'))
#             token.blacklist()
#         except Exception as e:
#             pass
#         response = Response({"Logout successful"}, status=status.HTTP_200_OK)
#         response.delete_cookie("access_token")
#         response.delete_cookie("refresh_token")
#         # response.set_cookie(key='access_token', value="", httponly=True, samesite='None', secure=True)
#         # response.set_cookie(key='refresh_token', value="", httponly=True, samesite='None', secure=True)

#         return response

from rest_framework.decorators import APIView, api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def logout(request):
    # Get the refresh token from cookies
    raw_token = request.COOKIES.get('refresh_token', None)

    # Attempt to blacklist the refresh token
    if raw_token:
        try:
            token = RefreshToken(raw_token.encode('utf-8'))
            token.blacklist()
        except Exception as e:
            return Response({'message':f"Error blacklisting token: {e}"})
            # print(f"Error blacklisting token: {e}")

    # Clear session
    request.session.flush()  # Clear session data

    # Delete the cookies
    response = JsonResponse({"message": "Logout successful"}, status=status.HTTP_200_OK)
    response.delete_cookie("access_token", path='/')
    response.delete_cookie("refresh_token", path='/')

    # Delete the Google social token if it exists
    social_token = SocialToken.objects.filter(account__user=request.user.id, account__provider='google').first()
    if social_token:
        social_token.delete()

    return response


# ADMIN login

# @api_view(['POST'])
# def admin_login(request):
#     email = request.data['email']
#     password = request.data['password']
#
#     user = User.objects.filter(email=email).first()
#     if user is None:
#         raise AuthenticationFailed('Invalid email')
#
#     if not user.is_superuser:
#         raise AuthenticationFailed('Permission denied!')
#
#     if not user.check_password(password):
#         raise AuthenticationFailed('Incorrect password!')
#
#     refresh = RefreshToken.for_user(user)
#     access_token = str(refresh.access_token)
#     refresh_token = str(refresh)
#
#     response = Response({
#         'access_token': access_token,
#         'refresh_token': refresh_token,
#         "id" : user.id,
#         "first_name" : user.first_name,
#         "last_name" : user.last_name,
#         "username" : user.username,
#         "email" : user.email,
#         "date_joined" : user.date_joined,
#         "last_login" : user.last_login,
#         "created_date" : user.created_date,
#         "modified_date" : user.modified_date,
#         "is_admin" : user.is_admin,
#         "is_active" : user.is_active,
#         "is_staff" : user.is_staff,
#         "is_superuser" : user.is_superuser,
#         "first_login" : user.first_login
#
#     })
#     response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='None', secure=True)
#     response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite='None', secure=True)
#
#     return response

@api_view(['POST'])
def admin_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = User.objects.filter(email=email).first()
    if user is None:
        raise AuthenticationFailed('Invalid email')

    if not user.is_superuser:
        raise AuthenticationFailed('Permission denied!')

    if not user.check_password(password):
        raise AuthenticationFailed('Incorrect password!')

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "email": user.email,
        "date_joined": user.date_joined,
        "last_login": user.last_login,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    })

    response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='None', secure=True)
    response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite='None', secure=True)

    return response


class AdminViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AdminSerializer
    http_method_names = ['get']
    lookup_field = 'pk'
    permission_classes = [IsSuperAdmin]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


# verify mobile OTP
class ProfileOTPVerify(APIView):
    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')
        user_id = request.data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
            user_profile = user.user_profile
            user_otp = user_profile.mobile_otp
        except User.DoesNotExist:
            raise ValidationError({"message": "User doesnot exists."})
        response = verify_otp(otp, secret=user_otp)
        if response == True:
            user_profile.is_mobile_verified = True
            user_profile.profile_setup = True
            user_profile.save()
            return Response({"message": "Verified!"})
        else:
            return Response({"message": "Not verified!"}, status=status.HTTP_400_BAD_REQUEST)


class LocationOTPVerify(APIView):
    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')
        user_id = request.data.get('user_id')
        location = request.data.get('user_location')
        phone_number = request.data.get('phone_number')

        try:
            user = User.objects.get(id=user_id)
            user_location = UserLocation.objects.filter(id=location).first()
            user_otp = user_location.mobile_otp
        except User.DoesNotExist:
            raise ValidationError({"message": "User doesnot exists."})
        except UserLocation.DoesNotExist:
            raise ValidationError({"message": "User location doesnot exists."})

        response = verify_otp(otp, secret=user_otp)
        if response == True:
            user_location.is_mobile_verified = True
            user_location.save()
            return Response({"message": "Verified!"})
        else:
            return Response({"message": "Not verified!"}, status=status.HTTP_400_BAD_REQUEST)


from allauth.socialaccount.models import SocialToken
from django.shortcuts import redirect


def custom_login_redirect_view(request):
    response = redirect('https://majjakodeals.com/')
    # token = None
    # if request.user.is_authenticated:
    #     social_token = SocialToken.objects.filter(account__user=request.user, account__provider='google').first()
    #     print("social token", social_token)
    #     if social_token:
    #         token = social_token.token

    user = request.user
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # response = Response({
    #             'access_token': access_token,
    #             'refresh_token': refresh_token,
    #             "user": {
    #                 "id": user.id,
    #                 "first_name": user.first_name,
    #                 "last_name": user.last_name,
    #                 "username": user.username,
    #                 "email": user.email,
    #                 "date_joined": user.date_joined,
    #                 "last_login": user.last_login,
    #                 "is_admin": user.is_admin,
    #                 "is_active": user.is_active,
    #                 "is_staff": user.is_staff,
    #                 "is_superuser": user.is_superuser,
    #                 "first_login": user.first_login
    #             }
    #         })
    response = redirect('https://majjakodeals.com/')

    response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='None', secure=True)
    response.set_cookie(key='refresh_token', value=refresh_token, httponly=True, samesite='None', secure=True)

    # print("response", response.data['access_token'])

    # External URL with the token
    # redirect_url = 'https://majjakodeals.com/'
    # if token:
    #     redirect_url += f"?token={token}"

    # return redirect(redirect_url)
    return response


class ChangePasswordEmail(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({'message': 'Invalid email address.'})

        if user != request.user:
            return Response({"message": "Invalid email address."}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        mail_subject = "Password Change"
        mail_template = "email/pw_change.html"

        context = {
            "to_email": email,
            "link": f"{settings.PROTOCOL}{settings.DOMAIN}/account/change-password/{token}/{uid}",
            "user": user,
            "site_name": settings.SITE_NAME
        }

        send_mail_using_graph(
            receiver_email=context['to_email'],
            subject=mail_subject,
            message_text=render_to_string(mail_template, context)
        )

        return Response({"message": "Password change email sent successfully."}, status=status.HTTP_200_OK)


class ChangePassword(APIView):
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        user = request.user

        if not user.check_password(old_password):
            return Response({"message": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if old_password == new_password:
            return Response({"message": "New password cannot be the same as the old password."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"message": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes


class ResetPasswordEmail(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({'message': 'Invalid email address.'})

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        mail_subject = "Password Reset"
        mail_template = "email/password_reset.html"

        context = {
            "to_email": email,
            "link": f"{settings.PROTOCOL}{settings.DOMAIN}/info/reset-password/{uid}/{token}",
            "user": user,
            "site_name": settings.SITE_NAME
        }

        send_mail_using_graph(
            receiver_email=context['to_email'],
            subject=mail_subject,
            message_text=render_to_string(mail_template, context)
        )

        return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)


from django.contrib.auth.hashers import check_password


class ResetPassword(APIView):
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        try:
            uid_decoded = urlsafe_base64_decode(uid)
            uid_str = uid_decoded.decode('utf-8')
            user = User.objects.get(id=uid_str)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response({"message": "Invalid user ID."}, status=status.HTTP_400_BAD_REQUEST)
        except UnicodeDecodeError:
            return Response({"message": "Error decoding user ID. Invalid format."}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"message": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        if check_password(new_password, user.password):
            return Response({"message": "New password cannot be the same as the old password."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"message": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(Q(user=self.request.user) | Q(user__isnull=True)).order_by('-created_at')

    def retrieve(self, request, *args, **kwargs):
        review_instance = self.get_object()
        review_instance.seen = True
        review_instance.save()
        serializer = self.get_serializer(review_instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        paginator = StandardResultsSetPagination()

        queryset = self.filter_queryset(self.get_queryset())
        unseen_count = queryset.filter(seen=False).count()

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            paginated_response.data['unseen_count'] = unseen_count
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'unseen_count': unseen_count,
            'results': serializer.data
        })


class VerifyRefreshTokenView(APIView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({"message": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.check_exp()
            return Response({"message": "Refresh token is valid."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"message": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)


class UserUpdateViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    http_method_names = ['get', 'patch', 'put']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class test(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    http_method_names = ['get', 'patch', 'put']

    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        raise ValidationError({"message": "whats this"})
        return super().list(request, *args, **kwargs)


@permission_classes([IsAuthenticated])
class ResendOtpView(APIView):
    @staticmethod
    def process_otp(instance):
        try:
            phone_number = instance.phone_number
            nation = instance.nation

            otp, secret = generate_otp()
            instance.mobile_otp = secret
            instance.save()

            message = f"OTP verification {otp}"
            if not instance.phone_number or not instance.nation:
                raise ValidationError({
                                          "message": f"Phone number or nation not available{instance.id}, {instance},{instance.phone_number},{instance.nation}"})
            response = mobile_message(phone_number, nation, message)
            return {"message": "OTP sent successfully!"}
        except ValidationError as e:
            raise ValidationError({'message': f"Failed to send OTP: {e}"})

    def post(self, request, *args, **kwargs):
        user_profile_id = request.data.get('user_profile', '')
        user_location_id = request.data.get('user_location', '')

        if not user_profile_id and not user_location_id:
            return Response({"message": "No user_profile or user_location provided"}, status=400)

        response_data = {}

        if user_location_id:
            try:
                user_location = UserLocation.objects.get(id=user_location_id)
                response_data = self.process_otp(user_location)
            except UserLocation.DoesNotExist:
                raise ValidationError({"message": "Invalid user location"})

        if user_profile_id:
            try:
                user_profile = UserProfile.objects.get(id=user_profile_id)
                response_data = self.process_otp(user_profile)
            except UserProfile.DoesNotExist:
                raise ValidationError({"message": "Invalid user profile"})

        return Response(response_data)

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from dvls.settings import DJOSER


class ResendAuthenticationMailView(APIView):
    def get_context_data(self, user, request):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        site_name = get_current_site(request).name
        activation_url = DJOSER['ACTIVATION_URL'].format(uid=uid, token=token)
        return {
            "user": user,
            "uid": uid,
            "token": token,
            "url": activation_url,
            "site_name": site_name,
            "protocol": "https",
            "domain": settings.DOMAIN,
        }

    def send_activation_email(self, user, context):
        subject = f"Activate your account on {context['site_name']}"
        try:
            send_mail_using_graph(
                receiver_email=user.email,
                subject=subject,
                message_text=render_to_string("email/activation.html", context)
            )
        except Exception as e:
            raise ValidationError({'message': f'Failed to send email: {e}'})

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'message': 'User email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({'message':'User does not exist.'})
        
        context = self.get_context_data(user, request)
        self.send_activation_email(user, context)
        
        return Response({'message': 'Activation email sent successfully.'}, status=status.HTTP_200_OK)



        
