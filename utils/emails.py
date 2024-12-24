from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from djoser import utils
from djoser.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from utils.mail import send_mail_using_graph  # Your custom email-sending function

class PasswordResetEmail:
    template_name = "email/password_reset.html"

    def __init__(self, *args, **kwargs):
        """
        Initialize with context provided by Djoser.
        `context` contains the `user` and `request`.
        """
        self.user = kwargs.get("user")
        self.request = kwargs.get("request")

    def get_context_data(self):
        """
        Build context for rendering the email template.
        """
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        site_name = get_current_site(self.request).name
        protocol = "https" if self.request.is_secure() else "http"
        reset_url = settings.PASSWORD_RESET_CONFIRM_URL.format(uid=uid, token=token)
        domain = settings.DOMAIN

        return {
            "user": self.user,
            "uid": uid,
            "token": token,
            "url": reset_url,
            "site_name": site_name,
            "protocol": protocol,
            "domain": domain
        }

    def send(self, to_email):
        """
        Render the email template and send the email.
        `to_email` is provided by Djoser.
        """
        context = self.get_context_data()
        subject = f"Password Reset for {context['site_name']}"
        message = render_to_string(self.template_name, context)

        send_mail_using_graph(
            receiver_email=to_email[0],
            subject=subject,
            message_text=message,
        )

from templated_mail.mail import BaseEmailMessage

class ActivationEmail(BaseEmailMessage):
    template_name = "email/activation.html"

    def get_context_data(self):
        # print(settings.DOMAIN)

        context = super().get_context_data()
        user =  context.get("user")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        site_name = get_current_site('self.request').name
        protocol = "https" 
        activation_url = settings.ACTIVATION_URL.format(uid=uid, token=token)
        domain = settings.DOMAIN
        return {
            "user": user,
            "uid": uid,
            "token": token,
            "url": activation_url,
            "site_name": site_name,
            "protocol": protocol,
            "domain": domain
        }

    def send(self, to_email):
        context = self.get_context_data()
        subject = f"Activate your account on {context['site_name']}"
        message = render_to_string(self.template_name, context)

        send_mail_using_graph(
            receiver_email=to_email[0],
            subject=subject,
            message_text=message,
        )



class ConfirmationEmail:
    template_name = "email/confirmation.html"

    def __init__(self, request, user):
        self.request = request
        self.user = user

    def send(self, to):
        """
        Send confirmation email (no context required).
        """
        message = render_to_string(self.template_name, {"user": self.user})
        subject = "Confirmation Email"

        for recipient in to:
            send_mail_using_graph(
                receiver_email=recipient,
                subject=subject,
                message_text=message
            )


class PasswordChangedConfirmationEmail:
    template_name = "email/password_changed_confirmation.html"

    def __init__(self, request, user):
        self.request = request
        self.user = user

    def send(self, to):
        """
        Send confirmation email for password change.
        """
        message = render_to_string(self.template_name, {"user": self.user})
        subject = "Your Password Has Been Changed"

        for recipient in to:
            send_mail_using_graph(
                receiver_email=recipient,
                subject=subject,
                message_text=message
            )


class UsernameChangedConfirmationEmail:
    template_name = "email/username_changed_confirmation.html"

    def __init__(self, request, user):
        self.request = request
        self.user = user

    def send(self, to):
        """
        Send confirmation email for username change.
        """
        message = render_to_string(self.template_name, {"user": self.user})
        subject = "Your Username Has Been Changed"

        for recipient in to:
            send_mail_using_graph(
                receiver_email=recipient,
                subject=subject,
                message_text=message
            )


class UsernameResetEmail:
    template_name = "email/username_reset.html"

    def __init__(self, request, user):
        self.request = request
        self.user = user

    def get_context_data(self):
        """
        Build context data for the email template.
        """
        context = {
            "user": self.user,
            "uid": utils.encode_uid(self.user.pk),
            "token": default_token_generator.make_token(self.user),
            "url": settings.USERNAME_RESET_CONFIRM_URL.format(
                uid=utils.encode_uid(self.user.pk),
                token=default_token_generator.make_token(self.user),
            ),
            "site_name": get_current_site(self.request).name,
            "protocol": "https" if self.request.is_secure() else "http",
            "domain" : settings.DOMAIN
        }
        return context

    def send(self, to):
        """
        Render the template using render_to_string and send the email.
        """
        context = self.get_context_data()
        message = render_to_string(self.template_name, context)  # Render the template
        subject = f"Username Reset Request on {context['site_name']}"

        for recipient in to:
            send_mail_using_graph(
                receiver_email=recipient,
                subject=subject,
                message_text=message
            )

