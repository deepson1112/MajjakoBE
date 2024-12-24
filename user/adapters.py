from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError
from user.models import User
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        email = sociallogin.account.extra_data.get('email')
        if User.objects.filter(email=email):
                url = 'https://majjakodeals.com/info/google-auth-failure'
                # Create a response and raise an ImmediateHttpResponse
                response = redirect(url)
                raise ImmediateHttpResponse(response)
        return super().save_user(request, sociallogin, form)

   

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        # Build the redirection URL
        url = 'https://majjakodeals.com/info/google-auth-failure'
        
        # Create a response and raise an ImmediateHttpResponse
        response = redirect(url)
        raise ImmediateHttpResponse(response)