from typing import Any, Dict
from django.db import IntegrityError, transaction
from rest_framework.serializers import ModelSerializer
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from user.models import Notification, User, UserLocation, UserProfile
from vendor.models import Vendor
from django.template.defaultfilters import slugify
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework.settings import api_settings
from djoser.serializers import TokenCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens  import RefreshToken,AccessToken

from .utils import generate_otp, mobile_message

from rest_framework.exceptions import ValidationError

class UserRegisterSerializer(UserCreateSerializer):
    retype_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )
    restaurant_name = serializers.CharField(write_only=True, required=False)
    restaurant_license = serializers.ImageField(
        write_only=True, required=False)
    email=serializers.CharField()

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "restaurant_name",
            "password",
            "retype_password",
            "role",
            "restaurant_license",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["is_active"] = instance.is_active
        return data

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("retype_password"):
            raise serializers.ValidationError(
                {"msg": "the provided passwords do not match"}
            )
        if attrs["role"] == 1:
            if  not (attrs.get("restaurant_name",None)):
                raise serializers.ValidationError(
                          {
                        "msg": "Restaurants are required to provide their restautants name while registering"
                    }
                )
        restaurant_name = None
        if attrs.get("restaurant_name", None):
            restaurant_name = attrs.pop("restaurant_name", "None")
            restaurant_license = attrs.pop("restaurant_license","None")

        user = User(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error[api_settings.NON_FIELD_ERRORS_KEY]}
            )

        if restaurant_name:
            attrs['restaurant_name'] = restaurant_name
            attrs['restaurant_license'] = restaurant_license


        return attrs


    @transaction.atomic
    def create(self, validated_data):
        vendor_name = validated_data.pop('restaurant_name', None)
        vendor_license = validated_data.pop('restaurant_license',None)

        if User.objects.filter(email=validated_data['email']).exists():
            user = User.objects.get(email=validated_data['email'])
            if user.guest_user:
                user.first_name = validated_data['first_name']
                user.last_name = validated_data['last_name']
                user.role = validated_data['role']
                # user.restaurant_license = validated_data.get("restaurant_license",None)
                user.set_password(validated_data['password'])
                user.guest_user = False
                user.save()
                return user
            else:
                raise serializers.ValidationError({"message":"User with this email exists."})

        user = 0
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail("cannot_create_user")
        
        user_profile = UserProfile.objects.create(
            user = user,
        )
        if validated_data['role'] == 1: 
            vendor = Vendor.objects.create(
                user=user,
                vendor_name=vendor_name,
                user_profile = user_profile,
                vendor_license = vendor_license,
                vendor_slug = slugify(vendor_name)+'-'+str(user.id)
            )

        return user

    def perform_create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data["email"], **validated_data
            )
        return user



class CustomTokenCreateSerializer(TokenObtainPairSerializer):
    
    def validate(self, attrs):
        request = self.context.get('request')
        data = super().validate(attrs)
        data['id'] = self.user.id
        data['first_login'] = not self.user.first_login
        self.user.first_login = True
        self.user.save()
        data['role_display'] = "Vendor" if self.user.role == 1 else "Customer" 
        data['role'] = self.user.role  
        
        if data['role'] == 1:
                data['vendor_type'] = self.user.user.vendor_type
                data['vendor_type_display'] = self.user.user.get_vendor_type_display()
                data['profile_setup'] = self.user.user.profile_setup
        
        if data['role'] == 2:
            data['profile_setup'] = self.user.user_profile.profile_setup

        data['email'] = self.user.email
        data['user_profile'] = self.user.user_profile.id

        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        data['username'] = self.user.username
        data['is_admin'] = self.user.is_admin
        data['is_active'] = self.user.is_active
        data['is_staff'] = self.user.is_staff
        data['is_superuser'] = self.user.is_superuser
        try:
            data['vendor_id'] = Vendor.objects.get(user=self.user).id
        except Vendor.DoesNotExist:
            data['vendor_id'] = None
        try:
            user_profile = UserProfile.objects.get(user=self.user)
            data['profile_picture'] = str(request.build_absolute_uri('/')) + ("media/")+ str(user_profile.profile_picture) if user_profile.profile_picture else None 
            data['cover_photo'] = str(request.build_absolute_uri('/'))  + ("media/")+ str(user_profile.cover_photo) if user_profile.cover_photo else None
            data['address'] =user_profile.address
            data['country'] =user_profile.country
            data['state'] =user_profile.state
            data['city'] =user_profile.city
            data['pin_code'] =user_profile.pin_code
            data['latitude'] =user_profile.latitude
            data['longitude'] =user_profile.longitude
            data['phone_number'] = user_profile.phone_number
        except Exception as e:
            # print(e)
            pass
        data['profile_id'] = user_profile.id
        return data
    

class UserProfileSerializer(serializers.ModelSerializer):
    already_verified = serializers.BooleanField(read_only=True)
    class Meta:
        fields = "__all__"
        model = UserProfile
        read_only_fields = ['user', 'modified_at','created_at']
    
    def update(self, instance, validated_data):
        phone_number = validated_data.get('phone_number', '')
        if phone_number != instance.phone_number:
            instance.is_mobile_verified = False
            instance.save()

        profile_instance =  super().update(instance, validated_data)

        phone_number = profile_instance.phone_number
        nation = profile_instance.nation

        if phone_number and profile_instance.is_mobile_verified == False and not UserLocation.objects.filter(user=self.context.get('request').user, phone_number=phone_number, is_mobile_verified=True).exists():
            otp, secret = generate_otp()

            profile_instance.mobile_otp = secret
            profile_instance.save()

            
            message = f"OTP verification {otp}"
            response = mobile_message(phone_number, nation, message)
            
            
            profile_instance.already_verified=False
            profile_instance.save()
            
        else:
            profile_instance.is_mobile_verified = True
            profile_instance.already_verified=True
            profile_instance.save()
            
        return profile_instance


class UsersSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(allow_null = True) 
    role_display = serializers.ReadOnlyField(source = "get_role_display")
    vendor_id = serializers.SerializerMethodField(source = "get_vendor_id")
    profile_id = serializers.SerializerMethodField()
    # user_profile = serializers.SerializerMethodField()

    class Meta:
        # fields = "__all__"
        model = User
        exclude = ["password"]


    
    def to_representation(self, instance):

        data = super().to_representation(instance)
        try:
            profile = UserProfileSerializer(UserProfile.objects.get(user=instance), context = {"request":self.context.get("request")}).data
            data['profile_picture'] = profile['profile_picture']#.url if profile['profile_picture'] else None
            data['cover_photo'] = profile['cover_photo']#.url if profile['cover_photo'] else None
            data['country'] = profile['country']
            data['state'] = profile['state']
            data['city'] = profile['city']
            data['pin_code'] = profile['pin_code']
            data['latitude'] = profile['latitude']
            data['longitude'] = profile['longitude']
            data['phone_number'] = profile['phone_number']
            # data['location'] = profile['location']

            if data['role'] == 1:
                data['vendor_type'] = instance.user.vendor_type
                data['vendor_type_display'] = instance.user.get_vendor_type_display()
                data['profile_setup'] = instance.user.profile_setup

            data['loyalty_points'] = profile['loyalty_points']

            if data['role'] == 2:
                data['profile_setup'] = profile['profile_setup']

            return data
        except UserProfile.DoesNotExist:
            return data

    def get_profile_id(self, instance):
        return UserProfile.objects.get(user=instance).id
    

    def get_vendor_id(self, instance):
        try:
           return  Vendor.objects.get(user=instance).id
        except Vendor.DoesNotExist:
            return None
        
    def get_restaurant_name(self, instance):
        try:
            vendor = Vendor.objects.get(user = instance)
            return vendor.vendor_name
        except Vendor.DoesNotExist:
            return None

    def get_user_profile(self, instance):
        try:
            return UserProfileSerializer(UserProfile.objects.get(user=instance)).data
        except UserProfile.DoesNotExist:
            return None
        

class CreateUserLocationSerializer(serializers.ModelSerializer):
    already_verified = serializers.BooleanField(read_only=True)

    class Meta:
        fields = "__all__"
        model = UserLocation
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context.get('request').user

        user_location_instance = super().create(validated_data)

        phone_number = user_location_instance.phone_number
        nation = user_location_instance.nation

        if not (UserLocation.objects.filter(user=self.context.get('request').user, phone_number=phone_number, is_mobile_verified=True).exists() or UserProfile.objects.filter(user=self.context.get('request').user, phone_number=phone_number, is_mobile_verified=True).exists()):
            otp, secret = generate_otp()

            user_location_instance.mobile_otp = secret
            user_location_instance.save()

            
            message = f"OTP verification {otp}"
            response = mobile_message(phone_number, nation, message)
            
            
            user_location_instance.already_verified=False
            user_location_instance.save()
                    
        else:
            user_location_instance.is_mobile_verified = True
            user_location_instance.already_verified=True
            user_location_instance.save()
        
        return user_location_instance
    
    def update(self, instance, validated_data):

        phone_number = validated_data.get('phone_number', '')
        if phone_number != instance.phone_number:
            instance.is_mobile_verified = False
            instance.save()
        user_location_instance = super().update(instance, validated_data)
        user=self.context.get('request').user
        
        phone_number = user_location_instance.phone_number
        nation = user_location_instance.nation

        if phone_number and not (
            UserLocation.objects.filter(user=user, phone_number=phone_number, is_mobile_verified=True).exists() or
            UserProfile.objects.filter(user=user, phone_number=phone_number, is_mobile_verified=True).exists()
        ):
            otp, secret = generate_otp()

            user_location_instance.mobile_otp = secret
            user_location_instance.save()

            
            message = f"OTP verification {otp}"
            response = mobile_message(phone_number, nation, message)
            
            
            user_location_instance.already_verified=False
            user_location_instance.save()
                    
        else:
            user_location_instance.is_mobile_verified = True
            user_location_instance.already_verified=True
            user_location_instance.save()
        
        return user_location_instance

class CompleteUserLocationSerializer(serializers.Serializer):
    default_address = serializers.SerializerMethodField(read_only=True)
    billing_address = serializers.SerializerMethodField(read_only=True)

    def get_billing_address(self, instance):
        request = self.context.get("request")
        user= request.user
        user_locations = UserLocation.objects.all().filter(user=user, is_mobile_verified=True)
        return CreateUserLocationSerializer(user_locations, many=True, context={"request":request}).data


    def get_default_address(self, instance):
        user = self.context.get("request").user
        try:
            user_details = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None
        
        
        return {
            "user":user_details.user.id,
            "address":user_details.address if user_details.address else "",
            "country":user_details.country if user_details.country else "",
            "state":user_details.state if user_details.state else "",
            "city":user_details.city if user_details.city else "",
            "pin_code":user_details.pin_code if user_details.pin_code else "",
            "latitude":user_details.latitude if user_details.latitude else "",
            "longitude":user_details.longitude if user_details.longitude else "",
            # "location":user_details.location,
            "first_name":user.first_name,
            "last_name":user.last_name,
            "phone_number":user_details.phone_number,
            "email":user.email,

        }
from django.contrib.auth import authenticate

class GuestLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def create(self, validated_data):
        email = validated_data['email']
        if User.objects.filter(email=email).exists():
            if User.objects.filter(email=email,guest_user=False):
                raise serializers.ValidationError({"message":"The provided email has an account please login"})
            else:
                return User.objects.get(email=email)
        user = User.objects.create_user(
            email = email,
            first_name = "",
            last_name = "",
            username = email,
            password = email,
            guest_user=True,
            active=True,
        )
        UserProfile.objects.create(
            user=user
        )
        return user

    def to_representation(self, value):
        request = self.context.get("request")

        data = super().to_representation(value)
        refresh_token = RefreshToken.for_user(value)
        access_token = refresh_token.access_token
        data['refresh_token'] = str(refresh_token)
        data['access_token'] = str(refresh_token.access_token)

        data['id'] = value.id
        data['first_login'] = not value.first_login
        value.first_login = False
        value.save()
        data['role_display'] = "Vendor" if value.role == 1 else "Customer" 
        data['role'] = value.role  

        data['email'] = value.email
        data['user_profile'] = value.user_profile.id

        data['first_name'] = value.first_name
        data['last_name'] = value.last_name
        data['username'] = value.username
        data['is_admin'] = value.is_admin
        data['is_active'] = value.is_active
        data['is_staff'] = value.is_staff
        data['is_superuser'] = value.is_superuser
        data['guest_user'] = value.guest_user
        try:
            data['vendor_id'] = Vendor.objects.get(user=value).id
        except Vendor.DoesNotExist:
            data['vendor_id'] = None
        try:
            user_profile = UserProfile.objects.get(user=value)
            data['profile_picture'] = str(request.build_absolute_uri('/')) + ("media/")+ str(user_profile.profile_picture) if user_profile.profile_picture else None 
            data['cover_photo'] = str(request.build_absolute_uri('/'))  + ("media/")+ str(user_profile.cover_photo) if user_profile.cover_photo else None
            data['address'] =user_profile.address
            data['country'] =user_profile.country
            data['state'] =user_profile.state
            data['city'] =user_profile.city
            data['pin_code'] =user_profile.pin_code
            data['latitude'] =user_profile.latitude
            data['longitude'] =user_profile.longitude
            data['phone_number'] = user_profile.phone_number

        except Exception as e:
            # print(e)
            pass
        return data

    

class LogoutSerializer(serializers.Serializer):

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except:
            raise serializers.ValidationError({"bad token"})
        

from djoser.serializers import PasswordSerializer, CurrentPasswordSerializer, SendEmailResetSerializer

class SetPasswordSerializer(PasswordSerializer, CurrentPasswordSerializer):
    
    def validate(self, attrs):
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({"message":"The new password cannot be old password"})
        return super().validate(attrs)

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email", "role", "date_joined", "last_login", "created_date", "modified_date", "is_admin", "is_active", "is_staff", "is_superuser", "first_login", "guest_user"]

class ResetPasswordSerializer(SendEmailResetSerializer):
    def validate(self, attrs):
        request = self.context.get('request')
        if not User.objects.filter(email = attrs['email']).exists():
            raise serializers.ValidationError({'message': 'Invalid email'})
        return super().validate(attrs)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"

class UserUpdateVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"

class UserUpdateSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer()
    user = UserUpdateVendorSerializer()

    class Meta:
        model = User
        exclude = ['password']
    
    def update(self, instance, validated_data):
        user_profile_data = validated_data.pop('user_profile',None)
        vendor_data = validated_data.pop('user', None)

        user = super().update(instance, validated_data)

        if user_profile_data:
            user_profile = instance.user_profile
            for attr, value in user_profile_data.items():
                setattr(user_profile, attr, value)
            user_profile.save()
        
        if vendor_data:
            offerings = vendor_data.pop('offerings', None)
            vendor = instance.user
            for attr, value in vendor_data.items():
                setattr(vendor, attr, value)
            vendor.save()
            
            if offerings:
                vendor.offerings.set(offerings)

        return user