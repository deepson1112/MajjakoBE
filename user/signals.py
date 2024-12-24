from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from user.models import UserProfile

@receiver(user_signed_up)
def activate_user_on_signup(request, user, **kwargs):
    if not user.is_active:
        user.is_active = True
        user.first_login = True
        user.role = 2
        user.save()

        UserProfile.objects.create(
            user=user
        )