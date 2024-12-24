from django.urls import path
from .views import test, CreateUserLocationView, CustomRefreshTokenObtainPairView, CustomTokenObtainPairView, GuestLoginViewSet, VerifyRefreshTokenView, logout, UserLogout,  UserProfileViewSet, admin_login, AdminViewSet, ProfileOTPVerify, LocationOTPVerify, custom_login_redirect_view, ChangePasswordEmail, ResetPasswordEmail, ChangePassword, ResetPassword, NotificationViewSet, UserUpdateViewSet, ResendOtpView, ResendAuthenticationMailView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('user-profile', UserProfileViewSet, basename='user-profile')
router.register('guest-user', GuestLoginViewSet, basename='guest-user')

router.register('user-location', CreateUserLocationView, basename='user-location')

router.register('notification', NotificationViewSet, basename='notification')

router.register('user-update', UserUpdateViewSet, basename='user-update')
router.register('test', test, basename='tst')


urlpatterns = [
     path('token/', CustomTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
     path('refresh-token/', CustomRefreshTokenObtainPairView.as_view(),
         name='token_refresh_pair'),
     path('logout', logout),

     path('admin-login/', admin_login),
     path('admin/me', AdminViewSet.as_view({'get': 'retrieve'})),

     path('profile-otp-verify/',  ProfileOTPVerify.as_view()),
     path('location-otp-verify/', LocationOTPVerify.as_view()),

     path('auth/custom-redirect/', custom_login_redirect_view, name='custom_login_redirect'),

     path('change-password-email/', ChangePasswordEmail.as_view()),
     path('change-password/', ChangePassword.as_view()),
     path('reset-password-email/', ResetPasswordEmail.as_view()),
     path('reset-password/', ResetPassword.as_view()),
    path('token/verify-refresh/', VerifyRefreshTokenView.as_view(), name='verify-refresh-token'),

    path('resend-otp/', ResendOtpView.as_view(), name='resend_otp'),
    path('resend-authentication-mail/', ResendAuthenticationMailView.as_view(), name='resend-authentication-mail')

] + router.urls
